#!/usr/bin/env python3
"""Failure tolerance question."""

import inquirer
from ..base_question import BaseQuestion


class FailureToleranceQuestion(BaseQuestion):
    """Question for acceptable failure rate."""

    @property
    def question_key(self) -> str:
        return "failure_tolerance"

    @property
    def cli_flag_name(self) -> str:
        return "--failure-tolerance"

    @property
    def question_text(self) -> str:
        return "Failure Tolerance"

    @property
    def section_title(self) -> str:
        return "Success Definition"

    def _get_emoji(self) -> str:
        return "⚠️"

    def _prompt_user(self):
        """Prompt user for failure tolerance."""
        self.console.print("[dim]What is your acceptable failure rate?[/dim]")

        choices = [
            ('Zero tolerance - must work perfectly', 'zero'),
            ('Low tolerance (<1% failure)', 'low'),
            ('Moderate tolerance (1-5% failure)', 'moderate'),
            ('High tolerance (fail fast approach)', 'high'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'failure_tolerance',
            message="Acceptable failure rate",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('failure_tolerance') == 'cancel':
            return 'cancel'

        return answer.get('failure_tolerance')

    def _format_value_for_display(self, value):
        """Format the failure tolerance for display."""
        tolerance_map = {
            'zero': 'Zero tolerance (must work perfectly)',
            'low': 'Low tolerance (<1% failure)',
            'moderate': 'Moderate tolerance (1-5% failure)',
            'high': 'High tolerance (fail fast approach)'
        }
        return tolerance_map.get(value, str(value))