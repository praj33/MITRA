"""
backend/tests/test_comm_gmail_full.py — Comprehensive Test Suite for Gmail Full Integration (B.COMM-4B)

Covers all 30 requirements:
 1. Gmail send still works
 2. Gmail read requires gmail.readonly
 3. Gmail search requires gmail.readonly
 4. Gmail draft requires gmail.compose
 5. Existing old-scope account receives reauth-required result
 6. OAuth scope upgrade preserves authenticated user identity
 7. OAuth state is user-bound
 8. OAuth callback cannot upgrade another user's account
 9. Cross-user Gmail read blocked
10. Cross-user Gmail search blocked
11. Cross-user Gmail draft blocked
12. Message normalization
13. Thread retrieval
14. Pagination
15. Query handling
16. Invalid query handling
17. HTML sanitization
18. MIME decoding
19. Attachment metadata
20. Attachment download
21. Oversized attachment rejected
22. Unsafe filename rejected (path traversal protection)
23. CRLF/header injection rejected
24. Draft does not send
25. Send still requires confirmation
26. Gmail provider errors normalized
27. Tokens never appear in API response
28. Tokens never appear in logs/errors
29. Token refresh uses TokenRefreshService
30. Revoked/invalid Google token handled safely
"""
import base64
import json
import os
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
)
from app.services.communication_service import CommunicationService
from app.services.connected_account_service import connected_account_service
from app.services.oauth_transaction_service import oauth_transaction_service
from app.executors.email_executor import EmailExecutor
from app.executors.mime_builder import (
    build_safe_rfc2822_message,
    sanitize_html_content,
    validate_safe_header_value,
)


@pytest.fixture(autouse=True)
def clean_test_environment():
    """Ensure in-memory connected accounts and OAuth transactions are pristine."""
    from app.services.connected_account_service import _IN_MEMORY_CONNECTED_ACCOUNTS
    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS
    _IN_MEMORY_CONNECTED_ACCOUNTS.clear()
    _IN_MEMORY_OAUTH_TRANSACTIONS.clear()
    yield
    _IN_MEMORY_CONNECTED_ACCOUNTS.clear()
    _IN_MEMORY_OAUTH_TRANSACTIONS.clear()


@pytest.fixture
def client():
    return TestClient(app)


def _setup_google_account(
    user_id: str,
    email: str = "alice@example.com",
    scopes: list = None,
    access_token: str = "ya29.test_access_token_123"
):
    if scopes is None:
        scopes = [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/calendar",
        ]
    return connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email=email,
        access_token=access_token,
        refresh_token="test_refresh_token_xyz",
        scopes=scopes,
    )


# ── 1. GMAIL SEND STILL WORKS ──────────────────────────────────────────────

def test_01_gmail_send_still_works():
    """Gmail send executes successfully with B.COMM-3 confirmation and mock Gmail API."""
    user_id = "usr_send_test"
    _setup_google_account(user_id)

    comm_service = CommunicationService()

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id=user_id,
        recipient="bob@example.com",
        subject="Hello Bob",
        content="Testing Gmail Send",
        confirmation_confirmed=True,
    )

    mock_send_res = MagicMock()
    mock_send_res.status_code = 200
    mock_send_res.content = b'{"id":"msg_12345","threadId":"th_12345"}'
    mock_send_res.json.return_value = {"id": "msg_12345", "threadId": "th_12345"}

    with patch("requests.post", return_value=mock_send_res) as mock_post:
        result = comm_service.execute_action(action)
        assert result.status == "sent"
        assert result.delivery_state == "sent"
        assert result.provider_message_id == "msg_12345"
        assert mock_post.called
        assert "users/me/messages/send" in mock_post.call_args[0][0]


# ── 2. GMAIL READ REQUIRES GMAIL.READONLY ──────────────────────────────────

def test_02_gmail_read_requires_gmail_readonly():
    """Attempting to read inbox without gmail.readonly fails closed with GMAIL_REAUTH_REQUIRED."""
    user_id = "usr_read_restricted"
    # Account with send-only
    _setup_google_account(
        user_id,
        scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/gmail.send"]
    )

    comm_service = CommunicationService()
    action = CommunicationAction(
        intent=CommunicationIntent.READ_MESSAGES,
        channel=CommunicationChannel.EMAIL,
        user_id=user_id,
    )

    result = comm_service.execute_action(action)
    assert result.status == "failed"
    assert result.error_code == "GMAIL_REAUTH_REQUIRED"


# ── 3. GMAIL SEARCH REQUIRES GMAIL.READONLY ────────────────────────────────

def test_03_gmail_search_requires_gmail_readonly():
    """Attempting to search messages without gmail.readonly fails closed with GMAIL_REAUTH_REQUIRED."""
    user_id = "usr_search_restricted"
    _setup_google_account(
        user_id,
        scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/gmail.send"]
    )

    comm_service = CommunicationService()
    action = CommunicationAction(
        intent=CommunicationIntent.SEARCH_MESSAGES,
        channel=CommunicationChannel.EMAIL,
        user_id=user_id,
        query="is:unread",
    )

    result = comm_service.execute_action(action)
    assert result.status == "failed"
    assert result.error_code == "GMAIL_REAUTH_REQUIRED"


# ── 4. GMAIL DRAFT REQUIRES GMAIL.COMPOSE ──────────────────────────────────

def test_04_gmail_draft_requires_gmail_compose():
    """Creating a draft without gmail.compose fails closed with GMAIL_REAUTH_REQUIRED."""
    user_id = "usr_draft_restricted"
    _setup_google_account(
        user_id,
        scopes=[
            "openid", "email", "profile",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly"
        ]
    )

    comm_service = CommunicationService()
    action = CommunicationAction(
        intent=CommunicationIntent.DRAFT_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id=user_id,
        recipient="bob@example.com",
        subject="Draft Subject",
        content="Draft content",
    )

    result = comm_service.execute_action(action)
    assert result.status == "failed"
    assert result.error_code == "GMAIL_REAUTH_REQUIRED"


# ── 5. EXISTING OLD-SCOPE ACCOUNT RECEIVES REAUTH-REQUIRED RESULT ──────────

def test_05_existing_old_scope_account_receives_reauth_required_result():
    """Old accounts with only B.COMM-1/2 scopes correctly flag upgrade_required and block read/search/draft."""
    user_id = "usr_old_account"
    _setup_google_account(
        user_id,
        scopes=[
            "openid", "email", "profile",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar"
        ]
    )

    access_state = connected_account_service.get_gmail_access_state(user_id)
    assert access_state["gmail_access_level"] == "send_only"
    assert access_state["gmail_upgrade_required"] is True
    assert access_state["gmail_read_enabled"] is False
    assert access_state["gmail_compose_enabled"] is False

    executor = EmailExecutor()
    res_read = executor.read_inbox_gmail(user_id)
    assert res_read["status"] == "error"
    assert res_read["error_code"] == "GMAIL_REAUTH_REQUIRED"

    res_draft = executor.create_draft_gmail(user_id, "test@example.com", "Sub", "Msg")
    assert res_draft["status"] == "error"
    assert res_draft["error_code"] == "GMAIL_REAUTH_REQUIRED"


# ── 6. OAUTH SCOPE UPGRADE PRESERVES AUTHENTICATED USER IDENTITY ───────────

def test_06_oauth_scope_upgrade_preserves_authenticated_user_identity(client):
    """Initiating 'upgrade_gmail' purpose validates JWT and binds state to authenticated user."""
    user_id = "usr_upgrade_flow"
    jwt_token = create_access_token({"sub": user_id, "user_id": user_id, "email": "user@example.com", "name": "User"})

    res = client.get(
        "/api/oauth/google/start?purpose=upgrade_gmail",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "state" in data
    assert "url" in data
    assert "gmail.readonly" in data["url"]
    assert "gmail.compose" in data["url"]

    # Verify transaction is bound to this user
    tx = oauth_transaction_service.get_transaction(data["state"])
    assert tx is not None
    assert tx["user_id"] == user_id
    assert tx["purpose"] == "upgrade_gmail"


# ── 7. OAUTH STATE IS USER-BOUND ───────────────────────────────────────────

def test_07_oauth_state_is_user_bound(client):
    """Anonymous user cannot initiate upgrade_gmail (requires authentication)."""
    res = client.get("/api/oauth/google/start?purpose=upgrade_gmail")
    assert res.status_code == 401


# ── 8. OAUTH CALLBACK CANNOT UPGRADE ANOTHER USER'S ACCOUNT ────────────────

def test_08_oauth_callback_cannot_upgrade_another_users_account(client):
    """Callback persists connection strictly to the user_id stored in transaction state."""
    user_a = "usr_legit_a"
    tx = oauth_transaction_service.create_transaction(
        provider="google",
        purpose="upgrade_gmail",
        user_id=user_a,
        redirect_uri="http://localhost:8000/api/oauth/google/callback"
    )
    state = tx["state"]

    mock_tokens = {
        "access_token": "ya29.new_upgraded_token",
        "refresh_token": "refresh_new",
        "expires_in": 3600,
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/calendar"
    }
    mock_identity = {
        "provider_subject": "google_sub_123",
        "email": "alice@gmail.com",
        "name": "Alice"
    }

    with patch("app.integrations.oauth.google.GoogleOAuthProvider.exchange_code", return_value=mock_tokens), \
         patch("app.integrations.oauth.google.GoogleOAuthProvider.get_user_identity", return_value=mock_identity):
        res = client.get(f"/api/oauth/google/callback?code=mock_code_xyz&state={state}")
        assert res.status_code in (200, 302)

    # Verify User A has connection, User B has none
    conn_a = connected_account_service.get_user_connection(user_a, "google")
    assert conn_a is not None
    assert "https://www.googleapis.com/auth/gmail.readonly" in conn_a["scopes"]

    conn_b = connected_account_service.get_user_connection("usr_other_b", "google")
    assert conn_b is None


# ── 9. CROSS-USER GMAIL READ BLOCKED ───────────────────────────────────────

def test_09_cross_user_gmail_read_blocked():
    """User A cannot read User B's mailbox."""
    user_a = "usr_alice"
    user_b = "usr_bob"
    _setup_google_account(user_b, email="bob@example.com")

    comm_service = CommunicationService()
    # User A tries to specify User B's account
    action = CommunicationAction(
        intent=CommunicationIntent.READ_MESSAGES,
        channel=CommunicationChannel.EMAIL,
        user_id=user_a,
        account_id="bob@example.com",
    )

    result = comm_service.execute_action(action)
    assert result.status == "failed"
    assert result.error_code in ("ACCOUNT_NOT_AUTHORIZED", "GMAIL_REAUTH_REQUIRED")


# ── 10. CROSS-USER GMAIL SEARCH BLOCKED ────────────────────────────────────

def test_10_cross_user_gmail_search_blocked():
    """User A cannot search User B's mailbox."""
    user_a = "usr_alice_search"
    user_b = "usr_bob_search"
    _setup_google_account(user_b, email="bob@example.com")

    comm_service = CommunicationService()
    action = CommunicationAction(
        intent=CommunicationIntent.SEARCH_MESSAGES,
        channel=CommunicationChannel.EMAIL,
        user_id=user_a,
        account_id="bob@example.com",
        query="invoice",
    )

    result = comm_service.execute_action(action)
    assert result.status == "failed"
    assert result.error_code in ("ACCOUNT_NOT_AUTHORIZED", "GMAIL_REAUTH_REQUIRED")


# ── 11. CROSS-USER GMAIL DRAFT BLOCKED ─────────────────────────────────────

def test_11_cross_user_gmail_draft_blocked():
    """User A cannot create a draft under User B's account."""
    user_a = "usr_alice_draft"
    user_b = "usr_bob_draft"
    _setup_google_account(user_b, email="bob@example.com")

    comm_service = CommunicationService()
    action = CommunicationAction(
        intent=CommunicationIntent.DRAFT_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id=user_a,
        account_id="bob@example.com",
        recipient="client@example.com",
        subject="Contract Draft",
        content="Confidential terms",
    )

    result = comm_service.execute_action(action)
    assert result.status == "failed"
    assert result.error_code in ("ACCOUNT_NOT_AUTHORIZED", "GMAIL_REAUTH_REQUIRED")


# ── 12. MESSAGE NORMALIZATION ──────────────────────────────────────────────

def test_12_message_normalization():
    """Raw Gmail payload is normalized into canonical MITRA message schema."""
    executor = EmailExecutor()
    raw_payload = {
        "id": "18f9a1b2c3d4e5f6",
        "threadId": "th_987654321",
        "snippet": "Hello there, this is a test message...",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "From", "value": "Sender <sender@example.com>"},
                {"name": "To", "value": "Recipient <recipient@example.com>"},
                {"name": "Subject", "value": "Project Update Q4"},
                {"name": "Date", "value": "Thu, 01 Oct 2026 10:00:00 +0000"}
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": base64.urlsafe_b64encode(b"Here is the detailed body text.").decode()
                    }
                }
            ]
        }
    }

    normalized = executor._normalize_gmail_message(raw_payload)
    assert normalized["id"] == "18f9a1b2c3d4e5f6"
    assert normalized["thread_id"] == "th_987654321"
    assert normalized["sender"] == "Sender <sender@example.com>"
    assert normalized["recipient"] == "Recipient <recipient@example.com>"
    assert normalized["subject"] == "Project Update Q4"
    assert normalized["snippet"] == "Hello there, this is a test message..."
    assert normalized["content"] == "Here is the detailed body text."
    assert normalized["timestamp"] == "Thu, 01 Oct 2026 10:00:00 +0000"
    assert normalized["has_attachments"] is False
    assert "INBOX" in normalized["labels"]


# ── 13. THREAD RETRIEVAL ───────────────────────────────────────────────────

def test_13_thread_retrieval():
    """Retrieving a thread returns all messages normalized."""
    user_id = "usr_thread_test"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_thread_data = {
        "id": "th_1001",
        "messages": [
            {
                "id": "msg_001",
                "threadId": "th_1001",
                "snippet": "First in thread",
                "labelIds": ["INBOX"],
                "payload": {
                    "headers": [
                        {"name": "From", "value": "alice@example.com"},
                        {"name": "Subject", "value": "Thread discussion"}
                    ],
                    "body": {"data": base64.urlsafe_b64encode(b"Message 1").decode()}
                }
            },
            {
                "id": "msg_002",
                "threadId": "th_1001",
                "snippet": "Second in thread",
                "labelIds": ["INBOX"],
                "payload": {
                    "headers": [
                        {"name": "From", "value": "bob@example.com"},
                        {"name": "Subject", "value": "Re: Thread discussion"}
                    ],
                    "body": {"data": base64.urlsafe_b64encode(b"Message 2").decode()}
                }
            }
        ]
    }

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = mock_thread_data

    with patch("requests.get", return_value=mock_res):
        res = executor.get_thread_gmail(user_id, "th_1001")
        assert res["status"] == "success"
        assert res["thread_id"] == "th_1001"
        assert len(res["messages"]) == 2
        assert res["messages"][0]["id"] == "msg_001"
        assert res["messages"][1]["id"] == "msg_002"


# ── 14. PAGINATION ─────────────────────────────────────────────────────────

def test_14_pagination():
    """read_inbox_gmail forwards pageToken and returns next_page_token."""
    user_id = "usr_page_test"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_list_res = MagicMock()
    mock_list_res.status_code = 200
    mock_list_res.json.return_value = {
        "messages": [{"id": "m1", "threadId": "t1"}],
        "nextPageToken": "page_token_abc123"
    }

    mock_msg_res = MagicMock()
    mock_msg_res.status_code = 200
    mock_msg_res.json.return_value = {
        "id": "m1",
        "threadId": "t1",
        "snippet": "Snippet 1",
        "payload": {"headers": [{"name": "Subject", "value": "Page test"}]}
    }

    def _mock_get(url, **kwargs):
        if "messages/m1" in url:
            return mock_msg_res
        return mock_list_res

    with patch("requests.get", side_effect=_mock_get) as mock_get:
        res = executor.read_inbox_gmail(user_id, limit=10, page_token="prev_tok")
        assert res["status"] == "success"
        assert res["next_page_token"] == "page_token_abc123"
        assert len(res["messages"]) == 1
        # Verify pageToken was in query params
        first_call_params = mock_get.call_args_list[0][1].get("params", {})
        assert first_call_params.get("pageToken") == "prev_tok"


# ── 15. QUERY HANDLING ─────────────────────────────────────────────────────

def test_15_query_handling():
    """search_messages_gmail correctly submits query expressions."""
    user_id = "usr_q_test"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_list_res = MagicMock()
    mock_list_res.status_code = 200
    mock_list_res.json.return_value = {"messages": []}

    with patch("requests.get", return_value=mock_list_res) as mock_get:
        res = executor.search_messages_gmail(user_id, query="from:boss@example.com is:unread", limit=25)
        assert res["status"] == "success"
        params = mock_get.call_args[1]["params"]
        assert params["q"] == "from:boss@example.com is:unread"
        assert params["maxResults"] == 25


# ── 16. INVALID QUERY HANDLING ─────────────────────────────────────────────

def test_16_invalid_query_handling():
    """Empty query or query containing CRLF is rejected safely."""
    user_id = "usr_invalid_q"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    res_empty = executor.search_messages_gmail(user_id, query="   ")
    assert res_empty["status"] == "error"
    assert res_empty["error_code"] == "GMAIL_INVALID_QUERY"

    res_crlf = executor.search_messages_gmail(user_id, query="is:unread\r\nmalicious:injected")
    assert res_crlf["status"] == "error"
    assert res_crlf["error_code"] == "GMAIL_INVALID_QUERY"


# ── 17. HTML SANITIZATION ──────────────────────────────────────────────────

def test_17_html_sanitization():
    """Dangerous HTML tags, javascript URIs, and event handlers are stripped."""
    dangerous_html = """
    <div>
        <h1>Invoice Ready</h1>
        <script>alert('pwned')</script>
        <iframe src="http://evil.com"></iframe>
        <a href="javascript:stealTokens()" onclick="sendExfil()">Click here</a>
        <img src="https://example.com/logo.png" onload="alert('loaded')">
        <p>Your payment is due.</p>
    </div>
    """
    clean_html = sanitize_html_content(dangerous_html)
    assert "<script" not in clean_html
    assert "alert(" not in clean_html
    assert "<iframe" not in clean_html
    assert "javascript:" not in clean_html
    assert "onclick=" not in clean_html
    assert "onload=" not in clean_html
    assert "<h1>Invoice Ready</h1>" in clean_html
    assert "<p>Your payment is due.</p>" in clean_html


# ── 18. MIME DECODING ──────────────────────────────────────────────────────

def test_18_mime_decoding():
    """MIME builder and decoder handles UTF-8 unicode text and HTML alternatives."""
    raw_bytes = build_safe_rfc2822_message(
        to_email="recipient@example.com",
        subject="Unicode Test — Prüfungsbestätigung 🚀",
        text_body="Plain text with accented characters: é, à, ü, ñ.",
        html_body="<p>HTML body with emoji ✨</p>"
    )
    raw_str = raw_bytes.decode("utf-8", errors="replace")
    assert "Prüfungsbestätigung" in raw_str or "=?utf-8?" in raw_str
    assert "recipient@example.com" in raw_str


# ── 19. ATTACHMENT METADATA ────────────────────────────────────────────────

def test_19_attachment_metadata():
    """Attachments are detected and metadata is exposed without downloading payload."""
    executor = EmailExecutor()
    raw_payload = {
        "id": "msg_with_att",
        "threadId": "th_att",
        "snippet": "Contains PDF invoice",
        "labelIds": ["INBOX"],
        "payload": {
            "headers": [{"name": "Subject", "value": "Invoice #101"}],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": base64.urlsafe_b64encode(b"Please find invoice attached.").decode()}
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "invoice_101.pdf",
                    "body": {
                        "attachmentId": "att_blob_999",
                        "size": 1048576  # 1MB
                    }
                }
            ]
        }
    }
    normalized = executor._normalize_gmail_message(raw_payload)
    assert normalized["has_attachments"] is True
    assert "attachments" in normalized
    assert len(normalized["attachments"]) == 1
    att = normalized["attachments"][0]
    assert att["filename"] == "invoice_101.pdf"
    assert att["mime_type"] == "application/pdf"
    assert att["size"] == 1048576
    assert att["attachment_id"] == "att_blob_999"


# ── 20. ATTACHMENT DOWNLOAD ────────────────────────────────────────────────

def test_20_attachment_download():
    """download_gmail_attachment retrieves attachment payload on demand."""
    user_id = "usr_dl_test"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "size": 512,
        "data": base64.urlsafe_b64encode(b"PDF document data stream").decode()
    }

    with patch("requests.get", return_value=mock_res):
        res = executor.download_gmail_attachment(
            user_id=user_id,
            message_id="msg_123",
            attachment_id="att_blob_999",
            filename="invoice.pdf"
        )
        assert res["status"] == "success"
        assert res["filename"] == "invoice.pdf"
        assert res["size"] == 512
        assert "data_base64" in res


# ── 21. OVERSIZED ATTACHMENT REJECTED ──────────────────────────────────────

def test_21_oversized_attachment_rejected():
    """Attachment downloads larger than 25MB are rejected."""
    user_id = "usr_oversized"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "size": 30 * 1024 * 1024,  # 30MB
        "data": "huge_base64_blob"
    }

    with patch("requests.get", return_value=mock_res):
        res = executor.download_gmail_attachment(
            user_id=user_id,
            message_id="msg_123",
            attachment_id="att_blob_huge",
            filename="huge.zip"
        )
        assert res["status"] == "error"
        assert res["error_code"] == "GMAIL_ATTACHMENT_TOO_LARGE"


# ── 22. UNSAFE FILENAME REJECTED (PATH TRAVERSAL PROTECTION) ───────────────

def test_22_unsafe_filename_rejected():
    """Path traversal sequences in filenames are safely stripped or rejected."""
    user_id = "usr_traversal"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"size": 100, "data": "dummy"}

    with patch("requests.get", return_value=mock_res):
        res = executor.download_gmail_attachment(
            user_id=user_id,
            message_id="msg_123",
            attachment_id="att_blob_1",
            filename="../../etc/shadow"
        )
        # os.path.basename extracts 'shadow' (no directory traversal)
        assert res["status"] == "success"
        assert res["filename"] == "shadow"
        assert "/" not in res["filename"]
        assert "\\" not in res["filename"]


# ── 23. CRLF/HEADER INJECTION REJECTED ─────────────────────────────────────

def test_23_crlf_header_injection_rejected():
    """CRLF sequences in Subject or email headers are rejected by MIME builder."""
    with pytest.raises(ValueError, match="Header injection detected"):
        build_safe_rfc2822_message(
            to_email="recipient@example.com",
            subject="Harmless subject\r\nBcc: spy@attacker.com",
            text_body="Message content"
        )

    with pytest.raises(ValueError, match="Header injection detected"):
        build_safe_rfc2822_message(
            to_email="recipient@example.com\r\nCc: victim@example.com",
            subject="Harmless subject",
            text_body="Message content"
        )


# ── 24. DRAFT DOES NOT SEND ────────────────────────────────────────────────

def test_24_draft_does_not_send():
    """Creating a draft invokes users/me/drafts and never invokes users/me/messages/send."""
    user_id = "usr_draft_nosend"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_draft_res = MagicMock()
    mock_draft_res.status_code = 200
    mock_draft_res.json.return_value = {
        "id": "draft_777",
        "message": {"id": "msg_777", "threadId": "th_777"}
    }

    with patch("requests.post", return_value=mock_draft_res) as mock_post:
        res = executor.create_draft_gmail(
            user_id=user_id,
            to_email="recipient@example.com",
            subject="Draft only",
            message="Content to be sent later"
        )
        assert res["status"] == "success"
        assert res["draft_id"] == "draft_777"
        called_url = mock_post.call_args[0][0]
        assert "users/me/drafts" in called_url
        assert "users/me/messages/send" not in called_url


# ── 25. SEND STILL REQUIRES CONFIRMATION ───────────────────────────────────

def test_25_send_still_requires_confirmation():
    """SEND_MESSAGE without confirmation_confirmed=True is staged as confirmation_required."""
    user_id = "usr_unconfirmed_send"
    _setup_google_account(user_id)
    comm_service = CommunicationService()

    action = CommunicationAction(
        intent=CommunicationIntent.SEND_MESSAGE,
        channel=CommunicationChannel.EMAIL,
        user_id=user_id,
        recipient="bob@example.com",
        subject="Important",
        content="Sensitive text",
        confirmation_confirmed=False,
    )

    with patch("requests.post") as mock_post:
        result = comm_service.execute_action(action)
        assert result.status == "confirmation_required"
        assert result.delivery_state == "pending"
        assert result.pending_action_id is not None
        # Provider MUST NOT be reached
        assert not mock_post.called


# ── 26. GMAIL PROVIDER ERRORS NORMALIZED ───────────────────────────────────

def test_26_gmail_provider_errors_normalized():
    """Gmail API 404, 429, 401/403 are mapped to canonical error codes."""
    executor = EmailExecutor()

    # 404 Not Found
    res_404 = MagicMock()
    res_404.status_code = 404
    res_404.json.return_value = {"error": {"message": "Message not found"}}
    mapped_404 = executor._map_gmail_error(res_404)
    assert mapped_404["error_code"] == "GMAIL_NOT_FOUND"

    # 429 Rate Limited
    res_429 = MagicMock()
    res_429.status_code = 429
    res_429.json.return_value = {"error": {"message": "Rate limit exceeded"}}
    mapped_429 = executor._map_gmail_error(res_429)
    assert mapped_429["error_code"] == "GMAIL_RATE_LIMITED"

    # 403 Insufficient Scope
    res_403 = MagicMock()
    res_403.status_code = 403
    res_403.json.return_value = {"error": {"message": "Request had insufficient authentication scopes."}}
    mapped_403 = executor._map_gmail_error(res_403)
    assert mapped_403["error_code"] == "GMAIL_REAUTH_REQUIRED"


# ── 27. TOKENS NEVER APPEAR IN API RESPONSE ────────────────────────────────

def test_27_tokens_never_appear_in_api_response(client):
    """GET /api/connections returns sanitized records without OAuth tokens."""
    user_id = "usr_sanitized_meta"
    _setup_google_account(user_id)
    jwt_token = create_access_token({"sub": user_id, "user_id": user_id, "email": "user@example.com", "name": "User"})

    res = client.get("/api/connections", headers={"Authorization": f"Bearer {jwt_token}"})
    assert res.status_code == 200
    data = res.json()
    raw_str = json.dumps(data)

    assert "ya29.test_access_token_123" not in raw_str
    assert "test_refresh_token_xyz" not in raw_str
    assert "encrypted_access_token" not in raw_str
    assert "encrypted_refresh_token" not in raw_str
    assert "access_token" not in raw_str


# ── 28. TOKENS NEVER APPEAR IN LOGS/ERRORS ─────────────────────────────────

def test_28_tokens_never_appear_in_logs_or_errors():
    """Executor error responses do not leak access tokens or credentials."""
    user_id = "usr_leak_check"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_err_res = MagicMock()
    mock_err_res.status_code = 500
    mock_err_res.json.return_value = {"error": {"message": "Backend crash"}}

    with patch("requests.get", return_value=mock_err_res):
        res = executor.read_inbox_gmail(user_id)
        err_str = json.dumps(res)
        assert "ya29.test_access_token_123" not in err_str
        assert "refresh_token" not in err_str


# ── 29. TOKEN REFRESH USES TOKENREFRESHSERVICE ─────────────────────────────

def test_29_token_refresh_uses_token_refresh_service():
    """Gmail operations fetch valid token through TokenRefreshService."""
    user_id = "usr_refresh_mock"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    mock_list_res = MagicMock()
    mock_list_res.status_code = 200
    mock_list_res.json.return_value = {"messages": []}

    with patch("app.services.token_refresh_service.token_refresh_service.get_valid_access_token", return_value="fresh_token_888") as mock_get_token, \
         patch("requests.get", return_value=mock_list_res) as mock_get:
        executor.read_inbox_gmail(user_id)
        assert mock_get_token.called
        headers = mock_get.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer fresh_token_888"


# ── 30. REVOKED/INVALID GOOGLE TOKEN HANDLED SAFELY ────────────────────────

def test_30_revoked_or_invalid_google_token_handled_safely():
    """When token cannot be refreshed or was revoked, returns GMAIL_REAUTH_REQUIRED safely."""
    user_id = "usr_revoked"
    _setup_google_account(user_id)
    executor = EmailExecutor()

    with patch("app.services.token_refresh_service.token_refresh_service.get_valid_access_token", return_value=None):
        res = executor.read_inbox_gmail(user_id)
        assert res["status"] == "error"
        assert res["error_code"] == "GMAIL_REAUTH_REQUIRED"
