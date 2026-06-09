from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, Literal, Optional

from app.core.mitra_entry_guard import mitra_enforcement_scope
from app.external.enforcement.deterministic_trace import generate_trace_id
from app.external.safety.behavior_validator import validate_behavior
from app.governance.policy_engine import get_policy_engine
from app.karma_adapter import fetch_user_karma, karma_bias_from_points
from app.mitra_system_registry import mitra_registry


SignalType = Literal[
    "correction",
    "intent_refinement",
    "implicit_positive",
    "implicit_negative",
]

PolicyDecisionType = Literal["ALLOW", "REWRITE", "BLOCK"]

_DECISION_PRIORITY = {"ALLOW": 0, "REWRITE": 1, "BLOCK": 2}
_REASON_BY_CODE = {
    "CONTENT_AND_ACTION_ALLOWED": "The request passed Mitra policy and enforcement checks.",
    "SAFE_REWRITE_REQUIRED": "The request requires a safer rewrite before responding or acting.",
    "POLICY_VIOLATION": "The request violated Mitra policy rules.",
    "MISSING_POLICY_RUNTIME": "The policy runtime result was missing, so Mitra failed closed.",
    "MISSING_BUCKET_ARTIFACT": "The policy artifact was not persisted to the bucket, so Mitra failed closed.",
    "GLOBAL_KILL_SWITCH": "The Mitra runtime is currently terminated by the global kill switch.",
    "SYSTEM_TERMINATION": "The Mitra runtime terminated the request before execution.",
}
_CORRECTION_MARKERS = (
    "actually",
    "correction",
    "i meant",
    "i mean",
    "instead",
    "not that",
    "that's wrong",
    "that is wrong",
    "to correct",
)
_REFINEMENT_MARKERS = (
    "for example",
    "in other words",
    "let me rephrase",
    "more specifically",
    "to clarify",
)
_POLICY_FLAG_MAP = {
    "emotional_dependency_bait": ["soft_rewrite", "emotional_dependency"],
    "emotional_dependency": ["soft_rewrite", "emotional_dependency"],
    "loneliness_hook": ["soft_rewrite", "loneliness_hook"],
    "manipulative_phrasing": ["soft_rewrite", "manipulation_signal"],
    "region_platform_conflict": ["soft_rewrite"],
    "sexual_escalation_attempt": ["hard_deny"],
    "illegal_intent_probing": ["hard_deny"],
    "youth_risk_behavior": ["hard_deny"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _normalize_identity(value: Optional[str], fallback: str) -> str:
    normalized = _normalize_text(value)
    return normalized or fallback


def _coerce_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_confidence(value: Optional[float]) -> float:
    if value is None:
        return 0.0
    normalized = value / 100.0 if value > 1.0 else value
    return round(max(0.0, min(1.0, normalized)), 4)


def _decision_confidence(decision: str, *risk_confidences: float) -> float:
    risk_confidence = max(risk_confidences, default=0.0)
    if decision == "ALLOW":
        return round(1.0 - risk_confidence, 4)
    return round(risk_confidence, 4)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _text_similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def _map_behavior_decision(raw_decision: str) -> PolicyDecisionType:
    normalized = str(raw_decision or "").strip().lower()
    if normalized == "soft_rewrite":
        return "REWRITE"
    if normalized == "hard_deny":
        return "BLOCK"
    return "ALLOW"


def _map_status(enforcement_decision: str) -> Literal["ALLOW", "FLAG", "BLOCK"]:
    if enforcement_decision in {"BLOCK", "TERMINATE", "DELAY"}:
        return "BLOCK"
    if enforcement_decision == "REWRITE":
        return "FLAG"
    return "ALLOW"


def _map_risk_level(
    *,
    enforcement_decision: str,
    policy_decision: str,
) -> Literal["LOW", "MEDIUM", "HIGH"]:
    if enforcement_decision in {"BLOCK", "TERMINATE", "DELAY"} or policy_decision == "BLOCK":
        return "HIGH"
    if enforcement_decision == "REWRITE" or policy_decision == "REWRITE":
        return "MEDIUM"
    return "LOW"


def _build_reason(status: str, policy_decision: dict, enforcement_output: dict) -> str:
    explanation = str(policy_decision.get("explanation") or "").strip()
    if status in {"FLAG", "BLOCK"} and explanation:
        return explanation

    reason_code = str(enforcement_output.get("reason_code") or "").strip()
    if reason_code in _REASON_BY_CODE:
        return _REASON_BY_CODE[reason_code]
    if explanation:
        return explanation
    if status == "ALLOW":
        return _REASON_BY_CODE["CONTENT_AND_ACTION_ALLOWED"]
    if status == "FLAG":
        return _REASON_BY_CODE["SAFE_REWRITE_REQUIRED"]
    return _REASON_BY_CODE["POLICY_VIOLATION"]


def _policy_flags(decision: str, risk_category: str, original_output: str) -> list[str]:
    flags = list(_POLICY_FLAG_MAP.get(risk_category, []))
    if decision == "BLOCK" and "hard_deny" not in flags:
        flags.append("hard_deny")
    if decision == "REWRITE" and "soft_rewrite" not in flags:
        flags.append("soft_rewrite")

    corpus = original_output.lower()
    if any(token in corpus for token in ("kill myself", "suicide", "hurt myself", "harm myself", "end my life")):
        flags.append("self_harm")
    if any(token in corpus for token in ("kill you", "bomb", "weapon", "rape you")):
        flags.append("violence")
    return sorted({flag for flag in flags if flag})


def _pattern_flag_for_signal(signal_type: SignalType, *, prior_exists: bool) -> str:
    if signal_type == "correction":
        return "explicit_correction_marker"
    if signal_type == "intent_refinement":
        return "intent_refinement_marker"
    if signal_type == "implicit_negative":
        return "abrupt_topic_shift"
    if prior_exists:
        return "stable_progression"
    return "first_touch"


@dataclass(frozen=True)
class MitraAuthorityInput:
    input_text: str
    raw_input: Dict[str, Any]
    category: str = ""
    request_confidence: Optional[float] = None
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    platform: str = "samachar"
    device: str = "api"
    voice_input: bool = False
    preferred_language: Optional[str] = None
    authenticated_user_context: Optional[Dict[str, Any]] = None
    system_context: Optional[Dict[str, Any]] = None
    trace_seed_payload: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    source: str = "/api/mitra/evaluate"
    age_gate_status: bool = False
    region_policy: Optional[Dict[str, Any]] = None


class MitraControlPlaneService:
    """The single Mitra decision authority."""

    def __init__(self) -> None:
        self._policy_engine = get_policy_engine()
        self.enforcement_service = mitra_registry.enforcement_service
        self.bucket_service = mitra_registry.bucket_service

    @staticmethod
    def _build_platform_policy(authority_input: MitraAuthorityInput) -> Dict[str, Any]:
        platform_policy = {
            "platform": authority_input.platform,
            "device": authority_input.device,
            "source": authority_input.source,
        }
        if authority_input.category:
            platform_policy["event_category"] = authority_input.category
        if authority_input.authenticated_user_context:
            platform_policy["authenticated_user_context"] = authority_input.authenticated_user_context
        return platform_policy

    @staticmethod
    def _build_trace_seed_payload(authority_input: MitraAuthorityInput) -> Dict[str, Any]:
        return {
            "input": authority_input.raw_input,
            "user_id": authority_input.user_id,
            "session_id": authority_input.session_id or "",
            "platform": authority_input.platform,
            "device": authority_input.device,
            "voice_input": bool(authority_input.voice_input),
            "source": authority_input.source,
        }

    @staticmethod
    def _extract_prior_text(prior_request: Optional[Dict[str, Any]]) -> str:
        if not prior_request:
            return ""
        prior_input = (prior_request.get("data") or {}).get("input")
        if isinstance(prior_input, dict):
            return _normalize_text(prior_input.get("text"))
        return _normalize_text(str(prior_input or ""))

    @staticmethod
    def _extract_prior_category(prior_request: Optional[Dict[str, Any]]) -> str:
        if not prior_request:
            return ""
        prior_input = (prior_request.get("data") or {}).get("input")
        if isinstance(prior_input, dict):
            return _normalize_text(prior_input.get("category"))
        return ""

    def context_fetch(self, user_id: str, *, exclude_trace_id: str | None = None) -> Dict[str, Any]:
        recent_requests = self.bucket_service.find_recent_stage_events(
            "mitra_request_log",
            user_id=user_id,
            exclude_trace_id=exclude_trace_id,
            limit=1,
        )
        prior_request = recent_requests[0] if recent_requests else None
        karma = fetch_user_karma(user_id)
        return {
            "user_id": user_id,
            "source": "bhiv_context_stub",
            "status": "available",
            "karma_points": int(karma.get("karma_points", 50)),
            "recent_trace_id": prior_request.get("trace_id") if prior_request else None,
            "history_available": bool(prior_request),
        }

    def _run_policy_runtime(
        self,
        *,
        trace_id: str,
        authority_input: MitraAuthorityInput,
        platform_policy: Dict[str, Any],
        karma_points: int,
        bhiv_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        region = None
        if isinstance(authority_input.region_policy, dict):
            region = authority_input.region_policy.get("region")

        rule_result = self._policy_engine.evaluate(
            authority_input.input_text,
            system="mitra",
            region=region,
        ).to_dict()
        behavior_result = validate_behavior(
            intent="auto",
            conversational_output=authority_input.input_text,
            age_gate_status=authority_input.age_gate_status,
            region_rule_status=authority_input.region_policy,
            platform_policy_state=platform_policy,
            karma_bias_input=karma_bias_from_points(karma_points),
        )

        behavior_decision = _map_behavior_decision(behavior_result.get("decision"))
        rule_decision = str(rule_result.get("decision") or "ALLOW").upper()
        selected_source = (
            "behavior_validator"
            if _DECISION_PRIORITY[behavior_decision] >= _DECISION_PRIORITY.get(rule_decision, 0)
            else "policy_registry"
        )
        decision = (
            behavior_decision
            if selected_source == "behavior_validator"
            else rule_decision
        )

        behavior_confidence = _clamp_confidence(behavior_result.get("confidence"))
        rule_confidence = _clamp_confidence(rule_result.get("confidence"))
        confidence = _decision_confidence(
            decision,
            behavior_confidence,
            rule_confidence,
        )
        risk_category = (
            behavior_result.get("risk_category")
            if selected_source == "behavior_validator"
            else rule_result.get("category")
        ) or "clean"
        explanation = (
            behavior_result.get("explanation")
            if selected_source == "behavior_validator"
            else rule_result.get("reason")
        ) or ""
        matched_patterns = list(behavior_result.get("matched_patterns") or [])
        if rule_result.get("matched_pattern"):
            matched_patterns.append(str(rule_result["matched_pattern"]))

        return {
            "decision": decision,
            "raw_decision": behavior_result.get("decision"),
            "risk_category": risk_category,
            "reason_code": behavior_result.get("reason_code") or "policy_rule_matched",
            "confidence": confidence,
            "confidence_basis": "decision_certainty",
            "trace_id": trace_id,
            "matched_patterns": sorted(set(matched_patterns)),
            "explanation": explanation,
            "safe_output": behavior_result.get("safe_output") or "",
            "original_output": authority_input.input_text,
            "policy_flags": _policy_flags(decision, str(risk_category), authority_input.input_text),
            "rule_id": rule_result.get("rule_id"),
            "policy_version": rule_result.get("policy_version"),
            "selected_source": selected_source,
            "source_decisions": {
                "policy_registry": {
                    "decision": rule_decision,
                    "category": rule_result.get("category"),
                    "confidence": rule_confidence,
                    "rule_id": rule_result.get("rule_id"),
                },
                "behavior_validator": {
                    "decision": behavior_decision,
                    "category": behavior_result.get("risk_category"),
                    "confidence": behavior_confidence,
                    "reason_code": behavior_result.get("reason_code"),
                },
            },
            "bhiv_context": {
                "recent_trace_id": bhiv_context.get("recent_trace_id"),
                "karma_points": bhiv_context.get("karma_points"),
                "history_available": bhiv_context.get("history_available"),
            },
        }

    def _resolve_signal(
        self,
        *,
        trace_id: str,
        authority_input: MitraAuthorityInput,
        policy_runtime: Dict[str, Any],
    ) -> Dict[str, Any]:
        prior_requests = self.bucket_service.find_recent_stage_events(
            "mitra_request_log",
            user_id=authority_input.user_id,
            session_id=authority_input.session_id,
            exclude_trace_id=trace_id,
            limit=1,
        )
        prior_request = prior_requests[0] if prior_requests else None
        current_text = authority_input.input_text
        current_lower = current_text.lower()
        previous_text = self._extract_prior_text(prior_request)
        previous_category = self._extract_prior_category(prior_request)
        similarity = _text_similarity(current_text, previous_text)
        token_overlap = len(_tokenize(current_text) & _tokenize(previous_text))
        prior_exists = bool(prior_request)

        signal_type: SignalType
        correction_starts = current_lower.startswith(("no ", "no,", "actually ", "i meant ", "instead "))
        correction_contains = any(marker in current_lower for marker in _CORRECTION_MARKERS)
        if prior_exists and (correction_starts or correction_contains):
            signal_type = "correction"
        elif prior_exists and (
            any(marker in current_lower for marker in _REFINEMENT_MARKERS)
            or (0.35 <= similarity <= 0.9 and token_overlap >= 2)
        ):
            signal_type = "intent_refinement"
        elif prior_exists and (
            similarity < 0.45
            and token_overlap <= 1
            and authority_input.category != previous_category
        ):
            signal_type = "implicit_negative"
        else:
            signal_type = "implicit_positive"

        adjusted_confidence = float(policy_runtime["confidence"])
        if signal_type == "correction":
            adjusted_confidence = max(adjusted_confidence - 0.07, 0.0)
        elif signal_type == "intent_refinement":
            adjusted_confidence = max(adjusted_confidence - 0.04, 0.0)
        elif signal_type == "implicit_negative":
            adjusted_confidence = max(adjusted_confidence - 0.1, 0.0)
        elif prior_exists:
            adjusted_confidence = min(adjusted_confidence + 0.02, 1.0)

        if policy_runtime["decision"] in {"BLOCK", "REWRITE"}:
            adjusted_confidence = max(adjusted_confidence, float(policy_runtime["confidence"]))

        return {
            "signal_type": signal_type,
            "pattern_flag": _pattern_flag_for_signal(signal_type, prior_exists=prior_exists),
            "adjusted_confidence": round(adjusted_confidence, 4),
            "trace_id": trace_id,
            "basis": {
                "previous_trace_id": (prior_request or {}).get("trace_id"),
                "similarity": round(similarity, 4),
                "token_overlap": token_overlap,
                "previous_category": previous_category or None,
                "current_category": authority_input.category or None,
            },
        }

    @staticmethod
    def _apply_conflict_guard(policy_runtime: Dict[str, Any], rl_signal: Dict[str, Any]) -> Dict[str, Any]:
        guarded_policy = dict(policy_runtime)
        guarded_policy["confidence"] = rl_signal["adjusted_confidence"]
        guarded_policy["conflict_guard"] = {
            "decision_immutable": True,
            "rl_can_adjust_confidence_only": True,
        }
        return {
            "policy_decision": guarded_policy,
            "rl_signal": dict(rl_signal),
        }

    @staticmethod
    def _build_system_context(
        authority_input: MitraAuthorityInput,
        *,
        bhiv_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "platform": authority_input.platform,
            "device": authority_input.device,
            "session_id": authority_input.session_id or authority_input.user_id,
            "user_id": authority_input.user_id,
            "voice_input": bool(authority_input.voice_input),
            "preferred_language": authority_input.preferred_language or "auto",
            "source": authority_input.source,
            "bhiv_context": bhiv_context,
        }
        if authority_input.category:
            context["category"] = authority_input.category
        if authority_input.system_context:
            for key, value in authority_input.system_context.items():
                if key not in context and value is not None:
                    context[key] = value
        return context

    def evaluate(self, authority_input: MitraAuthorityInput) -> Dict[str, Any]:
        input_text = _normalize_text(authority_input.input_text)
        if not input_text:
            raise ValueError("Input text is required for Mitra control plane evaluation.")

        user_id = _normalize_identity(authority_input.user_id, "anonymous")
        session_id = _normalize_identity(authority_input.session_id, user_id)
        resolved_input = MitraAuthorityInput(
            input_text=input_text,
            raw_input=authority_input.raw_input,
            category=_normalize_text(authority_input.category),
            request_confidence=authority_input.request_confidence,
            user_id=user_id,
            session_id=session_id,
            platform=_normalize_identity(authority_input.platform, "samachar"),
            device=_normalize_identity(authority_input.device, "api"),
            voice_input=bool(authority_input.voice_input),
            preferred_language=authority_input.preferred_language,
            authenticated_user_context=authority_input.authenticated_user_context or {},
            system_context=authority_input.system_context or {},
            trace_seed_payload=authority_input.trace_seed_payload,
            trace_id=_normalize_text(authority_input.trace_id) or None,
            source=_normalize_identity(authority_input.source, "/api/mitra/evaluate"),
            age_gate_status=bool(authority_input.age_gate_status),
            region_policy=authority_input.region_policy,
        )

        trace_id = resolved_input.trace_id or generate_trace_id(
            input_payload=resolved_input.trace_seed_payload or self._build_trace_seed_payload(resolved_input),
            enforcement_category="REQUEST",
        )
        timestamp = _now_iso()
        platform_policy = self._build_platform_policy(resolved_input)
        bhiv_context = self.context_fetch(resolved_input.user_id, exclude_trace_id=trace_id)
        karma_points = int(bhiv_context.get("karma_points", 50))

        self.bucket_service.log_event(
            trace_id,
            "request_received",
            {
                "trace_id": trace_id,
                "user_id": resolved_input.user_id,
                "session_id": resolved_input.session_id,
                "input": resolved_input.raw_input,
                "input_text": resolved_input.input_text,
                "platform": resolved_input.platform,
                "device": resolved_input.device,
                "voice_input": resolved_input.voice_input,
                "timestamp": timestamp,
            },
        )

        policy_runtime = self._run_policy_runtime(
            trace_id=trace_id,
            authority_input=resolved_input,
            platform_policy=platform_policy,
            karma_points=karma_points,
            bhiv_context=bhiv_context,
        )
        self.bucket_service.log_event(trace_id, "mitra_policy_runtime", policy_runtime)

        rl_signal = self._resolve_signal(
            trace_id=trace_id,
            authority_input=resolved_input,
            policy_runtime=policy_runtime,
        )
        self.bucket_service.log_event(trace_id, "mitra_rl_interpretation", rl_signal)

        guarded = self._apply_conflict_guard(policy_runtime, rl_signal)
        self.bucket_service.log_event(
            trace_id,
            "mitra_conflict_guard",
            {
                "trace_id": trace_id,
                "policy_decision": guarded["policy_decision"],
                "rl_signal": guarded["rl_signal"],
            },
        )

        with mitra_enforcement_scope(trace_id, "mitra_control_plane"):
            enforcement_output = self.enforcement_service.enforce_policy(
                payload={
                    "user_input": resolved_input.input_text,
                    "emotional_output": resolved_input.input_text,
                    "intent": resolved_input.category or "general",
                    "trace_id": trace_id,
                    "age_gate_status": resolved_input.age_gate_status,
                    "region_policy": resolved_input.region_policy,
                    "platform_policy": platform_policy,
                    "karma_score": karma_points,
                    "risk_flags": guarded["policy_decision"].get("policy_flags", []),
                    "authenticated_user_context": resolved_input.authenticated_user_context,
                    "user_context": resolved_input.authenticated_user_context,
                    "policy_decision": guarded["policy_decision"],
                    "rl_signal": guarded["rl_signal"],
                    "bhiv_context": bhiv_context,
                },
                trace_id=trace_id,
            )

        status = _map_status(str(enforcement_output.get("decision") or "BLOCK").upper())
        risk_level = _map_risk_level(
            enforcement_decision=str(enforcement_output.get("decision") or "BLOCK").upper(),
            policy_decision=str(guarded["policy_decision"].get("decision") or "BLOCK"),
        )
        system_context = self._build_system_context(resolved_input, bhiv_context=bhiv_context)
        bucket_log_reference = {
            "trace_id": trace_id,
            "stage": "mitra_response_contract",
            "artifact_locator": f"{trace_id}:mitra_response_contract",
            "backend": "mongodb",
        }
        response_contract: Dict[str, Any] = {
            "status": status,
            "risk_level": risk_level,
            "reason": _build_reason(status, guarded["policy_decision"], enforcement_output),
            "confidence": guarded["rl_signal"]["adjusted_confidence"],
            "trace_id": trace_id,
            "policy_decision": guarded["policy_decision"],
            "rl_signal": guarded["rl_signal"],
            "enforcement_output": enforcement_output,
            "bucket_log_reference": bucket_log_reference,
            "system_context": system_context,
        }

        self.bucket_service.log_event(trace_id, "mitra_response_contract", response_contract)
        self.bucket_service.log_event(
            trace_id,
            "mitra_request_log",
            {
                "user_id": resolved_input.user_id,
                "session_id": resolved_input.session_id,
                "input": {
                    "text": resolved_input.input_text,
                    "category": resolved_input.category,
                    "raw_input": resolved_input.raw_input,
                },
                "final_output": response_contract,
                "bucket_log_reference": bucket_log_reference,
                "trace_id": trace_id,
                "timestamp": timestamp,
            },
        )

        return {
            "trace_id": trace_id,
            "response_contract": response_contract,
            "policy_decision": guarded["policy_decision"],
            "rl_signal": guarded["rl_signal"],
            "enforcement_output": enforcement_output,
            "system_context": system_context,
            "bucket_log_reference": bucket_log_reference,
            "bhiv_context": bhiv_context,
        }
