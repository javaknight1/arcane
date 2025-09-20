#!/usr/bin/env python3
"""Team size question."""

import inquirer
from ..base_question import BaseQuestion


class TeamSizeQuestion(BaseQuestion):
    """Question for team size preference."""

    @property
    def question_key(self) -> str:
        return "team_size"

    @property
    def cli_flag_name(self) -> str:
        return "--team-size"

    @property
    def question_text(self) -> str:
        return "Team Size"

    @property
    def section_title(self) -> str:
        return "Basic Roadmap Preferences"

    def _get_emoji(self) -> str:
        return "👥"

    def _prompt_user(self):
        """Prompt user for team size."""
        question = inquirer.List(
            'team_size',
            message="Development team size",
            choices=[
                ('Solo developer', '1'),
                ('Small team (2-3)', '2-3'),
                ('Medium team (4-8)', '4-8'),
                ('Large team (8+)', '8+'),
                ('❌ Cancel', 'cancel')
            ]
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        return answer['team_size']