#!/usr/bin/env python3
"""Success timeline question."""

import inquirer
from ..base_question import BaseQuestion


class SuccessTimelineQuestion(BaseQuestion):
    """Question for success timeline."""

    @property
    def question_key(self) -> str:
        return "success_timeline"

    @property
    def cli_flag_name(self) -> str:
        return "--success-timeline"

    @property
    def question_text(self) -> str:
        return "Success Timeline"

    @property
    def section_title(self) -> str:
        return "Success Definition"

    def _get_emoji(self) -> str:
        return "⏰"

    def _prompt_user(self):
        """Prompt user for success timeline."""
        self.console.print("[dim]When do you expect to achieve your success metric?[/dim]")

        choices = [
            ('Immediate (< 1 month)', 'immediate'),
            ('Short-term (1-3 months)', 'short'),
            ('Medium-term (3-12 months)', 'medium'),
            ('Long-term (1+ years)', 'long'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'success_timeline',
            message="Success timeline",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('success_timeline') == 'cancel':
            return 'cancel'

        return answer.get('success_timeline')

    def _format_value_for_display(self, value):
        """Format the success timeline for display."""
        timeline_map = {
            'immediate': 'Immediate (< 1 month)',
            'short': 'Short-term (1-3 months)',
            'medium': 'Medium-term (3-12 months)',
            'long': 'Long-term (1+ years)'
        }
        return timeline_map.get(value, str(value))