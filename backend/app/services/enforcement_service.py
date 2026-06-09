from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

from app.core.mitra_entry_guard import get_mitra_entry_scope
from app.external.enforcement import enforcement_engine


class EnforcementService:
    def __init__(self):
        self.enforcement_engine = enforcement_engine

    @staticmethod
    def _normalize_trace_id(value: Any) -> str | None:
        if value is None:
            return None
        trace_id = str(value).strip()
        return trace_id or None

    @staticmethod
    def _compose_platform_policy(payload: Dict[str, Any]) -> Any:
        platform_policy = payload.get("platform_policy")
        authenticated_user_context = payload.get("authenticated_user_context") or payload.get("user_context")
        if platform_policy and authenticated_user_context:
            merged_policy = dict(platform_policy) if isinstance(platform_policy, dict) else {"platform_policy": platform_policy}
            merged_policy["authenticated_user_context"] = authenticated_user_context
            return merged_policy
        return platform_policy or authenticated_user_context

    @staticmethod
    def _extract_risk_flags(payload: Dict[str, Any]) -> list[Any]:
        risk_flags = payload.get("risk_flags")
        if risk_flags is None:
            risk_flags = (payload.get("policy_decision") or {}).get("policy_flags") or []
        if isinstance(risk_flags, str):
            return [risk_flags]
        if isinstance(risk_flags, list):
            return risk_flags
        return [risk_flags] if risk_flags else []

    @staticmethod
    def _normalize_karma_score(payload: Dict[str, Any]) -> int:
        raw_value = payload.get("karma_score")
        if raw_value is None:
            raw_value = (payload.get("bhiv_context") or {}).get("karma_points")
        if isinstance(raw_value, bool):
            return int(raw_value)
        if isinstance(raw_value, (int, float)):
            return int(raw_value)
        return 50

    def _bucket_preconditions(self, trace_id: str | None) -> Dict[str, Any]:
        from app.services.bucket_service import BucketService

        bucket = BucketService()
        return {
            "bucket_active": bucket.enforcement_artifact_required(),
            "policy_artifact_present": bool(trace_id)
            and bucket.validate_artifact(
                trace_id,
                stage="mitra_policy_runtime",
                required_fields=("decision", "trace_id"),
                expected_trace_id=trace_id,
            ),
        }

    @staticmethod
    def _emit_enforcement_telemetry(
        *,
        trace_id: str,
        result: Dict[str, Any],
        policy_decision: Dict[str, Any],
        rl_signal: Dict[str, Any],
        input_payload: SimpleNamespace,
        bucket_preconditions: Dict[str, Any],
    ) -> None:
        from app.services.bucket_service import BucketService

        BucketService().log_event(
            trace_id,
            "mitra_enforcement_telemetry",
            {
                "event_type": "mitra_enforcement_decision",
                "telemetry_version": "2.0",
                "trace_id": result["trace_id"],
                "decision": result["decision"],
                "scope": result["scope"],
                "reason_code": result["reason_code"],
                "intent": input_payload.intent,
                "risk_flags": list(input_payload.risk_flags),
                "risk_flag_count": len(input_payload.risk_flags),
                "karma_score": input_payload.karma_score,
                "policy_decision": policy_decision,
                "rl_signal": rl_signal,
                "bucket_active": bucket_preconditions["bucket_active"],
                "policy_artifact_valid": bucket_preconditions["policy_artifact_present"],
            },
        )

    def enforce_policy(self, payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        runtime_trace_id = self._normalize_trace_id(trace_id)
        scope = get_mitra_entry_scope()
        if not scope or str(scope.get("trace_id") or "") != str(runtime_trace_id or ""):
            from app.services.bucket_service import BucketService

            if runtime_trace_id:
                BucketService().log_event(
                    runtime_trace_id,
                    "enforcement_bypass_blocked",
                    {
                        "trace_id": runtime_trace_id,
                        "reason": "Direct enforcement access blocked. Use Mitra control plane.",
                        "source": scope.get("source") if scope else None,
                    },
                )
            raise PermissionError("Direct enforcement access blocked. Use Mitra control plane.")

        policy_decision = payload.get("policy_decision") or {}
        rl_signal = payload.get("rl_signal") or {}
        bucket_preconditions = self._bucket_preconditions(runtime_trace_id)
        input_payload = SimpleNamespace(
            intent=payload.get("intent") or "general",
            emotional_output=payload.get("emotional_output") or payload.get("user_input") or payload.get("text") or "",
            age_gate_status=bool(payload.get("age_gate_status", False)),
            region_policy=payload.get("region_policy"),
            platform_policy=self._compose_platform_policy(payload),
            karma_score=self._normalize_karma_score(payload),
            risk_flags=self._extract_risk_flags(payload),
            trace_id=runtime_trace_id,
            authenticated_user_context=payload.get("authenticated_user_context") or payload.get("user_context"),
            policy_decision=policy_decision,
            rl_signal=rl_signal,
            bucket_active=bucket_preconditions["bucket_active"],
            policy_artifact_present=bucket_preconditions["policy_artifact_present"],
        )

        verdict = self.enforcement_engine.enforce(input_payload)
        result: Dict[str, Any] = {
            "decision": getattr(verdict, "decision", "BLOCK"),
            "scope": getattr(verdict, "scope", "both"),
            "trace_id": getattr(verdict, "trace_id", runtime_trace_id or trace_id),
            "reason_code": getattr(verdict, "reason_code", "UNKNOWN"),
        }
        if getattr(verdict, "rewrite_class", None):
            result["rewrite_class"] = verdict.rewrite_class
        if getattr(verdict, "safe_output", None):
            result["safe_output"] = verdict.safe_output
            result["rewritten_output"] = verdict.safe_output

        self._emit_enforcement_telemetry(
            trace_id=runtime_trace_id or result["trace_id"],
            result=result,
            policy_decision=policy_decision,
            rl_signal=rl_signal,
            input_payload=input_payload,
            bucket_preconditions=bucket_preconditions,
        )
        return result

    def get_status(self) -> Dict[str, Any]:
        return {"service": "mitra_enforcement_runtime", "status": "active"}
