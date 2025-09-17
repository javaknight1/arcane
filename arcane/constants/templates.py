"""Prompt templates for LLM generation."""

PROMPT_TEMPLATES = {
    'roadmap_generation': """You are a senior technical product manager and architect tasked with creating a comprehensive project roadmap. Generate a detailed, actionable roadmap based on the provided project idea and preferences.

CRITICAL FORMATTING REQUIREMENTS:
- Use EXACT heading formats: # PROJECT_NAME, ## Milestone N:, ### Epic N.N:, #### Story N.N.N:, ##### Task N.N.N.N:
- Each item MUST include ALL required sections: Goal/Description, Benefits, Prerequisites, Technical Requirements, Claude Code Prompt
- Use consistent numbering: Milestone 1, Epic 1.0, Story 1.0.1, Task 1.0.1.1
- Keep names concise but descriptive (under 80 characters)
- Ensure proper markdown formatting with no extra spaces or characters

## Structured Project Analysis:
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

### COMPLETION INSTRUCTIONS:
YOU MUST generate the complete roadmap without stopping. Do not include phrases like:
- "I'll continue generating..."
- "Would you like me to continue..."
- "Let me know if this meets your requirements..."
- "Should I proceed with..."

Generate ALL milestones, epics, stories, and tasks in a single complete response. The roadmap should be production-ready and complete.

MANDATORY OUTPUT FORMAT - FOLLOW EXACTLY:

Start your response with metadata in this exact format:
```
===PROJECT_METADATA===
PROJECT_NAME: [Concise project name, 3-50 characters, no special characters]
PROJECT_TYPE: [web app, mobile app, desktop app, CLI tool, platform, etc.]
TECH_STACK: [primary technologies, e.g., "React, Node.js, PostgreSQL"]
ESTIMATED_DURATION: [timeline estimate, e.g., "6 months"]
TEAM_SIZE: [recommended team size, e.g., "3-5 developers"]
DESCRIPTION: [one-sentence project description]
===END_METADATA===
```

Then continue with the roadmap:

```
# [Same Project Name as Above]

## Milestone 1: [Phase Name]
### Epic 1.0: [Epic Name]
#### Story 1.0.1: [Story Name]
**Goal/Description**: [Clear description]
**Benefits**: [Business and technical benefits]
**Prerequisites**: [Dependencies]
**Technical Requirements**: [Specifications]
**Claude Code Prompt**: [Implementation guidance]

##### Task 1.0.1.1: [Task Name]
**Goal/Description**: [Specific details]
**Benefits**: [Task importance]
**Prerequisites**: [Requirements]
**Technical Requirements**: [Task specs]
**Claude Code Prompt**: [Detailed implementation prompt]

##### Task 1.0.1.2: [Next Task]
[Same format]

#### Story 1.0.2: [Next Story]
[Same format with tasks]

### Epic 1.1: [Next Epic]
[Same format]

## Milestone 2: [Next Milestone]
[Same format]
```

CRITICAL SUCCESS FACTORS:
1. Project name must be under 50 characters
2. Every item needs ALL five sections (Goal/Description, Benefits, Prerequisites, Technical Requirements, Claude Code Prompt)
3. Use exact numbering format (no variations)
4. Keep descriptions concise but complete
5. Ensure Claude Code Prompts are actionable and specific

IMPORTANT COMPLETION REQUIREMENTS:
- Generate the COMPLETE roadmap in one response
- Do NOT ask for confirmation or approval during generation
- Do NOT stop after the first milestone
- Include ALL milestones needed for the full project (typically 3-6 milestones)
- Each milestone should have 2-4 epics, each epic should have 2-6 stories, each story should have 3-8 tasks
- End with a clear completion marker, not a request for feedback

Generate a comprehensive, COMPLETE roadmap that balances technical depth with practical implementation guidance. Ensure each milestone delivers meaningful business value and builds toward the overall project goals. Generate the entire roadmap from start to finish without stopping for confirmation.""",

    'milestone_refinement': """Refine and expand the following milestone with more detailed epics, stories, and tasks:

## Current Milestone:
{milestone_content}

## Requirements:
- Add more technical depth to existing items
- Ensure all stories have comprehensive Claude Code prompts
- Include specific technical requirements for each task
- Add realistic time estimates
- Include clear dependencies between items

Provide the refined milestone with all the detailed structure.""",

    'epic_expansion': """Expand the following epic with detailed stories and tasks:

## Epic:
{epic_content}

## Context:
- Project Type: {project_type}
- Technical Stack: {tech_stack}
- Team Experience: {team_experience}

## Requirements:
- Create 3-5 user stories for this epic
- Each story should have 4-6 specific tasks
- Include detailed technical requirements
- Provide comprehensive Claude Code prompts for implementation
- Consider testing, documentation, and deployment tasks

Generate the expanded epic with complete story and task breakdown.""",

    'task_detail': """Create a detailed implementation plan for the following task:

## Task:
{task_content}

## Context:
- Parent Story: {story_context}
- Technical Stack: {tech_stack}
- Prerequisites: {prerequisites}

## Requirements:
- Provide step-by-step implementation guide
- Include specific code structure and file organization
- Define clear acceptance criteria
- Specify testing requirements
- Create a detailed Claude Code prompt for implementation
- Estimate time required (in hours)

Generate the detailed task implementation plan.""",

    'project_summary': """Generate a comprehensive project summary based on the following roadmap:

## Roadmap Overview:
{roadmap_overview}

## Statistics:
- Total Milestones: {milestone_count}
- Total Epics: {epic_count}
- Total Stories: {story_count}
- Total Tasks: {task_count}
- Estimated Duration: {total_hours} hours

## Requirements:
- Executive summary (2-3 paragraphs)
- Key deliverables and outcomes
- Technology stack summary
- Risk assessment
- Resource requirements
- Success metrics

Provide a professional project summary suitable for stakeholder presentation."""
}