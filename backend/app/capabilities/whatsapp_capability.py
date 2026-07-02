"""
whatsapp_capability.py — Mitra WhatsApp Capability
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

class WhatsAppCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "whatsapp"

    @property
    def description(self) -> str:
        return "Send WhatsApp messages to contacts."

    @property
    def supported_intents(self) -> List[str]:
        return ["telegram", "whatsapp", "send_whatsapp", "send_message"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            action_params = {
                "intent": intent,
                "raw_message": params.get("message", ""),
                "contact": params.get("entities", {}).get("contact", ""),
                "trace_id": trace_id,
            }
            result = await execution_svc.execute_action("whatsapp", action_params)
            summary = result.get("summary") or result.get("message") or "Message action completed."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
            )
        except Exception as exc:
            logger.warning("WhatsAppCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
