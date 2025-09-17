"""Notion import engine for roadmap data."""

import os
from typing import Dict, List, Any, Optional
from notion_client import Client

from arcane.items import Roadmap
from arcane.pages import (
    AnalyticsHubPage,
    BurndownPage,
    DashboardPage,
    DatabaseCreator,
    OverviewPage,
    SprintTrackingPage,
    TimelinePage,
    VelocityPage,
)


class NotionImportEngine:
    """Engine for importing roadmap data into Notion."""

    def __init__(self, notion_token: Optional[str] = None, parent_page_id: Optional[str] = None):
        """Initialize the Notion import engine."""
        self.notion_token = notion_token or os.getenv('NOTION_TOKEN')
        self.parent_page_id = parent_page_id or os.getenv('NOTION_PARENT_PAGE_ID')

        if not self.notion_token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN environment variable or pass notion_token parameter.")

        if not self.parent_page_id:
            raise ValueError("Parent page ID is required. Set NOTION_PARENT_PAGE_ID environment variable or pass parent_page_id parameter.")

        self.notion = Client(auth=self.notion_token)
        self.database_id = None
        self.page_ids = {}
        self.page_mapping = {}

    def import_roadmap(self, roadmap: Roadmap) -> Dict[str, str]:
        """Import a complete roadmap into Notion."""
        print("🚀 Starting Notion import...")

        # Create container page
        container_page_id = self._create_container_page(roadmap)

        # Create database
        self._create_database(roadmap, container_page_id)

        # Populate database with roadmap items
        self._populate_database(roadmap)

        # Create management pages
        self._create_management_pages(roadmap, container_page_id)

        # Print summary
        self._print_import_summary(container_page_id)

        return {
            'container_page_id': container_page_id,
            'database_id': self.database_id,
            **self.page_ids
        }

    def _create_container_page(self, roadmap: Roadmap) -> str:
        """Create the main container page for the roadmap."""
        print(f"Creating container page for {roadmap.project.name}...")

        response = self.notion.pages.create(
            parent={"page_id": self.parent_page_id},
            icon={"type": "emoji", "emoji": "🗺️"},
            properties={
                "title": [{"type": "text", "text": {"content": self._truncate_text(f"{roadmap.project.name} - Roadmap", 1990)}}]
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": roadmap.project.description or "Complete roadmap workspace with database, analytics, and management tools."}}
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📊 Roadmap Statistics"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": self._format_statistics(roadmap.get_statistics())}}
                        ]
                    }
                }
            ]
        )

        container_page_id = response["id"]
        print(f"✅ Created container page: {roadmap.project.name} (ID: {container_page_id})")
        return container_page_id

    def _create_database(self, roadmap: Roadmap, container_page_id: str) -> str:
        """Create the roadmap database."""
        # Convert roadmap items to dict format for DatabaseCreator
        items_dict = roadmap.to_dict_list()

        db_creator = DatabaseCreator(self.notion, items_dict)
        self.database_id = db_creator.create(container_page_id)
        return self.database_id

    def _populate_database(self, roadmap: Roadmap) -> None:
        """Populate the database with roadmap items."""
        if not self.database_id:
            raise ValueError("Database must be created before populating")

        print("Creating database pages...")

        icon_mapping = {
            "Project": "🚀",
            "Milestone": "🎯",
            "Epic": "⭐",
            "Story": "📝",
            "Task": "✅"
        }

        items = roadmap.get_all_items()
        total_items = len(items)

        for i, item in enumerate(items, 1):
            print(f"Creating page {i}/{total_items}: {item.name}")

            properties = self._build_item_properties(item)
            item_icon = icon_mapping.get(item.item_type, "📄")

            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                icon={"type": "emoji", "emoji": item_icon},
                properties=properties
            )

            self.page_mapping[item.name] = response["id"]
            print(f"✅ Created: {item.name}")

        # Set up parent relationships
        self._setup_parent_relationships(items)

    def _build_item_properties(self, item: Any) -> Dict[str, Any]:
        """Build properties dictionary for a database page."""
        # Truncate title to fit Notion's 2000 char limit, but preserve full content elsewhere
        truncated_name = self._truncate_text(item.name, 1990)  # Leave room for "..."

        properties = {
            "Name": {"title": [{"type": "text", "text": {"content": truncated_name}}]},
            "Type": {"select": {"name": item.item_type}},
            "Status": {"select": {"name": item.status}},
            "Priority": {"select": {"name": item.priority}}
        }

        # Add duration if present
        if item.duration:
            properties["Duration"] = {"number": item.duration}

        # Add text fields
        if item.description:
            content = item.description[:2000] if len(item.description) > 2000 else item.description
            properties["Goal/Description"] = {"rich_text": [{"type": "text", "text": {"content": content}}]}

        if item.benefits:
            content = item.benefits[:2000] if len(item.benefits) > 2000 else item.benefits
            properties["Benefits"] = {"rich_text": [{"type": "text", "text": {"content": content}}]}

        if item.prerequisites:
            content = item.prerequisites[:2000] if len(item.prerequisites) > 2000 else item.prerequisites
            properties["Prerequisites"] = {"rich_text": [{"type": "text", "text": {"content": content}}]}

        if item.technical_requirements:
            content = item.technical_requirements[:2000] if len(item.technical_requirements) > 2000 else item.technical_requirements
            properties["Technical Requirements"] = {"rich_text": [{"type": "text", "text": {"content": content}}]}

        if item.claude_code_prompt:
            content = item.claude_code_prompt[:2000] if len(item.claude_code_prompt) > 2000 else item.claude_code_prompt
            properties["Claude Code Prompt"] = {"rich_text": [{"type": "text", "text": {"content": content}}]}

        return properties

    def _setup_parent_relationships(self, items: List[Any]) -> None:
        """Set up parent-child relationships between database pages."""
        print("Setting up parent-child relationships...")

        for item in items:
            if item.parent and item.name in self.page_mapping:
                parent_name = item.parent.name
                if parent_name in self.page_mapping:
                    child_page_id = self.page_mapping[item.name]
                    parent_page_id = self.page_mapping[parent_name]

                    print(f"Setting parent: {item.name} -> {parent_name}")

                    try:
                        self.notion.pages.update(
                            page_id=child_page_id,
                            properties={"Parent": {"relation": [{"id": parent_page_id}]}}
                        )
                    except Exception as e:
                        print(f"Warning: Could not set parent relationship for {item.name}: {e}")

    def _create_management_pages(self, roadmap: Roadmap, container_page_id: str) -> None:
        """Create all management and analytics pages."""
        # Convert roadmap to dict format for page creators
        items_dict = roadmap.to_dict_list()

        # Create overview page
        overview_creator = OverviewPage(self.notion, items_dict)
        overview_id = overview_creator.create(container_page_id, database_id=self.database_id)
        self.page_ids["overview"] = overview_id

        # Create kanban board
        self._create_kanban_page(container_page_id)

        # Create analytics hub and subpages
        analytics_hub_creator = AnalyticsHubPage(self.notion, items_dict)
        analytics_hub_id = analytics_hub_creator.create(container_page_id)
        self.page_ids["analytics_hub"] = analytics_hub_id

        # Create analytics pages
        analytics_pages = [
            ("dashboard", DashboardPage, {"database_id": self.database_id}),
            ("burndown", BurndownPage, {"database_id": self.database_id}),
            ("sprint", SprintTrackingPage, {"database_id": self.database_id}),
            ("velocity", VelocityPage, {}),
            ("timeline", TimelinePage, {})
        ]

        for page_key, page_class, kwargs in analytics_pages:
            page_creator = page_class(self.notion, items_dict)
            page_id = page_creator.create(analytics_hub_id, **kwargs)
            self.page_ids[page_key] = page_id

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

    def _format_statistics(self, stats: Dict[str, Any]) -> str:
        """Format roadmap statistics for display."""
        return (
            f"• Milestones: {stats.get('milestones', 0)}\n"
            f"• Epics: {stats.get('epics', 0)}\n"
            f"• Stories: {stats.get('stories', 0)}\n"
            f"• Tasks: {stats.get('tasks', 0)}\n"
            f"• Total Items: {stats.get('total_items', 0)}\n"
            f"• Estimated Duration: {stats.get('total_duration_hours', 0)} hours\n"
            f"• Completion: {stats.get('completion_percentage', 0):.1f}%"
        )

    def _print_import_summary(self, container_page_id: str) -> None:
        """Print import completion summary."""
        print("\n" + "=" * 60)
        print("✅ NOTION IMPORT COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print("\n📄 Main Pages:")
        print(f"  🔗 Container: https://notion.so/{container_page_id.replace('-', '')}")
        print(f"  🔗 Database: https://notion.so/{self.database_id.replace('-', '')}")

        if self.page_ids:
            print("\n📊 Analytics & Management Pages:")
            for page_name, page_id in self.page_ids.items():
                formatted_name = page_name.replace('_', ' ').title()
                print(f"  🔗 {formatted_name}: https://notion.so/{page_id.replace('-', '')}")

        print("\n💡 Next Steps:")
        print("  1. Visit your Notion workspace")
        print("  2. Customize database views")
        print("  3. Start managing your roadmap!")
        print("=" * 60)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to fit Notion's character limits."""
        if len(text) <= max_length:
            return text

        # Truncate and add ellipsis
        truncated = text[:max_length-3] + "..."
        return truncated