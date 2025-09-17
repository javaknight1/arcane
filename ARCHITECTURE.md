# Arcane - Architecture Documentation

## Overview

This application has been completely refactored to use a clean, modular architecture that separates concerns and makes the codebase more maintainable and extensible. The new architecture follows the **Engine Pattern** with clear separation between data models, business logic, and external integrations.

## Directory Structure

```
arcane/
├── constants/           # Application constants and configuration
│   ├── templates.py     # LLM prompt templates
│   └── settings.py      # Configuration constants
├── engines/             # Core business logic engines
│   ├── generation/      # Roadmap generation using LLMs
│   ├── export/          # File export (CSV, JSON, YAML)
│   └── import_engine/   # Import to external systems (Notion)
├── items/               # Data models for roadmap hierarchy
│   ├── base.py          # Base Item class
│   ├── project.py       # Project (root level)
│   ├── milestone.py     # Milestone
│   ├── epic.py          # Epic
│   ├── story.py         # Story
│   ├── task.py          # Task
│   └── roadmap.py       # Roadmap container
├── llm_clients/         # LLM provider implementations
│   ├── base.py          # Abstract base class
│   ├── claude.py        # Anthropic Claude
│   ├── openai.py        # OpenAI GPT
│   ├── gemini.py        # Google Gemini
│   └── factory.py       # Factory pattern
├── pages/               # Notion page generators
└── prompts/             # Prompt building and templating
```

## Core Components

### 1. Data Models (`items/`)

**Hierarchy**: Project → Milestone → Epic → Story → Task

- **Base Item Class**: Common functionality for all roadmap items
- **Typed Classes**: Each level has its own class with specific behavior
- **Relationships**: Parent-child relationships are managed automatically
- **Methods**: Calculate duration, completion percentage, statistics

### 2. Engines (`engines/`)

**Generation Engine**: Converts user ideas into structured roadmaps using LLMs
- Prompt building and customization
- LLM interaction and response parsing
- Object creation from parsed text

**Export Engine**: Converts roadmap objects to various file formats
- CSV export (compatible with project management tools)
- JSON export (structured data)
- YAML export (human-readable)

**Import Engine**: Imports roadmaps into external systems
- Notion workspace creation
- Database and page generation
- Analytics and management pages

### 3. LLM Clients (`llm_clients/`)

**Factory Pattern**: Clean way to create different LLM providers
- Anthropic Claude
- OpenAI GPT
- Google Gemini
- Extensible for new providers

**Features**:
- Unified interface across providers
- Environment variable configuration
- Error handling and validation

### 4. Prompt System (`prompts/`)

**Template-Based**: All prompts stored as configurable templates
- Roadmap generation prompts
- Refinement and expansion prompts
- Context-aware prompt building

## API Usage

### New Modular API (Recommended)

```python
from arcane import (
    RoadmapGenerationEngine,
    FileExportEngine,
    NotionImportEngine
)

# Generate roadmap
engine = RoadmapGenerationEngine('claude')
roadmap = engine.generate_roadmap("Build a task manager", {
    'timeline': '6-months',
    'complexity': 'moderate'
})

# Export to files
exporter = FileExportEngine()
files = exporter.export_multiple(roadmap, 'my_roadmap')

# Import to Notion
importer = NotionImportEngine()
result = importer.import_roadmap(roadmap)
```

## Key Benefits

### 1. **Modularity**
- Each component has a single responsibility
- Easy to test and maintain individual parts
- Clear interfaces between components

### 2. **Extensibility**
- Easy to add new LLM providers
- Simple to add new export formats
- Straightforward to add new import targets

### 3. **Type Safety**
- Strong typing throughout the codebase
- Clear data models for all entities
- Compile-time error checking

### 4. **Clean Architecture**
- No legacy code or backward compatibility cruft
- Consistent API design throughout
- Modern Python practices

### 5. **Configuration Management**
- Centralized constants and settings
- Template-based prompt system
- Environment variable management

## Getting Started

### Quick Start Example

```python
from arcane import RoadmapGenerationEngine, FileExportEngine, NotionImportEngine

# Generate roadmap
engine = RoadmapGenerationEngine('claude')
roadmap = engine.generate_roadmap("Build a task manager", {
    'timeline': '6-months',
    'complexity': 'moderate'
})

# Export to files
exporter = FileExportEngine()
files = exporter.export_multiple(roadmap, 'my_roadmap')

# Import to Notion
importer = NotionImportEngine()
result = importer.import_roadmap(roadmap)
```

### Key Features

1. **Rich Data Objects**: Work with structured roadmap objects
2. **Multiple Export Formats**: Easy export to CSV, JSON, YAML
3. **Comprehensive Error Handling**: Clear error messages and validation
4. **Advanced Features**: Statistics, completion tracking, relationship management

## Future Enhancements

The new architecture makes it easy to add:

- **New LLM Providers**: Add files to `llm_clients/`
- **New Export Formats**: Extend `FileExportEngine`
- **New Import Targets**: Add engines for Jira, Asana, etc.
- **Advanced Analytics**: Extend roadmap statistics
- **Custom Templates**: Add new prompt templates
- **Validation Rules**: Add business logic validation

## Testing Strategy

Each component can be tested independently:

- **Unit Tests**: Test individual classes and methods
- **Integration Tests**: Test engine interactions
- **End-to-End Tests**: Test complete workflows
- **Mock Testing**: Mock LLM responses for consistent testing

This architecture provides a solid foundation for scaling into a SaaS product while maintaining simplicity for individual users.