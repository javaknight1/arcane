"""Storage manager for saving, loading, and resuming roadmaps.

Handles persistence of roadmaps to disk as JSON and YAML files,
and provides resume point detection for incomplete generations.
"""

from datetime import datetime, timezone
from pathlib import Path

import yaml

from arcane.items import Roadmap, ProjectContext


class StorageManager:
    """Handles saving, loading, and resuming roadmaps on disk."""

    def __init__(self, base_path: Path):
        """Initialize the storage manager.

        Args:
            base_path: Base directory for storing roadmap files.
        """
        self.base_path = Path(base_path)

    async def save_roadmap(self, roadmap: Roadmap) -> Path:
        """Save a roadmap to disk.

        Creates a project directory with:
        - roadmap.json: Full roadmap serialized as JSON
        - context.yaml: Project context in human-readable YAML

        Args:
            roadmap: The roadmap to save.

        Returns:
            Path to the saved roadmap.json file.
        """
        project_dir = self.base_path / self._slugify(roadmap.project_name)
        project_dir.mkdir(parents=True, exist_ok=True)

        roadmap_path = project_dir / "roadmap.json"
        roadmap_path.write_text(roadmap.model_dump_json(indent=2))

        context_path = project_dir / "context.yaml"
        context_path.write_text(
            yaml.dump(
                roadmap.context.model_dump(),
                default_flow_style=False,
                sort_keys=False,
            )
        )

        return roadmap_path

    async def load_roadmap(self, path: Path) -> Roadmap:
        """Load a roadmap from disk.

        Args:
            path: Path to roadmap.json file or project directory.

        Returns:
            The loaded Roadmap instance.
        """
        path = Path(path)
        if path.is_dir():
            path = path / "roadmap.json"
        return Roadmap.model_validate_json(path.read_text())

    async def load_context(self, path: Path) -> ProjectContext:
        """Load project context from a YAML file.

        Args:
            path: Path to context.yaml file.

        Returns:
            The loaded ProjectContext instance.
        """
        path = Path(path)
        data = yaml.safe_load(path.read_text())
        return ProjectContext(**data)

    def get_resume_point(self, roadmap: Roadmap) -> str | None:
        """Find where generation stopped in an incomplete roadmap.

        Walks the hierarchy looking for the first incomplete item:
        - Milestone with no epics
        - Epic with no stories
        - Story with no tasks

        Args:
            roadmap: The roadmap to check.

        Returns:
            A description of the resume point, or None if complete.
        """
        for m_idx, milestone in enumerate(roadmap.milestones):
            if not milestone.epics:
                return (
                    f"Milestone {m_idx + 1} ({milestone.name}) - no epics generated"
                )

            for e_idx, epic in enumerate(milestone.epics):
                if not epic.stories:
                    return (
                        f"Milestone {m_idx + 1} ({milestone.name}), "
                        f"Epic {e_idx + 1} ({epic.name}) - no stories generated"
                    )

                for s_idx, story in enumerate(epic.stories):
                    if not story.tasks:
                        return (
                            f"Milestone {m_idx + 1} ({milestone.name}), "
                            f"Epic {e_idx + 1} ({epic.name}), "
                            f"Story {s_idx + 1} ({story.name}) - no tasks generated"
                        )

        return None

    @staticmethod
    def _slugify(name: str) -> str:
        """Convert a name to a filesystem-safe slug.

        Args:
            name: The name to slugify.

        Returns:
            Lowercase name with spaces and underscores replaced by hyphens.
        """
        return name.lower().replace(" ", "-").replace("_", "-")
