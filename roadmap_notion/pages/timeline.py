"""Timeline tracking page creation module."""

from .base import BasePage


class TimelinePage(BasePage):
    """Creates the timeline tracking page."""

    def create(self, parent_page_id: str, **kwargs) -> str:
        """Create the timeline tracking page."""
        print("Creating timeline progress page...")

        content = [
            self.create_heading(1, "Timeline & Progress Tracking"),
            self.create_paragraph("Track project timeline, milestones, and schedule adherence."),
            self.create_heading(2, "Upcoming Work"),
            self.create_paragraph("Items scheduled for upcoming milestones and sprints.")
        ]

        response = self.notion.pages.create(
            parent={"page_id": parent_page_id},
            icon={"type": "emoji", "emoji": "📅"},
            properties={"title": [{"type": "text", "text": {"content": "Timeline & Progress Tracking"}}]},
            children=content
        )

        print(f"✅ Created timeline progress page (ID: {response['id']})")
        return response["id"]