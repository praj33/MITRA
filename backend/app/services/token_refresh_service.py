import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.services.connected_account_service import connected_account_service
from app.integrations.oauth.registry import oauth_provider_registry

logger = logging.getLogger(__name__)

class TokenRefreshService:
    """
    Transparently refreshes expired OAuth access tokens using stored encrypted refresh tokens.
    Handles grant revocation, expiration, and status updates cleanly.
    """
    def get_valid_access_token(self, user_id: str, provider: str) -> str:
        if not user_id or not provider:
            raise HTTPException(status_code=400, detail="user_id and provider are required.")

        conn = connected_account_service.get_user_connection(user_id, provider, include_decrypted_tokens=True)
        if not conn or conn.get("status") not in ("connected", "active"):
            raise HTTPException(status_code=401, detail=f"No connected {provider} account found for user.")

        access_token = conn.get("access_token")
        refresh_token = conn.get("refresh_token")
        expires_at_str = conn.get("expires_at")

        is_expired = False
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                # Refresh if expired or expiring within 60 seconds
                if datetime.utcnow() >= (expires_at - timedelta(seconds=60)):
                    is_expired = True
            except Exception:
                pass

        if not access_token:
            is_expired = True

        if not is_expired and access_token:
            connected_account_service.update_last_used_at(user_id, provider)
            return access_token

        # Attempt token refresh
        if not refresh_token:
            connected_account_service.mark_status(user_id, provider, "needs_reauthorization")
            raise HTTPException(
                status_code=401,
                detail=f"{provider} connection access token has expired and no refresh token is available. Please reconnect."
            )

        try:
            provider_inst = oauth_provider_registry.get(provider)
            res = provider_inst.refresh_access_token(refresh_token)
            new_access_token = res.get("access_token")
            expires_in = res.get("expires_in", 3600)

            if not new_access_token:
                raise ValueError("Provider refresh response did not return an access token.")

            new_expires_at = (datetime.utcnow() + timedelta(seconds=int(expires_in))).isoformat()
            new_refresh_token = res.get("refresh_token")

            connected_account_service.update_tokens(
                user_id=user_id,
                provider=provider,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_at=new_expires_at
            )
            connected_account_service.mark_status(user_id, provider, "connected")

            return new_access_token
        except Exception as exc:
            logger.warning(f"Token refresh failed for user '{user_id}' provider '{provider}': {exc}")
            connected_account_service.mark_status(user_id, provider, "needs_reauthorization")
            raise HTTPException(
                status_code=401,
                detail=f"{provider} authentication expired. Please re-authorize your account."
            )

token_refresh_service = TokenRefreshService()
