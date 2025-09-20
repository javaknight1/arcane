#!/usr/bin/env python3
"""Timeline preference question."""

import inquirer
from rich.prompt import Prompt
from ..base_question import BaseQuestion


class TimelineQuestion(BaseQuestion):
    """Question for project timeline preference."""

    @property
    def question_key(self) -> str:
        return "timeline"

    @property
    def cli_flag_name(self) -> str:
        return "--timeline"

    @property
    def question_text(self) -> str:
        return "Project Timeline"

    @property
    def section_title(self) -> str:
        return "Basic Roadmap Preferences"

    def _get_emoji(self) -> str:
        return "⏱️"

    def _prompt_user(self):
        """Prompt user for timeline preference."""
        question = inquirer.List(
            'timeline',
            message="Project timeline",
            choices=[
                ('3 months (MVP focus)', '3-months'),
                ('6 months (Balanced)', '6-months'),
                ('12 months (Comprehensive)', '12-months'),
                ('Custom timeline', 'custom'),
                ('❌ Cancel', 'cancel')
            ]
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        timeline = answer['timeline']
        if timeline == 'custom':
            try:
                custom_timeline = Prompt.ask("Enter custom timeline (e.g., '4 months', '18 months')")
                return custom_timeline
            except KeyboardInterrupt:
                return 'cancel'

        return timeline