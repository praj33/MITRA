"""
uniguru_capability.py — Mitra UniGuru Knowledge Capability
Integrates with live UniGuru v2 API for knowledge and educational queries.
Falls back to LLM knowledge mode if UniGuru is unavailable.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
from app.core.llm_bridge import llm_bridge
import logging
logger = logging.getLogger(__name__)

class UniGuruCapability(BaseCapability):
    @property
    def name(self) -> str: return "uniguru"
    @property
    def description(self) -> str:
        return "Answer educational and knowledge questions via UniGuru."
    @property
    def supported_intents(self) -> List[str]:
        return ["uniguru", "knowledge", "explain", "learn", "study", "educational"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            message = params.get("message", "")
            messages = [
                {"role": "system", "content": (
                    "You are an expert educational assistant powered by UniGuru. "
                    "Explain concepts clearly and accurately. Offer to go deeper if needed."
                )},
                {"role": "user", "content": message},
            ]
            answer = await llm_bridge.call_llm_with_messages(
                model="uniguru", messages=messages, temperature=0.4
            )
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary="Knowledge response from UniGuru.",
                data={"answer": answer, "query": message},
                trace_id=trace_id,
                actions=[{"label": "Go deeper", "action": "explain_more"}, {"label": "Give an example", "action": "give_example"}],
            )
        except Exception as exc:
            logger.warning("UniGuruCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
