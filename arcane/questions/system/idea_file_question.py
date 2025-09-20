#!/usr/bin/env python3
"""Idea file selection question."""

import inquirer
from pathlib import Path
from rich.prompt import Prompt, Confirm
from ..base_question import BaseQuestion


class IdeaFileQuestion(BaseQuestion):
    """Question for idea file selection."""

    @property
    def question_key(self) -> str:
        return "idea_file"

    @property
    def cli_flag_name(self) -> str:
        return "--idea-file"

    @property
    def question_text(self) -> str:
        return "Idea File"

    @property
    def section_title(self) -> str:
        return "Project Input"

    def _get_emoji(self) -> str:
        return "📁"

    def _prompt_user(self):
        """Prompt user for idea file selection."""
        self.console.print("[dim]Provide a text file describing your project idea (optional)[/dim]")

        while True:
            file_path = Prompt.ask("📁 Enter path to your idea text file (or press Enter to skip)", default="")

            if not file_path:
                if Confirm.ask("Continue without idea file?", default=True):
                    return None
                continue

            if file_path.lower() == 'cancel':
                return 'cancel'

            path = Path(file_path).expanduser()
            if path.exists() and path.is_file():
                self.console.print(f"[green]✅ Found file: {path}[/green]")
                return str(path)
            else:
                self.console.print(f"[red]❌ File not found: {path}[/red]")
                retry_choice = inquirer.prompt([
                    inquirer.List(
                        'action',
                        message="What would you like to do?",
                        choices=[
                            ('Try again', 'retry'),
                            ('Skip file and continue', 'skip'),
                            ('❌ Cancel and exit', 'cancel')
                        ]
                    )
                ])

                if not retry_choice or retry_choice.get('action') == 'cancel':
                    return 'cancel'
                elif retry_choice.get('action') == 'skip':
                    return None

    def _format_value_for_display(self, value):
        """Format the file path for display."""
        if value is None:
            return "No file (using default idea content)"
        return str(value)