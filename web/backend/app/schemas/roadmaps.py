import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RoadmapCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    context: dict[str, Any] | None = None


class RoadmapDetail(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    status: str
    context: dict[str, Any] | None
    roadmap_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
