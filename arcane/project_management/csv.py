"""CSV exporter for roadmaps.

Exports roadmaps to CSV format that can be imported into any PM tool
that accepts CSV imports (Jira, Asana, Trello, etc.).
"""

import csv
from pathlib import Path

from arcane.items import Roadmap

from .base import BasePMClient, ExportResult


class CSVClient(BasePMClient):
    """Exports roadmap to CSV format.

    CSV is the universal fallback for PM tools. Most tools can import
    CSV files, making this a reliable export option when native
    integrations aren't available.

    The CSV includes all roadmap item types (milestones, epics, stories,
    tasks) with Parent_ID columns to preserve hierarchy.
    """

    # CSV column headers
    FIELDNAMES = [
        "Type",
        "ID",
        "Name",
        "Description",
        "Parent_ID",
        "Priority",
        "Status",
        "Estimated_Hours",
        "Prerequisites",
        "Acceptance_Criteria",
        "Labels",
        "Claude_Code_Prompt",
    ]

    @property
    def name(self) -> str:
        """Return the client name."""
        return "CSV"

    async def validate_credentials(self) -> bool:
        """CSV export requires no credentials."""
        return True

    async def export(
        self,
        roadmap: Roadmap,
        output_path: str | None = None,
        **kwargs,
    ) -> ExportResult:
        """Export roadmap to a CSV file.

        Args:
            roadmap: The Roadmap to export.
            output_path: Optional path for the CSV file. If not provided,
                defaults to ./{project_slug}/roadmap.csv

        Returns:
            ExportResult with success status and file path.
        """
        # Determine output path
        if output_path:
            path = Path(output_path)
        else:
            project_slug = self._slugify(roadmap.project_name)
            path = Path(f"./{project_slug}/roadmap.csv")

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Flatten hierarchy to rows
        rows = self._flatten(roadmap)

        # Write CSV
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows)

            return ExportResult(
                success=True,
                target=self.name,
                items_created=len(rows),
                url=str(path.absolute()),
            )
        except OSError as e:
            return ExportResult(
                success=False,
                target=self.name,
                items_created=0,
                errors=[str(e)],
            )

    def _flatten(self, roadmap: Roadmap) -> list[dict]:
        """Flatten roadmap hierarchy into a list of row dictionaries.

        Walks the complete hierarchy: milestones -> epics -> stories -> tasks.
        Each row includes a Parent_ID to preserve the hierarchy relationships.
        """
        rows = []

        for milestone in roadmap.milestones:
            # Add milestone row
            rows.append(
                self._create_row(
                    type_name="Milestone",
                    item=milestone,
                    parent_id=roadmap.id,
                    goal=milestone.goal,
                )
            )

            for epic in milestone.epics:
                # Add epic row
                rows.append(
                    self._create_row(
                        type_name="Epic",
                        item=epic,
                        parent_id=milestone.id,
                        goal=epic.goal,
                        prerequisites=epic.prerequisites,
                    )
                )

                for story in epic.stories:
                    # Add story row
                    rows.append(
                        self._create_row(
                            type_name="Story",
                            item=story,
                            parent_id=epic.id,
                            acceptance_criteria=story.acceptance_criteria,
                        )
                    )

                    for task in story.tasks:
                        # Add task row
                        rows.append(
                            self._create_row(
                                type_name="Task",
                                item=task,
                                parent_id=story.id,
                                prerequisites=task.prerequisites,
                                acceptance_criteria=task.acceptance_criteria,
                                claude_code_prompt=task.claude_code_prompt,
                            )
                        )

        return rows

    def _create_row(
        self,
        type_name: str,
        item,
        parent_id: str,
        goal: str | None = None,
        prerequisites: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
        claude_code_prompt: str = "",
    ) -> dict:
        """Create a CSV row dictionary for an item.

        Args:
            type_name: Item type (Milestone, Epic, Story, Task).
            item: The roadmap item (has id, name, description, priority, status, labels).
            parent_id: ID of the parent item.
            goal: Optional goal field (for Milestone, Epic).
            prerequisites: Optional list of prerequisite IDs.
            acceptance_criteria: Optional list of acceptance criteria.
            claude_code_prompt: Optional prompt for Claude Code (tasks only).

        Returns:
            Dictionary suitable for csv.DictWriter.
        """
        # Get estimated hours (available on all item types via computed_field)
        estimated_hours = getattr(item, "estimated_hours", 0)

        # Use goal in description if available, otherwise use item description
        description = goal if goal else item.description

        return {
            "Type": type_name,
            "ID": item.id,
            "Name": item.name,
            "Description": description,
            "Parent_ID": parent_id,
            "Priority": item.priority.value,
            "Status": item.status.value,
            "Estimated_Hours": estimated_hours,
            "Prerequisites": ", ".join(prerequisites or []),
            "Acceptance_Criteria": " | ".join(acceptance_criteria or []),
            "Labels": ", ".join(item.labels),
            "Claude_Code_Prompt": claude_code_prompt,
        }

    @staticmethod
    def _slugify(name: str) -> str:
        """Convert a name to a filesystem-safe slug."""
        return name.lower().replace(" ", "-").replace("_", "-")
