"""Dashboard page creation module."""

from typing import Dict, List
from .base import BasePage


class DashboardPage(BasePage):
    """Creates the project dashboard page."""

    def create(self, parent_page_id: str, database_id: str = None, **kwargs) -> str:
        """Create the dashboard page."""
        print("Creating dashboard/analytics page...")

        # Calculate metrics
        total_items = len(self.roadmap_items)
        completed_items = len(self.get_items_by_status("Completed"))
        in_progress_items = len(self.get_items_by_status("In Progress"))
        not_started_items = len(self.get_items_by_status("Not Started"))
        blocked_items = len(self.get_items_by_status("Blocked"))

        completion_percentage = self.calculate_completion_percentage()

        dashboard_content = [
            self.create_heading(1, "Project Dashboard & Analytics"),
            self.create_paragraph(f"Real-time project analytics and key performance indicators. Last updated: Today"),

            self.create_heading(2, "Status Breakdown"),
            self.create_bulleted_list_item(f"**Total Items:** {total_items}"),
            self.create_bulleted_list_item(f"**Completed:** {completed_items} ({completion_percentage:.1f}%)"),
            self.create_bulleted_list_item(f"**In Progress:** {in_progress_items}"),
            self.create_bulleted_list_item(f"**Not Started:** {not_started_items}"),
            self.create_bulleted_list_item(f"**Blocked:** {blocked_items}"),

            self.create_divider(),
            self.create_heading(2, "Quick Actions"),
            self.create_bulleted_list_item("View all items in the main database"),
            self.create_bulleted_list_item("Check blocked items that need attention"),
            self.create_bulleted_list_item("Review progress by milestone"),

            self.create_divider(),
            self.create_heading(2, "Specialized Analytics"),
            self.create_paragraph("Access detailed analytics and reporting:"),
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "**Burndown Analytics** - Progress tracking and burndown data"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "**Sprint & Milestone Tracking** - Sprint planning and capacity management"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "**Velocity & Performance Analytics** - Team velocity and completion rates"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "**Timeline & Progress Tracking** - Time-based views and milestone planning"}}
                    ]
                }
            }
        ]

        # Add database link if provided
        if database_id:
            dashboard_content.extend([
                self.create_divider(),
                self.create_heading(2, "Main Database"),
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

        response = self.notion.pages.create(
            parent={"page_id": parent_page_id},
            icon={"type": "emoji", "emoji": "📊"},
            properties={
                "title": [{"type": "text", "text": {"content": "Dashboard & Analytics"}}]
            },
            children=dashboard_content
        )

        dashboard_page_id = response["id"]
        print(f"✅ Created dashboard page (ID: {dashboard_page_id})")
        return dashboard_page_id