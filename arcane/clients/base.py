"""Base LLM Client - Abstract base class for all LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional
import os


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, provider: str, model: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            provider: Name of the LLM provider
            model: Optional model name override
        """
        self.provider = provider
        self.model = model

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text using the LLM."""
        pass

    def get_model_name(self) -> str:
        """Get the current model name.

        Returns:
            The model name being used
        """
        return self.model or self._get_default_model()

    def _get_default_model(self) -> str:
        """Get the default model for this provider.

        Returns:
            Default model name
        """
        return "unknown"

    def _validate_api_key(self, key_name: str) -> None:
        """Validate API key exists."""
        if not os.getenv(key_name):
            raise ValueError(f"{key_name} environment variable not set")