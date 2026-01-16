"""Story class - User-facing functionality or major technical work."""

import re
from typing import Optional, List
from .base import Item, ItemStatus


class Story(Item):
    """Story represents user-facing functionality or major technical work."""

    def __init__(
        self,
        name: str,
        number: str,  # e.g., "1.0.1", "1.0.2", etc.
        parent: Optional[Item] = None,
        duration: Optional[int] = None,
        priority: str = 'High',
        status: str = 'Not Started',
        description: Optional[str] = None,
        benefits: Optional[str] = None,
        prerequisites: Optional[str] = None,
        technical_requirements: Optional[str] = None,
        claude_code_prompt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        work_type: Optional[str] = None,
        complexity: Optional[str] = None
    ):
        self.number = number
        super().__init__(
            name=f"Story {number}: {name}" if not name.startswith("Story") else name,
            item_type='Story',
            parent=parent,
            duration=duration,
            priority=priority,
            status=status,
            description=description,
            benefits=benefits,
            prerequisites=prerequisites,
            technical_requirements=technical_requirements,
            claude_code_prompt=claude_code_prompt,
            tags=tags,
            work_type=work_type,
            complexity=complexity
        )
        self.id = number
        if not self.validate_id():
            raise ValueError(f"Invalid Story ID: {self.id}")

        # Story-specific fields
        self.technical_outline = []
        self.success_criteria = []

    def add_task(self, task: 'Task') -> None:
        """Add a task to this story."""
        self.add_child(task)

    def validate_id(self) -> bool:
        """Story IDs must be number.number.number (1.0.1, 2.3.4, etc.)."""
        return bool(re.match(r'^[1-9]\d*\.\d+\.\d+$', self.id))

    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid Story IDs."""
        return r'^[1-9]\d*\.\d+\.\d+$'

    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate prompt for story generation (with all tasks)."""
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        builder = RoadmapPromptBuilder()

        # Build list of expected tasks
        task_list = "\n".join([f"- Task {child.id}: {child.name.split(': ', 1)[-1] if ': ' in child.name else child.name}"
                              for child in self.get_children_by_type('Task')])

        epic_context = parent_context or ""
        if self.parent:
            epic_context = f"Epic {self.parent.id}: {self.parent.name.split(': ', 1)[-1] if ': ' in self.parent.name else self.parent.name}"

        return builder.build_custom_prompt(
            'story_with_tasks_generation',
            story_number=self.id,
            story_title=self.name.split(': ', 1)[-1] if ': ' in self.name else self.name,
            project_context=project_context,
            epic_context=epic_context,
            expected_tasks=task_list,
            roadmap_context=roadmap_context or ""
        )

    def parse_content(self, llm_response: str) -> None:
        """Parse story and tasks content from LLM response."""
        self.content = llm_response

        # Parse story section (before the first task)
        story_section = llm_response.split('###### Task')[0] if '###### Task' in llm_response else llm_response

        # Extract duration if present
        duration_match = re.search(r'\*\*Duration:\*\*\s*(\d+)\s*hours?', story_section)
        if duration_match:
            self.duration = int(duration_match.group(1))

        # Extract priority if present
        priority_match = re.search(r'\*\*Priority:\*\*\s*(.+?)(?:\n|$)', story_section)
        if priority_match:
            self.priority = priority_match.group(1).strip()

        # Extract "What it is" as description
        what_match = re.search(r'\*\*What it is:\*\*\s*(.+?)(?:\n\*\*|$)', story_section, re.DOTALL)
        if what_match:
            self.description = what_match.group(1).strip()

        # Extract benefits
        benefits_match = re.search(r'\*\*Benefits:\*\*\n((?:- .+?\n)+)', story_section)
        if benefits_match:
            self.benefits = benefits_match.group(1).strip()

        # Extract prerequisites
        prereq_match = re.search(r'\*\*Prerequisites:\*\*\n((?:- .+?\n)+)', story_section)
        if prereq_match:
            self.prerequisites = prereq_match.group(1).strip()

        # Extract technical outline
        tech_outline_match = re.search(r'\*\*Technical Outline:\*\*\n((?:\d+\. .+?\n?)+)', story_section)
        if tech_outline_match:
            self.technical_outline = [line.strip() for line in tech_outline_match.group(1).strip().split('\n') if line.strip()]

        # Extract success criteria
        success_match = re.search(r'\*\*Success Criteria:\*\*\n((?:- .+?\n)+)', story_section)
        if success_match:
            self.success_criteria = [s.strip('- ').strip()
                                   for s in success_match.group(1).split('\n') if s.strip()]

        # Extract Work Type if present
        work_type_match = re.search(r'\*\*Work Type:\*\*\s*(.+?)(?:\n|$)', story_section)
        if work_type_match:
            self.work_type = work_type_match.group(1).strip().lower()

        # Extract Complexity if present
        complexity_match = re.search(r'\*\*Complexity:\*\*\s*(.+?)(?:\n|$)', story_section)
        if complexity_match:
            self.complexity = complexity_match.group(1).strip().lower()

        # Extract Tags if present
        tags_match = re.search(r'\*\*Tags:\*\*\s*(.+?)(?:\n|$)', story_section)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            # Split by comma and clean up each tag
            self.tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]

        # Now parse each task section and update corresponding task objects
        task_pattern = r'###### Task (\d+\.\d+\.\d+\.\d+): (.+?)\n(.*?)(?=###### Task |$)'
        task_matches = re.findall(task_pattern, llm_response, re.DOTALL)

        for task_id, task_title, task_content in task_matches:
            # Find corresponding task child and update its content
            for task in self.get_children_by_type('Task'):
                if task.id == task_id:
                    # Reconstruct full task content for parsing
                    full_task_content = f"###### Task {task_id}: {task_title}\n{task_content}"
                    task.parse_content(full_task_content)
                    break

        self.update_generation_status(ItemStatus.GENERATED)