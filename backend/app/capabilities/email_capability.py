"""
email_capability.py — Mitra Email Capability
Routes email intents through ExecutionService.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

class EmailCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "email"

    @property
    def description(self) -> str:
        return "Compose, read, search, and send emails."

    @property
    def supported_intents(self) -> List[str]:
        return ["email", "draft_email", "send_email", "read_emails", "search_emails"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            message = params.get("message", "")
            entities = params.get("entities", {})
            to_addr = ""
            if isinstance(entities.get("email"), list) and entities["email"]:
                to_addr = entities["email"][0]
            action_params = {
                "to": to_addr,
                "subject": "Message from Mitra",
                "body": message,
                "intent": intent,
                "raw_message": message,
                "trace_id": trace_id,
            }
            result = await execution_svc.execute_action("email", action_params)
            summary = result.get("summary") or result.get("message") or "Email action completed."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
                actions=[{"label": "View Draft", "action": "view_draft"}, {"label": "Send Now", "action": "send_email"}],
            )
        except Exception as exc:
            logger.warning("EmailCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
