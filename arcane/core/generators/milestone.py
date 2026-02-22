"""Milestone generator implementation."""

from pydantic import BaseModel

from .base import BaseGenerator
from .skeletons import MilestoneSkeletonList


class MilestoneGenerator(BaseGenerator):
    """Generates milestone skeletons for a project roadmap."""

    @property
    def item_type(self) -> str:
        return "milestone"

    def get_response_model(self) -> type[BaseModel]:
        return MilestoneSkeletonList
