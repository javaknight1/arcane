"""LLM Client Factory - Factory class for creating LLM clients."""

from typing import Optional, Dict, Tuple
from .base import BaseLLMClient
from .claude import ClaudeLLMClient
from .openai import OpenAILLMClient
from .gemini import GeminiLLMClient


class LLMClientFactory:
    """Factory class for creating LLM clients."""

    # Cache for client instances (by provider+model key)
    _client_cache: Dict[str, BaseLLMClient] = {}

    # Supported providers
    SUPPORTED_PROVIDERS = ['claude', 'openai', 'gemini']

    @classmethod
    def create(cls, provider: str, model: Optional[str] = None) -> BaseLLMClient:
        """Create an LLM client for the specified provider and optional model.

        Args:
            provider: LLM provider name ('claude', 'openai', 'gemini')
            model: Optional specific model name

        Returns:
            Configured LLM client instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()

        if provider == 'claude':
            return ClaudeLLMClient(model=model)
        elif provider == 'openai':
            return OpenAILLMClient(model=model)
        elif provider == 'gemini':
            return GeminiLLMClient(model=model)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported: {cls.SUPPORTED_PROVIDERS}"
            )

    @classmethod
    def create_from_string(cls, model_string: str) -> BaseLLMClient:
        """Create LLM client from model string.

        Args:
            model_string: Format "provider" or "provider/model-name"
                         Examples: "claude", "openai/gpt-4o-mini", "gemini/gemini-1.5-flash"

        Returns:
            Configured LLM client instance

        Raises:
            ValueError: If model_string format is invalid or provider is not supported
        """
        if not model_string:
            raise ValueError("Model string cannot be empty")

        model_string = model_string.lower().strip()

        if '/' in model_string:
            provider, model = model_string.split('/', 1)
            return cls.create(provider, model)
        else:
            return cls.create(model_string)

    @classmethod
    def parse_model_string(cls, model_string: str) -> Tuple[str, Optional[str]]:
        """Parse a model string into provider and model components.

        Args:
            model_string: Format "provider" or "provider/model-name"

        Returns:
            Tuple of (provider, model) where model may be None
        """
        if not model_string:
            return ('claude', None)

        model_string = model_string.lower().strip()

        if '/' in model_string:
            provider, model = model_string.split('/', 1)
            return (provider, model)
        else:
            return (model_string, None)

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
    def create_cached_from_string(cls, model_string: str) -> BaseLLMClient:
        """Create or retrieve a cached LLM client from model string.

        Args:
            model_string: Format "provider" or "provider/model-name"

        Returns:
            BaseLLMClient instance (cached if previously created)
        """
        provider, model = cls.parse_model_string(model_string)
        return cls.create_cached(provider, model)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the client cache."""
        cls._client_cache = {}

    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported providers.

        Returns:
            List of provider names
        """
        return cls.SUPPORTED_PROVIDERS.copy()

    @classmethod
    def is_valid_model_string(cls, model_string: str) -> bool:
        """Check if a model string is valid.

        Args:
            model_string: Format "provider" or "provider/model-name"

        Returns:
            True if valid, False otherwise
        """
        if not model_string:
            return False

        provider, _ = cls.parse_model_string(model_string)
        return provider in cls.SUPPORTED_PROVIDERS