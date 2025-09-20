#!/usr/bin/env python3
"""Payment integrations question."""

import inquirer
from ..base_question import BaseQuestion


class PaymentIntegrationsQuestion(BaseQuestion):
    """Question for payment integrations."""

    @property
    def question_key(self) -> str:
        return "payment_integrations"

    @property
    def cli_flag_name(self) -> str:
        return "--payment-integrations"

    @property
    def question_text(self) -> str:
        return "Payment Integrations"

    @property
    def section_title(self) -> str:
        return "Integration Requirements"

    def _get_emoji(self) -> str:
        return "💳"

    def _prompt_user(self):
        """Prompt user for payment integrations."""
        self.console.print("[dim]Select all payment systems you need to integrate with[/dim]")

        choices = [
            ('Stripe', 'stripe'),
            ('PayPal', 'paypal'),
            ('Square', 'square'),
            ('Cryptocurrency', 'cryptocurrency'),
            ('Bank transfers', 'bank-transfers'),
            ('None', 'none')
        ]

        question = inquirer.Checkbox(
            'payment_integrations',
            message="Select payment integrations (use SPACE to select, ENTER to confirm)",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        selected = answer.get('payment_integrations', [])

        # If 'none' is selected with other options, keep only 'none'
        if 'none' in selected and len(selected) > 1:
            selected = ['none']

        return selected

    def _format_value_for_display(self, value):
        """Format the payment integrations for display."""
        if not value or value == ['none']:
            return "No payment integrations"
        if isinstance(value, list):
            return ", ".join(value)
        return str(value)