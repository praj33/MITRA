"""
illegal_temporal_transition_tests.py - Tests for the temporal orchestration model
- Encodes irreversibility and time-order constraints
- Uses temporal-state-matrix.json as the source of truth for allowed transitions and rules
"""

import json
from dataclasses import dataclass
from pathlib import Path
import pytest

# ----------------------------------------------------------------------------
# Load temporal model matrix
# ----------------------------------------------------------------------------
MATRIX_PATH = Path(__file__).parent / "temporal-state-matrix.json"
with MATRIX_PATH.open("r", encoding="utf-8") as f:
    MATRIX = json.load(f)

STATE_INDEX = {s["name"]: s["index"] for s in MATRIX["states"]}
TERMINAL = {s["name"]: s.get("terminal", False) for s in MATRIX["states"]}
ALLOWED = MATRIX["transitions"]
RULES = MATRIX.get("rules", {})


# ----------------------------------------------------------------------------
# Model and Errors
# ----------------------------------------------------------------------------
class IllegalTemporalTransitionError(Exception):
    """Raised when an illegal temporal transition is attempted"""


@dataclass(frozen=True)
class Event:
    event_id: str
    to_state: str
    t_e: int  # event-time (monotone non-decreasing in stream)
    t_p: int  # processing-time (monotone non-decreasing in stream)
    t_d: int  # decision-time (strictly increasing ordering key)
    reason: str = ""
    actor: str = "test"


class TemporalStateMachine:
    """Temporal state machine enforcing irreversibility and time-order rules.

    Behavior:
    - Allowed transitions are read from temporal-state-matrix.json
    - Archived is absorbing
    - t_d strictly increases, t_e/t_p non-decreasing
    - Idempotent by event_id
    """

    def __init__(self):
        self.current = "Proposed"
        self.history = []  # list[Event]
        self._seen_event_ids = set()
        # Initialize with a synthetic genesis record at t_d = -1
        self._last_t_d = -1
        self._last_t_e = -1
        self._last_t_p = -1

    def apply(self, ev: Event):
        # Idempotence: ignore replays of the same event_id
        if ev.event_id in self._seen_event_ids:
            return "duplicate_ignored"

        # Time monotonicity checks
        if ev.t_d <= self._last_t_d:
            raise IllegalTemporalTransitionError("t_d must strictly increase")
        if ev.t_e < self._last_t_e:
            raise IllegalTemporalTransitionError("t_e must be non-decreasing")
        if ev.t_p < self._last_t_p:
            raise IllegalTemporalTransitionError("t_p must be non-decreasing")

        # Terminal absorbing check
        if self.current == "Archived":
            raise IllegalTemporalTransitionError("Archived is absorbing; no outgoing transitions")

        # Transition legality per matrix
        allowed_next = ALLOWED.get(self.current, [])
        if ev.to_state not in allowed_next:
            # If matrix allows any->Archived and rule is set, permit it
            if RULES.get("allow_any_to_archived", False) and ev.to_state == "Archived":
                pass
            else:
                raise IllegalTemporalTransitionError(f"Illegal transition: {self.current} -> {ev.to_state}")

        # Optional monotone index rule (redundant given explicit transitions but enforced)
        if RULES.get("monotone_index", False):
            if STATE_INDEX[ev.to_state] < STATE_INDEX[self.current]:
                raise IllegalTemporalTransitionError("Index reversal not allowed")
            if self.current != "Archived" and ev.to_state != "Archived":
                # Disallow staying in same index
                if STATE_INDEX[ev.to_state] == STATE_INDEX[self.current]:
                    raise IllegalTemporalTransitionError("No-op transitions not allowed")

        # Commit state
        self.current = ev.to_state
        self.history.append(ev)
        self._seen_event_ids.add(ev.event_id)
        self._last_t_d = ev.t_d
        self._last_t_e = ev.t_e
        self._last_t_p = ev.t_p
        if TERMINAL.get(self.current, False):
            return "closeout_recorded"
        return "applied"


# ----------------------------------------------------------------------------
# Helpers for tests
# ----------------------------------------------------------------------------
_counter = 0

def eid():
    global _counter
    _counter += 1
    return f"e{_counter}"


def ev(to_state: str, t_base: int):
    return Event(event_id=eid(), to_state=to_state, t_e=t_base, t_p=t_base, t_d=t_base)


# ----------------------------------------------------------------------------
# TESTS
# ----------------------------------------------------------------------------

def test_valid_forward_path_and_archival_absorbing():
    sm = TemporalStateMachine()
    assert sm.apply(ev("Evaluated", 1)) == "applied"
    assert sm.apply(ev("Validated", 2)) == "applied"
    assert sm.apply(ev("Delegated", 3)) == "applied"
    assert sm.apply(ev("Archived", 4)) == "closeout_recorded"

    # Any attempt after Archived must fail
    with pytest.raises(IllegalTemporalTransitionError):
        sm.apply(ev("Validated", 5))


def test_backward_reversal_forbidden():
    sm = TemporalStateMachine()
    sm.apply(ev("Evaluated", 1))
    with pytest.raises(IllegalTemporalTransitionError, match="Illegal transition: Evaluated -> Proposed"):
        sm.apply(ev("Proposed", 2))


def test_any_to_archived_allowed_from_any_state():
    sm = TemporalStateMachine()
    # Directly archive from Proposed
    assert sm.apply(ev("Archived", 1)) == "closeout_recorded"

    # New machine: advance then archive
    sm = TemporalStateMachine()
    sm.apply(ev("Evaluated", 1))
    sm.apply(ev("Validated", 2))
    assert sm.apply(ev("Archived", 3)) == "closeout_recorded"


def test_disallow_forward_jump_when_not_enumerated():
    sm = TemporalStateMachine()
    # Proposed -> Validated is not directly allowed by the matrix
    with pytest.raises(IllegalTemporalTransitionError, match="Proposed -> Validated"):
        sm.apply(ev("Validated", 1))


def test_time_monotonicity_enforced():
    sm = TemporalStateMachine()
    sm.apply(ev("Evaluated", 10))

    # Non-increasing t_d
    with pytest.raises(IllegalTemporalTransitionError, match="t_d must strictly increase"):
        sm.apply(Event(event_id=eid(), to_state="Validated", t_e=11, t_p=11, t_d=10))

    # Decreasing t_e
    with pytest.raises(IllegalTemporalTransitionError, match="t_e must be non-decreasing"):
        sm.apply(Event(event_id=eid(), to_state="Validated", t_e=5, t_p=12, t_d=12))

    # Decreasing t_p
    with pytest.raises(IllegalTemporalTransitionError, match="t_p must be non-decreasing"):
        sm.apply(Event(event_id=eid(), to_state="Validated", t_e=12, t_p=11, t_d=13))


def test_idempotence_by_event_id():
    sm = TemporalStateMachine()
    e = ev("Evaluated", 1)
    assert sm.apply(e) == "applied"
    # Re-apply same event id (should be ignored, no exception)
    assert sm.apply(e) == "duplicate_ignored"
    # Next distinct event advances
    assert sm.apply(ev("Validated", 2)) == "applied"


def test_forbidden_reversals_after_validated_and_delegated():
    sm = TemporalStateMachine()
    sm.apply(ev("Evaluated", 1))
    sm.apply(ev("Validated", 2))

    # Validated -> Evaluated forbidden
    with pytest.raises(IllegalTemporalTransitionError, match="Validated -> Evaluated"):
        sm.apply(ev("Evaluated", 3))

    # Move to Delegated, then attempt reversal
    sm.apply(ev("Delegated", 4))
    with pytest.raises(IllegalTemporalTransitionError, match="Delegated -> Validated"):
        sm.apply(ev("Validated", 5))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 
