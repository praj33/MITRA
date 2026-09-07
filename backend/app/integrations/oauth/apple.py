from typing import Dict, Any, List, Optional
from app.integrations.oauth.base import BaseOAuthProvider

class AppleOAuthProvider(BaseOAuthProvider):
    @property
    def provider_name(self) -> str:
        return "apple"

    def get_authorization_url(self, state: str, code_challenge: Optional[str] = None, scopes: Optional[List[str]] = None, redirect_uri: Optional[str] = None, purpose: str = "connect") -> str:
        raise NotImplementedError("Apple OAuth provider is registered for Phase 5.")

    def exchange_code(self, code: str, code_verifier: Optional[str] = None, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("Apple OAuth provider is registered for Phase 5.")

    def get_user_identity(self, access_token: str, id_token: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("Apple OAuth provider is registered for Phase 5.")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        raise NotImplementedError("Apple OAuth provider is registered for Phase 5.")
