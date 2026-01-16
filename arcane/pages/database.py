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

        work_type_options = [
            {"name": "Implementation", "color": "blue"},
            {"name": "Design", "color": "purple"},
            {"name": "Research", "color": "orange"},
            {"name": "Documentation", "color": "gray"},
            {"name": "Deployment", "color": "green"},
            {"name": "Maintenance", "color": "yellow"},
            {"name": "Configuration", "color": "brown"}
        ]

        complexity_options = [
            {"name": "Simple", "color": "green"},
            {"name": "Moderate", "color": "yellow"},
            {"name": "Complex", "color": "red"}
        ]

        database_properties = {
            # Core fields
            "Name": {"title": {}},
            "Type": {"select": {"options": type_options}},
            "Status": {"select": {"options": status_options}},
            "Priority": {"select": {"options": priority_options}},
            "Work Type": {"select": {"options": work_type_options}},
            "Complexity": {"select": {"options": complexity_options}},
            "Duration": {"number": {"format": "number"}},
            # Text fields - common
            "Goal/Description": {"rich_text": {}},
            "Benefits": {"rich_text": {}},
            "Prerequisites": {"rich_text": {}},
            "Technical Requirements": {"rich_text": {}},
            "Tags": {"multi_select": {"options": []}},
            # Task-specific
            "Claude Code Prompt": {"rich_text": {}},
            # Story-specific
            "User Value": {"rich_text": {}},
            # Milestone-specific
            "Milestone Goal": {"rich_text": {}},
            # Epic/Milestone risks
            "Risks": {"rich_text": {}},
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