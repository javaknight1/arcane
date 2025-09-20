"""Protocol definitions for display and console interfaces."""

from typing import Protocol, Any, Optional, Dict


class ConsoleDisplayProtocol(Protocol):
    """Protocol for console display functionality."""

    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[str] = None,
        justify: Optional[str] = None,
        overflow: Optional[str] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: bool = True,
        soft_wrap: Optional[bool] = None,
        new_line_start: bool = False
    ) -> None:
        """Print objects to the console."""
        ...

    def rule(
        self,
        title: str = "",
        *,
        characters: str = "─",
        style: str = "rule.line",
        end: str = "\n",
        align: str = "center"
    ) -> None:
        """Print a horizontal rule."""
        ...

    def status(
        self,
        status: str,
        *,
        spinner: str = "dots",
        speed: float = 1.0,
        refresh_per_second: float = 12.5
    ) -> 'StatusContext':
        """Create a status context manager."""
        ...


class StatusContext(Protocol):
    """Protocol for status context manager."""

    def __enter__(self) -> 'StatusContext':
        """Enter status context."""
        ...

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit status context."""
        ...

    def update(self, status: str) -> None:
        """Update status message."""
        ...


class ProgressReporterProtocol(Protocol):
    """Protocol for progress reporting functionality."""

    def show_generation_summary(self, summary: Dict[str, Any]) -> None:
        """Display generation results summary."""
        ...

    def show_cost_breakdown(self, cost_data: Dict[str, Any]) -> None:
        """Display cost breakdown information."""
        ...

    def show_outline_summary(
        self,
        milestone_count: int,
        epic_count: int,
        story_count: int,
        task_count: int
    ) -> None:
        """Display outline summary statistics."""
        ...

    def show_validation_issues(self, issues: list[str]) -> None:
        """Display validation issues."""
        ...


class UserInteractionProtocol(Protocol):
    """Protocol for user interaction functionality."""

    def confirm(
        self,
        prompt: str,
        default: bool = True,
        show_default: bool = True,
        show_choices: bool = True
    ) -> bool:
        """Get user confirmation."""
        ...

    def ask_choice(
        self,
        prompt: str,
        choices: list[str],
        default: Optional[str] = None,
        show_default: bool = True,
        show_choices: bool = True
    ) -> str:
        """Ask user to choose from options."""
        ...

    def ask_text(
        self,
        prompt: str,
        default: str = "",
        show_default: bool = True,
        password: bool = False
    ) -> str:
        """Ask user for text input."""
        ...