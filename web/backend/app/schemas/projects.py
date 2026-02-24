import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class RoadmapSummary(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    item_counts: dict[str, int] | None = None
    completion_percent: float | None = None

    model_config = {"from_attributes": True}


class ProjectSummary(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
    roadmap_count: int

    model_config = {"from_attributes": True}


class ProjectDetail(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
    roadmaps: list[RoadmapSummary]

    model_config = {"from_attributes": True}
