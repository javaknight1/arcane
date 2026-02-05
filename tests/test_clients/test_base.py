"""Tests for arcane.clients module."""

import pytest

from arcane.clients import (
    BaseAIClient,
    AIClientError,
    AnthropicClient,
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
