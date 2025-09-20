"""Protocol definitions for roadmap item interfaces."""

from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime


class RoadmapItemProtocol(Protocol):
    """Base protocol for all roadmap items."""

    @property
    def title(self) -> str:
        """Title of the roadmap item."""
        ...

    @property
    def description(self) -> str:
        """Description of the roadmap item."""
        ...

    @property
    def status(self) -> str:
        """Current status of the item."""
        ...

    @property
    def priority(self) -> str:
        """Priority level of the item."""
        ...

    @property
    def estimated_effort(self) -> Optional[str]:
        """Estimated effort for completing the item."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary representation."""
        ...

    def to_markdown(self) -> str:
        """Convert item to markdown format."""
        ...


class TaskProtocol(RoadmapItemProtocol, Protocol):
    """Protocol for task items."""

    @property
    def acceptance_criteria(self) -> List[str]:
        """List of acceptance criteria for the task."""
        ...

    @property
    def assignee(self) -> Optional[str]:
        """Person assigned to the task."""
        ...

    @property
    def dependencies(self) -> List[str]:
        """List of task dependencies."""
        ...


class StoryProtocol(RoadmapItemProtocol, Protocol):
    """Protocol for user story items."""

    @property
    def user_story(self) -> str:
        """User story description."""
        ...

    @property
    def acceptance_criteria(self) -> List[str]:
        """List of acceptance criteria."""
        ...

    @property
    def tasks(self) -> List[TaskProtocol]:
        """List of tasks within the story."""
        ...

    def add_task(self, task: TaskProtocol) -> None:
        """Add a task to the story."""
        ...


class EpicProtocol(RoadmapItemProtocol, Protocol):
    """Protocol for epic items."""

    @property
    def business_value(self) -> str:
        """Business value of the epic."""
        ...

    @property
    def success_criteria(self) -> List[str]:
        """Success criteria for the epic."""
        ...

    @property
    def stories(self) -> List[StoryProtocol]:
        """List of stories within the epic."""
        ...

    def add_story(self, story: StoryProtocol) -> None:
        """Add a story to the epic."""
        ...


class MilestoneProtocol(RoadmapItemProtocol, Protocol):
    """Protocol for milestone items."""

    @property
    def target_date(self) -> Optional[datetime]:
        """Target completion date."""
        ...

    @property
    def deliverables(self) -> List[str]:
        """List of key deliverables."""
        ...

    @property
    def success_criteria(self) -> List[str]:
        """Success criteria for the milestone."""
        ...

    @property
    def epics(self) -> List[EpicProtocol]:
        """List of epics within the milestone."""
        ...

    def add_epic(self, epic: EpicProtocol) -> None:
        """Add an epic to the milestone."""
        ...


class ProjectProtocol(Protocol):
    """Protocol for project information."""

    @property
    def name(self) -> str:
        """Project name."""
        ...

    @property
    def description(self) -> str:
        """Project description."""
        ...

    @property
    def project_type(self) -> str:
        """Type of project."""
        ...

    @property
    def tech_stack(self) -> List[str]:
        """Technology stack used."""
        ...

    @property
    def estimated_duration(self) -> Optional[str]:
        """Estimated project duration."""
        ...

    @property
    def team_size(self) -> Optional[int]:
        """Size of the development team."""
        ...

    @property
    def milestones(self) -> List[MilestoneProtocol]:
        """List of project milestones."""
        ...

    def add_milestone(self, milestone: MilestoneProtocol) -> None:
        """Add a milestone to the project."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary representation."""
        ...


class RoadmapProtocol(Protocol):
    """Protocol for roadmap structure."""

    @property
    def project(self) -> ProjectProtocol:
        """Project information."""
        ...

    @property
    def creation_date(self) -> datetime:
        """Date when roadmap was created."""
        ...

    @property
    def last_updated(self) -> datetime:
        """Date when roadmap was last updated."""
        ...

    def generate_all_content(
        self,
        llm_client: 'LLMClientProtocol',
        idea: str,
        interactive_mode: bool,
        console: 'ConsoleDisplayProtocol'
    ) -> None:
        """Generate content for all roadmap items."""
        ...

    def to_markdown(self) -> str:
        """Export roadmap to markdown format."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert roadmap to dictionary representation."""
        ...