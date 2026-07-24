"""
Run once: python setup_policy_runtime.py
Creates policy_runtime/ package with runtime.py, adapters.py, __init__.py
"""
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "policy_runtime")
os.makedirs(BASE, exist_ok=True)

# ── runtime.py ────────────────────────────────────────────────────────────────
RUNTIME = '''\
"""
policy_runtime/runtime.py — System-agnostic policy evaluation core.

Accepts: { text, system, region, user_id }
Returns: ALLOW | BLOCK | REWRITE  (plus trace metadata)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from policy_engine import evaluate_policy, PolicyDecision
from behavior_validator import validate_behavior

VALID_SYSTEMS = {"mitra", "creator_core", "bhiv"}


def evaluate(
    text: str,
    system: str,
    region: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Single entry point for all systems.

    Args:
        text:    Input text to evaluate.
        system:  Calling system — mitra | creator_core | bhiv.
        region:  Optional ISO region code (EU | UK | AU | DEFAULT).
        user_id: Optional caller identifier for tracing.

    Returns:
        dict with keys: decision, category, confidence, trace_id,
                        rule_id, reason, system, safe_output
    """
    resolved_system = system if system in VALID_SYSTEMS else "bhiv"

    # Gate 1: JSON policy rules (fast path)
    policy = evaluate_policy(text=text, system=resolved_system, region=region)

    if policy["decision"] in (PolicyDecision.BLOCK, PolicyDecision.REWRITE):
        return {
            "decision":       policy["decision"],
            "category":       policy["category"],
            "confidence":     policy["confidence"],
            "trace_id":       policy["trace_id"],
            "rule_id":        policy["rule_id"],
            "reason":         policy["reason"],
            "system":         resolved_system,
            "policy_version": policy.get("policy_version", "unknown"),
            "safe_output":    None,
        }

    # Gate 2: Behavior pattern library (deep scan)
    bv = validate_behavior("auto", text)
    decision_map = {
        "hard_deny":    "BLOCK",
        "soft_rewrite": "REWRITE",
        "allow":        "ALLOW",
    }
    decision = decision_map.get(bv["decision"], "ALLOW")

    return {
        "decision":       decision,
        "category":       bv["risk_category"],
        "confidence":     bv["confidence"],
        "trace_id":       bv["trace_id"],
        "rule_id":        f"BV-{bv[\'risk_category\'].upper()}",
        "reason":         bv["explanation"],
        "system":         resolved_system,
        "policy_version": policy.get("policy_version", "unknown"),
        "safe_output":    bv.get("safe_output") if decision != "ALLOW" else None,
    }
'''

# ── adapters.py ───────────────────────────────────────────────────────────────
ADAPTERS = '''\
"""
policy_runtime/adapters.py — Per-system adapter functions.

Each adapter calls the same runtime.evaluate(); only the system tag differs.
"""
from typing import Dict, Any, Optional
from .runtime import evaluate


def validate_for_mitra(
    text: str,
    region: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    return evaluate(text=text, system="mitra", region=region, user_id=user_id)


def validate_for_creator_core(
    text: str,
    region: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    return evaluate(text=text, system="creator_core", region=region, user_id=user_id)


def validate_for_bhiv(
    text: str,
    region: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    return evaluate(text=text, system="bhiv", region=region, user_id=user_id)
'''

# ── conflict_guard.py ────────────────────────────────────────────────────────
CONFLICT_GUARD = '''\
"""
policy_runtime/conflict_guard.py — Policy + RL Conflict Guard

Enforces the invariant: RL signals can NEVER override a safety decision.

Rules (in priority order):
  1. policy = BLOCK  → final = BLOCK, RL output discarded entirely
  2. policy = REWRITE → RL may only refine wording (tone/phrasing)
  3. policy = ALLOW  → RL may adjust tone and structure freely

Output:
  {
    final_decision:      str,    # ALLOW | BLOCK | REWRITE (never changed by RL)
    rl_applied:          bool,   # whether RL hint was used
    rl_scope:            str,    # "none" | "wording" | "tone_structure"
    adjusted_confidence: float,  # base + rl delta (only when rl_applied)
    policy_version:      str,    # forwarded from policy result
    trace_id:            str,
    guard_note:          str,
  }
"""
from typing import Dict, Any

_SCOPE_NONE          = "none"
_SCOPE_WORDING       = "wording"
_SCOPE_TONE_STRUCTURE = "tone_structure"


def apply_conflict_guard(
    policy_result: Dict[str, Any],
    rl_hint: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge a policy result with an RL hint under strict safety dominance.

    Args:
        policy_result: Output of policy_runtime.evaluate() — must contain
                       decision, confidence, trace_id, policy_version.
        rl_hint:       Output of rl_signal.interpret_signal() — must contain
                       adjusted_confidence, pattern_flag, policy_note.

    Returns:
        Merged result dict. final_decision is ALWAYS the policy decision.
    """
    decision   = policy_result["decision"]
    base_conf  = float(policy_result.get("confidence", 0.0))
    trace_id   = policy_result.get("trace_id", "")
    pv         = policy_result.get("policy_version", "unknown")
    rl_delta   = float(rl_hint.get("adjusted_confidence", 0.0))
    rl_flag    = rl_hint.get("pattern_flag", "NOMINAL")
    rl_note    = rl_hint.get("policy_note", "")

    # ── Rule 1: BLOCK — RL is completely ignored ─────────────────────
    if decision == "BLOCK":
        return {
            "final_decision":      "BLOCK",
            "rl_applied":          False,
            "rl_scope":            _SCOPE_NONE,
            "adjusted_confidence": base_conf,
            "policy_version":      pv,
            "trace_id":            trace_id,
            "guard_note": (
                "Policy BLOCK is absolute. RL signal discarded. "
                f"RL flag was: {rl_flag}."
            ),
        }

    # ── Rule 2: REWRITE — RL may refine wording only ─────────────────
    if decision == "REWRITE":
        # Confidence adjustment is allowed but decision stays REWRITE
        adjusted = min(max(base_conf + rl_delta, 0.0), 100.0)
        return {
            "final_decision":      "REWRITE",
            "rl_applied":          rl_delta != 0.0,
            "rl_scope":            _SCOPE_WORDING,
            "adjusted_confidence": adjusted,
            "policy_version":      pv,
            "trace_id":            trace_id,
            "guard_note": (
                f"Policy REWRITE preserved. RL permitted to refine wording only. "
                f"Confidence adjusted by {rl_delta:+.1f} → {adjusted:.1f}. "
                f"RL note: {rl_note}"
            ),
        }

    # ── Rule 3: ALLOW — RL may adjust tone and structure ─────────────
    adjusted = min(max(base_conf + rl_delta, 0.0), 100.0)
    return {
        "final_decision":      "ALLOW",
        "rl_applied":          rl_delta != 0.0,
        "rl_scope":            _SCOPE_TONE_STRUCTURE,
        "adjusted_confidence": adjusted,
        "policy_version":      pv,
        "trace_id":            trace_id,
        "guard_note": (
            f"Policy ALLOW. RL permitted to adjust tone and structure. "
            f"Confidence adjusted by {rl_delta:+.1f} → {adjusted:.1f}. "
            f"RL note: {rl_note}"
        ),
    }
'''

# ── rl_signal.py ─────────────────────────────────────────────────────────────
RL_SIGNAL = '''\
"""
policy_runtime/rl_signal.py — RL Signal Interpretation Layer

Consumes feedback signals from Raj and produces deterministic policy hints.

IMPORTANT: This layer NEVER changes ALLOW/BLOCK decisions directly.
It only adjusts confidence and emits advisory flags that downstream
policy evaluation may consult.

Signal types:
  correction        — Raj explicitly corrected a decision
  refinement        — Raj refined/clarified the output
  implicit_positive — Raj accepted/used the output without complaint
  implicit_negative — Raj ignored, dismissed, or re-asked

Output per call:
  {
    adjusted_confidence: float,   # delta applied to base confidence
    pattern_flag:        str,      # advisory flag for policy layer
    policy_note:         str,      # human-readable explanation
  }
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Any

# ---------------------------------------------------------------------------
# Signal types
# ---------------------------------------------------------------------------

SIGNAL_TYPES = frozenset({
    "correction",
    "refinement",
    "implicit_positive",
    "implicit_negative",
})

# ---------------------------------------------------------------------------
# Thresholds — deterministic, no randomness
# ---------------------------------------------------------------------------

_CORRECTION_SENSITIVITY_BOOST  = 10.0   # per correction hit
_REFINEMENT_CLARIFY_THRESHOLD  = 3      # refinements before CLARIFY flag
_POSITIVE_BASELINE_THRESHOLD   = 5      # positives before STABLE flag
_NEGATIVE_DRIFT_THRESHOLD      = 3      # negatives before DRIFT flag
_WINDOW                        = 10     # rolling window size
_MAX_BOOST                     = 25.0   # cap on upward confidence delta
_MAX_PENALTY                   = -20.0  # floor on downward confidence delta

# ---------------------------------------------------------------------------
# Pattern flags (advisory only)
# ---------------------------------------------------------------------------

FLAG_INCREASE_SENSITIVITY = "INCREASE_SENSITIVITY"   # repeated corrections
FLAG_REQUIRE_CLARIFICATION = "REQUIRE_CLARIFICATION" # frequent refinements
FLAG_MAINTAIN_BASELINE    = "MAINTAIN_BASELINE"      # repeated positives
FLAG_MONITOR_DRIFT        = "MONITOR_DRIFT"          # repeated negatives
FLAG_NOMINAL              = "NOMINAL"                # no pattern detected

# ---------------------------------------------------------------------------
# Per-user signal window
# ---------------------------------------------------------------------------

@dataclass
class _UserWindow:
    signals: Deque[str] = field(default_factory=lambda: deque(maxlen=_WINDOW))

    def push(self, signal_type: str) -> None:
        self.signals.append(signal_type)

    def count(self, signal_type: str) -> int:
        return sum(1 for s in self.signals if s == signal_type)


# Module-level registry — keyed by user_id
_windows: Dict[str, _UserWindow] = {}


def _get_window(user_id: str) -> _UserWindow:
    if user_id not in _windows:
        _windows[user_id] = _UserWindow()
    return _windows[user_id]


# ---------------------------------------------------------------------------
# Core interpretation
# ---------------------------------------------------------------------------

def interpret_signal(
    signal_type: str,
    user_id: str,
    base_confidence: float = 0.0,
) -> Dict[str, Any]:
    """
    Interpret a single RL signal and return policy hints.

    Args:
        signal_type:      One of correction | refinement |
                          implicit_positive | implicit_negative
        user_id:          Identifier for the signal source (Raj\'s user ID).
        base_confidence:  Current confidence value from the policy layer
                          (0–100). Used only to compute the adjusted delta.

    Returns:
        {
            adjusted_confidence: float  — delta to add to base_confidence
                                          (positive = more sensitive,
                                           negative = less sensitive).
                                          Does NOT replace the base value.
            pattern_flag:        str    — advisory flag.
            policy_note:         str    — human-readable explanation.
        }
    """
    if signal_type not in SIGNAL_TYPES:
        return {
            "adjusted_confidence": 0.0,
            "pattern_flag":        FLAG_NOMINAL,
            "policy_note":         f"Unknown signal type \'{signal_type}\'; no adjustment applied.",
        }

    window = _get_window(user_id)
    window.push(signal_type)

    corrections = window.count("correction")
    refinements  = window.count("refinement")
    positives    = window.count("implicit_positive")
    negatives    = window.count("implicit_negative")

    # ── Rule 1: repeated correction → increase sensitivity ──────────
    if corrections >= 2:
        delta = min(corrections * _CORRECTION_SENSITIVITY_BOOST, _MAX_BOOST)
        return {
            "adjusted_confidence": delta,
            "pattern_flag":        FLAG_INCREASE_SENSITIVITY,
            "policy_note": (
                f"{corrections} corrections in last {_WINDOW} signals. "
                "Sensitivity raised: policy engine will apply stricter matching."
            ),
        }

    # ── Rule 2: frequent refinement → require clarification ─────────
    if refinements >= _REFINEMENT_CLARIFY_THRESHOLD:
        return {
            "adjusted_confidence": 0.0,
            "pattern_flag":        FLAG_REQUIRE_CLARIFICATION,
            "policy_note": (
                f"{refinements} refinements in last {_WINDOW} signals. "
                "Output ambiguity detected: clarification step recommended before acting."
            ),
        }

    # ── Rule 3: repeated positive → maintain baseline ───────────────
    if positives >= _POSITIVE_BASELINE_THRESHOLD:
        return {
            "adjusted_confidence": 0.0,
            "pattern_flag":        FLAG_MAINTAIN_BASELINE,
            "policy_note": (
                f"{positives} positive signals in last {_WINDOW}. "
                "Policy baseline is performing well; no adjustment needed."
            ),
        }

    # ── Rule 4: repeated negative → monitor for drift ───────────────
    if negatives >= _NEGATIVE_DRIFT_THRESHOLD:
        delta = max(negatives * -5.0, _MAX_PENALTY)
        return {
            "adjusted_confidence": delta,
            "pattern_flag":        FLAG_MONITOR_DRIFT,
            "policy_note": (
                f"{negatives} negative signals in last {_WINDOW}. "
                "Confidence reduced: policy outputs may be drifting from expectations."
            ),
        }

    # ── Default: single signal, no pattern yet ───────────────────────
    _single_deltas = {
        "correction":        5.0,
        "refinement":        2.0,
        "implicit_positive": 0.0,
        "implicit_negative": -3.0,
    }
    delta = _single_deltas[signal_type]
    return {
        "adjusted_confidence": delta,
        "pattern_flag":        FLAG_NOMINAL,
        "policy_note": (
            f"Single {signal_type} signal recorded for user \'{user_id}\'. "
            f"Confidence delta: {delta:+.1f}. No pattern threshold reached yet."
        ),
    }


def reset_user_window(user_id: str) -> None:
    """Clear signal history for a user (test / session reset use only)."""
    _windows.pop(user_id, None)
'''

# ── __init__.py ───────────────────────────────────────────────────────────────
INIT = '''\
from .runtime import evaluate
from .adapters import validate_for_mitra, validate_for_creator_core, validate_for_bhiv
from .rl_signal import interpret_signal, reset_user_window
from .conflict_guard import apply_conflict_guard

__all__ = [
    "evaluate",
    "validate_for_mitra",
    "validate_for_creator_core",
    "validate_for_bhiv",
    "interpret_signal",
    "reset_user_window",
    "apply_conflict_guard",
]
'''

files = {
    "runtime.py":        RUNTIME,
    "adapters.py":       ADAPTERS,
    "conflict_guard.py": CONFLICT_GUARD,
    "rl_signal.py":      RL_SIGNAL,
    "__init__.py":       INIT,
}

for name, content in files.items():
    path = os.path.join(BASE, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  created: policy_runtime/{name}")

print("\npolicy_runtime/ package ready.")
