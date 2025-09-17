"""Prompt builder for generating structured prompts from templates."""

from typing import Dict, Any, Optional
from arcane.constants import PROMPT_TEMPLATES, DEFAULT_TIMELINE, DEFAULT_COMPLEXITY, DEFAULT_TEAM_SIZE, DEFAULT_FOCUS


class PromptBuilder:
    """Builder class for creating prompts from predefined templates."""

    def __init__(self):
        self.templates = PROMPT_TEMPLATES

    def build_roadmap_prompt(
        self,
        idea_content: str,
        timeline: Optional[str] = None,
        complexity: Optional[str] = None,
        team_size: Optional[str] = None,
        focus: Optional[str] = None
    ) -> str:
        """Build a roadmap generation prompt."""
        params = {
            'idea_content': idea_content or "No specific idea provided - generate a generic web application roadmap",
            'timeline': timeline or DEFAULT_TIMELINE,
            'complexity': complexity or DEFAULT_COMPLEXITY,
            'team_size': team_size or DEFAULT_TEAM_SIZE,
            'focus': focus or DEFAULT_FOCUS
        }
        return self.templates['roadmap_generation'].format(**params)

    def build_milestone_refinement_prompt(self, milestone_content: str) -> str:
        """Build a prompt for refining a milestone."""
        return self.templates['milestone_refinement'].format(
            milestone_content=milestone_content
        )

    def build_epic_expansion_prompt(
        self,
        epic_content: str,
        project_type: str = "web application",
        tech_stack: str = "modern full-stack",
        team_experience: str = "intermediate"
    ) -> str:
        """Build a prompt for expanding an epic."""
        return self.templates['epic_expansion'].format(
            epic_content=epic_content,
            project_type=project_type,
            tech_stack=tech_stack,
            team_experience=team_experience
        )

    def build_task_detail_prompt(
        self,
        task_content: str,
        story_context: str,
        tech_stack: str,
        prerequisites: str = "None"
    ) -> str:
        """Build a prompt for detailing a task."""
        return self.templates['task_detail'].format(
            task_content=task_content,
            story_context=story_context,
            tech_stack=tech_stack,
            prerequisites=prerequisites
        )

    def build_project_summary_prompt(
        self,
        roadmap_overview: str,
        statistics: Dict[str, Any]
    ) -> str:
        """Build a prompt for generating a project summary."""
        return self.templates['project_summary'].format(
            roadmap_overview=roadmap_overview,
            milestone_count=statistics.get('milestones', 0),
            epic_count=statistics.get('epics', 0),
            story_count=statistics.get('stories', 0),
            task_count=statistics.get('tasks', 0),
            total_hours=statistics.get('total_duration_hours', 0)
        )

    def build_custom_prompt(self, template_key: str, **kwargs) -> str:
        """Build a prompt from a custom template."""
        if template_key not in self.templates:
            raise ValueError(f"Template '{template_key}' not found")
        return self.templates[template_key].format(**kwargs)

    def add_template(self, key: str, template: str) -> None:
        """Add a new template to the builder."""
        self.templates[key] = template

    def get_template_keys(self) -> list:
        """Get all available template keys."""
        return list(self.templates.keys())