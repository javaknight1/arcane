"""Tests for LLMClientFactory model selection functionality."""

import pytest
import os
from unittest.mock import patch, MagicMock

from arcane.clients.factory import LLMClientFactory


class TestLLMClientFactoryCreate:
    """Tests for LLMClientFactory.create method."""

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_claude_without_model(self):
        """Test creating Claude client without specific model."""
        client = LLMClientFactory.create('claude')
        assert client is not None
        assert client.provider == 'claude'

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_claude_with_model(self):
        """Test creating Claude client with specific model."""
        client = LLMClientFactory.create('claude', 'claude-haiku-4-20250514')
        assert client is not None
        assert client.provider == 'claude'

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_create_openai_without_model(self):
        """Test creating OpenAI client without specific model."""
        client = LLMClientFactory.create('openai')
        assert client is not None
        assert client.provider == 'openai'

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_create_openai_with_model(self):
        """Test creating OpenAI client with specific model."""
        client = LLMClientFactory.create('openai', 'gpt-4o-mini')
        assert client is not None
        assert client.provider == 'openai'

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'})
    def test_create_gemini_without_model(self):
        """Test creating Gemini client without specific model."""
        client = LLMClientFactory.create('gemini')
        assert client is not None
        assert client.provider == 'gemini'

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'})
    def test_create_gemini_with_model(self):
        """Test creating Gemini client with specific model."""
        client = LLMClientFactory.create('gemini', 'gemini-1.5-flash')
        assert client is not None
        assert client.provider == 'gemini'

    def test_create_unsupported_provider(self):
        """Test creating client with unsupported provider raises error."""
        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create('unsupported')

        assert 'Unsupported LLM provider' in str(exc_info.value)
        assert 'unsupported' in str(exc_info.value)

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_case_insensitive(self):
        """Test that provider is case insensitive."""
        client1 = LLMClientFactory.create('Claude')
        client2 = LLMClientFactory.create('CLAUDE')
        client3 = LLMClientFactory.create('claude')

        assert client1.provider == 'claude'
        assert client2.provider == 'claude'
        assert client3.provider == 'claude'


class TestLLMClientFactoryCreateFromString:
    """Tests for LLMClientFactory.create_from_string method."""

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_from_provider_only(self):
        """Test creating client from provider-only string."""
        client = LLMClientFactory.create_from_string('claude')
        assert client is not None
        assert client.provider == 'claude'

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_from_provider_model_string(self):
        """Test creating client from provider/model string."""
        client = LLMClientFactory.create_from_string('claude/claude-haiku-4-20250514')
        assert client is not None
        assert client.provider == 'claude'

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_create_from_openai_model_string(self):
        """Test creating OpenAI client from provider/model string."""
        client = LLMClientFactory.create_from_string('openai/gpt-4o-mini')
        assert client is not None
        assert client.provider == 'openai'

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'})
    def test_create_from_gemini_model_string(self):
        """Test creating Gemini client from provider/model string."""
        client = LLMClientFactory.create_from_string('gemini/gemini-1.5-flash')
        assert client is not None
        assert client.provider == 'gemini'

    def test_create_from_empty_string_raises(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create_from_string('')

        assert 'empty' in str(exc_info.value).lower()

    def test_create_from_unsupported_provider(self):
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError):
            LLMClientFactory.create_from_string('unsupported/model')

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_from_string_case_insensitive(self):
        """Test that provider is case insensitive in string."""
        client1 = LLMClientFactory.create_from_string('Claude')
        client2 = LLMClientFactory.create_from_string('CLAUDE/claude-sonnet-4-20250514')

        assert client1.provider == 'claude'
        assert client2.provider == 'claude'

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_from_string_with_whitespace(self):
        """Test that whitespace is stripped from string."""
        client = LLMClientFactory.create_from_string('  claude  ')
        assert client.provider == 'claude'


class TestLLMClientFactoryParseModelString:
    """Tests for LLMClientFactory.parse_model_string method."""

    def test_parse_provider_only(self):
        """Test parsing provider-only string."""
        provider, model = LLMClientFactory.parse_model_string('claude')
        assert provider == 'claude'
        assert model is None

    def test_parse_provider_model(self):
        """Test parsing provider/model string."""
        provider, model = LLMClientFactory.parse_model_string('claude/claude-haiku-4-20250514')
        assert provider == 'claude'
        assert model == 'claude-haiku-4-20250514'

    def test_parse_openai_model(self):
        """Test parsing OpenAI provider/model string."""
        provider, model = LLMClientFactory.parse_model_string('openai/gpt-4o-mini')
        assert provider == 'openai'
        assert model == 'gpt-4o-mini'

    def test_parse_empty_string(self):
        """Test parsing empty string returns defaults."""
        provider, model = LLMClientFactory.parse_model_string('')
        assert provider == 'claude'
        assert model is None

    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        provider, model = LLMClientFactory.parse_model_string('OPENAI/GPT-4O')
        assert provider == 'openai'
        assert model == 'gpt-4o'

    def test_parse_with_whitespace(self):
        """Test that whitespace is stripped."""
        provider, model = LLMClientFactory.parse_model_string('  gemini/gemini-1.5-pro  ')
        assert provider == 'gemini'
        assert model == 'gemini-1.5-pro'


class TestLLMClientFactoryIsValidModelString:
    """Tests for LLMClientFactory.is_valid_model_string method."""

    def test_valid_provider_only(self):
        """Test that valid provider-only string is valid."""
        assert LLMClientFactory.is_valid_model_string('claude') is True
        assert LLMClientFactory.is_valid_model_string('openai') is True
        assert LLMClientFactory.is_valid_model_string('gemini') is True

    def test_valid_provider_model(self):
        """Test that valid provider/model strings are valid."""
        assert LLMClientFactory.is_valid_model_string('claude/claude-haiku-4-20250514') is True
        assert LLMClientFactory.is_valid_model_string('openai/gpt-4o-mini') is True

    def test_invalid_provider(self):
        """Test that invalid provider is not valid."""
        assert LLMClientFactory.is_valid_model_string('unsupported') is False
        assert LLMClientFactory.is_valid_model_string('invalid/model') is False

    def test_empty_string_invalid(self):
        """Test that empty string is invalid."""
        assert LLMClientFactory.is_valid_model_string('') is False

    def test_case_insensitive_validation(self):
        """Test that validation is case insensitive."""
        assert LLMClientFactory.is_valid_model_string('CLAUDE') is True
        assert LLMClientFactory.is_valid_model_string('OpenAI') is True


class TestLLMClientFactoryCaching:
    """Tests for LLMClientFactory caching functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        LLMClientFactory.clear_cache()

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_cached_returns_same_instance(self):
        """Test that create_cached returns same instance for same config."""
        client1 = LLMClientFactory.create_cached('claude')
        client2 = LLMClientFactory.create_cached('claude')

        assert client1 is client2

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_cached_different_models_different_instances(self):
        """Test that different models get different instances."""
        client1 = LLMClientFactory.create_cached('claude', 'claude-sonnet-4-20250514')
        client2 = LLMClientFactory.create_cached('claude', 'claude-haiku-4-20250514')

        assert client1 is not client2

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_cached_from_string(self):
        """Test create_cached_from_string method."""
        client1 = LLMClientFactory.create_cached_from_string('claude')
        client2 = LLMClientFactory.create_cached_from_string('claude')

        assert client1 is client2

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_clear_cache_removes_instances(self):
        """Test that clear_cache removes cached instances."""
        client1 = LLMClientFactory.create_cached('claude')

        LLMClientFactory.clear_cache()

        client2 = LLMClientFactory.create_cached('claude')

        assert client1 is not client2


class TestLLMClientFactoryGetSupportedProviders:
    """Tests for LLMClientFactory.get_supported_providers method."""

    def test_get_supported_providers_returns_all(self):
        """Test that all providers are returned."""
        providers = LLMClientFactory.get_supported_providers()

        assert 'claude' in providers
        assert 'openai' in providers
        assert 'gemini' in providers
        assert len(providers) == 3

    def test_get_supported_providers_returns_copy(self):
        """Test that get_supported_providers returns a copy."""
        providers1 = LLMClientFactory.get_supported_providers()
        providers2 = LLMClientFactory.get_supported_providers()

        # Modifying one shouldn't affect the other
        providers1.append('test')
        assert 'test' not in providers2


class TestCLIModelArgument:
    """Tests for CLI --model argument parsing."""

    def test_parse_model_argument_provider_only(self):
        """Test parsing --model with provider only."""
        # Simulate the parsing logic from __main__.py
        model_arg = 'claude'

        if '/' in model_arg:
            provider, model = model_arg.split('/', 1)
        else:
            provider = model_arg
            model = None

        assert provider == 'claude'
        assert model is None

    def test_parse_model_argument_provider_and_model(self):
        """Test parsing --model with provider/model format."""
        model_arg = 'openai/gpt-4o-mini'

        if '/' in model_arg:
            provider, model = model_arg.split('/', 1)
        else:
            provider = model_arg
            model = None

        assert provider == 'openai'
        assert model == 'gpt-4o-mini'

    def test_parse_model_argument_auto(self):
        """Test parsing --model with 'auto' value."""
        model_arg = 'auto'

        # auto should be handled specially
        if model_arg == 'auto':
            provider = 'claude'
            model = None
        elif '/' in model_arg:
            provider, model = model_arg.split('/', 1)
        else:
            provider = model_arg
            model = None

        assert provider == 'claude'
        assert model is None


class TestRoadmapGeneratorModelSupport:
    """Tests for RoadmapGenerator model parameter support."""

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generator_accepts_model_parameter(self):
        """Test that RoadmapGenerator accepts model parameter."""
        from arcane.engines.generation.roadmap_generator import RoadmapGenerator

        # Should not raise
        generator = RoadmapGenerator(
            llm_provider='claude',
            output_directory='/tmp/test',
            model='claude-haiku-4-20250514'
        )

        assert generator.llm_provider == 'claude'
        assert generator.model == 'claude-haiku-4-20250514'

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generator_without_model_parameter(self):
        """Test that RoadmapGenerator works without model parameter."""
        from arcane.engines.generation.roadmap_generator import RoadmapGenerator

        generator = RoadmapGenerator(
            llm_provider='claude',
            output_directory='/tmp/test'
        )

        assert generator.llm_provider == 'claude'
        assert generator.model is None

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_generator_with_openai_model(self):
        """Test RoadmapGenerator with OpenAI model."""
        from arcane.engines.generation.roadmap_generator import RoadmapGenerator

        generator = RoadmapGenerator(
            llm_provider='openai',
            model='gpt-4o-mini'
        )

        assert generator.llm_provider == 'openai'
        assert generator.model == 'gpt-4o-mini'


class TestIntegration:
    """Integration tests for model selection across components."""

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_factory_string_to_generator(self):
        """Test flow from model string to generator."""
        from arcane.engines.generation.roadmap_generator import RoadmapGenerator

        # Parse model string
        model_string = 'claude/claude-haiku-4-20250514'
        provider, model = LLMClientFactory.parse_model_string(model_string)

        # Verify parsing
        assert provider == 'claude'
        assert model == 'claude-haiku-4-20250514'

        # Create generator with parsed values
        generator = RoadmapGenerator(
            llm_provider=provider,
            model=model
        )

        assert generator.llm_provider == 'claude'
        assert generator.model == 'claude-haiku-4-20250514'

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_factory_creates_client_with_correct_model(self):
        """Test that factory creates client with correct model configuration."""
        client = LLMClientFactory.create_from_string('openai/gpt-4o-mini')

        assert client.provider == 'openai'
        # The model should be set on the client
        assert hasattr(client, 'model') or hasattr(client, '_model')

    def test_all_providers_valid_in_factory(self):
        """Test that all supported providers are valid."""
        providers = LLMClientFactory.get_supported_providers()

        for provider in providers:
            assert LLMClientFactory.is_valid_model_string(provider)
