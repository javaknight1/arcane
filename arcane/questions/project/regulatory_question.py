#!/usr/bin/env python3
"""Regulatory requirements question."""

import inquirer
from typing import List
from ..base_question import BaseQuestion


class RegulatoryQuestion(BaseQuestion):
    """Question for regulatory requirements."""

    @property
    def question_key(self) -> str:
        return "regulatory"

    @property
    def cli_flag_name(self) -> str:
        return "--regulatory"

    @property
    def question_text(self) -> str:
        return "Regulatory Requirements"

    @property
    def section_title(self) -> str:
        return "Industry & Market Context"

    def _get_emoji(self) -> str:
        return "📋"

    def _prompt_user(self):
        """Prompt user for regulatory requirements."""
        question = inquirer.Checkbox(
            'regulatory',
            message="Regulatory requirements (select all that apply)",
            choices=[
                ('GDPR (Data protection)', 'gdpr'),
                ('HIPAA (Healthcare)', 'hipaa'),
                ('PCI DSS (Payment cards)', 'pci-dss'),
                ('SOC 2 (Security)', 'soc2'),
                ('ISO 27001 (Information security)', 'iso27001'),
                ('FERPA (Education)', 'ferpa'),
                ('FedRAMP (US Government)', 'fedramp'),
                ('None', 'none')
            ],
            default=['none']
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        regulatory = answer['regulatory']

        # If 'none' is selected, clear others
        if 'none' in regulatory:
            regulatory = ['none']

        return regulatory

    def _process_user_answer(self, answer):
        """Process regulatory answer and create derived fields."""
        if isinstance(answer, list):
            return {
                'regulatory': answer,
                'regulatory_requirements': ', '.join(answer)
            }
        return answer

    def to_dict(self):
        """Convert to dictionary with both list and string formats."""
        if isinstance(self._value, dict):
            return self._value
        elif isinstance(self._value, list):
            return {
                'regulatory': self._value,
                'regulatory_requirements': ', '.join(self._value)
            }
        else:
            return {
                'regulatory': self._value or ['none'],
                'regulatory_requirements': str(self._value or 'none')
            }