#!/usr/bin/env python3
"""Measurement approach question."""

import inquirer
from ..base_question import BaseQuestion


class MeasurementApproachQuestion(BaseQuestion):
    """Question for measurement approach."""

    @property
    def question_key(self) -> str:
        return "measurement_approach"

    @property
    def cli_flag_name(self) -> str:
        return "--measurement-approach"

    @property
    def question_text(self) -> str:
        return "Measurement Approach"

    @property
    def section_title(self) -> str:
        return "Success Definition"

    def _get_emoji(self) -> str:
        return "📏"

    def _prompt_user(self):
        """Prompt user for measurement approach."""
        self.console.print("[dim]How will you measure success?[/dim]")

        choices = [
            ('Quantitative metrics only', 'quantitative'),
            ('Qualitative feedback focus', 'qualitative'),
            ('Mixed quantitative/qualitative', 'mixed'),
            ('No formal measurement planned', 'none'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'measurement_approach',
            message="Measurement approach",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('measurement_approach') == 'cancel':
            return 'cancel'

        return answer.get('measurement_approach')

    def _format_value_for_display(self, value):
        """Format the measurement approach for display."""
        approach_map = {
            'quantitative': 'Quantitative metrics only',
            'qualitative': 'Qualitative feedback focus',
            'mixed': 'Mixed quantitative/qualitative',
            'none': 'No formal measurement planned'
        }
        return approach_map.get(value, str(value))