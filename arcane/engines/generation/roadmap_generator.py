"""Roadmap generation engine using LLMs."""

import re
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from arcane.llm_clients import BaseLLMClient, LLMClientFactory
from arcane.prompts import PromptBuilder
from arcane.prompts.idea_processor import IdeaProcessor
from arcane.engines.generation.metadata_extractor import MetadataExtractor, ProjectMetadata
from arcane.items import (
    Roadmap, Project, Milestone, Epic, Story, Task
)
from arcane.constants import PRIORITY_LEVELS, DURATION_MULTIPLIERS


class RoadmapGenerationEngine:
    """Engine for generating comprehensive project roadmaps using LLMs."""

    def __init__(self, llm_provider: str = 'claude', output_directory: Optional[str] = None):
        self.llm_client = LLMClientFactory.create(llm_provider)
        self.prompt_builder = PromptBuilder()
        self.idea_processor = IdeaProcessor()
        self.metadata_extractor = MetadataExtractor()

        # Set up output directory
        if output_directory:
            self.output_dir = Path(output_directory)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.save_outputs = True
        else:
            self.output_dir = None
            self.save_outputs = False

    def generate_roadmap(
        self,
        idea: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Roadmap:
        """Generate a complete roadmap from an idea."""
        preferences = preferences or {}

        # Process the raw idea into structured format
        print("📝 Processing and structuring idea content...")
        processed_idea = self.idea_processor.process_idea(idea)

        # Build structured prompt with processed idea
        structured_idea_content = self._build_structured_idea_content(processed_idea)

        prompt = self.prompt_builder.build_roadmap_prompt(
            idea_content=structured_idea_content,
            timeline=preferences.get('timeline'),
            complexity=preferences.get('complexity'),
            team_size=preferences.get('team_size'),
            focus=preferences.get('focus')
        )

        # Generate roadmap content using LLM
        print("🤖 Generating roadmap with optimized prompt...")
        roadmap_text = self.llm_client.generate(prompt)

        # Extract metadata from LLM output
        print("📋 Extracting project metadata...")
        metadata, cleaned_roadmap_text = self.metadata_extractor.extract_metadata(roadmap_text)
        project_filename_base = metadata.get_safe_filename_base()

        # Save outputs using extracted metadata
        if self.save_outputs:
            self._save_prompt(prompt, project_filename_base)
            self._save_llm_output(roadmap_text, project_filename_base)
            self._save_metadata(metadata, project_filename_base)

        # Parse the cleaned text into roadmap objects
        roadmap = self._parse_roadmap_text(cleaned_roadmap_text, metadata.project_name)

        # Save structured roadmap data
        if self.save_outputs:
            self._save_structured_roadmap(roadmap, project_filename_base)

        # Store metadata in roadmap for later use
        roadmap.metadata = metadata

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

    def _build_structured_idea_content(self, processed_idea: Dict[str, Any]) -> str:
        """Build structured idea content for the prompt."""
        features_formatted = self.idea_processor.format_features(processed_idea['key_features'])

        # Update the processed idea with formatted features
        processed_idea['key_features_formatted'] = features_formatted

        return self.idea_processor.build_structured_prompt(processed_idea)

    def _save_prompt(self, prompt: str, filename_base: str) -> None:
        """Save the generated prompt for debugging."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename_base}_prompt.txt"
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"💾 Saved prompt: {filepath}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save prompt: {e}")

    def _save_llm_output(self, output: str, filename_base: str) -> None:
        """Save raw LLM output for debugging and reprocessing."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename_base}_llm_output.md"
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"💾 Saved LLM output: {filepath}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save LLM output: {e}")

    def _save_metadata(self, metadata: ProjectMetadata, filename_base: str) -> None:
        """Save extracted project metadata."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename_base}_metadata.json"
            filepath = self.output_dir / filename

            self.metadata_extractor.save_metadata(metadata, filepath)
            print(f"💾 Saved metadata: {filepath}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save metadata: {e}")

    def _save_structured_roadmap(self, roadmap: Roadmap, filename_base: str) -> None:
        """Save structured roadmap data as JSON."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename_base}_structured.json"
            filepath = self.output_dir / filename

            # Convert roadmap to dictionary format
            roadmap_data = {
                'project': {
                    'name': roadmap.project.name,
                    'description': roadmap.project.description,
                    'generated_at': datetime.now().isoformat()
                },
                'statistics': roadmap.get_statistics(),
                'items': roadmap.to_dict_list()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(roadmap_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved structured roadmap: {filepath}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save structured roadmap: {e}")