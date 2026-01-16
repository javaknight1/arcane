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
        self.console.print("[dim]You can choose a predefined range or enter a specific number[/dim]")

        question = inquirer.List(
            'team_size_choice',
            message="How would you like to specify team size?",
            choices=[
                ('Choose from ranges', 'ranges'),
                ('Enter specific number', 'specific'),
                ('❌ Cancel', 'cancel')
            ]
        )

        choice_answer = inquirer.prompt([question])
        if not choice_answer or choice_answer['team_size_choice'] == 'cancel':
            return 'cancel'

        if choice_answer['team_size_choice'] == 'ranges':
            range_question = inquirer.List(
                'team_size',
                message="Development team size",
                choices=[
                    ('Solo developer', '1'),
                    ('Small team (2-3)', '2-3'),
                    ('Medium team (4-8)', '4-8'),
                    ('Large team (9-15)', '9-15'),
                    ('Very large team (16-30)', '16-30'),
                    ('Enterprise team (30+)', '30+'),
                    ('❌ Cancel', 'cancel')
                ]
            )

            range_answer = inquirer.prompt([range_question])
            if not range_answer or range_answer['team_size'] == 'cancel':
                return 'cancel'

            return range_answer['team_size']

        else:  # specific number
            while True:
                specific_question = inquirer.Text(
                    'team_size_number',
                    message="Enter the exact number of team members (1-100)"
                )

                specific_answer = inquirer.prompt([specific_question])
                if not specific_answer:
                    return 'cancel'

                try:
                    team_number = int(specific_answer['team_size_number'])
                    if 1 <= team_number <= 100:
                        return str(team_number)
                    else:
                        self.console.print("[red]Please enter a number between 1 and 100[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a valid number[/red]")