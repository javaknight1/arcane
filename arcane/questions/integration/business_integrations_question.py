#!/usr/bin/env python3
"""Business integrations question."""

import inquirer
from ..base_question import BaseQuestion


class BusinessIntegrationsQuestion(BaseQuestion):
    """Question for business tool integrations."""

    @property
    def question_key(self) -> str:
        return "business_integrations"

    @property
    def cli_flag_name(self) -> str:
        return "--business-integrations"

    @property
    def question_text(self) -> str:
        return "Business Tool Integrations"

    @property
    def section_title(self) -> str:
        return "Integration Requirements"

    def _get_emoji(self) -> str:
        return "📊"

    def _prompt_user(self):
        """Prompt user for business integrations."""
        self.console.print("[dim]Select all business tools you need to integrate with[/dim]")

        choices = [
            ('CRM (Salesforce/HubSpot)', 'crm'),
            ('Accounting (QuickBooks/Xero)', 'accounting'),
            ('Analytics (GA/Mixpanel)', 'analytics'),
            ('Support (Zendesk/Intercom)', 'support'),
            ('Marketing automation', 'marketing-automation'),
            ('None', 'none')
        ]

        question = inquirer.Checkbox(
            'business_integrations',
            message="Select business integrations (use SPACE to select, ENTER to confirm)",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        selected = answer.get('business_integrations', [])

        # If 'none' is selected with other options, keep only 'none'
        if 'none' in selected and len(selected) > 1:
            selected = ['none']

        return selected

    def _format_value_for_display(self, value):
        """Format the business integrations for display."""
        if not value or value == ['none']:
            return "No business tool integrations"
        if isinstance(value, list):
            return ", ".join(value)
        return str(value)