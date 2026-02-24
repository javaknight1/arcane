import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, JsonType, TimestampMixin, UUIDPrimaryKey


class RoadmapRecord(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "roadmaps"

    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    context: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    roadmap_data: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    project = relationship("Project", back_populates="roadmaps")
    generation_jobs = relationship("GenerationJob", back_populates="roadmap", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="roadmap", cascade="all, delete-orphan")
