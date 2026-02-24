"""Generation endpoints for starting, polling, and streaming background AI generation."""

import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from ..config import Settings, get_settings
from ..database import get_session_factory
from ..deps import get_current_user, get_db
from ..models.generation_job import GenerationJob
from ..models.project import Project
from ..models.roadmap import RoadmapRecord
from ..models.user import User
from ..schemas.generation import GenerateRequest, GenerationJobResponse
from ..services import event_bus
from ..services.generation import run_generation, run_regeneration
from ..services.roadmap_items import (
    get_roadmap_for_user,
    ensure_roadmap_data,
    find_item_by_id,
)

router = APIRouter()


@router.post(
    "/roadmaps/{roadmap_id}/generate",
    response_model=GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_generation(
    roadmap_id: uuid.UUID,
    body: GenerateRequest = GenerateRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Start background AI generation for a roadmap."""
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)

    # Resolve context: body overrides stored context
    context = body.context or roadmap.context
    if not context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No context provided and roadmap has no stored context",
        )

    # API key check
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI generation is not configured (missing API key)",
        )

    # Conflict guard: check for active jobs
    active_result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.roadmap_id == roadmap_id,
            GenerationJob.status.in_(["pending", "in_progress"]),
        )
    )
    if active_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A generation job is already active for this roadmap",
        )

    # Create job
    job = GenerationJob(roadmap_id=roadmap_id, status="pending")
    db.add(job)

    # Set roadmap status to generating
    roadmap.status = "generating"

    await db.flush()
    await db.refresh(job)

    # Launch background task
    session_factory = get_session_factory()
    asyncio.create_task(
        run_generation(
            session_factory=session_factory,
            roadmap_record_id=str(roadmap_id),
            job_id=str(job.id),
            context_dict=context,
            anthropic_api_key=settings.anthropic_api_key,
            model=settings.model,
        )
    )

    return GenerationJobResponse.model_validate(job)


@router.post(
    "/roadmaps/{roadmap_id}/items/{item_id}/regenerate",
    response_model=GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def regenerate_item_children(
    roadmap_id: uuid.UUID,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Regenerate the children of a specific roadmap item."""
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)

    if not roadmap.context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No context stored on roadmap; cannot regenerate",
        )

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI generation is not configured (missing API key)",
        )

    # Conflict guard: check for active jobs
    active_result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.roadmap_id == roadmap_id,
            GenerationJob.status.in_(["pending", "in_progress"]),
        )
    )
    if active_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A generation job is already active for this roadmap",
        )

    # Find the item in roadmap data
    data = ensure_roadmap_data(roadmap)
    found = find_item_by_id(data, item_id)
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found in roadmap",
        )
    _, _, _, item_type = found

    if item_type == "task":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasks have no children to regenerate",
        )

    # Create job and launch background task
    job = GenerationJob(roadmap_id=roadmap_id, status="pending")
    db.add(job)
    await db.flush()
    await db.refresh(job)

    session_factory = get_session_factory()
    asyncio.create_task(
        run_regeneration(
            session_factory=session_factory,
            roadmap_record_id=str(roadmap_id),
            job_id=str(job.id),
            item_id=item_id,
            anthropic_api_key=settings.anthropic_api_key,
            model=settings.model,
        )
    )

    return GenerationJobResponse.model_validate(job)


@router.get(
    "/generation-jobs/{job_id}",
    response_model=GenerationJobResponse,
)
async def get_generation_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the status of a generation job (ownership-checked)."""
    result = await db.execute(
        select(GenerationJob)
        .join(RoadmapRecord)
        .join(Project)
        .where(GenerationJob.id == job_id, Project.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )
    return GenerationJobResponse.model_validate(job)


@router.get("/generation-jobs/{job_id}/stream")
async def stream_generation_progress(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream generation progress via Server-Sent Events."""
    # Verify job exists and user owns it
    result = await db.execute(
        select(GenerationJob)
        .join(RoadmapRecord)
        .join(Project)
        .where(GenerationJob.id == job_id, Project.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )

    job_id_str = str(job_id)

    # If job already completed or failed, send final event immediately
    if job.status in ("completed", "failed"):

        async def _terminal_events():
            if job.status == "completed":
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "roadmap_id": str(job.roadmap_id),
                        "total_items": job.progress or {},
                    }),
                }
            else:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": job.error or "Generation failed"}),
                }

        return EventSourceResponse(_terminal_events())

    # Subscribe and stream live events
    async def _stream_events():
        queue = event_bus.subscribe(job_id_str)
        try:
            # Send current progress as catch-up if available
            if job.progress:
                yield {
                    "event": "progress",
                    "data": json.dumps(job.progress),
                }

            while True:
                event = await queue.get()
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"]),
                }
                # Stop after terminal events
                if event["event"] in ("complete", "error"):
                    break
        finally:
            event_bus.unsubscribe(job_id_str, queue)

    return EventSourceResponse(_stream_events())
