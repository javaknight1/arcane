"""ExportJob model for tracking PM export operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, JsonType, UUIDPrimaryKey


class ExportJob(UUIDPrimaryKey, Base):
    __tablename__ = "export_jobs"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    workspace_params: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    progress: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    result: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    roadmap = relationship("RoadmapRecord", back_populates="export_jobs")
    user = relationship("User", back_populates="export_jobs")
