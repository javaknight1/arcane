"""Tests for tiered model selection integration."""

import pytest
from unittest.mock import MagicMock, patch

from arcane.clients.model_selector import ModelSelector, ModelTier
from arcane.clients.factory import LLMClientFactory
from arcane.config.settings import GenerationSettings


class TestLLMClientFactoryWithModel:
    """Tests for LLMClientFactory with model parameter."""

    def test_create_with_default_model(self):
        """Test creating client with default model."""
        with patch('arcane.clients.claude.ClaudeLLMClient._validate_api_key'):
            with patch('arcane.clients.claude.ClaudeLLMClient._initialize_client'):
                client = LLMClientFactory.create('claude')
                assert client.provider == 'claude'

    def test_create_with_custom_model(self):
        """Test creating client with custom model."""
        with patch('arcane.clients.claude.ClaudeLLMClient._validate_api_key'):
            with patch('arcane.clients.claude.ClaudeLLMClient._initialize_client'):
                client = LLMClientFactory.create('claude', model='claude-haiku-4-20250514')
                assert client.model == 'claude-haiku-4-20250514'

    def test_create_cached_returns_same_instance(self):
        """Test that create_cached returns same instance for same config."""
        LLMClientFactory.clear_cache()

        with patch('arcane.clients.claude.ClaudeLLMClient._validate_api_key'):
            with patch('arcane.clients.claude.ClaudeLLMClient._initialize_client'):
                client1 = LLMClientFactory.create_cached('claude', 'test-model')
                client2 = LLMClientFactory.create_cached('claude', 'test-model')

                assert client1 is client2

    def test_create_cached_different_models(self):
        """Test that different models get different instances."""
        LLMClientFactory.clear_cache()

        with patch('arcane.clients.claude.ClaudeLLMClient._validate_api_key'):
            with patch('arcane.clients.claude.ClaudeLLMClient._initialize_client'):
                client1 = LLMClientFactory.create_cached('claude', 'model-a')
                client2 = LLMClientFactory.create_cached('claude', 'model-b')

                assert client1 is not client2

    def test_clear_cache(self):
        """Test clearing the client cache."""
        LLMClientFactory.clear_cache()

        with patch('arcane.clients.claude.ClaudeLLMClient._validate_api_key'):
            with patch('arcane.clients.claude.ClaudeLLMClient._initialize_client'):
                client1 = LLMClientFactory.create_cached('claude', 'test')
                LLMClientFactory.clear_cache()
                client2 = LLMClientFactory.create_cached('claude', 'test')

                assert client1 is not client2

    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = LLMClientFactory.get_supported_providers()

        assert 'claude' in providers
        assert 'openai' in providers
        assert 'gemini' in providers


class TestClaudeClientWithModel:
    """Tests for Claude client with model parameter."""

    def test_default_model(self):
        """Test Claude client uses default model."""
        with patch('arcane.clients.claude.ClaudeLLMClient._validate_api_key'):
            with patch('arcane.clients.claude.ClaudeLLMClient._initialize_client'):
                from arcane.clients.claude import ClaudeLLMClient, DEFAULT_CLAUDE_MODEL
                client = ClaudeLLMClient()
                assert client.get_model_name() == DEFAULT_CLAUDE_MODEL

    def test_custom_model(self):
        """Test Claude client with custom model."""
        with patch('arcane.clients.claude.ClaudeLLMClient._validate_api_key'):
            with patch('arcane.clients.claude.ClaudeLLMClient._initialize_client'):
                from arcane.clients.claude import ClaudeLLMClient
                client = ClaudeLLMClient(model='claude-haiku-4-20250514')
                assert client.get_model_name() == 'claude-haiku-4-20250514'


class TestOpenAIClientWithModel:
    """Tests for OpenAI client with model parameter."""

    def test_default_model(self):
        """Test OpenAI client uses default model."""
        with patch('arcane.clients.openai.OpenAILLMClient._validate_api_key'):
            with patch('arcane.clients.openai.OpenAILLMClient._initialize_client'):
                from arcane.clients.openai import OpenAILLMClient, DEFAULT_OPENAI_MODEL
                client = OpenAILLMClient()
                assert client.get_model_name() == DEFAULT_OPENAI_MODEL

    def test_custom_model(self):
        """Test OpenAI client with custom model."""
        with patch('arcane.clients.openai.OpenAILLMClient._validate_api_key'):
            with patch('arcane.clients.openai.OpenAILLMClient._initialize_client'):
                from arcane.clients.openai import OpenAILLMClient
                client = OpenAILLMClient(model='gpt-4o-mini')
                assert client.get_model_name() == 'gpt-4o-mini'


class TestRecursiveGeneratorWithModelSelector:
    """Tests for RecursiveRoadmapGenerator with model selection."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate.return_value = "Generated content"
        return client

    def test_generator_init_with_tiered_mode(self, mock_llm_client):
        """Test generator initialization with tiered mode."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator

        generator = RecursiveRoadmapGenerator(mock_llm_client, model_mode='tiered')

        assert generator.model_mode == 'tiered'
        assert generator.model_selector is not None
        assert generator.model_selector.mode.value == 'tiered'

    def test_generator_init_with_premium_mode(self, mock_llm_client):
        """Test generator initialization with premium mode."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator

        generator = RecursiveRoadmapGenerator(mock_llm_client, model_mode='premium')

        assert generator.model_mode == 'premium'
        assert generator.model_selector.mode.value == 'premium'

    def test_get_client_for_item_non_tiered(self, mock_llm_client):
        """Test that non-tiered modes use default client."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator

        generator = RecursiveRoadmapGenerator(mock_llm_client, model_mode='premium')

        client = generator._get_client_for_item('task')

        # Should return default client in non-tiered mode
        assert client is mock_llm_client

    def test_get_provider_from_client(self, mock_llm_client):
        """Test extracting provider from client."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator

        generator = RecursiveRoadmapGenerator(mock_llm_client)

        provider = generator._get_provider_from_client(mock_llm_client)
        assert provider == 'claude'

    def test_get_provider_from_client_by_classname(self):
        """Test extracting provider from client class name."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator

        # Create a mock without provider attribute
        mock_client = MagicMock(spec=[])
        mock_client.__class__.__name__ = 'OpenAILLMClient'

        generator = RecursiveRoadmapGenerator.__new__(RecursiveRoadmapGenerator)
        provider = generator._get_provider_from_client(mock_client)

        assert provider == 'openai'

    def test_get_model_usage_stats(self, mock_llm_client):
        """Test getting model usage statistics."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator

        generator = RecursiveRoadmapGenerator(mock_llm_client, model_mode='tiered')

        # Simulate some usage
        generator.model_selector.get_model_for_item('milestone')
        generator.model_selector.get_model_for_item('task')

        stats = generator.get_model_usage_stats()

        assert len(stats) == 2  # Two different models used


class TestGenerationSettingsModelMode:
    """Tests for model_mode in GenerationSettings."""

    def test_default_model_mode(self):
        """Test default model mode in settings."""
        settings = GenerationSettings()
        assert settings.model_mode == 'tiered'

    def test_custom_model_mode(self):
        """Test custom model mode in settings."""
        settings = GenerationSettings(model_mode='premium')
        assert settings.model_mode == 'premium'


class TestTieredModelFlow:
    """End-to-end tests for tiered model flow."""

    def test_different_tiers_for_different_items(self):
        """Test that different item types get different model tiers."""
        selector = ModelSelector(provider='claude', mode='tiered')

        milestone_config = selector.get_model_for_item('milestone')
        task_config = selector.get_model_for_item('task')

        # Milestone should use premium tier
        assert milestone_config.tier == ModelTier.PREMIUM

        # Task should use economy tier
        assert task_config.tier == ModelTier.ECONOMY

        # They should have different model names
        # (For Claude, sonnet vs haiku)
        assert milestone_config.model_name != task_config.model_name

    def test_story_two_pass_tiers(self):
        """Test that story two-pass uses appropriate tiers."""
        selector = ModelSelector(provider='claude', mode='tiered')

        # Pass 1 (description) should use standard tier
        desc_config = selector.get_model_for_item('story_description')
        assert desc_config.tier == ModelTier.STANDARD

        # Pass 2 (tasks) should use economy tier
        tasks_config = selector.get_model_for_item('story_tasks')
        assert tasks_config.tier == ModelTier.ECONOMY

    def test_cost_reduction_estimate(self):
        """Test that tiered mode provides cost reduction."""
        selector = ModelSelector(provider='claude', mode='tiered')

        # Typical roadmap item counts
        item_counts = {
            'outline': 1,
            'milestone': 4,
            'epic': 12,
            'story_description': 40,
            'story_tasks': 40,
            'task': 160,
        }

        savings = selector.estimate_cost_savings(item_counts)

        # Should have meaningful savings
        assert savings['savings_percent'] > 30  # At least 30% savings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
