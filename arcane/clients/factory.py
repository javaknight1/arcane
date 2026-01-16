"""LLM Client Factory - Factory class for creating LLM clients."""

from typing import Optional, Dict
from .base import BaseLLMClient
from .claude import ClaudeLLMClient
from .openai import OpenAILLMClient
from .gemini import GeminiLLMClient


class LLMClientFactory:
    """Factory class for creating LLM clients."""

    # Cache for client instances (by provider+model key)
    _client_cache: Dict[str, BaseLLMClient] = {}

    @staticmethod
    def create(provider: str, model: Optional[str] = None) -> BaseLLMClient:
        """Create an LLM client for the specified provider.

        Args:
            provider: LLM provider name ('claude', 'openai', 'gemini')
            model: Optional model name override

        Returns:
            BaseLLMClient instance
        """
        providers = {
            'claude': ClaudeLLMClient,
            'openai': OpenAILLMClient,
            'gemini': GeminiLLMClient
        }

        if provider not in providers:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {list(providers.keys())}")

        return providers[provider](model=model)

    @classmethod
    def create_cached(cls, provider: str, model: Optional[str] = None) -> BaseLLMClient:
        """Create or retrieve a cached LLM client.

        This method caches clients by provider+model combination to avoid
        creating multiple client instances for the same configuration.

        Args:
            provider: LLM provider name
            model: Optional model name override

        Returns:
            BaseLLMClient instance (cached if previously created)
        """
        cache_key = f"{provider}:{model or 'default'}"

        if cache_key not in cls._client_cache:
            cls._client_cache[cache_key] = cls.create(provider, model)

        return cls._client_cache[cache_key]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the client cache."""
        cls._client_cache = {}

    @staticmethod
    def get_supported_providers() -> list:
        """Get list of supported providers.

        Returns:
            List of provider names
        """
        return ['claude', 'openai', 'gemini']