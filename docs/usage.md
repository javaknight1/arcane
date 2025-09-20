# Usage Guide

This guide covers how to use the Arcane CLI tool for generating and importing roadmaps.

## Quick Start

### Generate and Import a Complete Roadmap

The easiest way to get started is with the interactive CLI:

```bash
python -m arcane
```

This will:
1. Prompt you to select an LLM provider
2. Ask for your project idea file (optional)
3. Collect roadmap preferences
4. Generate the roadmap using AI
5. Convert to CSV format
6. Import to Notion with full analytics

### Command Overview

The tool provides several commands for different workflows:

```bash
# Interactive mode (recommended for first-time users)
python -m arcane

# Generate roadmap only
python -m arcane generate

# Import existing CSV
python -m arcane import <csv_file>

# Parse text file to CSV
python -m arcane parse <text_file> [output_csv]
```

## Detailed Workflows

### 1. Full Automated Workflow

For complete automation from idea to Notion:

```bash
python -m arcane
```

**Process:**
1. **LLM Selection**: Choose from Claude, OpenAI, or Gemini
2. **Idea Input**: Provide a text file describing your project (optional)
3. **Preferences**: Configure timeline, complexity, team size, and focus
4. **Generation**: AI creates a comprehensive roadmap
5. **Conversion**: Automatically converts to CSV format
6. **Import**: Creates Notion workspace with database and analytics

**Output in Notion:**
- Main roadmap database with all items
- Overview page with complete table of contents
- Kanban board view
- Analytics hub with specialized reporting tools

### 2. Manual Text to CSV Workflow

If you have an existing roadmap text file:

```bash
python -m arcane parse roadmap.txt output.csv
```

**Input Format:**
Your text file should follow this hierarchy:
```
# Project Name

## Milestone 1: Foundation Setup
### Epic 1.0: Core Infrastructure
#### Story 1.0.1: Database Setup
##### Task 1.0.1.1: Configure PostgreSQL
##### Task 1.0.1.2: Set up migrations
```

**Output:**
- CSV file with all hierarchy levels
- Parent-child relationships preserved
- All metadata fields included

### 3. Import Existing CSV

If you already have a CSV file:

```bash
python -m arcane import your_roadmap.csv
```

**CSV Requirements:**
- Must include columns: Name, Type, Parent, Duration, Priority, Status
- Optional columns: Goal/Description, Benefits, Prerequisites, Technical Requirements, Claude Code Prompt
- Types should be: Project, Milestone, Epic, Story, Task

## Roadmap Preferences

When generating roadmaps, you can customize:

### Timeline Options
- **3 months**: MVP-focused, essential features only
- **6 months**: Balanced approach with core features and polish
- **12 months**: Comprehensive roadmap with advanced features
- **Custom**: Specify your own timeline

### Technical Complexity
- **Simple**: Basic CRUD operations, minimal integrations
- **Moderate**: APIs, some third-party integrations
- **Complex**: Microservices, advanced architecture patterns

### Team Size
- **Solo developer**: Tasks sized for individual work
- **Small team (2-3)**: Parallel workstreams possible
- **Medium team (4-8)**: Multiple concurrent epics
- **Large team (8+)**: Complex coordination and dependencies

### Primary Focus
- **MVP/Startup launch**: Speed to market emphasis
- **Feature development**: Adding to existing product
- **System migration**: Legacy system replacement
- **Performance optimization**: Scalability and efficiency

## Project Idea Files

To get better AI-generated roadmaps, provide a detailed project description:

```txt
Project: ServicePro Field Service Management

Overview:
A comprehensive SaaS platform for field service businesses to manage
work orders, technicians, customers, and billing.

Key Features:
- Work order management and scheduling
- Technician mobile app with GPS tracking
- Customer portal for service requests
- Automated billing and invoicing
- Real-time analytics and reporting

Target Users:
- HVAC companies
- Plumbing services
- Electrical contractors
- General maintenance businesses

Technical Requirements:
- Web application with mobile-responsive design
- Native mobile apps for technicians
- Integration with popular accounting software
- Real-time notifications and updates
```

## Generated Notion Workspace

### Database Structure
- **Hierarchical organization**: Project → Milestones → Epics → Stories → Tasks
- **Rich metadata**: Status, priority, duration, descriptions
- **Relationships**: Parent-child links between items
- **Icons**: Visual indicators for each item type

### Management Pages
- **Overview**: Complete table of contents and project statistics
- **Kanban Board**: Visual workflow management
- **Analytics Hub**: Centralized reporting dashboard

### Analytics Tools
- **Dashboard**: High-level project metrics and progress
- **Burndown Analytics**: Progress tracking over time
- **Sprint Tracking**: Iteration-based planning tools
- **Velocity Analytics**: Team performance metrics
- **Timeline Progress**: Milestone and deadline tracking

## Tips for Best Results

### 1. Detailed Project Descriptions
- Include specific features and requirements
- Mention target users and use cases
- Specify technical constraints or preferences
- Describe integration requirements

### 2. Appropriate Complexity Selection
- Be realistic about your team's capabilities
- Consider existing infrastructure and tools
- Factor in learning curve for new technologies

### 3. Timeline Considerations
- Include buffer time for testing and iteration
- Account for dependencies and blockers
- Consider team availability and other commitments

### 4. Review and Customize
- Generated roadmaps are starting points
- Review and adjust based on your specific needs
- Add or remove items as appropriate
- Update estimates based on your experience

## Next Steps

After importing your roadmap:
1. Review all generated items in the Notion database
2. Adjust priorities and timelines based on your needs
3. Assign team members to specific items
4. Set up regular review cycles using the analytics tools
5. Track progress and update status as work progresses