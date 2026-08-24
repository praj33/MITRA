"""
TANTRA Execution State Machine
==============================
Deterministic state transitions for execution lifecycle.
Every state transition is recorded in Bucket.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.tantra.contracts import ExecutionStatus, ExecutionDecision


# Valid state transitions: from_state -> set of allowed to_states
VALID_TRANSITIONS: Dict[ExecutionStatus, set[ExecutionStatus]] = {
    ExecutionStatus.PENDING: {
        ExecutionStatus.DISPATCHED,
        ExecutionStatus.BLOCKED,
        ExecutionStatus.TERMINATED,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.DISPATCHED: {
        ExecutionStatus.IN_PROGRESS,
        ExecutionStatus.BLOCKED,
        ExecutionStatus.DELAYED,
        ExecutionStatus.REWRITE,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.TIMED_OUT,
        ExecutionStatus.TERMINATED,
    },
    ExecutionStatus.IN_PROGRESS: {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.BLOCKED,
        ExecutionStatus.DELAYED,
        ExecutionStatus.REWRITE,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.TIMED_OUT,
        ExecutionStatus.TERMINATED,
    },
    ExecutionStatus.COMPLETED: set(),
    ExecutionStatus.FAILED: set(),
    ExecutionStatus.BLOCKED: set(),
    ExecutionStatus.DELAYED: set(),
    ExecutionStatus.REWRITE: set(),
    ExecutionStatus.CANCELLED: set(),
    ExecutionStatus.TIMED_OUT: set(),
    ExecutionStatus.TERMINATED: set(),
}

# Decision-to-status mapping for enforcement gate
DECISION_STATUS_MAP: Dict[ExecutionDecision, ExecutionStatus] = {
    ExecutionDecision.ALLOW: ExecutionStatus.DISPATCHED,
    ExecutionDecision.REWRITE: ExecutionStatus.REWRITE,
    ExecutionDecision.DELAY: ExecutionStatus.DELAYED,
    ExecutionDecision.BLOCK: ExecutionStatus.BLOCKED,
    ExecutionDecision.TERMINATE: ExecutionStatus.TERMINATED,
}


@dataclass
class StateTransition:
    """A single state transition record."""
    from_status: ExecutionStatus
    to_status: ExecutionStatus
    timestamp: str
    reason: str = ""
    metadata: Dict[str, any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "from": self.from_status.value,
            "to": self.to_status.value,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }


@dataclass
class ExecutionStateMachine:
    """
    Tracks execution lifecycle through deterministic state transitions.
    Every transition is recorded for Bucket audit trail.
    """
    trace_id: str
    current_status: ExecutionStatus = ExecutionStatus.PENDING
    transitions: List[StateTransition] = field(default_factory=list)

    def __post_init__(self):
        self.transitions.append(
            StateTransition(
                from_status=ExecutionStatus.PENDING,
                to_status=ExecutionStatus.PENDING,
                timestamp=datetime.now(timezone.utc).isoformat(),
                reason="execution_created",
            )
        )

    def can_transition(self, to_status: ExecutionStatus) -> bool:
        """Check if transition to target status is valid."""
        allowed = VALID_TRANSITIONS.get(self.current_status, set())
        return to_status in allowed

    def transition(
        self,
        to_status: ExecutionStatus,
        reason: str = "",
        metadata: Optional[Dict] = None,
    ) -> StateTransition:
        """
        Execute a state transition. Raises if invalid.
        Returns the recorded transition.
        """
        if not self.can_transition(to_status):
            raise ValueError(
                f"Invalid transition: {self.current_status.value} -> {to_status.value}. "
                f"Allowed: {[s.value for s in VALID_TRANSITIONS.get(self.current_status, set())]}"
            )

        transition = StateTransition(
            from_status=self.current_status,
            to_status=to_status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason,
            metadata=metadata or {},
        )
        self.current_status = to_status
        self.transitions.append(transition)
        return transition

    def apply_enforcement_decision(self, decision: ExecutionDecision) -> StateTransition:
        """Apply enforcement decision as a state transition."""
        target_status = DECISION_STATUS_MAP.get(decision, ExecutionStatus.BLOCKED)
        return self.transition(
            target_status,
            reason=f"enforcement_{decision.value.lower()}",
        )

    def get_timeline(self) -> List[Dict]:
        """Return full transition timeline for Bucket storage."""
        return [t.to_dict() for t in self.transitions]

    def is_terminal(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.current_status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.BLOCKED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMED_OUT,
            ExecutionStatus.TERMINATED,
        }

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "current_status": self.current_status.value,
            "transition_count": len(self.transitions),
            "timeline": self.get_timeline(),
            "is_terminal": self.is_terminal(),
        }
