"""Roadmap orchestrator for hierarchical generation.

Coordinates the full generation process: milestones → epics → stories → tasks.
Saves incrementally after each story to prevent data loss on failures.
"""

from datetime import datetime, timezone
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from arcane.clients.base import BaseAIClient
from arcane.items import (
    Roadmap,
    StoredUsage,
    Milestone,
    Epic,
    Story,
    ProjectContext,
)
from arcane.storage import StorageManager
from arcane.templates import TemplateLoader
from arcane.utils import generate_id, format_actual_usage

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
        self.client = client
        self.console = console
        self.storage = storage
        self.interactive = interactive
        self._previous_usage = StoredUsage()
        self._progress: Progress | None = None
        self._task_id: int | None = None

        templates = TemplateLoader()
        self.milestone_gen = MilestoneGenerator(client, console, templates)
        self.epic_gen = EpicGenerator(client, console, templates)
        self.story_gen = StoryGenerator(client, console, templates)
        self.task_gen = TaskGenerator(client, console, templates)

    async def _save(self, roadmap: Roadmap) -> None:
        """Save roadmap with accumulated usage stats."""
        roadmap.usage = self._previous_usage.merged_with(self.client.usage)
        roadmap.updated_at = datetime.now(timezone.utc)
        await self.storage.save_roadmap(roadmap)

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

    def _init_progress(self, total: int) -> None:
        """Initialize the generation progress bar."""
        self._progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("{task.fields[remaining]} remaining"),
            console=self.console,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            "Starting...", total=max(total, 1), remaining=total
        )

    def _update_description(self, description: str) -> None:
        """Update the progress bar description to show current step."""
        if self._progress and self._task_id is not None:
            self._progress.update(self._task_id, description=description)

    def _advance(self, add_total: int = 0) -> None:
        """Advance progress by one step, optionally growing the total."""
        if not self._progress or self._task_id is None:
            return
        task = self._progress.tasks[self._task_id]
        new_total = task.total + add_total
        remaining = int(new_total - task.completed - 1)
        self._progress.update(
            self._task_id,
            total=new_total,
            advance=1,
            remaining=remaining,
        )

    def _pause_progress(self) -> None:
        """Temporarily hide the progress bar for interactive prompts."""
        if self._progress:
            self._progress.stop()

    def _resume_progress(self) -> None:
        """Resume the progress bar after a pause."""
        if self._progress:
            self._progress.start()

    def _finish_progress(self) -> None:
        """Stop and clean up the progress bar."""
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._task_id = None

    @staticmethod
    def _calculate_resume_total(roadmap: Roadmap) -> int:
        """Calculate the number of generation steps needed to complete a roadmap."""
        total = 0
        for ms in roadmap.milestones:
            if not ms.epics:
                total += 1
            else:
                for epic in ms.epics:
                    if not epic.stories:
                        total += 1
                    else:
                        for story in epic.stories:
                            if not story.tasks:
                                total += 1
        return total

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

        # Reset usage tracking for this session (new roadmap, no previous usage)
        self._previous_usage = StoredUsage()
        self.client.reset_usage()

        # Initialize progress bar (1 step for milestone generation)
        self._init_progress(1)

        # Phase 1: Generate milestones
        self._update_description("Generating milestones...")
        self.console.print("\n[bold]📋 Generating milestones...[/bold]")
        ms_result = await self.milestone_gen.generate(context)

        # Interactive review of milestones
        if self.interactive:
            self._pause_progress()
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
            self._resume_progress()

        self._advance(add_total=len(ms_result.milestones))

        # Create all milestone shells so resume can find them if generation fails
        ms_pairs = []
        for ms_skel in ms_result.milestones:
            milestone = Milestone(
                id=generate_id("milestone"),
                name=ms_skel.name,
                goal=ms_skel.goal,
                description=ms_skel.description,
                priority=ms_skel.priority,
            )
            roadmap.milestones.append(milestone)
            ms_pairs.append((ms_skel, milestone))

        # Save milestone shells so resume can find them if generation fails
        await self._save(roadmap)

        # Phase 2-4: Expand each milestone
        for ms_skel, milestone in ms_pairs:
            self.console.print(f"\n[bold]📦 Expanding: {ms_skel.name}[/bold]")

            # Generate epics for this milestone
            self._update_description(f"Generating epics for: {ms_skel.name}")
            ep_result = await self.epic_gen.generate(
                context,
                parent_context={"milestone": ms_skel.model_dump()},
            )

            # Interactive review of epics
            if self.interactive:
                self._pause_progress()
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
                self._resume_progress()

            self._advance(add_total=len(ep_result.epics))

            # Create all epic shells first so resume can detect incomplete ones
            epic_pairs = []
            for ep_skel in ep_result.epics:
                epic = Epic(
                    id=generate_id("epic"),
                    name=ep_skel.name,
                    goal=ep_skel.goal,
                    description=ep_skel.description,
                    priority=ep_skel.priority,
                )
                milestone.epics.append(epic)
                epic_pairs.append((ep_skel, epic))

            # Save epic shells so resume can find them if generation fails
            await self._save(roadmap)

            # Now expand each epic with stories and tasks
            for ep_skel, epic in epic_pairs:
                self.console.print(f"  [bold]🏗  Epic: {ep_skel.name}[/bold]")

                # Generate stories for this epic
                self._update_description(f"Generating stories for: {ep_skel.name}")
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
                    self._pause_progress()
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
                    self._resume_progress()

                self._advance(add_total=len(st_result.stories))

                # Create all story shells first so resume can detect incomplete ones
                story_pairs = []
                for st_skel in st_result.stories:
                    story = Story(
                        id=generate_id("story"),
                        name=st_skel.name,
                        description=st_skel.description,
                        priority=st_skel.priority,
                        acceptance_criteria=st_skel.acceptance_criteria,
                    )
                    epic.stories.append(story)
                    story_pairs.append((st_skel, story))

                # Save story shells so resume can find them if generation fails
                await self._save(roadmap)

                # Now generate tasks for each story
                for st_skel, story in story_pairs:
                    self.console.print(f"    [dim]📝 Story: {st_skel.name}[/dim]")

                    # Generate tasks for this story
                    self._update_description(f"Generating tasks for: {st_skel.name}")
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
                        self._pause_progress()
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
                        self._resume_progress()

                    self._advance()

                    story.tasks = task_result.tasks

                    # Save incrementally after each story
                    await self._save(roadmap)

        # Final save
        await self._save(roadmap)

        self._finish_progress()
        self._print_summary(roadmap)
        return roadmap

    async def resume(self, roadmap: Roadmap) -> Roadmap:
        """Resume generation of an incomplete roadmap.

        Walks the existing hierarchy, skips completed items, and generates
        missing children (epics, stories, tasks) from where it left off.

        Args:
            roadmap: A partially-complete roadmap loaded from disk.

        Returns:
            The completed Roadmap.
        """
        context = roadmap.context

        # Capture existing usage so we can accumulate across sessions
        self._previous_usage = roadmap.usage.model_copy()
        self.client.reset_usage()

        # Initialize progress bar based on remaining work
        resume_total = self._calculate_resume_total(roadmap)
        if resume_total > 0:
            self._init_progress(resume_total)

        # Walk milestones — they already exist, just need children filled in
        for milestone in roadmap.milestones:
            ms_ctx = self._item_context(milestone)

            # Case 1: Milestone has no epics — generate them
            if not milestone.epics:
                self.console.print(
                    f"\n[bold]📦 Resuming: {milestone.name}[/bold] (generating epics)"
                )

                self._update_description(f"Generating epics for: {milestone.name}")
                ep_result = await self.epic_gen.generate(
                    context,
                    parent_context={"milestone": ms_ctx},
                )

                if self.interactive:
                    self._pause_progress()
                    while True:
                        self._display_epics(ep_result.epics, milestone.name)
                        self.console.print(
                            "[dim]  [a] Approve and continue  [r] Regenerate epics[/dim]"
                        )
                        action = self._prompt_review("epics")
                        if action == ReviewAction.APPROVE:
                            break
                        self.console.print(
                            f"\n[bold]🔄 Regenerating epics for {milestone.name}...[/bold]"
                        )
                        ep_result = await self.epic_gen.generate(
                            context,
                            parent_context={"milestone": ms_ctx},
                        )
                    self._resume_progress()

                self._advance(add_total=len(ep_result.epics))

                for ep_skel in ep_result.epics:
                    epic = Epic(
                        id=generate_id("epic"),
                        name=ep_skel.name,
                        goal=ep_skel.goal,
                        description=ep_skel.description,
                        priority=ep_skel.priority,
                    )
                    milestone.epics.append(epic)

                # Save epic shells so resume can find them if generation fails
                await self._save(roadmap)

            # Now expand each epic that needs children
            for epic in milestone.epics:
                ep_ctx = self._item_context(epic)

                # Case 2: Epic has no stories — generate them
                if not epic.stories:
                    self.console.print(
                        f"  [bold]🏗  Resuming: {epic.name}[/bold] (generating stories)"
                    )

                    self._update_description(f"Generating stories for: {epic.name}")
                    st_result = await self.story_gen.generate(
                        context,
                        parent_context={"milestone": ms_ctx, "epic": ep_ctx},
                        sibling_context=[],
                    )

                    if self.interactive:
                        self._pause_progress()
                        while True:
                            self._display_stories(st_result.stories, epic.name)
                            self.console.print(
                                "[dim]  [a] Approve and continue  [r] Regenerate stories[/dim]"
                            )
                            action = self._prompt_review("stories")
                            if action == ReviewAction.APPROVE:
                                break
                            self.console.print(
                                f"\n[bold]🔄 Regenerating stories for {epic.name}...[/bold]"
                            )
                            st_result = await self.story_gen.generate(
                                context,
                                parent_context={"milestone": ms_ctx, "epic": ep_ctx},
                                sibling_context=[],
                            )
                        self._resume_progress()

                    self._advance(add_total=len(st_result.stories))

                    for st_skel in st_result.stories:
                        story = Story(
                            id=generate_id("story"),
                            name=st_skel.name,
                            description=st_skel.description,
                            priority=st_skel.priority,
                            acceptance_criteria=st_skel.acceptance_criteria,
                        )
                        epic.stories.append(story)

                    # Save story shells so resume can find them if generation fails
                    await self._save(roadmap)

                # Now expand each story that needs tasks
                for story in epic.stories:
                    if story.tasks:
                        continue

                    st_ctx = self._item_context(story)

                    self.console.print(
                        f"    [dim]📝 Resuming: {story.name}[/dim] (generating tasks)"
                    )

                    self._update_description(f"Generating tasks for: {story.name}")
                    task_result = await self.task_gen.generate(
                        context,
                        parent_context={
                            "milestone": ms_ctx,
                            "epic": ep_ctx,
                            "story": st_ctx,
                        },
                    )

                    if self.interactive:
                        self._pause_progress()
                        while True:
                            self._display_tasks(task_result.tasks, story.name)
                            self.console.print(
                                "[dim]  [a] Approve and continue  [r] Regenerate tasks[/dim]"
                            )
                            action = self._prompt_review("tasks")
                            if action == ReviewAction.APPROVE:
                                break
                            self.console.print(
                                f"\n[bold]🔄 Regenerating tasks for {story.name}...[/bold]"
                            )
                            task_result = await self.task_gen.generate(
                                context,
                                parent_context={
                                    "milestone": ms_ctx,
                                    "epic": ep_ctx,
                                    "story": st_ctx,
                                },
                            )
                        self._resume_progress()

                    self._advance()

                    story.tasks = task_result.tasks

                    # Save incrementally after each story
                    await self._save(roadmap)

        # Final save
        await self._save(roadmap)

        self._finish_progress()
        self._print_summary(roadmap)
        return roadmap

    @staticmethod
    def _item_context(item: Milestone | Epic | Story) -> dict:
        """Extract compact context dict from a saved item for parent_context.

        Only includes the fields used by the prompt template (name, goal,
        description, priority) to keep context concise.
        """
        ctx = {
            "name": item.name,
            "description": item.description,
            "priority": item.priority.value,
        }
        if hasattr(item, "goal"):
            ctx["goal"] = item.goal
        return ctx

    def _print_summary(self, roadmap: Roadmap) -> None:
        """Print generation summary with item counts and usage stats."""
        counts = roadmap.total_items
        self.console.print(f"\n[bold green]✅ Roadmap complete![/bold green]")
        self.console.print(
            f"   {counts['milestones']} milestones, {counts['epics']} epics, "
            f"{counts['stories']} stories, {counts['tasks']} tasks"
        )
        self.console.print(f"   Estimated: {roadmap.total_hours} hours")

        # Print session usage
        self.console.print()
        self.console.print(format_actual_usage(
            usage=self.client.usage,
            model=self.client.model_name,
            label="Session usage",
        ))

        # Print cumulative usage if there was previous usage
        if self._previous_usage.api_calls > 0:
            self.console.print()
            self.console.print(format_actual_usage(
                usage=roadmap.usage,
                model=self.client.model_name,
                label="Cumulative usage (all sessions)",
            ))
