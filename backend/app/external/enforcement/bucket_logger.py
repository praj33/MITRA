from __future__ import annotations

from typing import Any


def log_enforcement(
    *,
    trace_id: str,
    input_snapshot: dict[str, Any],
    policy_decision: dict[str, Any],
    rl_signal: dict[str, Any],
    evaluator_results: list[Any],
    final_decision: str,
) -> None:
    from app.services.bucket_service import BucketService

    BucketService().log_event(
        trace_id,
        "mitra_enforcement_runtime",
        {
            "event_type": "mitra_enforcement_audit",
            "audit_version": "2.0",
            "trace_id": trace_id,
            "input_snapshot": input_snapshot,
            "policy_decision": policy_decision,
            "rl_signal": rl_signal,
            "evaluator_results": [
                getattr(result, "__dict__", str(result))
                for result in (evaluator_results or [])
            ],
            "final_decision": final_decision,
        },
    )
