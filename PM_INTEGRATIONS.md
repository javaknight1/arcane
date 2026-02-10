# PM Tool Integration Mappings

This document defines how Arcane's roadmap data model maps to each project management tool's entity model, API specifics, and implementation notes for T28 (Linear), T29 (Jira), and T30 (Notion).

**Last Updated:** 2026-02-06

---

## Design Decisions

These decisions were made during planning and apply to all integrations:

1. **Status mapping: Native conversion per service.** Each PM client implements its own status mapping to the tool's native workflow states. No skipping — we always attempt to set the correct status.
2. **Estimates: Convert hours to points (1:1).** Points and hours are treated as equivalent. `estimated_hours=8` becomes `estimate=8` in Linear, `story_points=8` in Jira, `Estimated Points=8` in Notion.
3. **Linear Epics: Ignored.** Linear has no native Epic concept. Epics are flattened — stories are created directly under the Project (milestone). Epic metadata (name, goal) is not exported to Linear. This is a known limitation documented to the user.
4. **`claude_code_prompt`: Exported as a comment** on the task/issue in all three tools. Consistent, no custom field setup required, easy to copy-paste.
5. **`ExportResult`: Expanded** with `id_mapping`, `items_by_type`, and `warnings` fields for richer feedback.

---

## Arcane Data Model (Source of Truth)

For reference, here's what we're exporting:

```
Roadmap
  id, project_name, created_at, updated_at, context
  └── Milestone (BaseItem + goal, target_date)
       └── Epic (BaseItem + goal, prerequisites[])
            └── Story (BaseItem + acceptance_criteria[])
                 └── Task (BaseItem + estimated_hours, prerequisites[],
                           acceptance_criteria[], implementation_notes,
                           claude_code_prompt)

BaseItem: id, name, description, priority, status, labels[]
Priority: critical | high | medium | low
Status: not_started | in_progress | blocked | completed
```

---

## 1. Linear (T28) — GraphQL API

### Entity Mapping

| Arcane | Linear | Notes |
|--------|--------|-------|
| Roadmap | Initiative | Top-level container. Initiatives group Projects. |
| Milestone | Project | Projects are the main organizational unit. Each milestone becomes its own project. |
| Epic | _(not exported)_ | **Linear has no native Epic.** Epics are flattened — their child stories are created directly under the Project. |
| Story | Issue | Standard Linear issue. Linked to the Project (milestone). |
| Task | Sub-Issue | Child issues nested under the Story issue. |

### Field Mapping

| Arcane Field | Linear Field | Mapping Logic |
|---|---|---|
| `name` | `title` | Direct |
| `description` | `description` | Markdown — Linear supports full markdown natively |
| `priority` | `priority` | `critical→1(urgent)`, `high→2(high)`, `medium→3(medium)`, `low→4(low)` |
| `status` | `stateId` | Query team's `workflowStates`, then map by name: `not_started→"Todo"`, `in_progress→"In Progress"`, `blocked→"Todo"` (with "blocked" label), `completed→"Done"`. If exact match not found, fuzzy-match by state type: `started`, `unstarted`, `completed`. |
| `labels` | `labelIds` | Create-or-find labels by name |
| `estimated_hours` | `estimate` | Direct 1:1 as points (hours = points) |
| `prerequisites` | `relations` | Create "blocked by" issue relations |
| `acceptance_criteria` | Appended to `description` | No native field — append as markdown checklist in description |
| `implementation_notes` | Appended to `description` | Append below acceptance criteria |
| `claude_code_prompt` | Comment | Post as the first comment on the task issue |
| `goal` (Milestone) | Project `description` | Direct |
| `target_date` | `targetDate` on Project | Direct date mapping |

### Status Mapping Detail

Linear workflow states have a `type` field: `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled`. Strategy:

1. Query `workflowStates` for the team
2. First try exact name match (case-insensitive): "Todo", "In Progress", "Done"
3. If no exact match, fall back to state type: `not_started→unstarted`, `in_progress→started`, `completed→completed`
4. For `blocked`: set state to the `unstarted` type state, then add a "blocked" label

### API Details

- **Endpoint:** `https://api.linear.app/graphql`
- **Auth:** Bearer token in `Authorization` header
- **Rate limit:** 1,500 requests/hour (generous). Complexity-based limiting on queries.
- **Key mutations:** `projectCreate`, `issueCreate`, `issueLabelCreate`, `issueRelationCreate`, `commentCreate`
- **Pagination:** Cursor-based on queries

### Notes

- **Epic flattening:** Since epics are not exported, each story's description should include a note like "Epic: Authentication" so the context isn't completely lost.
- **Team selection:** User must specify which Linear team to create issues in. CLI flag: `--team`.

---

## 2. Jira (T29) — REST API v3

### Entity Mapping

| Arcane | Jira | Notes |
|--------|------|-------|
| Roadmap | Jira Project | Assumes project already exists. We create items within it. |
| Milestone | Version (Fix Version) | Versions are Jira's release/phase concept. Each milestone becomes a version. |
| Epic | Epic (issue type) | Native Jira concept. Requires the "Epic Name" custom field. |
| Story | Story (issue type) | Standard Jira issue type at hierarchy level 0. Linked to Epic via `epic` link. |
| Task | Sub-task (issue type) | Jira sub-tasks at hierarchy level -1. Nested under Story. |

### Field Mapping

| Arcane Field | Jira Field | Mapping Logic |
|---|---|---|
| `name` | `summary` | Direct |
| `description` | `description` (ADF) | **Must convert markdown → Atlassian Document Format (ADF)**. ADF is a JSON-based rich text format. |
| `priority` | `priority.id` | Must query available priorities first. Typically: `critical→1(Highest)`, `high→2(High)`, `medium→3(Medium)`, `low→4(Low)` |
| `status` | `transitions` | Cannot set status directly on create. Must: (1) create issue in initial state, (2) query transitions, (3) POST the appropriate transition. See status mapping detail below. |
| `labels` | `labels` | Direct — string array |
| `estimated_hours` | `story_points` (custom field) | Direct 1:1 as points (hours = points). Must discover the story points field ID via `GET /rest/api/3/field`. |
| `prerequisites` | `issuelinks` | Create "Blocks/Is blocked by" link type between issues |
| `acceptance_criteria` | Appended to `description` (ADF) | No native field — append as ADF bullet list in description |
| `implementation_notes` | Appended to `description` (ADF) | Append below acceptance criteria |
| `claude_code_prompt` | Comment | POST to `/rest/api/3/issue/{id}/comment` with ADF body |
| `goal` (Milestone) | Version `description` | Direct |
| `goal` (Epic) | `customfield_XXXXX` (Epic Name) or `description` | Epic Name field ID varies per Jira instance |
| `target_date` | Version `releaseDate` | Format: `"YYYY-MM-DD"` |

### Status Mapping Detail

Jira uses transitions, not direct status assignment. Strategy:

1. Create issue (lands in initial status, typically "To Do")
2. If desired status != initial status:
   a. `GET /rest/api/3/issue/{id}/transitions` — list available transitions
   b. Find transition whose `to.name` matches our target (case-insensitive)
   c. `POST /rest/api/3/issue/{id}/transitions` with the transition ID
3. Mapping: `not_started→"To Do"` (no-op, initial state), `in_progress→"In Progress"`, `blocked→"To Do"` (add "blocked" label, no standard blocked state), `completed→"Done"`
4. If target transition is not directly reachable from initial state, log a warning and skip

### API Details

- **Endpoint:** `https://{domain}.atlassian.net/rest/api/3/`
- **Auth:** Basic auth with email + API token (base64 encoded)
- **Rate limit:** ~100 requests/10 seconds for cloud. Varies by plan.
- **Key endpoints:**
  - `POST /rest/api/3/version` — create version (milestone)
  - `POST /rest/api/3/issue` — create issue (epic, story, task)
  - `POST /rest/api/3/issue/{id}/comment` — add comment
  - `POST /rest/api/3/issueLink` — create dependency link
  - `GET /rest/api/3/project/{key}` — get project metadata
  - `GET /rest/api/3/issue/createmeta` — get available issue types and fields
  - `GET /rest/api/3/issue/{id}/transitions` — get available transitions
  - `POST /rest/api/3/issue/{id}/transitions` — perform transition
- **Agile API:** `https://{domain}.atlassian.net/rest/agile/1.0/` for board/sprint operations

### Critical Concerns

- **ADF conversion:** Jira v3 API requires Atlassian Document Format for all rich text fields. Build a simple converter that handles: paragraphs, headings, bullet lists, code blocks. No need for full markdown parsing.
- **Epic link field:** The field name for linking stories to epics varies by Jira instance. Must discover it via `GET /rest/api/3/field` and find the field with `schema.custom = "com.pyxis.greenhopper.jira:gh-epic-link"`.
- **Issue type IDs:** Issue type names ("Epic", "Story", "Sub-task") map to IDs that vary per project. Must query `GET /rest/api/3/project/{key}` to get valid issue type IDs.
- **Project must exist:** We don't create the Jira project — user provides the project key.

---

## 3. Notion (T30) — REST API

### Entity Mapping

| Arcane | Notion | Notes |
|--------|--------|-------|
| Roadmap | Parent page | A top-level page containing all databases |
| Milestone | Database entry in "Milestones" database | Each level gets its own database for full view flexibility |
| Epic | Database entry in "Epics" database | Related to Milestones via relation property |
| Story | Database entry in "Stories" database | Related to Epics via relation property |
| Task | Database entry in "Tasks" database | Related to Stories via relation property |

### Field Mapping

| Arcane Field | Notion Property/Block | Mapping Logic |
|---|---|---|
| `name` | Page `title` property | Direct |
| `description` | Page content (paragraph blocks) | Notion pages have properties AND content blocks. Description goes in page body. |
| `priority` | `Select` property | Create select with options: Critical, High, Medium, Low |
| `status` | `Select` property named "Stage" | Notion's native `Status` type cannot be created via API. Use `Select` with options: Not Started, In Progress, Blocked, Completed. See status mapping detail below. |
| `labels` | `Multi-select` property | Direct mapping |
| `estimated_hours` | `Number` property named "Estimated Points" | Direct 1:1 as points (hours = points) |
| `prerequisites` | `Rich text` property | Task names listed (cross-DB self-referencing relations are complex) |
| `acceptance_criteria` | `to_do` blocks in page content | Render as checklist items in the page body |
| `implementation_notes` | `paragraph` blocks in page content | Render as paragraph in page body |
| `claude_code_prompt` | `toggle` block in page content | Collapsible block titled "Claude Code Prompt" with code block inside |
| `goal` | `Rich text` property | Direct |
| `target_date` | `Date` property | Direct |
| Parent-child relations | `Relation` property | Milestones↔Epics, Epics↔Stories, Stories↔Tasks as bidirectional relations |

### Status Mapping Detail

Using a `Select` property named "Stage" (not native `Status` which can't be created via API). Strategy:

1. Create the Select property with options: `Not Started`, `In Progress`, `Blocked`, `Completed`
2. When creating a page, set the Stage select value directly
3. Mapping: `not_started→"Not Started"`, `in_progress→"In Progress"`, `blocked→"Blocked"`, `completed→"Completed"`
4. This is the simplest of all three — direct select value assignment

### Database Schema

We create 4 databases on the parent page:

**Milestones Database:**
| Property | Type | Notes |
|---|---|---|
| Name | Title | Required |
| Goal | Rich text | |
| Target Date | Date | |
| Priority | Select | Critical/High/Medium/Low |
| Stage | Select | Not Started/In Progress/Blocked/Completed |
| Labels | Multi-select | |
| Estimated Points | Number | |

**Epics Database:**
| Property | Type | Notes |
|---|---|---|
| Name | Title | Required |
| Goal | Rich text | |
| Milestone | Relation → Milestones | |
| Priority | Select | |
| Stage | Select | |
| Labels | Multi-select | |
| Estimated Points | Number | |

**Stories Database:**
| Property | Type | Notes |
|---|---|---|
| Name | Title | Required |
| Epic | Relation → Epics | |
| Priority | Select | |
| Stage | Select | |
| Labels | Multi-select | |
| Estimated Points | Number | |

**Tasks Database:**
| Property | Type | Notes |
|---|---|---|
| Name | Title | Required |
| Story | Relation → Stories | |
| Priority | Select | |
| Stage | Select | |
| Labels | Multi-select | |
| Estimated Points | Number | Direct from field |
| Prerequisites | Rich text | Task names listed (cross-DB relations are complex) |

### API Details

- **Endpoint:** `https://api.notion.com/v1/`
- **Auth:** Bearer token in `Authorization` header. Also requires `Notion-Version: 2022-06-28` header.
- **Rate limit:** 3 requests/second. This is the tightest of all three tools. Must throttle carefully.
- **Key endpoints:**
  - `POST /v1/databases` — create database
  - `POST /v1/pages` — create page (database entry)
  - `PATCH /v1/blocks/{id}/children` — append content blocks to a page
  - `POST /v1/search` — find pages/databases
- **Block types:** `paragraph`, `heading_1/2/3`, `bulleted_list_item`, `to_do`, `toggle`, `code`, `divider`

### Critical Concerns

- **Rate limiting:** 3 req/sec means a roadmap with 100+ items needs careful throttling. A roadmap with 3 milestones, 9 epics, 27 stories, 81 tasks = 120 items = ~40 seconds minimum just for page creation, plus database creation and block appending.
- **Block append limits:** `PATCH /v1/blocks/{id}/children` accepts max 100 blocks per request.
- **Two-step page creation:** Create the page (with properties), then append content blocks. This doubles the API calls compared to Linear/Jira.
- **Parent page required:** User must provide a Notion page ID where databases will be created. The integration must have access to this page.

---

## Cross-Tool Feature Comparison

### Features All Three Support (Build Into Arcane)

| Feature | Linear | Jira | Notion | Arcane Action |
|---|---|---|---|---|
| Dependencies | Issue relations | Issue links | Relation properties | Export `prerequisites` as native relations |
| Labels/Tags | Labels | Labels | Multi-select | Direct from `BaseItem.labels` |
| Priority | 4 levels | 4+ levels | Select property | Direct from `Priority` enum |
| Status | Workflow states | Transitions | Select property | Native conversion per service |
| Estimates | Points (estimate) | Story points | Number property | 1:1 hours→points |
| Due dates | `dueDate` on issues | `duedate` field | Date property | **Add `due_date` to model** (future) |
| Assignees | `assigneeId` | `assignee` field | People property | **Add `assignee` to model** (future) |
| Rich text | Markdown | ADF (JSON) | Block-based | Need format conversion layer |
| Comments | Comments API | Comments API | Comment blocks | Export `claude_code_prompt` as comment |
| Hierarchy | Project→Issue→Sub-Issue | Version→Epic→Story→Sub-task | DB relations | Direct from our 4-level hierarchy |

### Tool-Specific Features (Future Development)

| Feature | Tool | Priority | Notes |
|---|---|---|---|
| Sprints/Cycles | Linear, Jira | P2 | Could auto-slice milestones into 2-week sprints |
| Components | Jira | P3 | Could derive from `tech_stack` or `labels` |
| Workflows | Jira | P3 | Complex — each project has custom workflow |
| Board views | Jira, Notion | N/A | Automatic from data — no export needed |
| Timeline views | Linear, Jira | P2 | Need `start_date` + `end_date` on items |
| Formulas/Rollups | Notion | P3 | Auto-create rollup for estimated points |
| Templates | Notion | P3 | Create template databases Arcane populates |

---

## Implementation Order

1. **Linear (T28)** — Cleanest API (GraphQL), best docs, most straightforward mapping
2. **Jira (T29)** — Hardest due to ADF format, dynamic field discovery, status transitions
3. **Notion (T30)** — Medium difficulty but tight rate limits require careful throttling

---

## Shared Infrastructure

All three integrations need:

1. **`BasePMClient`** — Already exists with `export()`, `validate_credentials()`, `name`. Add `_request_with_backoff()` for HTTP retries.
2. **Rate limiting** — Reuse the backoff pattern from `BaseAIClient._call_with_backoff()`, adapted for HTTP APIs. Notion additionally needs a proactive rate limiter (semaphore + sleep) to stay under 3 req/sec.
3. **Progress display** — Rich progress bar showing export progress (items created / total)
4. **Credential validation** — Each client validates before starting export
5. **Error recovery** — If export fails mid-way, report what was created and what remains via `ExportResult.warnings`
6. **ID mapping** — Track `arcane_id → pm_tool_id` mapping for dependency resolution (must create items before linking dependencies). Returned in `ExportResult.id_mapping`.
7. **Description builders** — Per-tool content formatter: Linear (markdown passthrough), Jira (ADF builder), Notion (block builder). Each composites `description`, `acceptance_criteria`, `implementation_notes` into the tool's native format.
