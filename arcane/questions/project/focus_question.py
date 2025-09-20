#!/usr/bin/env python3
"""Project focus question."""

import inquirer
from ..base_question import BaseQuestion


class FocusQuestion(BaseQuestion):
    """Question for project focus preference."""

    @property
    def question_key(self) -> str:
        return "focus"

    @property
    def cli_flag_name(self) -> str:
        return "--focus"

    @property
    def question_text(self) -> str:
        return "Primary Focus"

    @property
    def section_title(self) -> str:
        return "Basic Roadmap Preferences"

    def _get_emoji(self) -> str:
        return "🎯"

    def _prompt_user(self):
        """Prompt user for project focus."""
        question = inquirer.List(
            'focus',
            message="Primary focus",
            choices=[
                ('MVP / Startup launch', 'mvp'),
                ('Feature development', 'feature'),
                ('System migration', 'migration'),
                ('Performance optimization', 'optimization'),
                ('❌ Cancel', 'cancel')
            ]
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        return answer['focus']