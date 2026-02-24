"""Schemas for PM credential management and roadmap exports."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


# Credentials

class CredentialCreate(BaseModel):
    service: str  # "linear" | "jira" | "notion"
    credentials: dict[str, str]


class CredentialResponse(BaseModel):
    id: uuid.UUID
    service: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CredentialValidateResponse(BaseModel):
    service: str
    valid: bool
    message: str


# Exports

class ExportRequest(BaseModel):
    service: str  # "csv" | "linear" | "jira" | "notion"
    workspace_params: dict[str, str] | None = None


class ExportJobResponse(BaseModel):
    id: uuid.UUID
    roadmap_id: uuid.UUID
    service: str
    status: str
    progress: dict[str, Any] | None
    result: dict[str, Any] | None
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CSVExportResponse(BaseModel):
    csv_content: str
    filename: str
