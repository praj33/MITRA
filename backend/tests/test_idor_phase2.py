import asyncio
import os
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def set_env_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_phase2_secret_key_mitra_99999")
    monkeypatch.setenv("API_KEY", "test_api_key_mitra_123")


def get_auth_headers(user_id: str):
    token = create_access_token({"user_id": user_id, "email": f"{user_id}@mitra.ai"})
    return {"Authorization": f"Bearer {token}"}


# ── 1. Unauthenticated Requests Return 401 ──────────────────────────────────

def test_unauthenticated_integrations_returns_401(client):
    response = client.get("/api/integrations")
    assert response.status_code == 401


def test_unauthenticated_notifications_returns_401(client):
    response = client.get("/api/v1/notifications")
    assert response.status_code == 401


def test_unauthenticated_presence_returns_401(client):
    response = client.get("/api/v1/presence/me")
    assert response.status_code == 401


def test_unauthenticated_companion_chat_returns_401(client):
    response = client.post("/api/companion/chat", json={"message": "Hello"})
    assert response.status_code == 401


def test_unauthenticated_workflow_run_returns_401(client):
    response = client.post("/api/workflow/run", json={"workflow_name": "daily_briefing"})
    assert response.status_code == 401


# ── 2. User A Accessing Own Resources Succeeds ──────────────────────────────

def test_user_a_accesses_own_integrations(client):
    headers = get_auth_headers("user_alpha")
    response = client.get("/api/integrations", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_alpha"


def test_user_a_creates_and_fetches_own_notifications(client):
    headers = get_auth_headers("user_alpha")

    # Create notification
    create_res = client.post(
        "/api/v1/notifications/",
        json={"title": "Test Title", "body": "Test Body"},
        headers=headers
    )
    assert create_res.status_code == 200
    notif_id = create_res.json()["notification"]["id"]

    # Fetch own notifications
    get_res = client.get("/api/v1/notifications/me", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["user_id"] == "user_alpha"
    assert any(n["id"] == notif_id for n in get_res.json()["notifications"])


def test_user_a_updates_own_presence(client):
    headers = get_auth_headers("user_alpha")
    post_res = client.post("/api/v1/presence/heartbeat", headers=headers)
    assert post_res.status_code == 200
    assert post_res.json()["user_id"] == "user_alpha"

    get_res = client.get("/api/v1/presence/me", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "online"


# ── 3. Cross-User Access / IDOR Impersonation Prevention ────────────────────

def test_idor_integrations_query_param_ignored(client):
    """User A supplies query parameter trying to impersonate User B."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/integrations?user_id=user_beta", headers=headers_a)
    assert response.status_code == 200
    data = response.json()
    # MUST be scoped to user_alpha
    assert data["user_id"] == "user_alpha"
    assert data["user_id"] != "user_beta"


def test_idor_notifications_path_param_rejected(client):
    """User A attempts to read User B's notifications via path param."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/v1/notifications/user_beta", headers=headers_a)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


def test_idor_notifications_mark_read_belonging_to_other_user_rejected(client):
    """User A attempts to mark read a notification belonging to User B."""
    headers_b = get_auth_headers("user_beta")
    create_res = client.post(
        "/api/v1/notifications/",
        json={"title": "User B Private", "body": "Secret"},
        headers=headers_b
    )
    notif_id = create_res.json()["notification"]["id"]

    headers_a = get_auth_headers("user_alpha")
    mark_res = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers_a)
    assert mark_res.status_code == 404


def test_idor_presence_path_param_rejected(client):
    """User A attempts to access User B's presence state via path param."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/v1/presence/user_beta", headers=headers_a)
    assert response.status_code == 403


def test_idor_companion_body_user_id_override_rejected(client):
    """User A attempts to send chat request with body user_id='user_beta'."""
    headers_a = get_auth_headers("user_alpha")

    with patch("app.companion.companion_orchestrator.companion_orchestrator.process") as mock_process:
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"reply": "Hello"}
        mock_process.return_value = mock_response

        response = client.post(
            "/api/companion/chat",
            json={"message": "Hello companion", "user_id": "user_beta"},
            headers=headers_a
        )
        assert response.status_code == 200

        # Verify orchestrator was invoked with authenticated user_alpha, NOT user_beta!
        mock_process.assert_called_once()
        _, kwargs = mock_process.call_args
        assert kwargs["user_id"] == "user_alpha"
        assert kwargs["user_id"] != "user_beta"


def test_idor_companion_greeting_path_param_rejected(client):
    """User A attempts to get User B's greeting."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/companion/greeting/user_beta", headers=headers_a)
    assert response.status_code == 403


def test_idor_companion_session_path_param_rejected(client):
    """User A attempts to read User B's session."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/companion/session/user_beta", headers=headers_a)
    assert response.status_code == 403


def test_idor_companion_memory_path_param_rejected(client):
    """User A attempts to read User B's memory facts."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/companion/memory/user_beta", headers=headers_a)
    assert response.status_code == 403


def test_idor_companion_briefing_path_param_rejected(client):
    """User A attempts to view User B's daily briefing."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/companion/briefing/user_beta", headers=headers_a)
    assert response.status_code == 403


def test_idor_companion_analytics_path_param_rejected(client):
    """User A attempts to view User B's analytics."""
    headers_a = get_auth_headers("user_alpha")
    response = client.get("/api/companion/analytics/user_beta", headers=headers_a)
    assert response.status_code == 403


def test_unauthenticated_calendar_feed_rejected(client):
    """Unauthenticated query string user_id harvesting of .ics calendar feed is blocked."""
    response = client.get("/api/calendar/feed.ics?user_id=victim_user_123")
    assert response.status_code == 401


def test_tokenized_calendar_feed_succeeds(client):
    """Calendar feed with valid signed token succeeds."""
    token = create_access_token({"user_id": "valid_user_cal", "feed": True})
    response = client.get(f"/api/calendar/feed.ics?token={token}")
    assert response.status_code == 200
    assert "BEGIN:VCALENDAR" in response.text
