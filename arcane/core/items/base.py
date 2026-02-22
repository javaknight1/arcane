"""Base models and enums for roadmap items.

This module provides the foundational types used across all roadmap items:
Priority, Status enums and the BaseItem base class.
"""

from enum import Enum

from pydantic import BaseModel


class Priority(str, Enum):
    """Priority levels for roadmap items."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Status states for roadmap items."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class BaseItem(BaseModel):
    """Base class for all roadmap items.

    All roadmap items (Task, Story, Epic, Milestone) inherit from this class
    and share these common fields.
    """

    id: str
    name: str
    description: str
    priority: Priority
    status: Status = Status.NOT_STARTED
    labels: list[str] = []
