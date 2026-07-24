"""
runtime_pipeline.py — Unified Runtime Pipeline

Mandatory flow:
  User Input
  → Safety Validator
  → Intelligence Processing
  → Enforcement Decision
  → Orchestration
  → Execution
  → Bucket Logging

Trace IDs propagate across every layer.
No layer may be skipped.
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from behavior_validator import validate_behavior
from mediation_system import (
    MediationSystem, InboundMessage, MediationDecision
)
from enforcement_adapter import EnforcementAdapter
from policy_runtime_adapter import validate_for_mitra


# ---------------------------------------------------------------------------
# Trace-propagating stage record
# ---------------------------------------------------------------------------

@dataclass
class PipelineStage:
    stage:     str
    trace_id:  str
    input:     Dict[str, Any]
    output:    Dict[str, Any]
    timestamp: str
    status:    str   # pass | block | rewrite | delay | error


@dataclass
class PipelineResult:
    trace_id:      str
    final_status:  str   # success | blocked | delayed | error
    final_decision: str  # ALLOW | BLOCK | REWRITE | DELAY
    response_text: Optional[str]
    stages:        List[PipelineStage]
    bucket_artifact: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id":       self.trace_id,
            "final_status":   self.final_status,
            "final_decision": self.final_decision,
            "response_text":  self.response_text,
            "stages":         [asdict(s) for s in self.stages],
            "bucket_artifact": self.bucket_artifact,
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class RuntimePipeline:
    """
    Executes the mandatory 7-stage pipeline with trace ID propagation.
    Every stage receives and forwards the same trace_id.
    """

    def __init__(self):
        self._mediation   = MediationSystem()
        self._enforcement = EnforcementAdapter()

    def _now(self) -> str:
        return datetime.now().isoformat() + "Z"

    def _root_trace(self, text: str) -> str:
        raw = f"{text}:{self._now()}"
        return f"pipe_{hashlib.md5(raw.encode()).hexdigest()[:12]}"

    def _stage(
        self,
        name: str,
        trace_id: str,
        inp: Dict,
        out: Dict,
        status: str = "pass",
    ) -> PipelineStage:
        return PipelineStage(
            stage=name,
            trace_id=trace_id,
            input=inp,
            output=out,
            timestamp=self._now(),
            status=status,
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        user_input: str,
        user_id: str = "anonymous",
        platform: str = "api",
        region: Optional[str] = None,
    ) -> PipelineResult:

        stages: List[PipelineStage] = []
        trace_id = self._root_trace(user_input)
        mediation = MediationSystem()  # fresh instance per request — no state bleed

        # ── Stage 1: Safety Validator ──────────────────────────────────
        policy_result = validate_for_mitra(user_input, region=region, caller_id=user_id)
        safety_status = "pass" if policy_result["decision"] == "ALLOW" else (
            "block" if policy_result["decision"] == "BLOCK" else "rewrite"
        )
        stages.append(self._stage(
            "safety_validator", trace_id,
            {"text": user_input, "region": region},
            {**policy_result, "trace_id": trace_id},
            safety_status,
        ))

        if policy_result["decision"] == "BLOCK":
            artifact = self._build_artifact(trace_id, user_input, "BLOCK", stages)
            self._log_to_bucket(artifact)
            return PipelineResult(
                trace_id=trace_id,
                final_status="blocked",
                final_decision="BLOCK",
                response_text=None,
                stages=stages,
                bucket_artifact=artifact,
            )

        # Use safe_output if rewritten
        active_text = (
            policy_result.get("safe_output") or user_input
            if policy_result["decision"] == "REWRITE"
            else user_input
        )

        # ── Stage 2: Intelligence Processing ──────────────────────────
        intel_response = self._intelligence(active_text)
        stages.append(self._stage(
            "intelligence_processing", trace_id,
            {"text": active_text, "trace_id": trace_id},
            {"response": intel_response, "trace_id": trace_id},
        ))

        # ── Stage 3: Enforcement Decision ─────────────────────────────
        enf_result = self._enforcement.map_validator_to_enforcement(intel_response)
        enf_status = "pass" if enf_result["decision"] == "allow" else "block"
        stages.append(self._stage(
            "enforcement_decision", trace_id,
            {"response": intel_response, "trace_id": trace_id},
            {**enf_result, "trace_id": trace_id},
            enf_status,
        ))

        if enf_result["decision"] in ("block", "escalate"):
            artifact = self._build_artifact(trace_id, user_input, "BLOCK", stages)
            self._log_to_bucket(artifact)
            return PipelineResult(
                trace_id=trace_id,
                final_status="blocked",
                final_decision="BLOCK",
                response_text=None,
                stages=stages,
                bucket_artifact=artifact,
            )

        # ── Stage 4: Orchestration ─────────────────────────────────────
        inbound_msg = InboundMessage(
            content=active_text,
            sender=user_id,
            recipient="assistant",
            platform=platform,
            timestamp=self._now(),
        )
        med_result = mediation.validate_inbound(inbound_msg)
        orch_status = med_result.decision.value
        stages.append(self._stage(
            "orchestration", trace_id,
            {"content": active_text, "platform": platform, "trace_id": trace_id},
            {
                "decision":          med_result.decision.value,
                "reason":            med_result.reason,
                "safety_flags":      med_result.safety_flags,
                "rewritten_content": med_result.rewritten_content,
                "delay_until":       med_result.delay_until,
                "trace_id":          trace_id,
            },
            orch_status,
        ))

        if med_result.decision == MediationDecision.BLOCK:
            artifact = self._build_artifact(trace_id, user_input, "BLOCK", stages)
            self._log_to_bucket(artifact)
            return PipelineResult(
                trace_id=trace_id,
                final_status="blocked",
                final_decision="BLOCK",
                response_text=None,
                stages=stages,
                bucket_artifact=artifact,
            )

        if med_result.decision == MediationDecision.DELAY:
            artifact = self._build_artifact(trace_id, user_input, "DELAY", stages)
            self._log_to_bucket(artifact)
            return PipelineResult(
                trace_id=trace_id,
                final_status="delayed",
                final_decision="DELAY",
                response_text=f"Delayed until {med_result.delay_until}",
                stages=stages,
                bucket_artifact=artifact,
            )

        final_response = med_result.rewritten_content or intel_response

        # ── Stage 5: Execution ─────────────────────────────────────────
        stages.append(self._stage(
            "execution", trace_id,
            {"approved_response": final_response, "trace_id": trace_id},
            {"delivered": True, "output": final_response, "trace_id": trace_id},
        ))

        # ── Stage 6: Bucket Logging ────────────────────────────────────
        artifact = self._build_artifact(trace_id, user_input, "ALLOW", stages, final_response)
        self._log_to_bucket(artifact)
        stages.append(self._stage(
            "bucket_logging", trace_id,
            {"trace_id": trace_id},
            {"logged": True, "artifact_id": trace_id},
        ))

        return PipelineResult(
            trace_id=trace_id,
            final_status="success",
            final_decision="ALLOW",
            response_text=final_response,
            stages=stages,
            bucket_artifact=artifact,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _intelligence(self, text: str) -> str:
        low = text.lower()
        if any(w in low for w in ["weather", "forecast"]):
            return "Today's weather is sunny with a high of 75°F."
        if "help" in low:
            return "I'm here to help! What would you like assistance with?"
        if "remind" in low:
            return "I'll set that reminder for you."
        return "I understand your message. How can I assist you today?"

    def _build_artifact(
        self,
        trace_id: str,
        original_input: str,
        decision: str,
        stages: List[PipelineStage],
        response: Optional[str] = None,
    ) -> Dict[str, Any]:
        content_hash = hashlib.sha256(original_input.encode()).hexdigest()
        return {
            "trace_id":      trace_id,
            "decision":      decision,
            "original_input": original_input,
            "response":      response,
            "content_hash":  content_hash,
            "stage_count":   len(stages),
            "stages_summary": [{"stage": s.stage, "status": s.status} for s in stages],
            "timestamp":     self._now(),
        }

    def _log_to_bucket(self, artifact: Dict[str, Any]) -> None:
        """Write artifact to bucket log file (stub for Ashmit's bucket client)."""
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_bucket_log.json")
        logs = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        logs.append(artifact)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_pipeline = RuntimePipeline()

def run_pipeline(
    user_input: str,
    user_id: str = "anonymous",
    platform: str = "api",
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full 7-stage pipeline. Returns serializable dict."""
    return _pipeline.run(user_input, user_id=user_id, platform=platform, region=region).to_dict()
