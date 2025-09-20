"""LLM Client Factory - Factory class for creating LLM clients."""

from .base import BaseLLMClient
from .claude import ClaudeLLMClient
from .openai import OpenAILLMClient
from .gemini import GeminiLLMClient


class LLMClientFactory:
    """Factory class for creating LLM clients."""

    @staticmethod
    def create(provider: str) -> BaseLLMClient:
        """Create an LLM client for the specified provider."""
        providers = {
            'claude': ClaudeLLMClient,
            'openai': OpenAILLMClient,
            'gemini': GeminiLLMClient
        }

        if provider not in providers:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {list(providers.keys())}")

        return providers[provider]()