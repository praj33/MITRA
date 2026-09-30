"""
backend/app/services/communication_service.py — Unified Communication Service

Central orchestration layer for all MITRA communication:
- Enforces authenticated user identity
- Performs account ownership verification
- Enforces centralized approval policy (confirmation_required on SEND_MESSAGE)
- Ensures provider executor is NEVER invoked without explicit confirmation
- Normalizes provider responses into standardized delivery states
- Guarantees zero credential leakage
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.models.communication import (
    CommunicationAction,
    CommunicationChannel,
    CommunicationConfirmationPayload,
    CommunicationIntent,
    CommunicationResult,
    CommunicationStatus,
    DeliveryState,
    FORBIDDEN_CREDENTIAL_KEYS,
)
from app.services.connected_account_service import connected_account_service
from app.executors.email_executor import EmailExecutor
from app.executors.whatsapp_executor import WhatsAppExecutor

logger = logging.getLogger(__name__)


class CommunicationService:
    """
    Central provider-independent communication orchestrator.
    Handles approval policy, account resolution, and executor dispatch.
    """

    def __init__(
        self,
        email_executor: Optional[EmailExecutor] = None,
        whatsapp_executor: Optional[WhatsAppExecutor] = None,
    ):
        self.email_executor = email_executor or EmailExecutor()
        self.whatsapp_executor = whatsapp_executor or WhatsAppExecutor()

    def evaluate_approval_policy(self, intent: CommunicationIntent) -> bool:
        """
        Centralized approval decision:
        - READ_MESSAGES: no confirmation required (False)
        - SEARCH_MESSAGES: no confirmation required (False)
        - DRAFT_MESSAGE: no confirmation required (False)
        - SEND_MESSAGE: explicit confirmation required (True)
        """
        if intent == CommunicationIntent.SEND_MESSAGE:
            return True
        return False

    def resolve_sender_account(
        self, user_id: str, channel: CommunicationChannel, account_id: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Resolve the user's sender account identity and verify ownership.
        Returns (sender_identifier, error_code).
        If account_id is supplied, verifies it belongs to user_id.
        """
        if channel == CommunicationChannel.EMAIL:
            # Check Gmail connection
            gmail_conn = connected_account_service.get_user_connection(user_id=user_id, provider="gmail")
            # Check Microsoft connection
            ms_conn = connected_account_service.get_user_connection(user_id=user_id, provider="microsoft")

            matched_email = None
            if gmail_conn and gmail_conn.get("email"):
                matched_email = gmail_conn.get("email")
            elif ms_conn and ms_conn.get("email"):
                matched_email = ms_conn.get("email")

            # Check custom SMTP integration in DB
            if not matched_email:
                try:
                    from app.executors.email_executor import _get_db
                    db = _get_db()
                    if db is not None:
                        doc = db["user_integrations"].find_one({"user_id": user_id})
                        if doc and "smtp" in doc and doc["smtp"].get("username"):
                            matched_email = doc["smtp"].get("username")
                        elif doc and "gmail" in doc and doc["gmail"].get("email"):
                            matched_email = doc["gmail"].get("email")
                except Exception as exc:
                    logger.debug("Error querying user_integrations: %s", exc)

            if account_id:
                # If specific account_id requested, ensure it matches user's owned account
                if matched_email and account_id.lower() == matched_email.lower():
                    return matched_email, None
                # Check provider account ID
                if gmail_conn and gmail_conn.get("provider_account_id") == account_id:
                    return gmail_conn.get("email"), None
                if ms_conn and ms_conn.get("provider_account_id") == account_id:
                    return ms_conn.get("email"), None
                return None, "ACCOUNT_NOT_AUTHORIZED"

            return matched_email, None

        elif channel == CommunicationChannel.WHATSAPP:
            wa_conn = connected_account_service.get_user_connection(user_id=user_id, provider="whatsapp")
            matched_phone = None
            if wa_conn and (wa_conn.get("email") or wa_conn.get("provider_account_id")):
                matched_phone = wa_conn.get("email") or wa_conn.get("provider_account_id")

            if not matched_phone:
                try:
                    from app.executors.whatsapp_executor import _get_db
                    # check user_integrations
                    from pymongo import MongoClient
                    import os
                    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
                    db_name = os.getenv("DATABASE_NAME", "ai_assistant")
                    client = MongoClient(uri, serverSelectionTimeoutMS=1000)
                    doc = client[db_name]["user_integrations"].find_one({"user_id": user_id})
                    if doc and "whatsapp" in doc and doc["whatsapp"].get("phone"):
                        matched_phone = doc["whatsapp"].get("phone")
                except Exception:
                    pass

            if account_id:
                if matched_phone and account_id == matched_phone:
                    return matched_phone, None
                return None, "ACCOUNT_NOT_AUTHORIZED"

            return matched_phone, None

        return None, None

    def execute_action(
        self,
        action: CommunicationAction,
        trace_id: Optional[str] = None,
    ) -> CommunicationResult:
        """
        Execute a canonical communication action adhering to the unified contract:
        1. Authenticated user validation (fail closed)
        2. Account ownership check
        3. Centralized approval policy (confirmation check)
        4. Outbound provider execution
        5. Normalized result mapping with asynchronous delivery state
        """
        now_iso = datetime.utcnow().isoformat()
        trace_id = trace_id or f"comm_{uuid.uuid4().hex[:12]}"

        # ── 1. Authenticated User Binding ──
        user_id = action.user_id
        if not user_id or not str(user_id).strip() or str(user_id).strip().lower() in ("user_default", "default", "none", "null", "anonymous"):
            return CommunicationResult(
                status="failed",
                delivery_state="failed",
                channel=action.channel,
                error_code="AUTH_REQUIRED",
                error="Authorization error: user-owned communication actions require an authenticated user_id.",
                message="Authentication required.",
                action=action.to_dict(),
                trace_id=trace_id,
                timestamp=now_iso,
            )

        # ── 2. Account Resolution & Ownership Verification ──
        sender_account, account_err = self.resolve_sender_account(
            user_id=user_id, channel=action.channel, account_id=action.account_id
        )
        if account_err == "ACCOUNT_NOT_AUTHORIZED":
            return CommunicationResult(
                status="failed",
                delivery_state="failed",
                channel=action.channel,
                error_code="ACCOUNT_NOT_AUTHORIZED",
                error=f"Authorization error: account_id '{action.account_id}' does not belong to authenticated user.",
                message="Specified account is not authorized for this user.",
                action=action.to_dict(),
                trace_id=trace_id,
                timestamp=now_iso,
            )

        # ── 3. Centralized Approval Policy ──
        requires_confirmation = self.evaluate_approval_policy(action.intent)

        if requires_confirmation and not action.confirmation_confirmed:
            # Generate or preserve idempotency key
            idempotency_key = action.idempotency_key or f"idem_{uuid.uuid4().hex[:16]}"
            action.idempotency_key = idempotency_key

            confirmation_payload = CommunicationConfirmationPayload(
                channel=action.channel,
                sender_account=sender_account,
                recipient=action.recipient,
                subject=action.subject,
                content=action.content,
                action="SEND_MESSAGE",
                idempotency_key=idempotency_key,
                requires_confirmation=True,
            )

            logger.info(
                "Approval policy: SEND_MESSAGE requires explicit confirmation for user '%s' on %s",
                user_id, action.channel.value
            )

            # Invariant: Provider executor MUST NOT be reached
            return CommunicationResult(
                status="confirmation_required",
                delivery_state="pending",
                channel=action.channel,
                sender_account=sender_account,
                recipient=action.recipient,
                error_code="CONFIRMATION_REQUIRED",
                message="Explicit confirmation is required before sending this message.",
                confirmation=confirmation_payload.to_dict(),
                action=action.to_dict(),
                idempotency_key=idempotency_key,
                trace_id=trace_id,
                timestamp=now_iso,
            )

        # ── 4. Non-Send Intents (Draft, Read, Search) ──
        if action.intent == CommunicationIntent.DRAFT_MESSAGE:
            return CommunicationResult(
                status="accepted",
                delivery_state="pending",
                channel=action.channel,
                sender_account=sender_account,
                recipient=action.recipient,
                message=f"Draft message created for {action.recipient}.",
                action=action.to_dict(),
                idempotency_key=action.idempotency_key,
                trace_id=trace_id,
                timestamp=now_iso,
            )

        if action.intent in (CommunicationIntent.READ_MESSAGES, CommunicationIntent.SEARCH_MESSAGES):
            return CommunicationResult(
                status="accepted",
                delivery_state="unknown",
                channel=action.channel,
                sender_account=sender_account,
                recipient=action.recipient,
                message=f"Communication query '{action.intent.value}' accepted for {action.channel.value}.",
                action=action.to_dict(),
                trace_id=trace_id,
                timestamp=now_iso,
            )

        # ── 5. Provider Execution (SEND_MESSAGE confirmed) ──
        if action.channel == CommunicationChannel.EMAIL:
            if not action.recipient:
                return CommunicationResult(
                    status="failed",
                    delivery_state="failed",
                    channel=action.channel,
                    error_code="INVALID_RECIPIENT",
                    error="Recipient email address is required.",
                    message="Missing recipient.",
                    action=action.to_dict(),
                    trace_id=trace_id,
                    timestamp=now_iso,
                )

            exec_res = self.email_executor.send_message(
                to_email=action.recipient,
                subject=action.subject or "Message from Mitra AI",
                message=action.content or "",
                trace_id=trace_id,
                user_id=user_id,
                is_system_action=False,
            )

            # Map executor output to standardized CommunicationResult
            if exec_res.get("status") == "success":
                # INVARIANT: Provider API acceptance MUST NOT automatically be represented as DELIVERED
                return CommunicationResult(
                    status="sent",
                    delivery_state="sent",  # Marked as sent, delivery state pending actual delivery confirmation
                    channel=action.channel,
                    provider=exec_res.get("provider") or exec_res.get("method") or "email",
                    sender_account=exec_res.get("from") or sender_account,
                    recipient=action.recipient,
                    provider_message_id=exec_res.get("message_id") or exec_res.get("id"),
                    message=f"Email successfully sent to {action.recipient}.",
                    action=action.to_dict(),
                    idempotency_key=action.idempotency_key,
                    trace_id=trace_id,
                    timestamp=now_iso,
                )
            else:
                err_msg = exec_res.get("error", "Email dispatch failed.")
                err_code = "ACCOUNT_NOT_CONNECTED" if "No connected email account" in err_msg else "DELIVERY_FAILED"
                return CommunicationResult(
                    status="failed",
                    delivery_state="failed",
                    channel=action.channel,
                    provider=exec_res.get("provider") or "email",
                    sender_account=sender_account,
                    recipient=action.recipient,
                    error_code=err_code,
                    error=err_msg,
                    message=f"Email delivery failed: {err_msg}",
                    action=action.to_dict(),
                    idempotency_key=action.idempotency_key,
                    trace_id=trace_id,
                    timestamp=now_iso,
                )

        elif action.channel == CommunicationChannel.WHATSAPP:
            if not action.recipient:
                return CommunicationResult(
                    status="failed",
                    delivery_state="failed",
                    channel=action.channel,
                    error_code="INVALID_RECIPIENT",
                    error="Recipient WhatsApp phone number is required.",
                    message="Missing recipient.",
                    action=action.to_dict(),
                    trace_id=trace_id,
                    timestamp=now_iso,
                )

            exec_res = self.whatsapp_executor.send_message(
                to_number=action.recipient,
                message=action.content or "",
                trace_id=trace_id,
                user_id=user_id,
                is_system_otp=False,
            )

            # Current invariant: User-owned WhatsApp requires Meta WhatsApp Business
            if exec_res.get("status") == "success":
                return CommunicationResult(
                    status="sent",
                    delivery_state="pending",  # Asynchronous delivery invariant
                    channel=action.channel,
                    provider="meta_whatsapp",
                    sender_account=sender_account,
                    recipient=action.recipient,
                    provider_message_id=exec_res.get("message_sid"),
                    message=f"WhatsApp message sent to {action.recipient}.",
                    action=action.to_dict(),
                    idempotency_key=action.idempotency_key,
                    trace_id=trace_id,
                    timestamp=now_iso,
                )
            else:
                err_msg = exec_res.get("error", "WhatsApp dispatch failed.")
                err_code = exec_res.get("error_code") or "WHATSAPP_BUSINESS_REQUIRED"
                return CommunicationResult(
                    status="failed",
                    delivery_state="failed",
                    channel=action.channel,
                    provider="whatsapp",
                    sender_account=sender_account,
                    recipient=action.recipient,
                    error_code=err_code,
                    error=err_msg,
                    message=f"WhatsApp failed: {err_msg}",
                    action=action.to_dict(),
                    idempotency_key=action.idempotency_key,
                    trace_id=trace_id,
                    timestamp=now_iso,
                )

        return CommunicationResult(
            status="failed",
            delivery_state="failed",
            channel=action.channel,
            error_code="CONFIGURATION_REQUIRED",
            error=f"Unsupported communication channel: {action.channel}",
            action=action.to_dict(),
            trace_id=trace_id,
            timestamp=now_iso,
        )


# Global singleton instance
communication_service = CommunicationService()
