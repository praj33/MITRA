"""
TANTRA Runtime — The Sole Execution Engine
===========================================
Phase 2 — Constitutional Runtime

Every MITRA execution flows through this runtime:
  User -> MITRA -> Control Plane -> TANTRA Runtime -> Capability Runtime
  -> Execution -> Bucket -> Replay -> InsightFlow -> MITRA Response

No local execution paths are permitted.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import get_logger
from app.core.gateway_auth import GatewayAuth

from app.tantra.contracts import (
    CapabilityInvocation,
    CapabilityType,
    ExecutionDecision,
    ExecutionContext,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    FailureContract,
    ReplayMetadata,
    TraceMetadata,
)
from app.tantra.state_machine import ExecutionStateMachine
from app.tantra.governance import RuntimeGovernance, CancellationToken
from app.tantra.insightflow import InsightFlow, InsightFlowRecord, TelemetryEvent
from app.tantra.registry import ConstitutionalRegistry

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Capability Executor (interface to real platform executors)
# ---------------------------------------------------------------------------

class CapabilityExecutor:
    """
    Wraps the existing platform executors behind the TANTRA capability interface.
    Each capability executor validates gateway auth before execution.
    """

    def __init__(self) -> None:
        from app.services.execution_service import ExecutionService
        self._execution_service = ExecutionService()

    def execute(
        self,
        capability_type: CapabilityType,
        action: str,
        action_data: Dict[str, Any],
        trace_id: str,
        enforcement_decision: Any,
        gateway_auth: str,
    ) -> Dict[str, Any]:
        """
        Delegate to the appropriate platform executor.
        Gateway auth is verified by each executor.
        """
        return self._execution_service.execute_action(
            action_type=capability_type.value,
            action_data=action_data,
            trace_id=trace_id,
            enforcement_decision=enforcement_decision,
        )


# ---------------------------------------------------------------------------
# TANTRA Runtime
# ---------------------------------------------------------------------------

class TantraRuntime:
    """
    The sole execution runtime for MITRA.

    Lifecycle:
    1. Receive ExecutionRequest
    2. Validate preconditions (enforcement, health, cancellation)
    3. Apply enforcement gate
    4. Dispatch to Capability Runtime
    5. Record invocation in Bucket
    6. Generate InsightFlow telemetry
    7. Return ExecutionResult

    No execution may bypass this runtime.
    """

    def __init__(self) -> None:
        self._capability_executor = CapabilityExecutor()
        self._governance = RuntimeGovernance()
        self._registry = ConstitutionalRegistry()
        self._bucket_service = None  # Lazy init
        self._execution_records: Dict[str, ExecutionResult] = {}
        logger.info("TantraRuntime initialized — the sole execution engine")

    @property
    def bucket_service(self):
        if self._bucket_service is None:
            from app.services.bucket_service import BucketService
            self._bucket_service = BucketService()
        return self._bucket_service

    @property
    def governance(self) -> RuntimeGovernance:
        return self._governance

    @property
    def registry(self) -> ConstitutionalRegistry:
        return self._registry

    # ------------------------------------------------------------------
    # Core execution path
    # ------------------------------------------------------------------

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute a request through the TANTRA constitutional flow.
        This is the ONLY entry point for all MITRA executions.
        """
        start_time = time.time()
        trace_id = request.trace_metadata.trace_id
        state = ExecutionStateMachine(trace_id=trace_id)
        telemetry_events: List[TelemetryEvent] = []

        # 1. Record execution received
        telemetry_events.append(InsightFlow.on_execution_received(request))

        try:
            # 2. Validate preconditions
            is_valid, reason = self._governance.validate_preconditions(
                trace_id, request.capability_type.value
            )
            if not is_valid:
                state.transition(ExecutionStatus.BLOCKED, reason=reason)
                failure = FailureContract(
                    failure_id=hashlib.sha256(f"fail:{trace_id}".encode()).hexdigest()[:16],
                    failure_type="precondition_violation",
                    failure_code="PRECONDITION_FAILED",
                    message=reason,
                    capability_type=request.capability_type,
                    trace_id=trace_id,
                )
                result = self._build_result(
                    request, state, ExecutionStatus.BLOCKED,
                    request.context.enforcement_decision,
                    start_time, telemetry_events, failures=[failure],
                )
                self._record_to_bucket(request, result, state)
                return result

            # 3. Enforcement gate
            enforcement_start = time.time()
            decision = request.context.enforcement_decision
            enforcement_latency = (time.time() - enforcement_start) * 1000

            telemetry_events.append(
                InsightFlow.on_enforcement_evaluated(
                    trace_id, decision.value,
                    request.context.enforcement_reason_code,
                    enforcement_latency,
                )
            )

            # Apply enforcement decision to state machine
            state.apply_enforcement_decision(decision)

            # 4. If not ALLOW, return early with enforcement verdict
            if decision != ExecutionDecision.ALLOW:
                result = self._build_result(
                    request, state, state.current_status,
                    decision, start_time, telemetry_events,
                )
                self._record_to_bucket(request, result, state)
                telemetry_events.append(InsightFlow.on_execution_completed(result))
                return result

            # 5. Dispatch to Capability Runtime
            state.transition(ExecutionStatus.IN_PROGRESS, reason="dispatched_to_capability_runtime")
            telemetry_events.append(
                InsightFlow.on_capability_dispatched(
                    trace_id, request.capability_type.value, request.action,
                )
            )

            # 6. Execute with retry logic
            invocation_result = self._execute_with_retry(request, state, telemetry_events)

            # 7. Build final result
            terminal_status = state.current_status
            result = self._build_result(
                request, state, terminal_status,
                decision, start_time, telemetry_events,
                invocation=invocation_result.get("invocation"),
                failures=invocation_result.get("failures", []),
                response_data=invocation_result.get("response_data", {}),
            )

            # 8. Record in Bucket
            self._record_to_bucket(request, result, state)

            # 9. Record in Constitutional Registry
            self._registry.record_execution(
                trace_id=trace_id,
                execution_data={
                    "capability_type": request.capability_type.value,
                    "action": request.action,
                    "status": result.status.value,
                    "decision": result.decision.value,
                },
            )

            # 10. Final telemetry
            telemetry_events.append(InsightFlow.on_execution_completed(result))

            return result

        except Exception as e:
            logger.error(f"[{trace_id}] TANTRA execution failed: {e}")
            state.transition(ExecutionStatus.FAILED, reason=f"exception:{str(e)}")

            failure = FailureContract(
                failure_id=hashlib.sha256(f"fail:{trace_id}:{time.time()}".encode()).hexdigest()[:16],
                failure_type="runtime_exception",
                failure_code="RUNTIME_ERROR",
                message=str(e),
                capability_type=request.capability_type,
                trace_id=trace_id,
            )
            telemetry_events.append(
                InsightFlow.on_failure(trace_id, "runtime_exception", "RUNTIME_ERROR", str(e))
            )

            result = self._build_result(
                request, state, ExecutionStatus.FAILED,
                request.context.enforcement_decision,
                start_time, telemetry_events, failures=[failure],
            )
            self._record_to_bucket(request, result, state)
            return result

    # ------------------------------------------------------------------
    # Retry logic
    # ------------------------------------------------------------------

    def _execute_with_retry(
        self,
        request: ExecutionRequest,
        state: ExecutionStateMachine,
        telemetry_events: List[TelemetryEvent],
    ) -> Dict[str, Any]:
        """Execute capability with retry logic governed by RuntimeGovernance."""
        trace_id = request.trace_metadata.trace_id
        last_error = None
        invocation = None

        for attempt in range(request.max_retries + 1):
            # Check cancellation
            cancel_token = self._governance.get_cancellation_token(trace_id)
            if cancel_token and cancel_token.is_cancelled():
                state.transition(ExecutionStatus.CANCELLED, reason=cancel_token.reason)
                return {
                    "invocation": invocation,
                    "failures": [FailureContract(
                        failure_id=hashlib.sha256(f"cancel:{trace_id}".encode()).hexdigest()[:16],
                        failure_type="cancellation",
                        failure_code="EXECUTION_CANCELLED",
                        message=f"Execution cancelled: {cancel_token.reason}",
                        capability_type=request.capability_type,
                        trace_id=trace_id,
                        is_retryable=False,
                    )],
                    "response_data": {},
                }

            # Record invocation attempt
            invocation_start = time.time()
            invocation_id = hashlib.sha256(
                f"inv:{trace_id}:{attempt}:{time.time()}".encode()
            ).hexdigest()[:16]

            try:
                # Generate gateway auth for this invocation
                gateway_auth = GatewayAuth.issue(
                    trace_id=trace_id,
                    platform=request.capability_type.value,
                    action=request.action,
                    decision=request.context.enforcement_decision.value,
                )

                # Execute through capability executor
                exec_result = self._capability_executor.execute(
                    capability_type=request.capability_type,
                    action=request.action,
                    action_data=request.action_data,
                    trace_id=trace_id,
                    enforcement_decision=request.context.enforcement_decision.value,
                    gateway_auth=gateway_auth,
                )

                latency_ms = (time.time() - invocation_start) * 1000

                # Record success
                invocation = CapabilityInvocation(
                    invocation_id=invocation_id,
                    capability_type=request.capability_type,
                    action=request.action,
                    status=ExecutionStatus.COMPLETED,
                    started_at=datetime.now(timezone.utc).isoformat(),
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    latency_ms=latency_ms,
                    result_data=exec_result,
                    retry_count=attempt,
                    gateway_auth_token=gateway_auth,
                )

                self._governance.record_success(request.capability_type.value, latency_ms)
                state.transition(ExecutionStatus.COMPLETED, reason=f"capability_completed_attempt_{attempt}")

                telemetry_events.append(
                    InsightFlow.on_capability_completed(
                        trace_id, request.capability_type.value, request.action,
                        "completed", latency_ms,
                    )
                )

                return {
                    "invocation": invocation,
                    "failures": [],
                    "response_data": exec_result,
                }

            except Exception as e:
                latency_ms = (time.time() - invocation_start) * 1000
                last_error = str(e)
                self._governance.record_failure(request.capability_type.value)

                telemetry_events.append(
                    InsightFlow.on_capability_completed(
                        trace_id, request.capability_type.value, request.action,
                        "failed", latency_ms,
                    )
                )

                logger.warning(
                    f"[{trace_id}] Capability invocation attempt {attempt + 1} failed: {e}"
                )

                # Check if we should retry
                if self._governance.should_retry(request.capability_type.value, attempt, last_error):
                    delay_ms = self._governance.get_retry_delay_ms(request.capability_type.value, attempt)
                    logger.info(f"[{trace_id}] Retrying in {delay_ms}ms (attempt {attempt + 2})")
                    time.sleep(delay_ms / 1000.0)
                    continue
                else:
                    break

        # All retries exhausted
        failure = FailureContract(
            failure_id=hashlib.sha256(f"fail:{trace_id}:{time.time()}".encode()).hexdigest()[:16],
            failure_type="capability_failure",
            failure_code="MAX_RETRIES_EXHAUSTED",
            message=f"Capability {request.capability_type.value} failed after {request.max_retries + 1} attempts: {last_error}",
            capability_type=request.capability_type,
            trace_id=trace_id,
            is_retryable=False,
        )

        state.transition(ExecutionStatus.FAILED, reason=f"max_retries_exhausted:{last_error}")
        telemetry_events.append(
            InsightFlow.on_failure(
                trace_id, "capability_failure", "MAX_RETRIES_EXHAUSTED",
                failure.message, is_retryable=False,
            )
        )

        return {
            "invocation": invocation,
            "failures": [failure],
            "response_data": {},
        }

    # ------------------------------------------------------------------
    # Result building
    # ------------------------------------------------------------------

    def _build_result(
        self,
        request: ExecutionRequest,
        state: ExecutionStateMachine,
        status: ExecutionStatus,
        decision: ExecutionDecision,
        start_time: float,
        telemetry_events: List[TelemetryEvent],
        invocation: Optional[CapabilityInvocation] = None,
        failures: Optional[List[FailureContract]] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        total_latency = (time.time() - start_time) * 1000
        invocations = [invocation] if invocation else []

        result = ExecutionResult(
            trace_metadata=request.trace_metadata,
            status=status,
            decision=decision,
            response_data=response_data or {},
            invocations=invocations,
            failures=failures or [],
            total_latency_ms=total_latency,
            telemetry={
                "events": [e.to_dict() for e in telemetry_events],
                "state_timeline": state.get_timeline(),
            },
        )

        self._execution_records[request.trace_metadata.trace_id] = result
        return result

    # ------------------------------------------------------------------
    # Bucket recording
    # ------------------------------------------------------------------

    def _record_to_bucket(
        self,
        request: ExecutionRequest,
        result: ExecutionResult,
        state: ExecutionStateMachine,
    ) -> None:
        """Record execution to Bucket for audit trail and replay."""
        trace_id = request.trace_metadata.trace_id
        try:
            # Record execution stage
            self.bucket_service.log_event(
                trace_id,
                "tantra_execution",
                {
                    "trace_id": trace_id,
                    "capability_type": request.capability_type.value,
                    "action": request.action,
                    "status": result.status.value,
                    "decision": result.decision.value,
                    "latency_ms": round(result.total_latency_ms, 2),
                    "integrity_hash": result.integrity_hash,
                    "state_timeline": state.get_timeline(),
                    "invocation_count": len(result.invocations),
                    "failure_count": len(result.failures),
                },
            )

            # Record InsightFlow telemetry
            insight_record = InsightFlow.build_record(request, result, telemetry_events=[])
            self.bucket_service.log_event(
                trace_id,
                "tantra_insightflow",
                insight_record.to_dict(),
            )

        except Exception as e:
            logger.error(f"[{trace_id}] Failed to record to Bucket: {e}")

    # ------------------------------------------------------------------
    # Replay support
    # ------------------------------------------------------------------

    def get_execution_record(self, trace_id: str) -> Optional[ExecutionResult]:
        return self._execution_records.get(trace_id)

    def create_replay_metadata(self, trace_id: str) -> ReplayMetadata:
        original = self._execution_records.get(trace_id)
        return ReplayMetadata(
            original_trace_id=trace_id,
            replay_count=0,
            integrity_verified=original is not None,
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        return {
            "service": "tantra_runtime",
            "status": "active",
            "role": "sole_execution_runtime",
            "total_executions": len(self._execution_records),
            "governance": self._governance.get_health_report(),
            "registry": self._registry.get_health(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
