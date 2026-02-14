# Arcane

AI-powered roadmap generator that transforms project ideas into detailed, hierarchical roadmaps with implementation guidance.

## What It Does

Arcane uses AI to generate complete project roadmaps from a simple discovery conversation:

1. **Discovery**: Answer questions about your project vision, timeline, team, and requirements
2. **Generation**: AI generates a hierarchical roadmap (Milestones → Epics → Stories → Tasks)
3. **Export**: Export to CSV for import into any project management tool

Every task includes a Claude Code prompt for direct implementation assistance.

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/arcane.git
cd arcane
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### Configuration

Create a `.env` file:

```bash
ARCANE_ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Generate Your First Roadmap

```bash
arcane new
```

This starts an interactive session that:
1. Asks about your project (name, vision, problem, users)
2. Gathers constraints (timeline, team size, budget)
3. Collects technical preferences (stack, infrastructure)
4. Defines requirements (must-have, nice-to-have, out of scope)
5. Generates a complete roadmap with AI

### Preparing Your Answers

For the best results, plan your answers before running `arcane new`. We provide an idea file guide that walks you through every prompt with tips and examples:

- **[`examples/idea-file-guide.txt`](examples/idea-file-guide.txt)** — Template and guide for creating your own project idea file

Copy the guide, fill it in for your project, and reference it while answering arcane's prompts. The "Additional Notes" prompt at the end accepts free-form text — paste your architecture decisions, data model, and constraints there for the highest quality roadmap output.

## CLI Commands

### `arcane new`

Create a new roadmap from scratch.

```bash
# Interactive mode (default)
arcane new

# Skip first question with project name
arcane new --name "My Project"

# Non-interactive (skip review prompts)
arcane new --no-interactive

# Custom output directory
arcane new --output ./roadmaps
```

### `arcane view`

View a generated roadmap.

```bash
# Tree view (default)
arcane view ./my-project/roadmap.json

# Summary view
arcane view ./my-project --format summary

# Raw JSON
arcane view ./my-project --format json
```

### `arcane export`

Export roadmap to project management tools.

```bash
# Export to CSV (universal import format)
arcane export ./my-project/roadmap.json --to csv
```

### `arcane resume`

Resume an incomplete roadmap generation.

```bash
arcane resume ./my-project/roadmap.json
```

### `arcane config`

View current configuration.

```bash
arcane config --show
```

## How It Works

### Hierarchical Generation

Arcane generates roadmaps level-by-level to maintain quality:

```
Roadmap
├── Milestone (major phase)
│   ├── Epic (feature area)
│   │   ├── Story (user capability)
│   │   │   ├── Task (1-8 hour work item)
│   │   │   └── Task
│   │   └── Story
│   └── Epic
└── Milestone
```

Each level is generated with full context from parent items, ensuring consistency.

### Structured Output

All AI responses use Pydantic schemas to guarantee format consistency:

- Milestones have goals and target dates
- Epics have goals and prerequisites
- Stories have acceptance criteria
- Tasks have estimated hours, implementation notes, and Claude Code prompts

### Incremental Saving

Roadmaps are saved after each story is generated, so interrupted generations can be resumed.

## Configuration

All configuration uses environment variables with the `ARCANE_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `ARCANE_ANTHROPIC_API_KEY` | Anthropic API key (required) | - |
| `ARCANE_MODEL` | Claude model to use | `claude-sonnet-4-20250514` |
| `ARCANE_MAX_RETRIES` | API call retry count | `3` |
| `ARCANE_INTERACTIVE` | Pause for review between phases | `true` |
| `ARCANE_OUTPUT_DIR` | Default output directory | `./` |

### PM Tool Integration (Future)

| Variable | Description |
|----------|-------------|
| `ARCANE_LINEAR_API_KEY` | Linear API key |
| `ARCANE_JIRA_DOMAIN` | Jira Cloud domain |
| `ARCANE_JIRA_EMAIL` | Jira account email |
| `ARCANE_JIRA_API_TOKEN` | Jira API token |
| `ARCANE_NOTION_API_KEY` | Notion integration token |

## Output Structure

Generated roadmaps are saved to a project directory:

```
my-project/
├── roadmap.json      # Complete roadmap with all items
├── context.yaml      # Project context from discovery
├── roadmap.csv       # CSV export (if exported)
└── project-docs.md   # Project documentation (generated with CSV export)
```

### CSV Format

The CSV export includes all hierarchy levels with parent-child relationships:

| Column | Description |
|--------|-------------|
| Type | Milestone, Epic, Story, or Task |
| ID | Unique identifier |
| Name | Item name |
| Description | Full description |
| Parent_ID | ID of parent item |
| Priority | critical, high, medium, low |
| Status | not_started, in_progress, blocked, completed |
| Estimated_Hours | Time estimate (computed for parents) |
| Prerequisites | Comma-separated prerequisite IDs |
| Acceptance_Criteria | Pipe-separated criteria |
| Labels | Comma-separated labels |
| Claude_Code_Prompt | Implementation prompt (tasks only) |

## Development

### Setup

```bash
git clone https://github.com/yourusername/arcane.git
cd arcane
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
arcane/
├── cli.py              # Typer CLI commands
├── config.py           # Pydantic settings
├── clients/            # AI provider clients
│   ├── base.py         # BaseAIClient interface
│   └── anthropic.py    # Claude implementation
├── questions/          # Discovery question system
│   ├── base.py         # Question interface
│   ├── registry.py     # Question ordering
│   └── conductor.py    # Interactive flow
├── items/              # Pydantic data models
│   ├── task.py         # Task model
│   ├── story.py        # Story model
│   ├── epic.py         # Epic model
│   ├── milestone.py    # Milestone model
│   └── roadmap.py      # Roadmap container
├── generators/         # AI generation logic
│   ├── base.py         # BaseGenerator with retry
│   ├── orchestrator.py # Hierarchical coordinator
│   └── *.py            # Individual generators
├── templates/          # Jinja2 prompt templates
│   ├── system/         # System prompts
│   └── user/           # User prompts
├── project_management/ # PM tool exporters
│   ├── csv.py          # CSV export
│   ├── linear.py       # Linear (stub)
│   ├── jira.py         # Jira (stub)
│   └── notion.py       # Notion (stub)
└── storage/            # Persistence layer
    └── manager.py      # Save/load/resume
```

## License

MIT License - see [LICENSE](LICENSE) for details.
