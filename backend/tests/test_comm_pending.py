"""
backend/tests/test_comm_pending.py — Phase B.COMM-3 Structured Pending Communication Action Tests

Tests covering:
1. Pending action creation & deterministic hashing
2. Pending action ID uniqueness
3. Confirmation requires authentication (fails closed)
4. User A cannot confirm User B's pending action (cross-user rejection)
5. Expired pending action cannot confirm (ACTION_EXPIRED)
6. Cancelled pending action cannot confirm (ACTION_CANCELLED)
7. Already-confirmed action cannot execute twice (replay protection)
8. Duplicate confirmation does not send duplicate messages
9. Content integrity protected (tamper detection)
10. Recipient integrity protected (tamper detection)
11. Subject integrity protected (tamper detection)
12. Account integrity protected (tamper detection)
13. Channel integrity protected (tamper detection)
14. User ID integrity protected (tamper detection)
15. Idempotency key preserved across lifecycle
16. Provider is NOT called when confirmation fails
17. Provider is called exactly once on valid confirmation
18. Cancel prevents execution
19. No secrets in pending-action responses
20. No secrets in normalized errors
21. Cross-user pending action inspection/cancellation rejected
22. Disconnected account fails safely (ACCOUNT_DISCONNECTED)
23. Existing WHATSAPP_BUSINESS_REQUIRED behavior remains for user WhatsApp
24. Concurrency: Two simultaneous confirmation requests execute provider at most once
25. Direct REST API endpoints (/confirm and /cancel) via TestClient
26. GET pending action endpoint verifies ownership and sanitization
"""
import concurrent.futures
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.models.communication import (
    CommunicationAction,
    CommunicationChannel,
    CommunicationIntent,
    CommunicationResult,
    compute_action_hash,
)
from app.services.communication_service import CommunicationService, communication_service
from app.services.connected_account_service import connected_account_service
from app.services.pending_action_service import (
    _IN_MEMORY_PENDING_ACTIONS,
    PendingActionService,
    pending_action_service,
)


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_b_comm_3_pending_99999")
    monkeypatch.setenv("API_KEY", "test_api_key_mitra_123")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "kX8pZ_5vW1yT3uR0qL7mJ9nF2hD4gA6sB8cE0iK2mO4=")
    _IN_MEMORY_PENDING_ACTIONS.clear()


@pytest.fixture
def auth_headers_user1():
    token = create_access_token({"user_id": "usr_alice_123", "email": "alice@example.com"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2():
    token = create_access_token({"user_id": "usr_bob_456", "email": "bob@example.com"})
    return {"Authorization": f"Bearer {token}"}


# ── 1. Pending Action Creation & Deterministic Hashing ─────────────────────

def test_1_pending_action_creation():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        subject="Hello Bob",
        content="Meeting at 2 PM",
        idempotency_key="idem_test_1",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    assert pending.pending_action_id.startswith("pact_")
    assert pending.user_id == "usr_alice_123"
    assert pending.status == "PENDING"
    assert pending.recipient == "bob@example.com"
    assert pending.subject == "Hello Bob"
    assert pending.content == "Meeting at 2 PM"
    assert pending.idempotency_key == "idem_test_1"
    assert len(pending.action_hash) == 64  # SHA-256


# ── 2. Pending Action ID Uniqueness ────────────────────────────────────────

def test_2_pending_action_id_uniqueness():
    action1 = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Msg 1",
    )
    action2 = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Msg 2",
    )
    p1 = pending_action_service.create_pending_action(action1)
    p2 = pending_action_service.create_pending_action(action2)

    assert p1.pending_action_id != p2.pending_action_id


# ── 3. Confirmation Requires Authentication ────────────────────────────────

def test_3_confirmation_requires_authentication():
    client = TestClient(app)
    # No auth header
    resp = client.post("/api/communication/actions/pact_nonexistent/confirm", json={})
    assert resp.status_code == 401

    # Empty user_id via service
    res = communication_service.confirm_pending_action("pact_123", user_id="")
    assert res.status == "failed"
    assert res.error_code == "AUTH_REQUIRED"


# ── 4. User A Cannot Confirm User B's Pending Action ───────────────────────

def test_4_user_a_cannot_confirm_user_b_action():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Confidential message from Alice",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Bob attempts to confirm Alice's pending action
    res = communication_service.confirm_pending_action(
        pending_action_id=pending.pending_action_id,
        user_id="usr_bob_456",
    )
    assert res.status == "failed"
    assert res.error_code == "ACTION_NOT_FOUND"


# ── 5. Expired Pending Action Cannot Confirm ────────────────────────────────

def test_5_expired_action_cannot_confirm():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Expired message",
    )
    pending = pending_action_service.create_pending_action(action, ttl_seconds=-10)  # expired

    res = communication_service.confirm_pending_action(
        pending_action_id=pending.pending_action_id,
        user_id="usr_alice_123",
    )
    assert res.status == "failed"
    assert res.error_code == "ACTION_EXPIRED"


# ── 6. Cancelled Pending Action Cannot Confirm ─────────────────────────────

def test_6_cancelled_action_cannot_confirm():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Message to be cancelled",
    )
    pending = pending_action_service.create_pending_action(action)

    cancel_res = communication_service.cancel_pending_action(
        pending_action_id=pending.pending_action_id,
        user_id="usr_alice_123",
    )
    assert cancel_res["status"] == "cancelled"

    # Now attempt confirm
    res = communication_service.confirm_pending_action(
        pending_action_id=pending.pending_action_id,
        user_id="usr_alice_123",
    )
    assert res.status == "failed"
    assert res.error_code == "ACTION_CANCELLED"


# ── 7. Already Confirmed Action Cannot Execute Twice ───────────────────────

def test_7_already_confirmed_action_cannot_execute_twice():
    mock_email = MagicMock()
    mock_email.send_message.return_value = {
        "status": "success",
        "provider": "gmail",
        "message_id": "msg_gmail_12345",
        "from": "alice@gmail.com",
    }
    svc = CommunicationService(email_executor=mock_email)

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        action = CommunicationAction(
            intent=CommunicationIntent.SEND_MESSAGE,
            channel=CommunicationChannel.EMAIL,
            user_id="usr_alice_123",
            recipient="bob@example.com",
            content="Single send test",
            idempotency_key="idem_single_send",
        )
        pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

        # First confirmation -> succeeds
        res1 = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res1.status == "sent"

        # Second confirmation -> replay rejected
        res2 = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res2.error_code == "ACTION_ALREADY_EXECUTED" or "already" in str(res2.message).lower()


# ── 8. Duplicate Confirmation Cannot Send Twice ────────────────────────────

def test_8_duplicate_confirmation_cannot_send_twice():
    mock_email = MagicMock()
    mock_email.send_message.return_value = {
        "status": "success",
        "provider": "gmail",
        "message_id": "msg_gmail_duplicate_check",
        "from": "alice@gmail.com",
    }
    svc = CommunicationService(email_executor=mock_email)

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        action = CommunicationAction(
            intent=CommunicationIntent.SEND_MESSAGE,
            channel=CommunicationChannel.EMAIL,
            user_id="usr_alice_123",
            recipient="bob@example.com",
            content="Duplicate check test",
            idempotency_key="idem_duplicate_test",
        )
        pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

        svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")

        # Crucial invariant: provider called EXACTLY once
        assert mock_email.send_message.call_count == 1


# ── 9. Content Integrity Protected ─────────────────────────────────────────

def test_9_content_integrity_protected():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Original content",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Simulate malicious database tampering of content
    pending_action_service._tamper_action_for_testing(
        pending.pending_action_id, {"content": "Tampered malicious content!"}
    )

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res.status == "failed"
        assert res.error_code == "INTEGRITY_CHECK_FAILED"
        assert mock_email.send_message.call_count == 0


# ── 10. Recipient Integrity Protected ──────────────────────────────────────

def test_10_recipient_integrity_protected():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Meeting",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Tamper recipient
    pending_action_service._tamper_action_for_testing(
        pending.pending_action_id, {"recipient": "attacker@example.com"}
    )

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res.status == "failed"
        assert res.error_code == "INTEGRITY_CHECK_FAILED"
        assert mock_email.send_message.call_count == 0


# ── 11. Subject Integrity Protected ────────────────────────────────────────

def test_11_subject_integrity_protected():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        subject="Important meeting",
        content="Meeting",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Tamper subject
    pending_action_service._tamper_action_for_testing(
        pending.pending_action_id, {"subject": "Wire $10,000 immediately"}
    )

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res.status == "failed"
        assert res.error_code == "INTEGRITY_CHECK_FAILED"
        assert mock_email.send_message.call_count == 0


# ── 12. Account Integrity Protected ────────────────────────────────────────

def test_12_account_integrity_protected():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        account_id="alice@gmail.com",
        recipient="bob@example.com",
        content="Meeting",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Tamper account_id
    pending_action_service._tamper_action_for_testing(
        pending.pending_action_id, {"account_id": "ceo@company.com"}
    )

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res.status == "failed"
        assert res.error_code == "INTEGRITY_CHECK_FAILED"
        assert mock_email.send_message.call_count == 0


# ── 13. Channel Integrity Protected ────────────────────────────────────────

def test_13_channel_integrity_protected():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Meeting",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Tamper channel
    pending_action_service._tamper_action_for_testing(
        pending.pending_action_id, {"channel": "WHATSAPP"}
    )

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res.status == "failed"
        assert res.error_code == "INTEGRITY_CHECK_FAILED"
        assert mock_email.send_message.call_count == 0


# ── 14. User ID Integrity Protected ────────────────────────────────────────

def test_14_user_id_integrity_protected():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Meeting",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Tamper user_id
    pending_action_service._tamper_action_for_testing(
        pending.pending_action_id, {"user_id": "usr_eve_789"}
    )

    # Alice queries -> action not found under Alice
    res = communication_service.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
    assert res.status == "failed"
    assert res.error_code == "ACTION_NOT_FOUND"


# ── 15. Idempotency Key Preserved ──────────────────────────────────────────

def test_15_idempotency_key_preserved():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Meeting",
        idempotency_key="idem_custom_key_777",
    )
    # execute_action stages pending action
    res = communication_service.execute_action(action)
    assert res.status == "confirmation_required"
    assert res.idempotency_key == "idem_custom_key_777"
    assert res.pending_action_id is not None

    pending = pending_action_service.get_pending_action(res.pending_action_id, "usr_alice_123")
    assert pending.idempotency_key == "idem_custom_key_777"


# ── 16. Provider Is Not Called When Confirmation Fails ────────────────────

def test_16_provider_is_not_called_when_confirmation_fails():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Fail check",
    )
    pending = pending_action_service.create_pending_action(action, ttl_seconds=-1)  # expired

    res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
    assert res.status == "failed"
    assert mock_email.send_message.call_count == 0


# ── 17. Provider Is Called Exactly Once on Valid Confirmation ──────────────

def test_17_provider_called_exactly_once_on_valid_confirmation():
    mock_email = MagicMock()
    mock_email.send_message.return_value = {
        "status": "success",
        "provider": "gmail",
        "message_id": "gmail_msg_999",
        "from": "alice@gmail.com",
    }
    svc = CommunicationService(email_executor=mock_email)

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        action = CommunicationAction(
            intent=CommunicationIntent.SEND_MESSAGE,
            channel=CommunicationChannel.EMAIL,
            user_id="usr_alice_123",
            recipient="bob@example.com",
            content="Valid confirmation test",
        )
        res_stage = svc.execute_action(action)
        assert res_stage.status == "confirmation_required"
        assert mock_email.send_message.call_count == 0

        res_confirm = svc.confirm_pending_action(res_stage.pending_action_id, user_id="usr_alice_123")
        assert res_confirm.status == "sent"
        assert mock_email.send_message.call_count == 1


# ── 18. Cancel Prevents Execution ──────────────────────────────────────────

def test_18_cancel_prevents_execution():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Do not send",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Cancel
    svc.cancel_pending_action(pending.pending_action_id, user_id="usr_alice_123")

    # Confirm attempt
    res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
    assert res.status == "failed"
    assert res.error_code == "ACTION_CANCELLED"
    assert mock_email.send_message.call_count == 0


# ── 19. No Secrets in Pending Action Response ──────────────────────────────

def test_19_no_secrets_in_pending_action_response():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Check secrets",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")
    doc = pending.to_dict()

    for secret_key in ("password", "access_token", "refresh_token", "auth_token", "secret", "private_key"):
        assert secret_key not in doc


# ── 20. No Secrets in Normalized Errors ────────────────────────────────────

def test_20_no_secrets_in_normalized_errors():
    res = communication_service.confirm_pending_action("pact_nonexistent", user_id="usr_alice_123")
    err_str = str(res.to_dict()).lower()
    for secret_key in ("password", "access_token", "refresh_token", "client_secret"):
        assert secret_key not in err_str


# ── 21. Cross-User Pending Action Inspection/Cancellation Rejected ─────────

def test_21_cross_user_rejection():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Alice action",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Bob attempts to get Alice's pending action
    doc = pending_action_service.get_pending_action(pending.pending_action_id, user_id="usr_bob_456")
    assert doc is None

    # Bob attempts to cancel Alice's pending action
    cancel_res = communication_service.cancel_pending_action(pending.pending_action_id, user_id="usr_bob_456")
    assert cancel_res["status"] == "error"
    assert cancel_res["error_code"] == "ACTION_NOT_FOUND"


# ── 22. Disconnected Account Fails Safely ──────────────────────────────────

def test_22_disconnected_account_fails_safely():
    mock_email = MagicMock()
    svc = CommunicationService(email_executor=mock_email)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="bob@example.com",
        content="Account disconnect test",
    )
    # Staged when alice had a connected account
    pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

    # Account is now disconnected (returns None)
    with patch.object(connected_account_service, "get_user_connection", return_value=None):
        res = svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
        assert res.status == "failed"
        assert res.error_code == "ACCOUNT_DISCONNECTED"
        assert mock_email.send_message.call_count == 0


# ── 23. Existing WHATSAPP_BUSINESS_REQUIRED Remains ────────────────────────

def test_23_existing_whatsapp_business_required_remains():
    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.WHATSAPP,
        user_id="usr_alice_123",
        recipient="+919876543210",
        content="WhatsApp confirmation test",
    )
    pending = pending_action_service.create_pending_action(action)

    res = communication_service.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")
    assert res.status == "failed"
    assert res.error_code == "WHATSAPP_BUSINESS_REQUIRED"


# ── 24. Concurrency: Two Simultaneous Confirmations ─────────────────────────

def test_24_concurrency_simultaneous_confirmations():
    mock_email = MagicMock()
    mock_email.send_message.return_value = {
        "status": "success",
        "provider": "gmail",
        "message_id": "concurrent_gmail_123",
        "from": "alice@gmail.com",
    }
    svc = CommunicationService(email_executor=mock_email)

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@gmail.com"},
    ):
        action = CommunicationAction(
            intent=CommunicationIntent.SEND_MESSAGE,
            channel=CommunicationChannel.EMAIL,
            user_id="usr_alice_123",
            recipient="bob@example.com",
            content="Concurrent test",
            idempotency_key="idem_concurrent_123",
        )
        pending = pending_action_service.create_pending_action(action, sender_account="alice@gmail.com")

        results = []

        def call_confirm():
            return svc.confirm_pending_action(pending.pending_action_id, user_id="usr_alice_123")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(call_confirm)
            f2 = executor.submit(call_confirm)
            results = [f1.result(), f2.result()]

        # Crucial Invariant: Provider MUST be called at most once!
        assert mock_email.send_message.call_count == 1

        statuses = [r.status for r in results]
        error_codes = [r.error_code for r in results if r.error_code]

        # One request succeeded with sent
        assert "sent" in statuses
        # The other request was safely blocked or recognized as already executed/in-progress
        assert any(
            c in ("CONCURRENT_EXECUTION_BLOCKED", "ACTION_ALREADY_EXECUTED")
            for c in error_codes
        ) or statuses.count("sent") == 2


# ── 25. Dedicated REST API Endpoints (/confirm & /cancel) ──────────────────

def test_25_api_endpoints_via_testclient(auth_headers_user1):
    client = TestClient(app)

    with patch.object(
        connected_account_service,
        "get_user_connection",
        return_value={"provider": "gmail", "email": "alice@example.com"},
    ):
        action = CommunicationAction(
            intent=CommunicationIntent.SEND_MESSAGE,
            channel=CommunicationChannel.EMAIL,
            user_id="usr_alice_123",
            recipient="client@example.com",
            content="API test message",
        )
        pending = pending_action_service.create_pending_action(action, sender_account="alice@example.com")

        # Test POST /api/communication/actions/{id}/confirm
        with patch.object(
            communication_service.email_executor,
            "send_message",
            return_value={"status": "success", "provider": "gmail", "message_id": "test_id_1"},
        ):
            resp = client.post(
                f"/api/communication/actions/{pending.pending_action_id}/confirm",
                headers=auth_headers_user1,
                json={},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "sent"
            assert data["pending_action_id"] == pending.pending_action_id

        # Second action to test cancel
        pending2 = pending_action_service.create_pending_action(action, sender_account="alice@example.com")
        resp_cancel = client.post(
            f"/api/communication/actions/{pending2.pending_action_id}/cancel",
            headers=auth_headers_user1,
        )
        assert resp_cancel.status_code == 200
        assert resp_cancel.json()["status"] == "cancelled"


# ── 26. GET Pending Action Endpoint ────────────────────────────────────────

def test_26_get_pending_action_endpoint(auth_headers_user1, auth_headers_user2):
    client = TestClient(app)

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id="usr_alice_123",
        recipient="client@example.com",
        content="Get endpoint test",
    )
    pending = pending_action_service.create_pending_action(action, sender_account="alice@example.com")

    # Alice can inspect her own action
    resp = client.get(
        f"/api/communication/actions/{pending.pending_action_id}",
        headers=auth_headers_user1,
    )
    assert resp.status_code == 200
    assert resp.json()["pending_action_id"] == pending.pending_action_id
    assert resp.json()["recipient"] == "client@example.com"

    # Bob cannot inspect Alice's action (returns 404)
    resp_bob = client.get(
        f"/api/communication/actions/{pending.pending_action_id}",
        headers=auth_headers_user2,
    )
    assert resp_bob.status_code == 404
