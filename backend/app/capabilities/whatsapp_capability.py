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
        return "Send WhatsApp, Telegram, and Instagram messages to contacts."

    @property
    def supported_intents(self) -> List[str]:
        return ["telegram", "whatsapp", "send_whatsapp", "send_telegram", "send_message", "instagram", "send_instagram"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            raw_message = params.get("message", "")
            entities = params.get("entities", {})
            contact = entities.get("contact", "") or params.get("contact", "")
            user_id = params.get("user_id", "user_default")

            # Determine platform action_type
            intent_lower = (intent or "").lower()
            msg_lower = (raw_message or "").lower()
            if "telegram" in intent_lower or "telegram" in msg_lower:
                action_type = "telegram"
            elif "instagram" in intent_lower or "instagram" in msg_lower:
                action_type = "instagram"
            else:
                action_type = "whatsapp"

            # Contact / Recipient extraction
            if not contact and raw_message:
                # Check for Telegram handle (@user), Instagram handle (@user), or phone number
                handle_match = re.search(r'to\s+(@[\w\+\-\.]+)', raw_message, re.IGNORECASE)
                phone_match = re.search(r'(\+?\d[\d\s\-]{7,15}\d)', raw_message)
                to_num_match = re.search(r'to\s+([\d\s\+\-]{7,16})', raw_message, re.IGNORECASE)
                if handle_match:
                    contact = handle_match.group(1)
                elif phone_match:
                    contact = re.sub(r'[^\d\+]', '', phone_match.group(1))
                elif to_num_match:
                    contact = re.sub(r'[^\d\+]', '', to_num_match.group(1))
                else:
                    handle_any = re.search(r'to\s+([^\s]+)', raw_message, re.IGNORECASE)
                    if handle_any:
                        contact = handle_any.group(1)

            # Message body extraction (strip "Send Telegram message to @user saying ")
            clean_message = raw_message
            saying_match = re.search(r'saying\s+(.+)$', raw_message, re.IGNORECASE)
            msg_prefix_match = re.search(r'message\s+(.+)$', raw_message, re.IGNORECASE)
            if saying_match:
                clean_message = saying_match.group(1).strip()
            elif msg_prefix_match:
                clean_message = msg_prefix_match.group(1).strip()

            action_params = {
                "intent": intent,
                "raw_message": raw_message,
                "message": clean_message,
                "to": contact,
                "recipient": contact,
                "contact": contact,
                "user_id": user_id,
                "trace_id": trace_id,
            }

            result = execution_svc.execute_action(action_type, action_params, trace_id=trace_id or "auto")
            status = "success" if result.get("status") == "success" else "failed"
            summary = result.get("summary") or result.get("note") or f"{action_type.capitalize()} message sent to {contact}" if status == "success" else f"{action_type.capitalize()} failed: {result.get('error', 'unknown error')}"

            return CapabilityResult(
                capability=action_type,
                intent=intent,
                status=status,
                summary=summary,
                data=result,
                trace_id=trace_id,
            )
        except Exception as exc:
            logger.warning("WhatsAppCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
