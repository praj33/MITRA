"""
enforcement_adapter.py — Maps validator decisions to enforcement states (Embedded in Mitra)

Maps BehaviorValidator decisions to enforcement states with safety-first resolution.
"""

from enum import Enum
from app.governance.behavior_validator import BehaviorValidator, Decision, RiskCategory
import hashlib


class EnforcementState(Enum):
    """Enforcement states — safety-first resolution"""
    ALLOW = "allow"
    MONITOR = "monitor"
    BLOCK = "block"
    ESCALATE = "escalate"


class Severity(Enum):
    """Severity levels for enforcement decisions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnforcementAdapter:
    """Maps validator decisions to enforcement actions"""

    def __init__(self):
        self.validator = BehaviorValidator()

    def map_validator_to_enforcement(self, text, category="general"):
        """
        Map validator decision to enforcement state.

        Returns:
            dict with decision, severity, confidence, trace_id
        """
        # Get validator decision
        validator_result = self.validator.validate_behavior(
            intent="auto",
            conversational_output=text,
            age_gate_status=False,
            region_rule_status=None,
            platform_policy_state=None,
            karma_bias_input=0.5
        )

        validator_decision = validator_result.decision.value
        risk_category = validator_result.risk_category.value
        trace_id = validator_result.trace_id

        # Map to enforcement state with safety-first resolution
        if validator_decision == Decision.ALLOW.value:
            enforcement_decision = EnforcementState.ALLOW.value
            severity = Severity.LOW.value
            confidence = 0.95

        elif validator_decision == Decision.SOFT_REWRITE.value:
            enforcement_decision = EnforcementState.MONITOR.value
            severity = Severity.MEDIUM.value
            confidence = 0.85

        elif validator_decision == Decision.HARD_DENY.value:
            # Safety-first: escalate critical categories
            if risk_category in [RiskCategory.ILLEGAL_INTENT_PROBING.value,
                               RiskCategory.SEXUAL_ESCALATION_ATTEMPT.value,
                               RiskCategory.YOUTH_RISK_BEHAVIOR.value]:
                enforcement_decision = EnforcementState.ESCALATE.value
                severity = Severity.CRITICAL.value
                confidence = 0.98
            else:
                enforcement_decision = EnforcementState.BLOCK.value
                severity = Severity.HIGH.value
                confidence = 0.92

            # High confidence escalation
            if validator_result.confidence > 95.0 and enforcement_decision == EnforcementState.BLOCK.value:
                enforcement_decision = EnforcementState.ESCALATE.value
                severity = Severity.CRITICAL.value
                confidence = 0.99
        else:
            # Safety-first fallback
            enforcement_decision = EnforcementState.BLOCK.value
            severity = Severity.HIGH.value
            confidence = 0.90

        return {
            "decision": enforcement_decision,
            "severity": severity,
            "confidence": confidence,
            "trace_id": trace_id,
        }
