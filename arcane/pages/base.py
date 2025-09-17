"""Base class for all page creators."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from notion_client import Client


class BasePage(ABC):
    """Base class for creating Notion pages."""

    def __init__(self, notion_client: Client, roadmap_items: List[Dict]):
        self.notion = notion_client
        self.roadmap_items = roadmap_items

    @abstractmethod
    def create(self, parent_page_id: str, **kwargs) -> str:
        """
        Create the page and return its ID.

        Args:
            parent_page_id: The parent page ID where this page should be created
            **kwargs: Additional arguments specific to the page type

        Returns:
            str: The created page ID
        """
        pass

    def create_text_block(self, content: str, annotations: Optional[Dict] = None) -> Dict:
        """Create a text block with optional formatting."""
        text_obj = {"type": "text", "text": {"content": content}}
        if annotations:
            text_obj["annotations"] = annotations
        return text_obj

    def create_paragraph(self, content: str, annotations: Optional[Dict] = None) -> Dict:
        """Create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [self.create_text_block(content, annotations)]
            }
        }

    def create_heading(self, level: int, content: str, annotations: Optional[Dict] = None) -> Dict:
        """Create a heading block (1, 2, or 3)."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [self.create_text_block(content, annotations)]
            }
        }

    def create_bulleted_list_item(self, content: str, annotations: Optional[Dict] = None) -> Dict:
        """Create a bulleted list item."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [self.create_text_block(content, annotations)]
            }
        }

    def create_link_to_page(self, page_id: str) -> Dict:
        """Create a link to another page."""
        return {
            "object": "block",
            "type": "link_to_page",
            "link_to_page": {
                "page_id": page_id
            }
        }

    def create_divider(self) -> Dict:
        """Create a divider block."""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }

    def get_items_by_type(self, item_type: str) -> List[Dict]:
        """Get all items of a specific type."""
        return [item for item in self.roadmap_items if item.get("Type") == item_type]

    def get_items_by_status(self, status: str) -> List[Dict]:
        """Get all items with a specific status."""
        return [item for item in self.roadmap_items if item.get("Status") == status]

    def calculate_completion_percentage(self) -> float:
        """Calculate overall completion percentage."""
        if not self.roadmap_items:
            return 0.0

        total_items = len(self.roadmap_items)
        completed_items = len(self.get_items_by_status("Completed"))
        return (completed_items / total_items) * 100