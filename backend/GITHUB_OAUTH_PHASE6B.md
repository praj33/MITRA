# MITRA Phase 6B — GitHub OAuth & Developer Connections Architecture

## 1. Overview & Architecture

Phase 6B introduces production-grade **GitHub Developer Account Connections** to MITRA while fully adhering to MITRA's provider-independent OAuth 2.0 architecture and core security guarantees.

GitHub accounts allow MITRA to perform user-scoped operations:
- **Repositories**: List accessible repositories and retrieve repository metadata.
- **Issues**: List repository issues, view details, and create new issues on behalf of the authenticated user.
- **Pull Requests**: List repository pull requests and retrieve PR details.

---

## 2. Environment Variables & Callback Setup

Placeholders added to `backend/.env.example`:

```env
##############################
# OAUTH 2.0 CONFIGURATION (GITHUB)
##############################
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
# Dev Redirect URI: http://localhost:8000/api/oauth/github/callback
# Prod Redirect URI: https://yourdomain.com/api/oauth/github/callback
GITHUB_REDIRECT_URI=http://localhost:8000/api/oauth/github/callback
```

### GitHub OAuth App Setup Instructions
1. Navigate to **GitHub Settings -> Developer settings -> OAuth Apps**.
2. Click **New OAuth App**.
3. Set **Application Name**: `MITRA Assistant`.
4. Set **Homepage URL**: `http://localhost:3000` (or production URL).
5. Set **Authorization callback URL**: `http://localhost:8000/api/oauth/github/callback` (or production domain).
6. Save and copy `Client ID` and generate a `Client Secret`.

---

## 3. Scopes & Least Privilege Design

Selected Scopes:
- `read:user`: Read user profile data (ID, username, display name).
- `user:email`: Access user's primary/verified email address (including private emails via `/user/emails`).
- `repo`: Access public and private repositories, issues, and pull requests for connected developer workflow capabilities.

*Rationale for Scopes:*
- `repo` scope provides access to private repositories, issue creation, and pull request inspection necessary for developer assistant actions.
- Administrative, organizational management, SSH key management, workflow administration, and repository deletion permissions are **strictly excluded**.

---

## 4. Identity Resolution Flow

When exchanging code at callback:
1. `GET https://api.github.com/user` retrieves `id`, `login`, `name`, and public `email`.
2. If `email` is private (`None`), MITRA issues an authenticated query to `GET https://api.github.com/user/emails`.
3. Selects primary verified email, falling back to any verified email, and finally `username@users.noreply.github.com`.
4. Normalizes identity into `{provider_subject, username, name, email}`.

---

## 5. Token Lifecycle & Storage

- Tokens are stored encrypted at rest via `ConnectedAccountService` using AES-256 (Fernet symmetric encryption).
- Token sanitization (`_sanitize_record(include_tokens=False)`) guarantees raw or encrypted tokens are never returned in public REST endpoints or React state.
- Standard GitHub OAuth web app access tokens do not expire by default. When token refresh rotation is active or token expiry occurs, `TokenRefreshService` maintains connection state or marks the account as `needs_reauthorization` on failure.

---

## 6. GitHub Capabilities & Executor

`GitHubExecutor` handles developer capabilities:
- `list_repositories(user_id, visibility, sort, max_results)`
- `get_repository(user_id, owner, repo)`
- `list_issues(user_id, owner, repo, state, max_results)`
- `get_issue(user_id, owner, repo, issue_number)`
- `create_issue(user_id, owner, repo, title, body, labels)`
- `list_pull_requests(user_id, owner, repo, state, max_results)`
- `get_pull_request(user_id, owner, repo, pull_number)`

All executor methods enforce user scoping via `token_refresh_service.get_valid_access_token(user_id, "github")`.

---

## 7. Security Model & IDOR Prevention

- Connection start requires valid JWT Bearer header.
- Guest sessions are explicitly blocked with `403 Forbidden`.
- State tokens are cryptographically generated (32+ chars), stored in `OAuthTransactionService`, single-use, and bound to the authenticated user.
- Query parameters (e.g. `?user_id=attacker`) are ignored in favor of verified JWT identity.
- Disconnect endpoint (`DELETE /api/connections/github`) checks ownership and revokes tokens.

---

## 8. Limitations & Future Roadmap

- **Write Operations Scoped**: Only issue creation is allowed. High-risk write operations (PR merging, code push, repo deletion, workflow trigger) are deferred to explicit future phases with step-up approval gates.
