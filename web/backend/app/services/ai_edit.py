"""AI-assisted editing service.

Sends an item + natural language command to the AI and returns the edited item.
This is a synchronous (single AI call) operation — no background jobs needed.
"""

import json

from pydantic import BaseModel

from arcane.core.clients import create_client
from arcane.core.items.base import Priority
from arcane.core.items.task import Task
from arcane.core.templates.loader import TemplateLoader


# --- Response models for each item type ---


class EditedMilestone(BaseModel):
    name: str
    description: str
    priority: Priority
    labels: list[str] = []
    goal: str
    target_date: str | None = None


class EditedEpic(BaseModel):
    name: str
    description: str
    priority: Priority
    labels: list[str] = []
    goal: str
    prerequisites: list[str] = []


class EditedStory(BaseModel):
    name: str
    description: str
    priority: Priority
    labels: list[str] = []
    acceptance_criteria: list[str]


RESPONSE_MODELS = {
    "milestone": EditedMilestone,
    "epic": EditedEpic,
    "story": EditedStory,
    "task": Task,
}

# Keys that should never be overwritten by AI output
PRESERVE_KEYS = {"id", "status", "epics", "stories", "tasks"}


async def run_ai_edit(
    item: dict,
    item_type: str,
    command: str,
    context_dict: dict,
    parent_context: dict | None,
    anthropic_api_key: str,
    model: str,
) -> dict:
    """Edit a roadmap item using AI based on a natural language command.

    Returns a new dict with the AI-edited fields merged into the original item,
    preserving id, status, and child collections.
    """
    client = create_client("anthropic", api_key=anthropic_api_key, model=model)
    templates = TemplateLoader()

    # Strip children from the item before sending to AI
    item_for_ai = {k: v for k, v in item.items() if k not in ("epics", "stories", "tasks")}
    current_item_json = json.dumps(item_for_ai, indent=2)

    system_prompt, user_prompt = templates.render_edit(
        item_type=item_type,
        current_item=current_item_json,
        command=command,
        project_context=context_dict,
        parent_context=parent_context,
    )

    response_model = RESPONSE_MODELS[item_type]
    result = await client.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=response_model,
        level=item_type,
    )

    # Merge AI result into a copy of the original, preserving protected keys
    edited = dict(item)
    ai_data = result.model_dump()
    for key, value in ai_data.items():
        if key not in PRESERVE_KEYS:
            # Convert enums to their string values
            if hasattr(value, "value"):
                value = value.value
            edited[key] = value

    return edited
