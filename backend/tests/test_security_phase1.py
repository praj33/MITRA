import os
import asyncio
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import (
    create_access_token,
    verify_token_string,
    get_jwt_secret,
)
from app.core.auth_dependencies import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


def test_missing_jwt_secret_in_production(monkeypatch):
    """Verify system fails closed when JWT_SECRET_KEY is missing in production environment."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        get_jwt_secret()

    assert "JWT_SECRET_KEY environment variable is required in production mode" in str(exc_info.value)


def test_valid_jwt_creation_and_verification(monkeypatch):
    """Verify valid JWT creation and decoding extracts correct user claims."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_mitra_12345")

    token = create_access_token({"user_id": "usr_test_001", "email": "test@mitra.ai", "name": "Test User"})
    token_data = verify_token_string(token)

    assert token_data.user_id == "usr_test_001"
    assert token_data.email == "test@mitra.ai"
    assert token_data.name == "Test User"


def test_invalid_jwt_rejection(monkeypatch):
    """Verify invalid JWT string raises 401 HTTPException."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_mitra_12345")

    with pytest.raises(HTTPException) as exc_info:
        verify_token_string("invalid.token.signature")

    assert exc_info.value.status_code == 401


def test_expired_jwt_rejection(monkeypatch):
    """Verify expired JWT token raises 401 HTTPException."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_mitra_12345")

    expired_token = create_access_token(
        {"user_id": "usr_expired_001"},
        expires_delta=timedelta(seconds=-10)
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token_string(expired_token)

    assert exc_info.value.status_code == 401


def test_get_current_user_dependency_valid(monkeypatch):
    """Verify get_current_user dependency extracts valid user from Bearer header."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_mitra_12345")
    token = create_access_token({"user_id": "usr_valid_002", "email": "valid@mitra.ai"})

    credentials = MagicMock()
    credentials.credentials = token

    user = asyncio.run(get_current_user(request=None, credentials=credentials))
    assert user["user_id"] == "usr_valid_002"
    assert user["id"] == "usr_valid_002"


def test_get_current_user_dependency_missing(monkeypatch):
    """Verify get_current_user dependency raises 401 when token is missing."""
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(request=None, credentials=None))

    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail


def test_protected_integrations_endpoint_unauthenticated(client):
    """Verify GET /api/integrations rejects requests lacking Authorization header with 401."""
    response = client.get("/api/integrations")
    assert response.status_code == 401


def test_protected_integrations_endpoint_idor_prevention(client, monkeypatch):
    """
    Verify GET /api/integrations derives identity from JWT claim,
    ignoring malicious client-supplied user_id query parameters.
    """
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_mitra_12345")
    legitimate_token = create_access_token({"user_id": "legitimate_user_123"})

    # Attacker tries to query another user's integrations via query string
    response = client.get(
        "/api/integrations?user_id=victim_user_999",
        headers={"Authorization": f"Bearer {legitimate_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Response MUST be scoped to the authenticated user from JWT (legitimate_user_123)
    assert data["user_id"] == "legitimate_user_123"
    assert data["user_id"] != "victim_user_999"
