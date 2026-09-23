import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.gateway_auth import GatewayAuth
from app.services.connected_account_service import connected_account_service
from app.services.oauth_transaction_service import oauth_transaction_service
from app.executors.calendar_executor import CalendarExecutor
from app.integrations.oauth.google import GoogleOAuthProvider

client = TestClient(app)

TEST_USER_ID = "usr_cal_test_e2e_01"
TEST_JWT_SECRET = "test_phase_cal_jwt_secret_key_mitra_999"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "test_cal_key_32bytes_length_val=")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_google_client_secret_xyz")


def get_auth_headers(user_id: str = TEST_USER_ID) -> dict:
    token = create_access_token({"sub": user_id, "user_id": user_id, "email": f"{user_id}@example.com"})
    return {"Authorization": f"Bearer {token}"}


# ─── A. No connected provider: event saved locally ───────────────────────────
def test_create_event_without_provider_saves_locally():
    user_id = "usr_unconnected_cal_test"
    payload = {
        "title": "Local Standup",
        "start": "2026-09-24T09:00:00",
        "end": "2026-09-24T10:00:00",
        "timezone": "Asia/Kolkata",
        "location": "Room 1",
        "description": "Daily sync"
    }

    res = client.post(f"/api/pages/calendar/events?user_id={user_id}", json=payload, headers=get_auth_headers(user_id))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["sync_status"] == "Saved only in Mitra"
    assert data["synchronized"] is False
    assert data["provider"] is None
    assert data["event"]["title"] == "Local Standup"
    assert data["event"]["timezone"] == "Asia/Kolkata"


# ─── B. Google Calendar connected with proper scope: sync succeeds ───────────
@patch("requests.post")
def test_create_event_google_connected_success(mock_post):
    user_id = "usr_google_cal_full"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="cal_user@gmail.com",
        access_token="ya29.valid_access_token",
        scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar"]
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "g_event_12345",
        "htmlLink": "https://calendar.google.com/event?eid=12345"
    }
    mock_post.return_value = mock_resp

    payload = {
        "title": "Strategy Session",
        "start": "2026-09-24T09:00:00",
        "end": "2026-09-24T10:00:00",
        "timezone": "Asia/Kolkata"
    }

    res = client.post(f"/api/pages/calendar/events?user_id={user_id}", json=payload, headers=get_auth_headers(user_id))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["synchronized"] is True
    assert data["sync_status"] == "Created in Google Calendar"
    assert data["provider"] == "google"
    assert data["event"]["external_event_id"] == "g_event_12345"
    assert data["event"]["external_event_link"] == "https://calendar.google.com/event?eid=12345"

    # Verify posted payload has valid RFC3339 datetime with timezone offset
    call_args = mock_post.call_args
    post_json = call_args[1]["json"]
    assert post_json["start"]["timeZone"] == "Asia/Kolkata"
    assert "+05:30" in post_json["start"]["dateTime"]
    assert post_json["end"]["timeZone"] == "Asia/Kolkata"
    assert "+05:30" in post_json["end"]["dateTime"]


# ─── C. Google token has only identity scopes: no API call, saved locally ────
@patch("requests.post")
def test_create_event_google_identity_only_skips_external_call(mock_post):
    user_id = "usr_google_identity_only"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="identity_user@gmail.com",
        access_token="ya29.identity_only_token",
        scopes=["openid", "email", "profile"]
    )

    payload = {
        "title": "Internal 1-on-1",
        "start": "2026-09-24T14:00:00",
        "end": "2026-09-24T15:00:00",
        "timezone": "Asia/Kolkata"
    }

    res = client.post(f"/api/pages/calendar/events?user_id={user_id}", json=payload, headers=get_auth_headers(user_id))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["synchronized"] is False
    assert "Google Calendar permission required" in data["sync_status"]
    assert data["event"]["external_event_id"] is None
    # Google API must NOT have been called
    mock_post.assert_not_called()


# ─── D. Google API 403 insufficientPermissions: saved locally, no crash ──────
@patch("requests.post")
def test_create_event_google_403_insufficient_permissions(mock_post):
    user_id = "usr_google_403_scope"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="user_403@gmail.com",
        access_token="ya29.scope_403_token",
        scopes=["openid", "https://www.googleapis.com/auth/calendar"]
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = '{"error": {"code": 403, "message": "Request had insufficient authentication scopes.", "errors": [{"reason": "insufficientPermissions"}]}}'
    mock_post.return_value = mock_resp

    payload = {
        "title": "Sprint Planning",
        "start": "2026-09-24T11:00:00",
        "end": "2026-09-24T12:00:00",
        "timezone": "Asia/Kolkata"
    }

    res = client.post(f"/api/pages/calendar/events?user_id={user_id}", json=payload, headers=get_auth_headers(user_id))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["synchronized"] is False
    assert "Google Calendar permission required" in data["sync_status"]
    assert data["event"]["external_event_id"] is None


# ─── E. Google API 401: marks needs_reauthorization, saved locally ───────────
@patch("requests.post")
def test_create_event_google_401_auth_expired(mock_post):
    user_id = "usr_google_401_expired"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="user_401@gmail.com",
        access_token="ya29.expired_token",
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = '{"error": {"code": 401, "message": "Invalid Credentials"}}'
    mock_post.return_value = mock_resp

    payload = {
        "title": "Sprint Retrospective",
        "start": "2026-09-24T16:00:00",
        "end": "2026-09-24T17:00:00"
    }

    res = client.post(f"/api/pages/calendar/events?user_id={user_id}", json=payload, headers=get_auth_headers(user_id))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["synchronized"] is False
    assert "authentication expired" in data["sync_status"].lower()
    assert data["event"]["external_event_id"] is None


# ─── F. Google API disabled (SERVICE_DISABLED): saved locally, clear status ──
@patch("requests.post")
def test_create_event_google_403_service_disabled(mock_post):
    user_id = "usr_google_disabled_api"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="disabled_api@gmail.com",
        access_token="ya29.disabled_token",
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = '{"error": {"code": 403, "message": "Google Calendar API has not been used in project before or it is disabled.", "status": "PERMISSION_DENIED", "details": [{"reason": "SERVICE_DISABLED"}]}}'
    mock_post.return_value = mock_resp

    payload = {
        "title": "Quarterly Review",
        "start": "2026-09-24T15:00:00",
        "end": "2026-09-24T16:00:00"
    }

    res = client.post(f"/api/pages/calendar/events?user_id={user_id}", json=payload, headers=get_auth_headers(user_id))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["synchronized"] is False
    assert "disabled" in data["sync_status"].lower()


# ─── G. Google API 400: saved locally with sanitized error status ────────────
@patch("requests.post")
def test_create_event_google_400_bad_request(mock_post):
    user_id = "usr_google_400_bad"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="bad_req@gmail.com",
        access_token="ya29.bad_token",
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"code": 400, "message": "Invalid Value"}}
    mock_resp.text = '{"error": {"code": 400, "message": "Invalid Value"}}'
    mock_post.return_value = mock_resp

    payload = {
        "title": "Validation Test",
        "start": "2026-09-24T10:00:00",
        "end": "2026-09-24T11:00:00"
    }

    res = client.post(f"/api/pages/calendar/events?user_id={user_id}", json=payload, headers=get_auth_headers(user_id))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["synchronized"] is False
    assert "Invalid Value" in data["sync_status"] or "Invalid event data" in data["sync_status"]


# ─── H & I. Browser timezone and RFC3339 preservation ────────────────────────
def test_calendar_executor_rfc3339_preserves_user_timezone():
    executor = CalendarExecutor()
    start_rfc, end_rfc, resolved_tz = executor._format_event_times(
        "2026-09-24T09:00:00",
        "2026-09-24T10:00:00",
        "Asia/Kolkata"
    )
    assert resolved_tz == "Asia/Kolkata"
    assert start_rfc == "2026-09-24T09:00:00+05:30"
    assert end_rfc == "2026-09-24T10:00:00+05:30"

    # NY timezone test
    start_ny, end_ny, tz_ny = executor._format_event_times(
        "2026-09-24T09:00:00",
        "2026-09-24T10:00:00",
        "America/New_York"
    )
    assert tz_ny == "America/New_York"
    assert "-04:00" in start_ny or "-05:00" in start_ny


# ─── J. OAuth connect: granted Calendar scope persisted in connected_accounts ─
@patch.object(GoogleOAuthProvider, "exchange_code")
@patch.object(GoogleOAuthProvider, "get_user_identity")
def test_oauth_connect_persists_calendar_scope(mock_identity, mock_exchange):
    mock_exchange.return_value = {
        "access_token": "ya29.granted_calendar_token",
        "refresh_token": "1//granted_calendar_rt",
        "expires_in": 3600,
        "scope": "openid email profile https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.send"
    }
    mock_identity.return_value = {
        "provider_subject": "google_sub_calendar_999",
        "email": "user_calendar@gmail.com",
        "name": "Calendar User"
    }

    user_id = "usr_oauth_cal_connect_test"
    headers = get_auth_headers(user_id)
    start_res = client.get("/api/oauth/google/start?purpose=connect", headers=headers)
    assert start_res.status_code == 200
    state = start_res.json()["state"]

    callback_res = client.get(f"/api/oauth/google/callback?code=valid_cal_code&state={state}")
    assert callback_res.status_code == 200

    conn = connected_account_service.get_user_connection(user_id, "google", include_decrypted_tokens=False)
    assert conn is not None
    assert "scopes" in conn
    assert "https://www.googleapis.com/auth/calendar" in conn["scopes"]
    assert "email" in conn["scopes"]
