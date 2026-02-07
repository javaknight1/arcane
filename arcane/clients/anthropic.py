"""Anthropic Claude client implementation.

Provides the AnthropicClient class that implements BaseAIClient
using the Anthropic SDK with Instructor for structured output.
"""

import anthropic
import instructor
from pydantic import BaseModel

from .base import BaseAIClient, AIClientError, UsageStats


class AnthropicClient(BaseAIClient):
    """Claude client using Anthropic SDK + Instructor for structured output.

    This client wraps the Anthropic API and uses the Instructor library
    to ensure responses conform to Pydantic schemas. It also tracks
    cumulative token usage across all API calls.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize the Anthropic client.

        Args:
            api_key: Anthropic API key for authentication.
            model: The Claude model to use. Defaults to claude-sonnet-4-20250514.
        """
        self._api_key = api_key
        self._model = model
        self._raw_client = anthropic.AsyncAnthropic(api_key=api_key)
        self._client = instructor.from_anthropic(self._raw_client)
        self._usage = UsageStats()

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        level: str | None = None,
    ) -> BaseModel:
        """Generate a structured response from Claude.

        Args:
            system_prompt: The system-level instruction.
            user_prompt: The user-level prompt with context.
            response_model: Pydantic model class for the response.
            max_tokens: Maximum tokens in the response.
            temperature: Creativity level (0.0-1.0).
            level: Optional generation level for usage tracking.

        Returns:
            An instance of response_model with validated data.

        Raises:
            AIClientError: If the API call fails.
        """
        try:
            # Use create_with_completion to get both model and raw response
            response, completion = await self._client.messages.create_with_completion(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                response_model=response_model,
            )

            # Track usage from the completion
            if hasattr(completion, "usage") and completion.usage:
                self._usage.add(
                    input_tokens=completion.usage.input_tokens,
                    output_tokens=completion.usage.output_tokens,
                    level=level,
                )

            return response
        except Exception as e:
            raise AIClientError(f"Anthropic API call failed: {e}") from e

    async def validate_connection(self) -> bool:
        """Test that the client can reach the Anthropic API.

        Returns:
            True if the connection is valid, False otherwise.
        """
        try:
            await self._raw_client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        """Human-readable provider name."""
        return "Anthropic Claude"

    @property
    def model_name(self) -> str:
        """The specific model being used."""
        return self._model

    @property
    def usage(self) -> UsageStats:
        """Get cumulative usage statistics for this client."""
        return self._usage

    def reset_usage(self) -> None:
        """Reset usage statistics to zero."""
        self._usage.reset()
