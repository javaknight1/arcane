"""Recursive roadmap generator that processes items individually."""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt

from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import Item, ItemStatus
from arcane.engines.parsing.outline_parser import OutlineParser
# IdeaProcessor removed - using simplified processing


class RecursiveRoadmapGenerator:
    """Generates roadmap content by processing each item individually."""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.console = Console()
        self.outline_parser = OutlineParser()

    def generate_from_outline(self, outline_content: str, idea_content: str, interactive_mode: bool = False) -> List[Milestone]:
        """Generate complete roadmap from outline by processing each item recursively."""

        # Parse outline into item objects
        self.console.print("\n[cyan]📊 Parsing outline structure...[/cyan]")
        milestones = self.outline_parser.parse_outline(outline_content)

        # Validate structure
        issues = self.outline_parser.validate_structure(milestones)
        if issues:
            self.console.print("[red]❌ Structure validation issues found:[/red]")
            for issue in issues:
                self.console.print(f"[red]  • {issue}[/red]")
            return milestones

        # Show structure summary
        item_counts = self.outline_parser.count_items(milestones)
        self.console.print(f"[green]✅ Parsed {item_counts['milestones']} milestones, "
                          f"{item_counts['epics']} epics, {item_counts['stories']} stories, "
                          f"{item_counts['tasks']} tasks[/green]")

        # Process idea content (simplified processing)
        project_context = f"Project Idea: {idea_content}"

        # Generate content for each item
        self._generate_all_items(milestones, project_context, interactive_mode)

        return milestones

    def _generate_all_items(self, milestones: List[Milestone], project_context: str, interactive_mode: bool = False) -> None:
        """Generate content for all items in the roadmap."""

        # Get generation order (milestones, then epics, then stories+tasks)
        generation_items = []
        for milestone in milestones:
            generation_items.append(milestone)
            for epic in milestone.get_children_by_type('Epic'):
                generation_items.append(epic)
                for story in epic.get_children_by_type('Story'):
                    generation_items.append(story)

        total_items = len(generation_items)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        ) as progress:

            task = progress.add_task(
                "Generating roadmap content...",
                total=total_items
            )

            for item in generation_items:
                try:
                    self._generate_single_item(item, project_context, progress, task, milestones, interactive_mode)
                    progress.advance(task)

                except Exception as e:
                    self.console.print(f"\n[red]❌ Error generating {item.item_type} {item.id}: {str(e)}[/red]")

                    # Ask user what to do
                    if Confirm.ask(f"[yellow]Skip {item.item_type} {item.id} and continue?[/yellow]"):
                        item.update_generation_status(ItemStatus.SKIPPED)
                        self.console.print(f"[yellow]⏭️  Skipped {item.item_type} {item.id}[/yellow]")
                        progress.advance(task)
                        continue
                    else:
                        self.console.print("[red]🛑 Generation stopped[/red]")
                        break

    def _generate_single_item(self, item: Item, project_context: str, progress: Progress, task, milestones: List[Milestone], interactive_mode: bool = False) -> None:
        """Generate content for a single item with full roadmap context."""

        # Update progress description
        progress.update(task, description=f"Generating {item.item_type} {item.id}: {item.name.split(': ', 1)[-1] if ': ' in item.name else item.name}")

        # Mark as generating
        item.update_generation_status(ItemStatus.GENERATING)

        # Build comprehensive context
        parent_context = None
        if item.parent:
            parent_context = f"{item.parent.item_type} {item.parent.id}: {item.parent.name.split(': ', 1)[-1] if ': ' in item.parent.name else item.parent.name}"

        # Build full roadmap context for better coherence
        roadmap_context = self._build_roadmap_context(milestones, item)

        # Generate prompt with enhanced context
        prompt = item.generate_prompt(project_context, parent_context, roadmap_context)

        # Call LLM
        response = self.llm_client.generate(prompt)

        # Parse response and update item
        item.parse_content(response)

        # For stories, also update their tasks from the response
        if isinstance(item, Story):
            # Tasks are automatically updated by the story's parse_content method
            for task in item.get_children_by_type('Task'):
                if task.generation_status == ItemStatus.PENDING:
                    task.update_generation_status(ItemStatus.GENERATED)

        # Show generated content and ask for user confirmation (if interactive mode)
        if interactive_mode:
            self._show_item_confirmation(item, progress, task)

    def get_generation_summary(self, milestones: List[Milestone]) -> Dict[str, Any]:
        """Get summary of generation results."""
        summary = {
            'total_items': 0,
            'generated': 0,
            'failed': 0,
            'skipped': 0,
            'pending': 0,
            'by_type': {
                'Milestone': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0},
                'Epic': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0},
                'Story': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0},
                'Task': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0}
            }
        }

        for milestone in milestones:
            self._count_item_status(milestone, summary)
            for epic in milestone.get_children_by_type('Epic'):
                self._count_item_status(epic, summary)
                for story in epic.get_children_by_type('Story'):
                    self._count_item_status(story, summary)
                    for task in story.get_children_by_type('Task'):
                        self._count_item_status(task, summary)

        return summary

    def _count_item_status(self, item: Item, summary: Dict[str, Any]) -> None:
        """Count item status for summary."""
        summary['total_items'] += 1
        summary['by_type'][item.item_type]['total'] += 1

        if item.generation_status == ItemStatus.GENERATED:
            summary['generated'] += 1
            summary['by_type'][item.item_type]['generated'] += 1
        elif item.generation_status == ItemStatus.FAILED:
            summary['failed'] += 1
            summary['by_type'][item.item_type]['failed'] += 1
        elif item.generation_status == ItemStatus.SKIPPED:
            summary['skipped'] += 1
            summary['by_type'][item.item_type]['skipped'] += 1
        else:
            summary['pending'] += 1

    def export_to_markdown(self, milestones: List[Milestone]) -> str:
        """Export generated roadmap to markdown format."""
        lines = []

        for milestone in milestones:
            if milestone.content:
                lines.append(milestone.content)
                lines.append("")

            for epic in milestone.get_children_by_type('Epic'):
                if epic.content:
                    lines.append(epic.content)
                    lines.append("")

                for story in epic.get_children_by_type('Story'):
                    if story.content:
                        lines.append(story.content)
                        lines.append("")

        return "\n".join(lines)

    def save_progress(self, milestones: List[Milestone], filepath: str) -> None:
        """Save current generation progress to file (for future resume functionality)."""
        import json
        from datetime import datetime

        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'milestones': []
        }

        for milestone in milestones:
            milestone_data = {
                'id': milestone.id,
                'name': milestone.name,
                'status': milestone.generation_status.value,
                'content': milestone.content,
                'epics': []
            }

            for epic in milestone.get_children_by_type('Epic'):
                epic_data = {
                    'id': epic.id,
                    'name': epic.name,
                    'status': epic.generation_status.value,
                    'content': epic.content,
                    'stories': []
                }

                for story in epic.get_children_by_type('Story'):
                    story_data = {
                        'id': story.id,
                        'name': story.name,
                        'status': story.generation_status.value,
                        'content': story.content,
                        'tasks': []
                    }

                    for task in story.get_children_by_type('Task'):
                        task_data = {
                            'id': task.id,
                            'name': task.name,
                            'status': task.generation_status.value,
                            'content': task.content
                        }
                        story_data['tasks'].append(task_data)

                    epic_data['stories'].append(story_data)
                milestone_data['epics'].append(epic_data)
            progress_data['milestones'].append(milestone_data)

        with open(filepath, 'w') as f:
            json.dump(progress_data, f, indent=2)

        self.console.print(f"[green]💾 Progress saved to {filepath}[/green]")

    def _build_roadmap_context(self, milestones: List[Milestone], current_item: Item) -> str:
        """Build comprehensive roadmap context for better item generation coherence."""
        context_lines = []

        # Add roadmap overview
        context_lines.append("=== ROADMAP OVERVIEW ===")
        context_lines.append(f"Total Milestones: {len(milestones)}")

        # Count totals for overview
        total_epics = sum(len(m.get_children_by_type('Epic')) for m in milestones)
        total_stories = sum(len(e.get_children_by_type('Story')) for m in milestones for e in m.get_children_by_type('Epic'))
        total_tasks = sum(len(s.get_children_by_type('Task')) for m in milestones for e in m.get_children_by_type('Epic') for s in e.get_children_by_type('Story'))

        context_lines.append(f"Total Epics: {total_epics}")
        context_lines.append(f"Total Stories: {total_stories}")
        context_lines.append(f"Total Tasks: {total_tasks}")
        context_lines.append("")

        # Add milestone structure overview
        context_lines.append("=== MILESTONE STRUCTURE ===")
        for milestone in milestones:
            context_lines.append(f"## Milestone {milestone.id}: {milestone.name.split(': ', 1)[-1] if ': ' in milestone.name else milestone.name}")

            for epic in milestone.get_children_by_type('Epic'):
                context_lines.append(f"  ### Epic {epic.id}: {epic.name.split(': ', 1)[-1] if ': ' in epic.name else epic.name}")

                for story in epic.get_children_by_type('Story'):
                    context_lines.append(f"    #### Story {story.id}: {story.name.split(': ', 1)[-1] if ': ' in story.name else story.name}")

                    for task in story.get_children_by_type('Task'):
                        context_lines.append(f"      ##### Task {task.id}: {task.name.split(': ', 1)[-1] if ': ' in task.name else task.name}")

        context_lines.append("")

        # Add context about what's been generated so far
        context_lines.append("=== GENERATION STATUS ===")
        context_lines.append(f"Currently generating: {current_item.item_type} {current_item.id}")

        # List completed items
        completed_items = []
        for milestone in milestones:
            if milestone.generation_status == ItemStatus.GENERATED and milestone != current_item:
                completed_items.append(f"Milestone {milestone.id}")

            for epic in milestone.get_children_by_type('Epic'):
                if epic.generation_status == ItemStatus.GENERATED and epic != current_item:
                    completed_items.append(f"Epic {epic.id}")

                for story in epic.get_children_by_type('Story'):
                    if story.generation_status == ItemStatus.GENERATED and story != current_item:
                        completed_items.append(f"Story {story.id}")

        if completed_items:
            context_lines.append("Previously generated items:")
            for item in completed_items:
                context_lines.append(f"  ✅ {item}")
        else:
            context_lines.append("This is the first item being generated.")

        context_lines.append("")

        return "\n".join(context_lines)

    def _show_item_confirmation(self, item: Item, progress: Progress, task) -> None:
        """Show generated item and ask for user confirmation."""
        # Pause progress display temporarily
        progress.update(task, description=f"✅ Generated {item.item_type} {item.id}")

        self.console.print(f"\n[bold green]✅ Generated {item.item_type} {item.id}: {item.name.split(': ', 1)[-1] if ': ' in item.name else item.name}[/bold green]")

        # Show a preview of the generated content
        if item.content:
            preview = item.content[:300] + "..." if len(item.content) > 300 else item.content
            self.console.print(f"[dim]Preview: {preview}[/dim]")

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
                self.console.print("[yellow]🛑 Generation stopped by user[/yellow]")
                raise KeyboardInterrupt("User chose to quit generation")
            elif choice == "regenerate":
                self.console.print(f"[yellow]🔄 Regenerating {item.item_type} {item.id}...[/yellow]")
                # Mark as pending and regenerate
                item.update_generation_status(ItemStatus.PENDING)
                progress.update(task, description=f"Regenerating {item.item_type} {item.id}")

                # Regenerate the item
                parent_context = None
                if item.parent:
                    parent_context = f"{item.parent.item_type} {item.parent.id}: {item.parent.name.split(': ', 1)[-1] if ': ' in item.parent.name else item.parent.name}"

                # Get milestones from the current context (we need to pass this properly)
                roadmap_context = ""  # For now, skip roadmap context in regeneration
                prompt = item.generate_prompt("", parent_context, roadmap_context)
                response = self.llm_client.generate(prompt)
                item.parse_content(response)

                self.console.print(f"[green]✅ Regenerated {item.item_type} {item.id}[/green]")

                # Show the new content
                if item.content:
                    preview = item.content[:300] + "..." if len(item.content) > 300 else item.content
                    self.console.print(f"[dim]New Preview: {preview}[/dim]")

                # Continue the loop to ask again