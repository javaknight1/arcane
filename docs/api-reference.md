# API Reference

This document provides technical details about the modules and classes in the Roadmap Notion tool.

## Core Modules

### CLI Module (`roadmap_notion.cli`)

The main command-line interface for the application.

#### `RoadmapCLI`

Main CLI application class that orchestrates the entire workflow.

**Methods:**
- `run()`: Main application entry point
- `select_llm()`: Interactive LLM provider selection
- `check_environment_variables(llm_provider)`: Validate required environment variables
- `get_idea_file()`: Prompt for project idea file
- `get_roadmap_preferences()`: Collect user preferences for roadmap generation
- `generate_roadmap(llm_provider, idea_file, preferences)`: Generate roadmap using AI
- `convert_to_csv(roadmap_file)`: Convert roadmap text to CSV format
- `import_to_notion(csv_file)`: Import CSV data to Notion

### Generator Module (`roadmap_notion.generator`)

Handles AI-powered roadmap generation using various LLM providers.

#### `RoadmapGenerator`

Generates comprehensive project roadmaps using LLM providers.

**Constructor:**
```python
RoadmapGenerator(llm_client)
```

**Methods:**
- `create_roadmap_prompt(idea_content, preferences)`: Create comprehensive prompt for roadmap generation
- `generate(idea_content, preferences)`: Generate roadmap using the selected LLM
- `_get_timestamp()`: Get current timestamp in readable format

### LLM Client Module (`roadmap_notion.llm_client`)

Unified interface for multiple LLM providers.

#### `LLMClient`

Factory class for creating LLM clients.

**Static Methods:**
- `create(provider)`: Create an LLM client for the specified provider

**Methods:**
- `generate(prompt)`: Generate text using the configured LLM

#### Provider-Specific Clients

**`ClaudeLLMClient`**
- Anthropic Claude integration
- Uses `claude-3-5-sonnet-20241022` model
- Requires `ANTHROPIC_API_KEY` environment variable

**`OpenAILLMClient`**
- OpenAI GPT integration
- Uses `gpt-4-turbo-preview` model
- Requires `OPENAI_API_KEY` environment variable

**`GeminiLLMClient`**
- Google Gemini integration
- Uses `gemini-1.5-pro` model
- Requires `GOOGLE_API_KEY` environment variable

### Parser Module (`roadmap_notion.parser`)

Parses roadmap text files and converts them to structured CSV format.

#### `RoadmapParser`

Comprehensive parser for roadmap text files.

**Methods:**
- `parse_file(filepath)`: Parse roadmap.txt file and extract all hierarchy levels
- `save_to_csv(output_path)`: Save parsed items to CSV file
- `_parse_milestone(line)`: Parse milestone line
- `_parse_epic(line)`: Parse epic line
- `_parse_story(line)`: Parse story line
- `_parse_task(line)`: Parse task line
- `_parse_duration(duration_str)`: Parse duration string and extract hours
- `_ensure_project_root()`: Ensure there's a project root item

**Utility Functions:**
- `parse_roadmap(file_path, output_path=None)`: Parse a roadmap text file and optionally save to CSV

### Importer Module (`roadmap_notion.importer`)

Imports CSV data into Notion with organized page structure.

#### `NotionImporter`

Clean, modular Notion roadmap importer.

**Constructor:**
```python
NotionImporter(notion_token, parent_page_id)
```

**Methods:**
- `load_roadmap_data(csv_file)`: Load roadmap data from CSV file
- `create_container_page()`: Create the main container page for the roadmap
- `create_database(container_page_id)`: Create the roadmap database
- `populate_database()`: Populate the database with roadmap items
- `create_management_pages(container_page_id)`: Create all management and analytics pages
- `run_import(csv_file)`: Run the complete import process

## Page Creation Modules

### Base Page (`roadmap_notion.pages.base`)

#### `BasePage`

Abstract base class for creating Notion pages.

**Methods:**
- `create(parent_page_id, **kwargs)`: Create the page and return its ID (abstract)
- `create_text_block(content, annotations=None)`: Create a text block with optional formatting
- `create_paragraph(content, annotations=None)`: Create a paragraph block
- `create_heading(level, content, annotations=None)`: Create a heading block (1, 2, or 3)
- `create_bulleted_list_item(content, annotations=None)`: Create a bulleted list item
- `create_link_to_page(page_id)`: Create a link to another page
- `create_divider()`: Create a divider block
- `get_items_by_type(item_type)`: Get all items of a specific type
- `get_items_by_status(status)`: Get all items with a specific status
- `calculate_completion_percentage()`: Calculate overall completion percentage

### Database Creator (`roadmap_notion.pages.database`)

#### `DatabaseCreator`

Creates the main roadmap database with proper schema.

**Methods:**
- `create(parent_page_id, **kwargs)`: Create the roadmap database

### Overview Page (`roadmap_notion.pages.overview`)

#### `OverviewPage`

Creates the roadmap overview page with complete table of contents.

**Methods:**
- `create(parent_page_id, database_id=None, **kwargs)`: Create the roadmap overview page
- `_generate_table_of_contents()`: Generate hierarchical table of contents with ALL roadmap items

### Analytics Pages

**`AnalyticsHubPage`**: Creates the Analytics Hub container page
**`DashboardPage`**: Creates project dashboard with high-level metrics
**`BurndownPage`**: Creates burndown analytics page
**`SprintTrackingPage`**: Creates sprint tracking page
**`VelocityPage`**: Creates velocity analytics page
**`TimelinePage`**: Creates timeline progress page

## Data Structures

### Roadmap Item Structure

Each roadmap item in the CSV has the following structure:

```python
{
    'Name': str,                    # Item name/title
    'Type': str,                    # Project|Milestone|Epic|Story|Task
    'Parent': str,                  # Parent item name (empty for root)
    'Duration': str,                # Duration in hours
    'Priority': str,                # Critical|High|Medium|Low
    'Status': str,                  # Not Started|In Progress|Blocked|Completed|On Hold
    'Goal/Description': str,        # Detailed description
    'Benefits': str,                # Business and technical benefits
    'Prerequisites': str,           # What needs to be done first
    'Technical Requirements': str,  # Technical specifications
    'Claude Code Prompt': str       # Implementation guidance for Claude Code
}
```

### Hierarchy Levels

The tool supports five levels of hierarchy:

1. **Project**: Root level container
2. **Milestone**: Major phases representing significant business value
3. **Epic**: Major feature areas or technical components
4. **Story**: User-facing functionality or major technical work
5. **Task**: Specific implementation work

## Configuration

### Environment Variables

**Required:**
- `NOTION_TOKEN`: Notion integration token
- `NOTION_PARENT_PAGE_ID`: Parent page ID for roadmap creation

**LLM Providers (at least one required):**
- `ANTHROPIC_API_KEY`: Claude API key
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_API_KEY`: Google Gemini API key

### Notion Database Schema

The generated database includes these properties:

- **Name** (Title): Item name
- **Type** (Select): Item type with color coding
- **Status** (Select): Current status with color coding
- **Priority** (Select): Priority level with color coding
- **Duration** (Number): Estimated hours
- **Parent** (Relation): Self-referential relationship
- **Goal/Description** (Rich Text): Detailed description
- **Benefits** (Rich Text): Business benefits
- **Prerequisites** (Rich Text): Dependencies
- **Technical Requirements** (Rich Text): Technical specs
- **Claude Code Prompt** (Rich Text): Implementation guidance

## Error Handling

### Common Exceptions

- `ValueError`: Invalid configuration or missing required parameters
- `ImportError`: Missing required packages for LLM providers
- `RuntimeError`: API errors from LLM providers or Notion
- `FileNotFoundError`: Missing input files

### Validation

The tool includes validation for:
- Environment variable presence
- File existence and readability
- API key validity
- Notion workspace access
- CSV format and required columns

## Extensions

### Adding New LLM Providers

To add a new LLM provider:

1. Create a new client class inheriting from `BaseLLMClient`
2. Implement the `generate(prompt)` method
3. Add the provider to the `LLMClient.create()` factory method
4. Update CLI options and environment variable checking

### Custom Page Types

To add new page types:

1. Create a new class inheriting from `BasePage`
2. Implement the `create(parent_page_id, **kwargs)` method
3. Add the page to the importer's page creation workflow
4. Update the pages module `__init__.py` file

### Custom Parsers

To support additional input formats:

1. Create a new parser class with similar interface to `RoadmapParser`
2. Implement parsing logic for your format
3. Ensure output matches the expected CSV structure
4. Add CLI commands for the new parser