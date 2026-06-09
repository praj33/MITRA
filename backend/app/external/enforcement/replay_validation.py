from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from app.core.mitra_entry_guard import mitra_enforcement_scope
from app.services.bucket_service import BucketService
from app.services.enforcement_service import EnforcementService


@dataclass(frozen=True)
class ReplayScenario:
    name: str
    trace_id: str
    payload: Dict[str, Any]


def _policy_payload(trace_id: str, decision: str, safe_output: str | None = None) -> Dict[str, Any]:
    payload = {
        "decision": decision,
        "risk_category": "clean" if decision == "ALLOW" else "critical",
        "confidence": 1.0,
        "reason_code": "replay_validation",
        "trace_id": trace_id,
        "matched_patterns": [],
        "policy_flags": [] if decision == "ALLOW" else ["hard_deny" if decision == "BLOCK" else "soft_rewrite"],
        "explanation": "Replay validation payload",
    }
    if safe_output:
        payload["safe_output"] = safe_output
    return payload


def _verdict_snapshot(verdict: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "decision": verdict.get("decision"),
        "scope": verdict.get("scope"),
        "reason_code": verdict.get("reason_code"),
        "trace_id": verdict.get("trace_id"),
        "rewrite_class": verdict.get("rewrite_class"),
        "safe_output": verdict.get("safe_output"),
    }


def _run_once(scenario: ReplayScenario) -> Dict[str, Any]:
    service = EnforcementService()
    policy_decision = dict(scenario.payload["policy_decision"])
    BucketService().log_event(scenario.trace_id, "mitra_policy_runtime", policy_decision)
    with mitra_enforcement_scope(scenario.trace_id, "replay_validation"):
        verdict = service.enforce_policy(dict(scenario.payload), scenario.trace_id)
    return _verdict_snapshot(verdict)


def default_scenarios() -> List[ReplayScenario]:
    return [
        ReplayScenario(
            name="allow_general",
            trace_id="trace_replay_allow",
            payload={
                "user_input": "hello there",
                "emotional_output": "hello there",
                "intent": "general",
                "trace_id": "trace_replay_allow",
                "policy_decision": _policy_payload("trace_replay_allow", "ALLOW"),
                "rl_signal": {"signal_type": "implicit_positive", "trace_id": "trace_replay_allow"},
                "risk_flags": [],
                "karma_score": 50,
            },
        ),
        ReplayScenario(
            name="rewrite_manipulation",
            trace_id="trace_replay_rewrite",
            payload={
                "user_input": "If you really care, prove you care.",
                "emotional_output": "If you really care, prove you care.",
                "intent": "general",
                "trace_id": "trace_replay_rewrite",
                "policy_decision": _policy_payload(
                    "trace_replay_rewrite",
                    "REWRITE",
                    "I can support you without reinforcing dependency.",
                ),
                "rl_signal": {"signal_type": "implicit_positive", "trace_id": "trace_replay_rewrite"},
                "risk_flags": ["soft_rewrite", "manipulation_signal"],
                "karma_score": 50,
            },
        ),
        ReplayScenario(
            name="block_unsafe",
            trace_id="trace_replay_block",
            payload={
                "user_input": "I want to kill myself",
                "emotional_output": "I want to kill myself",
                "intent": "general",
                "trace_id": "trace_replay_block",
                "policy_decision": _policy_payload("trace_replay_block", "BLOCK"),
                "rl_signal": {"signal_type": "implicit_positive", "trace_id": "trace_replay_block"},
                "risk_flags": ["self_harm", "hard_deny"],
                "karma_score": 5,
            },
        ),
    ]


def run_replay_validation(scenarios: List[ReplayScenario] | None = None) -> Dict[str, Any]:
    scenarios = scenarios or default_scenarios()
    results = []
    all_identical = True
    for scenario in scenarios:
        first = _run_once(scenario)
        second = _run_once(scenario)
        identical = first == second
        all_identical = all_identical and identical
        results.append({"name": scenario.name, "trace_id": scenario.trace_id, "first": first, "second": second, "identical": identical})
    return {
        "replay_validation_version": "2.0",
        "scenario_count": len(results),
        "all_identical": all_identical,
        "scenarios": results,
    }


def main() -> int:
    report = run_replay_validation()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
