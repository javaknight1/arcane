# CLAUDE.md - Arcane: AI-Powered Roadmap Generator

## Project Overview

Arcane is a command-line tool that transforms a project idea into a complete, detailed roadmap and imports it directly into project management software (Jira, Linear, Notion). It uses AI models with structured output enforcement to guarantee consistent, detailed results.

### Core Problem We're Solving

When generating roadmaps with AI in a single shot:
- Output format is inconsistent (missing fields, wrong structure)
- Details degrade as the output gets longer
- Context is lost between generating different items
- The model "forgets" the overall project vision when generating individual tasks

### Our Solution: Multi-Phase Hierarchical Generation

1. **Discovery Questions**: Structured questions gather project context before any generation
2. **Top-Down Skeleton**: Generate structure level-by-level (Milestones → Epics → Stories → Tasks)
3. **Structured Output Enforcement**: Use tool calling / Pydantic schemas to guarantee format
4. **Context Injection**: Every AI call includes full project context + parent hierarchy
5. **Template-Driven Prompts**: Prompt templates live in separate files, not hardcoded in Python

---

## Workflow Rules

- **TODO.md is the source of truth.** When a task (T37, T38, etc.) is completed, always update TODO.md to mark it done — strike through the task index row, check the sprint checklist item, and update the "Current Task" / "Current Sprint" header. Do not wait to be asked.

---

## Tech Stack

- **Language**: Python 3.11+
- **CLI Framework**: Typer (with Rich for beautiful output)
- **AI Clients**: Anthropic SDK (primary), extensible to OpenAI, etc.
- **Schema Validation**: Pydantic v2
- **Structured Output**: Instructor library (patches AI clients for Pydantic returns)
- **Prompt Templating**: Jinja2 (for template files)
- **Config Management**: Pydantic Settings + YAML files
- **HTTP Client**: httpx (async, for PM tool APIs)
- **Testing**: pytest + pytest-asyncio

---

## Project Structure

```
arcane/
├── pyproject.toml                  # Project config, dependencies
├── README.md                       # User documentation
├── CLAUDE.md                       # This file - development guide
├── TODO.md                         # Future features and improvements
├── .env.example                    # Example environment variables
├── src/
│   └── arcane/
│       ├── __init__.py
│       ├── __main__.py             # Entry point: python -m arcane
│       ├── cli.py                  # Typer CLI commands
│       ├── config.py               # Settings and configuration
│       │
│       ├── clients/                # AI provider clients
│       │   ├── __init__.py         # create_client() factory
│       │   ├── base.py             # BaseAIClient interface
│       │   ├── anthropic.py        # Claude client (Anthropic SDK + Instructor)
│       │   └── openai.py           # OpenAI client (future, same interface)
│       │
│       ├── questions/              # Pre-generation discovery prompts
│       │   ├── __init__.py
│       │   ├── base.py             # Question interface class
│       │   ├── registry.py         # QuestionRegistry - ordered collection
│       │   ├── conductor.py        # Runs the question flow interactively
│       │   ├── basic.py            # Project name, vision, problem, users
│       │   ├── constraints.py      # Timeline, team size, experience, budget
│       │   ├── technical.py        # Tech stack, infrastructure, existing code
│       │   └── requirements.py     # Must-have, nice-to-have, out of scope
│       │
│       ├── items/                  # Roadmap item models
│       │   ├── __init__.py         # Exports all models
│       │   ├── base.py             # Enums (Priority, Status) + BaseItem
│       │   ├── task.py             # Task model
│       │   ├── story.py            # Story model (contains Tasks)
│       │   ├── epic.py             # Epic model (contains Stories)
│       │   ├── milestone.py        # Milestone model (contains Epics)
│       │   ├── roadmap.py          # Roadmap model (contains Milestones)
│       │   └── context.py          # ProjectContext (built from questions)
│       │
│       ├── templates/              # Prompt template files (Jinja2)
│       │   ├── loader.py           # TemplateLoader utility class
│       │   ├── system/             # System prompts per item type
│       │   │   ├── milestone.j2
│       │   │   ├── epic.j2
│       │   │   ├── story.j2
│       │   │   └── task.j2
│       │   └── user/               # User prompts (context injection)
│       │       ├── generate.j2     # Main generation prompt
│       │       └── refine.j2       # Retry with error feedback
│       │
│       ├── generators/             # Generation orchestration logic
│       │   ├── __init__.py
│       │   ├── base.py             # BaseGenerator with retry + validation
│       │   ├── skeletons.py        # Intermediate skeleton models
│       │   ├── milestone.py        # MilestoneGenerator
│       │   ├── epic.py             # EpicGenerator
│       │   ├── story.py            # StoryGenerator
│       │   ├── task.py             # TaskGenerator
│       │   └── orchestrator.py     # RoadmapOrchestrator (coordinates everything)
│       │
│       ├── project_management/     # PM tool integrations
│       │   ├── __init__.py
│       │   ├── base.py             # BasePMClient interface
│       │   ├── jira.py             # Jira Cloud API client
│       │   ├── linear.py           # Linear GraphQL API client
│       │   ├── notion.py           # Notion API client
│       │   └── csv.py              # CSV fallback (no API needed)
│       │
│       ├── storage/                # Local persistence
│       │   ├── __init__.py
│       │   └── manager.py          # Save/load roadmaps, resume support
│       │
│       └── utils/                  # Shared utilities
│           ├── __init__.py
│           ├── console.py          # Rich console helpers
│           └── ids.py              # ULID generation utilities
│
└── tests/
    ├── conftest.py
    ├── test_clients/
    ├── test_questions/
    ├── test_items/
    ├── test_generators/
    ├── test_project_management/
    └── test_storage/
```

---

## How Data Flows Through the System

```
User runs: arcane new

  ┌──────────────┐     answers      ┌───────────────┐
  │  questions/   │ ───────────────► │ items/context  │
  │  conductor    │                  │ ProjectContext │
  └──────────────┘                  └───────┬───────┘
                                            │
                                            ▼
  ┌──────────────┐   prompts   ┌────────────────────┐   API calls   ┌───────────┐
  │  templates/   │ ──────────►│   generators/       │ ────────────► │ clients/  │
  │  *.j2 files   │            │   orchestrator      │ ◄──────────── │ anthropic │
  └──────────────┘            │                    │  structured   └───────────┘
                               │   milestone_gen    │  responses
                               │   epic_gen         │
                               │   story_gen        │
                               │   task_gen         │
                               └────────┬───────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │  items/           │
                               │  Roadmap          │
                               │    └ Milestones   │
                               │       └ Epics     │
                               │          └ Stories│
                               │             └Tasks│
                               └────────┬─────────┘
                                        │
                          ┌─────────────┼──────────────┐
                          ▼             ▼              ▼
                    ┌──────────┐  ┌──────────┐  ┌──────────────────┐
                    │ storage/ │  │ arcane    │  │ project_mgmt/    │
                    │ JSON     │  │ view cmd  │  │ CSV/Linear/Jira  │
                    └──────────┘  └──────────┘  └──────────────────┘
```

---

## Detailed Module Specs

---

### 1. `clients/` — AI Provider Clients

The clients folder abstracts AI provider APIs behind a common interface. This lets us swap between Claude, GPT-4, or local models without changing any generation logic.

#### BaseAIClient Interface

```python
# clients/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class BaseAIClient(ABC):
    """Abstract interface for AI provider clients.
    
    All AI clients must implement this interface. The generators
    only interact with this interface, never with provider SDKs directly.
    """
    
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> BaseModel:
        """Generate a structured response from the AI model.
        
        Args:
            system_prompt: The system-level instruction
            user_prompt: The user-level prompt with context
            response_model: Pydantic model class the response must conform to
            max_tokens: Maximum tokens in the response
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            An instance of response_model with validated data
            
        Raises:
            AIClientError: If the API call fails after retries
            ValidationError: If the response doesn't match the schema
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Test that the client can reach the API."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name (e.g., 'Anthropic Claude')"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """The specific model being used (e.g., 'claude-sonnet-4-20250514')"""
        pass


class AIClientError(Exception):
    """Raised when an AI client call fails."""
    pass
```

#### Anthropic Client Implementation

```python
# clients/anthropic.py
import instructor
import anthropic
from .base import BaseAIClient, AIClientError

class AnthropicClient(BaseAIClient):
    """Claude client using Anthropic SDK + Instructor for structured output."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._api_key = api_key
        self._model = model
        self._raw_client = anthropic.AsyncAnthropic(api_key=api_key)
        self._client = instructor.from_anthropic(self._raw_client)
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> BaseModel:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                response_model=response_model,
            )
            return response
        except Exception as e:
            raise AIClientError(f"Anthropic API call failed: {e}") from e
    
    async def validate_connection(self) -> bool:
        try:
            await self._raw_client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False
    
    @property
    def provider_name(self) -> str:
        return "Anthropic Claude"
    
    @property
    def model_name(self) -> str:
        return self._model
```

#### Client Factory

```python
# clients/__init__.py
from .base import BaseAIClient, AIClientError
from .anthropic import AnthropicClient

def create_client(provider: str, **kwargs) -> BaseAIClient:
    """Factory to create AI clients by provider name."""
    clients = {
        "anthropic": AnthropicClient,
    }
    if provider not in clients:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(clients.keys())}")
    return clients[provider](**kwargs)
```

---

### 2. `questions/` — Pre-Generation Discovery

The questions folder handles all user interaction before AI generation begins. Every question follows a strict interface so the system is extensible and the outputs are predictable.

#### Question Interface

```python
# questions/base.py
from abc import ABC, abstractmethod
from enum import Enum

class QuestionType(str, Enum):
    TEXT = "text"           # Free-form text input
    INT = "int"             # Integer input
    CHOICE = "choice"       # Single selection from options
    MULTI = "multi"         # Multiple selections from options
    LIST = "list"           # Comma-separated list input
    CONFIRM = "confirm"     # Yes/no

class Question(ABC):
    """Base interface for all discovery questions.
    
    Every question must define:
    - key: unique identifier (maps to ProjectContext field name)
    - prompt: the question string shown to the user
    - question_type: what kind of input to collect
    - required: whether the user must answer
    - options: list of valid answers (for CHOICE and MULTI types)
    - default: default value if user skips
    
    And must implement:
    - validate(): validate the raw user input
    - transform(): convert raw input to the output type
    """
    
    @property
    @abstractmethod
    def key(self) -> str:
        """Unique identifier for this question (maps to ProjectContext field)."""
        pass
    
    @property
    @abstractmethod
    def prompt(self) -> str:
        """The question text shown to the user."""
        pass
    
    @property
    @abstractmethod
    def question_type(self) -> QuestionType:
        """The type of input to collect."""
        pass
    
    @property
    def required(self) -> bool:
        return True
    
    @property
    def options(self) -> list[str] | None:
        return None
    
    @property
    def default(self) -> str | None:
        return None
    
    @property
    def help_text(self) -> str | None:
        return None
    
    def validate(self, raw_input: str) -> bool:
        """Validate the raw user input. Override for custom validation."""
        if self.required and not raw_input.strip():
            return False
        return True
    
    def transform(self, raw_input: str):
        """Transform raw string input into the desired output type."""
        raw = raw_input.strip()
        match self.question_type:
            case QuestionType.TEXT:
                return raw
            case QuestionType.INT:
                return int(raw) if raw else self.default
            case QuestionType.CHOICE:
                return raw
            case QuestionType.MULTI:
                return [x.strip() for x in raw.split(",") if x.strip()]
            case QuestionType.LIST:
                return [x.strip() for x in raw.split(",") if x.strip()]
            case QuestionType.CONFIRM:
                return raw.lower() in ("y", "yes", "true", "1")
```

#### Example Questions

```python
# questions/basic.py
from .base import Question, QuestionType

class ProjectNameQuestion(Question):
    @property
    def key(self) -> str:
        return "project_name"
    
    @property
    def prompt(self) -> str:
        return "What's the name of your project?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT


class VisionQuestion(Question):
    @property
    def key(self) -> str:
        return "vision"
    
    @property
    def prompt(self) -> str:
        return "Describe your app in 2-3 sentences. What does it do?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT
    
    @property
    def help_text(self) -> str:
        return "Be specific about what the app does, not just the category"


class ProblemStatementQuestion(Question):
    @property
    def key(self) -> str:
        return "problem_statement"
    
    @property
    def prompt(self) -> str:
        return "What problem does this solve for users?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT


class TargetUsersQuestion(Question):
    @property
    def key(self) -> str:
        return "target_users"
    
    @property
    def prompt(self) -> str:
        return "Who are your target users?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST
    
    @property
    def help_text(self) -> str:
        return "Comma-separated, e.g.: field technicians, dispatchers, business owners"
```

```python
# questions/constraints.py
from .base import Question, QuestionType

class TimelineQuestion(Question):
    @property
    def key(self) -> str:
        return "timeline"
    
    @property
    def prompt(self) -> str:
        return "What's your target timeline?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE
    
    @property
    def options(self) -> list[str]:
        return ["1 month MVP", "3 months", "6 months", "1 year", "custom"]


class TeamSizeQuestion(Question):
    @property
    def key(self) -> str:
        return "team_size"
    
    @property
    def prompt(self) -> str:
        return "How many developers will work on this?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.INT
    
    @property
    def default(self) -> str:
        return "1"
    
    def validate(self, raw_input: str) -> bool:
        try:
            val = int(raw_input.strip()) if raw_input.strip() else int(self.default)
            return 1 <= val <= 100
        except ValueError:
            return False


class DeveloperExperienceQuestion(Question):
    @property
    def key(self) -> str:
        return "developer_experience"
    
    @property
    def prompt(self) -> str:
        return "What's the team's experience level?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE
    
    @property
    def options(self) -> list[str]:
        return ["junior", "mid-level", "senior", "mixed"]


class BudgetQuestion(Question):
    @property
    def key(self) -> str:
        return "budget_constraints"
    
    @property
    def prompt(self) -> str:
        return "What's your budget situation?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE
    
    @property
    def options(self) -> list[str]:
        return ["minimal (free tier everything)", "moderate", "flexible"]
```

```python
# questions/technical.py
from .base import Question, QuestionType

class TechStackQuestion(Question):
    @property
    def key(self) -> str:
        return "tech_stack"
    
    @property
    def prompt(self) -> str:
        return "What technologies do you want to use?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST
    
    @property
    def required(self) -> bool:
        return False
    
    @property
    def help_text(self) -> str:
        return "Comma-separated (e.g.: React, Go, PostgreSQL) or leave blank for AI to suggest"


class InfrastructureQuestion(Question):
    @property
    def key(self) -> str:
        return "infrastructure_preferences"
    
    @property
    def prompt(self) -> str:
        return "Any infrastructure preferences?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE
    
    @property
    def options(self) -> list[str]:
        return ["AWS", "GCP", "Azure", "Serverless", "Self-hosted", "No preference"]
    
    @property
    def required(self) -> bool:
        return False


class ExistingCodebaseQuestion(Question):
    @property
    def key(self) -> str:
        return "existing_codebase"
    
    @property
    def prompt(self) -> str:
        return "Are you adding to an existing codebase?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CONFIRM
    
    @property
    def default(self) -> str:
        return "n"
```

```python
# questions/requirements.py
from .base import Question, QuestionType

class MustHaveQuestion(Question):
    @property
    def key(self) -> str:
        return "must_have_features"
    
    @property
    def prompt(self) -> str:
        return "What features are absolutely required for launch?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST
    
    @property
    def help_text(self) -> str:
        return "Comma-separated, e.g.: user auth, job scheduling, mobile app"


class NiceToHaveQuestion(Question):
    @property
    def key(self) -> str:
        return "nice_to_have_features"
    
    @property
    def prompt(self) -> str:
        return "What features would be nice to have but aren't critical?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST
    
    @property
    def required(self) -> bool:
        return False


class OutOfScopeQuestion(Question):
    @property
    def key(self) -> str:
        return "out_of_scope"
    
    @property
    def prompt(self) -> str:
        return "Anything explicitly out of scope?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST
    
    @property
    def required(self) -> bool:
        return False
    
    @property
    def help_text(self) -> str:
        return "Helps the AI avoid generating roadmap items for things you don't want"


class SimilarProductsQuestion(Question):
    @property
    def key(self) -> str:
        return "similar_products"
    
    @property
    def prompt(self) -> str:
        return "Any similar products or competitors to reference?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST
    
    @property
    def required(self) -> bool:
        return False


class NotesQuestion(Question):
    @property
    def key(self) -> str:
        return "notes"
    
    @property
    def prompt(self) -> str:
        return "Any additional context or notes?"
    
    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT
    
    @property
    def required(self) -> bool:
        return False
```

#### Question Registry

```python
# questions/registry.py
from .base import Question
from .basic import ProjectNameQuestion, VisionQuestion, ProblemStatementQuestion, TargetUsersQuestion
from .constraints import TimelineQuestion, TeamSizeQuestion, DeveloperExperienceQuestion, BudgetQuestion
from .technical import TechStackQuestion, InfrastructureQuestion, ExistingCodebaseQuestion
from .requirements import MustHaveQuestion, NiceToHaveQuestion, OutOfScopeQuestion, SimilarProductsQuestion, NotesQuestion

class QuestionRegistry:
    """Ordered collection of all questions, grouped by category."""
    
    CATEGORIES: dict[str, list[type[Question]]] = {
        "Basic Information": [
            ProjectNameQuestion,
            VisionQuestion,
            ProblemStatementQuestion,
            TargetUsersQuestion,
        ],
        "Constraints": [
            TimelineQuestion,
            TeamSizeQuestion,
            DeveloperExperienceQuestion,
            BudgetQuestion,
        ],
        "Technical": [
            TechStackQuestion,
            InfrastructureQuestion,
            ExistingCodebaseQuestion,
        ],
        "Requirements": [
            MustHaveQuestion,
            NiceToHaveQuestion,
            OutOfScopeQuestion,
            SimilarProductsQuestion,
            NotesQuestion,
        ],
    }
    
    def get_all_questions(self) -> list[tuple[str, Question]]:
        """Return all questions as (category_name, question_instance) pairs."""
        result = []
        for category, question_classes in self.CATEGORIES.items():
            for cls in question_classes:
                result.append((category, cls()))
        return result
```

#### Question Conductor

```python
# questions/conductor.py
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

from .base import Question, QuestionType
from .registry import QuestionRegistry
from ..items.context import ProjectContext

class QuestionConductor:
    """Runs the interactive question flow and builds a ProjectContext."""
    
    def __init__(self, console: Console):
        self.console = console
        self.registry = QuestionRegistry()
        self.answers: dict[str, any] = {}
    
    async def run(self) -> ProjectContext:
        """Run the full question flow and return a ProjectContext."""
        self.console.print(Panel(
            "🔮 [bold magenta]Arcane[/bold magenta] - Let's build your roadmap!\n"
            "Answer a few questions so we can generate the best plan for your project.",
            border_style="magenta",
        ))
        
        current_category = None
        
        for category, question in self.registry.get_all_questions():
            if category != current_category:
                current_category = category
                self.console.print(f"\n[bold cyan]── {category} ──[/bold cyan]")
            
            # Skip if already answered (e.g., --name flag pre-filled project_name)
            if question.key in self.answers:
                continue
            
            answer = self._ask(question)
            if answer is not None:
                self.answers[question.key] = answer
        
        return ProjectContext(**self.answers)
    
    def _ask(self, question: Question):
        """Ask a single question and return the transformed answer."""
        if question.help_text:
            self.console.print(f"  [dim]{question.help_text}[/dim]")
        
        suffix = "" if question.required else " (optional, press Enter to skip)"
        
        match question.question_type:
            case QuestionType.TEXT | QuestionType.LIST:
                raw = Prompt.ask(
                    f"  {question.prompt}{suffix}",
                    default=question.default or "",
                    console=self.console,
                )
            case QuestionType.INT:
                raw = str(IntPrompt.ask(
                    f"  {question.prompt}",
                    default=int(question.default) if question.default else None,
                    console=self.console,
                ))
            case QuestionType.CHOICE:
                raw = Prompt.ask(
                    f"  {question.prompt}",
                    choices=question.options,
                    default=question.default,
                    console=self.console,
                )
            case QuestionType.CONFIRM:
                result = Confirm.ask(
                    f"  {question.prompt}",
                    default=question.default == "y",
                    console=self.console,
                )
                return result
            case _:
                raw = Prompt.ask(f"  {question.prompt}", console=self.console)
        
        if not raw.strip() and not question.required:
            return question.default if question.default else (
                [] if question.question_type in (QuestionType.LIST, QuestionType.MULTI) else ""
            )
        
        if not question.validate(raw):
            self.console.print("  [red]Invalid input. Please try again.[/red]")
            return self._ask(question)
        
        return question.transform(raw)
```

---

### 3. `items/` — Roadmap Item Models

All Pydantic models for roadmap entities. These are the data structures that flow through the entire system.

#### Base Models

```python
# items/base.py
from enum import Enum
from pydantic import BaseModel
from ulid import ULID

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Status(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"

class BaseItem(BaseModel):
    """Base class for all roadmap items."""
    id: str
    name: str
    description: str
    priority: Priority
    status: Status = Status.NOT_STARTED
    labels: list[str] = []

def generate_id(prefix: str) -> str:
    """Generate a unique ID like 'task-01HQ...' using ULID."""
    return f"{prefix}-{ULID()}"
```

#### Task Model

```python
# items/task.py
from pydantic import Field
from .base import BaseItem

class Task(BaseItem):
    """The most granular unit of work. Completable in 1-8 hours."""
    estimated_hours: int = Field(ge=1, le=40)
    prerequisites: list[str] = []           # IDs of dependent tasks
    acceptance_criteria: list[str]
    implementation_notes: str
    claude_code_prompt: str                  # Ready-to-use prompt for implementation
```

#### Story Model

```python
# items/story.py
from pydantic import computed_field
from .base import BaseItem
from .task import Task

class Story(BaseItem):
    """A user-facing capability. Contains multiple Tasks."""
    acceptance_criteria: list[str]
    tasks: list[Task] = []
    
    @computed_field
    @property
    def estimated_hours(self) -> int:
        return sum(t.estimated_hours for t in self.tasks)
```

#### Epic Model

```python
# items/epic.py
from pydantic import computed_field
from .base import BaseItem
from .story import Story

class Epic(BaseItem):
    """A feature area or system component. Contains multiple Stories."""
    goal: str
    prerequisites: list[str] = []
    stories: list[Story] = []
    
    @computed_field
    @property
    def estimated_hours(self) -> int:
        return sum(s.estimated_hours for s in self.stories)
```

#### Milestone Model

```python
# items/milestone.py
from pydantic import computed_field
from .base import BaseItem
from .epic import Epic

class Milestone(BaseItem):
    """A major phase or deliverable. Contains multiple Epics."""
    goal: str
    target_date: str | None = None
    epics: list[Epic] = []
    
    @computed_field
    @property
    def estimated_hours(self) -> int:
        return sum(e.estimated_hours for e in self.epics)
```

#### Roadmap Model

```python
# items/roadmap.py
from datetime import datetime
from pydantic import BaseModel, computed_field
from .milestone import Milestone
from .context import ProjectContext

class Roadmap(BaseModel):
    """Top-level container. The complete output of arcane."""
    id: str
    project_name: str
    created_at: datetime
    updated_at: datetime
    context: ProjectContext
    milestones: list[Milestone] = []
    
    @computed_field
    @property
    def total_hours(self) -> int:
        return sum(m.estimated_hours for m in self.milestones)
    
    @computed_field
    @property
    def total_items(self) -> dict[str, int]:
        milestones = len(self.milestones)
        epics = sum(len(m.epics) for m in self.milestones)
        stories = sum(len(e.stories) for m in self.milestones for e in m.epics)
        tasks = sum(len(s.tasks) for m in self.milestones for e in m.epics for s in e.stories)
        return {"milestones": milestones, "epics": epics, "stories": stories, "tasks": tasks}
```

#### ProjectContext Model

```python
# items/context.py
from pydantic import BaseModel

class ProjectContext(BaseModel):
    """Built from question answers. Injected into every AI call.
    
    Field names match the Question.key values exactly so the 
    conductor can build this directly from answers dict.
    """
    project_name: str
    vision: str
    problem_statement: str
    target_users: list[str]
    timeline: str
    team_size: int
    developer_experience: str
    budget_constraints: str
    tech_stack: list[str] = []
    infrastructure_preferences: str = "No preference"
    existing_codebase: bool = False
    must_have_features: list[str]
    nice_to_have_features: list[str] = []
    out_of_scope: list[str] = []
    similar_products: list[str] = []
    notes: str = ""
```

#### Items Package Init

```python
# items/__init__.py
from .base import Priority, Status, BaseItem, generate_id
from .task import Task
from .story import Story
from .epic import Epic
from .milestone import Milestone
from .roadmap import Roadmap
from .context import ProjectContext

__all__ = [
    "Priority", "Status", "BaseItem", "generate_id",
    "Task", "Story", "Epic", "Milestone", "Roadmap", "ProjectContext",
]
```

---

### 4. `templates/` — Prompt Template Files

Prompt templates live as Jinja2 files, NOT hardcoded in Python. This makes them easy to iterate on, test, and version separately from code.

#### Template Loader

```python
# templates/loader.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class TemplateLoader:
    """Loads and renders Jinja2 prompt templates."""
    
    def __init__(self):
        template_dir = Path(__file__).parent
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    
    def render_system(self, item_type: str) -> str:
        """Render a system prompt template (milestone, epic, story, task)."""
        template = self.env.get_template(f"system/{item_type}.j2")
        return template.render()
    
    def render_user(
        self,
        template_name: str,
        project_context: dict,
        parent_context: dict | None = None,
        sibling_context: list[str] | None = None,
        additional_guidance: str | None = None,
        errors: list[str] | None = None,
    ) -> str:
        """Render a user prompt template with context injection."""
        template = self.env.get_template(f"user/{template_name}.j2")
        return template.render(
            project=project_context,
            parent=parent_context,
            siblings=sibling_context,
            guidance=additional_guidance,
            errors=errors,
        )
```

#### System Prompt Templates

```jinja2
{# templates/system/milestone.j2 #}
You are an expert software project planner generating milestones for a software project roadmap.

A milestone represents a major phase or deliverable. Each milestone should:
- Represent a significant, demonstrable achievement
- Have a clear, measurable goal
- Be sequenced logically (foundations before features, MVP before scale)
- Account for the team size and timeline constraints
- Be completable independently (even if later milestones depend on it)

Generate ONLY milestone skeletons. Do NOT generate epics, stories, or tasks.
The milestones will be expanded in subsequent generation steps.

Be practical and realistic. Avoid generic filler milestones.
Every milestone should deliver tangible value.
```

```jinja2
{# templates/system/epic.j2 #}
You are an expert software project planner generating epics for a milestone.

An epic represents a coherent feature area or system component. Each epic should:
- Represent a distinct, bounded area of work
- Not overlap with other epics in this milestone
- Be achievable by the team in a reasonable timeframe
- Include all necessary work (no hidden complexity)
- Have a clear goal that contributes to the milestone's objective

Generate ONLY epic skeletons. Stories and tasks come in later steps.
```

```jinja2
{# templates/system/story.j2 #}
You are an expert software project planner generating user stories for an epic.

A story represents a user-facing capability or developer deliverable. Each story should:
- Be completable in 1-5 days by one developer
- Have clear acceptance criteria (testable conditions)
- Be independent enough to work on separately
- Contribute directly to the epic's goal
- Be sized appropriately for the team's experience level

Generate ONLY story skeletons. Tasks come in the next step.
```

```jinja2
{# templates/system/task.j2 #}
You are an expert software engineer generating implementation tasks for a user story.

A task is the most granular unit of work. Each task should:
- Be completable in 1-8 hours by one developer
- Have a single, clear objective
- Include specific implementation guidance
- Reference the project's tech stack and patterns
- Include a ready-to-use Claude Code prompt

For the claude_code_prompt field, write a detailed prompt that a developer could paste
directly into Claude Code to implement this task. Include:
- Specific files to create or modify
- Technology choices and patterns to follow
- Input/output specifications
- Error handling requirements
- Testing requirements
```

#### User Prompt Templates

```jinja2
{# templates/user/generate.j2 #}
## Project Context
Project: {{ project.project_name }}
Vision: {{ project.vision }}
Problem: {{ project.problem_statement }}
Target Users: {{ project.target_users | join(", ") }}
Timeline: {{ project.timeline }}
Team: {{ project.team_size }} developer(s), {{ project.developer_experience }} level
Budget: {{ project.budget_constraints }}
{% if project.tech_stack %}
Tech Stack: {{ project.tech_stack | join(", ") }}
{% endif %}
{% if project.infrastructure_preferences != "No preference" %}
Infrastructure: {{ project.infrastructure_preferences }}
{% endif %}
Must-Have Features: {{ project.must_have_features | join(", ") }}
{% if project.nice_to_have_features %}
Nice-to-Have: {{ project.nice_to_have_features | join(", ") }}
{% endif %}
{% if project.out_of_scope %}
Out of Scope: {{ project.out_of_scope | join(", ") }}
{% endif %}
{% if project.similar_products %}
Similar Products: {{ project.similar_products | join(", ") }}
{% endif %}
{% if project.notes %}
Additional Notes: {{ project.notes }}
{% endif %}

{% if parent %}
## Parent Context
This item belongs to:
{% for level, data in parent.items() %}
- {{ level | capitalize }}: {{ data.name }} — {{ data.goal | default(data.description, true) }}
{% endfor %}
{% endif %}

{% if siblings %}
## Already Generated (Do NOT Duplicate)
{% for sibling in siblings %}
- {{ sibling }}
{% endfor %}
{% endif %}

{% if guidance %}
## Additional Guidance
{{ guidance }}
{% endif %}
```

```jinja2
{# templates/user/refine.j2 #}
Your previous response had validation errors. Please fix these issues and try again.

## Errors
{% for error in errors %}
- {{ error }}
{% endfor %}
```

---

### 5. `generators/` — Generation Orchestration

Generators coordinate AI calls. They use clients for API access, templates for prompts, and return items.

#### BaseGenerator

```python
# generators/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError
from rich.console import Console

from ..clients.base import BaseAIClient, AIClientError
from ..items.context import ProjectContext
from ..templates.loader import TemplateLoader

class GenerationError(Exception):
    """Raised when generation fails after all retries."""
    pass

class BaseGenerator(ABC):
    """Base class for all generators.
    
    Handles: template rendering, AI calls, retry with feedback, validation.
    Subclasses only need to define item_type and response_model.
    """
    
    def __init__(
        self,
        client: BaseAIClient,
        console: Console,
        templates: TemplateLoader,
        max_retries: int = 3,
    ):
        self.client = client
        self.console = console
        self.templates = templates
        self.max_retries = max_retries
    
    @property
    @abstractmethod
    def item_type(self) -> str:
        """'milestone', 'epic', 'story', or 'task'"""
        pass
    
    @abstractmethod
    def get_response_model(self) -> type[BaseModel]:
        """The Pydantic model the AI response must conform to."""
        pass
    
    async def generate(
        self,
        project_context: ProjectContext,
        parent_context: dict | None = None,
        sibling_context: list[str] | None = None,
        additional_guidance: str | None = None,
    ) -> BaseModel:
        """Generate items with retry logic and validation."""
        
        system_prompt = self.templates.render_system(self.item_type)
        user_prompt = self.templates.render_user(
            "generate",
            project_context=project_context.model_dump(),
            parent_context=parent_context,
            sibling_context=sibling_context,
            additional_guidance=additional_guidance,
        )
        
        errors_so_far: list[str] = []
        
        for attempt in range(self.max_retries):
            try:
                if errors_so_far:
                    user_prompt = self.templates.render_user(
                        "refine",
                        project_context=project_context.model_dump(),
                        errors=errors_so_far,
                    )
                
                response = await self.client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=self.get_response_model(),
                )
                
                extra_errors = self._validate(response, project_context, sibling_context)
                if extra_errors:
                    errors_so_far.extend(extra_errors)
                    continue
                
                return response
                
            except (AIClientError, ValidationError) as e:
                errors_so_far.append(str(e))
                if attempt < self.max_retries - 1:
                    self.console.print(f"  [yellow]⚠ Attempt {attempt + 1} failed, retrying...[/yellow]")
                else:
                    raise GenerationError(
                        f"Failed to generate {self.item_type} after {self.max_retries} attempts.\n"
                        f"Errors: {errors_so_far}"
                    )
    
    def _validate(self, response: BaseModel, context: ProjectContext, siblings: list[str] | None) -> list[str]:
        """Optional extra validation. Override in subclasses. Return error list."""
        return []
```

#### Skeleton Models

```python
# generators/skeletons.py
from pydantic import BaseModel
from ..items.base import Priority

class MilestoneSkeleton(BaseModel):
    name: str
    goal: str
    description: str
    priority: Priority
    suggested_epic_areas: list[str]

class MilestoneSkeletonList(BaseModel):
    milestones: list[MilestoneSkeleton]

class EpicSkeleton(BaseModel):
    name: str
    goal: str
    description: str
    priority: Priority
    suggested_story_areas: list[str]

class EpicSkeletonList(BaseModel):
    epics: list[EpicSkeleton]

class StorySkeleton(BaseModel):
    name: str
    description: str
    priority: Priority
    acceptance_criteria: list[str]

class StorySkeletonList(BaseModel):
    stories: list[StorySkeleton]
```

#### Individual Generators

```python
# generators/milestone.py
from .base import BaseGenerator
from .skeletons import MilestoneSkeletonList

class MilestoneGenerator(BaseGenerator):
    @property
    def item_type(self) -> str:
        return "milestone"
    
    def get_response_model(self):
        return MilestoneSkeletonList
```

```python
# generators/epic.py
from .base import BaseGenerator
from .skeletons import EpicSkeletonList

class EpicGenerator(BaseGenerator):
    @property
    def item_type(self) -> str:
        return "epic"
    
    def get_response_model(self):
        return EpicSkeletonList
```

```python
# generators/story.py
from .base import BaseGenerator
from .skeletons import StorySkeletonList

class StoryGenerator(BaseGenerator):
    @property
    def item_type(self) -> str:
        return "story"
    
    def get_response_model(self):
        return StorySkeletonList
```

```python
# generators/task.py
from pydantic import BaseModel
from .base import BaseGenerator
from ..items.task import Task

class TaskList(BaseModel):
    tasks: list[Task]

class TaskGenerator(BaseGenerator):
    @property
    def item_type(self) -> str:
        return "task"
    
    def get_response_model(self):
        return TaskList
```

#### Orchestrator

```python
# generators/orchestrator.py
from datetime import datetime, timezone
from rich.console import Console
from rich.prompt import Prompt

from ..clients.base import BaseAIClient
from ..items import Roadmap, Milestone, Epic, Story, ProjectContext, generate_id
from ..templates.loader import TemplateLoader
from ..storage.manager import StorageManager

from .milestone import MilestoneGenerator
from .epic import EpicGenerator
from .story import StoryGenerator
from .task import TaskGenerator

class RoadmapOrchestrator:
    """Coordinates the full hierarchical generation process."""
    
    def __init__(
        self,
        client: BaseAIClient,
        console: Console,
        storage: StorageManager,
        interactive: bool = True,
    ):
        self.console = console
        self.storage = storage
        self.interactive = interactive
        
        templates = TemplateLoader()
        self.milestone_gen = MilestoneGenerator(client, console, templates)
        self.epic_gen = EpicGenerator(client, console, templates)
        self.story_gen = StoryGenerator(client, console, templates)
        self.task_gen = TaskGenerator(client, console, templates)
    
    async def generate(self, context: ProjectContext) -> Roadmap:
        roadmap = Roadmap(
            id=generate_id("roadmap"),
            project_name=context.project_name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=context,
        )
        
        # Phase 1: Milestones
        self.console.print("\n[bold]📋 Generating milestones...[/bold]")
        ms_result = await self.milestone_gen.generate(context)
        
        # Phase 2-4: Expand each milestone
        for ms_skel in ms_result.milestones:
            self.console.print(f"\n[bold]📦 Expanding: {ms_skel.name}[/bold]")
            
            milestone = Milestone(
                id=generate_id("milestone"),
                name=ms_skel.name, goal=ms_skel.goal,
                description=ms_skel.description, priority=ms_skel.priority,
            )
            
            ep_result = await self.epic_gen.generate(
                context, parent_context={"milestone": ms_skel.model_dump()},
            )
            
            for ep_skel in ep_result.epics:
                self.console.print(f"  [bold]🏗  Epic: {ep_skel.name}[/bold]")
                epic = Epic(
                    id=generate_id("epic"), name=ep_skel.name, goal=ep_skel.goal,
                    description=ep_skel.description, priority=ep_skel.priority,
                )
                
                st_result = await self.story_gen.generate(
                    context,
                    parent_context={"milestone": ms_skel.model_dump(), "epic": ep_skel.model_dump()},
                    sibling_context=[s.name for s in epic.stories],
                )
                
                for st_skel in st_result.stories:
                    self.console.print(f"    [dim]📝 Story: {st_skel.name}[/dim]")
                    story = Story(
                        id=generate_id("story"), name=st_skel.name,
                        description=st_skel.description, priority=st_skel.priority,
                        acceptance_criteria=st_skel.acceptance_criteria,
                    )
                    
                    task_result = await self.task_gen.generate(
                        context,
                        parent_context={
                            "milestone": ms_skel.model_dump(),
                            "epic": ep_skel.model_dump(),
                            "story": st_skel.model_dump(),
                        },
                    )
                    
                    story.tasks = task_result.tasks
                    epic.stories.append(story)
                    
                    roadmap.updated_at = datetime.now(timezone.utc)
                    await self.storage.save_roadmap(roadmap)
                
                milestone.epics.append(epic)
            roadmap.milestones.append(milestone)
        
        roadmap.updated_at = datetime.now(timezone.utc)
        await self.storage.save_roadmap(roadmap)
        
        counts = roadmap.total_items
        self.console.print(f"\n[bold green]✅ Roadmap complete![/bold green]")
        self.console.print(
            f"   {counts['milestones']} milestones, {counts['epics']} epics, "
            f"{counts['stories']} stories, {counts['tasks']} tasks"
        )
        self.console.print(f"   Estimated: {roadmap.total_hours} hours")
        return roadmap
```

---

### 6. `project_management/` — PM Tool Integrations

#### Base PM Client

```python
# project_management/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from ..items.roadmap import Roadmap

class ExportResult(BaseModel):
    success: bool
    target: str
    items_created: int
    errors: list[str] = []
    url: str | None = None

class BasePMClient(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def export(self, roadmap: Roadmap, **kwargs) -> ExportResult:
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        pass
```

#### CSV Client

```python
# project_management/csv.py
import csv
from pathlib import Path
from .base import BasePMClient, ExportResult
from ..items.roadmap import Roadmap

class CSVClient(BasePMClient):
    """Exports roadmap to CSV. Works with any PM tool that accepts CSV import."""
    
    @property
    def name(self) -> str:
        return "CSV"
    
    async def export(self, roadmap: Roadmap, output_path: str = None, **kwargs) -> ExportResult:
        path = Path(output_path or f"./{roadmap.project_name}/roadmap.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = self._flatten(roadmap)
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Type", "ID", "Name", "Description", "Parent_ID",
                "Priority", "Status", "Estimated_Hours",
                "Prerequisites", "Acceptance_Criteria",
                "Labels", "Claude_Code_Prompt"
            ])
            writer.writeheader()
            writer.writerows(rows)
        
        return ExportResult(success=True, target="CSV", items_created=len(rows), url=str(path.absolute()))
    
    async def validate_credentials(self) -> bool:
        return True
    
    def _flatten(self, roadmap: Roadmap) -> list[dict]:
        rows = []
        for ms in roadmap.milestones:
            rows.append(self._row("Milestone", ms, roadmap.id))
            for ep in ms.epics:
                rows.append(self._row("Epic", ep, ms.id, prerequisites=ep.prerequisites))
                for st in ep.stories:
                    rows.append(self._row("Story", st, ep.id, ac=st.acceptance_criteria))
                    for t in st.tasks:
                        rows.append(self._row("Task", t, st.id, prerequisites=t.prerequisites, ac=t.acceptance_criteria, prompt=t.claude_code_prompt))
        return rows
    
    def _row(self, type_name, item, parent_id, prerequisites=None, ac=None, prompt=""):
        return {
            "Type": type_name, "ID": item.id, "Name": item.name,
            "Description": item.description, "Parent_ID": parent_id,
            "Priority": item.priority.value, "Status": item.status.value,
            "Estimated_Hours": item.estimated_hours,
            "Prerequisites": ", ".join(prerequisites or []),
            "Acceptance_Criteria": " | ".join(ac or []),
            "Labels": ", ".join(item.labels),
            "Claude_Code_Prompt": prompt,
        }
```

#### Linear Client (stub for future implementation)

```python
# project_management/linear.py
import httpx
from .base import BasePMClient, ExportResult
from ..items.roadmap import Roadmap

class LinearClient(BasePMClient):
    """Exports roadmap to Linear via GraphQL API.
    
    Mapping: Milestones → Projects, Epics → Issues with 'epic' label,
    Stories → Issues linked to epic, Tasks → Sub-issues
    """
    
    GRAPHQL_URL = "https://api.linear.app/graphql"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": api_key, "Content-Type": "application/json"}
    
    @property
    def name(self) -> str:
        return "Linear"
    
    async def export(self, roadmap: Roadmap, team_id: str = None, **kwargs) -> ExportResult:
        raise NotImplementedError("Linear export coming soon")
    
    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.GRAPHQL_URL, headers=self.headers, json={"query": "{ viewer { id name } }"})
            return resp.status_code == 200
```

#### Jira Client (stub for future implementation)

```python
# project_management/jira.py
import httpx
from .base import BasePMClient, ExportResult
from ..items.roadmap import Roadmap

class JiraClient(BasePMClient):
    """Exports roadmap to Jira Cloud via REST API.
    
    Mapping: Milestones → Versions, Epics → Epics,
    Stories → Stories linked to Epic, Tasks → Sub-tasks
    """
    
    def __init__(self, domain: str, email: str, api_token: str):
        self.base_url = f"https://{domain}/rest/api/3"
        self.auth = (email, api_token)
    
    @property
    def name(self) -> str:
        return "Jira Cloud"
    
    async def export(self, roadmap: Roadmap, project_key: str = None, **kwargs) -> ExportResult:
        raise NotImplementedError("Jira export coming soon")
    
    async def validate_credentials(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/myself", auth=self.auth)
            return resp.status_code == 200
```

---

### 7. `storage/` — Local Persistence

```python
# storage/manager.py
from pathlib import Path
import yaml
from ..items.roadmap import Roadmap
from ..items.context import ProjectContext

class StorageManager:
    """Handles saving, loading, and resuming roadmaps on disk."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    async def save_roadmap(self, roadmap: Roadmap) -> Path:
        project_dir = self.base_path / self._slugify(roadmap.project_name)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        roadmap_path = project_dir / "roadmap.json"
        roadmap_path.write_text(roadmap.model_dump_json(indent=2))
        
        context_path = project_dir / "context.yaml"
        context_path.write_text(yaml.dump(roadmap.context.model_dump(), default_flow_style=False, sort_keys=False))
        
        return roadmap_path
    
    async def load_roadmap(self, path: Path) -> Roadmap:
        return Roadmap.model_validate_json(path.read_text())
    
    async def load_context(self, path: Path) -> ProjectContext:
        return ProjectContext(**yaml.safe_load(path.read_text()))
    
    def get_resume_point(self, roadmap: Roadmap) -> str | None:
        for m_idx, ms in enumerate(roadmap.milestones):
            for e_idx, ep in enumerate(ms.epics):
                if not ep.stories:
                    return f"Milestone {m_idx+1} ({ms.name}), Epic {e_idx+1} ({ep.name}) - no stories"
                for s_idx, st in enumerate(ep.stories):
                    if not st.tasks:
                        return f"Milestone {m_idx+1}, Epic {e_idx+1}, Story {s_idx+1} ({st.name}) - no tasks"
        return None
    
    @staticmethod
    def _slugify(name: str) -> str:
        return name.lower().replace(" ", "-").replace("_", "-")
```

---

### 8. Configuration

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_retries: int = 3
    linear_api_key: str | None = None
    jira_domain: str | None = None
    jira_email: str | None = None
    jira_api_token: str | None = None
    notion_api_key: str | None = None
    interactive: bool = True
    auto_save: bool = True
    output_dir: str = "./"
    
    class Config:
        env_file = ".env"
        env_prefix = "ARCANE_"
```

---

### 9. CLI Commands

```python
# cli.py
import asyncio
from pathlib import Path
import typer
from rich.console import Console

app = typer.Typer(name="arcane", help="🔮 AI-powered roadmap generator", no_args_is_help=True)
console = Console()

@app.command()
def new(
    name: str = typer.Option(None, "--name", "-n", help="Project name (skip first question)"),
    provider: str = typer.Option("anthropic", "--provider", "-p", help="AI provider"),
    output: str = typer.Option("./", "--output", "-o", help="Output directory"),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Skip review prompts"),
):
    """Create a new roadmap from scratch."""
    asyncio.run(_new(name, provider, output, not no_interactive))

@app.command()
def resume(path: str = typer.Argument(..., help="Path to project directory or roadmap.json")):
    """Resume generating an incomplete roadmap."""
    asyncio.run(_resume(path))

@app.command()
def export(
    path: str = typer.Argument(..., help="Path to roadmap.json"),
    to: str = typer.Option(..., "--to", "-t", help="Target: csv, linear, jira, notion"),
    workspace: str = typer.Option(None, "--workspace", "-w", help="Target workspace/project"),
):
    """Export roadmap to a project management tool."""
    asyncio.run(_export(path, to, workspace))

@app.command()
def view(
    path: str = typer.Argument(..., help="Path to roadmap.json"),
    format: str = typer.Option("tree", "--format", "-f", help="Display: tree, summary, json"),
):
    """View a generated roadmap."""
    asyncio.run(_view(path, format))

@app.command()
def config(show: bool = typer.Option(False, "--show", help="Show current config")):
    """Manage arcane configuration."""
    if show:
        from .config import Settings
        s = Settings()
        console.print(f"  Model: {s.model}")
        console.print(f"  API Key: {'✓ set' if s.anthropic_api_key else '✗ missing'}")
        console.print(f"  Linear: {'✓ set' if s.linear_api_key else '✗ not set'}")
        console.print(f"  Interactive: {s.interactive}")
```

---

## Dependencies (pyproject.toml additions)

Add `jinja2` to the existing dependencies:

```toml
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "anthropic>=0.40.0",
    "instructor>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.25.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.1.0",
    "python-slugify>=8.0.0",
    "python-ulid>=2.0.0",
]
```