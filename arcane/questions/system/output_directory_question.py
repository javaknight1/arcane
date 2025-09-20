#!/usr/bin/env python3
"""Output directory selection question."""

from pathlib import Path
from rich.prompt import Prompt, Confirm
from ..base_question import BaseQuestion


class OutputDirectoryQuestion(BaseQuestion):
    """Question for output directory selection."""

    @property
    def question_key(self) -> str:
        return "output_directory"

    @property
    def cli_flag_name(self) -> str:
        return "--output-dir"

    @property
    def question_text(self) -> str:
        return "Output Directory"

    @property
    def section_title(self) -> str:
        return "System Configuration"

    def _get_emoji(self) -> str:
        return "📁"

    def _prompt_user(self):
        """Prompt user for output directory selection."""
        self.console.print("[dim]Specify where to save generated files (optional)[/dim]")

        while True:
            dir_path = Prompt.ask("📁 Enter output directory path (or press Enter to skip)", default="")

            if not dir_path:
                if Confirm.ask("Continue without saving output files?", default=True):
                    return None
                continue

            if dir_path.lower() == 'cancel':
                return 'cancel'

            path = Path(dir_path).expanduser()

            # Try to create directory if it doesn't exist
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.console.print(f"[green]✅ Output directory ready: {path}[/green]")
                return str(path)
            except Exception as e:
                self.console.print(f"[red]❌ Could not create directory: {e}[/red]")
                if Confirm.ask("Try a different path?", default=True):
                    continue
                else:
                    return None

    def _format_value_for_display(self, value):
        """Format the directory path for display."""
        if value is None:
            return "No output directory (files will not be saved)"
        return str(value)