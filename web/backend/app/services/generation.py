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

logger = logging.getLogger(__name__)


class WebStorageAdapter:
    """Duck-typed storage adapter for the RoadmapOrchestrator.

    The orchestrator calls ``self.storage.save_roadmap(roadmap)`` after
    each story. This adapter serialises the arcane-core Roadmap into
    the RoadmapRecord.roadmap_data JSONB column and extracts progress
    counts into the GenerationJob.progress JSONB column.
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

        await orchestrator.generate(context)

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
