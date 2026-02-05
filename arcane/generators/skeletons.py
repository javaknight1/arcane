"""Skeleton models for intermediate generation steps.

These models represent the "skeleton" structure generated at each level
before expanding into full items. They contain suggestions for child
items but not the actual children.
"""

from pydantic import BaseModel

from arcane.items.base import Priority


class MilestoneSkeleton(BaseModel):
    """Intermediate milestone before epic expansion."""

    name: str
    goal: str
    description: str
    priority: Priority
    suggested_epic_areas: list[str]


class MilestoneSkeletonList(BaseModel):
    """Container for multiple milestone skeletons."""

    milestones: list[MilestoneSkeleton]


class EpicSkeleton(BaseModel):
    """Intermediate epic before story expansion."""

    name: str
    goal: str
    description: str
    priority: Priority
    suggested_story_areas: list[str]


class EpicSkeletonList(BaseModel):
    """Container for multiple epic skeletons."""

    epics: list[EpicSkeleton]


class StorySkeleton(BaseModel):
    """Intermediate story before task expansion."""

    name: str
    description: str
    priority: Priority
    acceptance_criteria: list[str]


class StorySkeletonList(BaseModel):
    """Container for multiple story skeletons."""

    stories: list[StorySkeleton]
