"""Analytics Hub page creation module."""

from typing import Dict, List
from .base import BasePage


class AnalyticsHubPage(BasePage):
    """Creates the Analytics Hub container page."""

    def create(self, parent_page_id: str, **kwargs) -> str:
        """Create the Analytics Hub page."""
        print("Creating Analytics Hub container page...")

        analytics_content = [
            self.create_heading(1, "Analytics Hub"),
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        self.create_text_block("Centralized hub for all project ", {"italic": True}),
                        self.create_text_block("analytics, metrics, and reporting", {"bold": True}),
                        self.create_text_block(" tools.", {"italic": True})
                    ]
                }
            },
            self.create_divider(),
            self.create_heading(2, "Available Analytics"),
            self.create_paragraph("This hub contains specialized analytics and reporting tools for comprehensive project insights:")
        ]

        response = self.notion.pages.create(
            parent={"page_id": parent_page_id},
            icon={"type": "emoji", "emoji": "📊"},
            properties={
                "title": [{"type": "text", "text": {"content": "Analytics Hub"}}]
            },
            children=analytics_content
        )

        analytics_hub_id = response["id"]
        print(f"✅ Created Analytics Hub page (ID: {analytics_hub_id})")
        return analytics_hub_id