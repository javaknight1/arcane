import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..deps import get_current_user, get_db
from ..models.project import Project
from ..models.roadmap import RoadmapRecord
from ..models.user import User
from ..schemas.items import (
    AiEditRequest,
    AiEditResponse,
    DeleteResponse,
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    ReorderRequest,
)
from ..schemas.projects import RoadmapSummary
from ..schemas.roadmaps import MilestoneStats, RoadmapCreate, RoadmapDetail, RoadmapStats
from ..services.ai_edit import run_ai_edit
from ..services.roadmap_items import (
    apply_item_update,
    cascade_status_update,
    count_descendants,
    create_child_item,
    ensure_roadmap_data,
    find_item_by_id,
    find_parent_chain,
    get_project_for_user,
    get_roadmap_for_user,
    reorder_children,
    save_roadmap_data,
)

router = APIRouter()


# --- Roadmap CRUD ---


@router.post(
    "/projects/{project_id}/roadmaps",
    response_model=RoadmapDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_roadmap(
    project_id: uuid.UUID,
    body: RoadmapCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await get_project_for_user(db, project_id, user)
    roadmap = RoadmapRecord(
        project_id=project_id,
        name=body.name,
        context=body.context,
        status="draft",
    )
    db.add(roadmap)
    await db.flush()
    await db.refresh(roadmap)
    return RoadmapDetail.model_validate(roadmap)


@router.get("/projects/{project_id}/roadmaps", response_model=list[RoadmapSummary])
async def list_roadmaps(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await get_project_for_user(db, project_id, user)
    result = await db.execute(
        select(RoadmapRecord)
        .where(RoadmapRecord.project_id == project_id)
        .order_by(RoadmapRecord.created_at.desc())
    )
    roadmaps = result.scalars().all()
    return [RoadmapSummary.model_validate(r) for r in roadmaps]


@router.get("/roadmaps/{roadmap_id}", response_model=RoadmapDetail)
async def get_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)
    return RoadmapDetail.model_validate(roadmap)


@router.delete("/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)
    await db.delete(roadmap)


@router.get("/roadmaps/{roadmap_id}/stats", response_model=RoadmapStats)
async def get_roadmap_stats(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)
    data = ensure_roadmap_data(roadmap)

    today = date.today()
    total_hours = 0
    total_hours_completed = 0
    milestone_stats: list[MilestoneStats] = []

    for ms in data.get("milestones", []):
        ms_hours = 0
        ms_hours_completed = 0
        ms_total_items = 0
        ms_completed_items = 0
        epic_count = 0
        story_count = 0
        task_count = 0

        for ep in ms.get("epics", []):
            epic_count += 1
            for st in ep.get("stories", []):
                story_count += 1
                for tk in st.get("tasks", []):
                    task_count += 1
                    ms_total_items += 1
                    h = tk.get("estimated_hours", 0) or 0
                    ms_hours += h
                    if tk.get("status") == "completed":
                        ms_completed_items += 1
                        ms_hours_completed += h

        target_date = ms.get("target_date")
        is_overdue = False
        if target_date and ms.get("status") != "completed":
            try:
                td = date.fromisoformat(target_date)
                is_overdue = td < today
            except (ValueError, TypeError):
                pass

        milestone_stats.append(MilestoneStats(
            id=ms.get("id", ""),
            name=ms.get("name", ""),
            status=ms.get("status", "not_started"),
            target_date=target_date,
            is_overdue=is_overdue,
            total_items=ms_total_items,
            completed_items=ms_completed_items,
            hours_total=ms_hours,
            hours_completed=ms_hours_completed,
            epic_count=epic_count,
            story_count=story_count,
            task_count=task_count,
        ))

        total_hours += ms_hours
        total_hours_completed += ms_hours_completed

    completion_percent = 0.0
    if total_hours > 0:
        completion_percent = round(total_hours_completed / total_hours * 100, 1)

    return RoadmapStats(
        hours_total=total_hours,
        hours_completed=total_hours_completed,
        completion_percent=completion_percent,
        milestones=milestone_stats,
    )


# --- Item endpoints ---


@router.patch("/roadmaps/{roadmap_id}/items/{item_id}", response_model=ItemResponse)
async def update_item(
    roadmap_id: uuid.UUID,
    item_id: str,
    body: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)
    data = ensure_roadmap_data(roadmap)
    result = find_item_by_id(data, item_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    item, _, _, item_type = result
    updates = body.model_dump(exclude_unset=True)
    apply_item_update(item, updates)
    cascaded = []
    if "status" in updates:
        cascaded = cascade_status_update(data, item_id)
    save_roadmap_data(roadmap, data)
    return ItemResponse(item_id=item["id"], item_type=item_type, data=item, cascaded=cascaded)


@router.delete("/roadmaps/{roadmap_id}/items/{item_id}", response_model=DeleteResponse)
async def delete_item(
    roadmap_id: uuid.UUID,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)
    data = ensure_roadmap_data(roadmap)
    result = find_item_by_id(data, item_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    item, parent_list, index, item_type = result
    children_count = count_descendants(item, item_type)
    parent_list.pop(index)
    save_roadmap_data(roadmap, data)
    return DeleteResponse(
        deleted_id=item_id,
        deleted_type=item_type,
        children_deleted=children_count,
    )


@router.post(
    "/roadmaps/{roadmap_id}/items/{parent_id}/children",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_child_item(
    roadmap_id: uuid.UUID,
    parent_id: str,
    body: ItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)
    data = ensure_roadmap_data(roadmap)
    new_item = create_child_item(parent_id, body.item_type, body.data, data)
    save_roadmap_data(roadmap, data)
    return ItemResponse(item_id=new_item["id"], item_type=body.item_type, data=new_item)


@router.put("/roadmaps/{roadmap_id}/items/reorder")
async def reorder_items(
    roadmap_id: uuid.UUID,
    body: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)
    data = ensure_roadmap_data(roadmap)
    reorder_children(body.parent_id, body.item_ids, data)
    save_roadmap_data(roadmap, data)
    return {"status": "ok"}


@router.post(
    "/roadmaps/{roadmap_id}/items/{item_id}/ai-edit",
    response_model=AiEditResponse,
)
async def ai_edit_item(
    roadmap_id: uuid.UUID,
    item_id: str,
    body: AiEditRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Edit a roadmap item using AI based on a natural language command."""
    roadmap = await get_roadmap_for_user(db, roadmap_id, user)

    if not roadmap.context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No context stored on roadmap; cannot use AI edit",
        )

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI editing is not configured (missing API key)",
        )

    data = ensure_roadmap_data(roadmap)
    result = find_item_by_id(data, item_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    item, _, _, item_type = result

    parent_context = find_parent_chain(data, item_id)
    original = dict(item)

    edited = await run_ai_edit(
        item=item,
        item_type=item_type,
        command=body.command,
        context_dict=roadmap.context,
        parent_context=parent_context,
        anthropic_api_key=settings.anthropic_api_key,
        model=settings.model,
    )

    # Apply edited fields back into the roadmap data
    for key, value in edited.items():
        item[key] = value
    save_roadmap_data(roadmap, data)

    return AiEditResponse(
        item_id=item_id,
        item_type=item_type,
        original=original,
        edited=edited,
    )
