"""Schemas for background roadmap generation."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    context: dict[str, Any] | None = None


class GenerationJobResponse(BaseModel):
    id: uuid.UUID
    roadmap_id: uuid.UUID
    status: str
    progress: dict[str, Any] | None
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}
