"""Burndown analytics page creation module."""

from typing import Dict, List
from .base import BasePage


class BurndownPage(BasePage):
    """Creates the burndown analytics page."""

    def create(self, parent_page_id: str, database_id: str = None, **kwargs) -> str:
        """Create the burndown analytics page."""
        print("Creating burndown analytics page...")

        burndown_content = [
            self.create_heading(1, "Burndown Analytics"),
            self.create_paragraph("Track project progress over time with burndown charts and completion metrics."),

            self.create_heading(2, "Current Burndown Status"),
            self.create_paragraph(f"Total Items: {len(self.roadmap_items)}"),
            self.create_paragraph(f"Completion Rate: {self.calculate_completion_percentage():.1f}%"),

            self.create_heading(2, "Burndown Data Views"),
            self.create_paragraph("Use the database views below to track progress:")
        ]

        if database_id:
            burndown_content.append(self.create_link_to_page(database_id))

        response = self.notion.pages.create(
            parent={"page_id": parent_page_id},
            icon={"type": "emoji", "emoji": "📉"},
            properties={
                "title": [{"type": "text", "text": {"content": "Burndown Analytics"}}]
            },
            children=burndown_content
        )

        page_id = response["id"]
        print(f"✅ Created burndown analytics page (ID: {page_id})")
        return page_id