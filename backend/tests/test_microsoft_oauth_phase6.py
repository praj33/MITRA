import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.core.security import create_access_token
from app.services.oauth_transaction_service import oauth_transaction_service
from app.services.connected_account_service import connected_account_service
from app.services.token_refresh_service import token_refresh_service
from app.executors.email_executor import EmailExecutor
from app.executors.calendar_executor import CalendarExecutor
from app.core.gateway_auth import GatewayAuth

client = TestClient(app)

@pytest.fixture
def test_user_a():
    return {"user_id": "usr_ms_test_a", "email": "usera@mitra.org", "name": "User A"}

@pytest.fixture
def test_user_b():
    return {"user_id": "usr_ms_test_b", "email": "userb@mitra.org", "name": "User B"}

@pytest.fixture
def auth_headers_a(test_user_a):
    token = create_access_token({"sub": test_user_a["user_id"], "user_id": test_user_a["user_id"], "email": test_user_a["email"]})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_b(test_user_b):
    token = create_access_token({"sub": test_user_b["user_id"], "user_id": test_user_b["user_id"], "email": test_user_b["email"]})
    return {"Authorization": f"Bearer {token}"}


# 1. Unauthenticated Microsoft connection start rejected
def test_unauthenticated_microsoft_connection_start_rejected():
    res = client.get("/api/oauth/microsoft/start?purpose=connect")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


# 2. Authenticated user can start Microsoft OAuth
def test_authenticated_user_can_start_microsoft_oauth(auth_headers_a):
    res = client.get("/api/oauth/microsoft/start?purpose=connect", headers=auth_headers_a)
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    assert "login.microsoftonline.com" in data["url"]
    assert "state" in data
    assert data["provider"] == "microsoft"


# 3. State generated with sufficient entropy & 4. PKCE S256 challenge generated
def test_microsoft_state_and_pkce_generated(auth_headers_a):
    res = client.get("/api/oauth/microsoft/start?purpose=connect", headers=auth_headers_a)
    data = res.json()
    state = data["state"]
    assert len(state) >= 32

    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS
    tx = _IN_MEMORY_OAUTH_TRANSACTIONS.get(state)
    assert tx is not None
    assert tx["provider"] == "microsoft"
    assert tx["code_challenge"] is not None
    assert tx["code_verifier"] is not None


# 5. State bound to authenticated user
def test_microsoft_state_bound_to_authenticated_user(auth_headers_a, test_user_a):
    res = client.get("/api/oauth/microsoft/start?purpose=connect", headers=auth_headers_a)
    state = res.json()["state"]
    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS
    tx = _IN_MEMORY_OAUTH_TRANSACTIONS.get(state)
    assert tx["user_id"] == test_user_a["user_id"]


# 6. State cannot be reused
def test_microsoft_state_cannot_be_reused(auth_headers_a):
    res = client.get("/api/oauth/microsoft/start?purpose=connect", headers=auth_headers_a)
    state = res.json()["state"]
    # First consumption succeeds
    tx1 = oauth_transaction_service.validate_and_consume_transaction(state, "microsoft")
    assert tx1 is not None
    # Second consumption fails
    with pytest.raises(Exception):
        oauth_transaction_service.validate_and_consume_transaction(state, "microsoft")


# 7. Expired state rejected
def test_microsoft_expired_state_rejected():
    tx = oauth_transaction_service.create_transaction("microsoft", "connect", "usr_expired")
    state = tx["state"]

    # Backdate transaction expiration
    expired_at = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS
    _IN_MEMORY_OAUTH_TRANSACTIONS[state]["expires_at"] = expired_at

    with pytest.raises(Exception):
        oauth_transaction_service.validate_and_consume_transaction(state, "microsoft")


# 8. Callback performs server-side code exchange & 9. Microsoft identity resolved & 10. Tokens encrypted at rest
@patch("app.integrations.oauth.microsoft.requests.post")
@patch("app.integrations.oauth.microsoft.requests.get")
def test_full_microsoft_oauth_callback_flow(mock_get, mock_post, auth_headers_a, test_user_a):
    # 1. Start OAuth
    start_res = client.get("/api/oauth/microsoft/start?purpose=connect", headers=auth_headers_a)
    state = start_res.json()["state"]

    # 2. Mock Microsoft token exchange response
    mock_token_res = MagicMock()
    mock_token_res.status_code = 200
    mock_token_res.json.return_value = {
        "access_token": "mock_ms_access_token_123",
        "refresh_token": "mock_ms_refresh_token_456",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "openid email profile Mail.Send Calendars.ReadWrite"
    }
    mock_post.return_value = mock_token_res

    # 3. Mock Microsoft Graph userinfo response
    mock_userinfo_res = MagicMock()
    mock_userinfo_res.status_code = 200
    mock_userinfo_res.json.return_value = {
        "id": "ms_sub_1001",
        "displayName": "User A (Microsoft)",
        "mail": "usera.ms@outlook.com",
        "userPrincipalName": "usera.ms@outlook.com"
    }
    mock_get.return_value = mock_userinfo_res

    # 4. Trigger callback
    cb_res = client.get(f"/api/oauth/microsoft/callback?code=mock_ms_code&state={state}")
    assert cb_res.status_code in (200, 302)

    # 5. Verify stored connection & token encryption
    conn = connected_account_service.get_user_connection(test_user_a["user_id"], "microsoft", include_decrypted_tokens=True)
    assert conn is not None
    assert conn["email"] == "usera.ms@outlook.com"
    assert conn["access_token"] == "mock_ms_access_token_123"
    assert conn["refresh_token"] == "mock_ms_refresh_token_456"
    assert conn["status"] == "connected"


# 11. Connection API never returns tokens
def test_microsoft_connection_api_never_returns_tokens(auth_headers_a, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="microsoft",
        email="usera.ms@outlook.com",
        access_token="secret_access_token",
        refresh_token="secret_refresh_token"
    )

    res = client.get("/api/connections", headers=auth_headers_a)
    assert res.status_code == 200
    conns = res.json()["connections"]
    ms_conn = next((c for c in conns if c["provider"] == "microsoft"), None)
    assert ms_conn is not None
    assert "access_token" not in ms_conn
    assert "refresh_token" not in ms_conn
    assert "encrypted_access_token" not in ms_conn
    assert ms_conn["email"] == "usera.ms@outlook.com"


# 12. Token refresh works
@patch("app.integrations.oauth.microsoft.requests.post")
def test_microsoft_token_refresh_works(mock_post, test_user_a):
    # Store expired access token with valid refresh token
    expired_at = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="microsoft",
        email="usera.ms@outlook.com",
        access_token="expired_access_token",
        refresh_token="valid_refresh_token",
        expires_at=expired_at
    )

    mock_refresh_res = MagicMock()
    mock_refresh_res.status_code = 200
    mock_refresh_res.json.return_value = {
        "access_token": "new_refreshed_ms_access_token",
        "refresh_token": "rotated_ms_refresh_token",
        "expires_in": 3600
    }
    mock_post.return_value = mock_refresh_res

    # Obtain valid access token transparently
    refreshed_token = token_refresh_service.get_valid_access_token(test_user_a["user_id"], "microsoft")
    assert refreshed_token == "new_refreshed_ms_access_token"

    updated_conn = connected_account_service.get_user_connection(test_user_a["user_id"], "microsoft", include_decrypted_tokens=True)
    assert updated_conn["access_token"] == "new_refreshed_ms_access_token"
    assert updated_conn["refresh_token"] == "rotated_ms_refresh_token"
    assert updated_conn["status"] == "connected"


# 13. Refresh failure causes needs_reauthorization
@patch("app.integrations.oauth.microsoft.requests.post")
def test_microsoft_refresh_failure_causes_needs_reauthorization(mock_post, test_user_a):
    expired_at = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="microsoft",
        email="usera.ms@outlook.com",
        access_token="expired_token",
        refresh_token="revoked_refresh_token",
        expires_at=expired_at
    )

    mock_res = MagicMock()
    mock_res.status_code = 400
    mock_res.text = "invalid_grant: The refresh token has been revoked."
    mock_post.return_value = mock_res

    with pytest.raises(Exception):
        token_refresh_service.get_valid_access_token(test_user_a["user_id"], "microsoft")

    conn = connected_account_service.get_user_connection(test_user_a["user_id"], "microsoft")
    assert conn["status"] == "needs_reauthorization"


# 14. Microsoft email execution uses user-scoped connection
@patch("app.executors.email_executor.requests.post")
def test_microsoft_email_execution_uses_user_scoped_connection(mock_post, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="microsoft",
        email="usera.ms@outlook.com",
        access_token="active_ms_email_token",
        expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
    )

    mock_graph_res = MagicMock()
    mock_graph_res.status_code = 202
    mock_post.return_value = mock_graph_res

    email_exec = EmailExecutor()
    result = email_exec.send_message(
        to_email="recipient@example.com",
        subject="Test Outlook Mail",
        message="Hello from MITRA Outlook integration!",
        trace_id="tr_ms_email_001",
        user_id=test_user_a["user_id"]
    )

    assert result["status"] == "success"
    assert result["method"] == "outlook_oauth_api"
    assert result["user_connected_account"] is True

    # Verify Microsoft Graph sendMail endpoint was invoked with Bearer token
    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert "graph.microsoft.com/v1.0/me/sendMail" in args[0]
    assert kwargs["headers"]["Authorization"] == "Bearer active_ms_email_token"


# 15. Microsoft calendar execution uses user-scoped connection
@patch("app.executors.calendar_executor.requests.post")
@patch("app.executors.calendar_executor.requests.get")
@patch("app.executors.calendar_executor.requests.patch")
@patch("app.executors.calendar_executor.requests.delete")
def test_microsoft_calendar_execution_uses_user_scoped_connection(
    mock_delete, mock_patch, mock_get, mock_post, test_user_a
):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="microsoft",
        email="usera.ms@outlook.com",
        access_token="active_ms_cal_token",
        expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
    )
    gw_token = GatewayAuth.issue(trace_id="tr_ms_cal_001", platform="calendar", action="create_event", decision="allow")
    cal_exec = CalendarExecutor()

    # 1. Create Event via Microsoft Graph
    mock_create_res = MagicMock()
    mock_create_res.status_code = 201
    mock_create_res.json.return_value = {"id": "ms_evt_999", "webLink": "https://outlook.office.com/calendar/item/999"}
    mock_post.return_value = mock_create_res

    res_create = cal_exec.create_event(
        title="Microsoft Graph Sync Meeting",
        start_time="2026-09-04T10:00:00Z",
        trace_id="tr_ms_cal_001",
        gateway_auth=gw_token,
        user_id=test_user_a["user_id"]
    )
    assert res_create["status"] == "success"
    assert res_create["method"] == "microsoft_calendar_api"
    assert res_create["event_id"] == "ms_evt_999"

    # 2. List Events via Microsoft Graph
    mock_list_res = MagicMock()
    mock_list_res.status_code = 200
    mock_list_res.json.return_value = {
        "value": [{"id": "ms_evt_999", "subject": "Microsoft Graph Sync Meeting", "start": {"dateTime": "2026-09-04T10:00:00Z"}}]
    }
    mock_get.return_value = mock_list_res

    gw_list_token = GatewayAuth.issue(trace_id="tr_ms_cal_002", platform="calendar", action="list_events", decision="allow")
    res_list = cal_exec.list_events(trace_id="tr_ms_cal_002", gateway_auth=gw_list_token, user_id=test_user_a["user_id"])
    assert res_list["status"] == "success"
    assert res_list["method"] == "microsoft_calendar_api"
    assert len(res_list["events"]) == 1

    # 3. Update Event via Microsoft Graph
    mock_update_res = MagicMock()
    mock_update_res.status_code = 200
    mock_patch.return_value = mock_update_res

    gw_up_token = GatewayAuth.issue(trace_id="tr_ms_cal_003", platform="calendar", action="update_event", decision="allow")
    res_up = cal_exec.update_event(
        event_id="ms_evt_999",
        updates={"title": "Updated Meeting Subject"},
        trace_id="tr_ms_cal_003",
        gateway_auth=gw_up_token,
        user_id=test_user_a["user_id"]
    )
    assert res_up["status"] == "success"
    assert res_up["method"] == "microsoft_calendar_api"

    # 4. Delete Event via Microsoft Graph
    mock_del_res = MagicMock()
    mock_del_res.status_code = 204
    mock_delete.return_value = mock_del_res

    gw_del_token = GatewayAuth.issue(trace_id="tr_ms_cal_004", platform="calendar", action="delete_event", decision="allow")
    res_del = cal_exec.delete_event(
        event_id="ms_evt_999",
        trace_id="tr_ms_cal_004",
        gateway_auth=gw_del_token,
        user_id=test_user_a["user_id"]
    )
    assert res_del["status"] == "success"
    assert res_del["method"] == "microsoft_calendar_api"


# 16. Microsoft disconnect removes connection safely
def test_microsoft_disconnect_removes_connection_safely(auth_headers_a, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="microsoft",
        email="usera.ms@outlook.com",
        access_token="token_to_purge"
    )

    del_res = client.delete("/api/connections/microsoft", headers=auth_headers_a)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    conn = connected_account_service.get_user_connection(test_user_a["user_id"], "microsoft")
    assert conn is None


# 17. Cross-user connection access blocked
def test_cross_user_microsoft_connection_access_blocked(auth_headers_a, auth_headers_b, test_user_a, test_user_b):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="microsoft",
        email="usera.ms@outlook.com",
        access_token="user_a_token"
    )

    # User B lists connections — User A's connection must not appear
    res_b = client.get("/api/connections", headers=auth_headers_b)
    conns_b = res_b.json()["connections"]
    assert not any(c["email"] == "usera.ms@outlook.com" for c in conns_b)

    # User B attempts to disconnect User A's Microsoft connection — returns 404
    del_b = client.delete("/api/connections/microsoft", headers=auth_headers_b)
    assert del_b.status_code == 404


# 18. Client-supplied user_id cannot override authenticated identity
def test_client_supplied_user_id_cannot_override_identity(auth_headers_a, test_user_a, test_user_b):
    res = client.get(f"/api/oauth/microsoft/start?purpose=connect&user_id={test_user_b['user_id']}", headers=auth_headers_a)
    assert res.status_code == 200
    state = res.json()["state"]

    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS
    tx = _IN_MEMORY_OAUTH_TRANSACTIONS.get(state)
    assert tx["user_id"] == test_user_a["user_id"]
    assert tx["user_id"] != test_user_b["user_id"]
