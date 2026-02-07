"""Base interface for AI provider clients.

The clients folder abstracts AI provider APIs behind a common interface.
This lets us swap between Claude, GPT-4, or local models without changing
any generation logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass
class UsageStats:
    """Tracks cumulative token usage across API calls."""

    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    # Breakdown by generation level
    calls_by_level: dict[str, int] = field(default_factory=dict)
    tokens_by_level: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Total tokens used (input + output)."""
        return self.input_tokens + self.output_tokens

    def add(self, input_tokens: int, output_tokens: int, level: str | None = None) -> None:
        """Record usage from an API call."""
        self.api_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

        if level:
            self.calls_by_level[level] = self.calls_by_level.get(level, 0) + 1
            if level not in self.tokens_by_level:
                self.tokens_by_level[level] = {"input": 0, "output": 0}
            self.tokens_by_level[level]["input"] += input_tokens
            self.tokens_by_level[level]["output"] += output_tokens

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.api_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls_by_level = {}
        self.tokens_by_level = {}

    def calculate_cost(self, input_price_per_million: float, output_price_per_million: float) -> float:
        """Calculate cost based on token pricing."""
        input_cost = (self.input_tokens / 1_000_000) * input_price_per_million
        output_cost = (self.output_tokens / 1_000_000) * output_price_per_million
        return input_cost + output_cost


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
        level: str | None = None,
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
            level: Optional generation level for usage tracking
                (e.g., 'milestone', 'epic', 'story', 'task').

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

    @property
    @abstractmethod
    def usage(self) -> UsageStats:
        """Get cumulative usage statistics for this client."""
        pass

    @abstractmethod
    def reset_usage(self) -> None:
        """Reset usage statistics to zero."""
        pass
