#!/usr/bin/env python3
"""Industry preference question."""

import inquirer
from ..base_question import BaseQuestion


class IndustryQuestion(BaseQuestion):
    """Question for industry/domain preference."""

    @property
    def question_key(self) -> str:
        return "industry"

    @property
    def cli_flag_name(self) -> str:
        return "--industry"

    @property
    def question_text(self) -> str:
        return "Industry/Domain"

    @property
    def section_title(self) -> str:
        return "Industry & Market Context"

    def _get_emoji(self) -> str:
        return "🏭"

    def _prompt_user(self):
        """Prompt user for industry preference."""
        question = inquirer.List(
            'industry',
            message="Industry/Domain",
            choices=[
                ('B2B SaaS', 'b2b-saas'),
                ('B2C Mobile', 'b2c-mobile'),
                ('E-commerce', 'ecommerce'),
                ('Healthcare', 'healthcare'),
                ('Finance', 'finance'),
                ('Education', 'education'),
                ('Gaming', 'gaming'),
                ('Enterprise', 'enterprise'),
                ('Government', 'government'),
                ('Non-profit', 'non-profit'),
                ('Other', 'other'),
                ('❌ Cancel', 'cancel')
            ]
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        return answer['industry']