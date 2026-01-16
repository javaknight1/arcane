"""Tests for ModelSelectionQuestion class."""

import pytest
import os
from unittest.mock import patch, MagicMock
from rich.console import Console

from arcane.questions.system.model_selection_question import (
    ModelSelectionQuestion,
    AVAILABLE_MODELS,
    PROVIDER_INFO,
    DEFAULT_MODELS,
)


class TestModelSelectionQuestionProperties:
    """Tests for ModelSelectionQuestion properties."""

    def test_question_key(self):
        """Test question_key property."""
        question = ModelSelectionQuestion()
        assert question.question_key == "model_selection"

    def test_cli_flag_name(self):
        """Test cli_flag_name property."""
        question = ModelSelectionQuestion()
        assert question.cli_flag_name == "--model"

    def test_question_text(self):
        """Test question_text property."""
        question = ModelSelectionQuestion()
        assert question.question_text == "LLM Model"

    def test_section_title(self):
        """Test section_title property."""
        question = ModelSelectionQuestion()
        assert question.section_title == "System Configuration"

    def test_get_emoji(self):
        """Test _get_emoji returns robot emoji."""
        question = ModelSelectionQuestion()
        assert question._get_emoji() == "🤖"


class TestAvailableModelsConstant:
    """Tests for AVAILABLE_MODELS constant structure."""

    def test_all_providers_present(self):
        """Test that all expected providers are present."""
        expected_providers = ['claude', 'openai', 'gemini']
        for provider in expected_providers:
            assert provider in AVAILABLE_MODELS

    def test_claude_models_structure(self):
        """Test Claude models have correct structure."""
        claude_models = AVAILABLE_MODELS['claude']

        assert 'claude-sonnet-4-20250514' in claude_models
        assert 'claude-haiku-4-20250514' in claude_models

        sonnet = claude_models['claude-sonnet-4-20250514']
        assert sonnet['display_name'] == 'Claude Sonnet 4 (Recommended)'
        assert sonnet['tier'] == 'premium'
        assert sonnet['supports_thinking'] is True
        assert sonnet['supports_caching'] is True
        assert 'description' in sonnet
        assert 'cost_indicator' in sonnet

        haiku = claude_models['claude-haiku-4-20250514']
        assert haiku['tier'] == 'economy'
        assert haiku['supports_thinking'] is False
        assert haiku['supports_caching'] is True

    def test_openai_models_structure(self):
        """Test OpenAI models have correct structure."""
        openai_models = AVAILABLE_MODELS['openai']

        assert 'gpt-4o' in openai_models
        assert 'gpt-4o-mini' in openai_models

        gpt4o = openai_models['gpt-4o']
        assert gpt4o['tier'] == 'premium'
        assert gpt4o['supports_thinking'] is False
        assert gpt4o['supports_caching'] is False

    def test_gemini_models_structure(self):
        """Test Gemini models have correct structure."""
        gemini_models = AVAILABLE_MODELS['gemini']

        assert 'gemini-1.5-pro' in gemini_models
        assert 'gemini-1.5-flash' in gemini_models

        pro = gemini_models['gemini-1.5-pro']
        assert pro['tier'] == 'premium'

        flash = gemini_models['gemini-1.5-flash']
        assert flash['tier'] == 'economy'


class TestProviderInfo:
    """Tests for PROVIDER_INFO constant."""

    def test_all_providers_have_info(self):
        """Test all providers have display names and API key env vars."""
        for provider in ['claude', 'openai', 'gemini']:
            assert provider in PROVIDER_INFO
            assert 'display_name' in PROVIDER_INFO[provider]
            assert 'api_key_env' in PROVIDER_INFO[provider]

    def test_api_key_env_vars(self):
        """Test correct API key environment variables."""
        assert PROVIDER_INFO['claude']['api_key_env'] == 'ANTHROPIC_API_KEY'
        assert PROVIDER_INFO['openai']['api_key_env'] == 'OPENAI_API_KEY'
        assert PROVIDER_INFO['gemini']['api_key_env'] == 'GOOGLE_API_KEY'


class TestDefaultModels:
    """Tests for DEFAULT_MODELS constant."""

    def test_all_providers_have_default(self):
        """Test all providers have a default model."""
        for provider in ['claude', 'openai', 'gemini']:
            assert provider in DEFAULT_MODELS
            # Default model should exist in AVAILABLE_MODELS
            assert DEFAULT_MODELS[provider] in AVAILABLE_MODELS[provider]

    def test_default_models_are_premium(self):
        """Test that default models are the premium tier."""
        for provider, model in DEFAULT_MODELS.items():
            model_info = AVAILABLE_MODELS[provider][model]
            assert model_info['tier'] == 'premium'


class TestProcessFlagValue:
    """Tests for CLI flag value processing."""

    def test_process_auto_flag(self):
        """Test processing 'auto' flag value."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('auto')

        assert result == {
            'provider': 'claude',
            'model_name': 'auto',
            'mode': 'tiered'
        }

    def test_process_provider_only_claude(self):
        """Test processing provider-only 'claude' flag."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('claude')

        assert result == {
            'provider': 'claude',
            'model_name': 'claude-sonnet-4-20250514',
            'mode': 'standard'
        }

    def test_process_provider_only_openai(self):
        """Test processing provider-only 'openai' flag."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('openai')

        assert result == {
            'provider': 'openai',
            'model_name': 'gpt-4o',
            'mode': 'standard'
        }

    def test_process_provider_only_gemini(self):
        """Test processing provider-only 'gemini' flag."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('gemini')

        assert result == {
            'provider': 'gemini',
            'model_name': 'gemini-1.5-pro',
            'mode': 'standard'
        }

    def test_process_provider_model_format(self):
        """Test processing 'provider/model' format."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('claude/claude-haiku-4-20250514')

        assert result == {
            'provider': 'claude',
            'model_name': 'claude-haiku-4-20250514',
            'mode': 'standard'
        }

    def test_process_openai_model_format(self):
        """Test processing OpenAI 'provider/model' format."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('openai/gpt-4o-mini')

        assert result == {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'mode': 'standard'
        }

    def test_process_gemini_model_format(self):
        """Test processing Gemini 'provider/model' format."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('gemini/gemini-1.5-flash')

        assert result == {
            'provider': 'gemini',
            'model_name': 'gemini-1.5-flash',
            'mode': 'standard'
        }

    def test_process_none_value(self):
        """Test processing None flag value."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value(None)

        assert result is None

    def test_process_unknown_provider(self):
        """Test processing unknown provider returns None."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('unknown_provider')

        assert result is None

    def test_process_unknown_model(self):
        """Test processing unknown model returns None."""
        question = ModelSelectionQuestion()
        result = question._process_flag_value('claude/unknown-model')

        assert result is None

    def test_process_case_insensitive(self):
        """Test flag processing is case insensitive."""
        question = ModelSelectionQuestion()

        result1 = question._process_flag_value('CLAUDE')
        result2 = question._process_flag_value('Claude')
        result3 = question._process_flag_value('claude')

        assert result1 == result2 == result3

    def test_process_with_whitespace(self):
        """Test flag processing strips whitespace."""
        question = ModelSelectionQuestion()

        result = question._process_flag_value('  claude  ')

        assert result['provider'] == 'claude'


class TestFormatValueForDisplay:
    """Tests for value formatting for display."""

    def test_format_specific_model(self):
        """Test formatting specific model selection."""
        question = ModelSelectionQuestion()
        value = {'provider': 'claude', 'model_name': 'claude-sonnet-4-20250514', 'mode': 'standard'}

        result = question._format_value_for_display(value)

        assert result == 'claude/claude-sonnet-4-20250514'

    def test_format_auto_model(self):
        """Test formatting auto/tiered selection."""
        question = ModelSelectionQuestion()
        value = {'provider': 'claude', 'model_name': 'auto', 'mode': 'tiered'}

        result = question._format_value_for_display(value)

        assert result == 'claude (tiered selection)'

    def test_format_string_value(self):
        """Test formatting string value."""
        question = ModelSelectionQuestion()

        result = question._format_value_for_display('some_string')

        assert result == 'some_string'


class TestValidation:
    """Tests for value validation."""

    def test_validation_none_value(self):
        """Test validation passes for None value."""
        question = ModelSelectionQuestion()
        question._value = None

        error = question.get_validation_error()

        assert error is None

    def test_validation_valid_specific_model(self):
        """Test validation passes for valid specific model."""
        question = ModelSelectionQuestion()
        question._value = {
            'provider': 'claude',
            'model_name': 'claude-sonnet-4-20250514',
            'mode': 'standard'
        }

        error = question.get_validation_error()

        assert error is None

    def test_validation_valid_auto_mode(self):
        """Test validation passes for auto/tiered mode."""
        question = ModelSelectionQuestion()
        question._value = {
            'provider': 'openai',
            'model_name': 'auto',
            'mode': 'tiered'
        }

        error = question.get_validation_error()

        assert error is None

    def test_validation_invalid_dict(self):
        """Test validation fails for non-dict value."""
        question = ModelSelectionQuestion()
        question._value = 'not_a_dict'

        error = question.get_validation_error()

        assert error == "Model selection must be a dictionary"

    def test_validation_missing_provider(self):
        """Test validation fails when provider is missing."""
        question = ModelSelectionQuestion()
        question._value = {'model_name': 'gpt-4o'}

        error = question.get_validation_error()

        assert error == "Provider is required"

    def test_validation_unknown_provider(self):
        """Test validation fails for unknown provider."""
        question = ModelSelectionQuestion()
        question._value = {'provider': 'unknown', 'model_name': 'model'}

        error = question.get_validation_error()

        assert 'Unknown provider' in error

    def test_validation_missing_model(self):
        """Test validation fails when model_name is missing."""
        question = ModelSelectionQuestion()
        question._value = {'provider': 'claude'}

        error = question.get_validation_error()

        assert error == "Model name is required"

    def test_validation_unknown_model(self):
        """Test validation fails for unknown model."""
        question = ModelSelectionQuestion()
        question._value = {
            'provider': 'claude',
            'model_name': 'unknown-model',
            'mode': 'standard'
        }

        error = question.get_validation_error()

        assert 'Unknown model' in error


class TestStaticMethods:
    """Tests for static helper methods."""

    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = ModelSelectionQuestion.get_available_providers()

        assert 'claude' in providers
        assert 'openai' in providers
        assert 'gemini' in providers
        assert len(providers) == 3

    def test_get_models_for_provider_claude(self):
        """Test getting models for Claude provider."""
        models = ModelSelectionQuestion.get_models_for_provider('claude')

        assert 'claude-sonnet-4-20250514' in models
        assert 'claude-haiku-4-20250514' in models

    def test_get_models_for_unknown_provider(self):
        """Test getting models for unknown provider returns empty dict."""
        models = ModelSelectionQuestion.get_models_for_provider('unknown')

        assert models == {}

    def test_get_model_info(self):
        """Test getting specific model info."""
        info = ModelSelectionQuestion.get_model_info('claude', 'claude-sonnet-4-20250514')

        assert info is not None
        assert info['display_name'] == 'Claude Sonnet 4 (Recommended)'
        assert info['supports_thinking'] is True

    def test_get_model_info_unknown(self):
        """Test getting info for unknown model returns None."""
        info = ModelSelectionQuestion.get_model_info('claude', 'unknown-model')

        assert info is None

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    def test_has_api_key_true(self):
        """Test has_api_key returns True when key is set."""
        result = ModelSelectionQuestion.has_api_key('claude')

        assert result is True

    @patch.dict(os.environ, {}, clear=True)
    def test_has_api_key_false(self):
        """Test has_api_key returns False when key is not set."""
        # Ensure ANTHROPIC_API_KEY is not set
        os.environ.pop('ANTHROPIC_API_KEY', None)

        result = ModelSelectionQuestion.has_api_key('claude')

        assert result is False

    def test_has_api_key_unknown_provider(self):
        """Test has_api_key returns False for unknown provider."""
        result = ModelSelectionQuestion.has_api_key('unknown')

        assert result is False

    def test_get_pricing_info(self):
        """Test getting pricing info from MODEL_CATALOG."""
        pricing = ModelSelectionQuestion.get_pricing_info('claude', 'claude-sonnet-4-20250514')

        assert pricing is not None
        assert 'cost_per_1k_input' in pricing
        assert 'cost_per_1k_output' in pricing
        assert 'tier' in pricing

    def test_get_pricing_info_unknown_provider(self):
        """Test getting pricing for unknown provider returns None."""
        pricing = ModelSelectionQuestion.get_pricing_info('unknown', 'model')

        assert pricing is None

    def test_get_pricing_info_unknown_model(self):
        """Test getting pricing for unknown model returns None."""
        pricing = ModelSelectionQuestion.get_pricing_info('claude', 'unknown-model')

        assert pricing is None


class TestFormatModelChoice:
    """Tests for model choice formatting."""

    def test_format_model_with_thinking(self):
        """Test formatting model that supports thinking."""
        question = ModelSelectionQuestion()
        model_info = AVAILABLE_MODELS['claude']['claude-sonnet-4-20250514']

        result = question._format_model_choice(model_info)

        assert 'Claude Sonnet 4' in result
        assert '[THINKING]' in result
        assert '[CACHING]' in result
        assert '$$' in result

    def test_format_economy_model(self):
        """Test formatting economy tier model."""
        question = ModelSelectionQuestion()
        model_info = AVAILABLE_MODELS['claude']['claude-haiku-4-20250514']

        result = question._format_model_choice(model_info)

        assert 'Claude Haiku 4' in result
        assert '[FAST]' in result
        assert '[CACHING]' in result
        assert '[THINKING]' not in result

    def test_format_openai_model(self):
        """Test formatting OpenAI model without special features."""
        question = ModelSelectionQuestion()
        model_info = AVAILABLE_MODELS['openai']['gpt-4o']

        result = question._format_model_choice(model_info)

        assert 'GPT-4o' in result
        assert '[THINKING]' not in result
        assert '[CACHING]' not in result


class TestGetProviderChoices:
    """Tests for provider choice generation."""

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}, clear=True)
    def test_provider_choices_with_api_key(self):
        """Test provider choices show configured status."""
        question = ModelSelectionQuestion()

        choices = question._get_provider_choices()

        # Find Claude choice
        claude_choice = next((c for c in choices if c[1] == 'claude'), None)
        assert claude_choice is not None
        assert '✅' in claude_choice[0]
        assert 'API key configured' in claude_choice[0]

    @patch.dict(os.environ, {}, clear=True)
    def test_provider_choices_without_api_key(self):
        """Test provider choices show warning when no API key."""
        # Ensure no API keys are set
        os.environ.pop('ANTHROPIC_API_KEY', None)
        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('GOOGLE_API_KEY', None)

        question = ModelSelectionQuestion()

        choices = question._get_provider_choices()

        # All should show warning
        for display, value in choices:
            assert '⚠️' in display
            assert 'No API key' in display


class TestGetModelChoices:
    """Tests for model choice generation."""

    def test_model_choices_for_claude(self):
        """Test getting model choices for Claude."""
        question = ModelSelectionQuestion()

        choices = question._get_model_choices('claude')

        model_names = [c[1] for c in choices]
        assert 'claude-sonnet-4-20250514' in model_names
        assert 'claude-haiku-4-20250514' in model_names

    def test_model_choices_for_openai(self):
        """Test getting model choices for OpenAI."""
        question = ModelSelectionQuestion()

        choices = question._get_model_choices('openai')

        model_names = [c[1] for c in choices]
        assert 'gpt-4o' in model_names
        assert 'gpt-4o-mini' in model_names

    def test_model_choices_for_unknown_provider(self):
        """Test getting model choices for unknown provider returns empty."""
        question = ModelSelectionQuestion()

        choices = question._get_model_choices('unknown')

        assert choices == []


class TestToDict:
    """Tests for dictionary conversion."""

    def test_to_dict_with_value(self):
        """Test converting to dictionary with a value."""
        question = ModelSelectionQuestion()
        question._value = {
            'provider': 'claude',
            'model_name': 'claude-sonnet-4-20250514',
            'mode': 'standard'
        }

        result = question.to_dict()

        assert result == {
            'model_selection': {
                'provider': 'claude',
                'model_name': 'claude-sonnet-4-20250514',
                'mode': 'standard'
            }
        }

    def test_to_dict_without_value(self):
        """Test converting to dictionary without a value."""
        question = ModelSelectionQuestion()

        result = question.to_dict()

        assert result == {'model_selection': None}


class TestSetValueFromFlag:
    """Tests for setting value from CLI flag."""

    def test_set_value_from_flag_valid(self):
        """Test setting valid value from flag."""
        question = ModelSelectionQuestion()

        question.set_value_from_flag('claude')

        assert question.is_answered is True
        assert question.value['provider'] == 'claude'
        assert question.value['model_name'] == 'claude-sonnet-4-20250514'

    def test_set_value_from_flag_none(self):
        """Test setting None value from flag does nothing."""
        question = ModelSelectionQuestion()

        question.set_value_from_flag(None)

        assert question.is_answered is False
        assert question.value is None

    def test_set_value_from_flag_invalid(self):
        """Test setting invalid value from flag results in None value.

        Note: The base class marks is_answered=True when any flag is provided,
        even if the processed value is None. Validation catches invalid values.
        """
        question = ModelSelectionQuestion()

        question.set_value_from_flag('invalid_provider')

        # Base class marks as answered when flag provided, value is None
        assert question.is_answered is True
        assert question.value is None


class TestPromptUserMocking:
    """Tests for _prompt_user with mocked inquirer."""

    @patch('arcane.questions.system.model_selection_question.inquirer')
    def test_prompt_user_cancel_at_provider(self, mock_inquirer):
        """Test canceling at provider selection."""
        mock_inquirer.prompt.return_value = {'provider': 'cancel'}
        question = ModelSelectionQuestion()

        result = question._prompt_user()

        assert result == 'cancel'

    @patch('arcane.questions.system.model_selection_question.inquirer')
    def test_prompt_user_auto_at_provider(self, mock_inquirer):
        """Test selecting auto at provider level."""
        mock_inquirer.prompt.return_value = {'provider': 'auto'}
        question = ModelSelectionQuestion()

        result = question._prompt_user()

        assert result == {
            'provider': 'claude',
            'model_name': 'auto',
            'mode': 'tiered'
        }

    @patch('arcane.questions.system.model_selection_question.inquirer')
    def test_prompt_user_select_provider_and_model(self, mock_inquirer):
        """Test selecting provider then model."""
        # First call returns provider, second returns model
        mock_inquirer.prompt.side_effect = [
            {'provider': 'openai'},
            {'model': 'gpt-4o-mini'}
        ]
        question = ModelSelectionQuestion()

        result = question._prompt_user()

        assert result == {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'mode': 'standard'
        }

    @patch('arcane.questions.system.model_selection_question.inquirer')
    def test_prompt_user_select_auto_at_model(self, mock_inquirer):
        """Test selecting provider then auto."""
        mock_inquirer.prompt.side_effect = [
            {'provider': 'gemini'},
            {'model': 'auto'}
        ]
        question = ModelSelectionQuestion()

        result = question._prompt_user()

        assert result == {
            'provider': 'gemini',
            'model_name': 'auto',
            'mode': 'tiered'
        }

    @patch('arcane.questions.system.model_selection_question.inquirer')
    def test_prompt_user_cancel_at_model(self, mock_inquirer):
        """Test canceling at model selection."""
        mock_inquirer.prompt.side_effect = [
            {'provider': 'claude'},
            {'model': 'cancel'}
        ]
        question = ModelSelectionQuestion()

        result = question._prompt_user()

        assert result == 'cancel'

    @patch('arcane.questions.system.model_selection_question.inquirer')
    def test_prompt_user_no_answer_provider(self, mock_inquirer):
        """Test handling None from inquirer at provider."""
        mock_inquirer.prompt.return_value = None
        question = ModelSelectionQuestion()

        result = question._prompt_user()

        assert result == 'cancel'


class TestReset:
    """Tests for reset functionality."""

    def test_reset_clears_value(self):
        """Test that reset clears the value."""
        question = ModelSelectionQuestion()
        question._value = {'provider': 'claude', 'model_name': 'test'}
        question._is_answered = True

        question.reset()

        assert question.value is None
        assert question.is_answered is False


class TestIntegration:
    """Integration tests for ModelSelectionQuestion."""

    def test_full_flag_workflow(self):
        """Test complete workflow: set from flag -> validate -> to_dict."""
        question = ModelSelectionQuestion()

        # Set value from CLI flag
        question.set_value_from_flag('openai/gpt-4o-mini')

        # Validate
        error = question.get_validation_error()
        assert error is None

        # Convert to dict
        result = question.to_dict()
        assert result['model_selection']['provider'] == 'openai'
        assert result['model_selection']['model_name'] == 'gpt-4o-mini'

    def test_all_provider_model_combinations_valid(self):
        """Test all provider/model combinations are valid."""
        question = ModelSelectionQuestion()

        for provider, models in AVAILABLE_MODELS.items():
            for model_name in models:
                flag_value = f"{provider}/{model_name}"
                result = question._process_flag_value(flag_value)

                assert result is not None, f"Failed for {flag_value}"
                assert result['provider'] == provider
                assert result['model_name'] == model_name

                # Validate
                question._value = result
                error = question.get_validation_error()
                assert error is None, f"Validation failed for {flag_value}: {error}"

    def test_pricing_info_matches_catalog(self):
        """Test pricing info matches MODEL_CATALOG."""
        from arcane.clients.model_selector import MODEL_CATALOG, ModelTier

        for provider in AVAILABLE_MODELS:
            for model_name in AVAILABLE_MODELS[provider]:
                pricing = ModelSelectionQuestion.get_pricing_info(provider, model_name)

                # Find the model in catalog
                for tier, config in MODEL_CATALOG[provider].items():
                    if config.model_name == model_name:
                        assert pricing['cost_per_1k_input'] == config.cost_per_1k_input
                        assert pricing['cost_per_1k_output'] == config.cost_per_1k_output
                        break
