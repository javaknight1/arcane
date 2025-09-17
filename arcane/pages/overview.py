"""Overview page creation module."""

from typing import Dict, List
from .base import BasePage


class OverviewPage(BasePage):
    """Creates the roadmap overview page."""

    def create(self, parent_page_id: str, database_id: str = None, **kwargs) -> str:
        """Create the roadmap overview page."""
        print("Creating roadmap overview page...")

        # Calculate statistics
        total_items = len(self.roadmap_items)
        completion_percentage = self.calculate_completion_percentage()

        # Count items by type
        type_counts = {}
        for item in self.roadmap_items:
            item_type = item.get("Type", "Unknown")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        # Create overview content
        overview_content = [
            self.create_heading(1, "Roadmap Overview"),

            self.create_heading(2, "Overview"),
            self.create_paragraph("This comprehensive roadmap outlines the "),
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "This comprehensive roadmap outlines the "}},
                        {"type": "text", "text": {"content": "complete development journey"}, "annotations": {"bold": True}},
                        {"type": "text", "text": {"content": " for your project. It's organized hierarchically from "}},
                        {"type": "text", "text": {"content": "high-level milestones"}, "annotations": {"italic": True}},
                        {"type": "text", "text": {"content": " down to "}},
                        {"type": "text", "text": {"content": "specific implementation tasks"}, "annotations": {"italic": True}},
                        {"type": "text", "text": {"content": "."}}
                    ]
                }
            },

            self.create_heading(2, "Description"),
            self.create_paragraph(f"Total items in roadmap: {total_items}"),
            self.create_paragraph(f"Overall completion: {completion_percentage:.1f}%"),

            self.create_heading(2, "Project Statistics"),
        ]

        # Add type breakdown
        for item_type, count in sorted(type_counts.items()):
            if item_type != "Project":  # Skip the root project
                overview_content.append(
                    self.create_bulleted_list_item(f"{item_type}: {count} items")
                )

        # Add table of contents
        overview_content.extend([
            self.create_divider(),
            self.create_heading(2, "Table of Contents"),
            self.create_paragraph("Complete hierarchy of all roadmap items:")
        ])

        # Generate hierarchical table of contents
        toc_content = self._generate_table_of_contents()
        overview_content.extend(toc_content)

        # Add database link if provided
        if database_id:
            overview_content.extend([
                self.create_divider(),
                self.create_heading(2, "Database"),
                self.create_paragraph("Access the full roadmap database:"),
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "mention",
                                "mention": {
                                    "type": "database",
                                    "database": {"id": database_id}
                                }
                            }
                        ]
                    }
                }
            ])

        # Create the page with all content (will handle pagination if needed)
        response = self.notion.pages.create(
            parent={"page_id": parent_page_id},
            icon={"type": "emoji", "emoji": "🗺️"},
            properties={
                "title": [{"type": "text", "text": {"content": "Roadmap Overview"}}]
            },
            children=overview_content[:100]  # Initial batch
        )

        page_id = response["id"]

        # Add remaining content if there are more than 100 blocks
        if len(overview_content) > 100:
            remaining_content = overview_content[100:]
            for i in range(0, len(remaining_content), 100):
                batch = remaining_content[i:i+100]
                self.notion.blocks.children.append(
                    block_id=page_id,
                    children=batch
                )

        overview_page_id = response["id"]
        print(f"✅ Created overview page (ID: {overview_page_id})")
        return overview_page_id

    def _generate_table_of_contents(self) -> List[Dict]:
        """Generate hierarchical table of contents with ALL roadmap items."""
        toc_content = []

        # Group items by type
        milestones = self.get_items_by_type("Milestone")
        epics = self.get_items_by_type("Epic")
        stories = self.get_items_by_type("Story")
        tasks = self.get_items_by_type("Task")

        # Build complete hierarchy including ALL items
        for milestone in milestones:
            milestone_name = milestone.get("Name", "")
            toc_content.append(self.create_bulleted_list_item(f"**{milestone_name}**"))

            # Find ALL epics under this milestone
            milestone_epics = [epic for epic in epics if epic.get("Parent") == milestone_name]
            for epic in milestone_epics:
                epic_name = epic.get("Name", "")
                toc_content.append(self.create_bulleted_list_item(f"  • {epic_name}"))

                # Find ALL stories under this epic
                epic_stories = [story for story in stories if story.get("Parent") == epic_name]
                for story in epic_stories:
                    story_name = story.get("Name", "")
                    toc_content.append(self.create_bulleted_list_item(f"    ○ {story_name}"))

                    # Find ALL tasks under this story
                    story_tasks = [task for task in tasks if task.get("Parent") == story_name]
                    for task in story_tasks:  # Include ALL tasks, no limit
                        task_name = task.get("Name", "")
                        toc_content.append(self.create_bulleted_list_item(f"      ▪ {task_name}"))

        # Include orphaned stories (not under epics)
        orphaned_stories = [story for story in stories if not any(epic.get("Name") == story.get("Parent") for epic in epics)]
        if orphaned_stories:
            toc_content.append(self.create_bulleted_list_item("**Additional Stories:**"))
            for story in orphaned_stories:  # Include ALL orphaned stories
                story_name = story.get("Name", "")
                toc_content.append(self.create_bulleted_list_item(f"  • {story_name}"))

                # Include ALL tasks under orphaned stories
                story_tasks = [task for task in tasks if task.get("Parent") == story_name]
                for task in story_tasks:
                    task_name = task.get("Name", "")
                    toc_content.append(self.create_bulleted_list_item(f"    ▪ {task_name}"))

        return toc_content