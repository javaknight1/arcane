#!/usr/bin/env python3
"""Technical challenges assessment question."""

import inquirer
from ..base_question import BaseQuestion


class TechnicalChallengesQuestion(BaseQuestion):
    """Question for technical challenges assessment."""

    @property
    def question_key(self) -> str:
        return "technical_challenges"

    @property
    def cli_flag_name(self) -> str:
        return "--technical-challenges"

    @property
    def question_text(self) -> str:
        return "Technical Challenges"

    @property
    def section_title(self) -> str:
        return "Technical Assessment"

    def _get_emoji(self) -> str:
        return "⚙️"

    def _prompt_user(self):
        """Prompt user for technical challenges selection."""
        self.console.print("[dim]Select all technical challenges that apply to your project[/dim]")

        choices = [
            ('Real-time data processing', 'realtime-data'),
            ('High concurrency (1000+ users)', 'high-concurrency'),
            ('Complex business logic', 'complex-logic'),
            ('Multiple third-party integrations', 'integrations'),
            ('Machine learning/AI components', 'ml-ai'),
            ('Blockchain/distributed systems', 'blockchain'),
            ('IoT/Hardware integration', 'iot-hardware'),
            ('Multi-tenant architecture', 'multi-tenant'),
            ('Offline-first capabilities', 'offline-first'),
            ('Complex data migrations', 'data-migrations'),
            ('Microservices architecture', 'microservices'),
            ('GraphQL/Complex APIs', 'graphql-apis'),
            ('None of the above', 'none')
        ]

        question = inquirer.Checkbox(
            'technical_challenges',
            message="Select technical challenges (use SPACE to select, ENTER to confirm)",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        selected = answer.get('technical_challenges', [])

        # If 'none' is selected with other options, keep only 'none'
        if 'none' in selected and len(selected) > 1:
            selected = ['none']

        return selected

    def _format_value_for_display(self, value):
        """Format the challenges for display."""
        if not value or value == ['none']:
            return "No specific technical challenges"
        if isinstance(value, list):
            return ", ".join(value)
        return str(value)