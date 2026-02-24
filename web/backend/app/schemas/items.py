from typing import Any

from pydantic import BaseModel, Field


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    labels: list[str] | None = None
    goal: str | None = None
    target_date: str | None = None
    estimated_hours: int | None = None
    acceptance_criteria: list[str] | None = None
    implementation_notes: str | None = None
    claude_code_prompt: str | None = None
    prerequisites: list[str] | None = None


class ItemCreate(BaseModel):
    item_type: str = Field(pattern=r"^(milestone|epic|story|task)$")
    data: dict[str, Any]


class ReorderRequest(BaseModel):
    parent_id: str = Field(description="Parent item ID, or 'root' for milestones")
    item_ids: list[str]


class CascadedUpdate(BaseModel):
    id: str
    status: str


class ItemResponse(BaseModel):
    item_id: str
    item_type: str
    data: dict[str, Any]
    cascaded: list[CascadedUpdate] = []


class DeleteResponse(BaseModel):
    deleted_id: str
    deleted_type: str
    children_deleted: int


class AiEditRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2000)


class AiEditResponse(BaseModel):
    item_id: str
    item_type: str
    original: dict[str, Any]
    edited: dict[str, Any]
