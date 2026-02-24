"""Export and credential management endpoints."""

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
from ..models.export_job import ExportJob
from ..models.project import Project
from ..models.roadmap import RoadmapRecord
from ..models.user import User
from ..schemas.exports import (
    CredentialCreate,
    CredentialResponse,
    CredentialValidateResponse,
    CSVExportResponse,
    ExportJobResponse,
    ExportRequest,
)
from ..services import event_bus
from ..services.credentials import (
    VALID_SERVICES,
    delete_credential,
    get_credential,
    list_credentials,
    save_credential,
    validate_credential,
)
from ..services.export import export_csv_inline, reconstruct_roadmap, run_export
from ..services.roadmap_items import get_roadmap_for_user

router = APIRouter()


# ── Credentials ──────────────────────────────────────────────────────────


@router.get("/credentials", response_model=list[CredentialResponse])
async def list_user_credentials(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List connected PM services (metadata only, no secrets)."""
    creds = await list_credentials(db, user.id)
    return [CredentialResponse.model_validate(c) for c in creds]


@router.post("/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def save_user_credential(
    body: CredentialCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Save or update PM credentials for a service."""
    if body.service not in VALID_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service. Must be one of: {', '.join(sorted(VALID_SERVICES))}",
        )
    cred = await save_credential(db, user.id, body.service, body.credentials, settings.encryption_key)
    return CredentialResponse.model_validate(cred)


@router.delete("/credentials/{service}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_credential(
    service: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Disconnect a PM service."""
    deleted = await delete_credential(db, user.id, service)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for service: {service}",
        )


@router.post("/credentials/{service}/validate", response_model=CredentialValidateResponse)
async def validate_user_credential(
    service: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Test stored credentials for a PM service."""
    creds = await get_credential(db, user.id, service, settings.encryption_key)
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for service: {service}",
        )
    valid, message = await validate_credential(service, creds)
    return CredentialValidateResponse(service=service, valid=valid, message=message)


# ── Exports ──────────────────────────────────────────────────────────────


@router.post("/roadmaps/{roadmap_id}/export")
async def start_export(
    roadmap_id: uuid.UUID,
    body: ExportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Start an export. CSV returns content inline; others launch background job."""
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)

    if body.service == "csv":
        reconstructed = reconstruct_roadmap(roadmap)
        csv_content = export_csv_inline(reconstructed)
        filename = f"{roadmap.name.lower().replace(' ', '-')}-roadmap.csv"
        return CSVExportResponse(csv_content=csv_content, filename=filename)

    if body.service not in VALID_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service. Must be one of: csv, {', '.join(sorted(VALID_SERVICES))}",
        )

    # Fetch credentials
    creds = await get_credential(db, user.id, body.service, settings.encryption_key)
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No credentials configured for {body.service}. Add them in Settings.",
        )

    # Create export job
    job = ExportJob(
        roadmap_id=roadmap_id,
        user_id=user.id,
        service=body.service,
        status="pending",
        workspace_params=body.workspace_params,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # Launch background task
    session_factory = get_session_factory()
    asyncio.create_task(
        run_export(
            session_factory=session_factory,
            export_job_id=str(job.id),
            roadmap_record_id=str(roadmap_id),
            service=body.service,
            credentials=creds,
            workspace_params=body.workspace_params,
        )
    )

    return ExportJobResponse.model_validate(job)


@router.get("/export-jobs/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the status of an export job."""
    result = await db.execute(
        select(ExportJob).where(
            ExportJob.id == job_id,
            ExportJob.user_id == user.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export job not found",
        )
    return ExportJobResponse.model_validate(job)


@router.get("/export-jobs/{job_id}/stream")
async def stream_export_progress(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream export progress via Server-Sent Events."""
    result = await db.execute(
        select(ExportJob).where(
            ExportJob.id == job_id,
            ExportJob.user_id == user.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export job not found",
        )

    job_id_str = str(job_id)

    if job.status in ("completed", "failed"):
        async def _terminal_events():
            if job.status == "completed":
                yield {
                    "event": "complete",
                    "data": json.dumps(job.result or {}),
                }
            else:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": job.error or "Export failed"}),
                }

        return EventSourceResponse(_terminal_events())

    async def _stream_events():
        queue = event_bus.subscribe(job_id_str)
        try:
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
                if event["event"] in ("complete", "error"):
                    break
        finally:
            event_bus.unsubscribe(job_id_str, queue)

    return EventSourceResponse(_stream_events())


@router.get("/roadmaps/{roadmap_id}/exports", response_model=list[ExportJobResponse])
async def list_export_history(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List export history for a roadmap."""
    # Verify ownership
    await get_roadmap_for_user(db, roadmap_id, user)

    result = await db.execute(
        select(ExportJob)
        .where(ExportJob.roadmap_id == roadmap_id, ExportJob.user_id == user.id)
        .order_by(ExportJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return [ExportJobResponse.model_validate(j) for j in jobs]
