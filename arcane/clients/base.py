"""Base interface for AI provider clients.

The clients folder abstracts AI provider APIs behind a common interface.
This lets us swap between Claude, GPT-4, or local models without changing
any generation logic.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class AIClientError(Exception):
    """Raised when an AI client call fails.

    This exception wraps any provider-specific errors (API errors,
    network issues, validation failures) into a common error type.
    """

    pass


class BaseAIClient(ABC):
    """Abstract interface for AI provider clients.

    All AI clients must implement this interface. The generators
    only interact with this interface, never with provider SDKs directly.
    """

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> BaseModel:
        """Generate a structured response from the AI model.

        Args:
            system_prompt: The system-level instruction that sets the
                AI's behavior and role.
            user_prompt: The user-level prompt with context and the
                specific request.
            response_model: Pydantic model class the response must
                conform to. The AI will return structured data matching
                this schema.
            max_tokens: Maximum tokens in the response. Defaults to 4096.
            temperature: Creativity level (0.0 = deterministic,
                1.0 = creative). Defaults to 0.7.

        Returns:
            An instance of response_model with validated data.

        Raises:
            AIClientError: If the API call fails after retries.
            ValidationError: If the response doesn't match the schema.
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Test that the client can reach the API.

        Sends a minimal request to verify API connectivity and
        authentication.

        Returns:
            True if the connection is valid, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of the AI provider.

        Examples: 'Anthropic Claude', 'OpenAI GPT'
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The specific model being used.

        Examples: 'claude-sonnet-4-20250514', 'gpt-4o'
        """
        pass
