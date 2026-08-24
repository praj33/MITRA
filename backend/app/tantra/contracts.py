"""
TANTRA Canonical Execution Contracts
=====================================
Phase 1 — Runtime Contract Lock

These contracts are the ONLY supported execution interface for MITRA.
No component may bypass these contracts.

Every MITRA execution request MUST conform to these schemas.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExecutionStatus(str, Enum):
    """Lifecycle states of a TANTRA execution."""
    PENDING = "pending"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    DELAYED = "delayed"
    REWRITE = "rewrite"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    TERMINATED = "terminated"


class CapabilityType(str, Enum):
    """Types of capabilities TANTRA can invoke."""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    CALENDAR = "calendar"
    REMINDER = "reminder"
    EMS = "ems"
    DEVICE_GATEWAY = "device_gateway"
    ECOSYSTEM_PRODUCT = "ecosystem_product"
    LLM_INVOCATION = "llm_invocation"
    CUSTOM = "custom"


class ExecutionDecision(str, Enum):
    """Enforcement decisions propagated through TANTRA."""
    ALLOW = "ALLOW"
    REWRITE = "REWRITE"
    DELAY = "DELAY"
    BLOCK = "BLOCK"
    TERMINATE = "TERMINATE"


# ---------------------------------------------------------------------------
# Trace & Replay Metadata
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TraceMetadata:
    """
    Distributed trace metadata.
    Generated deterministically from request payload via SHA-256.
    Follows execution through every stage.
    """
    trace_id: str
    parent_trace_id: Optional[str] = None
    span_id: str = ""
    source: str = "mitra"
    started_at: str = ""
    enforcement_category: str = "REQUEST"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def generate(
        input_payload: Dict[str, Any],
        enforcement_category: str = "REQUEST",
        source: str = "mitra",
    ) -> "TraceMetadata":
        canonical = json.dumps(
            {"input_payload": input_payload, "category": enforcement_category},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")
        trace_id = f"trace_{hashlib.sha256(canonical).hexdigest()[:16]}"
        span_id = hashlib.sha256(f"span:{trace_id}".encode()).hexdigest()[:12]
        return TraceMetadata(
            trace_id=trace_id,
            span_id=span_id,
            source=source,
            started_at=datetime.now(timezone.utc).isoformat(),
            enforcement_category=enforcement_category,
        )


@dataclass(frozen=True)
class ReplayMetadata:
    """
    Metadata for replaying an execution.
    Stored in Bucket alongside execution artifacts.
    """
    original_trace_id: str
    replay_count: int = 0
    last_replayed_at: Optional[str] = None
    replay_hash: Optional[str] = None
    integrity_verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Execution Contracts
# ---------------------------------------------------------------------------

@dataclass
class ExecutionContext:
    """
    Contextual envelope for every execution request.
    Carries platform, user, session, enforcement, and system context.
    """
    platform: str = "web"
    device: str = "unknown"
    session_id: str = ""
    user_id: str = "anonymous"
    voice_input: bool = False
    preferred_language: str = "auto"
    detected_language: Optional[str] = None
    enforcement_decision: ExecutionDecision = ExecutionDecision.ALLOW
    enforcement_reason_code: str = ""
    enforcement_scope: str = "both"
    policy_decision: Optional[Dict[str, Any]] = None
    rl_signal: Optional[Dict[str, Any]] = None
    bhiv_context: Optional[Dict[str, Any]] = None
    authenticated_user_context: Optional[Dict[str, Any]] = None
    bucket_log_reference: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["enforcement_decision"] = self.enforcement_decision.value
        return d


@dataclass
class ExecutionRequest:
    """
    The canonical execution request — the ONLY supported execution interface.
    Created by MITRA Control Plane, consumed by TANTRA Runtime.
    """
    trace_metadata: TraceMetadata
    context: ExecutionContext
    capability_type: CapabilityType
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    action_data: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 30
    max_retries: int = 3
    priority: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_metadata": self.trace_metadata.to_dict(),
            "context": self.context.to_dict(),
            "capability_type": self.capability_type.value,
            "action": self.action,
            "payload": self.payload,
            "action_data": self.action_data,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "priority": self.priority,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_legacy(
        *,
        action_type: str,
        action_data: Dict[str, Any],
        trace_id: str,
        enforcement_decision: Any,
        context: Optional[ExecutionContext] = None,
    ) -> "ExecutionRequest":
        """Construct from legacy ExecutionService parameters."""
        from app.external.enforcement.enforcement_verdict import EnforcementVerdict

        if isinstance(enforcement_decision, EnforcementVerdict):
            decision_str = enforcement_decision.decision
            reason_code = enforcement_decision.reason_code
            scope = enforcement_decision.scope
        elif isinstance(enforcement_decision, dict):
            decision_str = enforcement_decision.get("decision", "BLOCK")
            reason_code = enforcement_decision.get("reason_code", "LEGACY")
            scope = enforcement_decision.get("scope", "both")
        else:
            decision_str = str(enforcement_decision or "BLOCK")
            reason_code = "LEGACY_UNTYPED"
            scope = "both"

        try:
            decision = ExecutionDecision(decision_str.upper())
        except ValueError:
            decision = ExecutionDecision.BLOCK

        capability_map = {
            "whatsapp": CapabilityType.WHATSAPP,
            "email": CapabilityType.EMAIL,
            "telegram": CapabilityType.TELEGRAM,
            "instagram": CapabilityType.INSTAGRAM,
            "calendar": CapabilityType.CALENDAR,
            "reminder": CapabilityType.REMINDER,
            "ems": CapabilityType.EMS,
            "device_gateway": CapabilityType.DEVICE_GATEWAY,
        }

        if context is None:
            context = ExecutionContext()

        return ExecutionRequest(
            trace_metadata=TraceMetadata(
                trace_id=trace_id,
                source="mitra_control_plane",
                started_at=datetime.now(timezone.utc).isoformat(),
            ),
            context=ExecutionContext(
                platform=context.platform,
                device=context.device,
                session_id=context.session_id,
                user_id=context.user_id,
                enforcement_decision=decision,
                enforcement_reason_code=reason_code,
                enforcement_scope=scope,
                policy_decision=context.policy_decision,
                rl_signal=context.rl_signal,
                bhiv_context=context.bhiv_context,
                authenticated_user_context=context.authenticated_user_context,
                bucket_log_reference=context.bucket_log_reference,
            ),
            capability_type=capability_map.get(action_type.lower(), CapabilityType.CUSTOM),
            action=action_data.get("action", "execute"),
            payload=action_data,
            action_data=action_data,
        )


@dataclass
class CapabilityInvocation:
    """
    Records a single capability invocation within an execution.
    Stored in Bucket for replay and observability.
    """
    invocation_id: str
    capability_type: CapabilityType
    action: str
    status: ExecutionStatus
    started_at: str
    completed_at: Optional[str] = None
    latency_ms: float = 0.0
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    gateway_auth_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "capability_type": self.capability_type.value,
            "action": self.action,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "latency_ms": round(self.latency_ms, 2),
            "result_data": self.result_data,
            "error": self.error,
            "retry_count": self.retry_count,
            "gateway_auth_token": self.gateway_auth_token,
        }


@dataclass
class FailureContract:
    """
    Structured failure metadata.
    Every failure in TANTRA is captured with full context.
    """
    failure_id: str
    failure_type: str
    failure_code: str
    message: str
    capability_type: Optional[CapabilityType] = None
    trace_id: str = ""
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_retryable: bool = False
    retry_after_ms: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.capability_type:
            d["capability_type"] = self.capability_type.value
        return d


@dataclass
class ExecutionResult:
    """
    The canonical execution result — returned by TANTRA Runtime.
    Contains status, response data, invocations, failures, and telemetry.
    """
    trace_metadata: TraceMetadata
    status: ExecutionStatus
    decision: ExecutionDecision
    response_data: Dict[str, Any] = field(default_factory=dict)
    invocations: List[CapabilityInvocation] = field(default_factory=list)
    failures: List[FailureContract] = field(default_factory=list)
    replay_metadata: Optional[ReplayMetadata] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)
    completed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_latency_ms: float = 0.0
    integrity_hash: str = ""

    def __post_init__(self):
        if not self.integrity_hash:
            self.integrity_hash = self._compute_integrity_hash()

    def _compute_integrity_hash(self) -> str:
        canonical = {
            "trace_id": self.trace_metadata.trace_id,
            "status": self.status.value,
            "decision": self.decision.value,
            "invocation_count": len(self.invocations),
            "failure_count": len(self.failures),
            "completed_at": self.completed_at,
        }
        blob = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_metadata": self.trace_metadata.to_dict(),
            "status": self.status.value,
            "decision": self.decision.value,
            "response_data": self.response_data,
            "invocations": [i.to_dict() for i in self.invocations],
            "failures": [f.to_dict() for f in self.failures],
            "replay_metadata": self.replay_metadata.to_dict() if self.replay_metadata else None,
            "telemetry": self.telemetry,
            "completed_at": self.completed_at,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "integrity_hash": self.integrity_hash,
        }

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert to the format expected by existing orchestrator response builders."""
        result = {
            "status": "success" if self.status == ExecutionStatus.COMPLETED else self.status.value,
            "trace_id": self.trace_metadata.trace_id,
            "timestamp": self.completed_at,
            "service": "tantra_runtime",
            "execution_proof": {
                "trace_id": self.trace_metadata.trace_id,
                "status": self.status.value,
                "decision": self.decision.value,
                "integrity_hash": self.integrity_hash,
                "invocation_count": len(self.invocations),
            },
        }
        if self.response_data:
            result.update(self.response_data)
        if self.failures:
            result["error"] = self.failures[0].message
        return result
