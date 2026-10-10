from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from fastapi import HTTPException, Request

from app.inbound.inbound_gateway import process_message
from app.services.inbound_account_resolver import inbound_account_resolver
from app.services.webhook_dedup_service import webhook_dedup_service

logger = logging.getLogger(__name__)

# Bounded replay window (5 minutes max age, 1 minute future drift)
MAX_WEBHOOK_AGE_SECONDS = 300
FUTURE_DRIFT_TOLERANCE_SECONDS = 60


def _verify_whatsapp_webhook(request: Request, raw_body: bytes) -> bool:
    """
    Verify WhatsApp/META webhook signatures.

    FAIL CLOSED INVARIANT:
    - If WHATSAPP_WEBHOOK_SECRET or META_APP_SECRET is missing/empty,
      verification FAILS IMMEDIATELY (returns False). NEVER returns True.
    - Requires valid X-Hub-Signature-256 computed as sha256=HMAC_SHA256(secret, raw_body).
    - Constant-time comparison using hmac.compare_digest.
    """
    secret = (os.getenv("WHATSAPP_WEBHOOK_SECRET") or os.getenv("META_APP_SECRET") or "").strip()
    if not secret:
        logger.warning(
            "WhatsApp webhook verification failed: WHATSAPP_WEBHOOK_SECRET not configured (fail closed)."
        )
        return False

    signature_header = request.headers.get("X-Hub-Signature-256") or request.headers.get(
        "x-hub-signature-256"
    )
    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("WhatsApp webhook missing or invalid X-Hub-Signature-256 header.")
        return False

    provided_sig = signature_header.split("=", 1)[1].strip()
    expected_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(provided_sig, expected_sig)


def _validate_event_timestamp(timestamp_val: Any) -> tuple[bool, Optional[str]]:
    """Validate event timestamp against bounded replay window."""
    if timestamp_val is None:
        return False, "missing_timestamp"
    try:
        ts = float(timestamp_val)
        if ts > 10**12:
            ts = ts / 1000.0
        now_ts = datetime.now(timezone.utc).timestamp()
        age = now_ts - ts
        if age > MAX_WEBHOOK_AGE_SECONDS:
            return False, "event_timestamp_expired"
        if age < -FUTURE_DRIFT_TOLERANCE_SECONDS:
            return False, "event_timestamp_future"
        return True, None
    except Exception:
        return False, "invalid_timestamp"


def _to_iso_timestamp(value: Any) -> str:
    if value is None:
        return datetime.utcnow().isoformat()
    try:
        ts = float(value)
        if ts > 10**12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return datetime.utcnow().isoformat()


def _iter_whatsapp_messages(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    entries = payload.get("entry", []) or []
    for entry in entries:
        # WhatsApp Cloud API shape
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            # Status delivery receipts (sent, delivered, read, failed)
            for status in value.get("statuses", []) or []:
                yield {
                    "source": "status",
                    "entry": entry,
                    "change": change,
                    "value": value,
                    "status_item": status,
                }
            # Inbound messages
            for message in value.get("messages", []) or []:
                yield {
                    "source": "cloud",
                    "entry": entry,
                    "change": change,
                    "value": value,
                    "message": message,
                }

        # Legacy/compat Messenger-like shape
        for event in entry.get("messaging", []) or []:
            if event.get("message"):
                yield {
                    "source": "legacy",
                    "entry": entry,
                    "event": event,
                    "message": event.get("message") or {},
                }


async def handle_whatsapp_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive WhatsApp webhook events and forward into the unified inbound gateway.

    SECURITY INVARIANTS:
    1. Authentication: Fail-closed signature verification against raw body.
    2. Replay Protection: Validates event timestamp within bounded 5-minute window.
    3. Deduplication: Rejects already-processed provider message IDs.
    4. Account Binding: Resolves external sender phone to a registered MITRA user_id.
       Unresolved events FAIL CLOSED and are quarantined; never triggers assistant.
    5. Delivery Statuses: Acknowledges delivery status receipts without triggering assistant.
    """
    try:
        raw_body = await request.body()
        if not _verify_whatsapp_webhook(request, raw_body):
            return {"status": "rejected", "reason": "webhook_verification_failed"}

        try:
            payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8") or "{}")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(exc)}") from exc

        messages = list(_iter_whatsapp_messages(payload))
        if not messages:
            return {"status": "ignored", "reason": "no_message_events"}

        processed = []
        ignored = []

        for item in messages:
            source = item.get("source")

            # 1. Delivery Status Receipt Handling (Acknowledge safely)
            if source == "status":
                status_item = item.get("status_item") or {}
                ignored.append({
                    "reason": "status_update_acknowledged",
                    "status": status_item.get("status"),
                    "recipient_id": status_item.get("recipient_id"),
                    "message_id": status_item.get("id"),
                })
                continue

            message = item.get("message") or {}

            # 2. Extract and Validate Provider Message ID (Deduplication)
            event_id = message.get("id") or message.get("MessageSid")
            if not event_id and source == "legacy":
                event_id = (item.get("event") or {}).get("message", {}).get("mid")

            if not event_id:
                logger.warning("WhatsApp message rejected: missing provider event ID.")
                ignored.append({"reason": "missing_event_id"})
                continue

            # Atomic deduplication check
            if not webhook_dedup_service.check_and_record("whatsapp", event_id):
                logger.warning("WhatsApp duplicate event ignored: %s", event_id)
                ignored.append({"reason": "duplicate_event_ignored", "event_id": event_id})
                continue

            # 3. Timestamp Replay Window Validation
            raw_ts = message.get("timestamp")
            if not raw_ts and source == "legacy":
                raw_ts = (item.get("event") or {}).get("timestamp")

            is_valid_ts, ts_reason = _validate_event_timestamp(raw_ts)
            if not is_valid_ts:
                logger.warning("WhatsApp message timestamp invalid/expired: %s (%s)", raw_ts, ts_reason)
                ignored.append({"reason": ts_reason or "invalid_timestamp", "event_id": event_id})
                continue

            # 4. Message Content Extraction
            if source == "cloud":
                msg_type = message.get("type")
                if msg_type != "text":
                    ignored.append({"reason": f"unsupported_message_type:{msg_type}", "event_id": event_id})
                    continue
                text_body = (message.get("text") or {}).get("body")
                if not text_body:
                    ignored.append({"reason": "missing_text_body", "event_id": event_id})
                    continue

                value = item.get("value") or {}
                contacts = value.get("contacts") or []
                sender_phone = message.get("from") or (contacts[0].get("wa_id") if contacts else "")

                # 5. User / Account Binding (Zero Trust on External sender_id)
                resolved_user_id = inbound_account_resolver.resolve_user_id(
                    platform="whatsapp",
                    sender_identity=sender_phone,
                    metadata=value.get("metadata"),
                )
                if not resolved_user_id:
                    logger.warning(
                        "WhatsApp sender '%s' not associated with any MITRA user account (fail closed / quarantined).",
                        sender_phone,
                    )
                    ignored.append({
                        "reason": "unresolved_account",
                        "event_id": event_id,
                        "sender": sender_phone,
                        "message": "Sender is not bound to any registered MITRA user.",
                    })
                    continue

                result = await process_message(
                    platform="whatsapp",
                    user_id=resolved_user_id,
                    message=text_body,
                    timestamp=_to_iso_timestamp(raw_ts),
                    metadata={
                        "provider": "whatsapp",
                        "source": "cloud",
                        "message_id": event_id,
                        "sender_phone": sender_phone,
                        "resolved_user_id": resolved_user_id,
                        "contacts": contacts,
                        "metadata": value.get("metadata"),
                        "event": item,
                    },
                    device="mobile",
                    preferred_language="auto",
                    voice_input=False,
                )
                processed.append(result)
                continue

            # Legacy webhook payloads
            if source == "legacy":
                text_value = message.get("text")
                if isinstance(text_value, dict):
                    text_value = text_value.get("body")
                if not text_value:
                    ignored.append({"reason": "missing_text_body", "event_id": event_id})
                    continue

                event = item.get("event") or {}
                sender_phone = (event.get("sender") or {}).get("id", "")

                resolved_user_id = inbound_account_resolver.resolve_user_id(
                    platform="whatsapp",
                    sender_identity=sender_phone,
                    metadata=event,
                )
                if not resolved_user_id:
                    logger.warning(
                        "Legacy WhatsApp sender '%s' not associated with any MITRA user account (fail closed).",
                        sender_phone,
                    )
                    ignored.append({
                        "reason": "unresolved_account",
                        "event_id": event_id,
                        "sender": sender_phone,
                        "message": "Sender is not bound to any registered MITRA user.",
                    })
                    continue

                result = await process_message(
                    platform="whatsapp",
                    user_id=resolved_user_id,
                    message=str(text_value),
                    timestamp=_to_iso_timestamp(raw_ts),
                    metadata={
                        "provider": "whatsapp",
                        "source": "legacy",
                        "message_id": event_id,
                        "sender_phone": sender_phone,
                        "resolved_user_id": resolved_user_id,
                        "event": event,
                    },
                    device="mobile",
                    preferred_language="auto",
                    voice_input=False,
                )
                processed.append(result)

        if not processed:
            # Check reasons to return accurate non-execution status
            first_reason = ignored[0].get("reason") if ignored else "no_supported_messages"
            if first_reason == "unresolved_account":
                return {"status": "quarantined", "reason": "unresolved_account", "ignored": ignored}
            elif first_reason == "duplicate_event_ignored":
                return {"status": "duplicate", "reason": "duplicate_event_ignored", "ignored": ignored}
            elif first_reason in ("event_timestamp_expired", "event_timestamp_future"):
                return {"status": "rejected", "reason": first_reason, "ignored": ignored}
            elif first_reason == "status_update_acknowledged":
                return {"status": "acknowledged", "reason": "status_update_acknowledged", "ignored": ignored}
            return {"status": "ignored", "reason": first_reason, "ignored": ignored}

        return {
            "status": "processed",
            "count": len(processed),
            "trace_id": processed[0].get("trace_id"),
            "processed_at": datetime.utcnow().isoformat(),
            "ignored": ignored,
        }
    except Exception as exc:
        logger.error("Error in handle_whatsapp_webhook: %s", exc)
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(exc)}") from exc
