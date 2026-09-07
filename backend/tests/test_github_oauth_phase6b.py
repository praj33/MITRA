import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.core.security import create_access_token
from app.services.oauth_transaction_service import (
    oauth_transaction_service,
    _IN_MEMORY_OAUTH_TRANSACTIONS,
)
from app.services.connected_account_service import (
    connected_account_service,
    _IN_MEMORY_CONNECTED_ACCOUNTS,
)
from app.services.token_refresh_service import token_refresh_service
from app.integrations.oauth.github import GitHubOAuthProvider
from app.executors.github_executor import GitHubExecutor
from app.integrations.oauth.registry import oauth_provider_registry

client = TestClient(app)


@pytest.fixture
def test_user_a():
    return {
        "user_id": "usr_gh_test_a",
        "email": "user_a_gh@mitra.org",
        "name": "User A GH",
    }


@pytest.fixture
def test_user_b():
    return {
        "user_id": "usr_gh_test_b",
        "email": "user_b_gh@mitra.org",
        "name": "User B GH",
    }


@pytest.fixture
def auth_headers_a(test_user_a):
    token = create_access_token(
        {
            "sub": test_user_a["user_id"],
            "user_id": test_user_a["user_id"],
            "email": test_user_a["email"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_b(test_user_b):
    token = create_access_token(
        {
            "sub": test_user_b["user_id"],
            "user_id": test_user_b["user_id"],
            "email": test_user_b["email"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


# 1. Unauthenticated GitHub connection start rejected
def test_unauthenticated_github_connection_start_rejected():
    res = client.get("/api/oauth/github/start?purpose=connect")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


# 2. Authenticated user can start GitHub OAuth
def test_authenticated_user_can_start_github_oauth(auth_headers_a):
    res = client.get("/api/oauth/github/start?purpose=connect", headers=auth_headers_a)
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    assert "github.com/login/oauth/authorize" in data["url"]
    assert "state" in data
    assert data["provider"] == "github"


# 3. Secure state generated
def test_secure_state_generated(auth_headers_a):
    res = client.get("/api/oauth/github/start?purpose=connect", headers=auth_headers_a)
    data = res.json()
    state = data["state"]
    assert len(state) >= 32


# 4. State bound to authenticated user
def test_state_bound_to_authenticated_user(auth_headers_a, test_user_a):
    res = client.get("/api/oauth/github/start?purpose=connect", headers=auth_headers_a)
    state = res.json()["state"]

    tx = _IN_MEMORY_OAUTH_TRANSACTIONS.get(state)
    assert tx is not None
    assert tx["user_id"] == test_user_a["user_id"]
    assert tx["provider"] == "github"


# 5. State expires
def test_state_expires():
    old_state = "expired_state_gh_123456789012345678901234"
    _IN_MEMORY_OAUTH_TRANSACTIONS[old_state] = {
        "state": old_state,
        "provider": "github",
        "user_id": "usr_gh_test_a",
        "code_verifier": "verifier",
        "purpose": "connect",
        "created_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
        "expires_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
        "used_at": None,
    }

    res = client.get(f"/api/oauth/github/callback?code=mock_code&state={old_state}")
    assert res.status_code == 400
    assert (
        "invalid" in res.json()["detail"].lower()
        or "expired" in res.json()["detail"].lower()
    )


# 6. State cannot be reused
def test_state_cannot_be_reused(auth_headers_a):
    res = client.get("/api/oauth/github/start?purpose=connect", headers=auth_headers_a)
    state = res.json()["state"]

    tx1 = oauth_transaction_service.validate_and_consume_transaction(state, "github")
    assert tx1 is not None

    with pytest.raises(HTTPException) as exc_info:
        oauth_transaction_service.validate_and_consume_transaction(state, "github")
    assert exc_info.value.status_code == 400


# 7. Callback rejects invalid state
def test_callback_rejects_invalid_state():
    res = client.get(
        "/api/oauth/github/callback?code=mock_code&state=fake_nonexistent_state_12345"
    )
    assert res.status_code == 400
    assert "invalid" in res.json()["detail"].lower()


# 8. Server-side authorization-code exchange
@patch("requests.post")
@patch("requests.get")
def test_server_side_authorization_code_exchange(
    mock_get, mock_post, auth_headers_a, test_user_a
):
    start_res = client.get(
        "/api/oauth/github/start?purpose=connect", headers=auth_headers_a
    )
    state = start_res.json()["state"]

    # Mock code exchange
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "access_token": "gho_mock_access_token_12345",
        "token_type": "Bearer",
        "scope": "read:user user:email repo",
    }
    mock_post.return_value = mock_post_resp

    # Mock user identity
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = {
        "id": 98765432,
        "login": "octocat_dev",
        "name": "Mona Lisa Octocat",
        "email": "octocat@github.com",
    }
    mock_get.return_value = mock_get_resp

    cb_res = client.get(
        f"/api/oauth/github/callback?code=valid_gh_code&state={state}",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert cb_res.status_code in (302, 307)
    assert "status=success" in cb_res.headers["location"]
    assert "provider=github" in cb_res.headers["location"]

    conn = connected_account_service.get_user_connection(
        test_user_a["user_id"], "github"
    )
    assert conn is not None
    assert conn["email"] == "octocat@github.com"


# 9. GitHub identity resolution
@patch("requests.get")
def test_github_identity_resolution(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 1234567,
        "login": "testdev",
        "name": "Test Developer",
        "email": "dev@test.org",
    }
    mock_get.return_value = mock_resp

    provider = GitHubOAuthProvider()
    identity = provider.get_user_identity("mock_token")
    assert identity["provider_subject"] == "1234567"
    assert identity["username"] == "testdev"
    assert identity["name"] == "Test Developer"
    assert identity["email"] == "dev@test.org"


# 10. Private-email/unavailable-email handling
@patch("requests.get")
def test_private_email_handling(mock_get):
    # First call: /user has email=None
    # Second call: /user/emails returns email list
    resp1 = MagicMock()
    resp1.status_code = 200
    resp1.json.return_value = {
        "id": 55555,
        "login": "privatedev",
        "name": "Private Dev",
        "email": None,
    }

    resp2 = MagicMock()
    resp2.status_code = 200
    resp2.json.return_value = [
        {"email": "unverified@test.org", "primary": False, "verified": False},
        {"email": "primary_verified@test.org", "primary": True, "verified": True},
    ]

    mock_get.side_effect = [resp1, resp2]

    provider = GitHubOAuthProvider()
    identity = provider.get_user_identity("mock_token")
    assert identity["email"] == "primary_verified@test.org"

    # Fallback test if /user/emails also fails or is empty
    resp1_b = MagicMock()
    resp1_b.status_code = 200
    resp1_b.json.return_value = {
        "id": 66666,
        "login": "noemailuser",
        "name": "No Email",
        "email": None,
    }

    resp2_b = MagicMock()
    resp2_b.status_code = 404

    mock_get.side_effect = [resp1_b, resp2_b]
    identity_fallback = provider.get_user_identity("mock_token")
    assert identity_fallback["email"] == "noemailuser@users.noreply.github.com"


# 11. Tokens encrypted at rest
def test_tokens_encrypted_at_rest(test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_sub_123",
        email="dev@github.org",
        access_token="secret_gh_access_token_abc",
        refresh_token="secret_gh_refresh_token_xyz",
    )

    # Directly inspect stored record in memory/DB to verify plaintext token is not present
    key = f"{test_user_a['user_id']}_github"
    record = _IN_MEMORY_CONNECTED_ACCOUNTS.get(key)
    if record:
        assert record.get("encrypted_access_token") != "secret_gh_access_token_abc"
        assert "secret_gh_access_token_abc" not in str(record)

    # Decryption works via service call
    decrypted_token = token_refresh_service.get_valid_access_token(
        test_user_a["user_id"], "github"
    )
    assert decrypted_token == "secret_gh_access_token_abc"


# 12. Connections API does not return tokens
def test_connections_api_does_not_return_tokens(auth_headers_a, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_sub_999",
        email="safe_dev@github.org",
        access_token="super_secret_access_token",
        refresh_token="super_secret_refresh_token",
    )

    res = client.get("/api/connections", headers=auth_headers_a)
    assert res.status_code == 200
    data = res.json()
    assert "connections" in data

    gh_conn = next(c for c in data["connections"] if c["provider"] == "github")
    assert gh_conn["email"] == "safe_dev@github.org"
    assert "access_token" not in gh_conn
    assert "refresh_token" not in gh_conn
    assert "encrypted_access_token" not in gh_conn
    assert "encrypted_refresh_token" not in gh_conn


# 13. GitHub repository API uses connected user's token
@patch("requests.get")
def test_github_repository_api_uses_connected_user_token(mock_get, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_sub_repo",
        email="repo_dev@github.org",
        access_token="gho_valid_repo_token",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "id": 101,
            "name": "MITRA-Core",
            "full_name": "mitra/MITRA-Core",
            "private": True,
            "html_url": "https://github.com/mitra/MITRA-Core",
        }
    ]
    mock_get.return_value = mock_resp

    executor = GitHubExecutor()
    res = executor.list_repositories(test_user_a["user_id"])
    assert res["status"] == "success"
    assert res["count"] == 1
    assert res["repositories"][0]["name"] == "MITRA-Core"

    # Verify headers contained correct token
    mock_get.assert_called()
    called_headers = mock_get.call_args[1]["headers"]
    assert called_headers["Authorization"] == "Bearer gho_valid_repo_token"


# 14. GitHub issue API uses connected user's token
@patch("requests.get")
@patch("requests.post")
def test_github_issue_api_uses_connected_user_token(
    mock_post, mock_get, test_user_a
):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_sub_issue",
        email="issue_dev@github.org",
        access_token="gho_valid_issue_token",
    )

    # Test list issues
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = [
        {"number": 1, "title": "OAuth Bug", "state": "open"}
    ]
    mock_get.return_value = mock_get_resp

    executor = GitHubExecutor()
    list_res = executor.list_issues(test_user_a["user_id"], "mitra", "backend")
    assert list_res["status"] == "success"
    assert list_res["count"] == 1

    # Test create issue
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 201
    mock_post_resp.json.return_value = {
        "number": 42,
        "title": "New Security Audit Issue",
        "html_url": "https://github.com/mitra/backend/issues/42",
    }
    mock_post.return_value = mock_post_resp

    create_res = executor.create_issue(
        test_user_a["user_id"],
        "mitra",
        "backend",
        "New Security Audit Issue",
        "Body content",
    )
    assert create_res["status"] == "success"
    assert create_res["issue_number"] == 42
    post_headers = mock_post.call_args[1]["headers"]
    assert post_headers["Authorization"] == "Bearer gho_valid_issue_token"


# 15. GitHub pull-request API uses connected user's token
@patch("requests.get")
def test_github_pull_request_api_uses_connected_user_token(mock_get, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_sub_pr",
        email="pr_dev@github.org",
        access_token="gho_valid_pr_token",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "number": 10,
            "title": "Phase 6B GitHub Integration PR",
            "state": "open",
            "head": {"ref": "feature/mitra-production-foundation"},
            "base": {"ref": "main"},
        }
    ]
    mock_get.return_value = mock_resp

    executor = GitHubExecutor()
    pr_res = executor.list_pull_requests(test_user_a["user_id"], "mitra", "backend")
    assert pr_res["status"] == "success"
    assert pr_res["count"] == 1
    assert pr_res["pull_requests"][0]["number"] == 10

    get_headers = mock_get.call_args[1]["headers"]
    assert get_headers["Authorization"] == "Bearer gho_valid_pr_token"


# 16. Cross-user access blocked
def test_cross_user_access_blocked(test_user_a, test_user_b):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_sub_a",
        email="usera@github.org",
        access_token="token_user_a",
    )

    executor = GitHubExecutor()
    res_b = executor.list_repositories(user_id=test_user_b["user_id"])
    assert res_b["status"] == "failed"
    assert "No active GitHub connection" in res_b["error"]


# 17. Client-supplied user_id cannot override JWT identity
def test_client_supplied_user_id_cannot_override_jwt_identity(
    auth_headers_a, test_user_a, test_user_b
):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_a",
        email="usera_jwt@github.org",
        access_token="token_a",
    )
    connected_account_service.create_connection(
        user_id=test_user_b["user_id"],
        provider="github",
        provider_account_id="gh_b",
        email="userb_jwt@github.org",
        access_token="token_b",
    )

    # Attempt IDOR override via query param
    res = client.get(
        f"/api/connections?user_id={test_user_b['user_id']}", headers=auth_headers_a
    )
    assert res.status_code == 200
    data = res.json()
    gh_conn = next(c for c in data["connections"] if c["provider"] == "github")
    # Must return User A's connection, ignoring query parameter
    assert gh_conn["email"] == "usera_jwt@github.org"


# 18. Disconnect safely removes GitHub connection
def test_disconnect_safely_removes_github_connection(auth_headers_a, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_rem",
        email="rem_dev@github.org",
        access_token="token_to_remove",
    )

    assert (
        connected_account_service.get_user_connection(test_user_a["user_id"], "github")
        is not None
    )

    res = client.delete("/api/connections/github", headers=auth_headers_a)
    assert res.status_code == 200

    assert (
        connected_account_service.get_user_connection(test_user_a["user_id"], "github")
        is None
    )


# 19. GitHub API errors handled without leaking secrets
@patch("requests.get")
def test_github_api_errors_handled_without_leaking_secrets(mock_get, test_user_a):
    connected_account_service.create_connection(
        user_id=test_user_a["user_id"],
        provider="github",
        provider_account_id="gh_err",
        email="err_dev@github.org",
        access_token="gho_secret_leaked_never",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Bad credentials"
    mock_get.return_value = mock_resp

    executor = GitHubExecutor()
    res = executor.list_repositories(test_user_a["user_id"])
    assert res["status"] == "failed"
    assert "gho_secret_leaked_never" not in str(res)


# 20. Existing Google/Microsoft connection behavior remains intact
def test_existing_google_microsoft_connection_behavior_remains_intact(
    auth_headers_a, test_user_a
):
    google_provider = oauth_provider_registry.get("google")
    microsoft_provider = oauth_provider_registry.get("microsoft")
    github_provider = oauth_provider_registry.get("github")

    assert google_provider.provider_name == "google"
    assert microsoft_provider.provider_name == "microsoft"
    assert github_provider.provider_name == "github"

    # Verify Google start endpoint
    res_g = client.get("/api/oauth/google/start?purpose=connect", headers=auth_headers_a)
    assert res_g.status_code == 200
    assert "accounts.google.com" in res_g.json()["url"]

    # Verify Microsoft start endpoint
    res_m = client.get(
        "/api/oauth/microsoft/start?purpose=connect", headers=auth_headers_a
    )
    assert res_m.status_code == 200
    assert "login.microsoftonline.com" in res_m.json()["url"]

    # Verify GitHub start endpoint
    res_gh = client.get(
        "/api/oauth/github/start?purpose=connect", headers=auth_headers_a
    )
    assert res_gh.status_code == 200
    assert "github.com/login/oauth/authorize" in res_gh.json()["url"]
