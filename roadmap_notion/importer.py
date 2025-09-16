#!/usr/bin/env python3
"""Clean, modular Notion Roadmap Importer.

Imports roadmap CSV data into Notion with organized page structure.
"""

import csv
import os
import sys

from dotenv import load_dotenv
from notion_client import Client

from .pages import (
    AnalyticsHubPage,
    BurndownPage,
    DashboardPage,
    DatabaseCreator,
    OverviewPage,
    SprintTrackingPage,
    TimelinePage,
    VelocityPage,
)


class NotionImporter:
    """Clean, modular Notion roadmap importer."""

    def __init__(self, notion_token: str, parent_page_id: str):
        """Initialize the importer with Notion credentials."""
        self.notion = Client(auth=notion_token)
        self.parent_page_id = parent_page_id
        self.roadmap_items = []
        self.database_id = None
        self.page_ids = {}

    def load_roadmap_data(self, csv_file: str) -> None:
        """Load roadmap data from CSV file."""
        print(f"Loading roadmap data from {csv_file}...")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.roadmap_items = list(reader)

        print(f"Loaded {len(self.roadmap_items)} roadmap items")

    def create_container_page(self) -> str:
        """Create the main container page for the roadmap."""
        print("Creating roadmap container page...")

        # Extract project name from first item
        project_name = "ServicePro Roadmap"
        if self.roadmap_items:
            first_item = self.roadmap_items[0]
            if first_item.get("Type") == "Project":
                project_name = first_item.get("Name", project_name)

        response = self.notion.pages.create(
            parent={"page_id": self.parent_page_id},
            icon={"type": "emoji", "emoji": "🗺️"},
            properties={
                "title": [{"type": "text", "text": {"content": f"{project_name} - Roadmap"}}]
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Complete roadmap workspace with database, analytics, and management tools."}}
                        ]
                    }
                }
            ]
        )

        container_page_id = response["id"]
        print(f"✅ Created container page: {project_name} - Roadmap (ID: {container_page_id})")
        return container_page_id

    def create_database(self, container_page_id: str) -> str:
        """Create the roadmap database."""
        db_creator = DatabaseCreator(self.notion, self.roadmap_items)
        self.database_id = db_creator.create(container_page_id)
        return self.database_id

    def populate_database(self) -> None:
        """Populate the database with roadmap items."""
        if not self.database_id:
            raise ValueError("Database must be created before populating")

        print("Creating database pages...")
        page_mapping = self._create_all_pages()
        self._setup_parent_relationships(page_mapping)

    def _create_all_pages(self) -> dict:
        """Create all database pages and return mapping."""
        page_mapping = {}
        icon_mapping = {
            "Project": "🚀", "Milestone": "🎯", "Epic": "⭐",
            "Story": "📝", "Task": "✅"
        }

        for i, item in enumerate(self.roadmap_items, 1):
            print(f"Creating page {i}/{len(self.roadmap_items)}: {item['Name']}")

            properties = self._build_page_properties(item)
            item_icon = icon_mapping.get(item.get("Type", "Task"), "📄")

            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                icon={"type": "emoji", "emoji": item_icon},
                properties=properties
            )

            page_mapping[item["Name"]] = response["id"]
            print(f"✅ Created: {item['Name']}")

        return page_mapping

    def _build_page_properties(self, item: dict) -> dict:
        """Build properties dictionary for a page."""
        properties = {
            "Name": {"title": [{"type": "text", "text": {"content": item["Name"]}}]},
            "Type": {"select": {"name": item.get("Type", "Story")}},
            "Status": {"select": {"name": item.get("Status", "Not Started")}},
            "Priority": {"select": {"name": item.get("Priority", "Medium")}}
        }

        # Add duration if present
        if item.get("Duration") and item["Duration"].isdigit():
            properties["Duration"] = {"number": int(item["Duration"])}

        # Add rich text fields
        text_fields = ["Goal/Description", "Benefits", "Prerequisites", "Technical Requirements", "Claude Code Prompt"]
        for field in text_fields:
            if item.get(field):
                content = item[field][:2000] if len(item[field]) > 2000 else item[field]
                properties[field] = {"rich_text": [{"type": "text", "text": {"content": content}}]}

        return properties

    def _setup_parent_relationships(self, page_mapping: dict) -> None:
        """Set up parent-child relationships between pages."""
        print("Setting up parent-child relationships...")
        for item in self.roadmap_items:
            if item.get("Parent") and item["Parent"] in page_mapping:
                child_page_id = page_mapping[item["Name"]]
                parent_page_id = page_mapping[item["Parent"]]

                print(f"Setting parent: {item['Name']} -> {item['Parent']}")

                try:
                    self.notion.pages.update(
                        page_id=child_page_id,
                        properties={"Parent": {"relation": [{"id": parent_page_id}]}}
                    )
                except Exception as e:
                    print(f"Warning: Could not set parent relationship for {item['Name']}: {e}")

    def create_management_pages(self, container_page_id: str) -> None:
        """Create all management and analytics pages."""
        # Create overview and kanban pages
        self._create_overview_page(container_page_id)
        self._create_kanban_page(container_page_id)

        # Create analytics hub and subpages
        analytics_hub_id = self._create_analytics_hub(container_page_id)
        self._create_analytics_pages(analytics_hub_id)

    def _create_overview_page(self, container_page_id: str) -> None:
        """Create the overview page."""
        overview_creator = OverviewPage(self.notion, self.roadmap_items)
        overview_id = overview_creator.create(container_page_id, database_id=self.database_id)
        self.page_ids["overview"] = overview_id

    def _create_kanban_page(self, container_page_id: str) -> None:
        """Create the kanban board page."""
        kanban_response = self.notion.pages.create(
            parent={"page_id": container_page_id},
            icon={"type": "emoji", "emoji": "📋"},
            properties={"title": [{"type": "text", "text": {"content": "Kanban Board"}}]},
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Kanban-style view of the roadmap database:"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "link_to_page",
                    "link_to_page": {"page_id": self.database_id}
                }
            ]
        )
        self.page_ids["kanban"] = kanban_response["id"]
        print(f"✅ Created kanban board page (ID: {kanban_response['id']})")

    def _create_analytics_hub(self, container_page_id: str) -> str:
        """Create analytics hub and return its ID."""
        analytics_hub_creator = AnalyticsHubPage(self.notion, self.roadmap_items)
        analytics_hub_id = analytics_hub_creator.create(container_page_id)
        self.page_ids["analytics_hub"] = analytics_hub_id
        return analytics_hub_id

    def _create_analytics_pages(self, analytics_hub_id: str) -> None:
        """Create all analytics pages under the Analytics Hub."""
        analytics_pages = [
            ("dashboard", DashboardPage, {"database_id": self.database_id}),
            ("burndown", BurndownPage, {"database_id": self.database_id}),
            ("sprint", SprintTrackingPage, {"database_id": self.database_id}),
            ("velocity", VelocityPage, {}),
            ("timeline", TimelinePage, {})
        ]

        for page_key, page_class, kwargs in analytics_pages:
            page_creator = page_class(self.notion, self.roadmap_items)
            page_id = page_creator.create(analytics_hub_id, **kwargs)
            self.page_ids[page_key] = page_id

    def run_import(self, csv_file: str) -> None:
        """Run the complete import process."""
        print("🚀 Starting Roadmap Import...")

        # Load data
        self.load_roadmap_data(csv_file)

        # Create container
        container_page_id = self.create_container_page()

        # Create database and populate it
        self.create_database(container_page_id)
        self.populate_database()

        # Create management pages
        self.create_management_pages(container_page_id)

        # Print summary
        self._print_import_summary(container_page_id)

    def _print_import_summary(self, container_page_id: str) -> None:
        """Print import completion summary with links."""
        print("✅ Import completed successfully!")

        # Main pages
        main_pages = [
            ("🔗 Database URL", self.database_id),
            ("📄 Overview Page", self.page_ids['overview']),
            ("📋 Kanban Board", self.page_ids['kanban']),
            ("📊 Analytics Hub", self.page_ids['analytics_hub'])
        ]

        for label, page_id in main_pages:
            print(f"{label}: https://notion.so/{page_id.replace('-', '')}")

        # Analytics pages
        print("\n📊 Specialized Analytics:")
        analytics_pages = [
            ("📉 Burndown Analytics", self.page_ids['burndown']),
            ("🏃‍♂️ Sprint Tracking", self.page_ids['sprint']),
            ("⚡ Velocity Analytics", self.page_ids['velocity']),
            ("📅 Timeline Progress", self.page_ids['timeline'])
        ]

        for label, page_id in analytics_pages:
            print(f"{label}: https://notion.so/{page_id.replace('-', '')}")

        print(f"\n📊 Created {len(self.roadmap_items)} roadmap items + {len(self.page_ids)} management pages")


def main():
    """Main function to run the importer."""
    load_dotenv()

    # Validate environment variables
    notion_token = os.getenv("NOTION_TOKEN")
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")

    if not all([notion_token, parent_page_id]):
        print("❌ Error: NOTION_TOKEN and NOTION_PARENT_PAGE_ID must be set in .env file")
        sys.exit(1)

    # Validate command line arguments
    if len(sys.argv) < 2:
        print("❌ Error: Please provide CSV file path")
        print("Usage: python -m roadmap_notion.importer <csv_file>")
        sys.exit(1)

    # Run import
    importer = NotionImporter(notion_token, parent_page_id)
    importer.run_import(sys.argv[1])


if __name__ == "__main__":
    main()