"""Task class - Specific implementation work."""

import re
from typing import Optional
from .base import Item, ItemStatus


class Task(Item):
    """Task represents specific implementation work."""

    def __init__(
        self,
        name: str,
        number: str,  # e.g., "1.0.1.1", "1.0.1.2", etc.
        parent: Optional[Item] = None,
        duration: Optional[int] = None,
        priority: str = 'Medium',
        status: str = 'Not Started',
        description: Optional[str] = None,
        benefits: Optional[str] = None,
        prerequisites: Optional[str] = None,
        technical_requirements: Optional[str] = None,
        claude_code_prompt: Optional[str] = None
    ):
        self.number = number
        super().__init__(
            name=f"Task {number}: {name}" if not name.startswith("Task") else name,
            item_type='Task',
            parent=parent,
            duration=duration,
            priority=priority,
            status=status,
            description=description,
            benefits=benefits,
            prerequisites=prerequisites,
            technical_requirements=technical_requirements,
            claude_code_prompt=claude_code_prompt
        )
        self.id = number
        if not self.validate_id():
            raise ValueError(f"Invalid Task ID: {self.id}")

        # Task-specific fields
        self.what_to_do = []
        self.success_criteria = []

    def validate_id(self) -> bool:
        """Task IDs must be number.number.number.number (1.0.1.1, 2.3.4.5, etc.)."""
        return bool(re.match(r'^[1-9]\d*\.\d+\.\d+\.\d+$', self.id))

    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid Task IDs."""
        return r'^[1-9]\d*\.\d+\.\d+\.\d+$'

    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate prompt for task generation (usually handled by story generation)."""
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        builder = RoadmapPromptBuilder()

        story_context = parent_context or ""
        if self.parent:
            story_context = f"Story {self.parent.id}: {self.parent.name.split(': ', 1)[-1] if ': ' in self.parent.name else self.parent.name}"

        return builder.build_custom_prompt(
            'task_generation_individual',
            task_number=self.id,
            task_title=self.name.split(': ', 1)[-1] if ': ' in self.name else self.name,
            project_context=project_context,
            story_context=story_context,
            roadmap_context=roadmap_context or ""
        )

    def parse_content(self, llm_response: str) -> None:
        """Parse task content from LLM response."""
        self.content = llm_response

        # Extract duration if present
        duration_match = re.search(r'\*\*Duration:\*\*\s*(\d+)\s*hours?', llm_response)
        if duration_match:
            self.duration = int(duration_match.group(1))

        # Extract priority if present
        priority_match = re.search(r'\*\*Priority:\*\*\s*(.+?)(?:\n|$)', llm_response)
        if priority_match:
            self.priority = priority_match.group(1).strip()

        # Extract "What to do" as list
        what_to_do_match = re.search(r'\*\*What to do:\*\*\n((?:\d+\. .+?\n?)+)', llm_response, re.DOTALL)
        if what_to_do_match:
            self.what_to_do = [line.strip() for line in what_to_do_match.group(1).strip().split('\n') if line.strip()]
            # Also set as description for compatibility
            self.description = '\n'.join(self.what_to_do)

        # Extract success criteria
        success_match = re.search(r'\*\*Success Criteria:\*\*\n((?:- .+?\n)+)', llm_response)
        if success_match:
            self.success_criteria = [s.strip('- ').strip()
                                   for s in success_match.group(1).split('\n') if s.strip()]

        # Extract Claude Code prompt
        claude_prompt_match = re.search(r'\*\*Claude Code Prompt:\*\*\n```\n?(.+?)```',
                                       llm_response, re.DOTALL)
        if claude_prompt_match:
            self.claude_code_prompt = claude_prompt_match.group(1).strip()

        self.update_generation_status(ItemStatus.GENERATED)