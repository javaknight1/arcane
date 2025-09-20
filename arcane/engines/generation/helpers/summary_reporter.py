"""Generation summary reporting helper for roadmap generation."""

from typing import Dict, Any
from rich.console import Console
from rich.table import Table

from arcane.protocols.display_protocols import ConsoleDisplayProtocol, ProgressReporterProtocol
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class GenerationSummaryReporter(ProgressReporterProtocol):
    """Handles generation summary reporting and display."""

    def __init__(self, console: ConsoleDisplayProtocol):
        self.console = console

    def show_generation_summary(self, summary: Dict[str, Any]) -> None:
        """Show generation results summary."""
        self.console.print("\n[bold cyan]📈 First Milestone Generation Summary[/bold cyan]")

        table = Table(title="First Milestone Results")
        table.add_column("Item Type", style="cyan")
        table.add_column("Total", style="white")
        table.add_column("Generated", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Skipped", style="yellow")

        # Calculate attempted items (only count items that were actually processed)
        attempted_items = summary['generated'] + summary['failed'] + summary['skipped']

        for item_type, counts in summary['by_type'].items():
            # Only show rows for item types that had attempts
            attempted_for_type = counts['generated'] + counts['failed'] + counts['skipped']
            if attempted_for_type > 0:
                table.add_row(
                    item_type,
                    str(counts['total']),
                    str(counts['generated']),
                    str(counts['failed']),
                    str(counts['skipped'])
                )

        self.console.print(table)

        # Overall status based on attempted items only
        if attempted_items > 0:
            success_rate = (summary['generated'] / attempted_items) * 100
            if success_rate >= 90:
                status_style = "green"
                status_icon = "✅"
            elif success_rate >= 70:
                status_style = "yellow"
                status_icon = "⚠️"
            else:
                status_style = "red"
                status_icon = "❌"

            self.console.print(f"\n[{status_style}]{status_icon} Generation Success Rate: {success_rate:.1f}% ({summary['generated']}/{attempted_items} items)[/{status_style}]")
        else:
            self.console.print("\n[yellow]⚠️ No items were processed[/yellow]")

        # Show note about any unprocessed milestones
        remaining_milestones = summary['by_type']['Milestone']['total'] - summary['by_type']['Milestone']['generated']
        if remaining_milestones > 0:
            self.console.print(f"\n[dim]📝 Note: {remaining_milestones} milestones were not successfully generated[/dim]")

    def show_cost_breakdown(self, cost_data: Dict[str, Any]) -> None:
        """Display cost breakdown information."""
        # Implementation can be added when needed
        pass

    def show_outline_summary(
        self,
        milestone_count: int,
        epic_count: int,
        story_count: int,
        task_count: int
    ) -> None:
        """Display outline summary statistics."""
        self.console.print(f"\n[green]✅ Generated outline with:[/green]")
        self.console.print(f"  📊 {milestone_count} milestones")
        self.console.print(f"  📁 {epic_count} epics")
        self.console.print(f"  📄 {story_count} stories")
        self.console.print(f"  ✅ {task_count} tasks")

    def show_validation_issues(self, issues: list[str]) -> None:
        """Display validation issues."""
        self.console.print("[red]❌ Structure validation issues:[/red]")
        for issue in issues:
            self.console.print(f"[red]  • {issue}[/red]")