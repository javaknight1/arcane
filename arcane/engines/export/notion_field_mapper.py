"""Notion field mapping configuration and conversion."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class NotionPropertyType(Enum):
    """Notion database property types."""
    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    CHECKBOX = "checkbox"
    RELATION = "relation"


@dataclass
class FieldMapping:
    """Maps an item attribute to a Notion property."""
    item_attribute: str          # Attribute name on Item class
    notion_property: str         # Property name in Notion database
    property_type: NotionPropertyType
    default_value: Any = None
    capitalize_select: bool = True  # Whether to capitalize select values


# Base fields common to all item types
BASE_FIELD_MAPPINGS = [
    FieldMapping('name', 'Name', NotionPropertyType.TITLE),
    FieldMapping('item_type', 'Type', NotionPropertyType.SELECT),
    FieldMapping('status', 'Status', NotionPropertyType.SELECT, 'Not Started'),
    FieldMapping('priority', 'Priority', NotionPropertyType.SELECT, 'Medium'),
    FieldMapping('duration', 'Duration', NotionPropertyType.NUMBER, 0),
    FieldMapping('description', 'Goal/Description', NotionPropertyType.RICH_TEXT, ''),
    FieldMapping('benefits', 'Benefits', NotionPropertyType.RICH_TEXT, ''),
    FieldMapping('prerequisites', 'Prerequisites', NotionPropertyType.RICH_TEXT, ''),
    FieldMapping('technical_requirements', 'Technical Requirements', NotionPropertyType.RICH_TEXT, ''),
    FieldMapping('work_type', 'Work Type', NotionPropertyType.SELECT, 'implementation'),
    FieldMapping('complexity', 'Complexity', NotionPropertyType.SELECT, 'moderate'),
    FieldMapping('tags', 'Tags', NotionPropertyType.MULTI_SELECT, []),
]

# Task-specific field mappings
TASK_FIELD_MAPPINGS = BASE_FIELD_MAPPINGS + [
    FieldMapping('claude_code_prompt', 'Claude Code Prompt', NotionPropertyType.RICH_TEXT, ''),
]

# Story-specific field mappings
STORY_FIELD_MAPPINGS = BASE_FIELD_MAPPINGS + [
    FieldMapping('user_value', 'User Value', NotionPropertyType.RICH_TEXT, ''),
    FieldMapping('claude_code_prompt', 'Claude Code Prompt', NotionPropertyType.RICH_TEXT, ''),
]

# Epic-specific field mappings
EPIC_FIELD_MAPPINGS = BASE_FIELD_MAPPINGS + [
    FieldMapping('risks_and_mitigations', 'Risks', NotionPropertyType.RICH_TEXT, ''),
]

# Milestone-specific field mappings
MILESTONE_FIELD_MAPPINGS = BASE_FIELD_MAPPINGS + [
    FieldMapping('goal', 'Milestone Goal', NotionPropertyType.RICH_TEXT, ''),
    FieldMapping('risks_if_delayed', 'Risks', NotionPropertyType.RICH_TEXT, ''),
]


def get_mappings_for_item_type(item_type: str) -> List[FieldMapping]:
    """Get field mappings for an item type."""
    mapping_registry = {
        'Task': TASK_FIELD_MAPPINGS,
        'Story': STORY_FIELD_MAPPINGS,
        'Epic': EPIC_FIELD_MAPPINGS,
        'Milestone': MILESTONE_FIELD_MAPPINGS,
        'Project': BASE_FIELD_MAPPINGS,
    }
    return mapping_registry.get(item_type, BASE_FIELD_MAPPINGS)


class NotionFieldMapper:
    """Converts Item objects to Notion page properties."""

    # Notion's character limit per text block
    TEXT_LIMIT = 2000

    def __init__(self):
        self.missing_field_log = []
        self.truncation_log = []

    def item_to_notion_properties(self, item: 'Item') -> Dict[str, Any]:
        """Convert an Item to Notion page properties dict."""
        properties = {}
        mappings = get_mappings_for_item_type(item.item_type)

        for mapping in mappings:
            value = self._get_item_value(item, mapping)
            notion_value = self._convert_to_notion_format(value, mapping, item)

            if notion_value is not None:
                properties[mapping.notion_property] = notion_value

        return properties

    def _get_item_value(self, item: 'Item', mapping: FieldMapping) -> Any:
        """Get value from item, using default if not present."""
        value = getattr(item, mapping.item_attribute, None)

        # Check for empty strings, empty lists, None
        if value is None or value == '' or value == []:
            value = mapping.default_value

            if mapping.default_value is None:
                self.missing_field_log.append({
                    'item_id': getattr(item, 'id', 'unknown'),
                    'item_name': getattr(item, 'name', 'unknown'),
                    'field': mapping.notion_property,
                    'attribute': mapping.item_attribute
                })

        return value

    def _convert_to_notion_format(self, value: Any, mapping: FieldMapping, item: 'Item') -> Optional[Dict]:
        """Convert Python value to Notion property format."""
        if value is None:
            return None

        prop_type = mapping.property_type

        if prop_type == NotionPropertyType.TITLE:
            text = str(value)
            if len(text) > self.TEXT_LIMIT:
                self._log_truncation(item, mapping.notion_property, len(text))
                text = text[:self.TEXT_LIMIT - 3] + "..."
            return {
                "title": [{"text": {"content": text}}]
            }

        elif prop_type == NotionPropertyType.RICH_TEXT:
            text = str(value) if value else ""
            if len(text) > self.TEXT_LIMIT:
                self._log_truncation(item, mapping.notion_property, len(text))
                # Split into multiple text blocks for longer content
                blocks = []
                for i in range(0, len(text), self.TEXT_LIMIT):
                    blocks.append({"text": {"content": text[i:i+self.TEXT_LIMIT]}})
                return {"rich_text": blocks}
            return {
                "rich_text": [{"text": {"content": text}}] if text else []
            }

        elif prop_type == NotionPropertyType.NUMBER:
            try:
                return {"number": float(value) if value else 0}
            except (ValueError, TypeError):
                return {"number": 0}

        elif prop_type == NotionPropertyType.SELECT:
            if not value:
                return None
            # Capitalize first letter for select options
            display_value = str(value)
            if mapping.capitalize_select:
                display_value = display_value.capitalize()
            return {
                "select": {"name": display_value}
            }

        elif prop_type == NotionPropertyType.MULTI_SELECT:
            if isinstance(value, list):
                if not value:
                    return {"multi_select": []}
                return {
                    "multi_select": [{"name": str(v).strip()} for v in value if v and str(v).strip()]
                }
            elif isinstance(value, str):
                if not value:
                    return {"multi_select": []}
                tags = [t.strip() for t in value.split(',') if t.strip()]
                return {
                    "multi_select": [{"name": t} for t in tags]
                }
            return {"multi_select": []}

        elif prop_type == NotionPropertyType.CHECKBOX:
            return {"checkbox": bool(value)}

        elif prop_type == NotionPropertyType.DATE:
            if value:
                return {"date": {"start": str(value)}}
            return None

        return None

    def _log_truncation(self, item: 'Item', field: str, original_length: int) -> None:
        """Log when a field is truncated."""
        self.truncation_log.append({
            'item_id': getattr(item, 'id', 'unknown'),
            'item_name': getattr(item, 'name', 'unknown'),
            'field': field,
            'original_length': original_length,
            'limit': self.TEXT_LIMIT
        })

    def build_page_content_blocks(self, item: 'Item') -> List[Dict]:
        """Build Notion page content blocks for an item."""
        blocks = []

        # Add acceptance criteria as checklist for stories
        if hasattr(item, 'acceptance_criteria') and item.acceptance_criteria:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Acceptance Criteria"}}]
                }
            })

            for criterion in item.acceptance_criteria:
                if criterion and len(criterion.strip()) > 0:
                    blocks.append({
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [{"text": {"content": criterion[:self.TEXT_LIMIT]}}],
                            "checked": False
                        }
                    })

        # Add success criteria for epics/milestones
        if hasattr(item, 'success_criteria') and item.success_criteria:
            if not blocks:  # Only add header if we didn't already add acceptance criteria
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Success Criteria"}}]
                    }
                })

            for criterion in item.success_criteria:
                if criterion and len(criterion.strip()) > 0:
                    blocks.append({
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [{"text": {"content": criterion[:self.TEXT_LIMIT]}}],
                            "checked": False
                        }
                    })

        # Add key deliverables for milestones
        if hasattr(item, 'key_deliverables') and item.key_deliverables:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Key Deliverables"}}]
                }
            })

            for deliverable in item.key_deliverables:
                if deliverable and len(deliverable.strip()) > 0:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": deliverable[:self.TEXT_LIMIT]}}]
                        }
                    })

        # Add goals for epics
        if hasattr(item, 'goals') and item.goals:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Goals"}}]
                }
            })

            for goal in item.goals:
                if goal and len(goal.strip()) > 0:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": goal[:self.TEXT_LIMIT]}}]
                        }
                    })

        # Add Claude Code Prompt as code block for tasks
        if hasattr(item, 'claude_code_prompt') and item.claude_code_prompt:
            prompt = item.claude_code_prompt
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Implementation Prompt"}}]
                }
            })

            # Split long prompts into multiple code blocks if needed
            if len(prompt) > self.TEXT_LIMIT:
                for i in range(0, len(prompt), self.TEXT_LIMIT):
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"text": {"content": prompt[i:i+self.TEXT_LIMIT]}}],
                            "language": "markdown"
                        }
                    })
            else:
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"text": {"content": prompt}}],
                        "language": "markdown"
                    }
                })

        # Add user value for stories
        if hasattr(item, 'user_value') and item.user_value:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "User Value"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": item.user_value[:self.TEXT_LIMIT]}}],
                    "icon": {"emoji": "👤"}
                }
            })

        return blocks

    def get_missing_fields_report(self) -> str:
        """Generate report of fields that couldn't be mapped."""
        if not self.missing_field_log:
            return "All fields mapped successfully."

        lines = ["Missing Field Report:", "=" * 40]
        for entry in self.missing_field_log:
            lines.append(f"Item {entry['item_id']} ({entry['item_name']}): {entry['field']} (attr: {entry['attribute']})")
        return "\n".join(lines)

    def get_truncation_report(self) -> str:
        """Generate report of fields that were truncated."""
        if not self.truncation_log:
            return "No fields truncated."

        lines = ["Truncation Report:", "=" * 40]
        for entry in self.truncation_log:
            lines.append(f"Item {entry['item_id']}: {entry['field']} was {entry['original_length']} chars (limit: {entry['limit']})")
        return "\n".join(lines)
