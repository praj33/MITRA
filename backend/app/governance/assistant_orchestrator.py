"""
assistant_orchestrator.py — Unified runtime orchestrator

Inbound flow requirement:
Inbound → MediationSystem.validate_inbound → SafetyService → Intelligence → Enforcement → Execution

Outbound flow points (to be enforced by execution layer modifications):
Intent → MediationSystem.validate_outbound → If BLOCK → stop → If REWRITE → use rewritten_content → If DELAY → schedule → If ALLOW → proceed

This orchestrator normalizes inbound requests from multiple channels and ensures
that mediation is invoked immediately after normalization. It returns a
structured result with a stage-by-stage trace for proof generation.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib

from mediation_system import (
    InboundMessage,
    MediationDecision,
    validate_inbound_message,
)


@dataclass
class StageRecord:
    name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    timestamp: str


@dataclass
class OrchestratorResult:
    status: str
    trace_id: str
    response_text: Optional[str]
    decision: str
    stages: List[StageRecord]


class AssistantOrchestrator:
    def __init__(self) -> None:
        pass

    def _now(self) -> str:
        return datetime.now().isoformat() + "Z"

    def _make_trace_id(self, seed: str) -> str:
        return f"trace_{hashlib.md5((seed + self._now()).encode()).hexdigest()[:12]}"

    def _record(self, name: str, _in: Dict[str, Any], _out: Dict[str, Any]) -> StageRecord:
        return StageRecord(name=name, input=_in, output=_out, timestamp=self._now())

    # Inbound sources: whatsapp, email, telephony, api
    def handle_inbound(self, source: str, payload: Dict[str, Any]) -> OrchestratorResult:
        """
        Normalize inbound payload and run mandatory mediation first.
        Supported sources: 'api', 'whatsapp', 'email', 'telephony'
        """
        stages: List[StageRecord] = []

        # 0) Normalize
        norm = self._normalize(source, payload)
        stages.append(self._record("normalize", {"source": source, **payload}, norm))

        # 1) MediationSystem.validate_inbound — MUST be first after normalization
        inbound_msg = InboundMessage(
            content=norm["content"],
            sender=norm["sender"],
            recipient=norm["recipient"],
            platform=norm["platform"],
            timestamp=norm["timestamp"],
            message_type=norm.get("message_type", "general"),
        )
        med_result = validate_inbound_message(inbound_msg)
        stages.append(
            self._record(
                "mediation_inbound",
                asdict(inbound_msg),
                {
                    "decision": med_result.decision.value,
                    "reason": med_result.reason,
                    "trace_id": med_result.trace_id,
                    "safety_flags": med_result.safety_flags,
                    "rewritten_content": med_result.rewritten_content,
                    "delay_until": med_result.delay_until,
                },
            )
        )

        # Apply decision contract immediately
        if med_result.decision == MediationDecision.BLOCK:
            return OrchestratorResult(
                status="blocked",
                trace_id=med_result.trace_id,
                response_text=None,
                decision="BLOCK",
                stages=stages,
            )
        if med_result.decision == MediationDecision.DELAY:
            return OrchestratorResult(
                status="delayed",
                trace_id=med_result.trace_id,
                response_text=f"Message delayed until {med_result.delay_until}",
                decision="DELAY",
                stages=stages,
            )
        if med_result.decision == MediationDecision.REWRITE:
            norm["content"] = med_result.rewritten_content or norm["content"]
            stages.append(self._record("mediation_rewrite_applied", {"content_before": inbound_msg.content}, {"content_after": norm["content"]}))

        # 2) SafetyService (placeholder: sequencing proof; real safety runs here)
        safety_in = {"content": norm["content"], "trace_id": med_result.trace_id}
        safety_out = {"decision": "allow", "reason": "sequencing_proof", "trace_id": med_result.trace_id}
        stages.append(self._record("safety_service", safety_in, safety_out))

        # 3) Intelligence
        intel_in = {"content": norm["content"], "trace_id": med_result.trace_id}
        # Simple deterministic response for demo
        response_text = self._intelligence_generate(norm["content"]) 
        intel_out = {"generated_response": response_text, "trace_id": med_result.trace_id}
        stages.append(self._record("intelligence", intel_in, intel_out))

        # 4) Enforcement (placeholder decision pass-through)
        enf_in = {"generated_response": response_text, "trace_id": med_result.trace_id}
        enf_out = {"enforcement_decision": "allow", "approval_token": f"tok_{med_result.trace_id[-6:]}", "trace_id": med_result.trace_id}
        stages.append(self._record("enforcement", enf_in, enf_out))

        # 5) Execution (render/return only after enforcement)
        exec_in = {"approved": True, "response_text": response_text, "trace_id": med_result.trace_id}
        exec_out = {"delivered": True, "ui_render": response_text, "trace_id": med_result.trace_id}
        stages.append(self._record("execution", exec_in, exec_out))

        return OrchestratorResult(
            status="success",
            trace_id=med_result.trace_id,
            response_text=response_text,
            decision="ALLOW",
            stages=stages,
        )

    def _normalize(self, source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = self._now()
        if source == "api":
            return {
                "content": payload.get("user_input", ""),
                "sender": payload.get("user_id", "anonymous"),
                "recipient": payload.get("recipient", "assistant"),
                "platform": "api",
                "timestamp": payload.get("timestamp", now),
                "message_type": payload.get("message_type", "general"),
            }
        if source == "whatsapp":
            return {
                "content": payload.get("content", ""),
                "sender": payload.get("from", "unknown"),
                "recipient": "assistant",
                "platform": "whatsapp",
                "timestamp": payload.get("timestamp", now),
                "message_type": "general",
            }
        if source == "email":
            body = payload.get("body", "")
            subj = payload.get("subject", "")
            return {
                "content": f"{subj}\n\n{body}".strip(),
                "sender": payload.get("from", "unknown"),
                "recipient": payload.get("to", "assistant"),
                "platform": "email",
                "timestamp": payload.get("timestamp", now),
                "message_type": "general",
            }
        if source == "telephony":
            return {
                "content": payload.get("transcript", ""),
                "sender": payload.get("caller_id", "unknown"),
                "recipient": "assistant",
                "platform": "voice",
                "timestamp": payload.get("timestamp", now),
                "message_type": "general",
            }
        # Default passthrough
        return {
            "content": payload.get("content", ""),
            "sender": payload.get("sender", "unknown"),
            "recipient": payload.get("recipient", "assistant"),
            "platform": source,
            "timestamp": payload.get("timestamp", now),
            "message_type": payload.get("message_type", "general"),
        }

    def _intelligence_generate(self, content: str) -> str:
        low = content.lower()
        if "weather" in low:
            return "Today's weather is sunny with a high of 75°F."
        if "help" in low:
            return "I'm here to help! What would you like assistance with?"
        return "I understand your message. How can I assist you today?"


# Singleton accessor
_orchestrator = AssistantOrchestrator()

def get_orchestrator() -> AssistantOrchestrator:
    return _orchestrator
