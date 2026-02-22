import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..deps import get_current_user, get_db
from ..models.project import Project
from ..models.roadmap import RoadmapRecord
from ..models.user import User
from ..schemas.projects import (
    ProjectCreate,
    ProjectDetail,
    ProjectSummary,
    ProjectUpdate,
    RoadmapSummary,
)
from ..services.roadmap_items import get_project_for_user

router = APIRouter()


@router.post("/", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = Project(name=body.name, user_id=user.id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return ProjectDetail(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        roadmaps=[],
    )


@router.get("/", response_model=list[ProjectSummary])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            Project.id,
            Project.name,
            Project.created_at,
            Project.updated_at,
            func.count(RoadmapRecord.id).label("roadmap_count"),
        )
        .outerjoin(RoadmapRecord)
        .where(Project.user_id == user.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )
    rows = result.all()
    return [
        ProjectSummary(
            id=row.id,
            name=row.name,
            created_at=row.created_at,
            updated_at=row.updated_at,
            roadmap_count=row.roadmap_count,
        )
        for row in rows
    ]


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.roadmaps))
        .where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectDetail(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        roadmaps=[
            RoadmapSummary(
                id=r.id,
                name=r.name,
                status=r.status,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in project.roadmaps
        ],
    )


@router.patch("/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await get_project_for_user(db, project_id, user)
    project.name = body.name
    await db.flush()
    await db.refresh(project)
    # Load roadmaps for response
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.roadmaps))
        .where(Project.id == project.id)
    )
    project = result.scalar_one()
    return ProjectDetail(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        roadmaps=[
            RoadmapSummary(
                id=r.id,
                name=r.name,
                status=r.status,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in project.roadmaps
        ],
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await get_project_for_user(db, project_id, user)
    await db.delete(project)
