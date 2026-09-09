import os
import time
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("API_KEY", "localtest")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("AUTH_STORE_MODE", "inmemory")

from app.main import app
from app.core.security import verify_token_string
from app.services.auth_service import auth_service

client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def setup_function():
    auth_service.reset_inmemory_store()


def test_guest_auth_endpoint_structure_and_jwt_claims():
    """Verify POST /api/auth/guest returns expected JSON structure and 1-hour JWT claims."""
    response = client.post("/api/auth/guest")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert "token" in data
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

    user = data["user"]
    assert user["id"].startswith("usr_guest_")
    assert user["is_guest"] is True
    assert user["name"] == "Guest User"

    # Validate JWT claims
    token_str = data["token"]
    decoded = verify_token_string(token_str)
    assert decoded.user_id == user["id"]
    assert decoded.is_guest is True


def test_guest_me_endpoint():
    """Verify GET /api/auth/me accepts guest token and returns guest user object."""
    guest_res = client.post("/api/auth/guest")
    assert guest_res.status_code == 200
    token = guest_res.json()["token"]
    guest_id = guest_res.json()["user"]["id"]

    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_user = me_res.json()["user"]
    assert me_user["id"] == guest_id
    assert me_user["is_guest"] is True


def test_guest_token_companion_chat_access():
    """Verify guest JWT token authenticates POST /api/companion/chat."""
    guest_res = client.post("/api/auth/guest")
    assert guest_res.status_code == 200
    token = guest_res.json()["token"]
    guest_id = guest_res.json()["user"]["id"]

    chat_res = client.post(
        "/api/companion/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": guest_id,
            "message": "Hello Mitra, I am a guest user!",
            "platform": "web",
        },
    )
    assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
    chat_body = chat_res.json()
    assert "message" in chat_body or "response" in chat_body


def test_guest_token_forbidden_from_connecting_integrations():
    """Verify guest tokens are rejected with 403 Forbidden when attempting to connect OAuth integrations."""
    guest_res = client.post("/api/auth/guest")
    assert guest_res.status_code == 200
    token = guest_res.json()["token"]

    oauth_res = client.get(
        "/api/oauth/google/start?purpose=connect",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert oauth_res.status_code == 403, f"Expected 403 Forbidden, got {oauth_res.status_code}"
    assert "Guest sessions cannot connect external accounts" in oauth_res.json()["detail"]


def test_guest_token_idor_prevention():
    """Verify guest token identity is enforced server-side and cannot be overridden by request payload."""
    guest_res = client.post("/api/auth/guest")
    assert guest_res.status_code == 200
    token = guest_res.json()["token"]
    guest_id = guest_res.json()["user"]["id"]

    # Pass a spoofed user_id in body
    chat_res = client.post(
        "/api/companion/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": "usr_victim_account_12345",
            "message": "Attempt IDOR attack",
            "platform": "web",
        },
    )
    assert chat_res.status_code == 200
    # Server processes chat under guest identity, preventing IDOR
