"""Tests for arcane.clients module."""

import pytest
from pydantic import BaseModel

from arcane.core.clients import (
    BaseAIClient,
    AIClientError,
    AnthropicClient,
    UsageStats,
    create_client,
)


class TestBaseAIClient:
    """Tests for the BaseAIClient abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """BaseAIClient cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseAIClient()

        assert "abstract" in str(exc_info.value).lower()

    def test_ai_client_error_is_exception(self):
        """AIClientError is a proper Exception subclass."""
        error = AIClientError("Test error message")
        assert isinstance(error, Exception)
        assert str(error) == "Test error message"


class TestCreateClient:
    """Tests for the create_client factory function."""

    def test_create_anthropic_client(self):
        """create_client('anthropic') returns AnthropicClient instance."""
        client = create_client("anthropic", api_key="test-key")

        assert isinstance(client, AnthropicClient)
        assert isinstance(client, BaseAIClient)

    def test_create_client_unknown_provider_raises(self):
        """create_client with unknown provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_client("unknown", api_key="test-key")

        assert "Unknown provider" in str(exc_info.value)
        assert "unknown" in str(exc_info.value)

    def test_create_client_passes_kwargs(self):
        """create_client passes kwargs to the client constructor."""
        client = create_client(
            "anthropic",
            api_key="test-key",
            model="claude-opus-4-20250514",
        )

        assert client.model_name == "claude-opus-4-20250514"


class TestAnthropicClient:
    """Tests for the AnthropicClient class."""

    def test_provider_name(self):
        """AnthropicClient.provider_name returns expected value."""
        client = AnthropicClient(api_key="test-key")
        assert client.provider_name == "Anthropic Claude"

    def test_model_name_default(self):
        """AnthropicClient.model_name returns default model."""
        client = AnthropicClient(api_key="test-key")
        assert client.model_name == "claude-sonnet-4-20250514"

    def test_model_name_custom(self):
        """AnthropicClient.model_name returns custom model when specified."""
        client = AnthropicClient(
            api_key="test-key",
            model="claude-opus-4-20250514",
        )
        assert client.model_name == "claude-opus-4-20250514"

    def test_client_has_raw_client(self):
        """AnthropicClient creates internal raw client."""
        client = AnthropicClient(api_key="test-key")
        assert hasattr(client, "_raw_client")
        assert client._raw_client is not None

    def test_client_has_instructor_client(self):
        """AnthropicClient creates instructor-wrapped client."""
        client = AnthropicClient(api_key="test-key")
        assert hasattr(client, "_client")
        assert client._client is not None

    def test_is_base_client_subclass(self):
        """AnthropicClient is a BaseAIClient subclass."""
        client = AnthropicClient(api_key="test-key")
        assert isinstance(client, BaseAIClient)

    def test_has_generate_method(self):
        """AnthropicClient has async generate method."""
        client = AnthropicClient(api_key="test-key")
        assert hasattr(client, "generate")
        assert callable(client.generate)

    def test_has_validate_connection_method(self):
        """AnthropicClient has async validate_connection method."""
        client = AnthropicClient(api_key="test-key")
        assert hasattr(client, "validate_connection")
        assert callable(client.validate_connection)


class TestAIClientError:
    """Tests for AIClientError exception."""

    def test_error_with_message(self):
        """AIClientError stores the error message."""
        error = AIClientError("API request failed")
        assert "API request failed" in str(error)

    def test_error_can_be_raised(self):
        """AIClientError can be raised and caught."""
        with pytest.raises(AIClientError) as exc_info:
            raise AIClientError("Test error")

        assert "Test error" in str(exc_info.value)

    def test_error_preserves_cause(self):
        """AIClientError preserves the original exception cause."""
        original = ValueError("Original error")

        try:
            try:
                raise original
            except ValueError as e:
                raise AIClientError("Wrapped error") from e
        except AIClientError as e:
            assert e.__cause__ is original


class RateLimitError(Exception):
    """Simulated rate limit error for testing."""
    pass


class RateLimitTestClient(BaseAIClient):
    """Mock client with configurable rate limit behavior for testing."""

    def __init__(self, rate_limit_count: int = 0):
        self._call_count = 0
        self._rate_limit_count = rate_limit_count
        self._usage = UsageStats()
        # Use tiny delays for fast tests
        self.rate_limit_initial_delay = 0.01
        self.rate_limit_max_delay = 0.05

    def _is_rate_limit_error(self, error: Exception) -> bool:
        return isinstance(error, RateLimitError)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        level: str | None = None,
    ) -> BaseModel:
        return None

    async def validate_connection(self) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "Test Provider"

    @property
    def model_name(self) -> str:
        return "test-model"

    @property
    def usage(self) -> UsageStats:
        return self._usage

    def reset_usage(self) -> None:
        self._usage.reset()

    async def mock_api_call(self):
        """Simulates an API call that rate limits N times then succeeds."""
        self._call_count += 1
        if self._call_count <= self._rate_limit_count:
            raise RateLimitError("Rate limited")
        return "success"

    async def mock_api_call_always_fails(self):
        """Simulates an API call that always rate limits."""
        self._call_count += 1
        raise RateLimitError("Rate limited")

    async def mock_api_call_other_error(self):
        """Simulates a non-rate-limit error."""
        raise ValueError("Some other error")


class TestRateLimiting:
    """Tests for BaseAIClient rate limiting with exponential backoff."""

    async def test_no_rate_limit_returns_immediately(self):
        """Calls succeed immediately when no rate limit is hit."""
        client = RateLimitTestClient(rate_limit_count=0)
        result = await client._call_with_backoff(client.mock_api_call)
        assert result == "success"
        assert client._call_count == 1

    async def test_retries_on_rate_limit_then_succeeds(self):
        """Retries on rate limit errors and returns when successful."""
        client = RateLimitTestClient(rate_limit_count=2)
        result = await client._call_with_backoff(client.mock_api_call)
        assert result == "success"
        assert client._call_count == 3  # 2 failures + 1 success

    async def test_raises_after_max_retries_exhausted(self):
        """Raises the rate limit error after all retries are exhausted."""
        client = RateLimitTestClient()
        client.rate_limit_max_retries = 2
        with pytest.raises(RateLimitError):
            await client._call_with_backoff(client.mock_api_call_always_fails)
        assert client._call_count == 3  # initial + 2 retries

    async def test_non_rate_limit_error_raises_immediately(self):
        """Non-rate-limit errors are raised without retrying."""
        client = RateLimitTestClient()
        with pytest.raises(ValueError, match="Some other error"):
            await client._call_with_backoff(client.mock_api_call_other_error)

    async def test_disabled_rate_limiting(self):
        """Setting max_retries=0 disables rate limit retries."""
        client = RateLimitTestClient()
        client.rate_limit_max_retries = 0
        with pytest.raises(RateLimitError):
            await client._call_with_backoff(client.mock_api_call_always_fails)
        assert client._call_count == 1  # No retries

    def test_default_rate_limit_settings(self):
        """BaseAIClient has sensible default rate limit settings."""
        client = RateLimitTestClient()
        # Check defaults from BaseAIClient (overridden in __init__ for tests)
        assert BaseAIClient.rate_limit_max_retries == 5
        assert BaseAIClient.rate_limit_initial_delay == 2.0
        assert BaseAIClient.rate_limit_max_delay == 60.0

    def test_is_rate_limit_error_default_returns_false(self):
        """Default _is_rate_limit_error returns False (no rate limiting)."""
        # Use a mock that doesn't override _is_rate_limit_error
        from tests.test_generators.test_base import MockClient
        client = MockClient()
        assert client._is_rate_limit_error(Exception("test")) is False

    def test_anthropic_client_detects_rate_limit(self):
        """AnthropicClient._is_rate_limit_error detects anthropic.RateLimitError."""
        import anthropic as anthropic_sdk
        client = AnthropicClient(api_key="test-key")
        # Create a mock RateLimitError (needs response and body)
        import httpx
        mock_response = httpx.Response(429, request=httpx.Request("POST", "https://api.anthropic.com"))
        error = anthropic_sdk.RateLimitError(response=mock_response, body=None, message="rate limited")
        assert client._is_rate_limit_error(error) is True
        assert client._is_rate_limit_error(ValueError("not rate limit")) is False
