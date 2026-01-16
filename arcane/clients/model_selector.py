"""Tiered model selection for cost-optimized LLM usage."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class ModelTier(Enum):
    """Model quality/cost tiers."""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: str
    model_name: str
    tier: ModelTier
    cost_per_1k_input: float
    cost_per_1k_output: float
    best_for: List[str] = field(default_factory=list)
    max_tokens: int = 4096
    supports_streaming: bool = True

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a given token count.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in dollars
        """
        input_cost = (input_tokens / 1000) * self.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.cost_per_1k_output
        return input_cost + output_cost

    def __str__(self) -> str:
        return f"{self.provider}/{self.model_name} ({self.tier.value})"


# Model catalog with pricing (as of early 2025)
MODEL_CATALOG: Dict[str, Dict[ModelTier, ModelConfig]] = {
    'claude': {
        ModelTier.PREMIUM: ModelConfig(
            provider='claude',
            model_name='claude-sonnet-4-20250514',
            tier=ModelTier.PREMIUM,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            best_for=['outline', 'milestone', 'complex_reasoning'],
            max_tokens=8192,
        ),
        ModelTier.STANDARD: ModelConfig(
            provider='claude',
            model_name='claude-sonnet-4-20250514',
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            best_for=['epic', 'story_description', 'detailed_content'],
            max_tokens=8192,
        ),
        ModelTier.ECONOMY: ModelConfig(
            provider='claude',
            model_name='claude-haiku-4-20250514',
            tier=ModelTier.ECONOMY,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            best_for=['task', 'story_tasks', 'simple_generation'],
            max_tokens=4096,
        ),
    },
    'openai': {
        ModelTier.PREMIUM: ModelConfig(
            provider='openai',
            model_name='gpt-4o',
            tier=ModelTier.PREMIUM,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
            best_for=['outline', 'milestone', 'complex_reasoning'],
            max_tokens=4096,
        ),
        ModelTier.STANDARD: ModelConfig(
            provider='openai',
            model_name='gpt-4o',
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
            best_for=['epic', 'story_description'],
            max_tokens=4096,
        ),
        ModelTier.ECONOMY: ModelConfig(
            provider='openai',
            model_name='gpt-4o-mini',
            tier=ModelTier.ECONOMY,
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.0006,
            best_for=['task', 'story_tasks', 'simple_generation'],
            max_tokens=4096,
        ),
    },
    'gemini': {
        ModelTier.PREMIUM: ModelConfig(
            provider='gemini',
            model_name='gemini-1.5-pro',
            tier=ModelTier.PREMIUM,
            cost_per_1k_input=0.00125,
            cost_per_1k_output=0.005,
            best_for=['outline', 'milestone', 'complex_reasoning'],
            max_tokens=8192,
        ),
        ModelTier.STANDARD: ModelConfig(
            provider='gemini',
            model_name='gemini-1.5-pro',
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.00125,
            cost_per_1k_output=0.005,
            best_for=['epic', 'story_description'],
            max_tokens=8192,
        ),
        ModelTier.ECONOMY: ModelConfig(
            provider='gemini',
            model_name='gemini-1.5-flash',
            tier=ModelTier.ECONOMY,
            cost_per_1k_input=0.000075,
            cost_per_1k_output=0.0003,
            best_for=['task', 'story_tasks', 'simple_generation'],
            max_tokens=8192,
        ),
    },
}

# Mapping of item types to appropriate model tiers
ITEM_TIER_MAPPING: Dict[str, ModelTier] = {
    # High complexity items need premium models
    'outline': ModelTier.PREMIUM,
    'semantic_outline': ModelTier.PREMIUM,
    'milestone': ModelTier.PREMIUM,

    # Medium complexity items use standard models
    'epic': ModelTier.STANDARD,
    'story_description': ModelTier.STANDARD,
    'story': ModelTier.STANDARD,

    # Low complexity items can use economy models
    'story_tasks': ModelTier.ECONOMY,
    'task': ModelTier.ECONOMY,
    'subtask': ModelTier.ECONOMY,
}


class SelectionMode(Enum):
    """Model selection modes."""
    TIERED = "tiered"      # Use appropriate tier for each item type
    PREMIUM = "premium"    # Always use premium models (highest quality)
    ECONOMY = "economy"    # Always use economy models (lowest cost)
    STANDARD = "standard"  # Always use standard models (balanced)


class ModelSelector:
    """Selects appropriate models based on item type and mode."""

    def __init__(
        self,
        provider: str,
        mode: str = 'tiered',
        custom_mappings: Optional[Dict[str, ModelTier]] = None
    ):
        """Initialize the model selector.

        Args:
            provider: LLM provider name ('claude', 'openai', 'gemini')
            mode: Selection mode ('tiered', 'premium', 'economy', 'standard')
            custom_mappings: Optional custom item type to tier mappings
        """
        self.provider = provider.lower()
        self.mode = SelectionMode(mode.lower()) if isinstance(mode, str) else mode
        self.custom_mappings = custom_mappings or {}

        # Validate provider
        if self.provider not in MODEL_CATALOG:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Available: {', '.join(MODEL_CATALOG.keys())}"
            )

        # Track usage statistics
        self._usage_stats: Dict[str, Dict[str, Any]] = {}

    def get_model_for_item(self, item_type: str) -> ModelConfig:
        """Get appropriate model configuration for an item type.

        Args:
            item_type: Type of item being generated

        Returns:
            ModelConfig for the appropriate model
        """
        provider_models = MODEL_CATALOG[self.provider]

        if self.mode == SelectionMode.PREMIUM:
            config = provider_models[ModelTier.PREMIUM]
        elif self.mode == SelectionMode.ECONOMY:
            config = provider_models.get(
                ModelTier.ECONOMY,
                provider_models.get(ModelTier.STANDARD, provider_models[ModelTier.PREMIUM])
            )
        elif self.mode == SelectionMode.STANDARD:
            config = provider_models.get(
                ModelTier.STANDARD,
                provider_models[ModelTier.PREMIUM]
            )
        else:  # TIERED mode
            # Check custom mappings first
            tier = self.custom_mappings.get(
                item_type,
                ITEM_TIER_MAPPING.get(item_type, ModelTier.STANDARD)
            )
            config = provider_models.get(tier, provider_models[ModelTier.STANDARD])

        # Track usage
        self._track_usage(item_type, config)

        return config

    def get_model_name(self, item_type: str) -> str:
        """Get just the model name for an item type.

        Args:
            item_type: Type of item being generated

        Returns:
            Model name string
        """
        return self.get_model_for_item(item_type).model_name

    def get_tier_for_item(self, item_type: str) -> ModelTier:
        """Get the tier that would be used for an item type.

        Args:
            item_type: Type of item

        Returns:
            ModelTier that would be selected
        """
        if self.mode == SelectionMode.PREMIUM:
            return ModelTier.PREMIUM
        elif self.mode == SelectionMode.ECONOMY:
            return ModelTier.ECONOMY
        elif self.mode == SelectionMode.STANDARD:
            return ModelTier.STANDARD
        else:
            return self.custom_mappings.get(
                item_type,
                ITEM_TIER_MAPPING.get(item_type, ModelTier.STANDARD)
            )

    def _track_usage(self, item_type: str, config: ModelConfig) -> None:
        """Track model usage for statistics.

        Args:
            item_type: Type of item
            config: Model configuration used
        """
        key = f"{config.model_name}:{config.tier.value}"
        if key not in self._usage_stats:
            self._usage_stats[key] = {
                'model': config.model_name,
                'tier': config.tier.value,
                'count': 0,
                'item_types': set(),
            }
        self._usage_stats[key]['count'] += 1
        self._usage_stats[key]['item_types'].add(item_type)

    def get_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics.

        Returns:
            Dictionary of usage stats by model
        """
        # Convert sets to lists for JSON serialization
        stats = {}
        for key, value in self._usage_stats.items():
            stats[key] = {
                'model': value['model'],
                'tier': value['tier'],
                'count': value['count'],
                'item_types': list(value['item_types']),
            }
        return stats

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self._usage_stats = {}

    def estimate_cost_savings(
        self,
        item_counts: Dict[str, int],
        avg_input_tokens: int = 2000,
        avg_output_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Estimate cost savings compared to using premium for everything.

        Args:
            item_counts: Dictionary of item type to count
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request

        Returns:
            Dictionary with cost comparison
        """
        provider_models = MODEL_CATALOG[self.provider]
        premium_config = provider_models[ModelTier.PREMIUM]

        premium_cost = 0.0
        tiered_cost = 0.0

        for item_type, count in item_counts.items():
            # Premium cost (all items with premium model)
            premium_cost += premium_config.estimate_cost(
                avg_input_tokens * count,
                avg_output_tokens * count
            )

            # Tiered cost (appropriate model for each type)
            tiered_config = self.get_model_for_item(item_type)
            tiered_cost += tiered_config.estimate_cost(
                avg_input_tokens * count,
                avg_output_tokens * count
            )

        savings = premium_cost - tiered_cost
        savings_percent = (savings / premium_cost * 100) if premium_cost > 0 else 0

        return {
            'premium_cost': round(premium_cost, 4),
            'tiered_cost': round(tiered_cost, 4),
            'savings': round(savings, 4),
            'savings_percent': round(savings_percent, 1),
            'mode': self.mode.value,
        }

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers.

        Returns:
            List of provider names
        """
        return list(MODEL_CATALOG.keys())

    @classmethod
    def get_available_modes(cls) -> List[str]:
        """Get list of available selection modes.

        Returns:
            List of mode names
        """
        return [mode.value for mode in SelectionMode]

    @classmethod
    def get_models_for_provider(cls, provider: str) -> Dict[str, ModelConfig]:
        """Get all models available for a provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary of tier to ModelConfig
        """
        if provider not in MODEL_CATALOG:
            raise ValueError(f"Unknown provider: {provider}")

        return {tier.value: config for tier, config in MODEL_CATALOG[provider].items()}


def get_default_selector(provider: str = 'claude') -> ModelSelector:
    """Get a default model selector.

    Args:
        provider: LLM provider name

    Returns:
        ModelSelector instance with default settings
    """
    return ModelSelector(provider=provider, mode='tiered')
