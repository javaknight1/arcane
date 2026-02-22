import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, JsonType, UUIDPrimaryKey


class GenerationJob(UUIDPrimaryKey, Base):
    __tablename__ = "generation_jobs"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    progress: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roadmap = relationship("RoadmapRecord", back_populates="generation_jobs")
