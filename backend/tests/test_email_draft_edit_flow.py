"""
backend/tests/test_email_draft_edit_flow.py
Tests for the structured Email Draft Edit architecture and prepare-send workflow:
- Structured draft state is preserved without LLM or synthetic natural-language commands
- Server-side draft retrieval, ownership validation, and recipient binding
- Edited body becomes CommunicationAction.content without command text contamination
- Approval policy enforcement: status="confirmation_required", requires explicit confirm
- Direct REST confirmation executes Gmail sending with exact canonical content
- Cross-user isolation and unauthenticated access rejection
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.communication_service import communication_service
from app.executors.email_executor import EmailExecutor
from app.models.communication import (
    CommunicationAction,
    CommunicationChannel,
    CommunicationIntent,
)
from app.core.auth_dependencies import get_current_user


def test_prepare_send_draft_unauthenticated_rejected():
    """Unauthenticated or anonymous user is rejected with AUTH_REQUIRED."""
    res = communication_service.prepare_send_draft(
        draft_id="draft_123",
        user_id="",
        body="Hello Raj",
    )
    assert res.get("status") == "error"
    assert res.get("error_code") == "AUTH_REQUIRED"

    res_default = communication_service.prepare_send_draft(
        draft_id="draft_123",
        user_id="user_default",
        body="Hello Raj",
    )
    assert res_default.get("status") == "error"
    assert res_default.get("error_code") == "AUTH_REQUIRED"


def test_prepare_send_draft_missing_draft_id_rejected():
    """Missing draft_id is rejected."""
    res = communication_service.prepare_send_draft(
        draft_id="",
        user_id="usr_valid_123",
        body="Hello Raj",
    )
    assert res.get("status") == "error"
    assert res.get("error_code") == "DRAFT_NOT_FOUND"


def test_prepare_send_draft_nonexistent_draft_rejected():
    """If Gmail API reports draft not found, error is propagated."""
    user_id = "usr_valid_456"
    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get:
        mock_get.return_value = {
            "status": "error",
            "error_code": "GMAIL_NOT_FOUND",
            "error": "Draft not found in Gmail.",
        }
        res = communication_service.prepare_send_draft(
            draft_id="nonexistent_draft_999",
            user_id=user_id,
            body="Hello Raj, edited",
        )
        assert res.get("status") == "error"
        assert res.get("error_code") == "GMAIL_NOT_FOUND"


def test_prepare_send_draft_preserves_canonical_recipient_and_edited_fields():
    """
    Core Architectural Guarantee:
    - Canonical draft provides recipient: rajprajapati1729@gmail.com
    - User edits body to 'Hello Raj, this is the edited message.'
    - prepare_send_draft stages CommunicationAction with content strictly equal to edited body
    - Result requires confirmation and contains structured confirmation payload
    """
    user_id = "usr_valid_789"
    draft_id = "r_draft_xyz"

    canonical_draft = {
        "id": draft_id,
        "recipient": "rajprajapati1729@gmail.com",
        "subject": "MITRA Test",
        "content": "Hello Raj",
    }

    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft, \
         patch("app.services.connected_account_service.connected_account_service.get_user_connection") as mock_conn:

        mock_get_draft.return_value = {
            "status": "success",
            "draft_id": draft_id,
            "draft": canonical_draft,
        }
        mock_conn.return_value = {
            "email": "assistant_sender@example.com",
            "account_id": "acc_google_123",
            "provider": "google",
        }

        res = communication_service.prepare_send_draft(
            draft_id=draft_id,
            user_id=user_id,
            subject="MITRA Test",
            body="Hello Raj, this is the edited message.",
            recipient="rajprajapati1729@gmail.com",
        )

        assert res.get("status") == "confirmation_required", f"Expected confirmation_required, got {res}"
        assert res.get("pending_action_id") is not None
        assert "pact_" in res["pending_action_id"]

        confirmation = res.get("confirmation", {})
        assert confirmation.get("recipient") == "rajprajapati1729@gmail.com"
        assert confirmation.get("subject") == "MITRA Test"
        assert confirmation.get("content") == "Hello Raj, this is the edited message."

        # Verify NO natural language or command text in content
        assert "Send an email to" not in confirmation.get("content")
        assert "with subject" not in confirmation.get("content")
        assert "and message" not in confirmation.get("content")


def test_prepare_send_draft_binds_recipient_to_canonical_draft():
    """Recipient remains bound to the canonical server-side draft and cannot be hijacked by client."""
    user_id = "usr_valid_bind"
    draft_id = "r_draft_bind_123"

    canonical_draft = {
        "id": draft_id,
        "recipient": "legitimate_recipient@gmail.com",
        "subject": "Confidential Report",
        "content": "Original Content",
    }

    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft, \
         patch("app.services.connected_account_service.connected_account_service.get_user_connection") as mock_conn:

        mock_get_draft.return_value = {
            "status": "success",
            "draft_id": draft_id,
            "draft": canonical_draft,
        }
        mock_conn.return_value = {"email": "sender@example.com", "provider": "google"}

        # Attempt to tamper with recipient in request
        res = communication_service.prepare_send_draft(
            draft_id=draft_id,
            user_id=user_id,
            subject="Updated Report",
            body="Edited body content",
            recipient="malicious_hijacker@attacker.com",
        )

        assert res.get("status") == "confirmation_required"
        # Server must enforce legitimate recipient from canonical draft
        confirmation = res.get("confirmation", {})
        assert confirmation.get("recipient") == "legitimate_recipient@gmail.com"


def test_edited_draft_confirmation_and_final_gmail_executor_content():
    """
    Full End-to-End Execution Sequence:
    1. prepare_send_draft stages action with edited body
    2. confirm_pending_action confirms it
    3. EmailExecutor.send_message receives strictly the canonical edited content
    """
    user_id = "usr_e2e_tester"
    draft_id = "r_draft_e2e"

    canonical_draft = {
        "id": draft_id,
        "recipient": "rajprajapati1729@gmail.com",
        "subject": "MITRA Test",
        "content": "Hello Raj",
    }

    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft, \
         patch("app.services.connected_account_service.connected_account_service.get_user_connection") as mock_conn, \
         patch.object(EmailExecutor, "send_message") as mock_send:

        mock_get_draft.return_value = {
            "status": "success",
            "draft_id": draft_id,
            "draft": canonical_draft,
        }
        mock_conn.return_value = {"email": "sender@gmail.com", "provider": "google"}
        mock_send.return_value = {
            "status": "success",
            "message": "Email sent successfully.",
            "message_id": "msg_gmail_789",
        }

        # Step 1: Prepare send
        prep_res = communication_service.prepare_send_draft(
            draft_id=draft_id,
            user_id=user_id,
            subject="MITRA Test",
            body="Hello Raj, this is the edited message.",
        )
        assert prep_res.get("status") == "confirmation_required"
        pending_id = prep_res.get("pending_action_id")

        # Step 2: Confirm pending action
        confirm_res = communication_service.confirm_pending_action(
            pending_action_id=pending_id,
            user_id=user_id,
        )

        assert confirm_res.status == "sent"

        # Step 3: Verify exact parameters delivered to EmailExecutor
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["to_email"] == "rajprajapati1729@gmail.com"
        assert call_kwargs["subject"] == "MITRA Test"
        assert call_kwargs["message"] == "Hello Raj, this is the edited message."

        # Invariant checks: zero command leakage
        delivered_body = call_kwargs["message"]
        assert "Send an email to" not in delivered_body
        assert "with subject" not in delivered_body
        assert "and message" not in delivered_body
        assert "Edit before sending" not in delivered_body


def test_prepare_send_draft_rest_endpoint(monkeypatch):
    """FastAPI endpoint POST /api/communication/drafts/{draft_id}/prepare-send operates cleanly."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_b_comm_3_pending_99999")
    from app.core.security import create_access_token

    client = TestClient(app)
    user_id = "usr_rest_client"
    token = create_access_token({"user_id": user_id, "email": "user@example.com"})
    headers = {"Authorization": f"Bearer {token}"}

    draft_id = "r_draft_rest_456"
    canonical_draft = {
        "id": draft_id,
        "recipient": "rajprajapati1729@gmail.com",
        "subject": "MITRA Test",
        "content": "Hello Raj",
    }

    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft, \
         patch("app.services.connected_account_service.connected_account_service.get_user_connection") as mock_conn:

        mock_get_draft.return_value = {
            "status": "success",
            "draft_id": draft_id,
            "draft": canonical_draft,
        }
        mock_conn.return_value = {"email": "sender@gmail.com", "provider": "google"}

        response = client.post(
            f"/api/communication/drafts/{draft_id}/prepare-send",
            headers=headers,
            json={
                "recipient": "rajprajapati1729@gmail.com",
                "subject": "MITRA Test",
                "body": "Hello Raj, this is the edited message.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "confirmation_required"
        assert data.get("confirmation", {}).get("content") == "Hello Raj, this is the edited message."
        assert data.get("confirmation", {}).get("recipient") == "rajprajapati1729@gmail.com"


def test_google_provider_connection_resolves_and_authorizes_edited_draft():
    """
    Production regression test:
    Google OAuth stores connection with provider='google'.
    resolve_sender_account and prepare_send_draft must resolve provider='google',
    bind account_id without authorization error, stage confirmation_required,
    and allow subsequent confirmation to send with exact edited body.
    """
    user_id = "usr_prod_verified"
    draft_id = "r_draft_prod_999"
    sender_email = "blackholeinfiverse20@gmail.com"

    canonical_draft = {
        "id": draft_id,
        "recipient": "rajprajapati1729@gmail.com",
        "subject": "Edit Test",
        "content": "Hello Raj.",
    }

    def mock_get_conn(user_id=None, provider=None, *args, **kwargs):
        # Strictly return connection ONLY for provider='google', not 'gmail'
        uid = user_id or kwargs.get("user_id")
        prov = provider or kwargs.get("provider")
        if uid == "usr_prod_verified" and prov == "google":
            return {
                "user_id": "usr_prod_verified",
                "provider": "google",
                "email": sender_email,
                "provider_account_id": "google_sub_108392",
                "status": "connected",
            }
        return None

    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft, \
         patch("app.services.connected_account_service.connected_account_service.get_user_connection", side_effect=mock_get_conn), \
         patch.object(EmailExecutor, "send_message") as mock_send:

        mock_get_draft.return_value = {
            "status": "success",
            "draft_id": draft_id,
            "draft": canonical_draft,
        }
        mock_send.return_value = {
            "status": "success",
            "message": "Email sent successfully.",
            "message_id": "msg_gmail_prod_1",
        }

        # Step 1: User edits body in structured editor and submits prepare-send
        prep_res = communication_service.prepare_send_draft(
            draft_id=draft_id,
            user_id=user_id,
            subject="Edit Test",
            body="Hello Raj, this message was edited in MITRA.",
        )

        assert prep_res.get("status") == "confirmation_required", f"Unexpected prep_res: {prep_res}"
        assert prep_res.get("error_code") != "ACCOUNT_NOT_AUTHORIZED"
        pending_id = prep_res.get("pending_action_id")
        assert pending_id is not None

        confirmation = prep_res.get("confirmation", {})
        assert confirmation.get("recipient") == "rajprajapati1729@gmail.com"
        assert confirmation.get("subject") == "Edit Test"
        assert confirmation.get("content") == "Hello Raj, this message was edited in MITRA."
        assert confirmation.get("sender_account") == sender_email

        # Step 2: User clicks "Send Now" on confirmation card
        confirm_res = communication_service.confirm_pending_action(
            pending_action_id=pending_id,
            user_id=user_id,
        )

        assert confirm_res.status == "sent", f"Unexpected confirm_res: {confirm_res.to_dict()}"
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["to_email"] == "rajprajapati1729@gmail.com"
        assert call_kwargs["subject"] == "Edit Test"
        assert call_kwargs["message"] == "Hello Raj, this message was edited in MITRA."


def test_resolve_sender_account_ownership_validation():
    """
    Ownership and security checks in resolve_sender_account:
    - User's owned email -> Authorized
    - User's provider_account_id -> Authorized
    - None (default) -> Authorized with matched email
    - Arbitrary/unowned account_id -> Rejected with ACCOUNT_NOT_AUTHORIZED
    """
    user_id = "usr_security_owner"

    def mock_get_conn(user_id=None, provider=None, *args, **kwargs):
        uid = user_id or kwargs.get("user_id")
        prov = provider or kwargs.get("provider")
        if uid == "usr_security_owner" and prov == "google":
            return {
                "user_id": "usr_security_owner",
                "provider": "google",
                "email": "blackholeinfiverse20@gmail.com",
                "provider_account_id": "google_sub_108392",
                "status": "connected",
            }
        return None

    with patch("app.services.connected_account_service.connected_account_service.get_user_connection", side_effect=mock_get_conn):
        # 1. Matching by email address
        acct, err = communication_service.resolve_sender_account(
            user_id, CommunicationChannel.EMAIL, account_id="blackholeinfiverse20@gmail.com"
        )
        assert err is None
        assert acct == "blackholeinfiverse20@gmail.com"

        # 2. Matching by provider_account_id
        acct, err = communication_service.resolve_sender_account(
            user_id, CommunicationChannel.EMAIL, account_id="google_sub_108392"
        )
        assert err is None
        assert acct in ("blackholeinfiverse20@gmail.com", "google_sub_108392")

        # 3. Default (no account_id specified)
        acct, err = communication_service.resolve_sender_account(
            user_id, CommunicationChannel.EMAIL, account_id=None
        )
        assert err is None
        assert acct == "blackholeinfiverse20@gmail.com"

        # 4. Arbitrary unauthorized account_id is strictly rejected
        acct, err = communication_service.resolve_sender_account(
            user_id, CommunicationChannel.EMAIL, account_id="attacker@evil.com"
        )
        assert err == "ACCOUNT_NOT_AUTHORIZED"
        assert acct is None

        # 5. Cross-user lookup is strictly rejected
        acct, err = communication_service.resolve_sender_account(
            "usr_other_unauthorized", CommunicationChannel.EMAIL, account_id="blackholeinfiverse20@gmail.com"
        )
        assert err == "ACCOUNT_NOT_AUTHORIZED"
        assert acct is None


def test_prepare_send_draft_ignores_arbitrary_client_account_id(monkeypatch):
    """
    Client-supplied account_id in prepare-send request payload cannot hijack
    or switch the server-side derived connected account.
    """
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_b_comm_3_pending_99999")
    from app.core.security import create_access_token

    client = TestClient(app)
    user_id = "usr_client_safe"
    token = create_access_token({"user_id": user_id, "email": "user@example.com"})
    headers = {"Authorization": f"Bearer {token}"}

    draft_id = "r_draft_safe_101"
    canonical_draft = {
        "id": draft_id,
        "recipient": "rajprajapati1729@gmail.com",
        "subject": "Original Subject",
        "content": "Original Body",
    }

    def mock_get_conn(user_id=None, provider=None, *args, **kwargs):
        uid = user_id or kwargs.get("user_id")
        prov = provider or kwargs.get("provider")
        if uid == "usr_client_safe" and prov == "google":
            return {
                "user_id": "usr_client_safe",
                "provider": "google",
                "email": "blackholeinfiverse20@gmail.com",
                "provider_account_id": "google_sub_108392",
                "status": "connected",
            }
        return None

    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft, \
         patch("app.services.connected_account_service.connected_account_service.get_user_connection", side_effect=mock_get_conn):

        mock_get_draft.return_value = {
            "status": "success",
            "draft_id": draft_id,
            "draft": canonical_draft,
        }

        # Attempt to pass an arbitrary account_id in the JSON request
        res = client.post(
            f"/api/communication/drafts/{draft_id}/prepare-send",
            headers=headers,
            json={
                "recipient": "rajprajapati1729@gmail.com",
                "subject": "Edit Test",
                "body": "Hello Raj, this message was edited in MITRA.",
                "account_id": "attacker@evil.com",
            },
        )

        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "confirmation_required"
        # The staged action MUST bind the authenticated user's own sender account, NOT attacker's
        confirmation = data.get("confirmation", {})
        assert confirmation.get("sender_account") == "blackholeinfiverse20@gmail.com"
        assert confirmation.get("sender_account") != "attacker@evil.com"


def test_cross_user_draft_access_rejected_at_prepare_send():
    """
    User A cannot prepare-send a draft belonging to User B.
    When Gmail API returns GMAIL_NOT_FOUND (since users/me/drafts/{id} does not exist for User A),
    the endpoint immediately returns 404 / GMAIL_NOT_FOUND without staging any pending action.
    """
    user_a = "usr_attacker_alice"
    draft_b_id = "r_draft_owned_by_bob"

    with patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft:
        mock_get_draft.return_value = {
            "status": "error",
            "error_code": "GMAIL_NOT_FOUND",
            "error": "Requested Gmail resource not found: draft does not exist in user mailbox.",
        }

        res = communication_service.prepare_send_draft(
            draft_id=draft_b_id,
            user_id=user_a,
            body="Unauthorized edit attempt",
        )

        assert res.get("status") == "error"
        assert res.get("error_code") == "GMAIL_NOT_FOUND"
        assert "pending_action_id" not in res
