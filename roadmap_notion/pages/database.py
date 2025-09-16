"""Database creation module."""

from typing import Dict, List
from .base import BasePage


class DatabaseCreator(BasePage):
    """Creates the main roadmap database."""

    def create(self, parent_page_id: str, **kwargs) -> str:
        """Create the roadmap database."""
        print("Creating roadmap database...")

        # Define select options
        type_options = [
            {"name": "Project", "color": "purple"},
            {"name": "Milestone", "color": "blue"},
            {"name": "Epic", "color": "green"},
            {"name": "Story", "color": "yellow"},
            {"name": "Task", "color": "orange"}
        ]

        status_options = [
            {"name": "Not Started", "color": "gray"},
            {"name": "In Progress", "color": "yellow"},
            {"name": "Blocked", "color": "red"},
            {"name": "Completed", "color": "green"},
            {"name": "On Hold", "color": "orange"}
        ]

        priority_options = [
            {"name": "Critical", "color": "red"},
            {"name": "High", "color": "orange"},
            {"name": "Medium", "color": "yellow"},
            {"name": "Low", "color": "green"}
        ]

        database_properties = {
            "Name": {"title": {}},
            "Type": {"select": {"options": type_options}},
            "Status": {"select": {"options": status_options}},
            "Priority": {"select": {"options": priority_options}},
            "Duration": {"number": {"format": "number"}},
            "Goal/Description": {"rich_text": {}},
            "Benefits": {"rich_text": {}},
            "Prerequisites": {"rich_text": {}},
            "Technical Requirements": {"rich_text": {}},
            "Claude Code Prompt": {"rich_text": {}}
        }

        response = self.notion.databases.create(
            parent={"page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Roadmap Database"}}],
            properties=database_properties
        )

        database_id = response["id"]

        # Add parent relation property after database creation
        self.notion.databases.update(
            database_id=database_id,
            properties={
                "Parent": {
                    "relation": {
                        "database_id": database_id,
                        "single_property": {}
                    }
                }
            }
        )

        print(f"Created database with ID: {database_id}")
        return database_id