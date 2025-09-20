#!/usr/bin/env python3
"""Infrastructure budget question."""

import inquirer
from ..base_question import BaseQuestion


class InfraBudgetQuestion(BaseQuestion):
    """Question for infrastructure budget."""

    @property
    def question_key(self) -> str:
        return "infra_budget"

    @property
    def cli_flag_name(self) -> str:
        return "--infra-budget"

    @property
    def question_text(self) -> str:
        return "Infrastructure Budget"

    @property
    def section_title(self) -> str:
        return "Budget Assessment"

    def _get_emoji(self) -> str:
        return "🏗️"

    def _prompt_user(self):
        """Prompt user for infrastructure budget."""
        self.console.print("[dim]What is your monthly infrastructure budget (hosting, cloud services, etc.)?[/dim]")

        choices = [
            ('Minimal (<$100/month)', 'minimal'),
            ('Moderate ($100-$1000/month)', 'moderate'),
            ('Substantial ($1000-$10k/month)', 'substantial'),
            ('Unlimited (>$10k/month)', 'unlimited'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'infra_budget',
            message="Monthly infrastructure budget",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('infra_budget') == 'cancel':
            return 'cancel'

        return answer.get('infra_budget')

    def _format_value_for_display(self, value):
        """Format the infrastructure budget for display."""
        budget_map = {
            'minimal': 'Minimal (<$100/month)',
            'moderate': 'Moderate ($100-$1000/month)',
            'substantial': 'Substantial ($1000-$10k/month)',
            'unlimited': 'Unlimited (>$10k/month)'
        }
        return budget_map.get(value, str(value))