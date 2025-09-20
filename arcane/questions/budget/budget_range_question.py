#!/usr/bin/env python3
"""Budget range question."""

import inquirer
from ..base_question import BaseQuestion


class BudgetRangeQuestion(BaseQuestion):
    """Question for overall budget range."""

    @property
    def question_key(self) -> str:
        return "budget_range"

    @property
    def cli_flag_name(self) -> str:
        return "--budget-range"

    @property
    def question_text(self) -> str:
        return "Overall Budget Range"

    @property
    def section_title(self) -> str:
        return "Budget Assessment"

    def _get_emoji(self) -> str:
        return "💰"

    def _prompt_user(self):
        """Prompt user for budget range."""
        self.console.print("[dim]What is your overall project budget range?[/dim]")

        choices = [
            ('Bootstrapped/Personal (<$10k)', 'bootstrap'),
            ('Seed funded ($10k-$100k)', 'seed'),
            ('Series A/B ($100k-$1M)', 'funded'),
            ('Enterprise ($1M+)', 'enterprise'),
            ('Not determined yet', 'undefined'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'budget_range',
            message="Overall budget range",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('budget_range') == 'cancel':
            return 'cancel'

        return answer.get('budget_range')

    def _format_value_for_display(self, value):
        """Format the budget range for display."""
        budget_map = {
            'bootstrap': 'Bootstrapped (<$10k)',
            'seed': 'Seed funded ($10k-$100k)',
            'funded': 'Well funded ($100k-$1M)',
            'enterprise': 'Enterprise ($1M+)',
            'undefined': 'Not determined yet'
        }
        return budget_map.get(value, str(value))