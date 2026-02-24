from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKey


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    pm_credentials = relationship("PMCredential", back_populates="user", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="user", cascade="all, delete-orphan")
