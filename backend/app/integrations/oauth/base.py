from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseOAuthProvider(ABC):
    """
    Abstract base class for production OAuth 2.0 providers.
    Defines unified interface for authorization URL generation, code exchange,
    user identity fetching, and token refreshing.
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None,
        purpose: str = "connect"
    ) -> str:
        """Construct authorization URL for user redirect."""
        pass

    @abstractmethod
    def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchange authorization code server-side for access & refresh tokens."""
        pass

    @abstractmethod
    def get_user_identity(
        self,
        access_token: str,
        id_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch normalized user profile from provider userinfo endpoint."""
        pass

    @abstractmethod
    def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Request new access token using a valid refresh token."""
        pass

    def revoke_token(self, token: str) -> bool:
        """Best effort token revocation."""
        return True
