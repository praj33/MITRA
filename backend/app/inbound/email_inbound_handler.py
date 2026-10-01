from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request

from app.inbound.inbound_gateway import process_message
from app.services.inbound_account_resolver import inbound_account_resolver
from app.services.webhook_dedup_service import webhook_dedup_service

logger = logging.getLogger(__name__)

# Bounded replay window (5 minutes max age, 1 minute future drift)
MAX_WEBHOOK_AGE_SECONDS = 300
FUTURE_DRIFT_TOLERANCE_SECONDS = 60


def _verify_email_webhook(request: Request, raw_body: bytes) -> bool:
    """
    Verify Inbound Email webhook authentication.

    FAIL CLOSED INVARIANT:
    - If EMAIL_WEBHOOK_SECRET or INBOUND_EMAIL_WEBHOOK_SECRET is not configured or empty,
      verification FAILS IMMEDIATELY (returns False). NEVER returns True.
    - Supports:
      1. Header X-Webhook-Secret: constant-time comparison
      2. Header Authorization: Bearer <secret>: constant-time comparison
      3. Header X-Hub-Signature-256: sha256=HMAC_SHA256(secret, raw_body)
    - All token/signature comparisons use constant-time hmac.compare_digest.
    """
    secret = (os.getenv("EMAIL_WEBHOOK_SECRET") or os.getenv("INBOUND_EMAIL_WEBHOOK_SECRET") or "").strip()
    if not secret:
        logger.warning(
            "Email webhook verification failed: EMAIL_WEBHOOK_SECRET not configured (fail closed)."
        )
        return False

    # 1. Check X-Webhook-Secret or X-Email-Webhook-Secret
    webhook_secret_hdr = request.headers.get("X-Webhook-Secret") or request.headers.get("x-webhook-secret") or request.headers.get("X-Email-Webhook-Secret")
    if webhook_secret_hdr and hmac.compare_digest(webhook_secret_hdr.strip(), secret):
        return True

    # 2. Check Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.strip().lower().startswith("bearer "):
        bearer_token = auth_header.strip()[7:].strip()
        if hmac.compare_digest(bearer_token, secret):
            return True

    # 3. Check X-Hub-Signature-256 (HMAC SHA-256 over raw body)
    sig_header = request.headers.get("X-Hub-Signature-256") or request.headers.get("x-hub-signature-256")
    if sig_header and sig_header.startswith("sha256="):
        provided_sig = sig_header.split("=", 1)[1].strip()
        expected_sig = hmac.new(
            key=secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(provided_sig, expected_sig):
            return True

    logger.warning("Email webhook verification failed: invalid credentials or signature.")
    return False


def _validate_event_timestamp(timestamp_val: Any) -> tuple[bool, Optional[str]]:
    """Validate event timestamp against bounded replay window if provided."""
    if timestamp_val is None:
        return True, None  # Timestamp optional for email providers if event_id is present
    try:
        if isinstance(timestamp_val, (int, float)):
            ts = float(timestamp_val)
            if ts > 10**12:
                ts = ts / 1000.0
        elif isinstance(timestamp_val, str):
            # Parse ISO string
            clean_str = timestamp_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            ts = dt.timestamp()
        else:
            return True, None

        now_ts = datetime.now(timezone.utc).timestamp()
        age = now_ts - ts
        if age > MAX_WEBHOOK_AGE_SECONDS:
            return False, "event_timestamp_expired"
        if age < -FUTURE_DRIFT_TOLERANCE_SECONDS:
            return False, "event_timestamp_future"
        return True, None
    except Exception:
        return False, "invalid_timestamp"


async def handle_email_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive inbound email events and forward into the unified inbound gateway.

    SECURITY INVARIANTS:
    1. Authentication: Fail-closed verification (EMAIL_WEBHOOK_SECRET required).
    2. Replay Protection: Validates timestamp if present.
    3. Deduplication: Rejects already-processed email message IDs.
    4. Account Binding: Resolves sender/recipient email to a registered MITRA user_id.
       Unresolved events FAIL CLOSED and are quarantined; never triggers assistant.
    """
    try:
        raw_body = await request.body()
        if not _verify_email_webhook(request, raw_body):
            return {"status": "rejected", "reason": "webhook_verification_failed"}

        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                payload = json.loads(raw_body.decode("utf-8") or "{}")
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(exc)}") from exc
        else:
            payload = {"content": raw_body.decode("utf-8")}

        email_content = payload.get("content", "") or payload.get("text", "") or payload.get("body", "")
        sender = payload.get("from", payload.get("sender", ""))
        recipient = payload.get("to", payload.get("recipient", ""))
        subject = payload.get("subject", "No Subject")

        if not email_content:
            return {"status": "ignored", "reason": "empty_content"}

        # 1. Extract and Validate Provider Event / Message ID (Deduplication)
        event_id = (
            payload.get("message_id")
            or payload.get("Message-ID")
            or payload.get("id")
            or payload.get("event_id")
            or request.headers.get("Message-ID")
            or request.headers.get("message-id")
        )

        if not event_id:
            logger.warning("Email webhook rejected: missing provider message_id.")
            return {"status": "rejected", "reason": "missing_event_id"}

        # Atomic deduplication check
        if not webhook_dedup_service.check_and_record("email", str(event_id)):
            logger.warning("Email duplicate event ignored: %s", event_id)
            return {"status": "duplicate", "reason": "duplicate_event_ignored", "event_id": str(event_id)}

        # 2. Timestamp Replay Window Validation
        raw_ts = payload.get("timestamp") or payload.get("date") or payload.get("created_at")
        is_valid_ts, ts_reason = _validate_event_timestamp(raw_ts)
        if not is_valid_ts:
            logger.warning("Email event timestamp invalid/expired: %s (%s)", raw_ts, ts_reason)
            return {"status": "rejected", "reason": ts_reason or "invalid_timestamp", "event_id": str(event_id)}

        # 3. User / Account Binding (Zero Trust on External sender/email)
        resolved_user_id = inbound_account_resolver.resolve_user_id(
            platform="email",
            sender_identity=sender,
            recipient_identity=recipient,
            metadata=payload,
        )

        if not resolved_user_id:
            logger.warning(
                "Email event (from='%s', to='%s') not associated with any MITRA user account (fail closed / quarantined).",
                sender, recipient,
            )
            return {
                "status": "quarantined",
                "reason": "unresolved_account",
                "event_id": str(event_id),
                "sender": sender,
                "recipient": recipient,
                "message": "Email is not bound to any registered MITRA user.",
            }

        message_text = f"Subject: {subject}\n\n{email_content}"

        result = await process_message(
            platform="email",
            user_id=resolved_user_id,
            message=message_text,
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "provider": "email",
                "message_id": str(event_id),
                "sender": sender,
                "recipient": recipient,
                "resolved_user_id": resolved_user_id,
                "payload": payload,
            },
            device="desktop",
            preferred_language="auto",
            voice_input=False,
        )

        return {
            "status": "processed",
            "trace_id": result.get("trace_id"),
            "processed_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.error("Error in handle_email_webhook: %s", exc)
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(exc)}") from exc
