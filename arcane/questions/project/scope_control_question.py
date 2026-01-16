#!/usr/bin/env python3
"""Scope control question for LLM creative liberty."""

import inquirer
from ..base_question import BaseQuestion


class ScopeControlQuestion(BaseQuestion):
    """Question for controlling LLM scope and creative additions."""

    @property
    def question_key(self) -> str:
        return "scope_control"

    @property
    def cli_flag_name(self) -> str:
        return "--scope-control"

    @property
    def question_text(self) -> str:
        return "LLM Creative Liberty"

    @property
    def section_title(self) -> str:
        return "Basic Roadmap Preferences"

    def _get_emoji(self) -> str:
        return "🎯"

    def _prompt_user(self):
        """Prompt user for scope control preference."""
        question = inquirer.List(
            'scope_control',
            message="Should the LLM add roadmap items beyond your original idea?",
            choices=[
                ('Strict - Only items directly mentioned in idea', 'strict'),
                ('Standard - Include necessary supporting items', 'standard'),
                ('Creative - Add useful related features and improvements', 'creative'),
                ('Expansive - Include all possible enhancements and integrations', 'expansive'),
                ('❌ Cancel', 'cancel')
            ]
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        return answer['scope_control']

    def _get_display_value(self, value: str) -> str:
        """Get display value for CLI output."""
        display_map = {
            'strict': 'Strict (Only direct items)',
            'standard': 'Standard (Include supporting items)',
            'creative': 'Creative (Add useful features)',
            'expansive': 'Expansive (All enhancements)'
        }
        return display_map.get(value, value)