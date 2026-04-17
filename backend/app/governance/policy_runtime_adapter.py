"""
policy_runtime_adapter.py — Cross-System Safety Adapter (Embedded in Mitra)

Two-gate validation:
  Gate 1: PolicyEngine  — JSON policy rules (fast, configurable)
  Gate 2: BehaviorValidator — pattern library (deep, 100+ patterns)

If Gate 1 blocks/rewrites, Gate 2 is skipped.
If Gate 1 allows, Gate 2 runs as second gate.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from app.governance.behavior_validator import validate_behavior, BehaviorValidator, Decision
from app.governance.policy_engine import evaluate_policy, PolicyDecision


@dataclass
class AdapterRequest:
    text: str
    system: str          # mitra | creator_core | bhiv
    region: Optional[str] = None
    caller_id: Optional[str] = None


@dataclass
class AdapterResponse:
    decision: str        # ALLOW | BLOCK | REWRITE
    category: str
    confidence: float
    trace_id: str
    rule_id: str
    reason: str
    system: str
    safe_output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision":    self.decision,
            "category":    self.category,
            "confidence":  self.confidence,
            "trace_id":    self.trace_id,
            "rule_id":     self.rule_id,
            "reason":      self.reason,
            "system":      self.system,
            "safe_output": self.safe_output,
        }


class PolicyRuntimeAdapter:
    """
    Single stable interface for all BHIV systems to invoke safety validation.

    Evaluation order:
      1. policy_engine  — JSON policy rules (fast, configurable)
      2. behavior_validator — pattern library (deep, 100+ patterns)

    If policy_engine blocks/rewrites, behavior_validator is skipped.
    If policy_engine allows, behavior_validator runs as second gate.
    """

    SYSTEM_IDS = {"mitra", "creator_core", "bhiv"}

    def validate(self, request: AdapterRequest) -> AdapterResponse:
        system = request.system if request.system in self.SYSTEM_IDS else "bhiv"

        # Gate 1: Policy engine (JSON rules — fast)
        policy_result = evaluate_policy(
            text=request.text,
            system=system,
            region=request.region,
        )

        if policy_result["decision"] in ("BLOCK", "REWRITE"):
            return AdapterResponse(
                decision=policy_result["decision"],
                category=policy_result["category"],
                confidence=policy_result["confidence"],
                trace_id=policy_result["trace_id"],
                rule_id=policy_result["rule_id"],
                reason=policy_result["reason"],
                system=system,
                safe_output=None,
            )

        # Gate 2: Behavior validator (pattern library — deep)
        validator_result = validate_behavior("auto", request.text)

        decision_map = {
            "hard_deny":    "BLOCK",
            "soft_rewrite": "REWRITE",
            "allow":        "ALLOW",
        }
        decision = decision_map.get(validator_result["decision"], "ALLOW")

        return AdapterResponse(
            decision=decision,
            category=validator_result["risk_category"],
            confidence=validator_result["confidence"],
            trace_id=validator_result["trace_id"],
            rule_id=f"BV-{validator_result['risk_category'].upper()}",
            reason=validator_result["explanation"],
            system=system,
            safe_output=validator_result.get("safe_output") if decision != "ALLOW" else None,
        )


# -----------------------------------------------------------------------
# Public API functions
# -----------------------------------------------------------------------

_adapter = PolicyRuntimeAdapter()


def validate_for_mitra(
    text: str,
    region: Optional[str] = None,
    caller_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Entry point for Mitra assistant pipeline."""
    return _adapter.validate(
        AdapterRequest(text=text, system="mitra", region=region, caller_id=caller_id)
    ).to_dict()


def validate_for_bhiv(
    text: str,
    system: str = "bhiv",
    region: Optional[str] = None,
    caller_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generic entry point for any BHIV product."""
    return _adapter.validate(
        AdapterRequest(text=text, system=system, region=region, caller_id=caller_id)
    ).to_dict()
