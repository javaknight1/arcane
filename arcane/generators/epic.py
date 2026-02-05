"""Epic generator implementation."""

from pydantic import BaseModel

from .base import BaseGenerator
from .skeletons import EpicSkeletonList


class EpicGenerator(BaseGenerator):
    """Generates epic skeletons for a milestone."""

    @property
    def item_type(self) -> str:
        return "epic"

    def get_response_model(self) -> type[BaseModel]:
        return EpicSkeletonList
