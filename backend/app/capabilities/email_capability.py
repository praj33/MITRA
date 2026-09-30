"""
email_capability.py — Mitra Email Capability
Routes email intents through ExecutionService.
"""
from __future__ import annotations
import re
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
        return [
            "email", "draft_email", "send_email", "read_emails", "search_emails",
            "SEND_MESSAGE", "DRAFT_MESSAGE", "READ_MESSAGES", "SEARCH_MESSAGES",
        ]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service

            # Security Requirement: User-owned email actions must carry authenticated user context
            user_id = params.get("user_id")
            if not user_id or not str(user_id).strip() or str(user_id).strip().lower() in ("user_default", "default", "none", "null"):
                logger.warning("EmailCapability rejected execution: missing or invalid authenticated user_id '%s'", user_id)
                return CapabilityResult.error_result(
                    self.name,
                    intent,
                    "Authentication required: user-owned email actions require an authenticated user identity.",
                    trace_id
                )

            message = params.get("message", "")
            entities = params.get("entities", {})
            to_addr = ""
            if isinstance(entities.get("email"), list) and entities["email"]:
                to_addr = entities["email"][0]

            # Fallback regex extraction if entity missing
            if not to_addr and message:
                match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
                if match:
                    to_addr = match.group(0)

            # Check explicit recipient in params
            if not to_addr and params.get("recipient"):
                to_addr = params.get("recipient")
            elif not to_addr and params.get("to"):
                to_addr = params.get("to")

            # Subject extraction
            subject = params.get("subject") or "Message from Mitra AI"
            body = params.get("body") or params.get("content") or message

            action_params = {
                "to": to_addr,
                "recipient": to_addr,
                "subject": subject,
                "body": body,
                "content": body,
                "message": message,
                "intent": intent,
                "raw_message": message,
                "trace_id": trace_id,
                "user_id": str(user_id).strip(),
                "account_id": params.get("account_id"),
                "idempotency_key": params.get("idempotency_key"),
                "confirmation_confirmed": bool(params.get("confirmation_confirmed", False)),
                "is_system_action": False,
            }
            result = execution_svc.execute_action("email", action_params)

            if result.get("status") == "confirmation_required":
                return CapabilityResult(
                    capability=self.name,
                    intent=intent,
                    status="pending",
                    summary=result.get("message") or f"Confirmation required before sending email to {to_addr}.",
                    data=result,
                    actions=[
                        {"label": "Send Now", "action": f"Confirm send email to {to_addr}"},
                        {"label": "Cancel", "action": "Cancel"}
                    ],
                    trace_id=trace_id,
                )
            elif result.get("status") in ("success", "sent", "accepted"):
                summary = (
                    result.get("summary")
                    or result.get("message")
                    or f"Email sent to {to_addr}"
                )
                return CapabilityResult(
                    capability=self.name,
                    intent=intent,
                    status="success",
                    summary=summary,
                    data=result,
                    trace_id=trace_id,
                    actions=[{"label": "View Details", "action": "view_email"}],
                )
            else:
                err_msg = result.get("error") or result.get("message") or "Email execution failed"
                return CapabilityResult(
                    capability=self.name,
                    intent=intent,
                    status="error",
                    summary=f"Email failed: {err_msg}",
                    error=err_msg,
                    data=result,
                    trace_id=trace_id,
                )
        except Exception as exc:
            logger.warning("EmailCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
