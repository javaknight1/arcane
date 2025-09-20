#!/usr/bin/env python3
"""Base question class for all user preference questions."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from rich.console import Console


class BaseQuestion(ABC):
    """Abstract base class for all user preference questions."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._value = None
        self._is_answered = False

    @property
    @abstractmethod
    def question_key(self) -> str:
        """Unique key for this question (used for CLI flags and storage)."""
        pass

    @property
    @abstractmethod
    def cli_flag_name(self) -> str:
        """Name of the CLI flag for this question."""
        pass

    @property
    @abstractmethod
    def question_text(self) -> str:
        """The text displayed to the user for this question."""
        pass

    @property
    @abstractmethod
    def section_title(self) -> str:
        """The section this question belongs to."""
        pass

    @property
    def value(self) -> Any:
        """Get the current value of this question."""
        return self._value

    @property
    def is_answered(self) -> bool:
        """Check if this question has been answered."""
        return self._is_answered

    def set_value_from_flag(self, flag_value: Any) -> None:
        """Set the value from a CLI flag."""
        if flag_value is not None:
            self._value = self._process_flag_value(flag_value)
            self._is_answered = True
            self._display_flag_value()

    def ask_user(self) -> Any:
        """Ask the user this question if not already answered."""
        if self._is_answered:
            return self._value

        try:
            answer = self._prompt_user()
            if answer is not None and answer != 'cancel':
                self._value = self._process_user_answer(answer)
                self._is_answered = True
                return self._value
            else:
                raise KeyboardInterrupt()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Question cancelled[/yellow]")
            raise

    def reset(self) -> None:
        """Reset the question to unanswered state."""
        self._value = None
        self._is_answered = False

    @abstractmethod
    def _prompt_user(self) -> Any:
        """Show the question to the user and get their answer."""
        pass

    def _process_flag_value(self, flag_value: Any) -> Any:
        """Process the value from CLI flag. Override if needed."""
        return flag_value

    def _process_user_answer(self, answer: Any) -> Any:
        """Process the user's answer. Override if needed."""
        return answer

    def _display_flag_value(self) -> None:
        """Display that a value was set from CLI flag."""
        emoji = self._get_emoji()
        display_value = self._format_value_for_display(self._value)
        self.console.print(f"[green]{emoji} {self.question_text}: {display_value} (provided via flag)[/green]")

    def _get_emoji(self) -> str:
        """Get emoji for this question type. Override in subclasses."""
        return "⚙️"

    def _format_value_for_display(self, value: Any) -> str:
        """Format value for display. Override if needed."""
        if isinstance(value, list):
            return ', '.join(str(v) for v in value)
        return str(value)

    def get_validation_error(self) -> Optional[str]:
        """Validate current value. Return error message if invalid."""
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template/storage."""
        return {
            self.question_key: self._value
        }