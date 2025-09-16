# Roadmap Generator CLI - Usage Guide

The Roadmap Generator CLI provides a complete automated workflow from idea to Notion workspace. It supports multiple LLM providers and provides beautiful terminal interfaces with progress tracking.

## 🚀 Quick Start

### Interactive Roadmap Generation (Recommended)
```bash
# Complete workflow: Idea → LLM → Roadmap → CSV → Notion
python -m roadmap_notion generate
```

This command will:
1. **Prompt for LLM selection** (Claude, OpenAI, Gemini)
2. **Check environment variables** automatically
3. **Ask for your idea file** (optional - can generate without)
4. **Collect roadmap preferences** (timeline, complexity, team size)
5. **Generate comprehensive roadmap** using AI
6. **Convert to CSV format** automatically
7. **Import to Notion** with full workspace structure

### Other Commands

#### Import Existing CSV
```bash
# Import a CSV file directly to Notion
python -m roadmap_notion import your_roadmap.csv
```

#### Parse Text to CSV
```bash
# Convert roadmap text file to CSV
python -m roadmap_notion parse roadmap.txt
python -m roadmap_notion parse roadmap.txt --output custom_name.csv
```

## 📋 Prerequisites

### Environment Variables
Set up your environment variables in a `.env` file:

```bash
# Choose your LLM provider (one or more)
ANTHROPIC_API_KEY=your_claude_api_key      # For Claude
OPENAI_API_KEY=your_openai_api_key         # For ChatGPT
GOOGLE_API_KEY=your_google_api_key         # For Gemini

# Notion integration (required)
NOTION_TOKEN=your_notion_integration_token
NOTION_PARENT_PAGE_ID=your_notion_parent_page_id
```

### Dependencies
Install all required packages:
```bash
pip install rich inquirer anthropic openai google-generativeai python-dotenv notion-client
```

## 🎯 Interactive Generation Flow

### Step 1: LLM Selection
The CLI will present an interactive menu:
```
🗺️  Roadmap Generator
Automated roadmap generation and Notion import

Select your preferred LLM provider:
❯ Claude (Anthropic)
  ChatGPT (OpenAI)
  Gemini (Google)
```

### Step 2: Environment Validation
Automatic validation of required environment variables:
```
✅ All environment variables configured
```

### Step 3: Idea File (Optional)
```
Idea Description File
Provide a text file describing your project idea

📁 Enter path to your idea text file: /path/to/my_idea.txt
✅ Found file: /path/to/my_idea.txt
```

### Step 4: Roadmap Preferences
Interactive selection of project parameters:
```
Project timeline:
❯ 3 months (MVP focus)
  6 months (Balanced)
  12 months (Comprehensive)
  Custom timeline

Technical complexity:
❯ Simple (Basic CRUD, minimal integrations)
  Moderate (APIs, some integrations)
  Complex (Microservices, advanced features)

Development team size:
❯ Solo developer
  Small team (2-3)
  Medium team (4-8)
  Large team (8+)

Primary focus:
❯ MVP / Startup launch
  Feature development
  System migration
  Performance optimization
```

### Step 5: AI Generation
Beautiful progress indicators during generation:
```
🤖 Generating roadmap with AI...
📊 Converting roadmap to CSV...
📤 Importing to Notion...
```

### Step 6: Completion Summary
```
🎉 Generation Complete!
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Step                ┃ Status    ┃ Output                        ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1. Roadmap          │ ✅ Success │ generated_roadmap.txt         │
│    Generation       │           │                               │
│ 2. CSV Conversion   │ ✅ Success │ generated_roadmap.csv         │
│ 3. Notion Import    │ ✅ Success │ Check Notion workspace        │
└─────────────────────┴───────────┴───────────────────────────────┘
```

## 📝 Idea File Format

### Option 1: Use the Template
Refer to `IDEA_TEMPLATE.md` for a comprehensive guide on structuring your idea description.

### Option 2: Simple Description
For basic usage, create a text file with:
```
Project Name: My Awesome SaaS

Problem: Small businesses struggle with managing customer relationships and project workflows.

Solution: An integrated CRM and project management platform that combines:
- Customer relationship management
- Project tracking and time management
- Invoicing and billing
- Team collaboration tools

Target Users: Small to medium businesses (5-50 employees) in service industries

Key Features:
- Customer database and contact management
- Project creation and task tracking
- Time tracking and invoicing
- Team chat and file sharing
- Mobile app for field workers

Technical Requirements:
- Web application with mobile responsive design
- REST API for mobile app integration
- Real-time notifications
- Cloud hosting with automatic backups
- Integration with payment processors
```

## 🎨 Generated Roadmap Structure

The AI generates roadmaps with this hierarchical structure:

```
# PROJECT_NAME

## Milestone 1: Foundation & Setup
### Epic 1.0: Project Infrastructure
#### Story 1.0.1: Repository Setup
##### Task 1.0.1.1: Initialize Git Repository
##### Task 1.0.1.2: Set Up CI/CD Pipeline
##### Task 1.0.1.3: Configure Development Environment

#### Story 1.0.2: Database Design
##### Task 1.0.2.1: Design Entity Relationship Diagram
##### Task 1.0.2.2: Set Up Database Schema
##### Task 1.0.2.3: Create Migration Scripts

### Epic 1.1: Authentication System
#### Story 1.1.1: User Registration
#### Story 1.1.2: Login System
#### Story 1.1.3: Password Reset

## Milestone 2: Core Features
### Epic 2.0: Customer Management
### Epic 2.1: Project Tracking
```

Each item includes:
- **Goal/Description**: Clear description of what needs to be accomplished
- **Benefits**: Business and technical benefits
- **Prerequisites**: What needs to be done first
- **Technical Requirements**: Technical specifications and constraints
- **Claude Code Prompt**: Specific implementation guidance for Claude Code

## 🔧 Advanced Usage

### Custom Environment Variables
```bash
# Use custom .env file location
export DOTENV_PATH=/path/to/custom/.env
python -m roadmap_notion generate
```

### Batch Processing
```bash
# Process multiple idea files
for idea_file in ideas/*.txt; do
    python -m roadmap_notion generate
done
```

### Integration with CI/CD
```bash
# Generate roadmap in automated workflow
python -m roadmap_notion generate --non-interactive --config config.json
```

## 🎯 What Gets Created in Notion

The generated workspace includes:

### 🗂️ Container Structure
- **Main Project Page**: `[Project Name] - Roadmap`
  - **Database**: Complete roadmap with all items and relationships
  - **Overview Page**: Hierarchical table of contents
  - **Kanban Board**: Board view of the database
  - **Analytics Hub**: Container for all analytics

### 📊 Analytics Pages
- **Dashboard**: Project overview and key metrics
- **Burndown Analytics**: Progress tracking and completion rates
- **Sprint Tracking**: Sprint planning and milestone management
- **Velocity Analytics**: Team performance and velocity metrics
- **Timeline Progress**: Schedule adherence and milestone tracking

### 🔗 Features
- **Parent-child relationships** between milestones, epics, stories, and tasks
- **Rich text formatting** with proper styling
- **Database properties** for status, priority, duration, and technical details
- **Clean navigation** between all pages and views

## 🛠️ Troubleshooting

### Common Issues

#### Missing Environment Variables
```
❌ Missing required environment variables:
  • ANTHROPIC_API_KEY
  • NOTION_TOKEN
```
**Solution**: Set up your `.env` file with required API keys.

#### LLM API Errors
```
❌ Error generating roadmap: Claude API error: Invalid API key
```
**Solution**: Verify your API key is correct and has sufficient credits.

#### File Not Found
```
❌ File not found: /path/to/idea.txt
```
**Solution**: Check file path and permissions.

#### Notion Import Errors
```
❌ Error importing to Notion: Invalid parent page ID
```
**Solution**: Verify your `NOTION_PARENT_PAGE_ID` is correct and the integration has access.

### Debug Mode
```bash
# Enable debug logging
export DEBUG=1
python -m roadmap_notion generate
```

## 📚 Examples

### Startup MVP Roadmap
```bash
# Quick MVP roadmap for a startup
echo "SaaS startup for small business invoicing and payment processing" > startup_idea.txt
python -m roadmap_notion generate
# Select: 3 months, Simple complexity, Solo developer, MVP focus
```

### Enterprise Migration Project
```bash
# Complex migration project
echo "Migrate legacy monolith to microservices architecture" > migration_idea.txt
python -m roadmap_notion generate
# Select: 12 months, Complex, Large team, System migration
```

### Feature Development
```bash
# Add new feature to existing product
echo "Add real-time chat feature to existing CRM platform" > feature_idea.txt
python -m roadmap_notion generate
# Select: 6 months, Moderate, Medium team, Feature development
```

## 🎉 Best Practices

1. **Be Specific**: The more detailed your idea description, the better the generated roadmap
2. **Use Templates**: Leverage `IDEA_TEMPLATE.md` for comprehensive descriptions
3. **Iterate**: Generate multiple versions with different parameters to compare approaches
4. **Customize**: Edit the generated roadmap text before conversion if needed
5. **Validate**: Review the generated items in Notion and adjust as necessary

## 🔄 Workflow Integration

The CLI is designed to integrate seamlessly into development workflows:

1. **Planning Phase**: Use `generate` command for initial roadmap creation
2. **Development Phase**: Use Claude Code prompts from the generated items
3. **Progress Tracking**: Update status in Notion database as work progresses
4. **Analytics**: Monitor progress using the generated analytics pages
5. **Iteration**: Re-generate sections as requirements evolve

This creates a complete end-to-end workflow from idea conception to implementation tracking.