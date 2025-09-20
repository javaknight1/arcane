#!/usr/bin/env python3
"""Development methodology question."""

import inquirer
from ..base_question import BaseQuestion


class DevMethodologyQuestion(BaseQuestion):
    """Question for development methodology."""

    @property
    def question_key(self) -> str:
        return "dev_methodology"

    @property
    def cli_flag_name(self) -> str:
        return "--dev-methodology"

    @property
    def question_text(self) -> str:
        return "Development Methodology"

    @property
    def section_title(self) -> str:
        return "Team Assessment"

    def _get_emoji(self) -> str:
        return "📋"

    def _prompt_user(self):
        """Prompt user for development methodology."""
        self.console.print("[dim]What development methodology does your team prefer?[/dim]")

        choices = [
            ('Agile/Scrum sprints', 'agile'),
            ('Kanban continuous flow', 'kanban'),
            ('Waterfall phases', 'waterfall'),
            ('No formal process', 'adhoc'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'dev_methodology',
            message="Development methodology",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('dev_methodology') == 'cancel':
            return 'cancel'

        return answer.get('dev_methodology')

    def _format_value_for_display(self, value):
        """Format the methodology for display."""
        methodology_map = {
            'agile': 'Agile/Scrum (Sprint-based)',
            'kanban': 'Kanban (Continuous flow)',
            'waterfall': 'Waterfall (Phase-based)',
            'adhoc': 'Ad-hoc (No formal process)'
        }
        return methodology_map.get(value, str(value))