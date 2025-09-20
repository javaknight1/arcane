#!/usr/bin/env python3
"""Developer integrations question."""

import inquirer
from ..base_question import BaseQuestion


class DeveloperIntegrationsQuestion(BaseQuestion):
    """Question for developer tool integrations."""

    @property
    def question_key(self) -> str:
        return "developer_integrations"

    @property
    def cli_flag_name(self) -> str:
        return "--developer-integrations"

    @property
    def question_text(self) -> str:
        return "Developer Tool Integrations"

    @property
    def section_title(self) -> str:
        return "Integration Requirements"

    def _get_emoji(self) -> str:
        return "🛠️"

    def _prompt_user(self):
        """Prompt user for developer integrations."""
        self.console.print("[dim]Select all developer tools you need to integrate with[/dim]")

        choices = [
            ('GitHub/GitLab', 'github-gitlab'),
            ('CI/CD pipelines', 'ci-cd'),
            ('Monitoring (Datadog/New Relic)', 'monitoring'),
            ('Error tracking (Sentry)', 'error-tracking'),
            ('Feature flags', 'feature-flags'),
            ('None', 'none')
        ]

        question = inquirer.Checkbox(
            'developer_integrations',
            message="Select developer integrations (use SPACE to select, ENTER to confirm)",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        selected = answer.get('developer_integrations', [])

        # If 'none' is selected with other options, keep only 'none'
        if 'none' in selected and len(selected) > 1:
            selected = ['none']

        return selected

    def _format_value_for_display(self, value):
        """Format the developer integrations for display."""
        if not value or value == ['none']:
            return "No developer tool integrations"
        if isinstance(value, list):
            return ", ".join(value)
        return str(value)