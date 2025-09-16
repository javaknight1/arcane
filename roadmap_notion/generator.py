"""Roadmap Generator - Uses LLMs to generate comprehensive project roadmaps."""

from datetime import datetime
from typing import Dict, Any


class RoadmapGenerator:
    """Generates project roadmaps using LLM providers."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def create_roadmap_prompt(self, idea_content: str, preferences: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for roadmap generation."""

        # Base prompt template
        base_prompt = """You are a senior technical product manager and architect tasked with creating a comprehensive project roadmap. Generate a detailed, actionable roadmap based on the provided project idea and preferences.

## Project Idea:
{idea_content}

## Project Preferences:
- Timeline: {timeline}
- Technical Complexity: {complexity}
- Team Size: {team_size}
- Primary Focus: {focus}

## Roadmap Requirements:

### Structure:
Create a hierarchical roadmap with this exact format:
```
# PROJECT_NAME

## Milestone 1: [Milestone Name]
### Epic 1.0: [Epic Name]
#### Story 1.0.1: [Story Name]
- **Goal/Description**: [Clear description of what needs to be accomplished]
- **Benefits**: [Business and technical benefits]
- **Prerequisites**: [What needs to be done first]
- **Technical Requirements**: [Technical specifications and constraints]
- **Claude Code Prompt**: [Specific prompt for implementing this story with Claude Code]

##### Task 1.0.1.1: [Task Name]
- **Goal/Description**: [Specific implementation details]
- **Benefits**: [Why this task is important]
- **Prerequisites**: [Dependencies and requirements]
- **Technical Requirements**: [Technical specs for this task]
- **Claude Code Prompt**: [Detailed prompt for Claude Code to implement this specific task]

##### Task 1.0.1.2: [Another Task Name]
[Same format as above]

#### Story 1.0.2: [Another Story Name]
[Same format as above with tasks]

### Epic 1.1: [Another Epic Name]
[Same format as above with stories and tasks]

## Milestone 2: [Next Milestone Name]
[Same format as above]
```

### Content Guidelines:

1. **Milestones**: 3-6 major phases that represent significant business value delivery
2. **Epics**: 2-4 epics per milestone, each representing a major feature area or technical component
3. **Stories**: 2-6 stories per epic, each representing user-facing functionality or major technical work
4. **Tasks**: 3-8 tasks per story, each representing specific implementation work

### Technical Detail Requirements:

1. **Architecture Considerations**: Include database design, API structure, frontend architecture
2. **Technology Stack**: Suggest appropriate technologies based on complexity and team size
3. **Infrastructure**: Include deployment, monitoring, and scalability considerations
4. **Testing Strategy**: Unit tests, integration tests, end-to-end testing
5. **Security**: Authentication, authorization, data protection
6. **Performance**: Optimization strategies and performance requirements

### Claude Code Prompts:
Each story and task must include a "Claude Code Prompt" that provides specific, actionable instructions for implementing that piece of functionality using Claude Code. These prompts should:
- Be specific enough to guide implementation
- Include file structures and naming conventions
- Specify testing requirements
- Include any necessary configuration or setup steps

### Industry Best Practices:
- Follow agile development principles
- Include proper CI/CD pipeline setup
- Consider mobile-first or responsive design where applicable
- Include proper error handling and logging
- Plan for scalability and maintainability
- Include documentation and knowledge transfer

### Timeline Considerations:
- Distribute work evenly across the specified timeline
- Include buffer time for testing and bug fixes
- Consider team ramp-up time
- Plan for iterative development and feedback cycles

Generate a comprehensive roadmap that balances technical depth with practical implementation guidance. Ensure each milestone delivers meaningful business value and builds toward the overall project goals."""

        defaults = {
            'idea_content': idea_content or "No specific idea provided - generate a generic web application roadmap",
            'timeline': preferences.get('timeline', '6-months'),
            'complexity': preferences.get('complexity', 'moderate'),
            'team_size': preferences.get('team_size', '2-3'),
            'focus': preferences.get('focus', 'mvp')
        }
        return base_prompt.format(**defaults)

    def generate(self, idea_content: str, preferences: Dict[str, Any]) -> str:
        """Generate a comprehensive roadmap using the selected LLM."""
        prompt = self.create_roadmap_prompt(idea_content, preferences)
        roadmap_content = self.llm_client.generate(prompt)

        metadata_fields = {
            'Generated': self._get_timestamp(),
            'LLM Provider': self.llm_client.provider,
            'Timeline': preferences.get('timeline', 'Not specified'),
            'Complexity': preferences.get('complexity', 'Not specified'),
            'Team Size': preferences.get('team_size', 'Not specified'),
            'Focus': preferences.get('focus', 'Not specified')
        }

        metadata_lines = [f"**{key}**: {value}" for key, value in metadata_fields.items()]
        metadata = "# Generated Roadmap\n" + "\n".join(metadata_lines) + "\n\n---\n\n"

        return metadata + roadmap_content

    def _get_timestamp(self) -> str:
        """Get current timestamp in readable format."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

