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
            msg_lower = (message or "").lower()
            entities = params.get("entities", {})

            # 1. Determine granular communication operation (SEND_MESSAGE, DRAFT_MESSAGE, READ_MESSAGES, SEARCH_MESSAGES)
            # Supported explicit intents or auto-detection from conversational message
            explicit_intent = (intent or "").strip().upper()
            if explicit_intent in ("READ_MESSAGES", "READ_EMAILS", "READ_INBOX", "READ"):
                comm_intent = "READ_MESSAGES"
            elif explicit_intent in ("SEARCH_MESSAGES", "SEARCH_EMAILS", "SEARCH"):
                comm_intent = "SEARCH_MESSAGES"
            elif explicit_intent in ("DRAFT_MESSAGE", "DRAFT_EMAIL", "DRAFT"):
                comm_intent = "DRAFT_MESSAGE"
            elif explicit_intent in ("SEND_MESSAGE", "SEND_EMAIL", "SEND"):
                comm_intent = "SEND_MESSAGE"
            else:
                # Conversational natural language classification:
                # Check DRAFT:
                draft_match = re.search(r'\b(create\s+(?:a\s+)?draft|save\s+(?:as\s+)?draft|make\s+(?:a\s+)?draft|compose\s+(?:a\s+)?draft|draft\s+(?:an?\s+)?(?:email|message)|draft)\b', msg_lower)
                # Check SEARCH:
                search_match = re.search(r'\b(search\s+(?:my\s+)?(?:inbox|emails?)|find\s+(?:emails?|messages?)|search\s+for\s+emails?|emails?\s+(?:containing|with|about))\b', msg_lower)
                # Check READ:
                read_match = re.search(r'\b(show\s+(?:me\s+)?(?:my\s+)?(?:latest|recent|unread|new)?\s*(?:\d+\s+)?emails?|read\s+(?:my\s+)?emails?|check\s+(?:my\s+)?(?:emails?|inbox)|list\s+(?:my\s+)?emails?|get\s+(?:my\s+)?(?:latest|recent)?\s*(?:\d+\s+)?emails?|fetch\s+(?:my\s+)?(?:latest|recent)?\s*(?:\d+\s+)?emails?|view\s+(?:my\s+)?emails?|inbox)\b', msg_lower)

                if draft_match:
                    comm_intent = "DRAFT_MESSAGE"
                elif search_match:
                    comm_intent = "SEARCH_MESSAGES"
                elif read_match:
                    comm_intent = "READ_MESSAGES"
                else:
                    comm_intent = "SEND_MESSAGE"

            # 2. Extract recipient (for DRAFT and SEND)
            to_addr = ""
            if isinstance(entities.get("email"), list) and entities["email"]:
                to_addr = entities["email"][0]
            if not to_addr and message:
                match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
                if match:
                    to_addr = match.group(0)
            if not to_addr and params.get("recipient"):
                to_addr = params.get("recipient")
            elif not to_addr and params.get("to"):
                to_addr = params.get("to")

            # 3. Extract Subject & Body / Content
            subject = params.get("subject")
            body = params.get("body") or params.get("content")

            # Extract saying / body from message if not provided
            if not body and message:
                saying_match = re.search(r'\b(?:saying|with\s+(?:the\s+)?(?:message|body|text)|body:?|message:?)\s+["\']?([^"\']+)["\']?$', message, re.IGNORECASE)
                if saying_match:
                    body = saying_match.group(1).strip()
                else:
                    body = message

            if not subject:
                subj_match = re.search(r'\b(?:subject:?|about|titled)\s+["\']?([^"\',]+)["\']?', message, re.IGNORECASE)
                if subj_match:
                    subject = subj_match.group(1).strip()
                else:
                    subject = "Message from Mitra AI"

            # 4. Extract query and limit for READ / SEARCH
            limit = params.get("limit") or 20
            limit_match = re.search(r'\b(?:latest|recent|top|first|show|read|get)\s+(\d+)\s+emails?\b', msg_lower)
            if not limit_match:
                limit_match = re.search(r'\b(\d+)\s+emails?\b', msg_lower)
            if limit_match:
                try:
                    limit = min(int(limit_match.group(1)), 100)
                except Exception:
                    limit = 20

            query = params.get("query")
            if not query and comm_intent == "SEARCH_MESSAGES" and message:
                q_match = re.search(r'\b(?:containing|with|about|for)\s+["\']?([^"\']+)["\']?$', message, re.IGNORECASE)
                if q_match:
                    query = q_match.group(1).strip()
                else:
                    query = message

            action_params = {
                "to": to_addr,
                "to_addr": to_addr,
                "recipient": to_addr,
                "subject": subject,
                "body": body,
                "content": body,
                "message": message,
                "intent": comm_intent,
                "query": query,
                "limit": limit,
                "raw_message": message,
                "trace_id": trace_id,
                "user_id": str(user_id).strip(),
                "account_id": params.get("account_id"),
                "idempotency_key": params.get("idempotency_key"),
                "confirmation_confirmed": bool(params.get("confirmation_confirmed", False)),
                "is_system_action": False,
            }
            result = execution_svc.execute_action("email", action_params)

            # 5. Formulate canonical capability response
            if result.get("status") == "confirmation_required":
                # INVARIANT: SEND_MESSAGE returns structured pending confirmation card
                summary_text = result.get("message") or "I've prepared the email. Please review and confirm before I send it."
                return CapabilityResult(
                    capability=self.name,
                    intent=comm_intent,
                    status="pending",
                    summary=summary_text,
                    data=result,
                    actions=[
                        {"label": "Send Now", "action": f"Confirm send email to {to_addr}"},
                        {"label": "Cancel", "action": "Cancel"}
                    ],
                    trace_id=trace_id,
                )
            elif result.get("status") in ("success", "sent", "accepted"):
                if comm_intent == "READ_MESSAGES":
                    msgs = result.get("messages", [])
                    if msgs:
                        lines = [f"Here are your latest {len(msgs)} emails:\n"]
                        for idx, m in enumerate(msgs[:10], 1):
                            snd = m.get("from") or "Unknown"
                            sbj = m.get("subject") or "(No Subject)"
                            dt = m.get("date") or ""
                            snp = m.get("snippet") or ""
                            lines.append(f"{idx}. **From:** {snd}\n   **Subject:** {sbj}\n   **Date:** {dt}\n   **Snippet:** {snp}")
                        summary_text = "\n\n".join(lines)
                    else:
                        summary_text = "Your inbox is clear. You have no new emails."
                elif comm_intent == "SEARCH_MESSAGES":
                    msgs = result.get("messages", [])
                    q_disp = query or "query"
                    if msgs:
                        lines = [f"Found {len(msgs)} emails matching '{q_disp}':\n"]
                        for idx, m in enumerate(msgs[:10], 1):
                            snd = m.get("from") or "Unknown"
                            sbj = m.get("subject") or "(No Subject)"
                            dt = m.get("date") or ""
                            snp = m.get("snippet") or ""
                            lines.append(f"{idx}. **From:** {snd}\n   **Subject:** {sbj}\n   **Date:** {dt}\n   **Snippet:** {snp}")
                        summary_text = "\n\n".join(lines)
                    else:
                        summary_text = f"No emails found matching '{q_disp}'."
                elif comm_intent == "DRAFT_MESSAGE":
                    summary_text = result.get("message") or (f"I created the draft for {to_addr}." if to_addr else "I created the draft email.")
                else:
                    summary_text = result.get("message") or f"Email sent to {to_addr}."

                return CapabilityResult(
                    capability=self.name,
                    intent=comm_intent,
                    status="success",
                    summary=summary_text,
                    data=result,
                    trace_id=trace_id,
                    actions=[{"label": "View Details", "action": "view_email"}],
                )
            else:
                err_msg = result.get("error") or result.get("message") or "Email execution failed"
                return CapabilityResult(
                    capability=self.name,
                    intent=comm_intent,
                    status="error",
                    summary=f"Email failed: {err_msg}",
                    error=err_msg,
                    data=result,
                    trace_id=trace_id,
                )
        except Exception as exc:
            logger.warning("EmailCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
