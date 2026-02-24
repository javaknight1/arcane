"""JSONB roadmap item traversal and mutation helpers."""

import copy
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from arcane.core.utils.ids import generate_id

from ..models.project import Project
from ..models.roadmap import RoadmapRecord
from ..models.user import User

# Maps item type to the key holding its children
CHILDREN_KEY = {
    "milestone": "epics",
    "epic": "stories",
    "story": "tasks",
    "task": None,  # tasks have no children
}

# Maps parent type to the type of its children
CHILD_TYPE = {
    "root": "milestone",
    "milestone": "epic",
    "epic": "story",
    "story": "task",
}

# Maps item type to the key under which items of that type live in their parent
COLLECTION_KEY = {
    "milestone": "milestones",
    "epic": "epics",
    "story": "stories",
    "task": "tasks",
}


async def get_project_for_user(
    db: AsyncSession, project_id: uuid.UUID, user: User
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def get_roadmap_for_user(
    db: AsyncSession, roadmap_id: uuid.UUID, user: User
) -> RoadmapRecord:
    result = await db.execute(
        select(RoadmapRecord)
        .join(Project)
        .where(RoadmapRecord.id == roadmap_id, Project.user_id == user.id)
    )
    roadmap = result.scalar_one_or_none()
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    return roadmap


def ensure_roadmap_data(roadmap: RoadmapRecord) -> dict:
    if roadmap.roadmap_data is None:
        return {"milestones": []}
    return copy.deepcopy(roadmap.roadmap_data)


def save_roadmap_data(roadmap: RoadmapRecord, data: dict) -> None:
    """Deep-copy and reassign so SQLAlchemy detects the JSONB change."""
    roadmap.roadmap_data = copy.deepcopy(data)


def find_item_by_id(
    data: dict, item_id: str
) -> tuple[dict, list, int, str] | None:
    """Find an item anywhere in the hierarchy.

    Returns (item, parent_list, index_in_parent, item_type) or None.
    """
    milestones = data.get("milestones", [])
    for mi, ms in enumerate(milestones):
        if ms.get("id") == item_id:
            return ms, milestones, mi, "milestone"
        for ei, ep in enumerate(ms.get("epics", [])):
            if ep.get("id") == item_id:
                return ep, ms["epics"], ei, "epic"
            for si, st in enumerate(ep.get("stories", [])):
                if st.get("id") == item_id:
                    return st, ep["stories"], si, "story"
                for ti, tk in enumerate(st.get("tasks", [])):
                    if tk.get("id") == item_id:
                        return tk, st["tasks"], ti, "task"
    return None


def count_descendants(item: dict, item_type: str) -> int:
    """Count all nested children of an item."""
    children_key = CHILDREN_KEY.get(item_type)
    if children_key is None:
        return 0
    children = item.get(children_key, [])
    count = len(children)
    child_type_key = CHILD_TYPE.get(item_type)
    if child_type_key:
        child_children_key = CHILDREN_KEY.get(child_type_key)
        if child_children_key:
            for child in children:
                count += count_descendants(child, child_type_key)
    return count


def apply_item_update(item: dict, updates: dict[str, Any]) -> dict:
    """Apply partial updates to an item dict, returning the modified item."""
    for key, value in updates.items():
        item[key] = value
    return item


def create_child_item(parent_id: str, item_type: str, item_data: dict, data: dict) -> dict:
    """Create a new child item under the given parent.

    Returns the created item dict.
    Raises HTTPException on invalid parent or type mismatch.
    """
    if parent_id == "root":
        if item_type != "milestone":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only milestones can be added at root level",
            )
        collection = data.setdefault("milestones", [])
    else:
        result = find_item_by_id(data, parent_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent item {parent_id} not found",
            )
        parent_item, _, _, parent_type = result
        expected_child_type = CHILD_TYPE.get(parent_type)
        if expected_child_type is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add children to a {parent_type}",
            )
        if item_type != expected_child_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expected child type '{expected_child_type}' for parent type '{parent_type}', got '{item_type}'",
            )
        children_key = CHILDREN_KEY[parent_type]
        collection = parent_item.setdefault(children_key, [])

    new_item = {"id": generate_id(item_type), **item_data}
    # Ensure child collection keys exist for non-task items
    children_key = CHILDREN_KEY.get(item_type)
    if children_key and children_key not in new_item:
        new_item[children_key] = []
    collection.append(new_item)
    return new_item


def find_parent_chain(data: dict, item_id: str) -> dict | None:
    """Return ancestor context for an item, formatted for generator parent_context.

    Returns {} for milestones, {"milestone": {...}} for epics,
    {"milestone": {...}, "epic": {...}} for stories, etc.
    Returns None if item_id not found.
    """
    def _ancestor_entry(item: dict, item_type: str) -> dict:
        entry = {
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "priority": item.get("priority", "medium"),
        }
        if item_type in ("milestone", "epic"):
            entry["goal"] = item.get("goal", "")
        return entry

    for ms in data.get("milestones", []):
        if ms.get("id") == item_id:
            return {}
        for ep in ms.get("epics", []):
            if ep.get("id") == item_id:
                return {"milestone": _ancestor_entry(ms, "milestone")}
            for st in ep.get("stories", []):
                if st.get("id") == item_id:
                    return {
                        "milestone": _ancestor_entry(ms, "milestone"),
                        "epic": _ancestor_entry(ep, "epic"),
                    }
                for tk in st.get("tasks", []):
                    if tk.get("id") == item_id:
                        return {
                            "milestone": _ancestor_entry(ms, "milestone"),
                            "epic": _ancestor_entry(ep, "epic"),
                            "story": _ancestor_entry(st, "story"),
                        }
    return None


def compute_parent_status(children: list[dict]) -> str:
    """Compute a parent's status from its children's statuses."""
    if not children:
        return "not_started"
    statuses = [c.get("status", "not_started") for c in children]
    if all(s == "completed" for s in statuses):
        return "completed"
    if all(s == "not_started" for s in statuses):
        return "not_started"
    if any(s == "blocked" for s in statuses):
        return "blocked"
    return "in_progress"


def cascade_status_update(data: dict, item_id: str) -> list[dict]:
    """After a status change on item_id, recompute all ancestor statuses.

    Returns list of {id, status} for each changed ancestor.
    """
    changed: list[dict] = []

    for ms in data.get("milestones", []):
        for ep in ms.get("epics", []):
            for st in ep.get("stories", []):
                for tk in st.get("tasks", []):
                    if tk.get("id") == item_id:
                        # Walk up: story -> epic -> milestone
                        return _recompute_ancestors(data, ms, ep, st)
                if st.get("id") == item_id:
                    return _recompute_ancestors(data, ms, ep)
            if ep.get("id") == item_id:
                return _recompute_ancestors(data, ms)
        if ms.get("id") == item_id:
            # Milestone has no parent to update
            return []
    return changed


def _recompute_ancestors(
    data: dict,
    ms: dict,
    ep: dict | None = None,
    st: dict | None = None,
) -> list[dict]:
    """Recompute status for story, epic, milestone ancestors as needed."""
    changed: list[dict] = []

    if st is not None:
        # Recompute story status from tasks
        new_status = compute_parent_status(st.get("tasks", []))
        if st.get("status") != new_status:
            st["status"] = new_status
            changed.append({"id": st["id"], "status": new_status})

    if ep is not None:
        # Recompute epic status from stories
        new_status = compute_parent_status(ep.get("stories", []))
        if ep.get("status") != new_status:
            ep["status"] = new_status
            changed.append({"id": ep["id"], "status": new_status})

    # Recompute milestone status from epics
    new_status = compute_parent_status(ms.get("epics", []))
    if ms.get("status") != new_status:
        ms["status"] = new_status
        changed.append({"id": ms["id"], "status": new_status})

    return changed


def reorder_children(parent_id: str, item_ids: list[str], data: dict) -> None:
    """Reorder children of a parent to match the given ID order.

    Raises HTTPException if IDs don't match existing children.
    """
    if parent_id == "root":
        collection = data.get("milestones", [])
    else:
        result = find_item_by_id(data, parent_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent item {parent_id} not found",
            )
        parent_item, _, _, parent_type = result
        children_key = CHILDREN_KEY.get(parent_type)
        if children_key is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item type '{parent_type}' has no children to reorder",
            )
        collection = parent_item.get(children_key, [])

    existing_ids = {item["id"] for item in collection}
    requested_ids = set(item_ids)

    if existing_ids != requested_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided item IDs do not match existing children",
        )

    id_to_item = {item["id"]: item for item in collection}
    reordered = [id_to_item[item_id] for item_id in item_ids]

    # Replace in-place
    if parent_id == "root":
        data["milestones"] = reordered
    else:
        result = find_item_by_id(data, parent_id)
        parent_item, _, _, parent_type = result
        parent_item[CHILDREN_KEY[parent_type]] = reordered
