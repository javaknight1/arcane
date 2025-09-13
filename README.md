# Roadmap Notion Importer

A Python tool to parse CSV roadmaps and import them into Notion as a project management system.

## Features

- Parse CSV roadmap files containing project phases, epics, and tasks
- Automatically create Notion databases and pages
- Set up relationships between projects, epics, and tasks
- Handle dependencies and timelines

## Installation

1. Clone the repository:
```bash
git clone https://github.com/javaknight1/notion-roadmap.git
cd notion-roadmap
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add your Notion API credentials to `.env`:
   - `NOTION_API_KEY`: Your Notion integration token
   - `NOTION_DATABASE_ID`: The ID of your Notion database

## Usage

### As a Python Package:
```python
from roadmap_notion.parser import parse_roadmap
from roadmap_notion.importer import NotionImporter

# Parse a roadmap text file to CSV
parse_roadmap("roadmap.txt", "output.csv")

# Import CSV to Notion
importer = NotionImporter()
importer.run_import("output.csv")
```

### Command Line:
```bash
# Parse a roadmap text file
roadmap-parse input.txt output.csv

# Import to Notion
roadmap-import roadmap.csv
```

## CSV Format

The CSV should contain the following columns:
- **Name**: The name/title of the roadmap item
- **Type**: Project, Milestone, Epic, Story, or Task
- **Parent**: The name of the parent item (for hierarchy)
- **Duration**: Duration in hours (optional)
- **Priority**: Critical, High, Medium, or Low
- **Status**: Not Started, In Progress, Completed, or Blocked
- **Goal/Description**: Detailed description of the item
- **Benefits**: Expected benefits (optional)
- **Prerequisites**: Required prerequisites (optional)
- **Technical Requirements**: Technical requirements (optional)
- **Claude Code Prompt**: AI prompts for implementation (optional)

See `examples/sample_roadmap.csv` for a complete example.

## Development

### Setting up for development:
```bash
git clone https://github.com/javaknight1/notion-roadmap.git
cd notion-roadmap
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### Running tests:
```bash
pytest
```

### Code formatting:
```bash
black .
flake8 .
```

## Examples

Check the `examples/` directory for:
- `sample_roadmap.csv`: Example CSV file format
- `example_usage.py`: Python usage examples

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)