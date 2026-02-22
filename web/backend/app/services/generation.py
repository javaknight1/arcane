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
from arcane.core.items.context import ProjectContext

from ..models.generation_job import GenerationJob
from ..models.roadmap import RoadmapRecord
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
