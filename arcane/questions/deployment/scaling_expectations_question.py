#!/usr/bin/env python3
"""Scaling expectations question."""

import inquirer
from ..base_question import BaseQuestion


class ScalingExpectationsQuestion(BaseQuestion):
    """Question for scaling expectations."""

    @property
    def question_key(self) -> str:
        return "scaling_expectations"

    @property
    def cli_flag_name(self) -> str:
        return "--scaling-expectations"

    @property
    def question_text(self) -> str:
        return "Scaling Expectations"

    @property
    def section_title(self) -> str:
        return "Deployment Assessment"

    def _get_emoji(self) -> str:
        return "📈"

    def _prompt_user(self):
        """Prompt user for scaling expectations."""
        self.console.print("[dim]What are your expected scaling patterns?[/dim]")

        choices = [
            ('Predictable, steady load', 'steady'),
            ('Daily peaks (business hours)', 'daily-peaks'),
            ('Seasonal variations', 'seasonal'),
            ('Viral/exponential growth possible', 'viral'),
            ('Batch processing peaks', 'batch'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'scaling_expectations',
            message="Scaling expectations",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('scaling_expectations') == 'cancel':
            return 'cancel'

        return answer.get('scaling_expectations')

    def _format_value_for_display(self, value):
        """Format the scaling expectations for display."""
        scaling_map = {
            'steady': 'Predictable, steady load',
            'daily-peaks': 'Daily peaks (business hours)',
            'seasonal': 'Seasonal variations',
            'viral': 'Viral/exponential growth possible',
            'batch': 'Batch processing peaks'
        }
        return scaling_map.get(value, str(value))