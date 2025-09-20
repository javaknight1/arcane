#!/usr/bin/env python3
"""Team distribution question."""

import inquirer
from ..base_question import BaseQuestion


class TeamDistributionQuestion(BaseQuestion):
    """Question for team distribution type."""

    @property
    def question_key(self) -> str:
        return "team_distribution"

    @property
    def cli_flag_name(self) -> str:
        return "--team-distribution"

    @property
    def question_text(self) -> str:
        return "Team Distribution"

    @property
    def section_title(self) -> str:
        return "Team Assessment"

    def _get_emoji(self) -> str:
        return "🌐"

    def _prompt_user(self):
        """Prompt user for team distribution type."""
        self.console.print("[dim]How is your development team distributed?[/dim]")

        choices = [
            ('Co-located/same office', 'colocated'),
            ('Same timezone remote', 'remote-sync'),
            ('Distributed across timezones', 'remote-async'),
            ('Hybrid office/remote', 'hybrid'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'team_distribution',
            message="Team distribution type",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('team_distribution') == 'cancel':
            return 'cancel'

        return answer.get('team_distribution')

    def _format_value_for_display(self, value):
        """Format the distribution for display."""
        distribution_map = {
            'colocated': 'Co-located (Same office)',
            'remote-sync': 'Remote Synchronous (Same timezone)',
            'remote-async': 'Remote Asynchronous (Distributed timezones)',
            'hybrid': 'Hybrid (Office + Remote)'
        }
        return distribution_map.get(value, str(value))