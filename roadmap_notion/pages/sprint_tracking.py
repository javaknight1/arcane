"""Sprint tracking page creation module."""

from .base import BasePage


class SprintTrackingPage(BasePage):
    """Creates the sprint tracking page."""

    def create(self, parent_page_id: str, database_id: str = None, **kwargs) -> str:
        """Create the sprint tracking page."""
        print("Creating sprint tracking page...")

        content = [
            self.create_heading(1, "Sprint & Milestone Tracking"),
            self.create_paragraph("Organize and track work by sprints, milestones, and time-based iterations."),
            self.create_heading(2, "Current Sprint Backlog"),
            self.create_paragraph("Items planned for the current iteration.")
        ]

        if database_id:
            content.append(self.create_link_to_page(database_id))

        response = self.notion.pages.create(
            parent={"page_id": parent_page_id},
            icon={"type": "emoji", "emoji": "🏃‍♂️"},
            properties={"title": [{"type": "text", "text": {"content": "Sprint & Milestone Tracking"}}]},
            children=content
        )

        print(f"✅ Created sprint tracking page (ID: {response['id']})")
        return response["id"]