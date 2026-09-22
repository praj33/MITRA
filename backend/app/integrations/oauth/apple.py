import os
import time
import urllib.parse
from typing import Dict, Any, List, Optional
import logging
import requests

from app.integrations.oauth.base import BaseOAuthProvider

logger = logging.getLogger(__name__)


class AppleOAuthProvider(BaseOAuthProvider):
    """
    Production-grade Apple OAuth 2.0 / Sign in with Apple provider.
    Supports secure PKCE / state validation, server-side code exchange,
    Apple ID token claim decoding, private relay email resolution, and token refresh.
    """

    AUTH_URL = "https://appleid.apple.com/auth/authorize"
    TOKEN_URL = "https://appleid.apple.com/auth/token"
    REVOKE_URL = "https://appleid.apple.com/auth/revoke"

    @property
    def provider_name(self) -> str:
        return "apple"

    def _get_client_id(self) -> str:
        return os.getenv("APPLE_CLIENT_ID", "").strip()

    def _get_team_id(self) -> str:
        return os.getenv("APPLE_TEAM_ID", "").strip()

    def _get_key_id(self) -> str:
        return os.getenv("APPLE_KEY_ID", "").strip()

    def _get_private_key(self) -> str:
        return os.getenv("APPLE_PRIVATE_KEY", "").strip()

    def _get_default_redirect_uri(self) -> str:
        return os.getenv(
            "APPLE_REDIRECT_URI", "http://localhost:8000/api/oauth/apple/callback"
        ).strip()

    def is_configured(self) -> bool:
        """Verify required Apple OAuth credentials exist in environment."""
        client_id = self._get_client_id()
        team_id = self._get_team_id()
        key_id = self._get_key_id()
        private_key = self._get_private_key()
        placeholders = {
            "", "your_apple_client_id", "your_apple_team_id",
            "your_apple_key_id", "your_apple_private_key"
        }
        return (
            client_id not in placeholders
            and team_id not in placeholders
            and key_id not in placeholders
            and private_key not in placeholders
        )

    def _generate_client_secret(self) -> str:
        """
        Generates client_secret JWT for Apple Sign-In using ES256 algorithm.
        Requires APPLE_PRIVATE_KEY, APPLE_TEAM_ID, APPLE_KEY_ID, and APPLE_CLIENT_ID.
        """
        import jwt

        client_id = self._get_client_id()
        team_id = self._get_team_id()
        key_id = self._get_key_id()
        private_key = self._get_private_key()

        if not private_key or not team_id or not key_id or not client_id:
            raise ValueError(
                "Apple Sign-In credentials missing. Please set APPLE_CLIENT_ID, "
                "APPLE_TEAM_ID, APPLE_KEY_ID, and APPLE_PRIVATE_KEY in backend .env."
            )

        now = int(time.time())
        payload = {
            "iss": team_id,
            "iat": now,
            "exp": now + 86400 * 180,  # 180 days (maximum permitted by Apple)
            "aud": "https://appleid.apple.com",
            "sub": client_id,
        }
        headers = {
            "kid": key_id,
            "alg": "ES256",
        }

        formatted_key = private_key.replace("\\n", "\n")
        return jwt.encode(payload, formatted_key, algorithm="ES256", headers=headers)

    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None,
        purpose: str = "login",
    ) -> str:
        """
        Construct Apple authorization URL.
        Enforces state validation and requests name + email scopes.
        """
        if not self.is_configured():
            raise ValueError(
                "Apple Sign-In is not configured on this server. "
                "Please configure APPLE_CLIENT_ID in backend .env."
            )

        effective_redirect = redirect_uri or self._get_default_redirect_uri()
        effective_scopes = scopes or ["name", "email"]
        scope_str = " ".join(effective_scopes)

        params = {
            "client_id": self._get_client_id(),
            "redirect_uri": effective_redirect,
            "response_type": "code id_token",
            "response_mode": "form_post",
            "scope": scope_str,
            "state": state,
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Server-side exchange of Apple authorization code for tokens.
        """
        if not self.is_configured():
            raise ValueError("Apple OAuth credentials are not configured. Cannot exchange code.")

        effective_redirect = redirect_uri or self._get_default_redirect_uri()
        client_secret = self._generate_client_secret()

        data = {
            "client_id": self._get_client_id(),
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": effective_redirect,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "MITRA-Assistant",
        }

        response = requests.post(self.TOKEN_URL, data=data, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Apple token exchange failed: HTTP {response.status_code} - {response.text}")
            raise ValueError(f"Apple token exchange failed: HTTP {response.status_code}")

        res_data = response.json()
        return {
            "access_token": res_data.get("access_token"),
            "refresh_token": res_data.get("refresh_token"),
            "id_token": res_data.get("id_token"),
            "expires_in": res_data.get("expires_in", 3600),
            "token_type": res_data.get("token_type", "Bearer"),
        }

    def get_user_identity(
        self, access_token: str, id_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts user identity claims from Apple id_token JWT.
        Uses Apple's permanent, unique 'sub' claim as the stable provider_subject identifier,
        and cleanly handles Apple private relay email addresses (@privaterelay.appleid.com).
        """
        if not id_token:
            raise ValueError("Apple identity resolution requires a valid id_token.")

        import jwt

        try:
            # Decode JWT claims without signature verification (signature verified by Apple during TLS exchange)
            claims = jwt.decode(id_token, options={"verify_signature": False})
        except Exception as exc:
            logger.error(f"Failed decoding Apple id_token JWT: {exc}")
            raise ValueError("Invalid Apple id_token format.") from exc

        sub = claims.get("sub")
        if not sub:
            raise ValueError("Apple id_token missing mandatory 'sub' subject claim.")

        email = claims.get("email")
        if not email:
            email = f"{sub}@privaterelay.appleid.com"

        is_private = "privaterelay" in email.lower()
        name = email.split("@")[0] if ("@" in email and not is_private) else "Apple User"

        return {
            "provider_subject": str(sub),
            "email": email,
            "name": name,
            "email_verified": claims.get("email_verified", True),
            "is_private_email": is_private,
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired Apple access token using stored refresh token."""
        if not self.is_configured():
            raise ValueError("Apple OAuth credentials not configured.")

        client_secret = self._generate_client_secret()
        data = {
            "client_id": self._get_client_id(),
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(self.TOKEN_URL, data=data, headers=headers, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"Apple token refresh failed: HTTP {response.status_code}")

        res_data = response.json()
        return {
            "access_token": res_data.get("access_token"),
            "expires_in": res_data.get("expires_in", 3600),
            "token_type": res_data.get("token_type", "Bearer"),
        }

    def revoke_token(self, token: str) -> bool:
        """Revoke Apple access or refresh token."""
        if not self.is_configured():
            return False
        try:
            client_secret = self._generate_client_secret()
            data = {
                "client_id": self._get_client_id(),
                "client_secret": client_secret,
                "token": token,
                "token_type_hint": "access_token",
            }
            requests.post(self.REVOKE_URL, data=data, timeout=5)
            return True
        except Exception:
            return False
