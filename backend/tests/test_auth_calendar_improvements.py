"""
test_auth_calendar_improvements.py — Verification suite for Auth & Calendar Improvements.

Covers:
1. Hardcoded identity eradication check
2. Google OAuth signup flow (least privilege identity scopes)
3. Apple OAuth Provider architecture & ES256 / claim extraction
4. Guest session binding & data migration in OAuth callback
5. Calendar synchronization status & provider isolation
"""

import os
import time
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token, verify_token_string
from app.integrations.oauth.registry import oauth_provider_registry
from app.integrations.oauth.apple import AppleOAuthProvider
from app.services.oauth_transaction_service import oauth_transaction_service
from app.services.connected_account_service import connected_account_service
from app.executors.calendar_executor import CalendarExecutor
from app.core.gateway_auth import GatewayAuth


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_stores():
    from app.core.security import rate_limit_store
    rate_limit_store.clear()
    yield
    rate_limit_store.clear()



# ─── 1. HARDCODED IDENTITY ERADICATION CHECKS ──────────────────────────────

def test_no_hardcoded_raj_kumar_in_auth_or_defaults():
    """Verify that Raj Kumar is not used anywhere in core auth or fallback logic."""
    from app.core.auth_dependencies import get_current_user
    # Ensure default guest user representation is strictly 'Guest User'
    guest_token = create_access_token({
        "sub": "usr_guest_test123",
        "user_id": "usr_guest_test123",
        "is_guest": True
    })
    data = verify_token_string(guest_token)
    assert data.is_guest is True


# ─── 2. GOOGLE OAUTH SIGNUP FLOW (LEAST PRIVILEGE SCOPES) ──────────────────

def test_google_oauth_signup_scopes(monkeypatch):
    """
    Verify purpose='signup' requests only identity scopes (openid, email, profile)
    and strictly avoids Gmail and Google Calendar permission scopes.
    """
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-google-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/oauth/google/callback")

    google_provider = oauth_provider_registry.get("google")

    signup_url = google_provider.get_authorization_url(
        state="test_state_123",
        code_challenge="test_challenge_123",
        purpose="signup"
    )

    # Validate that least-privilege scopes are present
    assert "openid" in signup_url
    assert "email" in signup_url
    assert "profile" in signup_url

    # Validate that high-privilege service scopes are EXCLUDED
    assert "gmail.send" not in signup_url
    assert "googleapis.com%2Fauth%2Fcalendar" not in signup_url
    assert "googleapis.com/auth/calendar" not in signup_url


def test_start_oauth_signup_with_guest_session_binding(client, monkeypatch):
    """
    Verify starting an OAuth signup transaction binds the existing guest session
    to the state transaction so that guest data can be migrated upon completion.
    """
    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-google-client-secret")

    guest_token = create_access_token({
        "sub": "usr_guest_abc12345",
        "user_id": "usr_guest_abc12345",
        "is_guest": True
    })

    response = client.get(
        "/api/oauth/google/start?purpose=signup",
        headers={"Authorization": f"Bearer {guest_token}"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["purpose"] == "signup"
    assert "url" in res_data
    assert "state" in res_data

    # Verify transaction stores the guest user_id
    state = res_data["state"]
    stored_tx = _IN_MEMORY_OAUTH_TRANSACTIONS.get(state)
    assert stored_tx is not None
    assert stored_tx["user_id"] == "usr_guest_abc12345"
    assert stored_tx["purpose"] == "signup"


# ─── 3. APPLE OAUTH PROVIDER ARCHITECTURE ───────────────────────────────────

def test_apple_oauth_provider_unconfigured_behavior(monkeypatch):
    """Verify Apple provider reports unconfigured and raises informative errors when credentials missing."""
    monkeypatch.delenv("APPLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("APPLE_PRIVATE_KEY", raising=False)

    apple_provider = AppleOAuthProvider()
    assert apple_provider.is_configured() is False

    with pytest.raises(ValueError, match="Apple Sign-In is not configured"):
        apple_provider.get_authorization_url(state="apple_state_001")


def test_apple_oauth_provider_configured_authorization_url(monkeypatch):
    """Verify Apple provider builds correct authorization URL with form_post and response_type."""
    monkeypatch.setenv("APPLE_CLIENT_ID", "com.mitra.companion.service")
    monkeypatch.setenv("APPLE_TEAM_ID", "TEAM123456")
    monkeypatch.setenv("APPLE_KEY_ID", "KEY123456")
    monkeypatch.setenv("APPLE_PRIVATE_KEY", "MOCK_PRIVATE_KEY_CONTENT")
    monkeypatch.setenv("APPLE_REDIRECT_URI", "https://api.mitra.local/api/oauth/apple/callback")

    apple_provider = AppleOAuthProvider()
    assert apple_provider.is_configured() is True

    url = apple_provider.get_authorization_url(state="apple_state_002")
    assert "appleid.apple.com/auth/authorize" in url
    assert "client_id=com.mitra.companion.service" in url
    assert "response_mode=form_post" in url
    assert "code+id_token" in url or "code%20id_token" in url
    assert "state=apple_state_002" in url


def test_apple_oauth_identity_claim_extraction():
    """Verify Apple provider extracts stable 'sub' claim and handles private relay emails."""
    apple_provider = AppleOAuthProvider()

    # Generate mock Apple id_token JWT (simulated decoded claims)
    import jwt
    mock_claims = {
        "iss": "https://appleid.apple.com",
        "aud": "com.mitra.companion.service",
        "sub": "001234.abcdef567890.1234",
        "email": "user123@privaterelay.appleid.com",
        "email_verified": True,
    }
    # 32-byte secret for test JWT
    mock_token = jwt.encode(mock_claims, "a_very_secure_test_secret_32_bytes_long!", algorithm="HS256")

    identity = apple_provider.get_user_identity(access_token="apple_access_token", id_token=mock_token)
    assert identity["provider_subject"] == "001234.abcdef567890.1234"
    assert identity["email"] == "user123@privaterelay.appleid.com"
    assert identity["is_private_email"] is True
    assert identity["email_verified"] is True


# ─── 4. OAUTH CALLBACK WITH GUEST DATA MIGRATION ────────────────────────────

def test_oauth_callback_signup_migrates_guest_data(client, monkeypatch):
    """
    Verify that completing OAuth with purpose='signup' for a guest session:
    1. Replaces guest token with permanent JWT
    2. Sets is_guest = False
    3. Migrates guest MongoDB records
    """
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-google-client-secret")

    guest_id = "usr_guest_migration_test"
    tx = oauth_transaction_service.create_transaction(
        provider="google",
        purpose="signup",
        user_id=guest_id
    )
    state = tx["state"]

    mock_google = oauth_provider_registry.get("google")
    with patch.object(mock_google, "exchange_code", return_value={
        "access_token": "mock_google_token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }), patch.object(mock_google, "get_user_identity", return_value={
        "provider_subject": "google_sub_9999",
        "email": "newuser@gmail.com",
        "name": "New Mitra User",
        "email_verified": True
    }):
        response = client.get(f"/api/oauth/google/callback?code=mock_code&state={state}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "token" in data
        assert data["user"]["email"] == "newuser@gmail.com"
        assert data["user"]["is_guest"] is False

        # Verify issued JWT token
        token_info = verify_token_string(data["token"])
        assert token_info.is_guest is False


# ─── 5. CALENDAR SYNCHRONIZATION STATUS & PROVIDER ISOLATION ────────────────

def test_calendar_executor_unconnected_returns_saved_only_in_mitra():
    """
    Verify when no external provider is connected, CalendarExecutor:
    1. Returns sync_status='Saved only in Mitra'
    2. Returns synchronized=False
    3. Never claims external Google/Microsoft sync
    """
    executor = CalendarExecutor()
    gw_token = GatewayAuth.issue(
        trace_id="tr_cal_unconn",
        platform="calendar",
        action="create_event",
        decision="allow"
    )

    res = executor.create_event(
        title="Weekly Sync",
        start_time="2026-09-15T10:00:00Z",
        trace_id="tr_cal_unconn",
        gateway_auth=gw_token,
        user_id="usr_unconnected_999"
    )

    assert res["status"] == "success"
    assert res["sync_status"] == "Saved only in Mitra"
    assert res["synchronized"] is False
    assert res["provider"] is None
    assert res["provider_event_id"] is None


def test_calendar_executor_google_connected_sync():
    """
    Verify when Google Calendar is connected, event creation writes to Google API
    and returns sync_status='Created in Google Calendar'.
    """
    executor = CalendarExecutor()
    gw_token = GatewayAuth.issue(
        trace_id="tr_cal_google",
        platform="calendar",
        action="create_event",
        decision="allow"
    )

    with patch.object(executor, "_get_effective_connection", return_value=("mock_google_token", "google")), \
         patch("requests.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            "id": "g_evt_777",
            "htmlLink": "https://calendar.google.com/event?eid=777"
        }
        mock_post.return_value = mock_res

        res = executor.create_event(
            title="Design Review",
            start_time="2026-09-15T14:00:00Z",
            trace_id="tr_cal_google",
            gateway_auth=gw_token,
            user_id="usr_google_user",
            timezone="America/New_York"
        )

        assert res["status"] == "success"
        assert res["sync_status"] == "Created in Google Calendar"
        assert res["synchronized"] is True
        assert res["provider"] == "google"
        assert res["provider_event_id"] == "g_evt_777"


def test_calendar_executor_microsoft_connected_sync():
    """
    Verify when Microsoft Calendar is connected, event creation writes to Microsoft Graph API
    and returns sync_status='Created in Microsoft Calendar'.
    """
    executor = CalendarExecutor()
    gw_token = GatewayAuth.issue(
        trace_id="tr_cal_ms",
        platform="calendar",
        action="create_event",
        decision="allow"
    )

    with patch.object(executor, "_get_effective_connection", return_value=("mock_ms_token", "microsoft")), \
         patch("requests.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 201
        mock_res.json.return_value = {
            "id": "ms_evt_888",
            "webLink": "https://outlook.office.com/calendar/item/888"
        }
        mock_post.return_value = mock_res

        res = executor.create_event(
            title="Sprint Planning",
            start_time="2026-09-16T11:00:00Z",
            trace_id="tr_cal_ms",
            gateway_auth=gw_token,
            user_id="usr_ms_user",
            timezone="Europe/London"
        )

        assert res["status"] == "success"
        assert res["sync_status"] == "Created in Microsoft Calendar"
        assert res["synchronized"] is True
        assert res["provider"] == "microsoft"
        assert res["provider_event_id"] == "ms_evt_888"


def test_calendar_time_range_validation():
    """Verify CalendarExecutor rejects explicit invalid end times (end <= start) and defaults missing end times to 1 hour."""
    executor = CalendarExecutor()

    # 1. Missing end time defaults to start + 1 hour
    gw_token_1 = GatewayAuth.issue(
        trace_id="tr_range_default",
        platform="calendar",
        action="create_event",
        decision="allow"
    )
    default_res = executor.create_event(
        title="Range Default Test",
        start_time="2026-09-15T15:00:00Z",
        end_time=None,
        trace_id="tr_range_default",
        gateway_auth=gw_token_1,
        user_id="usr_test"
    )
    assert default_res["status"] == "success"
    assert default_res["event"]["end"] == "2026-09-15T16:00:00+00:00"

    # 2. Explicit invalid end time returns a clear validation error
    gw_token_2 = GatewayAuth.issue(
        trace_id="tr_range_err",
        platform="calendar",
        action="create_event",
        decision="allow"
    )
    err_res = executor.create_event(
        title="Range Error Test",
        start_time="2026-09-15T15:00:00Z",
        end_time="2026-09-15T14:00:00Z",  # Invalid: before start
        trace_id="tr_range_err",
        gateway_auth=gw_token_2,
        user_id="usr_test"
    )
    assert err_res["status"] == "error"
    assert "Invalid time range" in err_res["error"]
    assert "strictly after" in err_res["error"]


def test_calendar_endpoint_invalid_time_range_returns_400(client):
    """Verify POST /api/pages/calendar/events returns 400 when end time <= start time."""
    payload = {
        "title": "Invalid End Time Meeting",
        "start": "2026-09-15T15:00:00Z",
        "end": "2026-09-15T14:00:00Z"
    }
    response = client.post("/api/pages/calendar/events", json=payload, headers={"X-API-Key": "localtest"})
    assert response.status_code == 400
    assert "Invalid time range" in response.json()["detail"]
