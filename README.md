# 🗺️ Roadmap Generator & Notion Importer

A comprehensive CLI tool that automates the entire roadmap generation workflow - from idea to implementation-ready Notion workspace. Generate professional roadmaps using AI (Claude, ChatGPT, Gemini) and automatically import them into Notion with complete project management features.

## ✨ Features

### 🚀 **Complete Automation**
- **One-command workflow**: Idea → AI Generation → CSV → Notion workspace
- **Multi-LLM support**: Claude, OpenAI ChatGPT, and Google Gemini
- **Beautiful terminal UI** with progress tracking and interactive menus
- **Automatic environment validation** and error handling

### 🎯 **Intelligent Roadmap Generation**
- **Structured AI prompts** for consistent, high-quality roadmaps
- **Hierarchical organization**: Project → Milestones → Epics → Stories → Tasks
- **Claude Code integration**: Every item includes specific implementation prompts
- **Customizable parameters**: Timeline, complexity, team size, and focus area

### 📊 **Complete Notion Workspace**
- **Container structure** with organized project hierarchy
- **Rich database** with parent-child relationships and properties
- **Overview page** with hierarchical table of contents
- **Kanban board** for visual project management
- **Analytics hub** with specialized tracking pages:
  - Dashboard with key metrics
  - Burndown analytics for progress tracking
  - Sprint tracking for agile workflows
  - Velocity analytics for team performance
  - Timeline progress for milestone tracking

## 🚀 Quick Start

### 1. Installation
```bash
git clone <your-repo-url>
cd roadmap-notion
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file with your API keys:
```bash
# Choose your LLM provider (one or more)
ANTHROPIC_API_KEY=your_claude_api_key      # For Claude
OPENAI_API_KEY=your_openai_api_key         # For ChatGPT
GOOGLE_API_KEY=your_google_api_key         # For Gemini

# Notion integration (required)
NOTION_TOKEN=your_notion_integration_token
NOTION_PARENT_PAGE_ID=your_notion_parent_page_id
```

### 3. Generate Your First Roadmap
```bash
# Interactive full workflow - handles everything!
python -m roadmap_notion generate
```

This single command will:
1. **Prompt for LLM selection** (Claude, OpenAI, Gemini)
2. **Validate environment** automatically
3. **Ask for your idea file** (optional - can generate without)
4. **Collect preferences** (timeline, complexity, team size, focus)
5. **Generate comprehensive roadmap** using AI
6. **Convert to CSV** automatically
7. **Import to Notion** with complete workspace

## 📖 Usage

### Interactive Roadmap Generation (Recommended)
```bash
# Complete automated workflow
python -m roadmap_notion generate
```

**Example interaction:**
```
🗺️  Roadmap Generator
Automated roadmap generation and Notion import

Select your preferred LLM provider:
❯ Claude (Anthropic)
  ChatGPT (OpenAI)
  Gemini (Google)

✅ All environment variables configured

📁 Enter path to your idea text file: my_idea.txt
✅ Found file: my_idea.txt

Project timeline:
❯ 6 months (Balanced)

🤖 Generating roadmap with AI...
📊 Converting roadmap to CSV...
📤 Importing to Notion...

🎉 Generation Complete!
```

### Other Commands
```bash
# Import existing CSV to Notion
python -m roadmap_notion import roadmap.csv

# Convert roadmap text to CSV only
python -m roadmap_notion parse roadmap.txt
python -m roadmap_notion parse roadmap.txt --output custom_name.csv

# Show help
python -m roadmap_notion --help
```

## 📝 Creating Your Idea File

### Quick Start
Create a simple text file describing your project:
```
Project: Customer CRM Platform

Problem: Small businesses struggle with managing customer relationships and tracking sales.

Solution: Web-based CRM that combines contact management, deal tracking, and email automation.

Key Features:
- Customer database with contact history
- Sales pipeline with deal tracking
- Email marketing automation
- Reporting and analytics dashboard
- Mobile app for field sales teams

Target Users: Small to medium businesses (10-100 employees)
```

### Comprehensive Description
For detailed roadmaps, use our structured template:
```bash
# See the complete guide
cat docs/IDEA_TEMPLATE.md
```

The template covers:
- Core concept and problem statement
- Technical requirements and architecture
- User experience and workflows
- Success criteria and constraints
- Implementation preferences

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

### Epic 1.1: Authentication System
#### Story 1.1.1: User Registration
#### Story 1.1.2: Login System

## Milestone 2: Core Features
### Epic 2.0: Customer Management
### Epic 2.1: Project Tracking
```

Each item includes:
- **Goal/Description**: Clear objectives
- **Benefits**: Business and technical value
- **Prerequisites**: Dependencies
- **Technical Requirements**: Implementation specs
- **Claude Code Prompt**: Specific guidance for Claude Code

## 🛠️ Advanced Usage

### Environment Variables
```bash
# Custom .env file location
export DOTENV_PATH=/path/to/custom/.env

# Debug mode
export DEBUG=1
```

### API Key Setup

#### Claude (Anthropic)
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create API key
3. Add to `.env`: `ANTHROPIC_API_KEY=your_key`

#### OpenAI (ChatGPT)
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create API key
3. Add to `.env`: `OPENAI_API_KEY=your_key`

#### Google Gemini
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create API key
3. Add to `.env`: `GOOGLE_API_KEY=your_key`

#### Notion Integration
1. Visit [Notion Integrations](https://www.notion.so/my-integrations)
2. Create new integration
3. Get integration token: `NOTION_TOKEN=secret_...`
4. Share parent page with integration
5. Get page ID from URL: `NOTION_PARENT_PAGE_ID=abc123...`

## 📊 What Gets Created in Notion

### 🗂️ Project Structure
- **Main Container**: `[Project Name] - Roadmap`
  - **Database**: All roadmap items with relationships
  - **Overview**: Hierarchical table of contents
  - **Kanban Board**: Visual project management
  - **Analytics Hub**: Metrics and tracking

### 📈 Analytics Pages
- **Dashboard**: Project overview and key metrics
- **Burndown Analytics**: Progress and completion tracking
- **Sprint Tracking**: Agile workflow management
- **Velocity Analytics**: Team performance metrics
- **Timeline Progress**: Schedule and milestone tracking

### 🔗 Database Features
- **Parent-child relationships** between all items
- **Rich properties**: Status, Priority, Duration, Technical Requirements
- **Claude Code prompts** for implementation guidance
- **Clean formatting** with proper styling

## 💡 Examples

### Startup MVP (3 months)
```bash
echo "SaaS platform for small business invoicing and payments" > startup_idea.txt
python -m roadmap_notion generate
# Select: 3 months, Simple, Solo developer, MVP focus
```

### Enterprise Feature (6 months)
```bash
echo "Add real-time collaboration to existing CRM platform" > feature_idea.txt
python -m roadmap_notion generate
# Select: 6 months, Moderate, Medium team, Feature development
```

### System Migration (12 months)
```bash
echo "Migrate legacy monolith to microservices architecture" > migration_idea.txt
python -m roadmap_notion generate
# Select: 12 months, Complex, Large team, System migration
```

## 🔧 Development

### Setup for Development
```bash
git clone <repo-url>
cd roadmap-notion
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Optional: Install development tools
pip install pytest black flake8
```

### Project Structure
```
roadmap_notion/
├── __main__.py           # CLI entry point
├── cli.py                # Interactive CLI with rich UI
├── generator.py          # AI roadmap generation
├── llm_client.py         # Multi-LLM support
├── parser.py             # Text-to-CSV conversion
├── importer.py           # Notion import (modular)
└── pages/                # Modular page creators
    ├── base.py           # Abstract base class
    ├── database.py       # Database creator
    ├── overview.py       # Overview page
    ├── analytics_hub.py  # Analytics container
    └── [other pages...]  # Individual analytics pages
```

### Testing
```bash
# Test individual commands
python -m roadmap_notion parse roadmap.txt
python -m roadmap_notion import test.csv

# Test full workflow (requires API keys)
python -m roadmap_notion generate
```

## 📚 Documentation

### Complete Documentation Suite

Comprehensive guides and references available in the [`docs/`](docs/) directory:

#### Getting Started
- **[Installation Guide](docs/installation.md)**: Step-by-step setup instructions with troubleshooting
- **[Usage Guide](docs/usage.md)**: Complete usage documentation with workflows and examples
- **[CLI Usage Reference](docs/CLI_USAGE.md)**: Detailed command-line interface documentation

#### Project Planning
- **[Idea Template](docs/IDEA_TEMPLATE.md)**: Comprehensive guide for describing project ideas
- **[Examples & Use Cases](docs/examples.md)**: Real-world examples across different industries and team sizes
- **[Claude Code Integration](docs/CLAUDE_GUIDE.md)**: Guide for using generated roadmaps with Claude Code

#### Technical Reference
- **[API Reference](docs/api-reference.md)**: Technical documentation for all modules and classes
- **[Application Summary](docs/ROADMAP_APP_SUMMARY.md)**: Technical overview and architecture
- **[Troubleshooting Guide](docs/troubleshooting.md)**: Common issues and solutions with error code reference

### Quick Reference

- **Getting Started**: See [Installation Guide](docs/installation.md) for complete setup
- **Project Ideas**: Use [Idea Template](docs/IDEA_TEMPLATE.md) for detailed project descriptions
- **Usage Examples**: Check [Examples](docs/examples.md) for your project type
- **Claude Code**: See [Claude Code Integration](docs/CLAUDE_GUIDE.md) for implementation guidance
- **CLI Commands**: Refer to [CLI Usage](docs/CLI_USAGE.md) for all command options
- **Technical Details**: See [API Reference](docs/api-reference.md) for implementation details
- **Architecture**: Review [Application Summary](docs/ROADMAP_APP_SUMMARY.md) for technical overview
- **Need Help?**: Consult [Troubleshooting Guide](docs/troubleshooting.md) for common issues

## 🐛 Troubleshooting

### Common Issues

#### Missing API Keys
```
❌ Missing required environment variables:
  • ANTHROPIC_API_KEY
```
**Solution**: Add API keys to `.env` file

#### File Not Found
```
❌ File not found: /path/to/idea.txt
```
**Solution**: Check file path or skip idea file

#### Notion Import Errors
```
❌ Error importing to Notion: Invalid parent page ID
```
**Solution**: Verify `NOTION_PARENT_PAGE_ID` and integration permissions

### Debug Mode
```bash
export DEBUG=1
python -m roadmap_notion generate
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with clear description

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for seamless integration with Claude Code
- Supports multiple LLM providers for flexibility
- Designed for professional project management workflows

---

**Ready to generate your first roadmap?**
```bash
python -m roadmap_notion generate
```