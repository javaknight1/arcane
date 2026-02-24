# Arcane Build Progress Tracker

This file tracks the complete build of Arcane following the step-by-step architecture in CLAUDE.md. Each task has complete implementation details so work can continue without needing follow-up prompts.

**Last Updated:** 2026-02-23
**Current Task:** T52 (Status Tracking) — Progress dashboards and status sync
**Current Sprint:** S17 (AI-Native PM Features) — In Progress
**Next Milestone:** S17 completion — AI-native PM features

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
| ~~T15~~  | ~~S5~~ | ~~P0~~   | ~~Export~~  | ~~CSV PM Client~~            | ~~CSV export client for universal PM import~~ ✓            |
| ~~T16~~  | ~~S5~~ | ~~P1~~   | ~~Export~~  | ~~PM Client Stubs~~          | ~~Stub implementations for Linear, Jira, Notion~~ ✓        |
| ~~T17~~  | ~~S5~~ | ~~P0~~   | ~~Integration~~ | ~~Integration Wiring~~   | ~~Wire all components and verify CLI works~~ ✓             |
| ~~T18~~  | ~~S5~~ | ~~P0~~   | ~~Testing~~ | ~~E2E Integration Test~~     | ~~End-to-end tests with mock AI client~~ ✓                 |
| ~~T19~~  | ~~S6~~ | ~~P1~~   | ~~Docs~~    | ~~README~~                   | ~~User-facing documentation and quick start~~ ✓            |
| ~~T20~~  | ~~S6~~ | ~~P0~~   | ~~Testing~~ | ~~Smoke Test Script~~        | ~~Real API testing script for prompt validation~~ ✓        |
| ~~T21~~  | ~~S6~~ | ~~P1~~   | ~~Templates~~ | ~~Prompt Tuning~~          | ~~Refine prompts based on smoke test results~~ ✓           |
| ~~T22~~  | ~~S6~~ | ~~P2~~   | ~~Maintenance~~ | ~~Repository Cleanup~~   | ~~Remove legacy files from pre-refactor~~ ✓                |
| ~~T23~~  | ~~S7~~ | ~~P0~~   | ~~UX~~      | ~~Interactive Review~~       | ~~Pause between phases for user review~~ ✓                 |
| ~~T24~~  | ~~S7~~ | ~~P0~~   | ~~UX~~      | ~~Cost Visibility~~          | ~~Show estimated cost before generation~~ ✓                |
| ~~T25~~  | ~~S8~~ | ~~P1~~   | ~~Generators~~ | ~~Resume Functionality~~  | ~~Continue interrupted generations~~ ✓                     |
| ~~T26~~  | ~~S8~~ | ~~P1~~   | ~~Clients~~ | ~~Rate Limiting~~            | ~~Backoff/retry for API rate limits~~ ✓                    |
| ~~T27~~  | ~~S8~~ | ~~P1~~   | ~~Questions~~ | ~~Back-Navigation~~        | ~~Edit previous answers in question flow~~ ✓               |
| ~~T34~~  | ~~S10~~ | ~~P1~~  | ~~CLI~~     | ~~Model Selection UX~~       | ~~Replace `--provider` with `--model` chooser~~ ✓          |
| ~~T35~~  | ~~S11~~ | ~~P1~~  | ~~UX~~      | ~~Export Progress Bar~~      | ~~Progress bar with percent and items remaining during export~~ ✓ |
| ~~T36~~  | ~~S11~~ | ~~P1~~  | ~~UX~~      | ~~Generation Progress Bar~~  | ~~Progress bar with percent and items remaining during new/resume~~ ✓ |
| ~~T28~~  | ~~S9~~  | ~~P2~~  | ~~Export~~  | ~~Linear Integration~~       | ~~Native export via GraphQL API~~ ✓                        |
| ~~T29~~  | ~~S9~~ | ~~P2~~   | ~~Export~~  | ~~Jira Integration~~         | ~~Native export via REST API~~ ✓                           |
| ~~T30~~  | ~~S9~~  | ~~P2~~  | ~~Export~~  | ~~Notion Integration~~       | ~~Native export via Notion API~~ ✓                         |
| T31      | S6     | P1       | Scripts     | Update Example Scripts       | Create new scripts that use `arcane new` CLI               |
| ~~T32~~  | ~~S6~~ | ~~P1~~   | ~~Scripts~~ | ~~Create Example Idea File~~ | ~~Create telchar.txt example for testing~~ ✓               |
| ~~T33~~  | ~~S9~~ | ~~P1~~   | ~~Export~~  | ~~Documentation Page Builders~~ | ~~Shared doc page builders from ProjectContext~~ ✓         |
|          |        |          |             |                              |                                                            |
| **SaaS** |        |          |             | **Arcane Web — AI-Native PM Tool** |                                                       |
| ~~T37~~  | ~~S12~~ | ~~P0~~  | ~~Refactor~~ | ~~Extract arcane-core~~     | ~~Shared library for models, generators, clients, templates~~ ✓ |
| ~~T38~~  | ~~S12~~ | ~~P0~~  | ~~Refactor~~ | ~~Thin CLI Wrapper~~        | ~~Refactor CLI to import from arcane-core~~ ✓              |
| ~~T39~~  | ~~S13~~ | ~~P0~~  | ~~Backend~~ | ~~FastAPI + PostgreSQL Setup~~ | ~~API scaffolding, DB schema, migrations~~ ✓               |
| ~~T40~~  | ~~S13~~ | ~~P0~~  | ~~Backend~~ | ~~Authentication~~           | ~~JWT auth, user accounts, API key storage~~ ✓             |
| ~~T41~~  | ~~S13~~ | ~~P0~~  | ~~Backend~~ | ~~Project & Roadmap CRUD~~   | ~~REST endpoints for all item types~~ ✓                    |
| ~~T42~~  | ~~S14~~ | ~~P0~~  | ~~Backend~~ | ~~Background Generation~~    | ~~Task queue for async roadmap generation~~ ✓              |
| ~~T43~~  | ~~S14~~ | ~~P1~~  | ~~Backend~~ | ~~Progress Streaming~~       | ~~WebSocket/SSE for real-time generation progress~~ ✓      |
| ~~T44~~  | ~~S15~~ | ~~P0~~  | ~~Frontend~~ | ~~Frontend Scaffolding~~     | ~~React/Next.js project, routing, auth UI~~ ✓              |
| ~~T45~~  | ~~S15~~ | ~~P0~~  | ~~Frontend~~ | ~~Discovery Wizard~~         | ~~Web-based question conductor~~ ✓                         |
| ~~T46~~  | ~~S15~~ | ~~P1~~  | ~~Frontend~~ | ~~Generation Progress View~~ | ~~Real-time progress display during generation~~ ✓         |
| ~~T47~~  | ~~S16~~ | ~~P0~~  | ~~Frontend~~ | ~~Roadmap Tree Viewer~~      | ~~Interactive tree view of roadmap hierarchy~~ ✓           |
| ~~T48~~  | ~~S16~~ | ~~P0~~  | ~~Frontend~~ | ~~Inline Editing~~           | ~~Edit, add, remove, reorder items in-place~~ ✓            |
| ~~T49~~  | ~~S16~~ | ~~P1~~  | ~~Feature~~ | ~~Multi-Roadmap Projects~~   | ~~Multiple roadmaps per project (MVP, v2, etc.)~~ ✓       |
| ~~T50~~  | ~~S17~~ | ~~P0~~  | ~~Feature~~ | ~~Regenerate at Any Level~~  | ~~Regenerate children of any item without full rebuild~~ ✓  |
| ~~T51~~  | ~~S17~~ | ~~P1~~  | ~~Feature~~ | ~~AI-Assisted Editing~~      | ~~"Split this story", "add error handling tasks", etc.~~ ✓ |
| T52      | S17    | P1       | Feature     | Status Tracking              | Progress dashboards and status sync                        |
| T53      | S17    | P2       | Feature     | Web Export to External PMs   | Wire existing exporters through web UI                     |
| T54      | S18    | P1       | Infra       | vLLM Infrastructure          | GPU setup, model serving, deployment                       |
| T55      | S18    | P1       | Clients     | VLLMClient Implementation    | BaseAIClient adapter for self-hosted models                |
| T56      | S18    | P2       | Testing     | Model Benchmarking           | Quality comparison of self-hosted vs Claude/GPT            |
| T57      | S19    | P1       | Feature     | Billing Integration          | Stripe payments, plan tiers, usage tracking                |
| T58      | S19    | P1       | Feature     | Team Collaboration           | Shared projects, roles, invites                            |
| T59      | S19    | P0       | Infra       | Deployment Infrastructure    | Docker, CI/CD, monitoring, production deploy               |

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

### Sprint 5 - Export & Polish (COMPLETE)

- [x] **T15** - CSV export client for universal PM import ✓
- [x] **T16** - PM client stubs for Linear, Jira, Notion ✓
- [x] **T17** - Wire all components and verify CLI works ✓
- [x] **T18** - End-to-end integration tests with mock client ✓

### Sprint 6 - Documentation & Testing

- [x] **T19** - README and user documentation ✓
- [x] **T20** - Real API smoke test script ✓
- [x] **T21** - Prompt tuning based on smoke test results ✓
- [x] **T22** - Repository cleanup of legacy files ✓
- [ ] **T31** - Update example scripts to use new CLI
- [x] **T32** - Create example idea file (telchar-idea.txt in examples/) ✓

### Sprint 7 - UX Improvements (COMPLETE)

- [x] **T23** - Interactive review mode between generation phases ✓
- [x] **T24** - Cost visibility before starting generation ✓

### Sprint 8 - Post-MVP Features (COMPLETE)

- [x] **T25** - Resume functionality for interrupted generations ✓
- [x] **T26** - Rate limiting with backoff/retry logic ✓
- [x] **T27** - Back-navigation to edit previous answers ✓

### Sprint 9 - Native Integrations (COMPLETE)

- [x] **T33** - Shared documentation page builders from ProjectContext ✓
- [x] **T28** - Native Linear integration via GraphQL API (includes doc page export) ✓
- [x] **T29** - Native Jira Cloud integration via REST API (includes doc page export) ✓
- [x] **T30** - Native Notion integration via API (includes doc page export) ✓

### Sprint 10 - Multi-Model Support (COMPLETE)

- [x] **T34** - Replace `--provider` with `--model` chooser ✓

### Sprint 11 - Progress Indicators (COMPLETE)

- [x] **T35** - Export progress bar with percent and items remaining ✓
- [x] **T36** - Generation progress bar with percent and items remaining ✓

---

## Arcane Web — AI-Native PM Tool

> **Goal:** Turn Arcane from a CLI roadmap generator into a full AI-native project management tool. Users generate roadmaps via a web interface, edit them in-place, track progress, and generate new roadmaps for subsequent project phases. The CLI continues to work as a standalone tool.
>
> **Architecture:** Shared `arcane-core` library consumed by both `arcane-cli` (existing) and `arcane-web` (new FastAPI + React app). Self-hosted model support added as a learning exercise via vLLM.

### Sprint 12 - Core Extraction (COMPLETE)

> **Goal:** Split the monolith into a reusable core library + thin CLI wrapper. This is the prerequisite for everything — no web work starts until this is done.

- [x] **T37** - Extract `arcane-core` shared library (models, generators, clients, templates, questions registry) ✓
- [x] **T38** - Refactor CLI as thin wrapper importing from arcane-core ✓

### Sprint 13 - API Foundation

> **Goal:** Stand up a FastAPI backend with auth and CRUD for all item types. By the end of this sprint, you can create a project, generate a roadmap, and read it back via REST API.

- [x] **T39** - FastAPI project scaffolding, PostgreSQL schema, Alembic migrations ✓
- [x] **T40** - JWT authentication, user accounts, encrypted PM credential storage ✓
- [x] **T41** - Project & Roadmap CRUD endpoints (all 4 item levels) ✓

### Sprint 14 - Async Generation (COMPLETE)

> **Goal:** Generation runs as a background job with real-time progress pushed to the client. The API returns immediately with a job ID; the client polls or streams for updates.

- [x] **T42** - Background generation via asyncio.create_task wrapping the existing orchestrator ✓
- [x] **T43** - SSE endpoint for generation progress streaming ✓

### Sprint 15 - Frontend Foundation (COMPLETE)

> **Goal:** A working web UI where a user can log in, answer discovery questions, kick off generation, and watch it happen in real time. No editing yet — just generate and view.

- [x] **T44** - React/Next.js project scaffolding, routing, auth pages (login/register) ✓
- [x] **T45** - Discovery wizard (web version of QuestionConductor) ✓
- [x] **T46** - Real-time generation progress view ✓

### Sprint 16 - Roadmap Viewer & Editor

> **Goal:** The core PM experience. Users can view their roadmap as an interactive tree, edit any item inline, and manage multiple roadmaps per project. This is where it becomes a real PM tool.

- [x] **T47** - Interactive roadmap tree view with expand/collapse and detail panels ✓
- [x] **T48** - Inline editing: add, remove, reorder, edit fields for all item types ✓
- [x] **T49** - Multi-roadmap per project (MVP roadmap, v2 roadmap, etc.) ✓

### Sprint 17 - AI-Native PM Features

> **Goal:** The differentiating features. Regenerate any subtree, use AI to assist with editing, and track status. Export to external PM tools as an offramp.

- [x] **T50** - Regenerate at any level ("regenerate this epic's stories") ✓
- [x] **T51** - AI-assisted editing ("split this story into smaller stories", "add tests") ✓
- [ ] **T52** - Status tracking and progress dashboards
- [ ] **T53** - Export to external PM tools via web UI (wire existing Linear/Jira/Notion/CSV exporters)

### Sprint 18 - Self-Hosted Models (Learning)

> **Goal:** Learn vLLM and self-hosted model serving by adding it as an alternative AI backend. Uses the existing `BaseAIClient` abstraction — zero changes to generation logic.

- [ ] **T54** - vLLM infrastructure setup (GPU provisioning, model serving, health checks)
- [ ] **T55** - `VLLMClient` implementation conforming to `BaseAIClient` interface
- [ ] **T56** - Benchmark quality: compare self-hosted model output vs Claude/GPT on same prompts

### Sprint 19 - Launch Prep

> **Goal:** Everything needed to open the product to real users. Billing, deployment, and basic collaboration.

- [ ] **T57** - Stripe billing integration (plan tiers, usage tracking, checkout)
- [ ] **T58** - Team collaboration (shared projects, role-based access, invites)
- [ ] **T59** - Deployment infrastructure (Docker, CI/CD, monitoring, production deploy)

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

### T24: Cost Visibility ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S7 - UX Improvements                                       |
| Priority    | P0 - Critical                                              |
| Type        | UX                                                         |
| Description | Show estimated token usage and cost before starting generation |

**Commit:** `feat: add cost estimation before generation starts`

**What was done:**
- Created `arcane/utils/cost_estimator.py` with:
  - `CostEstimate` dataclass for structured estimates
  - `estimate_generation_cost()` function with configurable parameters
  - `format_cost_estimate()` function for display formatting
  - Token estimates per call type (milestone, epic, story, task)
  - Model pricing dictionary for accurate cost calculation
- Updated `arcane/utils/__init__.py` to export cost estimator functions
- Modified `arcane/cli.py` to show cost estimate before generation (interactive mode only)
- Added user confirmation prompt before proceeding

**User experience:**
```
📊 Estimated generation:
   ~40 API calls
   ~136,700 tokens (55,100 in / 81,600 out)
   ~$1.39 estimated cost

Proceed with generation? [Y/n] >
```

---

### T25: Resume Functionality ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S8 - Post-MVP Features                                     |
| Priority    | P1 - High                                                  |
| Type        | Generators                                                 |
| Description | Actually continue generation from where it stopped, not just detect |

**Commit:** `feat: implement actual resume functionality for interrupted generations`

**What was done:**
- Fixed incremental save ordering in `generate()`: milestones and epics are now appended to the roadmap before expansion so partial progress is captured in saves
- Added `resume(roadmap)` method to `RoadmapOrchestrator` that walks the existing hierarchy, skips complete items, and generates missing children
- Added `_item_context()` helper to extract compact context dicts from saved items for `parent_context` injection
- Extracted `_print_summary()` for shared use by both `generate()` and `resume()`
- Wired up `_resume()` in `cli.py` with API key validation, connection check, and confirmation prompt
- Fixed pre-existing test failures: updated all 4 MockClient classes to implement `usage`, `reset_usage`, and `level` parameter

---

### T26: Rate Limiting ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S8 - Post-MVP Features                                     |
| Priority    | P1 - High                                                  |
| Type        | Clients                                                    |
| Description | Handle Anthropic API rate limits with exponential backoff and retry |

**Commit:** `feat: add rate limiting with exponential backoff`

**What was done:**
- Added rate limiting infrastructure to `BaseAIClient`:
  - Configurable class attributes: `rate_limit_max_retries` (5), `rate_limit_initial_delay` (2s), `rate_limit_max_delay` (60s)
  - `_is_rate_limit_error(error)` method — subclasses override to detect provider-specific rate limit exceptions (returns False by default for local models)
  - `_call_with_backoff(coro_func)` helper — wraps any async call with exponential backoff, only retrying on rate limit errors
- `AnthropicClient` overrides `_is_rate_limit_error` to detect `anthropic.RateLimitError`
- Extracted `_create_message()` from `generate()` so the raw API call can be wrapped with `_call_with_backoff()`
- Future clients (OpenAI, Gemini) override `_is_rate_limit_error`; local models set `rate_limit_max_retries = 0`
- Added 8 tests covering: success path, retry-then-succeed, max retries exhausted, non-rate-limit passthrough, disabled mode, defaults, Anthropic detection

---

### T27: Question Back-Navigation ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S8 - Post-MVP Features                                     |
| Priority    | P1 - High                                                  |
| Type        | Questions                                                  |
| Description | Allow users to go back and edit previous answers during discovery |

**Commit:** `feat: add back-navigation in question flow`

**What was done:**
- Refactored `run()` from a `for` loop to an index-based `while` loop for bidirectional navigation
- Added `_BACK` sentinel returned by `_ask()` when user types `<`
- Back-navigation works across all question types:
  - TEXT/LIST: checks for `<` before validation
  - INT: switched from IntPrompt to Prompt with manual int validation
  - CHOICE: adds `<` to the choices list
  - CONFIRM: uses Prompt with choices `["y", "n", "<"]`
- Pre-filled answers (from CLI flags like `--name`) are tracked and skipped in both directions
- Category headers reprint correctly when navigating backward
- Added answer summary table after all questions, with option to edit any answer by number before finalizing
- Added `_display_summary()` and `_format_answer()` helpers

---

### T28: Linear Integration

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S9 - Native Integrations                                   |
| Priority    | P2 - Medium                                                |
| Type        | Export                                                     |
| Description | Native export to Linear using GraphQL API, including documentation pages |

**Commit message:** `feat: add native Linear integration`

**Mapping:**
- Milestones → Projects
- Epics → Issues with 'epic' label
- Stories → Issues linked to epic
- Tasks → Sub-issues

**Documentation pages:** Uses T33's doc page builders to create Linear Documents (markdown) associated with the Initiative. See PM_INTEGRATIONS.md "Documentation Pages" section for details.

---

### T29: Jira Integration ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S9 - Native Integrations                                   |
| Priority    | P2 - Medium                                                |
| Type        | Export                                                     |
| Description | Native export to Jira Cloud using REST API, including documentation pages via Confluence (optional) |

**Commit:** `feat: add native Jira Cloud integration`

**What was done:**
- Full `JiraClient` implementation in `arcane/project_management/jira.py`
- 4-phase export: project/field discovery → version creation → issue hierarchy (Epic → Story → Sub-task) → status transitions + prerequisite links
- ADF (Atlassian Document Format) builders for rich descriptions
- Priority mapping, story points, epic link custom field support
- Claude Code prompts exported as task comments
- Progress callback support
- Comprehensive test suite in `tests/test_project_management/test_jira.py`

---

### T30: Notion Integration

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S9 - Native Integrations                                   |
| Priority    | P2 - Medium                                                |
| Type        | Export                                                     |
| Description | Native export to Notion using API, including documentation pages as child pages |

**Commit message:** `feat: add native Notion integration`

**Mapping:**
- Create database with roadmap items
- Use nested pages for hierarchy
- Include all metadata as properties

**Documentation pages:** Uses T33's doc page builders to create child pages under the parent page (alongside the 4 databases). Notion is the best fit for doc pages since it IS a wiki — pages support rich block content (callouts, to-do lists, headings). See PM_INTEGRATIONS.md "Documentation Pages" section for details.

---

### T31: Update Example Scripts

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S6 - Documentation & Testing                               |
| Priority    | P1 - High                                                  |
| Type        | Scripts                                                    |
| Description | Create new example scripts that use the refactored `arcane new` CLI |

**Commit message:** `chore: update example scripts for new CLI`

**Background:**
The old scripts in `scripts/` use the deprecated `arcane interactive` command with many flags that no longer exist. The new CLI uses:
- `arcane new` - Interactive discovery and generation
- `arcane new --name "Project"` - Skip project name question
- `arcane new --no-interactive` - Skip review prompts
- `arcane new --output ./path` - Custom output directory

**Create/update scripts:**

1. **`scripts/run.sh`** - Basic example:
   ```bash
   #!/bin/bash
   # Basic Arcane roadmap generation
   arcane new --output ./output
   ```

2. **`scripts/run-with-idea.sh`** - Using idea file context:
   ```bash
   #!/bin/bash
   # Generate roadmap with idea file for reference
   # Note: The idea file is shown during discovery for context
   arcane new --name "$(head -1 idea.txt)" --output ./output
   ```

3. **`scripts/run-batch.sh`** - Non-interactive batch mode:
   ```bash
   #!/bin/bash
   # Non-interactive mode (for CI/testing)
   arcane new --name "Test Project" --no-interactive --output ./output
   ```

**Note:** Old scripts were deleted in T22 (Repository Cleanup). Only `scripts/smoke_test.py` remains.

---

### T32: Create Example Idea File ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S6 - Documentation & Testing                               |
| Priority    | P1 - High                                                  |
| Type        | Scripts                                                    |
| Description | Create telchar.txt example idea file for testing Arcane with real project |

**Commit:** `docs: add example idea file for testing`

**What was done:**
- Created `examples/telchar-idea.txt` — comprehensive 630-line project idea document
- Covers all 16 arcane prompts with detailed answers for the Telchar project (interactive project scaffolding CLI)
- Includes architecture notes (hybrid template engine), full 8-phase prompt flow, template directory structure
- Serves as both a testing input and a template for users writing their own idea files
- Documents both `--idea` flag usage and full `--no-interactive` flag-based invocation

---

### T33: Documentation Page Builders ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S9 - Native Integrations                                   |
| Priority    | P1 - High                                                  |
| Type        | Export                                                     |
| Description | Shared doc page building logic from ProjectContext, used by all PM integrations |

**Commit:** `feat: add documentation page builders from ProjectContext`

**What was done:**
- Created `arcane/project_management/docs.py` with:
  - `DocSection(BaseModel)` — title, content_type, items, optional icon
  - `DocPage(BaseModel)` — title, list of sections
  - `build_project_overview()` — vision callout, problem paragraph, target users list, optional similar products & notes
  - `build_requirements()` — must-have checklist, optional nice-to-have checklist & out-of-scope callout
  - `build_technical_decisions()` — optional tech stack list, infrastructure paragraph, codebase paragraph
  - `build_team_constraints()` — timeline callout, team paragraph, budget paragraph
  - `build_all_pages()` — returns all 4 pages
- Optional/empty fields omitted (e.g., no "Nice-to-Have" section if list is empty)
- Updated `arcane/project_management/__init__.py` to export all new symbols
- Created `tests/test_project_management/test_docs.py` with 30 tests covering all builders, minimal context, and model behavior

**Dependencies:** None (uses existing `ProjectContext` model). T28/T29/T30 depend on this task.

See PM_INTEGRATIONS.md "Documentation Pages" section for per-tool formatting details.

---

### T34: Model Selection UX

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S10 - Multi-Model Support                                  |
| Priority    | P1 - High                                                  |
| Type        | CLI                                                        |
| Description | Replace `--provider` with a `--model` flag that presents a curated list of AI models |

**Commit message:** `feat: replace --provider with --model chooser`

**Problem:**
Currently, users choose a provider (`--provider anthropic`) and the model is set separately via the `ARCANE_MODEL` env var (defaulting to `claude-sonnet-4-20250514`). This is awkward because:
1. Users think in terms of models ("I want to use Opus"), not providers
2. The `--provider` flag is meaningless when there's only one provider (anthropic)
3. The env var for model selection is hidden — most users won't discover it
4. As we add OpenAI/Gemini support, asking for provider AND model is redundant; the model name implies the provider

**Solution:**
Replace `--provider` with a `--model` flag that accepts a model identifier from a curated list. The CLI resolves which provider to use from the model name. In interactive mode with no `--model` flag, prompt the user to choose from the list.

**Curated model list (defined in a new `arcane/models.py` or in `config.py`):**
```python
SUPPORTED_MODELS = {
    # Display name -> (provider, model_id, description)
    "sonnet": ("anthropic", "claude-sonnet-4-20250514", "Claude Sonnet 4 — fast, balanced (recommended)"),
    "opus": ("anthropic", "claude-opus-4-20250514", "Claude Opus 4 — most capable, slower"),
    "haiku": ("anthropic", "claude-haiku-4-5-20251001", "Claude Haiku 4.5 — fastest, cheapest"),
    # Future:
    # "gpt-4o": ("openai", "gpt-4o", "GPT-4o — OpenAI's flagship"),
    # "gemini-pro": ("google", "gemini-1.5-pro", "Gemini 1.5 Pro"),
}
DEFAULT_MODEL = "sonnet"
```

**Files to modify:**

1. **`arcane/config.py`:**
   - Change `model: str = "claude-sonnet-4-20250514"` to `model: str = "sonnet"` (use short alias as default)
   - Add `SUPPORTED_MODELS` dict and `DEFAULT_MODEL` constant (or create a separate `arcane/models.py`)
   - Add `resolve_model(alias: str) -> tuple[str, str]` function that returns `(provider, model_id)` from an alias, or treats the input as a raw model ID if not in the alias list

2. **`arcane/cli.py`:**
   - Remove `--provider` flag from `new()` command
   - Add `--model` / `-m` flag: `typer.Option("sonnet", "--model", "-m", help="AI model to use (sonnet, opus, haiku)")`
   - In `_new()`: call `resolve_model(model)` to get `(provider, model_id)`, pass both to `create_client(provider, api_key=..., model=model_id)`
   - In interactive mode with no explicit `--model`: show a Rich selection prompt listing available models with descriptions
   - Update `config` command output to show resolved model name
   - Keep `ARCANE_MODEL` env var working (if set to "opus" or "claude-opus-4-20250514", both should work)

3. **`arcane/clients/__init__.py`:**
   - `create_client()` factory stays the same (still takes `provider` string internally)

4. **`arcane/utils/cost_estimator.py`:**
   - Update `MODEL_PRICING` keys to include new model IDs as they're added
   - `estimate_generation_cost()` should accept either alias ("sonnet") or full model ID
   - Add a lookup step: if model is an alias, resolve to model_id before pricing lookup

5. **`arcane/clients/anthropic.py`:**
   - No changes needed (already accepts model as a string parameter)

**New interactive prompt (when `--model` not provided and in interactive mode):**
```
  Which AI model should we use for generation?

  1. sonnet  — Claude Sonnet 4 — fast, balanced (recommended)
  2. opus    — Claude Opus 4 — most capable, slower
  3. haiku   — Claude Haiku 4.5 — fastest, cheapest

  Model [sonnet]:
```

**Tests to add:**
- `test_resolve_model_alias` — "sonnet" → ("anthropic", "claude-sonnet-4-20250514")
- `test_resolve_model_full_id` — "claude-opus-4-20250514" → ("anthropic", "claude-opus-4-20250514")
- `test_resolve_model_invalid` — "gpt-5" raises error with helpful message
- `test_model_flag_overrides_env` — CLI `--model opus` takes precedence over `ARCANE_MODEL`
- `test_cost_estimate_with_alias` — "opus" resolves correctly in cost estimator
- `test_default_model` — no flag and no env var defaults to "sonnet"

**Migration / backwards compatibility:**
- `ARCANE_MODEL=claude-sonnet-4-20250514` (old full ID) still works — `resolve_model()` checks aliases first, then checks if the value is a known model ID across all providers, then falls back to using it as-is with a warning
- `--provider` flag is removed entirely (was only "anthropic" anyway). If someone has scripts using `--provider`, they get a clean Typer error about an unknown option

---

### T35: Export Progress Bar

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S11 - Progress Indicators                                  |
| Priority    | P1 - High                                                  |
| Type        | UX                                                         |
| Description | Show a single-line progress bar at the bottom of export output with percent completion and items remaining |

**Commit message:** `feat: add progress bar to PM export`

**Problem:**
When exporting a large roadmap (e.g., telchar with hundreds of items) to Notion/Linear/Jira, the user has no visibility into progress. They don't know how far along the export is or how many items remain.

**Solution:**
Add a Rich Progress bar at the bottom of export output showing:
- A progress bar
- Percent completion
- Items completed / total items
- Current item being exported (e.g., "Exporting: Task - Set up database schema")

**Implementation:**

1. **Calculate total items before export starts:**
   - Count all milestones + epics + stories + tasks from `roadmap.total_items`
   - This gives the total for the progress bar denominator

2. **Add progress callback to `BasePMClient.export()`:**
   - Add an optional `progress_callback: Callable[[str, str], None] | None = None` parameter
   - PM clients call `progress_callback(item_type, item_name)` after each item is created
   - The callback increments the progress bar

3. **Use Rich Progress in the CLI export command:**
   ```python
   from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn

   total = sum(roadmap.total_items.values())
   with Progress(
       TextColumn("[bold blue]{task.description}"),
       BarColumn(),
       TaskProgressColumn(),
       TextColumn("{task.fields[remaining]} remaining"),
   ) as progress:
       task = progress.add_task("Exporting...", total=total, remaining=total)

       def on_progress(item_type: str, item_name: str):
           completed = progress.tasks[0].completed + 1
           remaining = total - completed
           progress.update(task, advance=1, remaining=remaining,
                          description=f"Exporting {item_type}: {item_name}")

       result = await client.export(roadmap, progress_callback=on_progress, **kwargs)
   ```

4. **Update each PM client to call the callback:**
   - `NotionClient.export()`: call after each database item is created
   - `CSVClient.export()`: call after each row is written
   - `LinearClient.export()`: call after each API mutation
   - `JiraClient.export()`: call after each API call

**Display example:**
```
Exporting Task: Set up database schema  ━━━━━━━━━━━━━━━━━━╸━━━━━━  67%  42 remaining
```

**Files to modify:**
- `arcane/project_management/base.py` — add `progress_callback` parameter to `BasePMClient.export()`
- `arcane/project_management/notion.py` — call callback after each item
- `arcane/project_management/csv.py` — call callback after each row
- `arcane/project_management/linear.py` — call callback after each item (when implemented)
- `arcane/project_management/jira.py` — call callback after each item (when implemented)
- `arcane/cli.py` — wrap export call with Rich Progress

**Tests:**
- Verify callback is called the expected number of times
- Verify export still works when no callback is provided (None)

---

### T36: Generation Progress Bar

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S11 - Progress Indicators                                  |
| Priority    | P1 - High                                                  |
| Type        | UX                                                         |
| Description | Show a progress bar during roadmap generation (new/resume) with percent completion and items remaining |

**Commit message:** `feat: add progress bar to roadmap generation`

**Problem:**
During `arcane new` or `arcane resume`, generation can take many minutes for large roadmaps. The user sees individual "Expanding: ..." messages but has no sense of overall progress or how much work remains.

**Solution:**
Add a Rich Progress bar showing overall generation progress. Since generation is hierarchical and the total number of items isn't known upfront (epics/stories/tasks are discovered as we go), use a two-phase approach:

1. **After milestones are generated:** Calculate estimated total API calls based on milestone count and expected expansion ratios
2. **Update total dynamically:** As epics and stories are generated, refine the total count

**Implementation:**

1. **Add progress tracking to `RoadmapOrchestrator`:**
   - After milestones are generated, estimate total items:
     - Each milestone → 1 epic generation call
     - Each epic (estimated ~3 per milestone) → 1 story generation call
     - Each story (estimated ~3 per epic) → 1 task generation call
   - Update estimates as actual counts become known

2. **Use Rich Progress in the orchestrator:**
   ```python
   from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn

   with Progress(
       TextColumn("[bold blue]{task.description}"),
       BarColumn(),
       TaskProgressColumn(),
       TextColumn("{task.fields[remaining]} remaining"),
   ) as progress:
       task = progress.add_task("Generating milestones...", total=estimated_total, remaining=estimated_total)

       # After each generation step:
       progress.update(task, advance=1, remaining=remaining,
                      description=f"Generating stories for: {epic.name}")
   ```

3. **Progress phases:**
   - "Generating milestones..." — 1 step
   - "Generating epics for: {milestone.name}" — 1 step per milestone
   - "Generating stories for: {epic.name}" — 1 step per epic
   - "Generating tasks for: {story.name}" — 1 step per story

4. **For resume:** Calculate remaining by counting items that still need generation (stories without tasks, epics without stories, etc.)

**Display example:**
```
Generating tasks for: Set up CI/CD pipeline  ━━━━━━━━━━━━╸━━━━━━━━━━━  38%  24 remaining
```

**Files to modify:**
- `arcane/generators/orchestrator.py` — add Rich Progress to `generate()` and `resume()` methods
- `arcane/cli.py` — pass console to orchestrator (already done)

**Tests:**
- Verify generation still completes with progress tracking
- Verify resume calculates remaining items correctly

---

---

## SaaS Detailed Tasks

---

### T37: Extract arcane-core Shared Library ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S12 - Core Extraction                                      |
| Priority    | P0 - Critical                                              |
| Type        | Refactor                                                   |
| Description | Extract all reusable logic into an `arcane-core` package that both CLI and web consume |

**Commit:** `refactor: extract arcane-core shared library under arcane/core/`

**What was done:**
- Chose the subdirectory split approach (Option B): single `pyproject.toml`, modules moved under `arcane/core/`
- Moved 8 directories (`items/`, `clients/`, `generators/`, `templates/`, `project_management/`, `questions/`, `storage/`, `utils/`) and 2 files (`config.py`, `models.py`) into `arcane/core/` via `git mv`
- Updated all imports from `arcane.X` to `arcane.core.X` across 13 source files, 22 test files, and `scripts/smoke_test.py`
- Created `arcane/core/__init__.py`
- CLI stays at `arcane/cli.py`, entry point unchanged

**Verification:** All 537 tests pass, CLI works identically, imports resolve correctly.

---

### T38: Thin CLI Wrapper ✓

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S12 - Core Extraction                                      |
| Priority    | P0 - Critical                                              |
| Type        | Refactor                                                   |
| Description | Refactor the existing CLI to import from arcane-core instead of owning the logic |

**Commit:** `refactor: extract arcane-core shared library under arcane/core/` (same commit as T37)

**What was done:**
- `cli.py` imports updated from `arcane.X` to `arcane.core.X` (11 top-level imports + 3 lazy imports)
- All Typer commands work identically
- Entry point `python -m arcane` unchanged
- `QuestionConductor`, `StorageManager`, and `utils/console.py` moved to `arcane/core/` (Rich dependency is fine — Console is always injected as a constructor parameter)

**Verification:** All 537 tests pass, CLI works identically.

---

### T39: FastAPI + PostgreSQL Setup

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S13 - API Foundation                                       |
| Priority    | P0 - Critical                                              |
| Type        | Backend                                                    |
| Description | Scaffold the FastAPI application with PostgreSQL database and Alembic migrations |

**Tech choices:**
- **FastAPI** — Same async/Pydantic ecosystem as arcane-core
- **SQLAlchemy 2.0** (async) — ORM with native async support
- **Alembic** — Database migrations
- **PostgreSQL** — Primary database; roadmap JSON stored in JSONB columns

**Database schema (initial):**
```sql
users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

projects (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

roadmaps (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects,
    name TEXT NOT NULL,           -- "MVP", "v2.0", etc.
    context JSONB NOT NULL,       -- ProjectContext serialized
    roadmap_data JSONB NOT NULL,  -- Full Roadmap serialized via model_dump()
    status TEXT NOT NULL,         -- draft, generating, complete
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)

generation_jobs (
    id UUID PRIMARY KEY,
    roadmap_id UUID REFERENCES roadmaps,
    status TEXT NOT NULL,          -- pending, running, completed, failed
    progress JSONB,                -- {current_step, total_steps, current_item}
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
)

pm_credentials (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    service TEXT NOT NULL,          -- notion, linear, jira
    credentials JSONB NOT NULL,    -- Encrypted API keys / OAuth tokens
    created_at TIMESTAMPTZ
)
```

**Key insight:** `roadmap_data` stores the full `Roadmap.model_dump()` as JSONB. This means we get the existing Pydantic serialization for free. Reads deserialize via `Roadmap.model_validate(data)`. No ORM mapping of the 4-level hierarchy needed — it's just a JSON document.

**API structure:**
```
web/backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, middleware, CORS
│   ├── config.py            # Web-specific settings
│   ├── database.py          # SQLAlchemy engine, session
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # API route handlers
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── roadmaps.py
│   │   ├── generation.py
│   │   └── export.py
│   ├── services/            # Business logic
│   └── deps.py              # Dependency injection (current_user, db session)
├── alembic/
├── alembic.ini
└── pyproject.toml
```

---

### T40: Authentication

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S13 - API Foundation                                       |
| Priority    | P0 - Critical                                              |
| Type        | Backend                                                    |
| Description | JWT-based authentication with user registration, login, and API key storage |

**Implementation:**
- **Registration:** `POST /auth/register` — email + password, returns JWT
- **Login:** `POST /auth/login` — email + password, returns access + refresh tokens
- **Token refresh:** `POST /auth/refresh` — refresh token → new access token
- **Password hashing:** bcrypt via `passlib`
- **JWT:** `python-jose` with RS256 or HS256
- **Dependency:** `get_current_user()` FastAPI dependency for protected routes
- **PM credentials:** Encrypted at rest (Fernet symmetric encryption, key from env var)

**Keep it simple for now:** Email/password auth only. OAuth (Google, GitHub) and SSO are Sprint 19 concerns.

---

### T41: Project & Roadmap CRUD

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S13 - API Foundation                                       |
| Priority    | P0 - Critical                                              |
| Type        | Backend                                                    |
| Description | REST API endpoints for projects, roadmaps, and individual item CRUD |

**Endpoints:**

```
# Projects
POST   /projects                     Create project
GET    /projects                     List user's projects
GET    /projects/{id}                Get project with roadmap list
PATCH  /projects/{id}                Update project name
DELETE /projects/{id}                Delete project and all roadmaps

# Roadmaps
POST   /projects/{id}/roadmaps       Create roadmap (from context, triggers generation)
GET    /projects/{id}/roadmaps        List roadmaps for project
GET    /roadmaps/{id}                 Get full roadmap (entire hierarchy)
DELETE /roadmaps/{id}                 Delete roadmap

# Items (operate on roadmap_data JSONB)
GET    /roadmaps/{id}/milestones                         List milestones
PATCH  /roadmaps/{id}/milestones/{ms_id}                 Update milestone
POST   /roadmaps/{id}/milestones                         Add milestone
DELETE /roadmaps/{id}/milestones/{ms_id}                 Remove milestone
# Same pattern for epics, stories, tasks nested under their parents
PATCH  /roadmaps/{id}/items/{item_id}                    Update any item by ID
DELETE /roadmaps/{id}/items/{item_id}                    Remove any item by ID
POST   /roadmaps/{id}/items/{parent_id}/children         Add child item
PUT    /roadmaps/{id}/items/reorder                      Reorder items within parent
```

**Key design decision:** Items are stored as JSONB, not normalized tables. CRUD operations load the Roadmap, modify the Pydantic model in memory, and save back. This is fine for single-user editing. If we need concurrent editing later (Sprint 19 collaboration), we'd add optimistic locking via `updated_at` version checks.

---

### T42: Background Generation

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S14 - Async Generation                                     |
| Priority    | P0 - Critical                                              |
| Type        | Backend                                                    |
| Description | Run roadmap generation as a background job with progress tracking |

**Why background:** A full roadmap generation makes dozens of AI API calls over several minutes. This can't be a synchronous HTTP request.

**Tech choice: Arq** (async Redis-based task queue) — lightweight, async-native, fits the existing async codebase. Alternative: Celery (heavier, more mature).

**Flow:**
1. `POST /projects/{id}/roadmaps` creates a roadmap record (status=generating) and enqueues a generation job
2. Job worker picks up the job, instantiates `RoadmapOrchestrator` from arcane-core
3. Orchestrator runs generation, saving progress to `generation_jobs.progress` JSONB after each item
4. On completion, saves final roadmap to `roadmaps.roadmap_data` and sets status=complete
5. On failure, sets status=failed with error message

**Progress tracking:**
- Generation job updates `progress` JSONB: `{step: "Generating stories for: Auth Epic", completed: 12, total: 45}`
- Client polls `GET /generation-jobs/{id}` or uses WebSocket (T43)

---

### T43: Progress Streaming

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S14 - Async Generation                                     |
| Priority    | P1 - High                                                  |
| Type        | Backend                                                    |
| Description | Real-time progress updates via WebSocket or SSE during generation |

**Options:**
- **SSE (Server-Sent Events):** Simpler, one-directional, works through proxies. Client uses `EventSource` API.
- **WebSocket:** Bidirectional (but we only need server→client), slightly more complex.

**Recommendation:** SSE for simplicity. Endpoint: `GET /generation-jobs/{id}/stream` returns event stream.

**Event format:**
```
event: progress
data: {"step": "Generating stories for: Auth Epic", "completed": 12, "total": 45}

event: item_created
data: {"type": "story", "name": "User Login", "parent": "Auth Epic"}

event: complete
data: {"roadmap_id": "uuid", "total_items": 156}

event: error
data: {"message": "API rate limit exceeded, retrying..."}
```

---

### T44: Frontend Scaffolding

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S15 - Frontend Foundation                                  |
| Priority    | P0 - Critical                                              |
| Type        | Frontend                                                   |
| Description | React/Next.js project setup with routing, auth UI, and API client |

**Tech choices:**
- **Next.js 14+** (App Router) — SSR where needed, file-based routing
- **Tailwind CSS** — Utility-first styling
- **shadcn/ui** — Component library (built on Radix primitives)
- **React Query (TanStack Query)** — Server state management, caching
- **Zustand** — Client state (if needed beyond React Query)

**Pages:**
```
/                          Landing / dashboard (project list)
/login                     Login form
/register                  Registration form
/projects/[id]             Project detail (roadmap list)
/projects/[id]/new         Discovery wizard → generation
/roadmaps/[id]             Roadmap viewer/editor
/roadmaps/[id]/generating  Generation progress view
/settings                  User settings, PM credentials
```

**API client:** Thin wrapper around `fetch` with JWT token handling, auto-refresh, and React Query integration.

---

### T45: Discovery Wizard

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S15 - Frontend Foundation                                  |
| Priority    | P0 - Critical                                              |
| Type        | Frontend                                                   |
| Description | Web-based question flow replacing the CLI QuestionConductor |

**Design:** Multi-step form wizard. Each category (Basic Info, Constraints, Technical, Requirements) is one step. Uses the same `QuestionRegistry` from arcane-core to define questions — the frontend renders them based on `question_type`.

**Component mapping:**
- `QuestionType.TEXT` → `<textarea>` or `<input type="text">`
- `QuestionType.INT` → `<input type="number">`
- `QuestionType.CHOICE` → Radio buttons or select dropdown
- `QuestionType.LIST` → Tag input (comma-separated with chips)
- `QuestionType.CONFIRM` → Toggle switch

**Flow:** Step through categories → Review summary → Submit → Redirect to generation progress view.

**API call:** `POST /projects/{id}/roadmaps` with the `ProjectContext` JSON body.

---

### T46: Generation Progress View

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S15 - Frontend Foundation                                  |
| Priority    | P1 - High                                                  |
| Type        | Frontend                                                   |
| Description | Real-time progress display during roadmap generation |

**UI:** Progress bar + live feed of items being generated. Shows current step, percent complete, and a scrolling list of created items (milestones → epics → stories → tasks appearing in real time).

**Implementation:** Connect to SSE endpoint from T43. Update React state on each event. On `complete` event, redirect to roadmap viewer.

---

### T47: Roadmap Tree Viewer

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S16 - Roadmap Viewer & Editor                              |
| Priority    | P0 - Critical                                              |
| Type        | Frontend                                                   |
| Description | Interactive tree view of the full roadmap hierarchy with expand/collapse and detail panels |

**Layout:** Left panel: collapsible tree (milestones → epics → stories → tasks). Right panel: detail view of selected item (description, acceptance criteria, hours, status, claude_code_prompt).

**Features:**
- Expand/collapse at any level
- Click item to view details
- Color-coded by status (not started, in progress, completed)
- Priority badges
- Hour estimates rolled up at each level
- Search/filter by name

**Libraries to evaluate:** react-arborist (tree component), or custom with Radix Accordion.

---

### T48: Inline Editing

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S16 - Roadmap Viewer & Editor                              |
| Priority    | P0 - Critical                                              |
| Type        | Frontend                                                   |
| Description | Edit any item in-place: modify fields, add/remove items, reorder within parent |

**Capabilities:**
- Click any field in the detail panel to edit inline
- Add new item (milestone, epic, story, task) under any parent
- Delete items (with confirmation for items with children)
- Drag-and-drop reorder within a parent
- Status and priority dropdowns
- Auto-save on blur (PATCH to API)

**API calls:** Uses the CRUD endpoints from T41. Optimistic updates with React Query mutation + rollback on error.

---

### T49: Multi-Roadmap Projects

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S16 - Roadmap Viewer & Editor                              |
| Priority    | P1 - High                                                  |
| Type        | Feature                                                    |
| Description | Support multiple roadmaps per project for phased planning (MVP, v2, etc.) |

**This is the retention feature.** Users don't generate one roadmap and leave — they generate the MVP roadmap, work through it, then come back and generate the v2 roadmap. The project page shows all roadmaps with their completion status.

**UI:** Project page shows a list of roadmaps as cards (name, status, item counts, progress %). "New Roadmap" button starts the discovery wizard with the project context pre-filled. Previous roadmap context is optionally injected into generation ("here's what was built in v1, now plan v2").

**Generation context:** When creating a subsequent roadmap, the system prompt includes a summary of completed roadmaps: "The following milestones have already been delivered: [list]. Generate the NEXT phase of work, not what's already done."

---

### T50: Regenerate at Any Level

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S17 - AI-Native PM Features                                |
| Priority    | P0 - Critical                                              |
| Type        | Feature                                                    |
| Description | Regenerate children of any item without rebuilding the full roadmap |

**Use cases:**
- "This epic's stories don't look right" → Regenerate stories for that epic
- "I need more tasks for this story" → Regenerate tasks
- "Restructure this milestone's epics" → Regenerate epics, which cascades to stories/tasks

**Implementation:**
- Add a "Regenerate" button to each item in the tree viewer
- Uses the existing generators from arcane-core with `parent_context` set to the selected item
- `sibling_context` populated from existing siblings to avoid duplication
- Option to keep or discard existing children
- Runs as background job (reuse T42 infrastructure)

---

### T51: AI-Assisted Editing

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S17 - AI-Native PM Features                                |
| Priority    | P1 - High                                                  |
| Type        | Feature                                                    |
| Description | Natural language commands to modify roadmap items using AI |

**Examples:**
- Select a story → "Split this into 3 smaller stories"
- Select an epic → "Add error handling and monitoring tasks to every story"
- Select a milestone → "This is too ambitious, reduce scope by 30%"
- Select a task → "Make this more detailed, include specific file paths"

**Implementation:**
- Chat-like input on the detail panel
- Sends the current item + command to an AI call
- AI returns modified item(s) as structured output (same Pydantic models)
- User reviews changes before applying
- New Jinja2 templates for edit commands (separate from generation templates)

---

### T52: Status Tracking

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S17 - AI-Native PM Features                                |
| Priority    | P1 - High                                                  |
| Type        | Feature                                                    |
| Description | Progress dashboards and status management for roadmap items |

**Features:**
- Change status on any item (not started → in progress → completed)
- Parent status auto-calculated from children (e.g., milestone is "in progress" if any epic is in progress)
- Dashboard view: progress bars per milestone, burndown-style chart
- Hours completed vs remaining
- Overdue detection (if target_date is set on milestones)

---

### T53: Web Export to External PMs

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S17 - AI-Native PM Features                                |
| Priority    | P2 - Medium                                                |
| Type        | Feature                                                    |
| Description | Wire the existing CLI exporters (Linear, Jira, Notion, CSV) through the web UI |

**Implementation:**
- Settings page: "Connect to Notion/Linear/Jira" with API key input (OAuth in Sprint 19)
- Export button on roadmap page with target selector
- Runs export as background job using the existing PM client classes from arcane-core
- Shows export progress (reuse progress bar infrastructure)
- Export history: which roadmap was exported where and when

---

### T54: vLLM Infrastructure

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S18 - Self-Hosted Models                                   |
| Priority    | P1 - High                                                  |
| Type        | Infra                                                      |
| Description | Set up vLLM model serving infrastructure for self-hosted AI |

**Learning goals:** Understand GPU provisioning, model loading, batching, quantization, and serving performance.

**Setup:**
- vLLM server serving an open-source model (Llama 3, Mistral, or similar)
- OpenAI-compatible API endpoint (vLLM provides this natively)
- Docker container for reproducible deployment
- Health check and monitoring endpoints
- GPU options: RunPod, Lambda Labs, or local GPU if available

**Key questions to answer through experimentation:**
- What's the minimum GPU needed for acceptable latency?
- How does quantization (4-bit, 8-bit) affect roadmap quality?
- What's the cost per roadmap vs Claude API?
- Can a 7B model produce usable roadmaps, or do we need 70B+?

---

### T55: VLLMClient Implementation

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S18 - Self-Hosted Models                                   |
| Priority    | P1 - High                                                  |
| Type        | Clients                                                    |
| Description | BaseAIClient adapter for vLLM-served models |

**Implementation:**
- New `VLLMClient(BaseAIClient)` in arcane-core
- Uses vLLM's OpenAI-compatible API (`/v1/chat/completions`)
- Structured output via instructor's OpenAI integration (vLLM supports function calling)
- `_is_rate_limit_error()` returns False (self-hosted, no rate limits)
- Connection validation via health check endpoint
- Configuration: `ARCANE_VLLM_URL`, `ARCANE_VLLM_MODEL`

**Add to model registry:**
```python
SUPPORTED_MODELS = {
    ...
    "local": ("vllm", "auto", "Self-hosted model via vLLM"),
}
```

---

### T56: Model Benchmarking

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S18 - Self-Hosted Models                                   |
| Priority    | P2 - Medium                                                |
| Type        | Testing                                                    |
| Description | Compare self-hosted model output quality against Claude and GPT |

**Benchmark script:**
- Use a fixed ProjectContext (e.g., the telchar project)
- Generate roadmaps with Claude Sonnet, Claude Opus, GPT-4o, and self-hosted model
- Compare: item count, hour estimates, description quality, claude_code_prompt usefulness
- Measure: latency per API call, total generation time, cost per roadmap
- Output: comparison report (markdown or HTML)

---

### T57: Billing Integration

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S19 - Launch Prep                                          |
| Priority    | P1 - High                                                  |
| Type        | Feature                                                    |
| Description | Stripe payments with plan tiers and usage tracking |

**Pricing model (decide later, but scaffold for):**
- **Free tier:** 1 project, 2 roadmaps, uses self-hosted model
- **Pro ($15-20/month):** Unlimited projects/roadmaps, Claude/GPT models, export to PM tools
- **Team ($30/user/month):** Collaboration, shared projects (Sprint 19)

**Implementation:** Stripe Checkout for subscriptions, webhook handler for payment events, usage metering for AI token consumption.

---

### T58: Team Collaboration

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S19 - Launch Prep                                          |
| Priority    | P1 - High                                                  |
| Type        | Feature                                                    |
| Description | Shared projects with role-based access and team invites |

**Features:**
- Teams with owner, admin, member roles
- Invite via email
- Shared projects visible to all team members
- Activity log (who generated, edited, exported)
- Optional: OAuth login (Google, GitHub) for easier team onboarding

---

### T59: Deployment Infrastructure

| Field       | Value                                                      |
| ----------- | ---------------------------------------------------------- |
| Sprint      | S19 - Launch Prep                                          |
| Priority    | P0 - Critical                                              |
| Type        | Infra                                                      |
| Description | Production deployment with Docker, CI/CD, monitoring |

**Components:**
- **Docker Compose:** Backend (FastAPI), Frontend (Next.js), PostgreSQL, Redis (for Arq), optional vLLM
- **CI/CD:** GitHub Actions — lint, test, build, deploy
- **Hosting:** Railway, Fly.io, or AWS ECS (pick based on cost at launch scale)
- **Monitoring:** Sentry for errors, basic health checks, log aggregation
- **Domain:** arcane.dev or similar
- **SSL:** Let's Encrypt via Caddy or cloud provider

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
- **Refactor:** Code restructuring
- **Backend:** FastAPI / server-side
- **Frontend:** React / client-side
- **Feature:** Product feature
- **Infra:** Infrastructure and deployment

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
├── __init__.py         # Package root (version only)
├── __main__.py         # Entry point
├── cli.py              # Typer CLI commands
└── core/               # Shared library (arcane-core)
    ├── clients/        # AI provider abstraction
    ├── config.py       # Settings with pydantic-settings
    ├── generators/     # Generation orchestration
    ├── items/          # Pydantic data models
    ├── models.py       # Model registry
    ├── project_management/ # PM tool exporters
    ├── questions/      # Discovery question system
    ├── storage/        # Save/load/resume
    ├── templates/      # Jinja2 prompt templates
    └── utils/          # ID generation, console helpers
```
