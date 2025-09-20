"""Base LLM Client - Abstract base class for all LLM providers."""

from abc import ABC, abstractmethod
import os


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, provider: str):
        self.provider = provider

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text using the LLM."""
        pass

    def _validate_api_key(self, key_name: str) -> None:
        """Validate API key exists."""
        if not os.getenv(key_name):
            raise ValueError(f"{key_name} environment variable not set")