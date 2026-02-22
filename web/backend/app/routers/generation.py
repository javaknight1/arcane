"""Generation endpoints for starting and polling background AI generation."""

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..database import get_session_factory
from ..deps import get_current_user, get_db
from ..models.generation_job import GenerationJob
from ..models.project import Project
from ..models.roadmap import RoadmapRecord
from ..models.user import User
from ..schemas.generation import GenerateRequest, GenerationJobResponse
from ..services.generation import run_generation
from ..services.roadmap_items import get_roadmap_for_user

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
