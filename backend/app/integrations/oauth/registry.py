from typing import Dict
from app.integrations.oauth.base import BaseOAuthProvider
from app.integrations.oauth.google import GoogleOAuthProvider
from app.integrations.oauth.microsoft import MicrosoftOAuthProvider
from app.integrations.oauth.apple import AppleOAuthProvider
from app.integrations.oauth.github import GitHubOAuthProvider

class OAuthProviderRegistry:
    """Central registry for managing registered OAuth 2.0 provider implementations."""
    def __init__(self):
        self._providers: Dict[str, BaseOAuthProvider] = {}
        # Register standard providers
        self.register(GoogleOAuthProvider())
        self.register(MicrosoftOAuthProvider())
        self.register(AppleOAuthProvider())
        self.register(GitHubOAuthProvider())

    def register(self, provider: BaseOAuthProvider) -> None:
        self._providers[provider.provider_name.lower()] = provider

    def get(self, provider_name: str) -> BaseOAuthProvider:
        name = provider_name.lower()
        if name not in self._providers:
            raise KeyError(f"Unsupported OAuth provider: {provider_name}")
        return self._providers[name]

oauth_provider_registry = OAuthProviderRegistry()
