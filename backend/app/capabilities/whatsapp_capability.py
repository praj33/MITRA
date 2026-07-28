"""
whatsapp_capability.py — Mitra WhatsApp Capability
"""
from __future__ import annotations
import re
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
            message = params.get("message", "")
            entities = params.get("entities", {})
            contact = entities.get("contact", "") or params.get("contact", "")

            # Regex for phone number extraction
            if not contact and message:
                match = re.search(r'\+?\d[\d\s\-]{7,15}\d', message)
                if match:
                    contact = match.group(0).replace(" ", "").replace("-", "")

            action_params = {
                "intent": intent,
                "raw_message": message,
                "message": message,
                "to": contact,
                "recipient": contact,
                "contact": contact,
                "trace_id": trace_id,
            }
            result = execution_svc.execute_action("whatsapp", action_params)
            status = "success" if result.get("status") == "success" else "failed"
            summary = result.get("summary") or result.get("message") or f"WhatsApp message sent to {contact}" if status == "success" else f"WhatsApp failed: {result.get('error', 'unknown error')}"
            return CapabilityResult(
                capability=self.name, intent=intent, status=status,
                summary=summary, data=result, trace_id=trace_id,
            )
        except Exception as exc:
            logger.warning("WhatsAppCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
