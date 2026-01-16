"""Tests for tiered model selection system."""

import pytest
from arcane.clients.model_selector import (
    ModelSelector,
    ModelConfig,
    ModelTier,
    SelectionMode,
    MODEL_CATALOG,
    ITEM_TIER_MAPPING,
    get_default_selector,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_estimate_cost(self):
        """Test cost estimation."""
        config = ModelConfig(
            provider='test',
            model_name='test-model',
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
        )

        # 1000 input tokens, 500 output tokens
        cost = config.estimate_cost(1000, 500)
        expected = (1000 / 1000 * 0.001) + (500 / 1000 * 0.002)
        assert cost == expected

    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        config = ModelConfig(
            provider='test',
            model_name='test-model',
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
        )

        cost = config.estimate_cost(0, 0)
        assert cost == 0.0

    def test_str_representation(self):
        """Test string representation."""
        config = ModelConfig(
            provider='claude',
            model_name='claude-sonnet',
            tier=ModelTier.PREMIUM,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        )

        assert str(config) == "claude/claude-sonnet (premium)"

    def test_default_values(self):
        """Test default values."""
        config = ModelConfig(
            provider='test',
            model_name='test-model',
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
        )

        assert config.best_for == []
        assert config.max_tokens == 4096
        assert config.supports_streaming is True


class TestModelTier:
    """Tests for ModelTier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert ModelTier.PREMIUM.value == "premium"
        assert ModelTier.STANDARD.value == "standard"
        assert ModelTier.ECONOMY.value == "economy"

    def test_tier_from_string(self):
        """Test creating tier from string."""
        assert ModelTier("premium") == ModelTier.PREMIUM
        assert ModelTier("standard") == ModelTier.STANDARD
        assert ModelTier("economy") == ModelTier.ECONOMY


class TestSelectionMode:
    """Tests for SelectionMode enum."""

    def test_mode_values(self):
        """Test selection mode values."""
        assert SelectionMode.TIERED.value == "tiered"
        assert SelectionMode.PREMIUM.value == "premium"
        assert SelectionMode.ECONOMY.value == "economy"
        assert SelectionMode.STANDARD.value == "standard"


class TestModelCatalog:
    """Tests for MODEL_CATALOG."""

    def test_claude_models_exist(self):
        """Test Claude models are in catalog."""
        assert 'claude' in MODEL_CATALOG
        assert ModelTier.PREMIUM in MODEL_CATALOG['claude']
        assert ModelTier.STANDARD in MODEL_CATALOG['claude']
        assert ModelTier.ECONOMY in MODEL_CATALOG['claude']

    def test_openai_models_exist(self):
        """Test OpenAI models are in catalog."""
        assert 'openai' in MODEL_CATALOG
        assert ModelTier.PREMIUM in MODEL_CATALOG['openai']
        assert ModelTier.ECONOMY in MODEL_CATALOG['openai']

    def test_gemini_models_exist(self):
        """Test Gemini models are in catalog."""
        assert 'gemini' in MODEL_CATALOG
        assert ModelTier.PREMIUM in MODEL_CATALOG['gemini']
        assert ModelTier.ECONOMY in MODEL_CATALOG['gemini']

    def test_all_models_have_required_fields(self):
        """Test all models have required fields."""
        for provider, tiers in MODEL_CATALOG.items():
            for tier, config in tiers.items():
                assert config.provider == provider
                assert config.model_name is not None
                assert config.tier == tier
                assert config.cost_per_1k_input >= 0
                assert config.cost_per_1k_output >= 0


class TestItemTierMapping:
    """Tests for ITEM_TIER_MAPPING."""

    def test_outline_uses_premium(self):
        """Test outline uses premium tier."""
        assert ITEM_TIER_MAPPING['outline'] == ModelTier.PREMIUM

    def test_milestone_uses_premium(self):
        """Test milestone uses premium tier."""
        assert ITEM_TIER_MAPPING['milestone'] == ModelTier.PREMIUM

    def test_epic_uses_standard(self):
        """Test epic uses standard tier."""
        assert ITEM_TIER_MAPPING['epic'] == ModelTier.STANDARD

    def test_story_uses_standard(self):
        """Test story description uses standard tier."""
        assert ITEM_TIER_MAPPING['story_description'] == ModelTier.STANDARD

    def test_task_uses_economy(self):
        """Test task uses economy tier."""
        assert ITEM_TIER_MAPPING['task'] == ModelTier.ECONOMY

    def test_story_tasks_uses_economy(self):
        """Test story tasks uses economy tier."""
        assert ITEM_TIER_MAPPING['story_tasks'] == ModelTier.ECONOMY


class TestModelSelector:
    """Tests for ModelSelector class."""

    def test_init_with_valid_provider(self):
        """Test initialization with valid provider."""
        selector = ModelSelector(provider='claude')
        assert selector.provider == 'claude'
        assert selector.mode == SelectionMode.TIERED

    def test_init_with_invalid_provider(self):
        """Test initialization with invalid provider raises error."""
        with pytest.raises(ValueError) as exc_info:
            ModelSelector(provider='invalid')
        assert "Unknown provider" in str(exc_info.value)

    def test_init_with_different_modes(self):
        """Test initialization with different modes."""
        for mode in ['tiered', 'premium', 'economy', 'standard']:
            selector = ModelSelector(provider='claude', mode=mode)
            assert selector.mode == SelectionMode(mode)

    def test_get_model_for_outline(self):
        """Test getting model for outline (premium tier)."""
        selector = ModelSelector(provider='claude', mode='tiered')
        config = selector.get_model_for_item('outline')

        assert config.tier == ModelTier.PREMIUM

    def test_get_model_for_epic(self):
        """Test getting model for epic (standard tier)."""
        selector = ModelSelector(provider='claude', mode='tiered')
        config = selector.get_model_for_item('epic')

        assert config.tier == ModelTier.STANDARD

    def test_get_model_for_task(self):
        """Test getting model for task (economy tier)."""
        selector = ModelSelector(provider='claude', mode='tiered')
        config = selector.get_model_for_item('task')

        assert config.tier == ModelTier.ECONOMY

    def test_premium_mode_always_uses_premium(self):
        """Test premium mode uses premium for all items."""
        selector = ModelSelector(provider='claude', mode='premium')

        for item_type in ['outline', 'epic', 'task', 'unknown']:
            config = selector.get_model_for_item(item_type)
            assert config.tier == ModelTier.PREMIUM

    def test_economy_mode_always_uses_economy(self):
        """Test economy mode uses economy for all items."""
        selector = ModelSelector(provider='claude', mode='economy')

        for item_type in ['outline', 'epic', 'task', 'unknown']:
            config = selector.get_model_for_item(item_type)
            assert config.tier == ModelTier.ECONOMY

    def test_standard_mode_always_uses_standard(self):
        """Test standard mode uses standard for all items."""
        selector = ModelSelector(provider='claude', mode='standard')

        for item_type in ['outline', 'epic', 'task', 'unknown']:
            config = selector.get_model_for_item(item_type)
            assert config.tier == ModelTier.STANDARD

    def test_unknown_item_type_uses_standard(self):
        """Test unknown item type defaults to standard tier."""
        selector = ModelSelector(provider='claude', mode='tiered')
        config = selector.get_model_for_item('unknown_type')

        assert config.tier == ModelTier.STANDARD

    def test_get_model_name(self):
        """Test getting just the model name."""
        selector = ModelSelector(provider='claude', mode='tiered')
        name = selector.get_model_name('task')

        assert 'haiku' in name.lower()

    def test_get_tier_for_item(self):
        """Test getting tier for item type."""
        selector = ModelSelector(provider='claude', mode='tiered')

        assert selector.get_tier_for_item('outline') == ModelTier.PREMIUM
        assert selector.get_tier_for_item('task') == ModelTier.ECONOMY

    def test_custom_mappings(self):
        """Test custom tier mappings."""
        custom = {'special_item': ModelTier.PREMIUM}
        selector = ModelSelector(provider='claude', custom_mappings=custom)

        config = selector.get_model_for_item('special_item')
        assert config.tier == ModelTier.PREMIUM

    def test_usage_stats_tracking(self):
        """Test usage statistics are tracked."""
        selector = ModelSelector(provider='claude', mode='tiered')

        selector.get_model_for_item('task')
        selector.get_model_for_item('task')
        selector.get_model_for_item('outline')

        stats = selector.get_usage_stats()
        assert len(stats) == 2  # Two different models used

    def test_reset_stats(self):
        """Test resetting usage statistics."""
        selector = ModelSelector(provider='claude', mode='tiered')

        selector.get_model_for_item('task')
        assert len(selector.get_usage_stats()) == 1

        selector.reset_stats()
        assert len(selector.get_usage_stats()) == 0

    def test_estimate_cost_savings(self):
        """Test cost savings estimation."""
        selector = ModelSelector(provider='claude', mode='tiered')

        item_counts = {
            'outline': 1,
            'milestone': 3,
            'epic': 10,
            'story_description': 30,
            'task': 100,
        }

        savings = selector.estimate_cost_savings(item_counts)

        assert 'premium_cost' in savings
        assert 'tiered_cost' in savings
        assert 'savings' in savings
        assert 'savings_percent' in savings
        assert savings['tiered_cost'] <= savings['premium_cost']

    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = ModelSelector.get_available_providers()

        assert 'claude' in providers
        assert 'openai' in providers
        assert 'gemini' in providers

    def test_get_available_modes(self):
        """Test getting available modes."""
        modes = ModelSelector.get_available_modes()

        assert 'tiered' in modes
        assert 'premium' in modes
        assert 'economy' in modes
        assert 'standard' in modes

    def test_get_models_for_provider(self):
        """Test getting all models for a provider."""
        models = ModelSelector.get_models_for_provider('claude')

        assert 'premium' in models
        assert 'standard' in models
        assert 'economy' in models
        assert all(isinstance(v, ModelConfig) for v in models.values())

    def test_get_models_for_invalid_provider(self):
        """Test getting models for invalid provider raises error."""
        with pytest.raises(ValueError):
            ModelSelector.get_models_for_provider('invalid')


class TestGetDefaultSelector:
    """Tests for get_default_selector function."""

    def test_default_selector(self):
        """Test creating default selector."""
        selector = get_default_selector()

        assert selector.provider == 'claude'
        assert selector.mode == SelectionMode.TIERED

    def test_default_selector_with_provider(self):
        """Test creating default selector with custom provider."""
        selector = get_default_selector(provider='openai')

        assert selector.provider == 'openai'
        assert selector.mode == SelectionMode.TIERED


class TestCostSavings:
    """Tests for cost savings calculations."""

    def test_tiered_cheaper_than_premium(self):
        """Test that tiered mode is cheaper than premium for mixed workloads."""
        selector_tiered = ModelSelector(provider='claude', mode='tiered')
        selector_premium = ModelSelector(provider='claude', mode='premium')

        # Typical roadmap with many tasks
        item_counts = {
            'outline': 1,
            'milestone': 4,
            'epic': 12,
            'story': 40,
            'task': 160,
        }

        tiered_cost = 0.0
        premium_cost = 0.0

        for item_type, count in item_counts.items():
            tiered_config = selector_tiered.get_model_for_item(item_type)
            premium_config = selector_premium.get_model_for_item(item_type)

            # Assume 2000 input, 1000 output per request
            tiered_cost += tiered_config.estimate_cost(2000 * count, 1000 * count)
            premium_cost += premium_config.estimate_cost(2000 * count, 1000 * count)

        # Tiered should be significantly cheaper
        assert tiered_cost < premium_cost
        # Should save at least 30%
        savings_percent = (premium_cost - tiered_cost) / premium_cost * 100
        assert savings_percent > 30

    def test_economy_cheapest_option(self):
        """Test that economy mode is the cheapest option."""
        selectors = {
            'tiered': ModelSelector(provider='claude', mode='tiered'),
            'premium': ModelSelector(provider='claude', mode='premium'),
            'economy': ModelSelector(provider='claude', mode='economy'),
            'standard': ModelSelector(provider='claude', mode='standard'),
        }

        item_counts = {'task': 100}
        costs = {}

        for mode, selector in selectors.items():
            config = selector.get_model_for_item('task')
            costs[mode] = config.estimate_cost(200000, 100000)

        assert costs['economy'] == min(costs.values())


class TestOpenAIModelSelector:
    """Tests for OpenAI model selection."""

    def test_openai_tiered_selection(self):
        """Test OpenAI tiered model selection."""
        selector = ModelSelector(provider='openai', mode='tiered')

        # Premium for outline
        outline_config = selector.get_model_for_item('outline')
        assert 'gpt-4o' in outline_config.model_name
        assert outline_config.tier == ModelTier.PREMIUM

        # Economy for task
        task_config = selector.get_model_for_item('task')
        assert 'mini' in task_config.model_name
        assert task_config.tier == ModelTier.ECONOMY


class TestGeminiModelSelector:
    """Tests for Gemini model selection."""

    def test_gemini_tiered_selection(self):
        """Test Gemini tiered model selection."""
        selector = ModelSelector(provider='gemini', mode='tiered')

        # Premium for outline
        outline_config = selector.get_model_for_item('outline')
        assert 'pro' in outline_config.model_name
        assert outline_config.tier == ModelTier.PREMIUM

        # Economy for task
        task_config = selector.get_model_for_item('task')
        assert 'flash' in task_config.model_name
        assert task_config.tier == ModelTier.ECONOMY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
