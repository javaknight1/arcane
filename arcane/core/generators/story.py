"""Story generator implementation."""

from pydantic import BaseModel

from .base import BaseGenerator
from .skeletons import StorySkeletonList


class StoryGenerator(BaseGenerator):
    """Generates story skeletons for an epic."""

    @property
    def item_type(self) -> str:
        return "story"

    def get_response_model(self) -> type[BaseModel]:
        return StorySkeletonList
