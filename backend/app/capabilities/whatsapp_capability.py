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
        return [
            "telegram", "whatsapp", "send_whatsapp", "send_message",
            "SEND_MESSAGE", "DRAFT_MESSAGE", "READ_MESSAGES", "SEARCH_MESSAGES",
        ]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service

            # Security Requirement: User-owned WhatsApp actions must carry authenticated user context
            user_id = params.get("user_id")
            if not user_id or not str(user_id).strip() or str(user_id).strip().lower() in ("user_default", "default", "none", "null"):
                logger.warning("WhatsAppCapability rejected execution: missing or invalid authenticated user_id '%s'", user_id)
                return CapabilityResult.error_result(
                    self.name,
                    intent,
                    "Authentication required: user-owned WhatsApp actions require an authenticated user identity.",
                    trace_id
                )

            message = params.get("message", "")
            entities = params.get("entities", {})
            contact = entities.get("contact", "") or params.get("contact", "")

            # Regex for phone number extraction
            if not contact and message:
                match = re.search(r'\+?\d[\d\s\-]{7,15}\d', message)
                if match:
                    contact = match.group(0).replace(" ", "").replace("-", "")

            # Check explicit recipient in params
            if not contact and params.get("recipient"):
                contact = params.get("recipient")
            elif not contact and params.get("to"):
                contact = params.get("to")

            action_params = {
                "intent": intent,
                "raw_message": message,
                "message": message,
                "content": message,
                "to": contact,
                "recipient": contact,
                "contact": contact,
                "trace_id": trace_id,
                "user_id": str(user_id).strip(),
                "account_id": params.get("account_id"),
                "idempotency_key": params.get("idempotency_key"),
                "confirmation_confirmed": bool(params.get("confirmation_confirmed", False)),
                "is_system_action": False,
                "is_system_otp": False,
            }
            result = execution_svc.execute_action("whatsapp", action_params)

            if result.get("status") == "confirmation_required":
                return CapabilityResult(
                    capability=self.name,
                    intent=intent,
                    status="pending",
                    summary=result.get("message") or f"Confirmation required before sending WhatsApp message to {contact}.",
                    data=result,
                    actions=[
                        {"label": "Send Now", "action": f"Confirm send WhatsApp to {contact}"},
                        {"label": "Cancel", "action": "Cancel"}
                    ],
                    trace_id=trace_id,
                )
            elif result.get("status") in ("success", "sent", "accepted"):
                summary = (
                    result.get("summary")
                    or result.get("message")
                    or f"WhatsApp message sent to {contact}"
                )
                return CapabilityResult(
                    capability=self.name,
                    intent=intent,
                    status="success",
                    summary=summary,
                    data=result,
                    trace_id=trace_id,
                )
            else:
                err_msg = result.get("error") or result.get("message") or "WhatsApp execution failed"
                return CapabilityResult(
                    capability=self.name,
                    intent=intent,
                    status="error",
                    summary=f"WhatsApp failed: {err_msg}",
                    error=err_msg,
                    data=result,
                    trace_id=trace_id,
                )
        except Exception as exc:
            logger.warning("WhatsAppCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
