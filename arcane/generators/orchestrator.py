"""Roadmap orchestrator for hierarchical generation.

Coordinates the full generation process: milestones → epics → stories → tasks.
Saves incrementally after each story to prevent data loss on failures.
"""

from datetime import datetime, timezone

from rich.console import Console

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
