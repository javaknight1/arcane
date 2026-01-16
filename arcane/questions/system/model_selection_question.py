#!/usr/bin/env python3
"""LLM model selection question with provider and model choices."""

import os
from typing import Any, Dict, List, Optional, Tuple
import inquirer
from ..base_question import BaseQuestion
from arcane.clients.model_selector import MODEL_CATALOG, ModelTier


# Extended model information with user-friendly details
AVAILABLE_MODELS: Dict[str, Dict[str, Dict[str, Any]]] = {
    'claude': {
        'claude-sonnet-4-20250514': {
            'display_name': 'Claude Sonnet 4 (Recommended)',
            'description': 'Best balance of speed, intelligence, and cost',
            'tier': 'premium',
            'supports_thinking': True,
            'supports_caching': True,
            'cost_indicator': '$$',
        },
        'claude-haiku-4-20250514': {
            'display_name': 'Claude Haiku 4 (Fast & Cheap)',
            'description': 'Fastest responses, lowest cost, good for simple tasks',
            'tier': 'economy',
            'supports_thinking': False,
            'supports_caching': True,
            'cost_indicator': '$',
        },
    },
    'openai': {
        'gpt-4o': {
            'display_name': 'GPT-4o (Recommended)',
            'description': 'Most capable OpenAI model',
            'tier': 'premium',
            'supports_thinking': False,
            'supports_caching': False,
            'cost_indicator': '$$',
        },
        'gpt-4o-mini': {
            'display_name': 'GPT-4o Mini (Fast & Cheap)',
            'description': 'Faster and cheaper, good for simple tasks',
            'tier': 'economy',
            'supports_thinking': False,
            'supports_caching': False,
            'cost_indicator': '$',
        },
    },
    'gemini': {
        'gemini-1.5-pro': {
            'display_name': 'Gemini 1.5 Pro (Recommended)',
            'description': 'Most capable Gemini model with large context',
            'tier': 'premium',
            'supports_thinking': False,
            'supports_caching': False,
            'cost_indicator': '$$',
        },
        'gemini-1.5-flash': {
            'display_name': 'Gemini 1.5 Flash (Fast & Cheap)',
            'description': 'Optimized for speed and efficiency',
            'tier': 'economy',
            'supports_thinking': False,
            'supports_caching': False,
            'cost_indicator': '$',
        },
    },
}

# Provider display names and API key environment variables
PROVIDER_INFO: Dict[str, Dict[str, str]] = {
    'claude': {
        'display_name': 'Claude (Anthropic)',
        'api_key_env': 'ANTHROPIC_API_KEY',
    },
    'openai': {
        'display_name': 'OpenAI (ChatGPT)',
        'api_key_env': 'OPENAI_API_KEY',
    },
    'gemini': {
        'display_name': 'Gemini (Google)',
        'api_key_env': 'GOOGLE_API_KEY',
    },
}

# Default models for each provider (used when only provider is specified)
DEFAULT_MODELS: Dict[str, str] = {
    'claude': 'claude-sonnet-4-20250514',
    'openai': 'gpt-4o',
    'gemini': 'gemini-1.5-pro',
}


class ModelSelectionQuestion(BaseQuestion):
    """Question for selecting LLM provider and specific model."""

    @property
    def question_key(self) -> str:
        return "model_selection"

    @property
    def cli_flag_name(self) -> str:
        return "--model"

    @property
    def question_text(self) -> str:
        return "LLM Model"

    @property
    def section_title(self) -> str:
        return "System Configuration"

    def _get_emoji(self) -> str:
        return "🤖"

    def _prompt_user(self) -> Any:
        """Prompt user for provider and model selection."""
        self.console.print("\n[bold cyan]🤖 Select LLM Model[/bold cyan]")
        self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]\n")

        # Step 1: Provider selection
        provider = self._prompt_provider_selection()
        if provider == 'cancel':
            return 'cancel'
        if provider == 'auto':
            return {'provider': 'claude', 'model_name': 'auto', 'mode': 'tiered'}

        # Step 2: Model selection for chosen provider
        model_result = self._prompt_model_selection(provider)
        if model_result == 'cancel':
            return 'cancel'

        return model_result

    def _prompt_provider_selection(self) -> str:
        """Prompt user to select a provider.

        Returns:
            Provider key, 'auto' for tiered mode, or 'cancel'
        """
        self.console.print("[bold]Step 1: Choose Provider[/bold]\n")

        choices = self._get_provider_choices()
        choices.append(('', ''))  # Separator
        choices.append((
            '🔄 Auto (Tiered) - Optimal model per task type',
            'auto'
        ))
        choices.append(('❌ Cancel and Exit', 'cancel'))

        question = inquirer.List(
            'provider',
            message="Choose LLM provider",
            choices=choices,
            carousel=True
        )
        answer = inquirer.prompt([question])

        if not answer:
            return 'cancel'
        return answer.get('provider', 'cancel')

    def _prompt_model_selection(self, provider: str) -> Any:
        """Prompt user to select a model for the chosen provider.

        Args:
            provider: The selected provider key

        Returns:
            Dict with provider and model_name, or 'cancel'
        """
        provider_display = PROVIDER_INFO[provider]['display_name']
        self.console.print(f"\n[bold]Step 2: Choose Model for {provider_display}[/bold]\n")

        choices = self._get_model_choices(provider)
        choices.append(('', ''))  # Separator
        choices.append((
            f'🔄 Auto (Tiered) - Use optimal {provider_display} model per task',
            'auto'
        ))
        choices.append(('⬅️  Back to Provider Selection', 'back'))
        choices.append(('❌ Cancel and Exit', 'cancel'))

        question = inquirer.List(
            'model',
            message=f"Choose {provider_display} model",
            choices=choices,
            carousel=True
        )
        answer = inquirer.prompt([question])

        if not answer:
            return 'cancel'

        model_choice = answer.get('model', 'cancel')

        if model_choice == 'back':
            return self._prompt_user()  # Restart from provider selection
        if model_choice == 'cancel':
            return 'cancel'
        if model_choice == 'auto':
            return {'provider': provider, 'model_name': 'auto', 'mode': 'tiered'}

        return {'provider': provider, 'model_name': model_choice, 'mode': 'standard'}

    def _get_provider_choices(self) -> List[Tuple[str, str]]:
        """Get provider choices with API key status indicators.

        Returns:
            List of (display_string, value) tuples
        """
        choices = []

        for provider_key, info in PROVIDER_INFO.items():
            has_api_key = bool(os.getenv(info['api_key_env']))
            status_icon = '✅' if has_api_key else '⚠️'
            status_text = 'API key configured' if has_api_key else 'No API key'

            display = f"{status_icon} {info['display_name']} - {status_text}"
            choices.append((display, provider_key))

        return choices

    def _get_model_choices(self, provider: str) -> List[Tuple[str, str]]:
        """Get model choices for a provider with feature badges.

        Args:
            provider: Provider key

        Returns:
            List of (display_string, value) tuples
        """
        choices = []
        provider_models = AVAILABLE_MODELS.get(provider, {})

        for model_name, model_info in provider_models.items():
            display = self._format_model_choice(model_info)
            choices.append((display, model_name))

        return choices

    def _format_model_choice(self, model_info: Dict[str, Any]) -> str:
        """Format a model choice with badges and description.

        Args:
            model_info: Model information dictionary

        Returns:
            Formatted display string
        """
        badges = []

        # Cost indicator
        cost = model_info.get('cost_indicator', '$')
        badges.append(cost)

        # Feature badges
        if model_info.get('supports_thinking'):
            badges.append('[THINKING]')
        if model_info.get('supports_caching'):
            badges.append('[CACHING]')

        # Tier-based badges
        tier = model_info.get('tier', 'standard')
        if tier == 'economy':
            badges.append('[FAST]')

        badge_str = ' '.join(badges)
        display_name = model_info.get('display_name', 'Unknown')
        description = model_info.get('description', '')

        return f"{display_name} {badge_str}\n    {description}"

    def _process_flag_value(self, flag_value: Any) -> Any:
        """Process the value from CLI flag.

        Accepts formats:
        - "claude" -> uses default claude model
        - "openai/gpt-4o" -> uses specific model
        - "auto" -> uses tiered selection

        Args:
            flag_value: The CLI flag value

        Returns:
            Processed dict with provider and model_name
        """
        if flag_value is None:
            return None

        flag_value = str(flag_value).lower().strip()

        # Handle "auto" for tiered mode
        if flag_value == 'auto':
            return {'provider': 'claude', 'model_name': 'auto', 'mode': 'tiered'}

        # Handle "provider/model" format
        if '/' in flag_value:
            parts = flag_value.split('/', 1)
            provider = parts[0]
            model_name = parts[1]

            if provider not in AVAILABLE_MODELS:
                self.console.print(
                    f"[yellow]⚠️  Unknown provider '{provider}'. "
                    f"Available: {', '.join(AVAILABLE_MODELS.keys())}[/yellow]"
                )
                return None

            # Validate model name
            if model_name not in AVAILABLE_MODELS[provider]:
                available = ', '.join(AVAILABLE_MODELS[provider].keys())
                self.console.print(
                    f"[yellow]⚠️  Unknown model '{model_name}' for {provider}. "
                    f"Available: {available}[/yellow]"
                )
                return None

            return {'provider': provider, 'model_name': model_name, 'mode': 'standard'}

        # Handle provider-only format (e.g., "claude")
        if flag_value in AVAILABLE_MODELS:
            return {
                'provider': flag_value,
                'model_name': DEFAULT_MODELS[flag_value],
                'mode': 'standard'
            }

        # Unknown format
        self.console.print(
            f"[yellow]⚠️  Unknown model format '{flag_value}'. "
            f"Use 'provider' or 'provider/model' format.[/yellow]"
        )
        return None

    def _format_value_for_display(self, value: Any) -> str:
        """Format value for display.

        Args:
            value: The value to format

        Returns:
            Formatted string
        """
        if isinstance(value, dict):
            provider = value.get('provider', 'unknown')
            model = value.get('model_name', 'unknown')
            mode = value.get('mode', 'standard')

            if model == 'auto':
                return f"{provider} (tiered selection)"
            return f"{provider}/{model}"

        return str(value)

    def get_validation_error(self) -> Optional[str]:
        """Validate current value.

        Returns:
            Error message if invalid, None otherwise
        """
        if self._value is None:
            return None

        if not isinstance(self._value, dict):
            return "Model selection must be a dictionary"

        provider = self._value.get('provider')
        if not provider:
            return "Provider is required"

        if provider not in AVAILABLE_MODELS:
            return f"Unknown provider: {provider}"

        model_name = self._value.get('model_name')
        if not model_name:
            return "Model name is required"

        # 'auto' is valid for tiered mode
        if model_name == 'auto':
            return None

        if model_name not in AVAILABLE_MODELS[provider]:
            return f"Unknown model '{model_name}' for provider '{provider}'"

        return None

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers.

        Returns:
            List of provider keys
        """
        return list(AVAILABLE_MODELS.keys())

    @staticmethod
    def get_models_for_provider(provider: str) -> Dict[str, Dict[str, Any]]:
        """Get available models for a provider.

        Args:
            provider: Provider key

        Returns:
            Dictionary of model configurations
        """
        return AVAILABLE_MODELS.get(provider, {})

    @staticmethod
    def get_model_info(provider: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model.

        Args:
            provider: Provider key
            model_name: Model name

        Returns:
            Model info dict or None if not found
        """
        provider_models = AVAILABLE_MODELS.get(provider, {})
        return provider_models.get(model_name)

    @staticmethod
    def has_api_key(provider: str) -> bool:
        """Check if API key is configured for a provider.

        Args:
            provider: Provider key

        Returns:
            True if API key is set
        """
        if provider not in PROVIDER_INFO:
            return False
        env_var = PROVIDER_INFO[provider]['api_key_env']
        return bool(os.getenv(env_var))

    @staticmethod
    def get_pricing_info(provider: str, model_name: str) -> Optional[Dict[str, float]]:
        """Get pricing information from MODEL_CATALOG.

        Args:
            provider: Provider key
            model_name: Model name

        Returns:
            Dict with pricing info or None if not found
        """
        if provider not in MODEL_CATALOG:
            return None

        # Find the model in the catalog
        for tier, config in MODEL_CATALOG[provider].items():
            if config.model_name == model_name:
                return {
                    'cost_per_1k_input': config.cost_per_1k_input,
                    'cost_per_1k_output': config.cost_per_1k_output,
                    'tier': config.tier.value,
                }

        return None
