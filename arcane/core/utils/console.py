"""Rich console utilities for Arcane.

Provides a shared Console instance and helper functions for consistent
terminal output styling throughout the application.
"""

from rich.console import Console
from rich.panel import Panel


# Shared console instance for the entire application
console = Console()


def success(msg: str) -> None:
    """Print a success message with a green checkmark."""
    console.print(f"[bold green]\u2713[/bold green] {msg}")


def error(msg: str) -> None:
    """Print an error message with a red X."""
    console.print(f"[bold red]\u2717[/bold red] {msg}")


def warning(msg: str) -> None:
    """Print a warning message with a yellow warning sign."""
    console.print(f"[bold yellow]\u26a0[/bold yellow] {msg}")


def info(msg: str) -> None:
    """Print an informational message in dim style."""
    console.print(f"[dim]{msg}[/dim]")


def header(msg: str) -> None:
    """Print a header message in a magenta-bordered panel."""
    console.print(Panel(msg, border_style="magenta"))
