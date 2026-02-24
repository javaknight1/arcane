"""Export service for PM tool integrations.

Provides reconstruct_roadmap() to build arcane-core Roadmap from DB records,
export_csv_inline() for synchronous CSV export, and run_export() for
background PM exports.
"""

import copy
import csv
import io
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from arcane.core.items import Roadmap
from arcane.core.items.context import ProjectContext
from arcane.core.project_management.csv import CSVClient

from ..models.export_job import ExportJob
from ..models.roadmap import RoadmapRecord
from . import event_bus

logger = logging.getLogger(__name__)


def reconstruct_roadmap(record: RoadmapRecord) -> Roadmap:
    """Build an arcane-core Roadmap from a DB RoadmapRecord.

    Combines record.roadmap_data (milestones hierarchy) with record.context
    (ProjectContext fields) to produce a full Roadmap object suitable for
    passing to PM exporters.
    """
    data = record.roadmap_data or {}
    context_dict = record.context or {}

    context = ProjectContext(**context_dict)

    return Roadmap(
        id=str(record.id),
        project_name=record.name,
        created_at=record.created_at,
        updated_at=record.updated_at,
        context=context,
        milestones=data.get("milestones", []),
    )


def export_csv_inline(roadmap: Roadmap) -> str:
    """Generate CSV content in-memory and return as a string."""
    client = CSVClient()
    rows = client._flatten(roadmap)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSVClient.FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


async def run_export(
    session_factory: async_sessionmaker,
    export_job_id: str,
    roadmap_record_id: str,
    service: str,
    credentials: dict,
    workspace_params: dict | None,
) -> None:
    """Background task that runs a PM export.

    Creates its own DB sessions (short-lived, committed per operation)
    because it runs outside the request lifecycle.
    """
    job_uuid = uuid.UUID(export_job_id)
    roadmap_uuid = uuid.UUID(roadmap_record_id)

    # Mark job in_progress
    async with session_factory() as session:
        result = await session.execute(
            select(ExportJob).where(ExportJob.id == job_uuid)
        )
        job = result.scalar_one()
        job.status = "in_progress"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

    try:
        # Load roadmap from DB
        async with session_factory() as session:
            result = await session.execute(
                select(RoadmapRecord).where(RoadmapRecord.id == roadmap_uuid)
            )
            record = result.scalar_one()
            roadmap = reconstruct_roadmap(record)

        # Create PM client
        if service == "linear":
            from arcane.core.project_management import LinearClient
            client = LinearClient(api_key=credentials["api_key"])
        elif service == "jira":
            from arcane.core.project_management import JiraClient
            client = JiraClient(
                domain=credentials["domain"],
                email=credentials["email"],
                api_token=credentials["api_token"],
            )
        elif service == "notion":
            from arcane.core.project_management import NotionClient
            client = NotionClient(api_key=credentials["api_key"])
        else:
            raise ValueError(f"Unknown service: {service}")

        items_exported = 0

        def progress_callback(item_type: str, item_name: str) -> None:
            nonlocal items_exported
            items_exported += 1
            event_bus.publish(export_job_id, {
                "event": "progress",
                "data": {
                    "items_exported": items_exported,
                    "current_item": f"{item_type}: {item_name}",
                },
            })

        # Run export
        kwargs = workspace_params or {}
        export_result = await client.export(
            roadmap,
            progress_callback=progress_callback,
            **kwargs,
        )

        # Emit complete event
        result_dict = export_result.model_dump(mode="json")
        event_bus.publish(export_job_id, {
            "event": "complete",
            "data": result_dict,
        })

        # Mark job completed
        async with session_factory() as session:
            result = await session.execute(
                select(ExportJob).where(ExportJob.id == job_uuid)
            )
            job = result.scalar_one()
            job.status = "completed"
            job.result = copy.deepcopy(result_dict)
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()

    except Exception as exc:
        logger.exception("Export failed for job %s", export_job_id)

        event_bus.publish(export_job_id, {
            "event": "error",
            "data": {"message": f"Export failed: {exc}"},
        })

        async with session_factory() as session:
            result = await session.execute(
                select(ExportJob).where(ExportJob.id == job_uuid)
            )
            job = result.scalar_one()
            job.status = "failed"
            job.error = str(exc)[:2000]
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()

    finally:
        event_bus.cleanup(export_job_id)
