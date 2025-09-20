"""Protocol interfaces for type safety and better design patterns."""

from .llm_protocols import LLMClientProtocol, GenerationResultProtocol
from .roadmap_protocols import (
    RoadmapItemProtocol,
    MilestoneProtocol,
    EpicProtocol,
    StoryProtocol,
    TaskProtocol,
    ProjectProtocol,
    RoadmapProtocol
)
from .display_protocols import ConsoleDisplayProtocol, ProgressReporterProtocol
from .file_protocols import FileOperationsProtocol, TemplateLoaderProtocol

__all__ = [
    # LLM protocols
    'LLMClientProtocol',
    'GenerationResultProtocol',

    # Roadmap item protocols
    'RoadmapItemProtocol',
    'MilestoneProtocol',
    'EpicProtocol',
    'StoryProtocol',
    'TaskProtocol',
    'ProjectProtocol',
    'RoadmapProtocol',

    # Display protocols
    'ConsoleDisplayProtocol',
    'ProgressReporterProtocol',

    # File operation protocols
    'FileOperationsProtocol',
    'TemplateLoaderProtocol'
]