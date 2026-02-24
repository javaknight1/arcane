"""Background generation service.

Provides WebStorageAdapter (duck-typed storage for the orchestrator) and
run_generation() which runs as an asyncio background task.
"""

import copy
import io
import logging
import uuid
from datetime import datetime, timezone

from rich.console import Console
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from arcane.core.clients import create_client
from arcane.core.generators.orchestrator import RoadmapOrchestrator
from arcane.core.generators.epic import EpicGenerator
from arcane.core.generators.story import StoryGenerator
from arcane.core.generators.task import TaskGenerator
from arcane.core.items.context import ProjectContext
from arcane.core.templates.loader import TemplateLoader
from arcane.core.utils.ids import generate_id

from ..models.generation_job import GenerationJob
from ..models.roadmap import RoadmapRecord
from .roadmap_items import find_item_by_id, find_parent_chain
from . import event_bus

logger = logging.getLogger(__name__)


class WebStorageAdapter:
    """Duck-typed storage adapter for the RoadmapOrchestrator.

    The orchestrator calls ``self.storage.save_roadmap(roadmap)`` after
    each story. This adapter serialises the arcane-core Roadmap into
    the RoadmapRecord.roadmap_data JSONB column and extracts progress
    counts into the GenerationJob.progress JSONB column.

    It also publishes progress and item_created events to the event bus
    so that SSE subscribers receive real-time updates.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker,
        roadmap_record_id: str,
        job_id: str,
    ):
        self.session_factory = session_factory
        self.roadmap_record_id = uuid.UUID(roadmap_record_id)
        self.job_id = uuid.UUID(job_id)
        self.job_id_str = job_id
        self._prev_counts: dict[str, int] = {
            "milestones": 0,
            "epics": 0,
            "stories": 0,
            "tasks": 0,
        }

    async def save_roadmap(self, roadmap) -> None:
        """Persist roadmap data and progress to the database."""
        roadmap_data = roadmap.model_dump(mode="json")
        progress = self._extract_progress(roadmap)

        async with self.session_factory() as session:
            result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == self.roadmap_record_id)
            )
            record = result.scalar_one()
            record.roadmap_data = copy.deepcopy(roadmap_data)

            job_result = await session.execute(
                select(GenerationJob).where(GenerationJob.id == self.job_id)
            )
            job = job_result.scalar_one()
            job.progress = copy.deepcopy(progress)

            await session.commit()

        # Emit item_created events for newly added items
        self._emit_item_created_events(roadmap, progress)

        # Emit progress event
        event_bus.publish(self.job_id_str, {
            "event": "progress",
            "data": progress,
        })

        # Update previous counts
        self._prev_counts = {
            "milestones": progress["milestones"],
            "epics": progress["epics"],
            "stories": progress["stories"],
            "tasks": progress["tasks"],
        }

    def _emit_item_created_events(self, roadmap, progress: dict) -> None:
        """Detect newly added items and emit item_created events."""
        # Walk the hierarchy and emit events for new items
        item_type_order = ["milestones", "epics", "stories", "tasks"]
        for item_type in item_type_order:
            new_count = progress[item_type]
            old_count = self._prev_counts[item_type]
            if new_count <= old_count:
                continue
            # Find the new items by walking the roadmap
            for item_info in self._find_new_items(roadmap, item_type, old_count):
                event_bus.publish(self.job_id_str, {
                    "event": "item_created",
                    "data": item_info,
                })

    @staticmethod
    def _find_new_items(roadmap, item_type: str, skip_count: int) -> list[dict]:
        """Walk the roadmap and return info for items past skip_count."""
        results = []
        count = 0
        if item_type == "milestones":
            for m in roadmap.milestones:
                if count >= skip_count:
                    results.append({"type": "milestone", "name": m.name, "parent": None})
                count += 1
        elif item_type == "epics":
            for m in roadmap.milestones:
                for e in m.epics:
                    if count >= skip_count:
                        results.append({"type": "epic", "name": e.name, "parent": m.name})
                    count += 1
        elif item_type == "stories":
            for m in roadmap.milestones:
                for e in m.epics:
                    for s in e.stories:
                        if count >= skip_count:
                            results.append({"type": "story", "name": s.name, "parent": e.name})
                        count += 1
        elif item_type == "tasks":
            for m in roadmap.milestones:
                for e in m.epics:
                    for s in e.stories:
                        for t in s.tasks:
                            if count >= skip_count:
                                results.append({"type": "task", "name": t.name, "parent": s.name})
                            count += 1
        return results

    @staticmethod
    def _extract_progress(roadmap) -> dict:
        """Extract generation progress counts from a Roadmap."""
        counts = roadmap.total_items
        stories_total = counts["stories"]
        stories_completed = sum(
            1
            for m in roadmap.milestones
            for e in m.epics
            for s in e.stories
            if s.tasks
        )

        # Determine current phase
        if counts["milestones"] == 0:
            phase = "milestones"
        elif counts["epics"] == 0:
            phase = "epics"
        elif counts["stories"] == 0:
            phase = "stories"
        elif stories_completed < stories_total:
            phase = "tasks"
        else:
            phase = "complete"

        return {
            "milestones": counts["milestones"],
            "epics": counts["epics"],
            "stories": counts["stories"],
            "tasks": counts["tasks"],
            "stories_completed": stories_completed,
            "stories_total": stories_total,
            "phase": phase,
        }


async def run_generation(
    session_factory: async_sessionmaker,
    roadmap_record_id: str,
    job_id: str,
    context_dict: dict,
    anthropic_api_key: str,
    model: str,
) -> None:
    """Background task that runs the arcane-core orchestrator.

    Creates its own DB sessions (short-lived, committed per operation)
    because it runs outside the request lifecycle.
    """
    job_uuid = uuid.UUID(job_id)
    roadmap_uuid = uuid.UUID(roadmap_record_id)

    # Mark job as in_progress
    async with session_factory() as session:
        result = await session.execute(
            select(GenerationJob).where(GenerationJob.id == job_uuid)
        )
        job = result.scalar_one()
        job.status = "in_progress"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

    try:
        context = ProjectContext(**context_dict)
        client = create_client("anthropic", api_key=anthropic_api_key, model=model)
        adapter = WebStorageAdapter(session_factory, roadmap_record_id, job_id)
        console = Console(file=io.StringIO(), quiet=True)
        orchestrator = RoadmapOrchestrator(
            client=client,
            console=console,
            storage=adapter,
            interactive=False,
        )

        roadmap = await orchestrator.generate(context)

        # Emit complete event before DB update
        event_bus.publish(job_id, {
            "event": "complete",
            "data": {
                "roadmap_id": roadmap_record_id,
                "total_items": roadmap.total_items,
            },
        })

        # Mark job completed & roadmap generated
        async with session_factory() as session:
            result = await session.execute(
                select(GenerationJob).where(GenerationJob.id == job_uuid)
            )
            job = result.scalar_one()
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)

            rm_result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == roadmap_uuid)
            )
            roadmap_record = rm_result.scalar_one()
            roadmap_record.status = "generated"

            await session.commit()

    except Exception as exc:
        logger.exception("Generation failed for job %s", job_id)

        # Emit error event before DB update
        event_bus.publish(job_id, {
            "event": "error",
            "data": {"message": f"Generation failed: {exc}"},
        })

        async with session_factory() as session:
            result = await session.execute(
                select(GenerationJob).where(GenerationJob.id == job_uuid)
            )
            job = result.scalar_one()
            job.status = "failed"
            job.error = str(exc)[:2000]
            job.completed_at = datetime.now(timezone.utc)

            rm_result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == roadmap_uuid)
            )
            roadmap_record = rm_result.scalar_one()
            roadmap_record.status = "failed"

            await session.commit()

    finally:
        event_bus.cleanup(job_id)


def _skeleton_to_dict(skeleton, item_type: str) -> dict:
    """Convert a skeleton Pydantic model to a JSONB-format dict."""
    item_id = generate_id(item_type)
    d = {
        "id": item_id,
        "name": skeleton.name,
        "description": skeleton.description,
        "priority": skeleton.priority.value if hasattr(skeleton.priority, "value") else skeleton.priority,
        "status": "not_started",
        "labels": [],
    }
    if item_type in ("milestone", "epic"):
        d["goal"] = skeleton.goal
    if item_type == "milestone":
        d["target_date"] = None
        d["epics"] = []
    elif item_type == "epic":
        d["prerequisites"] = []
        d["stories"] = []
    elif item_type == "story":
        d["acceptance_criteria"] = skeleton.acceptance_criteria
        d["tasks"] = []
    return d


def _task_to_dict(task) -> dict:
    """Convert a Task Pydantic model to a JSONB-format dict."""
    return {
        "id": generate_id("task"),
        "name": task.name,
        "description": task.description,
        "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
        "status": "not_started",
        "labels": list(task.labels) if task.labels else [],
        "estimated_hours": task.estimated_hours,
        "prerequisites": list(task.prerequisites) if task.prerequisites else [],
        "acceptance_criteria": list(task.acceptance_criteria) if task.acceptance_criteria else [],
        "implementation_notes": task.implementation_notes,
        "claude_code_prompt": task.claude_code_prompt,
    }


async def _regenerate_children(
    item: dict,
    item_type: str,
    parent_context: dict,
    context: ProjectContext,
    generators: dict,
    job_id_str: str,
    session_factory,
    roadmap_record_id: str,
    data: dict,
) -> int:
    """Generate new children for an item, cascading downward. Returns items created count."""
    roadmap_uuid = uuid.UUID(roadmap_record_id)
    total_created = 0

    if item_type == "milestone":
        # Build parent_context for children of this milestone
        child_parent_ctx = dict(parent_context)
        child_parent_ctx["milestone"] = {
            "name": item["name"],
            "description": item["description"],
            "priority": item.get("priority", "medium"),
            "goal": item.get("goal", ""),
        }
        ep_result = await generators["epic"].generate(context, parent_context=child_parent_ctx)
        new_epics = []
        for skel in ep_result.epics:
            epic_dict = _skeleton_to_dict(skel, "epic")
            new_epics.append(epic_dict)
            total_created += 1

            event_bus.publish(job_id_str, {
                "event": "item_created",
                "data": {"type": "epic", "name": skel.name, "parent": item["name"]},
            })

        item["epics"] = new_epics

        # Save intermediate state
        async with session_factory() as session:
            result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == roadmap_uuid)
            )
            record = result.scalar_one()
            record.roadmap_data = copy.deepcopy(data)
            await session.commit()

        # Recurse: generate stories+tasks for each epic
        for epic_dict in new_epics:
            count = await _regenerate_children(
                epic_dict, "epic", child_parent_ctx, context, generators,
                job_id_str, session_factory, roadmap_record_id, data,
            )
            total_created += count

    elif item_type == "epic":
        child_parent_ctx = dict(parent_context)
        child_parent_ctx["epic"] = {
            "name": item["name"],
            "description": item["description"],
            "priority": item.get("priority", "medium"),
            "goal": item.get("goal", ""),
        }
        st_result = await generators["story"].generate(context, parent_context=child_parent_ctx)
        new_stories = []
        for skel in st_result.stories:
            story_dict = _skeleton_to_dict(skel, "story")
            new_stories.append(story_dict)
            total_created += 1

            event_bus.publish(job_id_str, {
                "event": "item_created",
                "data": {"type": "story", "name": skel.name, "parent": item["name"]},
            })

        item["stories"] = new_stories

        # Save intermediate state
        async with session_factory() as session:
            result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == roadmap_uuid)
            )
            record = result.scalar_one()
            record.roadmap_data = copy.deepcopy(data)
            await session.commit()

        # Recurse: generate tasks for each story
        for story_dict in new_stories:
            count = await _regenerate_children(
                story_dict, "story", child_parent_ctx, context, generators,
                job_id_str, session_factory, roadmap_record_id, data,
            )
            total_created += count

    elif item_type == "story":
        child_parent_ctx = dict(parent_context)
        child_parent_ctx["story"] = {
            "name": item["name"],
            "description": item["description"],
            "priority": item.get("priority", "medium"),
        }
        task_result = await generators["task"].generate(context, parent_context=child_parent_ctx)
        new_tasks = []
        for task in task_result.tasks:
            task_dict = _task_to_dict(task)
            new_tasks.append(task_dict)
            total_created += 1

            event_bus.publish(job_id_str, {
                "event": "item_created",
                "data": {"type": "task", "name": task.name, "parent": item["name"]},
            })

        item["tasks"] = new_tasks

        # Save to DB
        async with session_factory() as session:
            result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == roadmap_uuid)
            )
            record = result.scalar_one()
            record.roadmap_data = copy.deepcopy(data)
            await session.commit()

    # Emit progress event
    event_bus.publish(job_id_str, {
        "event": "progress",
        "data": {"items_created": total_created},
    })

    return total_created


async def run_regeneration(
    session_factory: async_sessionmaker,
    roadmap_record_id: str,
    job_id: str,
    item_id: str,
    anthropic_api_key: str,
    model: str,
) -> None:
    """Background task that regenerates children of a specific item."""
    job_uuid = uuid.UUID(job_id)
    roadmap_uuid = uuid.UUID(roadmap_record_id)

    # Mark job as in_progress
    async with session_factory() as session:
        result = await session.execute(
            select(GenerationJob).where(GenerationJob.id == job_uuid)
        )
        job = result.scalar_one()
        job.status = "in_progress"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

    try:
        # Load roadmap data and context
        async with session_factory() as session:
            result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == roadmap_uuid)
            )
            roadmap_record = result.scalar_one()
            data = copy.deepcopy(roadmap_record.roadmap_data) or {"milestones": []}
            context_dict = roadmap_record.context

        # Find item and parent chain
        found = find_item_by_id(data, item_id)
        if found is None:
            raise ValueError(f"Item {item_id} not found in roadmap data")
        item, _, _, item_type = found

        parent_chain = find_parent_chain(data, item_id) or {}
        context = ProjectContext(**context_dict)

        # Create AI client and generators
        client = create_client("anthropic", api_key=anthropic_api_key, model=model)
        console = Console(file=io.StringIO(), quiet=True)
        templates = TemplateLoader()

        generators = {
            "epic": EpicGenerator(client, console, templates),
            "story": StoryGenerator(client, console, templates),
            "task": TaskGenerator(client, console, templates),
        }

        # Run cascading regeneration
        total_created = await _regenerate_children(
            item, item_type, parent_chain, context, generators,
            job_id, session_factory, roadmap_record_id, data,
        )

        # Emit complete event
        event_bus.publish(job_id, {
            "event": "complete",
            "data": {
                "roadmap_id": roadmap_record_id,
                "items_created": total_created,
            },
        })

        # Mark job completed (do NOT change roadmap status)
        async with session_factory() as session:
            result = await session.execute(
                select(GenerationJob).where(GenerationJob.id == job_uuid)
            )
            job = result.scalar_one()
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()

    except Exception as exc:
        logger.exception("Regeneration failed for job %s", job_id)

        event_bus.publish(job_id, {
            "event": "error",
            "data": {"message": f"Regeneration failed: {exc}"},
        })

        async with session_factory() as session:
            result = await session.execute(
                select(GenerationJob).where(GenerationJob.id == job_uuid)
            )
            job = result.scalar_one()
            job.status = "failed"
            job.error = str(exc)[:2000]
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()

    finally:
        event_bus.cleanup(job_id)
