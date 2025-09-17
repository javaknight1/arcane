"""Roadmap generation engine using LLMs."""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from roadmap_notion.llm_clients import BaseLLMClient, LLMClientFactory
from roadmap_notion.prompts import PromptBuilder
from roadmap_notion.items import (
    Roadmap, Project, Milestone, Epic, Story, Task
)
from roadmap_notion.constants import PRIORITY_LEVELS, DURATION_MULTIPLIERS


class RoadmapGenerationEngine:
    """Engine for generating comprehensive project roadmaps using LLMs."""

    def __init__(self, llm_provider: str = 'claude'):
        self.llm_client = LLMClientFactory.create(llm_provider)
        self.prompt_builder = PromptBuilder()

    def generate_roadmap(
        self,
        idea: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Roadmap:
        """Generate a complete roadmap from an idea."""
        preferences = preferences or {}

        # Generate roadmap content using LLM
        prompt = self.prompt_builder.build_roadmap_prompt(
            idea_content=idea,
            timeline=preferences.get('timeline'),
            complexity=preferences.get('complexity'),
            team_size=preferences.get('team_size'),
            focus=preferences.get('focus')
        )

        roadmap_text = self.llm_client.generate(prompt)

        # Parse the generated text into roadmap objects
        roadmap = self._parse_roadmap_text(roadmap_text, idea)

        return roadmap

    def _parse_roadmap_text(self, text: str, project_name: str) -> Roadmap:
        """Parse LLM-generated text into roadmap objects."""
        # Create project root
        project = Project(
            name=project_name or "Generated Roadmap",
            description=f"Comprehensive roadmap generated on {datetime.now().strftime('%Y-%m-%d')}"
        )

        roadmap = Roadmap(project)

        # Parse the text line by line
        lines = text.split('\n')
        current_milestone = None
        current_epic = None
        current_story = None
        current_section = None
        section_content = []

        for line in lines:
            line = line.strip()

            # Check for Milestone
            if self._is_milestone(line):
                if current_section and section_content:
                    self._apply_section_content(
                        current_milestone or current_epic or current_story,
                        current_section,
                        section_content
                    )
                    section_content = []
                    current_section = None

                current_milestone = self._parse_milestone(line, project)
                current_epic = None
                current_story = None

            # Check for Epic
            elif self._is_epic(line):
                if current_section and section_content:
                    self._apply_section_content(
                        current_epic or current_story,
                        current_section,
                        section_content
                    )
                    section_content = []
                    current_section = None

                if current_milestone:
                    current_epic = self._parse_epic(line, current_milestone)
                    current_story = None

            # Check for Story
            elif self._is_story(line):
                if current_section and section_content:
                    self._apply_section_content(
                        current_story,
                        current_section,
                        section_content
                    )
                    section_content = []
                    current_section = None

                if current_epic:
                    current_story = self._parse_story(line, current_epic)

            # Check for Task
            elif self._is_task(line):
                if current_story:
                    self._parse_task(line, current_story)

            # Check for metadata sections
            elif self._is_metadata_section(line):
                if current_section and section_content:
                    self._apply_section_content(
                        current_milestone or current_epic or current_story,
                        current_section,
                        section_content
                    )
                current_section = self._get_section_type(line)
                section_content = []

            # Collect content for current section
            elif current_section and line:
                section_content.append(line)

        # Apply any remaining section content
        if current_section and section_content:
            self._apply_section_content(
                current_milestone or current_epic or current_story,
                current_section,
                section_content
            )

        return roadmap

    def _is_milestone(self, line: str) -> bool:
        """Check if line represents a milestone."""
        return bool(re.match(r'^##\s+Milestone\s+\d+:', line, re.IGNORECASE))

    def _is_epic(self, line: str) -> bool:
        """Check if line represents an epic."""
        return bool(re.match(r'^###\s+Epic\s+[\d.]+:', line, re.IGNORECASE))

    def _is_story(self, line: str) -> bool:
        """Check if line represents a story."""
        return bool(re.match(r'^####\s+Story\s+[\d.]+:', line, re.IGNORECASE))

    def _is_task(self, line: str) -> bool:
        """Check if line represents a task."""
        return bool(re.match(r'^#####\s+Task\s+[\d.]+:', line, re.IGNORECASE))

    def _is_metadata_section(self, line: str) -> bool:
        """Check if line starts a metadata section."""
        patterns = [
            r'^\*\*Goal/Description\*\*:',
            r'^\*\*Benefits\*\*:',
            r'^\*\*Prerequisites\*\*:',
            r'^\*\*Technical Requirements\*\*:',
            r'^\*\*Claude Code Prompt\*\*:'
        ]
        return any(re.match(pattern, line) for pattern in patterns)

    def _get_section_type(self, line: str) -> str:
        """Get the type of metadata section."""
        if 'Goal/Description' in line:
            return 'description'
        elif 'Benefits' in line:
            return 'benefits'
        elif 'Prerequisites' in line:
            return 'prerequisites'
        elif 'Technical Requirements' in line:
            return 'technical_requirements'
        elif 'Claude Code Prompt' in line:
            return 'claude_code_prompt'
        return None

    def _parse_milestone(self, line: str, project: Project) -> Milestone:
        """Parse a milestone from text."""
        match = re.match(r'^##\s+Milestone\s+(\d+):\s*(.+)', line, re.IGNORECASE)
        if match:
            number = match.group(1)
            name = match.group(2).strip()
            milestone = Milestone(
                name=name,
                number=number,
                parent=project,
                priority=PRIORITY_LEVELS.get('Milestone', 'Critical')
            )
            return milestone
        return None

    def _parse_epic(self, line: str, milestone: Milestone) -> Epic:
        """Parse an epic from text."""
        match = re.match(r'^###\s+Epic\s+([\d.]+):\s*(.+)', line, re.IGNORECASE)
        if match:
            number = match.group(1)
            name = match.group(2).strip()
            epic = Epic(
                name=name,
                number=number,
                parent=milestone,
                priority=PRIORITY_LEVELS.get('Epic', 'Critical')
            )
            return epic
        return None

    def _parse_story(self, line: str, epic: Epic) -> Story:
        """Parse a story from text."""
        match = re.match(r'^####\s+Story\s+([\d.]+):\s*(.+)', line, re.IGNORECASE)
        if match:
            number = match.group(1)
            name = match.group(2).strip()
            story = Story(
                name=name,
                number=number,
                parent=epic,
                priority=PRIORITY_LEVELS.get('Story', 'High')
            )
            return story
        return None

    def _parse_task(self, line: str, story: Story) -> Task:
        """Parse a task from text."""
        match = re.match(r'^#####\s+Task\s+([\d.]+):\s*(.+)', line, re.IGNORECASE)
        if match:
            number = match.group(1)
            name = match.group(2).strip()
            task = Task(
                name=name,
                number=number,
                parent=story,
                priority=PRIORITY_LEVELS.get('Task', 'Medium')
            )
            return task
        return None

    def _apply_section_content(self, item: Any, section: str, content: List[str]) -> None:
        """Apply section content to an item."""
        if not item or not section:
            return

        content_text = ' '.join(content).strip()

        if section == 'description':
            item.description = content_text
        elif section == 'benefits':
            item.benefits = content_text
        elif section == 'prerequisites':
            item.prerequisites = content_text
        elif section == 'technical_requirements':
            item.technical_requirements = content_text
        elif section == 'claude_code_prompt':
            item.claude_code_prompt = content_text

    def _parse_duration(self, text: str) -> Optional[int]:
        """Extract duration in hours from text."""
        for unit, multiplier in DURATION_MULTIPLIERS.items():
            pattern = rf'(\d+)\s*{unit}'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1)) * multiplier
        return None

    def refine_milestone(self, milestone: Milestone) -> Milestone:
        """Refine and expand a milestone with more detail."""
        prompt = self.prompt_builder.build_milestone_refinement_prompt(
            milestone_content=str(milestone)
        )
        refined_text = self.llm_client.generate(prompt)
        # Parse and update milestone
        # Implementation would update the existing milestone with new details
        return milestone

    def expand_epic(self, epic: Epic, project_context: Dict[str, str]) -> Epic:
        """Expand an epic with detailed stories and tasks."""
        prompt = self.prompt_builder.build_epic_expansion_prompt(
            epic_content=str(epic),
            project_type=project_context.get('project_type', 'web application'),
            tech_stack=project_context.get('tech_stack', 'modern full-stack'),
            team_experience=project_context.get('team_experience', 'intermediate')
        )
        expanded_text = self.llm_client.generate(prompt)
        # Parse and update epic with new stories and tasks
        return epic