# Arcane Build Progress Tracker

This file tracks the complete build of Arcane following the step-by-step architecture in CLAUDE.md. Each step has complete implementation details so work can continue without needing follow-up prompts.

**Last Updated:** 2026-02-06
**Current Step:** Step 14 (CSV PM Client)

---

## Progress Summary

| Step | Status | Description |
|------|--------|-------------|
| 0 | ✅ DONE | Bootstrap - Directory structure |
| 1 | ✅ DONE | Configuration - `config.py` |
| 2 | ✅ DONE | Utilities - `utils/ids.py`, `utils/console.py` |
| 3 | ✅ DONE | Item Models - `items/*.py` |
| 4 | ✅ DONE | Question Interface - `questions/base.py`, `basic.py` |
| 5 | ✅ DONE | Remaining Questions - `constraints.py`, `technical.py`, `requirements.py` |
| 6 | ✅ DONE | Question Registry & Conductor |
| 7 | ✅ DONE | AI Client Interface - `clients/*.py` |
| 8 | ✅ DONE | Template Loader & Templates |
| 9 | ✅ DONE | BaseGenerator & Skeletons |
| 10 | ✅ DONE | Individual Generators |
| 11 | ✅ DONE | Storage Manager |
| 12 | ✅ DONE | Roadmap Orchestrator |
| 13 | ✅ DONE | CLI Commands |
| 14 | ⬜ TODO | CSV PM Client |
| 15 | ⬜ TODO | PM Client Stubs (Linear, Jira, Notion) |
| 16 | ⬜ TODO | Integration Wiring |
| 17 | ⬜ TODO | End-to-End Integration Test |
| 18 | ⬜ TODO | README & Documentation |
| 19 | ⬜ TODO | Real API Smoke Test Script |
| 20 | ⬜ TODO | Prompt Tuning |
| 21 | ⬜ TODO | Repository Cleanup |

---

## Detailed Steps

---

### Step 0: Bootstrap — Directory Structure ✅ DONE

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

### Step 1: Configuration — `config.py` ✅ DONE

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

### Step 2: Utility Modules ✅ DONE

**Commit:** `feat: add ID generation and Rich console utilities`

**Files created:**
- `arcane/utils/ids.py` - `generate_id(prefix)` using ULID
- `arcane/utils/console.py` - Shared Console + helper functions (success, error, warning, info, header)
- `arcane/utils/__init__.py` - Exports
- `tests/test_utils.py` - Utility tests

---

### Step 3: Item Models ✅ DONE

**Commit:** `feat: add all Pydantic item models with hierarchy roll-ups`

**Files created in `arcane/items/`:**
- `base.py` - Priority, Status enums, BaseItem
- `task.py` - Task model (estimated_hours, acceptance_criteria, implementation_notes, claude_code_prompt)
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

### Step 4: Question Interface and Basic Questions ✅ DONE

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

### Step 5: Remaining Questions ✅ DONE

**Commit:** `feat: add constraint, technical, and requirement questions`

**Files created:**
- `arcane/questions/constraints.py`:
  - TimelineQuestion (CHOICE: "1 month MVP", "3 months", "6 months", "1 year", "custom")
  - TeamSizeQuestion (INT, default="1", validates 1-100)
  - DeveloperExperienceQuestion (CHOICE: "junior", "mid-level", "senior", "mixed")
  - BudgetQuestion (CHOICE: "minimal (free tier everything)", "moderate", "flexible")
- `arcane/questions/technical.py`:
  - TechStackQuestion (LIST, optional)
  - InfrastructureQuestion (CHOICE: "AWS", "GCP", "Azure", "Serverless", "Self-hosted", "No preference")
  - ExistingCodebaseQuestion (CONFIRM, default="n")
- `arcane/questions/requirements.py`:
  - MustHaveQuestion (LIST, required)
  - NiceToHaveQuestion (LIST, optional)
  - OutOfScopeQuestion (LIST, optional)
  - SimilarProductsQuestion (LIST, optional)
  - NotesQuestion (TEXT, optional)

**Tests:**
- `tests/test_questions/test_all_questions.py`

---

### Step 6: Question Registry and Conductor ✅ DONE

**Commit:** `feat: add QuestionRegistry and interactive QuestionConductor`

**Files created:**
- `arcane/questions/registry.py`:
  - QuestionRegistry class with CATEGORIES dict (4 categories, 16 total questions)
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

### Step 7: AI Client Interface ✅ DONE

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

### Step 8: Template Loader and Templates ✅ DONE

**Commit:** `feat: add Jinja2 prompt templates and TemplateLoader`

**Files created:**
- `arcane/templates/loader.py`:
  - TemplateLoader class with Jinja2 Environment
  - render_system(item_type) - loads system/{item_type}.j2
  - render_user(template_name, project_context, parent_context, sibling_context, additional_guidance, errors)
- `arcane/templates/__init__.py` - Exports TemplateLoader
- `arcane/templates/system/milestone.j2` - System prompt for milestones
- `arcane/templates/system/epic.j2` - System prompt for epics
- `arcane/templates/system/story.j2` - System prompt for stories
- `arcane/templates/system/task.j2` - System prompt for tasks (includes claude_code_prompt instructions)
- `arcane/templates/user/generate.j2` - Main user prompt with context injection
- `arcane/templates/user/refine.j2` - Retry prompt with error list

**Tests:**
- `tests/test_templates.py` (10 tests)

---

### Step 9: Generator Skeletons and BaseGenerator ✅ DONE

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

### Step 10: Individual Generators ✅ DONE

**Commit:** `feat: add milestone, epic, story, and task generators`

**Files created:**
- `arcane/generators/milestone.py`:
  - MilestoneGenerator(BaseGenerator)
  - item_type = "milestone"
  - get_response_model() = MilestoneSkeletonList
- `arcane/generators/epic.py`:
  - EpicGenerator(BaseGenerator)
  - item_type = "epic"
  - get_response_model() = EpicSkeletonList
- `arcane/generators/story.py`:
  - StoryGenerator(BaseGenerator)
  - item_type = "story"
  - get_response_model() = StorySkeletonList
- `arcane/generators/task.py`:
  - TaskList(BaseModel) with tasks: list[Task]
  - TaskGenerator(BaseGenerator)
  - item_type = "task"
  - get_response_model() = TaskList
- Updated `arcane/generators/__init__.py` to export all generators

**Tests:**
- `tests/test_generators/test_generators.py` (19 tests)

---

### Step 11: Storage Manager ✅ DONE

**Commit:** `feat: add StorageManager with save/load/resume support`

**Files created:**
- `arcane/storage/manager.py`:
  - StorageManager class with save_roadmap, load_roadmap, load_context, get_resume_point
  - _slugify static method
- `arcane/storage/__init__.py` - Exports StorageManager

**Tests:**
- `tests/test_storage/test_manager.py` (14 tests)

---

### Step 12: Roadmap Orchestrator ✅ DONE

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

### Step 13: CLI Commands ✅ DONE

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

### Step 14: CSV PM Client ⬜ TODO

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

### Step 15: PM Client Stubs ⬜ TODO

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

### Step 16: Integration Wiring ⬜ TODO

**Commit message:** `feat: wire all components together and verify CLI works`

**Tasks:**
- Review and fix all imports in `cli.py`
- Verify `__main__.py` works
- Verify pyproject.toml entry point
- Run `pip install -e .`
- Test `arcane --help` and `arcane config --show`
- Fix any circular imports

---

### Step 17: End-to-End Integration Test ⬜ TODO

**Commit message:** `test: add end-to-end integration test with mock AI client`

**Create `tests/test_integration.py`:**
- MockAIClient that returns appropriate fixtures per response_model
- test_full_pipeline: generate roadmap, verify counts, verify IDs unique, verify saved to disk
- test_csv_export_from_generated
- test_view_tree_no_crash

---

### Step 18: README and Documentation ⬜ TODO

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

### Step 19: Real API Smoke Test Script ⬜ TODO

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

### Step 20: Prompt Tuning ⬜ TODO

**Commit message:** `refine: tune prompt templates based on smoke test results`

After running real API smoke test:
- Review output quality
- Tune Jinja2 templates
- Common fixes: specificity, hour estimates, claude_code_prompt quality, duplication prevention

---

### Step 21: Repository Cleanup ⬜ TODO

**Commit message:** `chore: clean up legacy files from pre-refactor architecture`

**Purpose:** Remove old files that were part of the previous architecture before the major refactor.

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

**After cleanup:**
- Run `git status` to verify changes
- Run tests to ensure nothing broke
- Commit with cleanup message

---

## Future Improvements

Items identified during development that should be addressed. Organized by priority.

### High Priority (Before MVP Complete)

| Item | Description | Status |
|------|-------------|--------|
| Interactive Review Mode | Pause between milestones/epics/stories for user review and approval | ⬜ TODO |
| Cost Visibility | Show estimated token usage/cost before starting generation | ⬜ TODO |

### Medium Priority (Post-MVP)

| Item | Description | Status |
|------|-------------|--------|
| Resume Functionality | Actually continue generation from where it stopped (not just detect) | ⬜ TODO |
| Rate Limiting | Add backoff/retry logic for Anthropic API rate limits | ⬜ TODO |
| Question Back-Navigation | Allow users to go back and edit previous answers | ⬜ TODO |

### Lower Priority (Future Releases)

| Item | Description | Status |
|------|-------------|--------|
| Linear Integration | Native export to Linear (GraphQL API) | ⬜ TODO |
| Jira Integration | Native export to Jira Cloud (REST API) | ⬜ TODO |
| Notion Integration | Native export to Notion (API) | ⬜ TODO |

---

## Quick Reference

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
├── clients/       # AI provider abstraction
├── config.py      # Settings with pydantic-settings
├── generators/    # Generation orchestration
├── items/         # Pydantic data models
├── project_management/  # PM tool exporters
├── questions/     # Discovery question system
├── storage/       # Save/load/resume
├── templates/     # Jinja2 prompt templates
└── utils/         # ID generation, console helpers
```
