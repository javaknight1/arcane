#!/usr/bin/env python3
"""Communication integrations question."""

import inquirer
from ..base_question import BaseQuestion


class CommunicationIntegrationsQuestion(BaseQuestion):
    """Question for communication integrations."""

    @property
    def question_key(self) -> str:
        return "communication_integrations"

    @property
    def cli_flag_name(self) -> str:
        return "--communication-integrations"

    @property
    def question_text(self) -> str:
        return "Communication Integrations"

    @property
    def section_title(self) -> str:
        return "Integration Requirements"

    def _get_emoji(self) -> str:
        return "📧"

    def _prompt_user(self):
        """Prompt user for communication integrations."""
        self.console.print("[dim]Select all communication services you need to integrate with[/dim]")

        choices = [
            ('Email (SendGrid/SES)', 'email'),
            ('SMS (Twilio)', 'sms'),
            ('Push notifications', 'push-notifications'),
            ('In-app chat', 'in-app-chat'),
            ('Video calls', 'video-calls'),
            ('None', 'none')
        ]

        question = inquirer.Checkbox(
            'communication_integrations',
            message="Select communication integrations (use SPACE to select, ENTER to confirm)",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        selected = answer.get('communication_integrations', [])

        # If 'none' is selected with other options, keep only 'none'
        if 'none' in selected and len(selected) > 1:
            selected = ['none']

        return selected

    def _format_value_for_display(self, value):
        """Format the communication integrations for display."""
        if not value or value == ['none']:
            return "No communication integrations"
        if isinstance(value, list):
            return ", ".join(value)
        return str(value)