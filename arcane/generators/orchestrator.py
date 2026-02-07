"""Roadmap orchestrator for hierarchical generation.

Coordinates the full generation process: milestones → epics → stories → tasks.
Saves incrementally after each story to prevent data loss on failures.
"""

from datetime import datetime, timezone
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from arcane.clients.base import BaseAIClient
from arcane.items import (
    Roadmap,
    Milestone,
    Epic,
    Story,
    ProjectContext,
)
from arcane.storage import StorageManager
from arcane.templates import TemplateLoader
from arcane.utils import generate_id

from .milestone import MilestoneGenerator
from .epic import EpicGenerator
from .story import StoryGenerator
from .task import TaskGenerator


class ReviewAction(str, Enum):
    """User action after reviewing generated items."""
    APPROVE = "approve"
    REGENERATE = "regenerate"


class RoadmapOrchestrator:
    """Coordinates the full hierarchical generation process."""

    def __init__(
        self,
        client: BaseAIClient,
        console: Console,
        storage: StorageManager,
        interactive: bool = True,
    ):
        """Initialize the orchestrator.

        Args:
            client: AI client for generation calls.
            console: Rich console for output.
            storage: Storage manager for saving roadmaps.
            interactive: Whether to pause for user review between levels.
        """
        self.console = console
        self.storage = storage
        self.interactive = interactive

        templates = TemplateLoader()
        self.milestone_gen = MilestoneGenerator(client, console, templates)
        self.epic_gen = EpicGenerator(client, console, templates)
        self.story_gen = StoryGenerator(client, console, templates)
        self.task_gen = TaskGenerator(client, console, templates)

    def _display_milestones(self, milestones: list) -> None:
        """Display generated milestones in a table format."""
        table = Table(title="Generated Milestones", show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Goal", style="white")
        table.add_column("Priority", style="yellow")

        for i, ms in enumerate(milestones, 1):
            table.add_row(
                str(i),
                ms.name,
                ms.goal[:60] + "..." if len(ms.goal) > 60 else ms.goal,
                ms.priority.value,
            )

        self.console.print()
        self.console.print(table)

    def _display_epics(self, epics: list, milestone_name: str) -> None:
        """Display generated epics in a table format."""
        table = Table(
            title=f"Epics for '{milestone_name}'",
            show_header=True,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Goal", style="white")
        table.add_column("Priority", style="yellow")

        for i, ep in enumerate(epics, 1):
            table.add_row(
                str(i),
                ep.name,
                ep.goal[:60] + "..." if len(ep.goal) > 60 else ep.goal,
                ep.priority.value,
            )

        self.console.print()
        self.console.print(table)

    def _display_stories(self, stories: list, epic_name: str) -> None:
        """Display generated stories in a table format."""
        table = Table(
            title=f"Stories for '{epic_name}'",
            show_header=True,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Priority", style="yellow")

        for i, st in enumerate(stories, 1):
            desc = st.description[:50] + "..." if len(st.description) > 50 else st.description
            table.add_row(
                str(i),
                st.name,
                desc,
                st.priority.value,
            )

        self.console.print()
        self.console.print(table)

    def _display_tasks(self, tasks: list, story_name: str) -> None:
        """Display generated tasks in a table format."""
        table = Table(
            title=f"Tasks for '{story_name}'",
            show_header=True,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Hours", style="green", justify="right")
        table.add_column("Priority", style="yellow")

        for i, task in enumerate(tasks, 1):
            table.add_row(
                str(i),
                task.name[:40] + "..." if len(task.name) > 40 else task.name,
                str(task.estimated_hours),
                task.priority.value,
            )

        self.console.print()
        self.console.print(table)

    def _prompt_review(self, item_type: str) -> ReviewAction:
        """Prompt user to approve or regenerate items."""
        self.console.print()
        choice = Prompt.ask(
            f"[bold]Review {item_type}[/bold]",
            choices=["a", "r"],
            default="a",
            console=self.console,
        )

        if choice == "r":
            return ReviewAction.REGENERATE
        return ReviewAction.APPROVE

    async def generate(self, context: ProjectContext) -> Roadmap:
        """Generate a complete roadmap from project context.

        Generates hierarchically: milestones → epics → stories → tasks.
        Saves incrementally after each story completes.

        Args:
            context: The project context from discovery questions.

        Returns:
            The complete generated Roadmap.
        """
        roadmap = Roadmap(
            id=generate_id("roadmap"),
            project_name=context.project_name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=context,
        )

        # Phase 1: Generate milestones
        self.console.print("\n[bold]📋 Generating milestones...[/bold]")
        ms_result = await self.milestone_gen.generate(context)

        # Interactive review of milestones
        if self.interactive:
            while True:
                self._display_milestones(ms_result.milestones)
                self.console.print(
                    "[dim]  [a] Approve and continue  [r] Regenerate milestones[/dim]"
                )
                action = self._prompt_review("milestones")
                if action == ReviewAction.APPROVE:
                    break
                self.console.print("\n[bold]🔄 Regenerating milestones...[/bold]")
                ms_result = await self.milestone_gen.generate(context)

        # Phase 2-4: Expand each milestone
        for ms_skel in ms_result.milestones:
            self.console.print(f"\n[bold]📦 Expanding: {ms_skel.name}[/bold]")

            milestone = Milestone(
                id=generate_id("milestone"),
                name=ms_skel.name,
                goal=ms_skel.goal,
                description=ms_skel.description,
                priority=ms_skel.priority,
            )

            # Generate epics for this milestone
            ep_result = await self.epic_gen.generate(
                context,
                parent_context={"milestone": ms_skel.model_dump()},
            )

            # Interactive review of epics
            if self.interactive:
                while True:
                    self._display_epics(ep_result.epics, ms_skel.name)
                    self.console.print(
                        "[dim]  [a] Approve and continue  [r] Regenerate epics[/dim]"
                    )
                    action = self._prompt_review("epics")
                    if action == ReviewAction.APPROVE:
                        break
                    self.console.print(
                        f"\n[bold]🔄 Regenerating epics for {ms_skel.name}...[/bold]"
                    )
                    ep_result = await self.epic_gen.generate(
                        context,
                        parent_context={"milestone": ms_skel.model_dump()},
                    )

            for ep_skel in ep_result.epics:
                self.console.print(f"  [bold]🏗  Epic: {ep_skel.name}[/bold]")

                epic = Epic(
                    id=generate_id("epic"),
                    name=ep_skel.name,
                    goal=ep_skel.goal,
                    description=ep_skel.description,
                    priority=ep_skel.priority,
                )

                # Generate stories for this epic
                st_result = await self.story_gen.generate(
                    context,
                    parent_context={
                        "milestone": ms_skel.model_dump(),
                        "epic": ep_skel.model_dump(),
                    },
                    sibling_context=[s.name for s in epic.stories],
                )

                # Interactive review of stories
                if self.interactive:
                    while True:
                        self._display_stories(st_result.stories, ep_skel.name)
                        self.console.print(
                            "[dim]  [a] Approve and continue  [r] Regenerate stories[/dim]"
                        )
                        action = self._prompt_review("stories")
                        if action == ReviewAction.APPROVE:
                            break
                        self.console.print(
                            f"\n[bold]🔄 Regenerating stories for {ep_skel.name}...[/bold]"
                        )
                        st_result = await self.story_gen.generate(
                            context,
                            parent_context={
                                "milestone": ms_skel.model_dump(),
                                "epic": ep_skel.model_dump(),
                            },
                            sibling_context=[s.name for s in epic.stories],
                        )

                for st_skel in st_result.stories:
                    self.console.print(f"    [dim]📝 Story: {st_skel.name}[/dim]")

                    story = Story(
                        id=generate_id("story"),
                        name=st_skel.name,
                        description=st_skel.description,
                        priority=st_skel.priority,
                        acceptance_criteria=st_skel.acceptance_criteria,
                    )

                    # Generate tasks for this story
                    task_result = await self.task_gen.generate(
                        context,
                        parent_context={
                            "milestone": ms_skel.model_dump(),
                            "epic": ep_skel.model_dump(),
                            "story": st_skel.model_dump(),
                        },
                    )

                    # Interactive review of tasks
                    if self.interactive:
                        while True:
                            self._display_tasks(task_result.tasks, st_skel.name)
                            self.console.print(
                                "[dim]  [a] Approve and continue  [r] Regenerate tasks[/dim]"
                            )
                            action = self._prompt_review("tasks")
                            if action == ReviewAction.APPROVE:
                                break
                            self.console.print(
                                f"\n[bold]🔄 Regenerating tasks for {st_skel.name}...[/bold]"
                            )
                            task_result = await self.task_gen.generate(
                                context,
                                parent_context={
                                    "milestone": ms_skel.model_dump(),
                                    "epic": ep_skel.model_dump(),
                                    "story": st_skel.model_dump(),
                                },
                            )

                    story.tasks = task_result.tasks
                    epic.stories.append(story)

                    # Save incrementally after each story
                    roadmap.updated_at = datetime.now(timezone.utc)
                    await self.storage.save_roadmap(roadmap)

                milestone.epics.append(epic)

            roadmap.milestones.append(milestone)

        # Final save
        roadmap.updated_at = datetime.now(timezone.utc)
        await self.storage.save_roadmap(roadmap)

        # Print summary
        counts = roadmap.total_items
        self.console.print(f"\n[bold green]✅ Roadmap complete![/bold green]")
        self.console.print(
            f"   {counts['milestones']} milestones, {counts['epics']} epics, "
            f"{counts['stories']} stories, {counts['tasks']} tasks"
        )
        self.console.print(f"   Estimated: {roadmap.total_hours} hours")

        return roadmap
