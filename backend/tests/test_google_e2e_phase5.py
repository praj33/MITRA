import os
import pytest
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.gateway_auth import GatewayAuth
from app.services.oauth_transaction_service import oauth_transaction_service
from app.services.connected_account_service import connected_account_service
from app.services.token_refresh_service import token_refresh_service
from app.integrations.oauth.google import GoogleOAuthProvider
from app.executors.email_executor import EmailExecutor
from app.executors.calendar_executor import CalendarExecutor

client = TestClient(app)

TEST_JWT_SECRET = "test_phase5_e2e_jwt_secret_key_mitra_999"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "test_phase5_encryption_key_32bytes_len=")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_google_client_secret_xyz")

def get_auth_header(user_id: str, email: str = "user@example.com") -> dict:
    token = create_access_token({"sub": user_id, "user_id": user_id, "email": email})
    return {"Authorization": f"Bearer {token}"}

# 1. Authenticated User Starts Google Connection
def test_authenticated_user_starts_google_connection():
    headers = get_auth_header("user_e2e_01")
    response = client.get("/api/oauth/google/start?purpose=connect", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "state" in data
    assert data["provider"] == "google"

# 2 & 3. State Stored & PKCE Challenge Generated
def test_state_stored_and_pkce_challenge_generated():
    headers = get_auth_header("user_e2e_02")
    response = client.get("/api/oauth/google/start?purpose=connect", headers=headers)
    data = response.json()
    state = data["state"]

    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS
    record = _IN_MEMORY_OAUTH_TRANSACTIONS.get(state)
    assert record is not None
    assert record["code_challenge"] is not None
    assert record["code_challenge_method"] == "S256"
    assert record["user_id"] == "user_e2e_02"

# 4, 5, 6, 7, 8. Callback Validates State, Code Exchanged, Identity Retrieved, Connected Account Created & Tokens Encrypted
@patch.object(GoogleOAuthProvider, "exchange_code")
@patch.object(GoogleOAuthProvider, "get_user_identity")
def test_full_google_oauth_callback_flow(mock_identity, mock_exchange):
    mock_exchange.return_value = {
        "access_token": "ya29.e2e_google_access_token_val",
        "refresh_token": "1//e2e_google_refresh_token_val",
        "expires_in": 3600
    }
    mock_identity.return_value = {
        "provider_subject": "google_sub_e2e_777",
        "email": "alice.google@example.com",
        "name": "Alice Google"
    }

    headers = get_auth_header("user_alice_e2e")
    start_res = client.get("/api/oauth/google/start?purpose=connect", headers=headers)
    state = start_res.json()["state"]

    callback_res = client.get(f"/api/oauth/google/callback?code=valid_e2e_code&state={state}")
    assert callback_res.status_code == 200
    assert callback_res.json()["status"] == "success"

    conn_raw = connected_account_service.get_user_connection("user_alice_e2e", "google", include_decrypted_tokens=False)
    assert "access_token" not in conn_raw
    assert "refresh_token" not in conn_raw

    conn_dec = connected_account_service.get_user_connection("user_alice_e2e", "google", include_decrypted_tokens=True)
    assert conn_dec["access_token"] == "ya29.e2e_google_access_token_val"
    assert conn_dec["refresh_token"] == "1//e2e_google_refresh_token_val"

# 9 & 16. Connection Metadata Returned & Tokens Never Reach API Response
def test_connections_api_returns_safe_metadata():
    user_id = "user_safe_metadata_01"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="safe_metadata@example.com",
        access_token="ya29.top_secret_at",
        refresh_token="1//top_secret_rt"
    )

    headers = get_auth_header(user_id)
    response = client.get("/api/connections", headers=headers)
    assert response.status_code == 200
    data = response.json()

    conn_list = data.get("connections", [])
    assert len(conn_list) == 1
    conn = conn_list[0]

    assert conn["provider"] == "google"
    assert conn["email"] == "safe_metadata@example.com"
    assert conn["status"] in ["connected", "active"]
    assert "access_token" not in conn
    assert "refresh_token" not in conn
    assert "ya29.top_secret_at" not in str(data)
    assert "1//top_secret_rt" not in str(data)

# 10. Token Refresh Works
@patch.object(GoogleOAuthProvider, "refresh_access_token")
def test_token_refresh_works(mock_refresh):
    user_id = "user_tr_works_01"
    expired_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="tr@example.com",
        access_token="old_expired_at",
        refresh_token="rt_valid_123",
        expires_at=expired_time
    )

    mock_refresh.return_value = {
        "access_token": "fresh_new_access_token_999",
        "expires_in": 3600
    }

    fresh = token_refresh_service.get_valid_access_token(user_id, "google")
    assert fresh == "fresh_new_access_token_999"

# 11. Refresh Failure Causes needs_reauthorization
@patch.object(GoogleOAuthProvider, "refresh_access_token")
def test_refresh_failure_causes_needs_reauthorization(mock_refresh):
    user_id = "user_rf_fails_01"
    expired_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="rf@example.com",
        access_token="old_expired_at",
        refresh_token="rt_revoked_456",
        expires_at=expired_time
    )

    mock_refresh.side_effect = ValueError("invalid_grant")

    with pytest.raises(Exception):
        token_refresh_service.get_valid_access_token(user_id, "google")

    conn = connected_account_service.get_user_connection(user_id, "google")
    assert conn["status"] == "needs_reauthorization"

# 12. Gmail Uses Connected Account
@patch.object(EmailExecutor, "send_email_gmail_api")
def test_gmail_uses_connected_account(mock_gmail_send):
    user_id = "user_gmail_exec_01"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="gmail_user@example.com",
        access_token="ya29.gmail_token_abc"
    )

    mock_gmail_send.return_value = {
        "status": "success",
        "to": "recipient@example.com",
        "subject": "Test Subject",
        "message": "Test Body",
        "method": "gmail_oauth_api"
    }

    executor = EmailExecutor()
    res = executor.send_message(
        to_email="recipient@example.com",
        subject="Test Subject",
        message="Test Body",
        trace_id="tr_gmail_01",
        user_id=user_id
    )

    assert res["status"] == "success"
    assert res["user_connected_account"] is True
    mock_gmail_send.assert_called_once()

# 13. Calendar Uses Connected Account (Create, List, Update, Delete)
@patch("requests.post")
@patch("requests.get")
@patch("requests.patch")
@patch("requests.delete")
def test_calendar_uses_connected_account(mock_del, mock_patch, mock_get, mock_post):
    user_id = "user_cal_exec_01"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="cal_user@example.com",
        access_token="ya29.calendar_token_xyz"
    )

    # Mock HTTP responses
    res_post = MagicMock(status_code=201)
    res_post.json.return_value = {"id": "evt_1001", "htmlLink": "http://calendar.google.com/evt_1001"}
    mock_post.return_value = res_post

    res_get = MagicMock(status_code=200)
    res_get.json.return_value = {"items": [{"id": "evt_1001", "summary": "Meeting"}]}
    mock_get.return_value = res_get

    res_patch = MagicMock(status_code=200)
    mock_patch.return_value = res_patch

    res_del = MagicMock(status_code=204)
    mock_del.return_value = res_del

    executor = CalendarExecutor()

    # Issue gateway invocation tokens for calendar operations
    gw_create = GatewayAuth.issue(trace_id="tr_c1", platform="calendar", action="create_event", decision="allow")
    gw_list = GatewayAuth.issue(trace_id="tr_l1", platform="calendar", action="list_events", decision="allow")
    gw_update = GatewayAuth.issue(trace_id="tr_u1", platform="calendar", action="update_event", decision="allow")
    gw_delete = GatewayAuth.issue(trace_id="tr_d1", platform="calendar", action="delete_event", decision="allow")

    # Create Event
    c_res = executor.create_event(
        title="Meeting", start_time="2026-09-04T10:00:00Z", trace_id="tr_c1",
        gateway_auth=gw_create, user_id=user_id
    )
    assert c_res["status"] == "success"
    assert c_res["event_id"] == "evt_1001"

    # List Events
    l_res = executor.list_events(
        max_results=5, trace_id="tr_l1",
        gateway_auth=gw_list, user_id=user_id
    )
    assert l_res["status"] == "success"
    assert len(l_res["events"]) == 1

    # Update Event
    u_res = executor.update_event(
        event_id="evt_1001", updates={"summary": "Updated"}, trace_id="tr_u1",
        gateway_auth=gw_update, user_id=user_id
    )
    assert u_res["status"] == "success"

    # Delete Event
    d_res = executor.delete_event(
        event_id="evt_1001", trace_id="tr_d1",
        gateway_auth=gw_delete, user_id=user_id
    )
    assert d_res["status"] == "success"

# 14. Disconnect Works
def test_disconnect_works():
    user_id = "user_disc_01"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="disc@example.com",
        access_token="ya29.disc_token"
    )

    headers = get_auth_header(user_id)
    response = client.delete("/api/connections/google", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    conn = connected_account_service.get_user_connection(user_id, "google")
    assert conn is None

# 15. Cross-User Access Blocked
def test_cross_user_access_blocked():
    user_owner = "user_owner_999"
    user_attacker = "user_attacker_888"

    connected_account_service.create_connection(
        user_id=user_owner,
        provider="google",
        email="owner@example.com",
        access_token="ya29.owner_token"
    )

    headers_attacker = get_auth_header(user_attacker)

    res_list = client.get("/api/connections", headers=headers_attacker)
    assert res_list.status_code == 200
    assert len(res_list.json()["connections"]) == 0

    res_del = client.delete("/api/connections/google", headers=headers_attacker)
    assert res_del.status_code == 404

    owner_conn = connected_account_service.get_user_connection(user_owner, "google")
    assert owner_conn is not None
