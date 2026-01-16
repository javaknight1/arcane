"""CLI command for interactive refinement of roadmap items.

Allows users to refine specific items with feedback without regenerating everything.
"""

import json
import argparse
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table

from arcane.engines.generation.refinement_engine import RefinementEngine, RefinementRecord
from arcane.clients.factory import LLMClientFactory
from arcane.items.base import Item
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class RefineCommand:
    """Command for interactive refinement of roadmap items."""

    def __init__(self):
        self.console = Console()
        self.engine: Optional[RefinementEngine] = None
        self.roadmap_data: Optional[Dict[str, Any]] = None
        self.items_by_id: Dict[str, Dict[str, Any]] = {}
        self.modified: bool = False

    def setup_parser(self, subparsers) -> argparse.ArgumentParser:
        """Setup argument parser for refine command.

        Args:
            subparsers: Subparsers from main argument parser

        Returns:
            Configured argument parser
        """
        parser = subparsers.add_parser(
            'refine',
            help='Refine specific items in a roadmap',
            description='Interactive refinement of roadmap items with version control',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  arcane refine roadmap.json                    # Interactive mode
  arcane refine roadmap.json -i 1.0.1           # Refine specific item
  arcane refine roadmap.json -i 1.0.1 --revert 0  # Revert to original
  arcane refine roadmap.json --history          # Show refinement history
            """
        )

        parser.add_argument(
            'roadmap_file',
            help='Path to roadmap JSON file'
        )

        parser.add_argument(
            '-i', '--item',
            help='Item ID to refine (e.g., 1.0.1)'
        )

        parser.add_argument(
            '-I', '--interactive',
            action='store_true',
            help='Interactive mode - browse and refine items'
        )

        parser.add_argument(
            '--feedback',
            help='Feedback for refinement (non-interactive mode)'
        )

        parser.add_argument(
            '--revert',
            type=int,
            metavar='VERSION',
            help='Revert item to specific version (0 = original)'
        )

        parser.add_argument(
            '--history',
            action='store_true',
            help='Show refinement history'
        )

        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare all versions of an item'
        )

        parser.add_argument(
            '--provider',
            choices=['claude', 'openai', 'gemini'],
            default='claude',
            help='LLM provider to use (default: claude)'
        )

        parser.add_argument(
            '--output',
            '-o',
            help='Output file path (default: overwrites input)'
        )

        parser.add_argument(
            '--history-file',
            help='Path to save/load refinement history'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )

        return parser

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the refine command.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code (0 = success)
        """
        try:
            # Load roadmap
            if not self._load_roadmap(args.roadmap_file):
                return 1

            # Initialize refinement engine
            llm_client = LLMClientFactory.create(args.provider)
            self.engine = RefinementEngine(llm_client)

            # Load history if specified
            if args.history_file and Path(args.history_file).exists():
                self.engine.import_history(args.history_file)
                self.console.print(f"[dim]Loaded history from {args.history_file}[/dim]")

            # Determine mode
            if args.history:
                self._show_all_history()
            elif args.compare and args.item:
                self._compare_versions(args.item)
            elif args.revert is not None and args.item:
                self._revert_item(args.item, args.revert)
            elif args.item and args.feedback:
                self._refine_single_item(args.item, args.feedback)
            elif args.interactive or not args.item:
                self._interactive_mode()
            elif args.item:
                self._refine_item_prompt(args.item)

            # Save if modified
            if self.modified and not args.dry_run:
                output_path = args.output or args.roadmap_file
                if Confirm.ask(f"Save changes to {output_path}?", default=True):
                    self._save_roadmap(output_path)

                    # Save history if specified
                    if args.history_file:
                        self.engine.export_history(args.history_file)
                        self.console.print(f"[green]History saved to {args.history_file}[/green]")
            elif args.dry_run and self.modified:
                self.console.print("[yellow]Dry run - changes not saved[/yellow]")

            return 0

        except FileNotFoundError as e:
            self.console.print(f"[red]File not found: {e}[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            logger.exception("Error in refine command")
            return 1

    def _load_roadmap(self, filepath: str) -> bool:
        """Load roadmap from JSON file.

        Args:
            filepath: Path to roadmap file

        Returns:
            True if loaded successfully
        """
        path = Path(filepath)
        if not path.exists():
            self.console.print(f"[red]File not found: {filepath}[/red]")
            return False

        with open(path, 'r', encoding='utf-8') as f:
            self.roadmap_data = json.load(f)

        # Build item lookup
        self._build_item_lookup(self.roadmap_data)

        self.console.print(f"[green]Loaded roadmap from {filepath}[/green]")
        self.console.print(f"[dim]Found {len(self.items_by_id)} items[/dim]")

        return True

    def _build_item_lookup(self, data: Dict[str, Any], parent_path: str = "") -> None:
        """Build lookup dictionary of all items.

        Args:
            data: Roadmap data dictionary
            parent_path: Parent item path for context
        """
        # Handle milestones array
        milestones = data.get('milestones', [])
        for milestone in milestones:
            m_id = milestone.get('id', '')
            self.items_by_id[m_id] = milestone

            # Process epics
            for epic in milestone.get('epics', []):
                e_id = epic.get('id', '')
                self.items_by_id[e_id] = epic

                # Process stories
                for story in epic.get('stories', []):
                    s_id = story.get('id', '')
                    self.items_by_id[s_id] = story

                    # Process tasks
                    for task in story.get('tasks', []):
                        t_id = task.get('id', '')
                        self.items_by_id[t_id] = task

    def _save_roadmap(self, filepath: str) -> None:
        """Save roadmap to JSON file.

        Args:
            filepath: Path to save file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        self.roadmap_data['last_modified'] = datetime.now().isoformat()

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.roadmap_data, f, indent=2)

        self.console.print(f"[green]Saved roadmap to {filepath}[/green]")

    def _interactive_mode(self) -> None:
        """Run interactive refinement mode."""
        self.console.print(Panel(
            "[bold cyan]Interactive Refinement Mode[/bold cyan]\n"
            "Browse and refine roadmap items with AI assistance.\n"
            "Type 'help' for commands, 'done' to exit.",
            border_style="cyan"
        ))

        while True:
            # Display item tree
            self._display_item_tree()

            # Get command
            cmd = Prompt.ask(
                "\n[cyan]Command[/cyan]",
                default="done"
            ).strip().lower()

            if cmd == 'done' or cmd == 'exit' or cmd == 'q':
                break
            elif cmd == 'help':
                self._show_help()
            elif cmd == 'tree':
                self._display_item_tree(detailed=True)
            elif cmd == 'history':
                self._show_all_history()
            elif cmd == 'summary':
                self._show_summary()
            elif cmd.startswith('view '):
                item_id = cmd[5:].strip()
                self._view_item(item_id)
            elif cmd.startswith('refine '):
                item_id = cmd[7:].strip()
                self._refine_item_prompt(item_id)
            elif cmd.startswith('revert '):
                parts = cmd[7:].strip().split()
                if len(parts) == 2:
                    self._revert_item(parts[0], int(parts[1]))
                else:
                    self.console.print("[red]Usage: revert <item_id> <version>[/red]")
            elif cmd.startswith('compare '):
                item_id = cmd[8:].strip()
                self._compare_versions(item_id)
            else:
                # Assume it's an item ID
                if cmd in self.items_by_id:
                    self._refine_item_prompt(cmd)
                else:
                    self.console.print(f"[red]Unknown command or item: {cmd}[/red]")
                    self.console.print("[dim]Type 'help' for available commands[/dim]")

    def _show_help(self) -> None:
        """Show help for interactive mode."""
        help_text = """
[bold]Available Commands:[/bold]

  [cyan]<item_id>[/cyan]       Refine the specified item (e.g., 1.0.1)
  [cyan]view <id>[/cyan]       View item details without refining
  [cyan]refine <id>[/cyan]     Same as entering item ID
  [cyan]revert <id> <v>[/cyan] Revert item to version v (0 = original)
  [cyan]compare <id>[/cyan]    Compare all versions of an item
  [cyan]tree[/cyan]            Show detailed item tree
  [cyan]history[/cyan]         Show all refinement history
  [cyan]summary[/cyan]         Show refinement summary
  [cyan]help[/cyan]            Show this help
  [cyan]done[/cyan]            Exit and optionally save
"""
        self.console.print(Panel(help_text, title="Help", border_style="blue"))

    def _display_item_tree(self, detailed: bool = False) -> None:
        """Display roadmap items as a tree.

        Args:
            detailed: Whether to show detailed information
        """
        if not self.roadmap_data:
            return

        tree = Tree("[bold]Roadmap[/bold]")

        for milestone in self.roadmap_data.get('milestones', []):
            m_id = milestone.get('id', '?')
            m_name = milestone.get('name', 'Unnamed')
            version = self._get_version_indicator(m_id)
            m_branch = tree.add(f"[yellow]{m_id}[/yellow] {m_name} {version}")

            for epic in milestone.get('epics', []):
                e_id = epic.get('id', '?')
                e_name = epic.get('name', 'Unnamed')
                version = self._get_version_indicator(e_id)
                e_branch = m_branch.add(f"[blue]{e_id}[/blue] {e_name} {version}")

                if detailed:
                    for story in epic.get('stories', []):
                        s_id = story.get('id', '?')
                        s_name = story.get('name', 'Unnamed')
                        version = self._get_version_indicator(s_id)
                        s_branch = e_branch.add(f"[green]{s_id}[/green] {s_name} {version}")

                        for task in story.get('tasks', []):
                            t_id = task.get('id', '?')
                            t_name = task.get('name', 'Unnamed')
                            version = self._get_version_indicator(t_id)
                            s_branch.add(f"[dim]{t_id}[/dim] {t_name} {version}")

        self.console.print(tree)

    def _get_version_indicator(self, item_id: str) -> str:
        """Get version indicator for an item.

        Args:
            item_id: Item ID

        Returns:
            Version indicator string
        """
        if self.engine and item_id in self.engine.history:
            version = len(self.engine.history[item_id])
            return f"[cyan](v{version})[/cyan]"
        return ""

    def _view_item(self, item_id: str) -> None:
        """View item details.

        Args:
            item_id: Item ID to view
        """
        if item_id not in self.items_by_id:
            self.console.print(f"[red]Item not found: {item_id}[/red]")
            return

        item = self.items_by_id[item_id]

        # Build display
        name = item.get('name', 'Unnamed')
        content = item.get('content', '')
        status = item.get('status', 'Unknown')

        self.console.print(Panel(
            f"[bold]{name}[/bold]\n\n"
            f"[dim]Status:[/dim] {status}\n\n"
            f"[dim]Content:[/dim]\n{content[:500]}{'...' if len(content) > 500 else ''}",
            title=f"Item {item_id}",
            border_style="green"
        ))

    def _refine_item_prompt(self, item_id: str) -> None:
        """Prompt user for feedback and refine item.

        Args:
            item_id: Item ID to refine
        """
        if item_id not in self.items_by_id:
            self.console.print(f"[red]Item not found: {item_id}[/red]")
            return

        item = self.items_by_id[item_id]
        name = item.get('name', 'Unnamed')
        content = item.get('content', item.get('description', ''))

        if not content:
            self.console.print(f"[red]Item {item_id} has no content to refine[/red]")
            return

        # Show current content
        self.console.print(f"\n[cyan]Current content for {item_id}:[/cyan]")
        self.console.print(Panel(
            content[:1000] + ('...' if len(content) > 1000 else ''),
            title=name,
            border_style="dim"
        ))

        # Get feedback
        feedback = Prompt.ask("\n[yellow]What would you like to improve?[/yellow]")
        if not feedback:
            self.console.print("[dim]No feedback provided, skipping[/dim]")
            return

        # Refine
        self.console.print("\n[cyan]Generating refined content...[/cyan]")

        # Create a mock Item for the engine
        mock_item = MockRefinementItem(
            item_id=item_id,
            name=name,
            item_type=self._get_item_type(item_id),
            content=content
        )

        try:
            new_content = self.engine.refine_item(
                mock_item,
                feedback,
                apply_immediately=False
            )

            # Show refined content
            self.console.print(f"\n[green]Refined content:[/green]")
            self.console.print(Panel(
                new_content[:1000] + ('...' if len(new_content) > 1000 else ''),
                title=f"Refined {name}",
                border_style="green"
            ))

            # Confirm
            if Confirm.ask("Accept this refinement?", default=True):
                item['content'] = new_content
                self.modified = True
                self.console.print("[green]Applied refinement[/green]")
            else:
                # Remove from history since rejected
                if item_id in self.engine.history:
                    self.engine.history[item_id].pop()
                self.console.print("[yellow]Refinement rejected[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error refining: {e}[/red]")

    def _refine_single_item(self, item_id: str, feedback: str) -> None:
        """Refine a single item with provided feedback.

        Args:
            item_id: Item ID to refine
            feedback: Feedback for refinement
        """
        if item_id not in self.items_by_id:
            self.console.print(f"[red]Item not found: {item_id}[/red]")
            return

        item = self.items_by_id[item_id]
        content = item.get('content', item.get('description', ''))

        if not content:
            self.console.print(f"[red]Item {item_id} has no content to refine[/red]")
            return

        mock_item = MockRefinementItem(
            item_id=item_id,
            name=item.get('name', ''),
            item_type=self._get_item_type(item_id),
            content=content
        )

        self.console.print(f"[cyan]Refining {item_id}...[/cyan]")
        new_content = self.engine.refine_item(mock_item, feedback, apply_immediately=False)

        item['content'] = new_content
        self.modified = True

        self.console.print(f"[green]Refined {item_id}[/green]")

    def _revert_item(self, item_id: str, version: int) -> None:
        """Revert item to a previous version.

        Args:
            item_id: Item ID to revert
            version: Version number to revert to
        """
        if item_id not in self.items_by_id:
            self.console.print(f"[red]Item not found: {item_id}[/red]")
            return

        try:
            content = self.engine.revert_to_version(item_id, version)
            self.items_by_id[item_id]['content'] = content
            self.modified = True
            self.console.print(f"[green]Reverted {item_id} to version {version}[/green]")
        except ValueError as e:
            self.console.print(f"[red]{e}[/red]")

    def _compare_versions(self, item_id: str) -> None:
        """Compare all versions of an item.

        Args:
            item_id: Item ID to compare
        """
        comparison = self.engine.compare_versions(item_id)
        if not comparison:
            self.console.print(f"[yellow]No refinement history for {item_id}[/yellow]")
            return

        table = Table(title=f"Version History for {item_id}")
        table.add_column("Version", style="cyan")
        table.add_column("Feedback", style="white")
        table.add_column("Timestamp", style="dim")
        table.add_column("Length", style="green")

        # Add original (version 0)
        table.add_row(
            "0 (original)",
            "-",
            "-",
            str(comparison['original_length'])
        )

        for v in comparison['versions']:
            table.add_row(
                str(v['version']),
                v['feedback'][:50] + '...' if len(v['feedback']) > 50 else v['feedback'],
                v['timestamp'][:19],
                str(v['content_length_after'])
            )

        self.console.print(table)

    def _show_all_history(self) -> None:
        """Show all refinement history."""
        summary = self.engine.get_summary()

        if summary['total_refinements'] == 0:
            self.console.print("[yellow]No refinement history[/yellow]")
            return

        table = Table(title="Refinement History Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Refinements", str(summary['total_refinements']))
        table.add_row("Items Refined", str(summary['items_refined']))
        table.add_row("Avg per Item", str(summary['average_refinements_per_item']))
        if summary['most_refined_item']:
            table.add_row("Most Refined", f"{summary['most_refined_item']} ({summary['most_refined_count']}x)")

        self.console.print(table)

        # Show detailed history
        if Confirm.ask("Show detailed history?", default=False):
            for item_id in self.engine.history:
                self._compare_versions(item_id)

    def _show_summary(self) -> None:
        """Show refinement summary."""
        summary = self.engine.get_summary()

        self.console.print(Panel(
            f"[cyan]Total Refinements:[/cyan] {summary['total_refinements']}\n"
            f"[cyan]Items Refined:[/cyan] {summary['items_refined']}\n"
            f"[cyan]Avg per Item:[/cyan] {summary['average_refinements_per_item']}\n"
            f"[cyan]Most Refined:[/cyan] {summary['most_refined_item'] or 'N/A'}",
            title="Refinement Summary",
            border_style="cyan"
        ))

    def _get_item_type(self, item_id: str) -> str:
        """Determine item type from ID format.

        Args:
            item_id: Item ID

        Returns:
            Item type string
        """
        parts = item_id.split('.')
        if len(parts) == 1:
            return "Milestone"
        elif len(parts) == 2:
            return "Epic"
        elif len(parts) == 3:
            return "Story"
        elif len(parts) == 4:
            return "Task"
        return "Item"


class MockRefinementItem:
    """Mock item class for refinement engine compatibility."""

    def __init__(self, item_id: str, name: str, item_type: str, content: str):
        self.id = item_id
        self.name = name
        self.item_type = item_type
        self.content = content
        self.description = content
        self.children = []
        self.parent = None
        self.technical_requirements = ""
        self.benefits = ""
        self.updated_at = datetime.now()

    def get_path(self) -> str:
        return self.name


def create_refine_command() -> RefineCommand:
    """Factory function to create RefineCommand instance.

    Returns:
        RefineCommand instance
    """
    return RefineCommand()
