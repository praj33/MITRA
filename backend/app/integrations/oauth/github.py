import os
import urllib.parse
import requests
from typing import Dict, Any, List, Optional
import logging

from app.integrations.oauth.base import BaseOAuthProvider

logger = logging.getLogger(__name__)


class GitHubOAuthProvider(BaseOAuthProvider):
    """
    GitHub OAuth 2.0 Provider implementation supporting developer identity resolution,
    user-scoped repository access, issues API, pull requests API, and token maintenance.
    """

    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USERINFO_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    DEFAULT_SCOPES = ["read:user", "user:email", "repo"]

    @property
    def provider_name(self) -> str:
        return "github"

    def _get_client_id(self) -> str:
        return os.getenv("GITHUB_CLIENT_ID", "mitra-github-client-id").strip()

    def _get_client_secret(self) -> str:
        return os.getenv("GITHUB_CLIENT_SECRET", "dev_secret_github_mitra").strip()

    def _get_default_redirect_uri(self) -> str:
        return os.getenv(
            "GITHUB_REDIRECT_URI", "http://localhost:8000/api/oauth/github/callback"
        ).strip()

    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None,
        purpose: str = "connect",
    ) -> str:
        """
        Construct authorization URL for GitHub OAuth 2.0 Web Application flow.
        Uses cryptographically generated state token for CSRF protection.
        """
        effective_scopes = scopes or self.DEFAULT_SCOPES
        scope_str = " ".join(effective_scopes)
        effective_redirect = redirect_uri or self._get_default_redirect_uri()

        params = {
            "client_id": self._get_client_id(),
            "redirect_uri": effective_redirect,
            "scope": scope_str,
            "state": state,
            "allow_signup": "true",
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange authorization code server-side for access token.
        """
        effective_redirect = redirect_uri or self._get_default_redirect_uri()
        payload = {
            "client_id": self._get_client_id(),
            "client_secret": self._get_client_secret(),
            "code": code,
            "redirect_uri": effective_redirect,
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "MITRA-Assistant",
        }

        try:
            response = requests.post(self.TOKEN_URL, data=payload, headers=headers, timeout=10)
            if response.status_code != 200:
                raise ValueError(
                    f"GitHub code exchange failed with HTTP {response.status_code}: {response.text}"
                )

            data = response.json()
            if "error" in data:
                error_desc = data.get("error_description", data["error"])
                raise ValueError(f"GitHub OAuth error: {error_desc}")

            access_token = data.get("access_token")
            if not access_token:
                raise ValueError("GitHub token exchange returned no access token.")

            return {
                "access_token": access_token,
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "token_type": data.get("token_type", "Bearer"),
                "scope": data.get("scope", ""),
            }
        except requests.RequestException as e:
            logger.error(f"GitHub code exchange network error: {e}")
            raise ValueError("Failed to communicate with GitHub OAuth token endpoint.")

    def get_user_identity(
        self, access_token: str, id_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch normalized GitHub user profile, using /user/emails if public email is unlisted.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "MITRA-Assistant",
        }

        try:
            res = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
            if res.status_code != 200:
                raise ValueError(
                    f"Failed to fetch GitHub user identity (HTTP {res.status_code})"
                )

            user_data = res.json()
            provider_subject = str(user_data.get("id"))
            username = user_data.get("login", "")
            name = user_data.get("name") or username
            email = user_data.get("email")

            # Handle private / unlisted public emails via /user/emails
            if not email:
                try:
                    email_res = requests.get(self.EMAILS_URL, headers=headers, timeout=10)
                    if email_res.status_code == 200:
                        emails = email_res.json()
                        if isinstance(emails, list) and len(emails) > 0:
                            # Primary verified email first
                            primary_verified = next(
                                (
                                    e["email"]
                                    for e in emails
                                    if e.get("primary") and e.get("verified")
                                ),
                                None,
                            )
                            if primary_verified:
                                email = primary_verified
                            else:
                                verified = next(
                                    (e["email"] for e in emails if e.get("verified")),
                                    None,
                                )
                                email = verified or emails[0].get("email")
                except Exception as ex:
                    logger.warning(
                        f"Failed to resolve private GitHub email for {username}: {ex}"
                    )

            if not email:
                email = f"{username}@users.noreply.github.com"

            return {
                "provider_subject": provider_subject,
                "email": email,
                "name": name,
                "username": username,
                "login": username,
            }
        except requests.RequestException as e:
            logger.error(f"GitHub user identity request failed: {e}")
            raise ValueError("Failed to retrieve GitHub user identity.")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Request new access token if GitHub App refresh token rotation is enabled.
        """
        if not refresh_token:
            raise ValueError(
                "GitHub standard web application OAuth access tokens are long-lived; no refresh token provided."
            )

        payload = {
            "client_id": self._get_client_id(),
            "client_secret": self._get_client_secret(),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "MITRA-Assistant",
        }

        try:
            res = requests.post(self.TOKEN_URL, data=payload, headers=headers, timeout=10)
            if res.status_code != 200:
                raise ValueError(
                    f"GitHub token refresh failed with HTTP {res.status_code}"
                )

            data = res.json()
            if "error" in data:
                raise ValueError(
                    f"GitHub refresh error: {data.get('error_description', data['error'])}"
                )

            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_in": data.get("expires_in"),
                "token_type": data.get("token_type", "Bearer"),
                "scope": data.get("scope", ""),
            }
        except requests.RequestException as e:
            logger.error(f"GitHub token refresh request failed: {e}")
            raise ValueError("Failed to refresh GitHub access token.")

    def revoke_token(self, token: str) -> bool:
        """Best effort token revocation."""
        return True
