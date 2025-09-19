"""Roadmap class - Container for the entire roadmap structure."""

from typing import List, Dict, Any, Optional
from .project import Project
from .milestone import Milestone
from .epic import Epic
from .story import Story
from .task import Task
from .base import Item


class Roadmap:
    """Container for the entire roadmap structure."""

    def __init__(self, project: Project):
        self.project = project

    def get_all_items(self) -> List[Item]:
        """Get all items in the roadmap as a flat list."""
        items = []
        self._collect_items(self.project, items)
        return items

    def _collect_items(self, item: Item, items_list: List[Item]) -> None:
        """Recursively collect all items in the hierarchy."""
        items_list.append(item)
        for child in item.children:
            self._collect_items(child, items_list)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert roadmap to list of dictionaries for export."""
        return [item.to_dict() for item in self.get_all_items()]

    def get_milestones(self) -> List[Milestone]:
        """Get all milestones in the roadmap."""
        return [item for item in self.project.children if isinstance(item, Milestone)]

    def get_epics(self) -> List[Epic]:
        """Get all epics in the roadmap."""
        epics = []
        for milestone in self.get_milestones():
            epics.extend([item for item in milestone.children if isinstance(item, Epic)])
        return epics

    def get_stories(self) -> List[Story]:
        """Get all stories in the roadmap."""
        stories = []
        for epic in self.get_epics():
            stories.extend([item for item in epic.children if isinstance(item, Story)])
        return stories

    def get_tasks(self) -> List[Task]:
        """Get all tasks in the roadmap."""
        tasks = []
        for story in self.get_stories():
            tasks.extend([item for item in story.children if isinstance(item, Task)])
        return tasks

    def find_item_by_name(self, name: str) -> Optional[Item]:
        """Find an item by its name."""
        for item in self.get_all_items():
            if item.name == name:
                return item
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the roadmap."""
        all_items = self.get_all_items()
        return {
            'total_items': len(all_items),
            'milestones': len(self.get_milestones()),
            'epics': len(self.get_epics()),
            'stories': len(self.get_stories()),
            'tasks': len(self.get_tasks()),
            'total_duration_hours': self.project.calculate_total_duration(),
            'completion_percentage': self.project.get_completion_percentage(),
            'status_breakdown': self._get_status_breakdown(all_items)
        }

    def _get_status_breakdown(self, items: List[Item]) -> Dict[str, int]:
        """Get breakdown of items by status."""
        breakdown = {'Not Started': 0, 'In Progress': 0, 'Completed': 0, 'Blocked': 0, 'Cancelled': 0}
        for item in items:
            if item.status in breakdown:
                breakdown[item.status] += 1
        return breakdown

    def generate_all_content(self, llm_client, idea_content: str, interactive_mode: bool = False, console=None) -> None:
        """Generate content for all items in the roadmap recursively."""
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
        from rich.prompt import Confirm, Prompt

        if console is None:
            console = Console()

        # Get generation order (depth-first: milestones -> epics -> stories)
        generation_items = []
        for milestone in self.project.get_children_by_type('Milestone'):
            generation_items.append(milestone)
            for epic in milestone.get_children_by_type('Epic'):
                generation_items.append(epic)
                for story in epic.get_children_by_type('Story'):
                    generation_items.append(story)
                    # Tasks are generated with stories, so we don't add them separately

        console.print(f"\n[bold green]🚀 Generating {len(generation_items)} items...[/bold green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task("Generating roadmap content...", total=len(generation_items))

            for item in generation_items:
                try:
                    # Update progress
                    progress.update(task, description=f"Generating {item.item_type} {item.id}: {item.name.split(': ', 1)[-1] if ': ' in item.name else item.name}")

                    # Build context
                    parent_context = None
                    if item.parent:
                        parent_context = f"{item.parent.item_type} {item.parent.id}: {item.parent.name.split(': ', 1)[-1] if ': ' in item.parent.name else item.parent.name}"

                    # Generate content for this item
                    item.generate_content(llm_client, idea_content, parent_context, "")

                    # Handle interactive mode
                    if interactive_mode:
                        self._handle_interactive_confirmation(item, console, llm_client, idea_content, parent_context)

                    progress.advance(task)

                except KeyboardInterrupt:
                    console.print("\n[yellow]⚠️ Generation stopped by user[/yellow]")
                    return
                except Exception as e:
                    console.print(f"\n[red]❌ Error generating {item.item_type} {item.id}: {str(e)}[/red]")
                    if Confirm.ask(f"[yellow]Skip {item.item_type} {item.id} and continue?[/yellow]"):
                        from arcane.items.base import ItemStatus
                        item.update_generation_status(ItemStatus.SKIPPED)
                        console.print(f"[yellow]⏭️  Skipped {item.item_type} {item.id}[/yellow]")
                        progress.advance(task)
                        continue
                    else:
                        console.print("[red]🛑 Generation stopped[/red]")
                        return

        console.print(f"\n[green]✅ Generation completed![/green]")

    def _handle_interactive_confirmation(self, item, console, llm_client, idea_content, parent_context):
        """Handle interactive confirmation for an item."""
        from rich.prompt import Prompt

        console.print(f"\n[bold green]✅ Generated {item.item_type} {item.id}: {item.name.split(': ', 1)[-1] if ': ' in item.name else item.name}[/bold green]")

        # Show a preview of the generated content
        if item.content:
            preview = item.content[:300] + "..." if len(item.content) > 300 else item.content
            console.print(f"[dim]Preview: {preview}[/dim]")

        # Ask user for confirmation
        while True:
            choice = Prompt.ask(
                "[cyan]What would you like to do?[/cyan]",
                choices=["continue", "quit", "regenerate"],
                default="continue"
            )

            if choice == "continue":
                break
            elif choice == "quit":
                console.print("[yellow]🛑 Generation stopped by user[/yellow]")
                raise KeyboardInterrupt("User chose to quit generation")
            elif choice == "regenerate":
                console.print(f"[yellow]🔄 Regenerating {item.item_type} {item.id}...[/yellow]")
                # Regenerate the item
                from arcane.items.base import ItemStatus
                item.update_generation_status(ItemStatus.PENDING)
                item.generate_content(llm_client, idea_content, parent_context, "")
                console.print(f"[green]✅ Regenerated {item.item_type} {item.id}[/green]")

                # Show the new content
                if item.content:
                    preview = item.content[:300] + "..." if len(item.content) > 300 else item.content
                    console.print(f"[dim]New Preview: {preview}[/dim]")

    def __repr__(self) -> str:
        stats = self.get_statistics()
        return (f"Roadmap(project='{self.project.name}', "
                f"milestones={stats['milestones']}, "
                f"epics={stats['epics']}, "
                f"stories={stats['stories']}, "
                f"tasks={stats['tasks']})")