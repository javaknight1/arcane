#!/usr/bin/env python3
"""Services budget question."""

import inquirer
from ..base_question import BaseQuestion


class ServicesBudgetQuestion(BaseQuestion):
    """Question for third-party services budget."""

    @property
    def question_key(self) -> str:
        return "services_budget"

    @property
    def cli_flag_name(self) -> str:
        return "--services-budget"

    @property
    def question_text(self) -> str:
        return "Services Budget"

    @property
    def section_title(self) -> str:
        return "Budget Assessment"

    def _get_emoji(self) -> str:
        return "🔧"

    def _prompt_user(self):
        """Prompt user for services budget."""
        self.console.print("[dim]What is your budget for third-party services (APIs, tools, SaaS)?[/dim]")

        choices = [
            ('Free tier only', 'free'),
            ('Basic paid tiers (<$500/month)', 'basic'),
            ('Professional tiers ($500-$5k/month)', 'professional'),
            ('Enterprise agreements (>$5k/month)', 'enterprise'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'services_budget',
            message="Third-party services budget",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('services_budget') == 'cancel':
            return 'cancel'

        return answer.get('services_budget')

    def _format_value_for_display(self, value):
        """Format the services budget for display."""
        budget_map = {
            'free': 'Free tier only',
            'basic': 'Basic paid tiers (<$500/month)',
            'professional': 'Professional tiers ($500-$5k/month)',
            'enterprise': 'Enterprise agreements (>$5k/month)'
        }
        return budget_map.get(value, str(value))