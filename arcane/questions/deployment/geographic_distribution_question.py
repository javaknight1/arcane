#!/usr/bin/env python3
"""Geographic distribution question."""

import inquirer
from ..base_question import BaseQuestion


class GeographicDistributionQuestion(BaseQuestion):
    """Question for geographic distribution needs."""

    @property
    def question_key(self) -> str:
        return "geographic_distribution"

    @property
    def cli_flag_name(self) -> str:
        return "--geographic-distribution"

    @property
    def question_text(self) -> str:
        return "Geographic Distribution"

    @property
    def section_title(self) -> str:
        return "Deployment Assessment"

    def _get_emoji(self) -> str:
        return "🌍"

    def _prompt_user(self):
        """Prompt user for geographic distribution needs."""
        self.console.print("[dim]What are your geographic distribution needs?[/dim]")

        choices = [
            ('Single region', 'single-region'),
            ('Multi-region (same continent)', 'multi-region'),
            ('Global distribution', 'global'),
            ('Data residency requirements', 'data-residency'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'geographic_distribution',
            message="Geographic distribution needs",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('geographic_distribution') == 'cancel':
            return 'cancel'

        return answer.get('geographic_distribution')

    def _format_value_for_display(self, value):
        """Format the geographic distribution for display."""
        geo_map = {
            'single-region': 'Single region',
            'multi-region': 'Multi-region (same continent)',
            'global': 'Global distribution',
            'data-residency': 'Data residency requirements'
        }
        return geo_map.get(value, str(value))