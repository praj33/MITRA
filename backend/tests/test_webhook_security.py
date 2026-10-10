"""
tests/test_webhook_security.py — Public Inbound Webhook Security Hardening Tests

Comprehensive test suite verifying Phase B.COMM-4A-HOTFIX invariants:
1. WhatsApp webhook with missing secret -> rejected (fail-closed)
2. WhatsApp webhook with invalid signature -> rejected
3. WhatsApp webhook with valid signature -> accepted at authentication layer
4. Email webhook without authentication -> rejected
5. Email webhook with invalid authentication -> rejected
6. Email webhook with valid authentication -> accepted at authentication layer
7. Unknown external identity -> rejected/quarantined (fail-closed)
8. sender_id cannot become MITRA user_id (zero trust)
9. duplicate provider event -> rejected/no second execution
10. old/replayed event -> rejected where timestamp validation applies
11. webhook authentication failure cannot trigger assistant execution
12. secrets never appear in normalized errors/log output
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.inbound_account_resolver import inbound_account_resolver
from app.services.webhook_dedup_service import webhook_dedup_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Ensure test environment variables and in-memory test states are clean before each test."""
    inbound_account_resolver.clear_test_mappings()
    webhook_dedup_service.clear_for_testing()
    yield
    inbound_account_resolver.clear_test_mappings()
    webhook_dedup_service.clear_for_testing()
    os.environ.pop("WHATSAPP_WEBHOOK_SECRET", None)
    os.environ.pop("META_APP_SECRET", None)
    os.environ.pop("EMAIL_WEBHOOK_SECRET", None)
    os.environ.pop("INBOUND_EMAIL_WEBHOOK_SECRET", None)


# ── TEST 1: WHATSAPP WEBHOOK WITH MISSING SECRET MUST FAIL CLOSED ──────────────

def test_1_whatsapp_webhook_missing_secret_fails_closed():
    """IF WHATSAPP_WEBHOOK_SECRET is missing/empty, reject webhook verification."""
    os.environ.pop("WHATSAPP_WEBHOOK_SECRET", None)
    os.environ.pop("META_APP_SECRET", None)

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB_UNAUTH",
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid_no_sec_1",
                                    "from": "+15550001111",
                                    "type": "text",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "unauthorized attempt"},
                                }
                            ]
                        }
                    }
                ],
            }
        ],
    }

    resp = client.post(
        "/webhook/whatsapp",
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "rejected"
    assert data.get("reason") == "webhook_verification_failed"


# ── TEST 2: WHATSAPP WEBHOOK WITH INVALID SIGNATURE IS REJECTED ────────────────

def test_2_whatsapp_webhook_invalid_signature_rejected():
    """WhatsApp webhook with mismatched X-Hub-Signature-256 MUST be rejected."""
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "super_secret_wa_key"

    raw_body = json.dumps({"test": "data"}).encode("utf-8")
    resp = client.post(
        "/webhook/whatsapp",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "rejected"
    assert data.get("reason") == "webhook_verification_failed"


# ── TEST 3: WHATSAPP WEBHOOK WITH VALID SIGNATURE ACCEPTED AT AUTH LAYER ───────

def test_3_whatsapp_webhook_valid_signature_accepted():
    """WhatsApp webhook with valid HMAC SHA-256 signature passes the auth layer."""
    secret = "legit_wa_secret"
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = secret

    sender_phone = "+15551234567"
    inbound_account_resolver.register_test_mapping("whatsapp", sender_phone, "usr_alice_123")

    event_id = f"wamid_valid_{int(time.time())}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB_LEGIT",
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": event_id,
                                    "from": sender_phone,
                                    "type": "text",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "valid authenticated message"},
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
    data = resp.json()
    assert data.get("status") == "processed"
    assert "trace_id" in data


# ── TEST 4: EMAIL WEBHOOK WITHOUT AUTHENTICATION REJECTED ──────────────────────

def test_4_email_webhook_without_auth_rejected():
    """Email webhook without credentials must be rejected immediately (fail closed)."""
    os.environ.pop("EMAIL_WEBHOOK_SECRET", None)
    os.environ.pop("INBOUND_EMAIL_WEBHOOK_SECRET", None)

    payload = {
        "message_id": "msg_unauth_1",
        "from": "stranger@evil.com",
        "to": "support@mitra.ai",
        "subject": "Attack",
        "content": "Malicious payload",
    }

    resp = client.post("/webhook/email", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "rejected"
    assert data.get("reason") == "webhook_verification_failed"


# ── TEST 5: EMAIL WEBHOOK WITH INVALID AUTHENTICATION REJECTED ─────────────────

def test_5_email_webhook_invalid_auth_rejected():
    """Email webhook with invalid secret/signature must be rejected."""
    os.environ["EMAIL_WEBHOOK_SECRET"] = "correct_email_secret_123"

    payload = {
        "message_id": "msg_bad_auth_1",
        "from": "bob@example.com",
        "content": "Test email",
    }

    # Test 5a: Wrong X-Webhook-Secret header
    resp1 = client.post(
        "/webhook/email",
        json=payload,
        headers={"X-Webhook-Secret": "wrong_secret"},
    )
    assert resp1.status_code == 200
    assert resp1.json().get("status") == "rejected"

    # Test 5b: Wrong Bearer token
    resp2 = client.post(
        "/webhook/email",
        json=payload,
        headers={"Authorization": "Bearer wrong_bearer_token"},
    )
    assert resp2.status_code == 200
    assert resp2.json().get("status") == "rejected"

    # Test 5c: Wrong HMAC signature
    resp3 = client.post(
        "/webhook/email",
        json=payload,
        headers={"X-Hub-Signature-256": "sha256=badbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadb"},
    )
    assert resp3.status_code == 200
    assert resp3.json().get("status") == "rejected"


# ── TEST 6: EMAIL WEBHOOK WITH VALID AUTHENTICATION ACCEPTED ───────────────────

def test_6_email_webhook_valid_auth_accepted():
    """Email webhook with correct secret or signature passes authentication."""
    secret = "verified_email_secret_456"
    os.environ["EMAIL_WEBHOOK_SECRET"] = secret

    sender_email = "authorized_user@example.com"
    inbound_account_resolver.register_test_mapping("email", sender_email, "usr_carol_789")

    # 6a: Test via X-Webhook-Secret header
    payload_a = {
        "message_id": f"msg_valid_a_{int(time.time())}",
        "from": sender_email,
        "subject": "Hello Mitra",
        "content": "Authentic inbound email text",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    resp_a = client.post(
        "/webhook/email",
        json=payload_a,
        headers={"X-Webhook-Secret": secret},
    )
    assert resp_a.status_code == 200
    assert resp_a.json().get("status") == "processed"

    # 6b: Test via HMAC-SHA256 signature
    payload_b = {
        "message_id": f"msg_valid_b_{int(time.time())}",
        "from": sender_email,
        "subject": "Hello Mitra via HMAC",
        "content": "Authentic inbound email text via HMAC",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    raw_b = json.dumps(payload_b).encode("utf-8")
    sig_b = hmac.new(secret.encode("utf-8"), raw_b, hashlib.sha256).hexdigest()

    resp_b = client.post(
        "/webhook/email",
        data=raw_b,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={sig_b}",
        },
    )
    assert resp_b.status_code == 200
    assert resp_b.json().get("status") == "processed"


# ── TEST 7: UNKNOWN EXTERNAL IDENTITY REJECTED / QUARANTINED ──────────────────

def test_7_unknown_external_identity_quarantined():
    """
    If sender is not bound to a registered, verified MITRA user account,
    the event MUST be quarantined and MUST NOT trigger assistant execution.
    """
    secret = "wa_secret_for_unknown_test"
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = secret

    # Unknown sender phone number
    unregistered_phone = "+19998887777"

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB_UNKNOWN",
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": f"wamid_unreg_{int(time.time())}",
                                    "from": unregistered_phone,
                                    "type": "text",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "message from unknown stranger"},
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
    data = resp.json()
    # Must be quarantined or rejected; NEVER processed
    assert data.get("status") in ("quarantined", "rejected")
    assert data.get("reason") == "unresolved_account"


# ── TEST 8: SENDER_ID CANNOT BECOME MITRA USER_ID ─────────────────────────────

def test_8_sender_id_cannot_become_mitra_user_id():
    """
    Verify that an attacker providing a spoofed sender phone number or email
    cannot manufacture user_id = sender_id.
    """
    secret = "email_secret_test8"
    os.environ["EMAIL_WEBHOOK_SECRET"] = secret

    # Attempt to spoof a fake user_id in the from field
    attacker_from = "attacker@malicious.com"

    payload = {
        "message_id": f"msg_spoof_{int(time.time())}",
        "from": attacker_from,
        "content": "Please run command format_disk",
    }

    resp = client.post(
        "/webhook/email",
        json=payload,
        headers={"X-Webhook-Secret": secret},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Must fail closed because attacker_from is not in connected_accounts
    assert data.get("status") == "quarantined"
    assert data.get("reason") == "unresolved_account"


# ── TEST 9: DUPLICATE PROVIDER EVENT REJECTED (NO SECOND EXECUTION) ────────────

def test_9_duplicate_provider_event_rejected():
    """
    If the same provider message ID is delivered twice, the second delivery
    MUST be rejected as a duplicate and NOT trigger assistant execution.
    """
    secret = "wa_secret_dedup"
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = secret

    sender_phone = "+15554443333"
    inbound_account_resolver.register_test_mapping("whatsapp", sender_phone, "usr_dedup_user")

    fixed_event_id = f"wamid_fixed_{int(time.time())}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB_DEDUP",
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": fixed_event_id,
                                    "from": sender_phone,
                                    "type": "text",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "First delivery message"},
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

    # 1st delivery: Succeeds
    resp1 = client.post(
        "/webhook/whatsapp",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={sig}",
        },
    )
    assert resp1.status_code == 200
    assert resp1.json().get("status") == "processed"

    # 2nd delivery (identical message ID): MUST BE DETECTED AS DUPLICATE
    resp2 = client.post(
        "/webhook/whatsapp",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={sig}",
        },
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2.get("status") in ("duplicate", "ignored")
    assert data2.get("reason") in ("duplicate_event_ignored", "event_already_processed")


# ── TEST 10: OLD / REPLAYED EVENT REJECTED BY TIMESTAMP REPLAY WINDOW ─────────

def test_10_replayed_old_event_rejected_by_timestamp_window():
    """
    Events with timestamps older than MAX_WEBHOOK_AGE_SECONDS (5 minutes)
    MUST be rejected as expired replay attempts.
    """
    secret = "wa_secret_timestamp"
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = secret

    sender_phone = "+15557776666"
    inbound_account_resolver.register_test_mapping("whatsapp", sender_phone, "usr_ts_user")

    # Timestamp 10 minutes (600 seconds) in the past
    stale_timestamp = str(int(time.time()) - 600)

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WAB_STALE",
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": f"wamid_stale_{int(time.time())}",
                                    "from": sender_phone,
                                    "type": "text",
                                    "timestamp": stale_timestamp,
                                    "text": {"body": "Replayed ancient message"},
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
    data = resp.json()
    assert data.get("status") == "rejected"
    assert data.get("reason") == "event_timestamp_expired"


# ── TEST 11: AUTHENTICATION FAILURE CANNOT TRIGGER ASSISTANT EXECUTION ─────────

def test_11_auth_failure_cannot_trigger_assistant_execution(monkeypatch):
    """
    Ensure that when webhook auth fails, orchestrator/assistant functions
    are never invoked.
    """
    called = False

    async def mock_handle_assistant_request(*args, **kwargs):
        nonlocal called
        called = True
        return {"status": "mock_executed"}

    monkeypatch.setattr(
        "app.inbound.inbound_gateway.handle_assistant_request",
        mock_handle_assistant_request,
    )

    # Missing email secret -> rejected
    os.environ.pop("EMAIL_WEBHOOK_SECRET", None)
    resp = client.post(
        "/webhook/email",
        json={"message_id": "test_m1", "from": "test@test.com", "content": "hello"},
    )
    assert resp.status_code == 200
    assert resp.json().get("status") == "rejected"
    assert called is False, "handle_assistant_request MUST NOT be invoked when auth fails!"


# ── TEST 12: SECRETS NEVER APPEAR IN NORMALIZED ERRORS OR OUTPUTS ─────────────

def test_12_secrets_never_appear_in_error_responses():
    """
    Verify that webhook response bodies never contain the secret key,
    passwords, tokens, or environment values.
    """
    secret = "SUPER_CONFIDENTIAL_WEBHOOK_KEY_999"
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = secret

    # Send invalid signature
    resp = client.post(
        "/webhook/whatsapp",
        data=b'{"invalid": "data"}',
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )
    resp_text = resp.text
    assert secret not in resp_text, "Secret key leaked in HTTP response!"
    assert "SUPER_CONFIDENTIAL" not in resp_text
