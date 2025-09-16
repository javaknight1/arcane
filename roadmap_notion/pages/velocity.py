"""Velocity analytics page creation module."""

from .base import BasePage


class VelocityPage(BasePage):
    """Creates the velocity analytics page."""

    def create(self, parent_page_id: str, **kwargs) -> str:
        """Create the velocity analytics page."""
        print("Creating velocity analytics page...")

        content = [
            self.create_heading(1, "Velocity & Performance Analytics"),
            self.create_paragraph("Track team velocity, completion rates, and performance metrics over time."),
            self.create_heading(2, "Current Metrics"),
            self.create_paragraph(f"Total Items: {len(self.roadmap_items)}"),
            self.create_paragraph(f"Completion Rate: {self.calculate_completion_percentage():.1f}%")
        ]

        response = self.notion.pages.create(
            parent={"page_id": parent_page_id},
            icon={"type": "emoji", "emoji": "⚡"},
            properties={"title": [{"type": "text", "text": {"content": "Velocity & Performance Analytics"}}]},
            children=content
        )

        print(f"✅ Created velocity analytics page (ID: {response['id']})")
        return response["id"]