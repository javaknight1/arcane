#!/usr/bin/env python3
"""Team expertise level question."""

import inquirer
from ..base_question import BaseQuestion


class TeamExpertiseQuestion(BaseQuestion):
    """Question for team expertise level."""

    @property
    def question_key(self) -> str:
        return "team_expertise"

    @property
    def cli_flag_name(self) -> str:
        return "--team-expertise"

    @property
    def question_text(self) -> str:
        return "Team Expertise Level"

    @property
    def section_title(self) -> str:
        return "Team Assessment"

    def _get_emoji(self) -> str:
        return "🎯"

    def _prompt_user(self):
        """Prompt user for team expertise level."""
        self.console.print("[dim]How would you describe your team's expertise with the planned tech stack?[/dim]")

        choices = [
            ('First time with this tech stack', 'learning'),
            ('Some experience, have built similar projects', 'intermediate'),
            ('Deep expertise, done many similar projects', 'expert'),
            ('Mixed expertise levels across team', 'mixed'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'team_expertise',
            message="Team expertise level",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('team_expertise') == 'cancel':
            return 'cancel'

        return answer.get('team_expertise')

    def _format_value_for_display(self, value):
        """Format the expertise level for display."""
        expertise_map = {
            'learning': 'Learning (First time with tech stack)',
            'intermediate': 'Intermediate (Some experience)',
            'expert': 'Expert (Deep expertise)',
            'mixed': 'Mixed (Various expertise levels)'
        }
        return expertise_map.get(value, str(value))