#!/usr/bin/env python3
"""Data integrations question."""

import inquirer
from ..base_question import BaseQuestion


class DataIntegrationsQuestion(BaseQuestion):
    """Question for data source integrations."""

    @property
    def question_key(self) -> str:
        return "data_integrations"

    @property
    def cli_flag_name(self) -> str:
        return "--data-integrations"

    @property
    def question_text(self) -> str:
        return "Data Source Integrations"

    @property
    def section_title(self) -> str:
        return "Integration Requirements"

    def _get_emoji(self) -> str:
        return "🗄️"

    def _prompt_user(self):
        """Prompt user for data integrations."""
        self.console.print("[dim]Select all data sources you need to integrate with[/dim]")

        choices = [
            ('REST APIs', 'rest-apis'),
            ('GraphQL APIs', 'graphql-apis'),
            ('Webhooks', 'webhooks'),
            ('WebSockets', 'websockets'),
            ('File uploads (S3/GCS)', 'file-uploads'),
            ('Databases', 'databases'),
            ('None', 'none')
        ]

        question = inquirer.Checkbox(
            'data_integrations',
            message="Select data integrations (use SPACE to select, ENTER to confirm)",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        selected = answer.get('data_integrations', [])

        # If 'none' is selected with other options, keep only 'none'
        if 'none' in selected and len(selected) > 1:
            selected = ['none']

        return selected

    def _format_value_for_display(self, value):
        """Format the data integrations for display."""
        if not value or value == ['none']:
            return "No data source integrations"
        if isinstance(value, list):
            return ", ".join(value)
        return str(value)