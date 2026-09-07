import os
import requests
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from app.integrations.oauth.base import BaseOAuthProvider

logger = logging.getLogger(__name__)

class MicrosoftOAuthProvider(BaseOAuthProvider):
    """
    Production-grade Microsoft OAuth 2.0 Identity Platform Provider with PKCE,
    least-privilege Graph scoping, code exchange, user identity retrieval, and token refresh.
    Supports multi-tenant ('common'), work/school ('organizations'), or personal ('consumers') accounts.
    """
    def __init__(self):
        self.userinfo_url = "https://graph.microsoft.com/v1.0/me"

    @property
    def provider_name(self) -> str:
        return "microsoft"

    def _get_client_id(self) -> str:
        return os.getenv("MICROSOFT_CLIENT_ID", "mitra-microsoft-client-id").strip()

    def _get_client_secret(self) -> str:
        return os.getenv("MICROSOFT_CLIENT_SECRET", "dev_secret_microsoft_mitra").strip()

    def _get_tenant_id(self) -> str:
        return os.getenv("MICROSOFT_TENANT_ID", "common").strip()

    def _get_default_redirect_uri(self) -> str:
        return os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/oauth/microsoft/callback").strip()

    @property
    def auth_url(self) -> str:
        tenant = self._get_tenant_id()
        return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"

    @property
    def token_url(self) -> str:
        tenant = self._get_tenant_id()
        return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

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
            if purpose == "login":
                # Least privilege identity scopes for login
                scopes = ["openid", "email", "profile", "offline_access"]
            else:
                # Service connection scopes for Outlook Send and Microsoft Calendar ReadWrite
                scopes = [
                    "openid",
                    "email",
                    "profile",
                    "offline_access",
                    "https://graph.microsoft.com/Mail.Send",
                    "https://graph.microsoft.com/Calendars.ReadWrite"
                ]

        scope_str = " ".join(scopes)

        params = {
            "client_id": client_id,
            "redirect_uri": target_redirect,
            "response_type": "code",
            "scope": scope_str,
            "response_mode": "query",
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
            logger.error(f"Microsoft token exchange failed: HTTP {response.status_code} - {response.text}")
            raise ValueError(f"Microsoft token exchange failed: HTTP {response.status_code}")

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
            logger.error(f"Microsoft Graph userinfo request failed: HTTP {response.status_code}")
            raise ValueError("Failed to retrieve Microsoft user identity.")

        info = response.json()
        sub = info.get("id")
        email = info.get("mail") or info.get("userPrincipalName")

        if not sub or not email:
            raise ValueError("Microsoft Graph user profile missing id or email claims.")

        return {
            "provider_subject": sub,
            "email": email,
            "name": info.get("displayName", email.split("@")[0]),
            "picture": None,
            "email_verified": True
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
            logger.warning(f"Microsoft token refresh failed: HTTP {response.status_code} - {response.text}")
            raise ValueError(f"Refresh failed: {response.text}")

        res_data = response.json()
        return {
            "access_token": res_data.get("access_token"),
            "refresh_token": res_data.get("refresh_token"),
            "expires_in": res_data.get("expires_in"),
            "scope": res_data.get("scope")
        }

    def revoke_token(self, token: str) -> bool:
        # Microsoft Graph does not provide a direct lightweight revocation REST endpoint for delegated tokens.
        return True
