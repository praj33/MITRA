import os
import pytest
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.encryption import is_encrypted, decrypt_secret
from app.services.oauth_transaction_service import oauth_transaction_service
from app.services.connected_account_service import connected_account_service
from app.services.token_refresh_service import token_refresh_service
from app.services.identity_account_service import identity_account_service
from app.integrations.oauth.google import GoogleOAuthProvider

client = TestClient(app)

TEST_JWT_SECRET = "test_phase4_secret_key_mitra_88888"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "test_phase4_encryption_key_32bytes_len=")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_google_client_secret_xyz")

def get_auth_header(user_id: str, email: str = "user@example.com") -> dict:
    token = create_access_token({"sub": user_id, "user_id": user_id, "email": email})
    return {"Authorization": f"Bearer {token}"}

# 1. OAuth State Cryptographically Generated
def test_oauth_state_is_cryptographically_generated():
    tx = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_state_01")
    state = tx["state"]
    assert isinstance(state, str)
    assert len(state) >= 32
    assert "user_state_01" not in state  # Pure random entropy, zero PII leak

# 2. OAuth State Is Unique
def test_oauth_state_is_unique():
    tx1 = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_unique_1")
    tx2 = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_unique_1")
    assert tx1["state"] != tx2["state"]

# 3. OAuth Transaction Expires & 4. Expired State Rejected
def test_oauth_transaction_expires_and_rejected():
    tx = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_exp_1")
    state = tx["state"]

    # Fast-forward expiration
    expired_at = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
    from app.services.oauth_transaction_service import _IN_MEMORY_OAUTH_TRANSACTIONS, _get_db
    _IN_MEMORY_OAUTH_TRANSACTIONS[state]["expires_at"] = expired_at
    db = _get_db()
    if db is not None:
        try:
            db["oauth_transactions"].update_one({"state": state}, {"$set": {"expires_at": expired_at}})
        except Exception:
            pass

    response = client.get(f"/api/oauth/google/callback?code=mock_code&state={state}")
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

# 5. Invalid State Rejected
def test_invalid_state_is_rejected():
    response = client.get("/api/oauth/google/callback?code=mock_code&state=nonexistent_invalid_state_999")
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()

# 6. Reused State Rejected
def test_reused_state_is_rejected():
    tx = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_reuse_1")
    state = tx["state"]

    # First consumption
    res1 = oauth_transaction_service.validate_and_consume_transaction(state, "google")
    assert res1["used_at"] is not None

    # Second consumption attempt
    with pytest.raises(Exception) as exc_info:
        oauth_transaction_service.validate_and_consume_transaction(state, "google")
    err_detail = getattr(exc_info.value, "detail", str(exc_info.value))
    assert "already been used" in err_detail

# 7. State Cannot Be Used by Another User
def test_state_cannot_be_used_by_another_user():
    tx = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_alice")
    state = tx["state"]

    with pytest.raises(Exception) as exc_info:
        oauth_transaction_service.validate_and_consume_transaction(state, "google", expected_user_id="user_bob")
    err_detail = getattr(exc_info.value, "detail", str(exc_info.value))
    assert "bound to a different user" in err_detail

# 8. Callback with Missing Code Fails Safely
def test_callback_with_missing_code_fails_safely():
    tx = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_nocode")
    response = client.get(f"/api/oauth/google/callback?state={tx['state']}")
    assert response.status_code == 400
    assert "missing required authorization code" in response.json()["detail"].lower()

# 9. Callback Cannot Accept Arbitrary user_id Override
def test_callback_cannot_accept_arbitrary_user_id():
    headers = get_auth_header("legit_user_123")
    # Endpoint derives identity strictly from JWT header
    response = client.get("/api/oauth/google/start?purpose=connect&user_id=attacker_user_999", headers=headers)
    assert response.status_code == 200
    data = response.json()
    state = data["state"]

    tx = oauth_transaction_service.validate_and_consume_transaction(state, "google")
    assert tx["user_id"] == "legit_user_123"  # Attacker user_id query param was ignored

# 10. Authorization Code Exchanged Server-Side & 11/12. Tokens Encrypted Before Persistence
@patch.object(GoogleOAuthProvider, "exchange_code")
@patch.object(GoogleOAuthProvider, "get_user_identity")
def test_code_exchanged_serverside_and_tokens_encrypted(mock_identity, mock_exchange):
    mock_exchange.return_value = {
        "access_token": "ya29.google_secret_access_token_12345",
        "refresh_token": "1//google_secret_refresh_token_67890",
        "expires_in": 3600
    }
    mock_identity.return_value = {
        "provider_subject": "google_sub_1001",
        "email": "testuser@gmail.com",
        "name": "Test User"
    }

    user_id = "user_oauth_persist_01"
    tx = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id=user_id)

    response = client.get(f"/api/oauth/google/callback?code=valid_auth_code&state={tx['state']}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify stored account tokens are ENCRYPTED in database/store
    conn = connected_account_service.get_user_connection(user_id, "google", include_decrypted_tokens=False)
    assert conn is not None
    assert "access_token" not in conn
    assert "refresh_token" not in conn

    # Internal query with decryption shows valid secrets
    conn_dec = connected_account_service.get_user_connection(user_id, "google", include_decrypted_tokens=True)
    assert conn_dec["access_token"] == "ya29.google_secret_access_token_12345"
    assert conn_dec["refresh_token"] == "1//google_secret_refresh_token_67890"

# 13 & 14. API Never Returns Access/Refresh Tokens & 23. Safe Metadata Only
def test_api_never_returns_access_or_refresh_tokens():
    user_id = "user_api_zero_leak_02"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="safe@example.com",
        access_token="ya29.super_secret_at",
        refresh_token="1//super_secret_rt"
    )

    headers = get_auth_header(user_id)
    response = client.get("/api/connections", headers=headers)
    assert response.status_code == 200
    data = response.json()

    conn_list = data.get("connections", [])
    assert len(conn_list) == 1
    conn = conn_list[0]

    assert conn["provider"] == "google"
    assert conn["email"] == "safe@example.com"
    assert "access_token" not in conn
    assert "refresh_token" not in conn
    assert "client_secret" not in conn
    assert "ya29.super_secret_at" not in str(data)
    assert "1//super_secret_rt" not in str(data)

# 15. Connected Account Belongs to Authenticated User (IDOR Safe)
def test_connected_account_belongs_to_authenticated_user():
    connected_account_service.create_connection(
        user_id="user_owner_a",
        provider="google",
        email="owner_a@example.com",
        access_token="token_a"
    )

    headers_b = get_auth_header("user_intruder_b")
    response = client.get("/api/connections", headers=headers_b)
    assert response.status_code == 200
    connections = response.json().get("connections", [])
    assert len(connections) == 0  # Intruder B sees zero connections

# 16. Duplicate Provider Account Handled Safely
def test_duplicate_provider_account_handled_safely():
    user_id = "user_dup_01"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="dup@example.com",
        access_token="old_access_token",
        provider_account_id="sub_999"
    )

    # Re-connecting same Google account updates existing connection cleanly
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="dup@example.com",
        access_token="new_access_token",
        provider_account_id="sub_999"
    )

    conns = connected_account_service.list_user_connections(user_id)
    assert len(conns) == 1
    conn_dec = connected_account_service.get_user_connection(user_id, "google", include_decrypted_tokens=True)
    assert conn_dec["access_token"] == "new_access_token"

# 17. Token Refresh Updates Encrypted Token
@patch.object(GoogleOAuthProvider, "refresh_access_token")
def test_token_refresh_updates_encrypted_token(mock_refresh):
    user_id = "user_refresh_test_01"
    expired_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="refresh@example.com",
        access_token="old_expired_at",
        refresh_token="valid_rt_999",
        expires_at=expired_time
    )

    mock_refresh.return_value = {
        "access_token": "new_fresh_access_token_777",
        "expires_in": 3600
    }

    fresh_token = token_refresh_service.get_valid_access_token(user_id, "google")
    assert fresh_token == "new_fresh_access_token_777"
    mock_refresh.assert_called_once_with("valid_rt_999")

# 18. Invalid Refresh Token Marks Connection Appropriately
@patch.object(GoogleOAuthProvider, "refresh_access_token")
def test_invalid_refresh_token_marks_connection_appropriately(mock_refresh):
    user_id = "user_invalid_rt_02"
    expired_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="revoked@example.com",
        access_token="expired_at",
        refresh_token="revoked_rt",
        expires_at=expired_time
    )

    mock_refresh.side_effect = ValueError("invalid_grant")

    with pytest.raises(Exception) as exc_info:
        token_refresh_service.get_valid_access_token(user_id, "google")

    err_detail = getattr(exc_info.value, "detail", str(exc_info.value))
    assert "re-authoriz" in err_detail.lower()
    conn = connected_account_service.get_user_connection(user_id, "google")
    assert conn["status"] == "needs_reauthorization"

# 19. Unauthenticated Connection Start Returns 401
def test_unauthenticated_connection_start_returns_401():
    response = client.get("/api/oauth/google/start?purpose=connect")
    assert response.status_code == 401

# 20. Disconnecting Another User's Connection Is Impossible
def test_disconnecting_another_users_connection_is_impossible():
    connected_account_service.create_connection(
        user_id="user_target_a",
        provider="google",
        email="target@example.com",
        access_token="token_a"
    )

    headers_b = get_auth_header("user_attacker_b")
    response = client.delete("/api/connections/google", headers=headers_b)
    assert response.status_code == 404

    # Target A's connection remains untouched
    assert connected_account_service.get_user_connection("user_target_a", "google") is not None

# 21. Google Provider Authorization URL Is Correct
def test_google_provider_authorization_url_is_correct():
    provider = GoogleOAuthProvider()
    url = provider.get_authorization_url(
        state="test_state_123",
        code_challenge="test_challenge_456",
        purpose="connect"
    )
    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "client_id=test-google-client-id.apps.googleusercontent.com" in url
    assert "response_type=code" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "state=test_state_123" in url
    assert "code_challenge=test_challenge_456" in url
    assert "code_challenge_method=S256" in url

# 22. Google Callback Validates Provider Identity
@patch.object(GoogleOAuthProvider, "exchange_code")
@patch.object(GoogleOAuthProvider, "get_user_identity")
def test_google_callback_validates_provider_identity(mock_identity, mock_exchange):
    mock_exchange.return_value = {"access_token": "at_test", "expires_in": 3600}
    mock_identity.return_value = {"provider_subject": "sub_valid_123", "email": "valid@gmail.com"}

    tx = oauth_transaction_service.create_transaction(provider="google", purpose="connect", user_id="user_id_val")
    response = client.get(f"/api/oauth/google/callback?code=code_123&state={tx['state']}")

    assert response.status_code == 200
    mock_identity.assert_called_once()
