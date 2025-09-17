# Claude Code Roadmap Generation Guide

This guide shows you how to ask Claude Code to generate roadmaps that work perfectly with the arcane tools.

## Quick Start Prompt

Copy and paste this prompt to Claude Code to generate a compatible roadmap:

```
I need you to create a detailed project roadmap for [YOUR PROJECT DESCRIPTION]. 

Please format the output as a structured text file that follows this exact hierarchy:

## **MILESTONE 1: [Milestone Name]**
**Duration:** [X] hours
**Priority:** [Critical/High/Medium/Low]
**Goal:** [Brief description of milestone objective]

### **Benefits:**
- [Benefit 1]
- [Benefit 2]

### **Prerequisites:**
- [Prerequisite 1]
- [Prerequisite 2]

### **Technical Requirements:**
- [Technical requirement 1]
- [Technical requirement 2]

## **Epic [Epic Name]**
**Duration:** [X] hours
**Priority:** [Critical/High/Medium/Low]
**Goal:** [Brief description of epic objective]

### **Story [Story Name]**
**What it is:** [Description of the story]
**Duration:** [X] hours
**Priority:** [Critical/High/Medium/Low]

#### **Task [Task Name]**
**What to do:** [Detailed description of the task]
**Duration:** [X] hours
**Priority:** [Critical/High/Medium/Low]
**Claude Code Prompt:** ```
[Specific prompt for implementing this task with Claude Code]
```

Please create a comprehensive roadmap with multiple milestones, epics, stories, and tasks. Include specific Claude Code prompts for each task that would help implement that feature.
```

## Example Usage

### For a Web Application:
```
I need you to create a detailed project roadmap for building a modern e-commerce web application with React frontend and Node.js backend.

[Use the template above]
```

### For a Mobile App:
```
I need you to create a detailed project roadmap for developing a fitness tracking mobile app using React Native.

[Use the template above]
```

### For a Python Package:
```
I need you to create a detailed project roadmap for building a Python package for data analysis and visualization.

[Use the template above]
```

## Important Formatting Rules

### ✅ Correct Format:
- Use exactly `## **MILESTONE X: Name**` for milestones
- Use exactly `## **Epic Name**` for epics  
- Use exactly `### **Story Name**` for stories
- Use exactly `#### **Task Name**` for tasks
- Include `**Duration:** X hours` for each item
- Include `**Priority:** Level` for each item
- Use triple backticks for Claude Code prompts: ````

### ❌ Incorrect Format:
- Don't use `# Milestone` or `### Milestone` 
- Don't forget the double asterisks: `**MILESTONE**`
- Don't use different section headers
- Don't forget duration and priority fields

## Advanced Prompt Features

### Request Specific Technologies:
```
Include these technologies in the roadmap:
- Frontend: React with TypeScript
- Backend: Node.js with Express
- Database: PostgreSQL
- Deployment: Docker + AWS
- Testing: Jest and Cypress
```

### Request Specific Methodologies:
```
Structure the roadmap following:
- Agile/Scrum methodology
- TDD (Test-Driven Development)
- CI/CD pipeline setup
- Code review processes
```

### Request Time Estimates:
```
Provide realistic time estimates for:
- Junior developer (1-2 years experience)
- Mid-level developer (3-5 years experience)
- Senior developer (5+ years experience)
```

## Sample Output Structure

Here's what a properly formatted roadmap looks like:

```
## **MILESTONE 1: Foundation Setup**
**Duration:** 40 hours
**Priority:** Critical
**Goal:** Establish project foundation and development environment

### **Benefits:**
- Standardized development environment
- Automated testing and deployment
- Clean project structure

### **Prerequisites:**
- Node.js installed
- Git repository created
- Development tools configured

## **Epic Project Setup**
**Duration:** 16 hours
**Priority:** High
**Goal:** Configure initial project structure and tooling

### **Story Development Environment**
**What it is:** Set up the complete development environment with all necessary tools and configurations
**Duration:** 8 hours
**Priority:** High

#### **Task Initialize React Project**
**What to do:** Create a new React project with TypeScript template and configure initial project structure
**Duration:** 2 hours
**Priority:** High
**Claude Code Prompt:** ```
Create a new React project with TypeScript. Set up the following:
1. Create project with create-react-app typescript template
2. Configure ESLint and Prettier
3. Set up folder structure with components, pages, hooks, and utils
4. Add basic routing with React Router
5. Configure absolute imports
```
```

## Tips for Better Roadmaps

1. **Be Specific About Your Project:**
   - Include target users
   - Mention key features
   - Specify technical constraints

2. **Request Detailed Tasks:**
   - Ask for specific implementation steps
   - Include testing requirements
   - Request documentation tasks

3. **Include Non-Coding Tasks:**
   - Design and UX tasks
   - Documentation writing
   - Deployment and DevOps
   - Code review and testing

4. **Ask for Dependencies:**
   - Prerequisites between tasks
   - External service integrations
   - Third-party libraries needed

## Converting Existing Plans

If you already have a project plan, you can ask Claude to convert it:

```
I have this existing project plan: [PASTE YOUR PLAN]

Please convert this into the roadmap format that works with arcane tools. Use the exact format with milestones, epics, stories, and tasks. Include duration estimates and Claude Code prompts for each implementation task.
```

## Troubleshooting

### Common Issues:

1. **Parser doesn't recognize sections:**
   - Check that you're using exact formatting: `## **MILESTONE 1: Name**`
   - Ensure double asterisks around keywords

2. **Missing duration/priority:**
   - Every item should have `**Duration:** X hours`
   - Every item should have `**Priority:** Level`

3. **Claude Code prompts not parsed:**
   - Use triple backticks: ````
   - Place prompts after `**Claude Code Prompt:**`

### Getting Help:

If the parser still has issues, ask Claude to validate the format:

```
Please review this roadmap and ensure it follows the exact format needed for arcane tools. Check that all milestones, epics, stories, and tasks are properly formatted with the required fields.
```