#!/usr/bin/env python3
"""Success metric question."""

import inquirer
from ..base_question import BaseQuestion


class SuccessMetricQuestion(BaseQuestion):
    """Question for primary success metric."""

    @property
    def question_key(self) -> str:
        return "success_metric"

    @property
    def cli_flag_name(self) -> str:
        return "--success-metric"

    @property
    def question_text(self) -> str:
        return "Primary Success Metric"

    @property
    def section_title(self) -> str:
        return "Success Definition"

    def _get_emoji(self) -> str:
        return "🎯"

    def _prompt_user(self):
        """Prompt user for success metric."""
        self.console.print("[dim]What is your primary success metric for this project?[/dim]")

        choices = [
            ('User adoption/growth rate', 'adoption'),
            ('Revenue generation', 'revenue'),
            ('Cost reduction/efficiency', 'cost-saving'),
            ('Time to market', 'speed'),
            ('System performance/reliability', 'performance'),
            ('User satisfaction/NPS', 'satisfaction'),
            ('Market disruption/innovation', 'innovation'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'success_metric',
            message="Primary success metric",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('success_metric') == 'cancel':
            return 'cancel'

        return answer.get('success_metric')

    def _format_value_for_display(self, value):
        """Format the success metric for display."""
        metric_map = {
            'adoption': 'User adoption/growth rate',
            'revenue': 'Revenue generation',
            'cost-saving': 'Cost reduction/efficiency',
            'speed': 'Time to market',
            'performance': 'System performance/reliability',
            'satisfaction': 'User satisfaction/NPS',
            'innovation': 'Market disruption/innovation'
        }
        return metric_map.get(value, str(value))