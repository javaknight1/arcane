# 🔮 Arcane - AI-Powered Roadmap Generation CLI

A comprehensive command-line tool that transforms ideas into actionable roadmaps using AI and integrates them with project management tools. Generate professional roadmaps using leading AI models (Claude, ChatGPT, Gemini) and automatically import them into Notion with complete project management features.

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
cd arcane
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
python -m arcane interactive
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

### Quick Start Methods

#### 1. 🚀 Use Predefined Profiles (Fastest)
Skip all questions with predefined configurations for common use cases:
```bash
# Solo founder building MVP (3 months, bootstrap budget)
python -m arcane interactive --profile mvp-startup --idea-file my_idea.txt

# AI/ML startup (6 months, modern tech stack)
python -m arcane interactive --profile ai-startup

# Enterprise migration (12 months, large team)
python -m arcane interactive --profile enterprise-migration

# Mobile app (B2C, viral scaling)
python -m arcane interactive --profile mobile-app

# Healthcare platform (HIPAA compliance)
python -m arcane interactive --profile healthcare-app
```

#### 2. 🎯 Custom Flag Configuration
Skip specific questions by providing flags:
```bash
# Skip basic preferences
python -m arcane interactive --timeline 6-months --complexity moderate --team-size 2-3

# Skip industry and regulatory context
python -m arcane interactive --industry healthcare --regulatory hipaa gdpr

# Skip deployment preferences
python -m arcane interactive --deployment-environment cloud --scaling-expectations viral
```

#### 3. 💬 Full Interactive Mode
Let the CLI guide you through all questions:
```bash
python -m arcane interactive
```

### Available Profiles

| Profile | Best For | Timeline | Team | Budget | Key Features |
|---------|----------|----------|------|--------|--------------|
| `mvp-startup` | Solo founders | 3 months | 1 dev | Bootstrap | Simple stack, minimal infrastructure |
| `ai-startup` | ML/AI products | 6 months | 2-3 devs | Seed funded | ML challenges, real-time data |
| `enterprise-migration` | Legacy systems | 12 months | 8+ devs | Enterprise | Complex migration, compliance |
| `mobile-app` | Consumer apps | 6 months | 2-3 devs | Seed funded | Offline-first, viral scaling |
| `ecommerce` | Online stores | 6 months | 4-8 devs | Funded | Payments, seasonal scaling |
| `healthcare-app` | Medical platforms | 12 months | 4-8 devs | Funded | HIPAA compliance, security |
| `fintech` | Financial services | 12 months | 4-8 devs | Funded | Financial compliance, real-time |
| `microservices` | Large platforms | 12 months | 8+ devs | Enterprise | Kubernetes, global scale |
| `blockchain` | Web3/DeFi | 6 months | 2-3 devs | Seed funded | Blockchain, crypto payments |
| `education-platform` | Learning systems | 6 months | 2-3 devs | Seed funded | FERPA compliance, video calls |

## 🚩 CLI Flag Reference

This comprehensive guide covers all available command-line flags organized by category.

### Core System Flags

| Flag | Purpose | Options | Default | Example |
|------|---------|---------|---------|---------|
| `--provider` | Select LLM provider | `claude`, `openai`, `gemini` | `claude` | `--provider openai` |
| `--idea-file` | Project description file | Any text file path | - | `--idea-file ./project.txt` |
| `--output-dir` | Output directory | Any directory path | `./output` | `--output-dir ./generated` |
| `--no-export` | Skip file export | Flag (no value) | - | `--no-export` |
| `--formats` | Export formats | `csv`, `json`, `yaml` | `csv` | `--formats csv json` |

### Profile Selection

| Flag | Purpose | Options | Example |
|------|---------|---------|---------|
| `--profile` | Predefined configuration (skips ALL questions) | `mvp-startup`, `enterprise-migration`, `ai-startup`, `mobile-app`, `ecommerce`, `healthcare-app`, `fintech`, `microservices`, `blockchain`, `education-platform` | `--profile ai-startup` |

### Basic Roadmap Configuration

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--timeline` | Project duration | `3-months`, `6-months`, `12-months` | `--timeline 6-months` | Milestone pacing and task sizing |
| `--complexity` | Technical complexity | `simple`, `moderate`, `complex` | `--complexity moderate` | Architecture decisions and challenge level |
| `--team-size` | Development team size | `1`, `2-3`, `4-8`, `8+` | `--team-size 2-3` | Task sizing and collaboration approach |
| `--focus` | Primary objective | `mvp`, `feature`, `migration`, `optimization` | `--focus mvp` | Feature prioritization and iteration speed |

### Industry and Regulatory Context

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--industry` | Industry domain | `b2b-saas`, `b2c-mobile`, `ecommerce`, `healthcare`, `finance`, `education`, `gaming`, `enterprise`, `government`, `non-profit`, `other` | `--industry healthcare` | Domain-specific requirements and standards |
| `--regulatory` | Compliance needs | `gdpr`, `hipaa`, `pci-dss`, `soc2`, `iso27001`, `ferpa`, `fedramp`, `none` | `--regulatory hipaa gdpr` | Compliance milestones and audit tasks |
| `--market-maturity` | Competition level | `greenfield`, `emerging`, `established`, `saturated` | `--market-maturity saturated` | Differentiation and competitive strategies |
| `--target-market` | Geographic scope | `local`, `regional`, `national`, `global` | `--target-market global` | Internationalization and scaling needs |

### Technical Assessment

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--technical-challenges` | Technical hurdles | `realtime-data`, `high-concurrency`, `complex-logic`, `integrations`, `ml-ai`, `blockchain`, `iot-hardware`, `multi-tenant`, `offline-first`, `data-migrations`, `microservices`, `graphql-apis` | `--technical-challenges realtime-data ml-ai` | Specialized implementation tasks |

### Team Assessment

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--team-expertise` | Technical skill level | `learning`, `intermediate`, `expert`, `mixed` | `--team-expertise intermediate` | Task complexity and learning milestones |
| `--team-distribution` | Working arrangement | `colocated`, `remote-sync`, `remote-async`, `hybrid` | `--team-distribution remote-async` | Communication and coordination tasks |
| `--dev-methodology` | Development process | `agile`, `kanban`, `waterfall`, `adhoc` | `--dev-methodology agile` | Sprint structure and workflow tasks |

### Budget Assessment

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--budget-range` | Overall budget | `bootstrap`, `seed`, `funded`, `enterprise`, `undefined` | `--budget-range seed` | Tool choices and infrastructure decisions |
| `--infra-budget` | Monthly infrastructure | `minimal`, `moderate`, `substantial`, `unlimited` | `--infra-budget minimal` | Hosting strategy and cost optimization |
| `--services-budget` | Third-party services | `free`, `basic`, `professional`, `enterprise` | `--services-budget professional` | Integration choices and feature availability |

### Deployment Assessment

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--deployment-environment` | Hosting strategy | `cloud`, `serverless`, `kubernetes`, `traditional`, `on-premise`, `hybrid`, `edge` | `--deployment-environment kubernetes` | Infrastructure architecture and DevOps tasks |
| `--geographic-distribution` | Global infrastructure | `single-region`, `multi-region`, `global`, `data-residency` | `--geographic-distribution multi-region` | CDN, replication, and compliance tasks |
| `--scaling-expectations` | Traffic patterns | `steady`, `daily-peaks`, `seasonal`, `viral`, `batch` | `--scaling-expectations viral` | Auto-scaling and capacity planning |

### Integration Requirements

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--payment-integrations` | Payment processing | `stripe`, `paypal`, `square`, `cryptocurrency`, `bank-transfers`, `none` | `--payment-integrations stripe paypal` | Payment gateway and PCI compliance tasks |
| `--communication-integrations` | Communication channels | `email`, `sms`, `push-notifications`, `in-app-chat`, `video-calls`, `none` | `--communication-integrations email sms` | Notification and messaging system tasks |
| `--business-integrations` | Business tools | `crm`, `accounting`, `analytics`, `support`, `marketing-automation`, `none` | `--business-integrations crm analytics` | Third-party API integration tasks |
| `--developer-integrations` | Development tools | `github-gitlab`, `ci-cd`, `monitoring`, `error-tracking`, `feature-flags`, `none` | `--developer-integrations github-gitlab ci-cd` | DevOps and development workflow tasks |
| `--data-integrations` | Data sources | `rest-apis`, `graphql-apis`, `webhooks`, `websockets`, `file-uploads`, `databases`, `none` | `--data-integrations rest-apis databases` | Data pipeline and API integration tasks |

### Success Definition

| Flag | Purpose | Options | Example | Impact |
|------|---------|---------|---------|---------|
| `--success-metric` | Primary measurement | `adoption`, `revenue`, `cost-saving`, `speed`, `performance`, `satisfaction`, `innovation` | `--success-metric revenue` | Analytics and tracking implementation |
| `--success-timeline` | Measurement timeframe | `immediate`, `short`, `medium`, `long` | `--success-timeline short` | Feedback loops and iteration cycles |
| `--measurement-approach` | Tracking methodology | `quantitative`, `qualitative`, `mixed`, `none` | `--measurement-approach mixed` | Analytics plus user research tasks |
| `--failure-tolerance` | Acceptable failure rate | `zero`, `low`, `moderate`, `high` | `--failure-tolerance zero` | Testing requirements and error handling |

### Other Commands
```bash
# Generate roadmap from idea only (save as JSON)
python -m arcane generate --idea "Build a task management app"

# Export existing roadmap
python -m arcane export --roadmap roadmap.json

# Import roadmap to Notion
python -m arcane import --roadmap roadmap.json

# Show help
python -m arcane --help
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

### Configuration
Arcane supports extensive customization through YAML configuration files. You can customize LLM settings, generation parameters, file handling, display options, and more.

📖 **[Complete Configuration Guide](docs/configuration.md)** - Detailed explanation of all configuration options, examples, and best practices.

Quick setup:
```bash
# Create user configuration directory
mkdir -p ~/.arcane

# Create basic configuration
cat > ~/.arcane/config.yaml << EOF
llm:
  default_provider: "claude"
generation:
  interactive_mode: true
  default_timeline: "6-months"
files:
  default_output_dir: "./my-roadmaps"
EOF
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
cd arcane
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
- **[Installation Guide](docs/installation.md)**: Step-by-step setup instructions with API key configuration
- **[Usage Guide](docs/usage.md)**: Complete usage documentation with workflows and examples
- **[Configuration Guide](docs/configuration.md)**: Comprehensive configuration options and customization

#### Project Planning
- **[Idea Template](docs/IDEA_TEMPLATE.md)**: Comprehensive guide for describing project ideas
- **[Examples & Use Cases](docs/examples.md)**: Real-world examples across different industries and team sizes
- **[Claude Code Integration](docs/CLAUDE_GUIDE.md)**: Guide for using generated roadmaps with Claude Code

#### Reference & Support
- **[Troubleshooting Guide](docs/troubleshooting.md)**: Common issues and solutions with error code reference

### Quick Reference

- **Getting Started**: See [Installation Guide](docs/installation.md) for complete setup
- **Project Ideas**: Use [Idea Template](docs/IDEA_TEMPLATE.md) for detailed project descriptions
- **Usage Examples**: Check [Examples](docs/examples.md) for your project type
- **Configuration**: See [Configuration Guide](docs/configuration.md) for customization options
- **Claude Code**: See [Claude Code Integration](docs/CLAUDE_GUIDE.md) for implementation guidance
- **CLI Commands**: Refer to the [CLI Flag Reference](#-cli-flag-reference) section above for all command options
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