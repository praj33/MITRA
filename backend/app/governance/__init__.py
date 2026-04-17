"""
Mitra Governance Package — Embedded from AI-Being-Governance-Layer

This package contains the complete Akanksha policy runtime, behavior validation,
mediation system, and enforcement adapter. These are embedded directly into the
Mitra pipeline — NOT called as external services.

Components:
  - PolicyEngine: JSON-configurable policy rules (content/behavior/regional)
  - BehaviorValidator: 100+ pattern canonical validator with 7 risk categories
  - PolicyRuntimeAdapter: Two-gate validation (PolicyEngine → BehaviorValidator)
  - MediationSystem: Inbound/outbound mediation (quiet hours, contact limits)
  - EnforcementAdapter: Maps validator decisions to enforcement states
"""

from app.governance.policy_runtime_adapter import (
    PolicyRuntimeAdapter,
    validate_for_mitra,
    validate_for_bhiv,
)
from app.governance.mediation_system import (
    MediationSystem,
    MediationDecision,
    InboundMessage,
    OutboundAction,
    MediationResult,
)
from app.governance.enforcement_adapter import (
    EnforcementAdapter,
    EnforcementState,
)

__all__ = [
    "PolicyRuntimeAdapter",
    "validate_for_mitra",
    "validate_for_bhiv",
    "MediationSystem",
    "MediationDecision",
    "InboundMessage",
    "OutboundAction",
    "MediationResult",
    "EnforcementAdapter",
    "EnforcementState",
]
