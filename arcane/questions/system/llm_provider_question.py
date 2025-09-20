#!/usr/bin/env python3
"""LLM provider selection question."""

import os
import inquirer
from ..base_question import BaseQuestion


class LLMProviderQuestion(BaseQuestion):
    """Question for LLM provider selection."""

    @property
    def question_key(self) -> str:
        return "llm_provider"

    @property
    def cli_flag_name(self) -> str:
        return "--provider"

    @property
    def question_text(self) -> str:
        return "LLM Provider"

    @property
    def section_title(self) -> str:
        return "System Configuration"

    def _get_emoji(self) -> str:
        return "🤖"

    def _prompt_user(self):
        """Prompt user for LLM provider selection."""
        self.console.print("[bold]Select your preferred LLM provider:[/bold]")

        available_providers = self._get_available_providers()
        if available_providers:
            self.console.print(f"[green]✅ {len(available_providers)} provider(s) configured with API keys[/green]")
        else:
            self.console.print("[yellow]⚠️  No API keys configured. All providers will show authentication errors.[/yellow]")

        self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]")

        choices = []
        if os.getenv('ANTHROPIC_API_KEY'):
            choices.append(('Claude (Anthropic) ✅', 'claude'))
        else:
            choices.append(('Claude (Anthropic) ⚠️ [No API key]', 'claude'))

        if os.getenv('OPENAI_API_KEY'):
            choices.append(('ChatGPT (OpenAI) ✅', 'openai'))
        else:
            choices.append(('ChatGPT (OpenAI) ⚠️ [No API key]', 'openai'))

        if os.getenv('GOOGLE_API_KEY'):
            choices.append(('Gemini (Google) ✅', 'gemini'))
        else:
            choices.append(('Gemini (Google) ⚠️ [No API key]', 'gemini'))

        choices.append(('❌ Cancel and Exit', 'cancel'))

        question = inquirer.List('llm_provider', message="Choose LLM provider", choices=choices, carousel=True)
        answer = inquirer.prompt([question])

        if not answer or answer.get('llm_provider') == 'cancel':
            return 'cancel'

        return answer.get('llm_provider')

    def _get_available_providers(self) -> list:
        """Get list of available LLM providers based on API keys."""
        available = []
        if os.getenv('ANTHROPIC_API_KEY'):
            available.append('Claude (Anthropic)')
        if os.getenv('OPENAI_API_KEY'):
            available.append('ChatGPT (OpenAI)')
        if os.getenv('GOOGLE_API_KEY'):
            available.append('Gemini (Google)')
        return available