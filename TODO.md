# Arcane Build Progress Tracker

This file tracks the complete build of Arcane following the step-by-step architecture in CLAUDE.md. Each task has complete implementation details so work can continue without needing follow-up prompts.

**Last Updated:** 2026-02-06
**Current Task:** T15 (CSV PM Client)
**Current Sprint:** S5 (Export & Polish)

---

## Task Index

Quick reference for all tasks. Use the ID (e.g., "implement T15") to reference a task.

| ID       | Sprint | Priority | Type        | Title                        | Description                                                |
| -------- | ------ | -------- | ----------- | ---------------------------- | ---------------------------------------------------------- |
| ~~T01~~  | ~~S1~~ | ~~P0~~   | ~~Setup~~   | ~~Bootstrap~~                | ~~Directory structure for new architecture~~ ✓             |
| ~~T02~~  | ~~S1~~ | ~~P0~~   | ~~Config~~  | ~~Configuration~~            | ~~Settings management with pydantic-settings~~ ✓           |
| ~~T03~~  | ~~S1~~ | ~~P0~~   | ~~Utils~~   | ~~Utilities~~                | ~~ID generation and Rich console utilities~~ ✓             |
| ~~T04~~  | ~~S1~~ | ~~P0~~   | ~~Models~~  | ~~Item Models~~              | ~~Pydantic models with hierarchy roll-ups~~ ✓              |
| ~~T05~~  | ~~S2~~ | ~~P0~~   | ~~Questions~~ | ~~Question Interface~~     | ~~Base question interface and basic questions~~ ✓          |
| ~~T06~~  | ~~S2~~ | ~~P0~~   | ~~Questions~~ | ~~Remaining Questions~~    | ~~Constraint, technical, and requirement questions~~ ✓     |
| ~~T07~~  | ~~S2~~ | ~~P0~~   | ~~Questions~~ | ~~Registry & Conductor~~   | ~~Question registry and interactive conductor~~ ✓          |
| ~~T08~~  | ~~S3~~ | ~~P0~~   | ~~Clients~~ | ~~AI Client Interface~~      | ~~BaseAIClient and Anthropic implementation~~ ✓            |
| ~~T09~~  | ~~S3~~ | ~~P0~~   | ~~Templates~~ | ~~Template Loader~~        | ~~Jinja2 prompt templates and loader~~ ✓                   |
| ~~T10~~  | ~~S3~~ | ~~P0~~   | ~~Generators~~ | ~~BaseGenerator~~         | ~~Base generator with retry logic and skeletons~~ ✓        |
| ~~T11~~  | ~~S3~~ | ~~P0~~   | ~~Generators~~ | ~~Individual Generators~~ | ~~Milestone, epic, story, and task generators~~ ✓          |
| ~~T12~~  | ~~S4~~ | ~~P0~~   | ~~Storage~~ | ~~Storage Manager~~          | ~~Save/load/resume detection for roadmaps~~ ✓              |
| ~~T13~~  | ~~S4~~ | ~~P0~~   | ~~Generators~~ | ~~Orchestrator~~          | ~~Roadmap orchestrator for hierarchical generation~~ ✓     |
| ~~T14~~  | ~~S4~~ | ~~P0~~   | ~~CLI~~     | ~~CLI Commands~~             | ~~Command-line interface with all commands~~ ✓             |
| T15      | S5     | P0       | Export      | CSV PM Client                | CSV export client for universal PM import                  |
| T16      | S5     | P1       | Export      | PM Client Stubs              | Stub implementations for Linear, Jira, Notion              |
| T17      | S5     | P0       | Integration | Integration Wiring           | Wire all components and verify CLI works                   |
| T18      | S5     | P0       | Testing     | E2E Integration Test         | End-to-end tests with mock AI client                       |
| T19      | S6     | P1       | Docs        | README                       | User-facing documentation and quick start                  |
| T20      | S6     | P0       | Testing     | Smoke Test Script            | Real API testing script for prompt validation              |
| T21      | S6     | P1       | Templates   | Prompt Tuning                | Refine prompts based on smoke test results                 |
| T22      | S6     | P2       | Maintenance | Repository Cleanup           | Remove legacy files from pre-refactor                      |
| T23      | S7     | P0       | UX          | Interactive Review           | Pause between phases for user review                       |
| T24      | S7     | P0       | UX          | Cost Visibility              | Show estimated cost before generation                      |
| T25      | S8     | P1       | Generators  | Resume Functionality         | Continue interrupted generations                           |
| T26      | S8     | P1       | Clients     | Rate Limiting                | Backoff/retry for API rate limits                          |
| T27      | S8     | P1       | Questions   | Back-Navigation              | Edit previous answers in question flow                     |
| T28      | S9     | P2       | Export      | Linear Integration           | Native export via GraphQL API                              |
| T29      | S9     | P2       | Export      | Jira Integration             | Native export via REST API                                 |
| T30      | S9     | P2       | Export      | Notion Integration           | Native export via Notion API                               |

---

## Sprint Roadmap

### Sprint 1 - Core Foundation (COMPLETE)

- [x] **T01** - Bootstrap directory structure ✓
- [x] **T02** - Configuration with pydantic-settings ✓
- [x] **T03** - ID generation and console utilities ✓
- [x] **T04** - Pydantic item models with hierarchy roll-ups ✓

### Sprint 2 - Discovery System (COMPLETE)

- [x] **T05** - Question interface and basic questions ✓
- [x] **T06** - Constraint, technical, and requirement questions ✓
- [x] **T07** - Question registry and interactive conductor ✓

### Sprint 3 - AI Integration (COMPLETE)

- [x] **T08** - AI client interface and Anthropic implementation ✓
- [x] **T09** - Jinja2 prompt templates and loader ✓
- [x] **T10** - BaseGenerator with retry logic and skeletons ✓
- [x] **T11** - Milestone, epic, story, and task generators ✓

### Sprint 4 - Storage & Orchestration (COMPLETE)

- [x] **T12** - Storage manager with save/load/resume ✓
- [x] **T13** - Roadmap orchestrator for hierarchical generation ✓
- [x] **T14** - CLI with new, resume, export, view, config commands ✓

### Sprint 5 - Export & Polish (CURRENT)

- [ ] **T15** - CSV export client for universal PM import
- [ ] **T16** - PM client stubs for Linear, Jira, Notion
- [ ] **T17** - Wire all components and verify CLI works
- [ ] **T18** - End-to-end integration tests with mock client

### Sprint 6 - Documentation & Testing

- [ ] **T19** - README and user documentation
- [ ] **T20** - Real API smoke test script
- [ ] **T21** - Prompt tuning based on smoke test results
- [ ] **T22** - Repository cleanup of legacy files

### Sprint 7 - UX Improvements

- [ ] **T23** - Interactive review mode between generation phases
- [ ] **T24** - Cost visibility before starting generation

### Sprint 8 - Post-MVP Features

- [ ] **T25** - Resume functionality for interrupted generations
- [ ] **T26** - Rate limiting with backoff/retry logic
- [ ] **T27** - Back-navigation to edit previous answers

### Sprint 9 - Native Integrations

- [ ] **T28** - Native Linear integration via GraphQL API
- [ ] **T29** - Native Jira Cloud integration via REST API
- [ ] **T30** - Native Notion integration via API

---

## Detailed Tasks

---

### T01: Bootstrap — Directory Structure ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S1 - Core Foundation                                       |
| Priority    | P0 - Critical                                              |
| Type        | Setup                                                      |
| Description | Create the new directory structure for refactored architecture |

**Commit:** `chore: restructure project for new architecture`

**What was done:**
- Deleted old architecture directories
- Created new directory structure:
  - `arcane/clients/`
  - `arcane/questions/`
  - `arcane/items/`
  - `arcane/templates/system/`
  - `arcane/templates/user/`
  - `arcane/generators/`
  - `arcane/project_management/`
  - `arcane/storage/`
  - `arcane/utils/`
- Created test directories:
  - `tests/test_clients/`
  - `tests/test_questions/`
  - `tests/test_items/`
  - `tests/test_generators/`
  - `tests/test_project_management/`
  - `tests/test_storage/`
- Updated `arcane/__init__.py` and `arcane/__main__.py`

---

### T02: Configuration ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S1 - Core Foundation                                       |
| Priority    | P0 - Critical                                              |
| Type        | Config                                                     |
| Description | Settings management using pydantic-settings with env/dotenv support |

**Commit:** `feat: add Settings config with env/dotenv support`

**Files created:**
- `arcane/config.py` - Settings class with pydantic-settings
- `.env.example` - Example environment variables
- `tests/test_config.py` - Configuration tests

**Settings fields:**
```python
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
```

**Config:** Uses `ARCANE_` prefix for env vars, loads from `.env` file.

---

### T03: Utility Modules ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S1 - Core Foundation                                       |
| Priority    | P0 - Critical                                              |
| Type        | Utils                                                      |
| Description | Shared utilities for ID generation (ULID) and Rich console helpers |

**Commit:** `feat: add ID generation and Rich console utilities`

**Files created:**
- `arcane/utils/ids.py` - `generate_id(prefix)` using ULID
- `arcane/utils/console.py` - Shared Console + helper functions
- `arcane/utils/__init__.py` - Exports
- `tests/test_utils.py` - Utility tests

---

### T04: Item Models ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S1 - Core Foundation                                       |
| Priority    | P0 - Critical                                              |
| Type        | Models                                                     |
| Description | Pydantic models for all roadmap entities with computed hour roll-ups |

**Commit:** `feat: add all Pydantic item models with hierarchy roll-ups`

**Files created in `arcane/items/`:**
- `base.py` - Priority, Status enums, BaseItem
- `task.py` - Task model (estimated_hours, acceptance_criteria, claude_code_prompt)
- `story.py` - Story model with computed estimated_hours
- `epic.py` - Epic model with computed estimated_hours
- `milestone.py` - Milestone model with computed estimated_hours
- `context.py` - ProjectContext (16 fields matching all question keys)
- `roadmap.py` - Roadmap with total_hours and total_items computed fields
- `__init__.py` - Exports all models

**Tests in `tests/test_items/`:**
- `test_base.py`
- `test_task.py`
- `test_hierarchy.py`
- `test_context.py`

---

### T05: Question Interface and Basic Questions ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S2 - Discovery System                                      |
| Priority    | P0 - Critical                                              |
| Type        | Questions                                                  |
| Description | Abstract question interface with validation/transform and basic questions |

**Commit:** `feat: add Question interface and basic question implementations`

**Files created:**
- `arcane/questions/base.py`:
  - QuestionType enum (TEXT, INT, CHOICE, MULTI, LIST, CONFIRM)
  - Question ABC with key, prompt, question_type, required, options, default, help_text
  - validate() and transform() methods
- `arcane/questions/basic.py`:
  - ProjectNameQuestion (key="project_name", TEXT)
  - VisionQuestion (key="vision", TEXT)
  - ProblemStatementQuestion (key="problem_statement", TEXT)
  - TargetUsersQuestion (key="target_users", LIST)

**Tests:**
- `tests/test_questions/test_base.py`
- `tests/test_questions/test_basic.py`

---

### T06: Remaining Questions ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S2 - Discovery System                                      |
| Priority    | P0 - Critical                                              |
| Type        | Questions                                                  |
| Description | Complete set of discovery questions for constraints, technical, requirements |

**Commit:** `feat: add constraint, technical, and requirement questions`

**Files created:**
- `arcane/questions/constraints.py`:
  - TimelineQuestion (CHOICE)
  - TeamSizeQuestion (INT, validates 1-100)
  - DeveloperExperienceQuestion (CHOICE)
  - BudgetQuestion (CHOICE)
- `arcane/questions/technical.py`:
  - TechStackQuestion (LIST, optional)
  - InfrastructureQuestion (CHOICE)
  - ExistingCodebaseQuestion (CONFIRM)
- `arcane/questions/requirements.py`:
  - MustHaveQuestion (LIST, required)
  - NiceToHaveQuestion (LIST, optional)
  - OutOfScopeQuestion (LIST, optional)
  - SimilarProductsQuestion (LIST, optional)
  - NotesQuestion (TEXT, optional)

**Tests:**
- `tests/test_questions/test_all_questions.py`

---

### T07: Question Registry and Conductor ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S2 - Discovery System                                      |
| Priority    | P0 - Critical                                              |
| Type        | Questions                                                  |
| Description | Registry for organizing questions and conductor for interactive flow |

**Commit:** `feat: add QuestionRegistry and interactive QuestionConductor`

**Files created:**
- `arcane/questions/registry.py`:
  - QuestionRegistry class with CATEGORIES dict (4 categories, 16 questions)
  - get_all_questions() returns (category, question) tuples
  - get_category(name) returns questions for one category
- `arcane/questions/conductor.py`:
  - QuestionConductor class
  - async run() method - runs interactive question flow
  - _ask() method - handles individual question with Rich prompts
  - Returns ProjectContext from collected answers
- `arcane/questions/__init__.py` - Exports

**Tests:**
- `tests/test_questions/test_registry.py`

---

### T08: AI Client Interface ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S3 - AI Integration                                        |
| Priority    | P0 - Critical                                              |
| Type        | Clients                                                    |
| Description | Abstract AI client interface with Anthropic implementation using Instructor |

**Commit:** `feat: add BaseAIClient interface and AnthropicClient implementation`

**Files created:**
- `arcane/clients/base.py`:
  - AIClientError exception
  - BaseAIClient ABC with:
    - async generate(system_prompt, user_prompt, response_model, max_tokens, temperature)
    - async validate_connection()
    - provider_name property
    - model_name property
- `arcane/clients/anthropic.py`:
  - AnthropicClient using Anthropic SDK + Instructor
  - Creates AsyncAnthropic and instructor.from_anthropic()
  - Implements all BaseAIClient methods
- `arcane/clients/__init__.py`:
  - Exports + create_client(provider, **kwargs) factory

**Tests:**
- `tests/test_clients/test_base.py` (16 tests)

---

### T09: Template Loader and Templates ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S3 - AI Integration                                        |
| Priority    | P0 - Critical                                              |
| Type        | Templates                                                  |
| Description | Jinja2 template system for AI prompts with system and user templates |

**Commit:** `feat: add Jinja2 prompt templates and TemplateLoader`

**Files created:**
- `arcane/templates/loader.py`:
  - TemplateLoader class with Jinja2 Environment
  - render_system(item_type) - loads system/{item_type}.j2
  - render_user(template_name, project_context, parent_context, sibling_context, errors)
- `arcane/templates/__init__.py` - Exports TemplateLoader
- `arcane/templates/system/milestone.j2` - System prompt for milestones
- `arcane/templates/system/epic.j2` - System prompt for epics
- `arcane/templates/system/story.j2` - System prompt for stories
- `arcane/templates/system/task.j2` - System prompt for tasks
- `arcane/templates/user/generate.j2` - Main user prompt with context injection
- `arcane/templates/user/refine.j2` - Retry prompt with error list

**Tests:**
- `tests/test_templates.py` (10 tests)

---

### T10: Generator Skeletons and BaseGenerator ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S3 - AI Integration                                        |
| Priority    | P0 - Critical                                              |
| Type        | Generators                                                 |
| Description | Base generator class with retry logic and intermediate skeleton models |

**Commit:** `feat: add BaseGenerator with retry logic and skeleton models`

**Files created:**
- `arcane/generators/skeletons.py`:
  - MilestoneSkeleton, MilestoneSkeletonList
  - EpicSkeleton, EpicSkeletonList
  - StorySkeleton, StorySkeletonList
- `arcane/generators/base.py`:
  - GenerationError exception
  - BaseGenerator ABC with:
    - __init__(client, console, templates, max_retries=3)
    - item_type property (abstract)
    - get_response_model() (abstract)
    - async generate() with retry loop
    - _validate() hook for subclass validation
- `arcane/generators/__init__.py` - Exports

**Tests:**
- `tests/test_generators/test_skeletons.py` (11 tests)
- `tests/test_generators/test_base.py` (11 tests)

---

### T11: Individual Generators ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S3 - AI Integration                                        |
| Priority    | P0 - Critical                                              |
| Type        | Generators                                                 |
| Description | Concrete generator implementations for each roadmap item level |

**Commit:** `feat: add milestone, epic, story, and task generators`

**Files created:**
- `arcane/generators/milestone.py` - MilestoneGenerator
- `arcane/generators/epic.py` - EpicGenerator
- `arcane/generators/story.py` - StoryGenerator
- `arcane/generators/task.py` - TaskGenerator with TaskList model
- Updated `arcane/generators/__init__.py` to export all generators

**Tests:**
- `tests/test_generators/test_generators.py` (19 tests)

---

### T12: Storage Manager ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S4 - Storage & Orchestration                               |
| Priority    | P0 - Critical                                              |
| Type        | Storage                                                    |
| Description | Persistence layer for saving/loading roadmaps with resume detection |

**Commit:** `feat: add StorageManager with save/load/resume support`

**Files created:**
- `arcane/storage/manager.py`:
  - StorageManager class with save_roadmap, load_roadmap, load_context, get_resume_point
  - _slugify static method
- `arcane/storage/__init__.py` - Exports StorageManager

**Tests:**
- `tests/test_storage/test_manager.py` (14 tests)

---

### T13: Roadmap Orchestrator ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S4 - Storage & Orchestration                               |
| Priority    | P0 - Critical                                              |
| Type        | Generators                                                 |
| Description | Top-level orchestrator for hierarchical generation with incremental saves |

**Commit:** `feat: add RoadmapOrchestrator for hierarchical generation`

**Files created:**
- `arcane/generators/orchestrator.py`:
  - RoadmapOrchestrator class
  - Coordinates milestones → epics → stories → tasks generation
  - Saves incrementally after each story
  - Prints summary with counts and hours
- Updated `arcane/generators/__init__.py` to export RoadmapOrchestrator

**Tests:**
- `tests/test_generators/test_orchestrator.py` (9 tests)

---

### T14: CLI Commands ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S4 - Storage & Orchestration                               |
| Priority    | P0 - Critical                                              |
| Type        | CLI                                                        |
| Description | Typer-based command-line interface with new, resume, export, view, config |

**Commit:** `feat: add CLI with new, resume, export, view, and config commands`

**Files created/modified:**
- `arcane/cli.py` - Full CLI implementation with all commands
- `arcane/config.py` - Added `extra="ignore"` to handle extra env vars

**Commands implemented:**
- `new` - Create a new roadmap with interactive discovery
- `resume` - Resume incomplete roadmaps (stub for now)
- `export` - Export to PM tools (stubs for csv, linear, jira, notion)
- `view` - Display roadmaps as tree, summary, or JSON
- `config` - Show/manage configuration

**Manual verification completed:**
- `python -m arcane --help` ✓
- `python -m arcane config --show` ✓
- `python -m arcane view /tmp/test.json` ✓ (all formats work)

---

### T15: CSV PM Client

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S5 - Export & Polish                                       |
| Priority    | P0 - Critical                                              |
| Type        | Export                                                     |
| Description | CSV export client for universal import into any PM tool that accepts CSV |

**Commit message:** `feat: add BasePMClient interface and CSV exporter`

**Create `arcane/project_management/base.py`:**
```python
class ExportResult(BaseModel):
    success: bool
    target: str
    items_created: int
    errors: list[str] = []
    url: str | None = None

class BasePMClient(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    async def export(self, roadmap: Roadmap, **kwargs) -> ExportResult: pass

    @abstractmethod
    async def validate_credentials(self) -> bool: pass
```

**Create `arcane/project_management/csv.py`:**
```python
class CSVClient(BasePMClient):
    @property
    def name(self) -> str:
        return "CSV"

    async def validate_credentials(self) -> bool:
        return True

    async def export(self, roadmap: Roadmap, output_path: str = None, **kwargs) -> ExportResult:
        # Flatten hierarchy, write CSV with fieldnames:
        # Type, ID, Name, Description, Parent_ID, Priority, Status,
        # Estimated_Hours, Prerequisites, Acceptance_Criteria, Labels, Claude_Code_Prompt

    def _flatten(self, roadmap: Roadmap) -> list[dict]:
        # Walk milestones → epics → stories → tasks
```

**Tests in `tests/test_project_management/test_csv.py`:**
- test_csv_export (verify file exists, row count)
- test_csv_hierarchy (verify Parent_ID correctness)
- test_csv_task_has_prompt
- test_export_result

---

### T16: PM Client Stubs

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S5 - Export & Polish                                       |
| Priority    | P1 - High                                                  |
| Type        | Export                                                     |
| Description | Stub implementations for Linear, Jira, Notion that raise NotImplementedError |

**Commit message:** `feat: add Linear, Jira, and Notion PM client stubs`

**Create stubs with validate_credentials() working and export() raising NotImplementedError:**
- `arcane/project_management/linear.py` - LinearClient
- `arcane/project_management/jira.py` - JiraClient
- `arcane/project_management/notion.py` - NotionClient

**Tests in `tests/test_project_management/test_stubs.py`:**
- Test instantiation
- Test .name properties
- Test export() raises NotImplementedError

---

### T17: Integration Wiring

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S5 - Export & Polish                                       |
| Priority    | P0 - Critical                                              |
| Type        | Integration                                                |
| Description | Wire all components together, fix imports, verify CLI works end-to-end |

**Commit message:** `feat: wire all components together and verify CLI works`

**Tasks:**
- Review and fix all imports in `cli.py`
- Verify `__main__.py` works
- Verify pyproject.toml entry point
- Run `pip install -e .`
- Test `arcane --help` and `arcane config --show`
- Fix any circular imports

---

### T18: End-to-End Integration Test

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S5 - Export & Polish                                       |
| Priority    | P0 - Critical                                              |
| Type        | Testing                                                    |
| Description | Full integration test using mock AI client to verify entire pipeline |

**Commit message:** `test: add end-to-end integration test with mock AI client`

**Create `tests/test_integration.py`:**
- MockAIClient that returns appropriate fixtures per response_model
- test_full_pipeline: generate roadmap, verify counts, verify IDs unique, verify saved to disk
- test_csv_export_from_generated
- test_view_tree_no_crash

---

### T19: README and Documentation

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S6 - Documentation & Testing                               |
| Priority    | P1 - High                                                  |
| Type        | Docs                                                       |
| Description | User-facing README with quick start, CLI commands, and project overview |

**Commit message:** `docs: update README and TODO for new architecture`

Rewrite README.md with:
- What It Does
- Quick Start
- CLI Commands
- How It Works
- Project Structure
- Configuration
- Export Targets
- Development

---

### T20: Real API Smoke Test Script

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S6 - Documentation & Testing                               |
| Priority    | P0 - Critical                                              |
| Type        | Testing                                                    |
| Description | Script to test full generation with real Anthropic API for prompt validation |

**Commit message:** `feat: add manual smoke test script for real API testing`

**Create `scripts/smoke_test.py`:**
- Loads Settings
- Creates real AnthropicClient
- Uses hardcoded ProjectContext
- Runs full generation
- Exports to CSV
- Prints results

Add `smoke-test-output/` to `.gitignore`.

---

### T21: Prompt Tuning

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S6 - Documentation & Testing                               |
| Priority    | P1 - High                                                  |
| Type        | Templates                                                  |
| Description | Refine Jinja2 prompt templates based on real API output quality |

**Commit message:** `refine: tune prompt templates based on smoke test results`

After running real API smoke test:
- Review output quality
- Tune Jinja2 templates
- Common fixes: specificity, hour estimates, claude_code_prompt quality, duplication prevention

---

### T22: Repository Cleanup

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S6 - Documentation & Testing                               |
| Priority    | P2 - Medium                                                |
| Type        | Maintenance                                                |
| Description | Remove legacy files from pre-refactor architecture |

**Commit message:** `chore: clean up legacy files from pre-refactor architecture`

**Files to review and potentially delete:**

1. **Old script files in `scripts/`:**
   - `scripts/run.sh` - Check if still relevant
   - `scripts/run-simple.sh` - Check if still relevant
   - `scripts/run-comprehensive.sh` - Check if still relevant
   - `scripts/run-solo.sh` - Check if still relevant

2. **Documentation files to review:**
   - `BUILD_STEPS.md` - Was used during refactor, may no longer be needed
   - `telchar.txt` - Unknown purpose, likely leftover

3. **Old question files that were deleted but may have leftover imports:**
   - Verify no references to deleted files in `arcane/questions/budget/`
   - Verify no references to deleted files in `arcane/questions/integration/`
   - Verify no references to deleted files in `arcane/questions/success/`

4. **Other cleanup tasks:**
   - Review `.gitignore` for completeness
   - Remove any `__pycache__` directories
   - Ensure all test files have proper `__init__.py`
   - Check for any orphaned imports in existing files

**Verification steps:**
```bash
# Find any Python files with import errors
venv/bin/python -m py_compile arcane/**/*.py

# Run full test suite to catch broken imports
venv/bin/python -m pytest tests/ -v --override-ini="addopts="

# Check for files not tracked by git that might be leftover
git status --porcelain
```

---

### T23: Interactive Review Mode

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S7 - UX Improvements                                       |
| Priority    | P0 - Critical                                              |
| Type        | UX                                                         |
| Description | Pause generation between phases for user review and approval |

**Commit message:** `feat: add interactive review mode with pause between generation phases`

**Implementation:**
- Modify `RoadmapOrchestrator.generate()` to check `self.interactive` flag
- After generating milestones, display them and prompt for approval
- After generating each epic's stories, display and prompt
- User can approve, request regeneration, or edit items
- Use Rich prompts for user input

**User experience:**
```
📋 Generated 3 milestones:
  1. MVP - Core features for initial launch
  2. v1.0 - Full feature release
  3. Scale - Performance and growth features

[A]pprove / [R]egenerate / [E]dit? >
```

---

### T24: Cost Visibility

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S7 - UX Improvements                                       |
| Priority    | P0 - Critical                                              |
| Type        | UX                                                         |
| Description | Show estimated token usage and cost before starting generation |

**Commit message:** `feat: add cost estimation before generation starts`

**Implementation:**
- Estimate number of API calls based on typical generation (2-4 milestones, 2-3 epics each, etc.)
- Calculate approximate token count per call
- Show estimated cost using Anthropic pricing
- Prompt user to confirm before proceeding

**User experience:**
```
📊 Estimated generation:
   ~15 API calls
   ~50,000 tokens
   ~$0.75 estimated cost

Proceed with generation? [Y/n] >
```

---

### T25: Resume Functionality

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S8 - Post-MVP Features                                     |
| Priority    | P1 - High                                                  |
| Type        | Generators                                                 |
| Description | Actually continue generation from where it stopped, not just detect |

**Commit message:** `feat: implement actual resume functionality for interrupted generations`

**Implementation:**
- Extend `RoadmapOrchestrator` with `resume(roadmap)` method
- Use `StorageManager.get_resume_point()` to find where to continue
- Skip already-generated items
- Continue from the incomplete item
- Maintain context from existing items

---

### T26: Rate Limiting

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S8 - Post-MVP Features                                     |
| Priority    | P1 - High                                                  |
| Type        | Clients                                                    |
| Description | Handle Anthropic API rate limits with exponential backoff and retry |

**Commit message:** `feat: add rate limiting with exponential backoff`

**Implementation:**
- Detect rate limit errors from Anthropic API
- Implement exponential backoff (1s, 2s, 4s, 8s, etc.)
- Add configurable max wait time
- Log rate limit events for visibility
- Consider adding request throttling proactively

---

### T27: Question Back-Navigation

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S8 - Post-MVP Features                                     |
| Priority    | P1 - High                                                  |
| Type        | Questions                                                  |
| Description | Allow users to go back and edit previous answers during discovery |

**Commit message:** `feat: add back-navigation in question flow`

**Implementation:**
- Store answer history in `QuestionConductor`
- Add "back" option to each question prompt
- Allow editing of previous answers
- Re-validate edited answers
- Show summary of all answers before finalizing

---

### T28: Linear Integration

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S9 - Native Integrations                                   |
| Priority    | P2 - Medium                                                |
| Type        | Export                                                     |
| Description | Native export to Linear using GraphQL API |

**Commit message:** `feat: add native Linear integration`

**Mapping:**
- Milestones → Projects
- Epics → Issues with 'epic' label
- Stories → Issues linked to epic
- Tasks → Sub-issues

---

### T29: Jira Integration

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S9 - Native Integrations                                   |
| Priority    | P2 - Medium                                                |
| Type        | Export                                                     |
| Description | Native export to Jira Cloud using REST API |

**Commit message:** `feat: add native Jira Cloud integration`

**Mapping:**
- Milestones → Versions
- Epics → Epics
- Stories → Stories linked to Epic
- Tasks → Sub-tasks

---

### T30: Notion Integration

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S9 - Native Integrations                                   |
| Priority    | P2 - Medium                                                |
| Type        | Export                                                     |
| Description | Native export to Notion using API |

**Commit message:** `feat: add native Notion integration`

**Mapping:**
- Create database with roadmap items
- Use nested pages for hierarchy
- Include all metadata as properties

---

## Quick Reference

### Priority Levels
- **P0 - Critical:** Must be done, blocks other work
- **P1 - High:** Important, should be done soon
- **P2 - Medium:** Nice to have, can wait

### Task Types
- **Setup:** Project structure and bootstrapping
- **Config:** Configuration and settings
- **Utils:** Shared utilities
- **Models:** Pydantic data models
- **Questions:** Discovery question system
- **Clients:** AI provider clients
- **Templates:** Jinja2 prompt templates
- **Generators:** Roadmap generation logic
- **Storage:** Persistence layer
- **CLI:** Command-line interface
- **Export:** PM tool exporters
- **Integration:** Wiring components together
- **Testing:** Tests and verification
- **Docs:** Documentation
- **Maintenance:** Cleanup and housekeeping
- **UX:** User experience improvements

### Running Tests
```bash
venv/bin/python -m pytest tests/ -v --override-ini="addopts="
```

### Committing Changes
```bash
git add <files>
git commit -m "$(cat <<'EOF'
<commit message>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

### Project Structure
```
arcane/
├── clients/            # AI provider abstraction
├── config.py           # Settings with pydantic-settings
├── generators/         # Generation orchestration
├── items/              # Pydantic data models
├── project_management/ # PM tool exporters
├── questions/          # Discovery question system
├── storage/            # Save/load/resume
├── templates/          # Jinja2 prompt templates
└── utils/              # ID generation, console helpers
```
