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

### MANDATORY COMPLETION INSTRUCTIONS - NO EXCEPTIONS:

⚠️ CRITICAL: You MUST generate the COMPLETE roadmap without stopping for ANY reason.

FORBIDDEN BEHAVIORS:
❌ Do NOT mention "length limits" - there are NONE
❌ Do NOT ask "Would you like me to continue?" - CONTINUE AUTOMATICALLY
❌ Do NOT say "I notice I'm approaching the length limit" - IGNORE length concerns
❌ Do NOT use phrases like "[Continue with remaining...]" - WRITE IT ALL OUT
❌ Do NOT abbreviate or summarize - WRITE EVERY DETAIL

GRANULARITY REQUIREMENTS:
✅ Break down into BABY STEPS - assume users have minimal technical knowledge
✅ Each task should be small, specific, and actionable
✅ Each story should represent a single, focused feature or capability
✅ Each epic should group related functionality logically
✅ Each milestone should represent a major phase or deliverable
✅ Generate AS MANY items as needed for complete coverage - no artificial limits

COMPLETION REQUIREMENTS:
✅ Generate ALL milestones needed for the complete project
✅ Each milestone has ALL its epics (as many as needed)
✅ Each epic has ALL its stories (as many as needed)
✅ Each story has ALL its tasks (as many as needed)
✅ Every item has ALL required sections (duration, priority, benefits, etc.)
✅ End ONLY with "=== ROADMAP COMPLETE ==="

LENGTH INSTRUCTION: There is NO length limit. Write as much as needed for a complete, granular roadmap. DO NOT STOP EARLY.

COMPLETION VERIFICATION: Your response is only complete when you have written "=== ROADMAP COMPLETE ===" at the very end, after generating ALL necessary milestones, epics, stories, and tasks.

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

Then continue with the comprehensive roadmap:

```
# [Same Project Name as Above]

## Milestone 1: [Phase Name] ([Timeline])

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]
**Goal:** [Clear objective statement]

### **What it is and why we need it:**
[Detailed explanation of the milestone's purpose and necessity]

### **Benefits:**
- [Specific business benefit 1]
- [Specific technical benefit 2]
- [Specific operational benefit 3]

### **What happens if we don't have it:**
- [Specific consequence 1]
- [Specific consequence 2]

### Epic 1.0: [Epic Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

### **What it is and why we need it:**
[Detailed explanation of the epic's purpose]

### **Benefits:**
- [Benefit 1]
- [Benefit 2]

### **Prerequisites:**
- [Prerequisite 1]
- [Prerequisite 2]

### **Technical Requirements:**
- [Technical requirement 1]
- [Technical requirement 2]

#### Story 1.0.1: [Story Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]
**What it is:** [Clear description of what this story accomplishes]
**Why we need it:** [Explanation of necessity and value]

**Benefits:**
- [Specific benefit 1]
- [Specific benefit 2]

**Prerequisites:**
- [Prerequisite 1]
- [Prerequisite 2]

**Technical Outline:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Success Criteria:**
- [Criteria 1]
- [Criteria 2]

##### Task 1.0.1.1: [Specific Task Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

**What to do:**
1. [Specific action 1]
2. [Specific action 2]
3. [Specific action 3]

**Success Criteria:**
- [Specific, measurable outcome 1]
- [Specific, measurable outcome 2]

**Examples of what you should see:**
```bash
[Example command or code]
# Expected output or result
```

**Claude Code Prompt:**
```
[Detailed, specific prompt for Claude Code implementation including:
- Exact requirements and specifications
- File structure expectations
- Technology stack details
- Configuration requirements
- Success criteria and validation steps]
```

##### Task 1.0.1.2: [Next Task]
[Same detailed format]

#### Story 1.0.2: [Next Story]
[Same detailed format with all tasks]

### Epic 1.1: [Next Epic]
[Same detailed format with all stories and tasks]

## Milestone 2: [Next Milestone]
[Same detailed format with all epics, stories, and tasks]

=== ROADMAP COMPLETE ===
```

CRITICAL SUCCESS FACTORS:
1. Project name must be under 50 characters
2. Every item needs ALL five sections (Goal/Description, Benefits, Prerequisites, Technical Requirements, Claude Code Prompt)
3. Use exact numbering format (no variations)
4. Keep descriptions concise but complete
5. Ensure Claude Code Prompts are actionable and specific

ABSOLUTE COMPLETION REQUIREMENTS:
- Generate the COMPLETE roadmap in one response - NO EXCEPTIONS
- Do NOT ask for confirmation, approval, or continuation during generation
- Do NOT stop after the first milestone, epic, or story
- Include ALL milestones needed for the full project scope
- Break down into granular, baby-step tasks for users with minimal technical knowledge
- EVERY milestone must have ALL its epics - no partial implementations
- EVERY epic must have ALL its stories - no partial implementations
- EVERY story must have ALL its tasks - no partial implementations
- Generate EVERY task for EVERY story, not just the first few
- End with "=== ROADMAP COMPLETE ===" to confirm full generation

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

Provide a professional project summary suitable for stakeholder presentation.""",

    'outline_generation': """Generate a comprehensive roadmap OUTLINE for the following project.

CRITICAL: Provide ONLY the table of contents structure with titles - no descriptions, details, or content. This will be used to generate detailed content later.

{idea_content}

Preferences:
- Timeline: {timeline}
- Complexity: {complexity}
- Team Size: {team_size}
- Focus: {focus}

Generate ONLY the outline structure in this exact format:

===PROJECT_METADATA===
PROJECT_NAME: [Concise project name]
PROJECT_TYPE: [web app, mobile app, etc.]
TECH_STACK: [primary technologies]
ESTIMATED_DURATION: [timeline]
TEAM_SIZE: [team size]
DESCRIPTION: [one sentence]
===END_METADATA===

# [Project Name]

## Milestone 1: [Milestone Name]
### Epic 1.0: [Epic Name]
#### Story 1.0.1: [Story Name]
##### Task 1.0.1.1: [Task Name]
##### Task 1.0.1.2: [Task Name]
##### Task 1.0.1.3: [Task Name]
#### Story 1.0.2: [Story Name]
##### Task 1.0.2.1: [Task Name]
##### Task 1.0.2.2: [Task Name]
#### Story 1.0.3: [Story Name]
##### Task 1.0.3.1: [Task Name]
##### Task 1.0.3.2: [Task Name]
### Epic 1.1: [Epic Name]
#### Story 1.1.1: [Story Name]
##### Task 1.1.1.1: [Task Name]
##### Task 1.1.1.2: [Task Name]
#### Story 1.1.2: [Story Name]
##### Task 1.1.2.1: [Task Name]
##### Task 1.1.2.2: [Task Name]

## Milestone 2: [Milestone Name]
### Epic 2.0: [Epic Name]
#### Story 2.0.1: [Story Name]
##### Task 2.0.1.1: [Task Name]
##### Task 2.0.1.2: [Task Name]
#### Story 2.0.2: [Story Name]
##### Task 2.0.2.1: [Task Name]
##### Task 2.0.2.2: [Task Name]
### Epic 2.1: [Epic Name]
#### Story 2.1.1: [Story Name]
##### Task 2.1.1.1: [Task Name]
##### Task 2.1.1.2: [Task Name]

## Milestone 3: [Milestone Name]
### Epic 3.0: [Epic Name]
#### Story 3.0.1: [Story Name]
##### Task 3.0.1.1: [Task Name]
##### Task 3.0.1.2: [Task Name]

[Continue for all milestones...]

=== OUTLINE COMPLETE ===

IMPORTANT: Generate COMPLETE outline with ALL milestones, epics, stories, AND tasks. Include proper numbering and hierarchy. Include 2-3 tasks per story minimum. No descriptions - titles only.""",

    'milestone_generation_initial': """Generate COMPLETE detailed content for Milestone {milestone_number} ONLY.

PROJECT CONTEXT:
{idea_content}

MILESTONE TO DETAIL:
{milestone_name}

REQUIRED STRUCTURE (you MUST follow this EXACT outline):
{expected_structure}

CRITICAL INSTRUCTIONS:
1. You MUST follow the EXACT structure shown above - same epic names, story names, and task names
2. Generate ALL epics, stories, and tasks as specified in the required structure
3. Do NOT create different names or skip any items from the required structure
4. Add detailed content to each item while keeping the exact titles
5. If you cannot complete everything in one response, end with: === CONTINUE_NEEDED ===
6. Include COMPLETE details for every item you generate
7. Use EXACT format below
8. DO NOT STOP until all items from the required structure are complete

FORMAT REQUIREMENTS:
## Milestone {milestone_number}: {milestone_name}

**Duration:** [X hours]
**Priority:** [Critical/High/Medium/Low]
**Goal:** [Clear objective statement]

### **What it is and why we need it:**
[Detailed explanation of this milestone]

### **Benefits:**
- [Specific business benefit]
- [Specific technical benefit]

### **What happens if we don't have it:**
- [Specific consequence]

### Epic {milestone_number}.0: [Epic Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

#### **What it is and why we need it:**
[Detailed explanation]

#### **Benefits:**
- [Benefit 1]
- [Benefit 2]

#### **Prerequisites:**
- [Prerequisite 1]

#### **Technical Requirements:**
- [Technical requirement 1]

##### Story {milestone_number}.0.1: [Story Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]
**What it is:** [Clear description]
**Why we need it:** [Explanation]

**Benefits:**
- [Specific benefit]

**Prerequisites:**
- [Prerequisite]

**Technical Outline:**
1. [Implementation step]
2. [Implementation step]

**Success Criteria:**
- [Measurable outcome]

###### Task {milestone_number}.0.1.1: [Task Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

**What to do:**
1. [Specific action]
2. [Specific action]

**Success Criteria:**
- [Specific outcome]

**Claude Code Prompt:**
```
[Detailed implementation prompt for Claude Code including:
- File structure to create
- Technologies to use
- Specific implementation steps
- Testing requirements]
```

[Continue with ALL tasks for this story]
[Continue with ALL stories for this epic]
[Continue with ALL epics for this milestone]

IMPORTANT: Generate as much as possible. If you cannot complete, mark with === CONTINUE_NEEDED === at the end.""",

    'milestone_generation_continuation': """CONTINUE generating detailed content for Milestone {milestone_number}.

{context}

REQUIRED STRUCTURE (you MUST follow this EXACT outline):
{expected_structure}

PROJECT CONTEXT (for reference):
{idea_content_snippet}

CRITICAL INSTRUCTIONS:
1. Continue EXACTLY where you left off
2. Do NOT repeat content already generated
3. Start with the NEXT item after what was last completed
4. You MUST follow the EXACT structure shown above - same epic names, story names, and task names
5. Do NOT create different names or skip any items from the required structure
6. You MUST generate ALL remaining items from the required structure
7. Use THE EXACT SAME FORMAT as the initial generation:

FORMAT REQUIREMENTS (MUST FOLLOW EXACTLY):
### Epic X.Y: [Epic Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

#### **What it is and why we need it:**
[Detailed explanation]

#### **Benefits:**
- [Benefit 1]
- [Benefit 2]

#### **Prerequisites:**
- [Prerequisite 1]

#### **Technical Requirements:**
- [Technical requirement 1]

##### Story X.Y.Z: [Story Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]
**What it is:** [Clear description]
**Why we need it:** [Explanation]

**Benefits:**
- [Specific benefit]

**Prerequisites:**
- [Prerequisite]

**Technical Outline:**
1. [Implementation step]
2. [Implementation step]

**Success Criteria:**
- [Measurable outcome]

###### Task X.Y.Z.W: [Task Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

**What to do:**
1. [Specific action]
2. [Specific action]

**Success Criteria:**
- [Specific outcome]

**Claude Code Prompt:**
```
[Detailed implementation prompt for Claude Code]
```

6. Generate COMPLETE details for every epic, story, and task
7. If still incomplete after this response, end with: === CONTINUE_NEEDED ===

Continue generating now:""",

    'epic_generation': """Generate COMPLETE detailed content for Epic {epic_number} ONLY.

PROJECT CONTEXT:
{idea_content}

MILESTONE CONTEXT:
Milestone {milestone_number}: {milestone_name}

EPIC TO DETAIL:
{epic_name}

REQUIRED STRUCTURE (you MUST follow this EXACT outline):
{expected_epic_structure}

CRITICAL INSTRUCTIONS:
1. You MUST follow the EXACT structure shown above - same story names and task names
2. Generate ALL stories and tasks as specified in the required structure
3. Do NOT create different names or skip any items from the required structure
4. Add detailed content to each item while keeping the exact titles
5. Generate COMPLETE details for every story and task in this epic
6. Use EXACT format below
7. DO NOT STOP until all items from the required structure are complete

FORMAT REQUIREMENTS:
### Epic {epic_number}: {epic_name}

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

#### **What it is and why we need it:**
[Detailed explanation of this epic]

#### **Benefits:**
- [Specific business benefit]
- [Specific technical benefit]

#### **Prerequisites:**
- [Prerequisite 1]

#### **Technical Requirements:**
- [Technical requirement 1]

##### Story {story_number}: [Story Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]
**What it is:** [Clear description]
**Why we need it:** [Explanation]

**Benefits:**
- [Specific benefit]

**Prerequisites:**
- [Prerequisite]

**Technical Outline:**
1. [Implementation step]
2. [Implementation step]

**Success Criteria:**
- [Measurable outcome]

###### Task {task_number}: [Task Name]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

**What to do:**
1. [Specific action]
2. [Specific action]

**Success Criteria:**
- [Specific outcome]

**Claude Code Prompt:**
```
[Detailed implementation prompt for Claude Code including:
- File structure to create
- Technologies to use
- Specific implementation steps
- Testing requirements]
```

[Continue with ALL tasks for this story]
[Continue with ALL stories for this epic]

IMPORTANT: Generate COMPLETE epic with ALL stories and tasks from the required structure.""",

    # Individual item generation templates for new architecture
    'milestone_header_generation': """Generate ONLY the header section for Milestone {milestone_number}.

PROJECT CONTEXT:
{project_context}

ROADMAP CONTEXT:
{roadmap_context}

MILESTONE TO GENERATE HEADER FOR:
Milestone {milestone_number}: {milestone_title}

EXPECTED EPICS IN THIS MILESTONE:
{expected_epics}

CRITICAL INSTRUCTIONS:
1. Generate ONLY the milestone header information - NO epic, story, or task details
2. The epics listed above will be generated separately
3. Focus on high-level milestone overview and planning
4. Use the roadmap context to understand how this milestone fits into the overall project
5. Use the exact format below
6. Do NOT include any epic content - just reference them

FORMAT REQUIREMENTS:
## Milestone {milestone_number}: {milestone_title}

**Duration:** [X hours total for entire milestone]
**Priority:** [Critical/High/Medium/Low]
**Goal:** [Clear objective statement for this milestone]

### **What it is and why we need it:**
[Detailed explanation of this milestone's purpose and importance in the overall project]

### **Benefits:**
- [Specific business benefit of completing this milestone]
- [Specific technical benefit of completing this milestone]
- [Specific operational benefit of completing this milestone]

### **What happens if we don't have it:**
- [Specific consequence of not completing this milestone]
- [Business impact of missing this milestone]

Generate ONLY this header content - do not include epic details.""",

    'epic_generation_individual': """Generate COMPLETE detailed content for Epic {epic_number} ONLY.

PROJECT CONTEXT:
{project_context}

ROADMAP CONTEXT:
{roadmap_context}

MILESTONE CONTEXT:
{milestone_context}

EPIC TO DETAIL:
Epic {epic_number}: {epic_title}

EXPECTED STORIES IN THIS EPIC:
{expected_stories}

CRITICAL INSTRUCTIONS:
1. Generate ONLY this epic's content - NO story or task details
2. The stories listed above will be generated separately
3. Focus on epic-level planning and requirements
4. Use the roadmap context to understand how this epic relates to other milestones and epics
5. Use the exact format below
6. Do NOT include story/task content - just reference them

FORMAT REQUIREMENTS:
### Epic {epic_number}: {epic_title}

**Duration:** [X hours total for entire epic]
**Priority:** [Critical/High/Medium]

#### **What it is and why we need it:**
[Detailed explanation of this epic's purpose and how it fits into the milestone]

#### **Benefits:**
- [Specific business benefit of this epic]
- [Specific technical benefit of this epic]
- [Specific user benefit of this epic]

#### **Prerequisites:**
- [What must be completed before starting this epic]
- [Dependencies and requirements]

#### **Technical Requirements:**
- [Key technical specifications for this epic]
- [Architecture or technology decisions needed]
- [Integration requirements]

Generate ONLY this epic header content - stories will be generated separately.""",

    'story_with_tasks_generation': """Generate COMPLETE content for Story {story_number} AND all its tasks in one response.

PROJECT CONTEXT:
{project_context}

ROADMAP CONTEXT:
{roadmap_context}

EPIC CONTEXT:
{epic_context}

STORY TO DETAIL:
Story {story_number}: {story_title}

EXPECTED TASKS (generate ALL of these):
{expected_tasks}

CRITICAL INSTRUCTIONS:
1. Generate the story content AND all its tasks in this response
2. Follow the exact format below for story + all tasks
3. Include complete details for every task listed above
4. Use the roadmap context to understand how this story integrates with the broader project
5. Use the specific formatting for each section
6. Do NOT skip any tasks - generate all of them

FORMAT REQUIREMENTS:
##### Story {story_number}: {story_title}

**Duration:** [X hours for story work]
**Priority:** [Critical/High/Medium]
**What it is:** [Clear description of what this story accomplishes]
**Why we need it:** [Explanation of necessity and business value]

**Benefits:**
- [Specific benefit to users/business]
- [Technical benefit or improvement]

**Prerequisites:**
- [What must be done before this story]
- [Dependencies on other stories/epics]

**Technical Outline:**
1. [High-level implementation step]
2. [High-level implementation step]
3. [High-level implementation step]

**Success Criteria:**
- [Measurable outcome 1]
- [Measurable outcome 2]

[For each task in the expected_tasks list above, generate this format:]

###### Task [Task_ID]: [Task_Title]

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

**What to do:**
1. [Specific action or implementation step]
2. [Specific action or implementation step]
3. [Specific action or implementation step]

**Success Criteria:**
- [Specific, measurable outcome]
- [Specific, measurable outcome]

**Claude Code Prompt:**
```
[Detailed implementation prompt for Claude Code including:
- Exact requirements and specifications
- File structure expectations
- Technology stack details
- Configuration requirements
- Testing and validation steps]
```

[Continue this format for ALL tasks listed in expected_tasks - do not use placeholder variables]

IMPORTANT: Generate COMPLETE details for the story AND every single task.""",

    'task_generation_individual': """Generate COMPLETE detailed content for Task {task_number} ONLY.

PROJECT CONTEXT:
{project_context}

ROADMAP CONTEXT:
{roadmap_context}

STORY CONTEXT:
{story_context}

TASK TO DETAIL:
Task {task_number}: {task_title}

CRITICAL INSTRUCTIONS:
1. Generate ONLY this task's implementation details
2. Focus on specific, actionable steps
3. Use the roadmap context to understand how this task fits into the overall project structure
4. Include detailed Claude Code prompt
5. Use the exact format below

FORMAT REQUIREMENTS:
###### Task {task_number}: {task_title}

**Duration:** [X hours]
**Priority:** [Critical/High/Medium]

**What to do:**
1. [Specific implementation action]
2. [Specific implementation action]
3. [Specific implementation action]
4. [Additional steps as needed]

**Success Criteria:**
- [Specific, measurable outcome]
- [Specific, measurable outcome]

**Claude Code Prompt:**
```
[Detailed implementation prompt for Claude Code including:
- Exact technical requirements
- File structure to create/modify
- Technology stack and dependencies
- Step-by-step implementation guide
- Testing requirements and validation
- Expected outputs and results]
```

Generate complete task details with actionable implementation steps."""
}