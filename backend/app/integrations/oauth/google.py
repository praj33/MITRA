import os
import requests
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from app.integrations.oauth.base import BaseOAuthProvider

logger = logging.getLogger(__name__)

class GoogleOAuthProvider(BaseOAuthProvider):
    """
    Production-grade Google OAuth 2.0 Provider with PKCE, least-privilege scoping,
    code exchange, user identity retrieval, and token refresh.
    """
    def __init__(self):
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        self.revoke_url = "https://oauth2.googleapis.com/revoke"

    @property
    def provider_name(self) -> str:
        return "google"

    def _get_client_id(self) -> str:
        return os.getenv("GOOGLE_CLIENT_ID", "mitra-google-client-id.apps.googleusercontent.com").strip()

    def _get_client_secret(self) -> str:
        return os.getenv("GOOGLE_CLIENT_SECRET", "dev_secret_google_mitra").strip()

    def _get_default_redirect_uri(self) -> str:
        return os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/oauth/google/callback").strip()

    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None,
        purpose: str = "connect"
    ) -> str:
        client_id = self._get_client_id()
        target_redirect = redirect_uri or self._get_default_redirect_uri()

        if not scopes:
            if purpose in ("login", "signup"):
                # Least privilege identity scopes for login / signup
                scopes = ["openid", "email", "profile"]
            else:
                # Service connection scopes
                scopes = [
                    "openid",
                    "email",
                    "profile",
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/calendar"
                ]

        scope_str = " ".join(scopes)

        params = {
            "client_id": client_id,
            "redirect_uri": target_redirect,
            "response_type": "code",
            "scope": scope_str,
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }

        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        client_id = self._get_client_id()
        client_secret = self._get_client_secret()
        target_redirect = redirect_uri or self._get_default_redirect_uri()

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": target_redirect
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(self.token_url, data=data, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Google token exchange failed: HTTP {response.status_code}")
            raise ValueError(f"Google token exchange failed: HTTP {response.status_code}")

        res_data = response.json()
        return {
            "access_token": res_data.get("access_token"),
            "refresh_token": res_data.get("refresh_token"),
            "expires_in": res_data.get("expires_in"),
            "scope": res_data.get("scope"),
            "token_type": res_data.get("token_type"),
            "id_token": res_data.get("id_token")
        }

    def get_user_identity(
        self,
        access_token: str,
        id_token: Optional[str] = None
    ) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.userinfo_url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Google userinfo request failed: HTTP {response.status_code}")
            raise ValueError("Failed to retrieve Google user identity.")

        info = response.json()
        sub = info.get("sub")
        email = info.get("email")

        if not sub or not email:
            raise ValueError("Google userinfo missing sub or email claims.")

        return {
            "provider_subject": sub,
            "email": email,
            "name": info.get("name", email.split("@")[0]),
            "picture": info.get("picture"),
            "email_verified": info.get("email_verified", False)
        }

    def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        client_id = self._get_client_id()
        client_secret = self._get_client_secret()

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(self.token_url, data=data, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Google token refresh failed: HTTP {response.status_code}")
            raise ValueError(f"Refresh failed: {response.text}")

        res_data = response.json()
        return {
            "access_token": res_data.get("access_token"),
            "expires_in": res_data.get("expires_in"),
            "scope": res_data.get("scope")
        }

    def revoke_token(self, token: str) -> bool:
        try:
            requests.post(self.revoke_url, params={"token": token}, timeout=5)
            return True
        except Exception:
            return False
