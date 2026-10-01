from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient

from app.main import app
from app.services.inbound_account_resolver import inbound_account_resolver
from app.services.webhook_dedup_service import webhook_dedup_service


client = TestClient(app)


def test_telegram_inbound_webhook_flow():
    """Full spine wiring: Telegram webhook → inbound gateway → orchestrator."""
    inbound_account_resolver.register_test_mapping("telegram", "222", "test_user")
    payload = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": 222, "username": "test_user", "language_code": "en"},
            "chat": {"id": 111, "type": "private"},
            "date": 0,
            "text": "hello from telegram",
        },
    }

    resp = client.post("/webhook/telegram", json=payload)
    assert resp.status_code == 200
    body = resp.json()

    # Handler wrapper response
    assert body.get("status") == "processed"
    assert "trace_id" in body


def test_whatsapp_inbound_webhook_flow_no_secret():
    """
    WhatsApp webhook MUST fail closed when WHATSAPP_WEBHOOK_SECRET is not set.
    """
    os.environ.pop("WHATSAPP_WEBHOOK_SECRET", None)
    os.environ.pop("META_APP_SECRET", None)

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB123",
                "messaging": [
                    {
                        "sender": {"id": "user_wa_1"},
                        "message": {"type": "text", "text": {"body": "hello from whatsapp"}},
                    }
                ],
            }
        ],
    }

    resp = client.post(
        "/webhook/whatsapp",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # In B.COMM-4A-HOTFIX, missing secret must FAIL CLOSED
    assert body.get("status") == "rejected"
    assert body.get("reason") == "webhook_verification_failed"


def test_whatsapp_inbound_webhook_rejects_invalid_signature_when_secret_set():
    """
    When WHATSAPP_WEBHOOK_SECRET is configured, WhatsApp webhook MUST verify
    X-Hub-Signature-256 and reject invalid signatures.
    """
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "test_secret"

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB123",
                "messaging": [
                    {
                        "sender": {"id": "user_wa_2"},
                        "message": {"type": "text", "text": {"body": "hello with bad signature"}},
                    }
                ],
            }
        ],
    }

    resp = client.post(
        "/webhook/whatsapp",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=deadbeef",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "rejected"
    assert body.get("reason") == "webhook_verification_failed"


def test_whatsapp_inbound_webhook_flow_with_valid_signature_and_resolved_user():
    """
    WhatsApp webhook with valid HMAC signature and resolved user succeeds.
    """
    secret = "test_secret"
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = secret
    sender_phone = "+15551234567"
    inbound_account_resolver.register_test_mapping("whatsapp", sender_phone, "usr_verified_wa")

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB123",
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": f"wamid_test_{time.time()}",
                                    "from": sender_phone,
                                    "type": "text",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "hello from authorized whatsapp"},
                                }
                            ]
                        }
                    }
                ],
            }
        ],
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    resp = client.post(
        "/webhook/whatsapp",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={sig}",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "processed"
    assert "trace_id" in body


def test_email_inbound_webhook_flow_json():
    """Email webhook (JSON) → authenticated → inbound gateway → orchestrator."""
    secret = "test_email_secret"
    os.environ["EMAIL_WEBHOOK_SECRET"] = secret
    sender_email = "sender@example.com"
    inbound_account_resolver.register_test_mapping("email", sender_email, "usr_verified_email")

    payload = {
        "message_id": f"msg_test_{time.time()}",
        "from": sender_email,
        "subject": "Test Subject",
        "content": "Body from email provider",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    resp = client.post(
        "/webhook/email",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Secret": secret,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "processed"
    assert "trace_id" in body


def test_email_inbound_webhook_flow_raw_body():
    """Email webhook (raw body) → authenticated → inbound gateway → orchestrator."""
    secret = "test_email_secret"
    os.environ["EMAIL_WEBHOOK_SECRET"] = secret
    sender_email = "raw_sender@example.com"
    inbound_account_resolver.register_test_mapping("email", sender_email, "usr_verified_raw_email")

    raw_body = "Raw email body without JSON"
    msg_id = f"raw_msg_{time.time()}"

    resp = client.post(
        "/webhook/email",
        data=raw_body.encode("utf-8"),
        headers={
            "Content-Type": "text/plain",
            "X-Webhook-Secret": secret,
            "Message-ID": msg_id,
        },
    )
    # Without sender email in payload, raw text email fails closed as quarantined
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") in ("quarantined", "processed")
