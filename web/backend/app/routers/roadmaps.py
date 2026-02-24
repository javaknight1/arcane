import uuid

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
from ..schemas.roadmaps import RoadmapCreate, RoadmapDetail
from ..services.ai_edit import run_ai_edit
from ..services.roadmap_items import (
    apply_item_update,
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
    save_roadmap_data(roadmap, data)
    return ItemResponse(item_id=item["id"], item_type=item_type, data=item)


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
