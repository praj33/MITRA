"""
TANTRA InsightFlow Telemetry
=============================
Generates observability signals for every execution.
No execution should be invisible.

Captures:
- Execution timeline events
- Lifecycle signals
- Performance metrics
- Failure telemetry
- Provenance metadata
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.tantra.contracts import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    TraceMetadata,
)


@dataclass
class TelemetryEvent:
    """A single telemetry event."""
    event_id: str
    event_type: str
    trace_id: str
    timestamp: str
    data: Dict[str, Any]
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "severity": self.severity,
        }


@dataclass
class InsightFlowRecord:
    """
    Complete InsightFlow telemetry record for an execution.
    Stored in Bucket as a dedicated stage.
    """
    trace_id: str
    events: List[TelemetryEvent] = field(default_factory=list)
    execution_started_at: Optional[str] = None
    execution_completed_at: Optional[str] = None
    total_latency_ms: float = 0.0
    status: str = "pending"
    telemetry_hash: str = ""

    def compute_hash(self) -> str:
        canonical = {
            "trace_id": self.trace_id,
            "event_count": len(self.events),
            "status": self.status,
        }
        blob = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        self.telemetry_hash = self.compute_hash()
        return {
            "trace_id": self.trace_id,
            "events": [e.to_dict() for e in self.events],
            "execution_started_at": self.execution_started_at,
            "execution_completed_at": self.execution_completed_at,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "status": self.status,
            "event_count": len(self.events),
            "telemetry_hash": self.telemetry_hash,
        }


class InsightFlow:
    """
    Telemetry engine for TANTRA executions.
    Generates events at every stage of the execution lifecycle.
    """

    @staticmethod
    def _event_id() -> str:
        raw = f"evt:{datetime.now(timezone.utc).isoformat()}:{hash(str(datetime.now()))}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def on_execution_received(request: ExecutionRequest) -> TelemetryEvent:
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="execution.received",
            trace_id=request.trace_metadata.trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "capability_type": request.capability_type.value,
                "action": request.action,
                "platform": request.context.platform,
                "enforcement_decision": request.context.enforcement_decision.value,
                "timeout_seconds": request.timeout_seconds,
            },
        )

    @staticmethod
    def on_enforcement_evaluated(
        trace_id: str,
        decision: str,
        reason_code: str,
        latency_ms: float = 0.0,
    ) -> TelemetryEvent:
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="enforcement.evaluated",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "decision": decision,
                "reason_code": reason_code,
                "latency_ms": round(latency_ms, 2),
            },
        )

    @staticmethod
    def on_capability_dispatched(
        trace_id: str,
        capability_type: str,
        action: str,
    ) -> TelemetryEvent:
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="capability.dispatched",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "capability_type": capability_type,
                "action": action,
            },
        )

    @staticmethod
    def on_capability_completed(
        trace_id: str,
        capability_type: str,
        action: str,
        status: str,
        latency_ms: float,
    ) -> TelemetryEvent:
        severity = "info" if status == "completed" else "warning"
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="capability.completed",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "capability_type": capability_type,
                "action": action,
                "status": status,
                "latency_ms": round(latency_ms, 2),
            },
            severity=severity,
        )

    @staticmethod
    def on_failure(
        trace_id: str,
        failure_type: str,
        failure_code: str,
        message: str,
        is_retryable: bool = False,
    ) -> TelemetryEvent:
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="execution.failed",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "failure_type": failure_type,
                "failure_code": failure_code,
                "message": message,
                "is_retryable": is_retryable,
            },
            severity="error",
        )

    @staticmethod
    def on_execution_completed(result: ExecutionResult) -> TelemetryEvent:
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="execution.completed",
            trace_id=result.trace_metadata.trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "status": result.status.value,
                "decision": result.decision.value,
                "total_latency_ms": round(result.total_latency_ms, 2),
                "invocation_count": len(result.invocations),
                "failure_count": len(result.failures),
                "integrity_hash": result.integrity_hash,
            },
        )

    @staticmethod
    def on_bucket_logged(
        trace_id: str,
        stage: str,
        artifact_locator: str,
    ) -> TelemetryEvent:
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="bucket.logged",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "stage": stage,
                "artifact_locator": artifact_locator,
            },
        )

    @staticmethod
    def on_chat_received(
        trace_id: str,
        platform: str = "web",
        detected_language: str = "en",
    ) -> TelemetryEvent:
        """Telemetry event when a chat/LLM request is received (non-TANTRA path)."""
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="chat.received",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "platform": platform,
                "detected_language": detected_language,
                "path": "llm_chat",
            },
        )

    @staticmethod
    def on_chat_completed(
        trace_id: str,
        response_length: int,
        latency_ms: float,
        provider: str = "unknown",
        intent: str = "general",
    ) -> TelemetryEvent:
        """Telemetry event when a chat/LLM response is generated (non-TANTRA path)."""
        severity = "info" if response_length > 0 else "warning"
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="chat.completed",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "response_length": response_length,
                "latency_ms": round(latency_ms, 2),
                "provider": provider,
                "intent": intent,
                "path": "llm_chat",
            },
            severity=severity,
        )

    @staticmethod
    def on_chat_failed(
        trace_id: str,
        error_type: str,
        error_message: str,
    ) -> TelemetryEvent:
        """Telemetry event when a chat/LLM response fails (non-TANTRA path)."""
        return TelemetryEvent(
            event_id=InsightFlow._event_id(),
            event_type="chat.failed",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "error_type": error_type,
                "error_message": error_message,
                "path": "llm_chat",
            },
            severity="error",
        )

    @staticmethod
    def build_record(
        request: ExecutionRequest,
        result: ExecutionResult,
        events: List[TelemetryEvent],
    ) -> InsightFlowRecord:
        """Build a complete InsightFlow record for Bucket storage."""
        return InsightFlowRecord(
            trace_id=request.trace_metadata.trace_id,
            events=events,
            execution_started_at=request.created_at,
            execution_completed_at=result.completed_at,
            total_latency_ms=result.total_latency_ms,
            status=result.status.value,
        )

    @staticmethod
    def build_chat_record(
        trace_id: str,
        events: List[TelemetryEvent],
        started_at: str,
        completed_at: str,
        total_latency_ms: float,
        status: str = "completed",
    ) -> InsightFlowRecord:
        """Build an InsightFlow record for chat/LLM responses (non-TANTRA path)."""
        return InsightFlowRecord(
            trace_id=trace_id,
            events=events,
            execution_started_at=started_at,
            execution_completed_at=completed_at,
            total_latency_ms=total_latency_ms,
            status=status,
        )
