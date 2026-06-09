"""
MITRA ENFORCEMENT ENGINE
------------------------
Deterministic, fail-closed, and bound to the single Mitra trace.
"""

from __future__ import annotations

from evaluator_modules import ALL_EVALUATORS

from .bucket_logger import log_enforcement
from .config_loader import RUNTIME_CONFIG
from .enforcement_verdict import EnforcementVerdict


DECISION_PRIORITY = ["BLOCK", "REWRITE", "EXECUTE"]


def _canonical_trace_payload(input_payload) -> dict:
    return {
        "intent": input_payload.intent,
        "emotional_output": input_payload.emotional_output,
        "age_gate_status": input_payload.age_gate_status,
        "region_policy": input_payload.region_policy,
        "platform_policy": input_payload.platform_policy,
        "karma_score": input_payload.karma_score,
        "risk_flags": input_payload.risk_flags,
        "policy_decision": input_payload.policy_decision,
        "rl_signal": input_payload.rl_signal,
    }


def _precondition_block(trace_id: str, *, reason_code: str) -> EnforcementVerdict:
    return EnforcementVerdict(
        decision="BLOCK",
        scope="both",
        trace_id=trace_id,
        reason_code=reason_code,
    )


def _policy_to_runtime_decision(policy_decision: dict | None) -> str:
    if not isinstance(policy_decision, dict):
        return "BLOCK"
    decision = str(policy_decision.get("decision") or "BLOCK").upper()
    if decision == "ALLOW":
        return "EXECUTE"
    if decision == "REWRITE":
        return "REWRITE"
    return "BLOCK"


def enforce(input_payload) -> EnforcementVerdict:
    trace_id = str(getattr(input_payload, "trace_id", "") or "").strip()
    trace_payload = _canonical_trace_payload(input_payload)
    policy_decision = getattr(input_payload, "policy_decision", None)
    rl_signal = getattr(input_payload, "rl_signal", None) or {}

    if not trace_id or not isinstance(policy_decision, dict):
        verdict = _precondition_block(trace_id or "trace_missing_policy", reason_code="MISSING_POLICY_RUNTIME")
        log_enforcement(
            trace_id=verdict.trace_id,
            input_snapshot=trace_payload,
            policy_decision=policy_decision or {},
            rl_signal=rl_signal,
            evaluator_results=[],
            final_decision=verdict.decision,
        )
        return verdict

    if getattr(input_payload, "bucket_active", False) and not getattr(input_payload, "policy_artifact_present", False):
        verdict = _precondition_block(trace_id, reason_code="MISSING_BUCKET_ARTIFACT")
        log_enforcement(
            trace_id=trace_id,
            input_snapshot=trace_payload,
            policy_decision=policy_decision,
            rl_signal=rl_signal,
            evaluator_results=[],
            final_decision=verdict.decision,
        )
        return verdict

    if RUNTIME_CONFIG.get("kill_switch") is True:
        verdict = EnforcementVerdict(
            decision="TERMINATE",
            scope="both",
            trace_id=trace_id,
            reason_code="GLOBAL_KILL_SWITCH",
        )
        log_enforcement(
            trace_id=trace_id,
            input_snapshot=trace_payload,
            policy_decision=policy_decision,
            rl_signal=rl_signal,
            evaluator_results=[],
            final_decision=verdict.decision,
        )
        return verdict

    evaluator_results = [e.evaluate(input_payload) for e in ALL_EVALUATORS]
    evaluator_decision = _resolve_runtime_decision(evaluator_results)
    final_decision = _resolve_final_decision(
        evaluator_decision=evaluator_decision,
        policy_decision=_policy_to_runtime_decision(policy_decision),
    )

    if final_decision == "EXECUTE":
        verdict = EnforcementVerdict(
            decision="ALLOW",
            scope="both",
            trace_id=trace_id,
            reason_code="CONTENT_AND_ACTION_ALLOWED",
        )
    elif final_decision == "REWRITE":
        verdict = EnforcementVerdict(
            decision="REWRITE",
            scope="response",
            trace_id=trace_id,
            reason_code="SAFE_REWRITE_REQUIRED",
            rewrite_class="MITRA_POLICY_REWRITE",
            safe_output=policy_decision.get("safe_output") or None,
        )
    else:
        verdict = EnforcementVerdict(
            decision="BLOCK",
            scope="both",
            trace_id=trace_id,
            reason_code="POLICY_VIOLATION",
        )

    log_enforcement(
        trace_id=trace_id,
        input_snapshot=trace_payload,
        policy_decision=policy_decision,
        rl_signal=rl_signal,
        evaluator_results=evaluator_results,
        final_decision=verdict.decision,
    )
    return verdict


def _resolve_runtime_decision(evaluator_results) -> str:
    for decision in DECISION_PRIORITY:
        for result in evaluator_results:
            if result.action == decision:
                return decision
    return "EXECUTE"


def _resolve_final_decision(*, evaluator_decision: str, policy_decision: str) -> str:
    for decision in DECISION_PRIORITY:
        if decision in {evaluator_decision, policy_decision}:
            return decision
    return "EXECUTE"
