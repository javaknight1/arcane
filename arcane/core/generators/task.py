"""Task generator implementation."""

from pydantic import BaseModel

from arcane.core.items import Task

from .base import BaseGenerator


class TaskList(BaseModel):
    """Container for generated tasks."""

    tasks: list[Task]


class TaskGenerator(BaseGenerator):
    """Generates implementation tasks for a story."""

    @property
    def item_type(self) -> str:
        return "task"

    def get_response_model(self) -> type[BaseModel]:
        return TaskList
