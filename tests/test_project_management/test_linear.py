"""Tests for Linear integration."""

import pytest

from arcane.items import Priority, Status
from arcane.project_management import LinearClient
from arcane.project_management.linear import LinearAPIError


class MockGraphQL:
    """Mock for LinearClient._graphql that returns canned responses."""

    def __init__(self):
        self.calls: list[tuple[str, dict | None]] = []
        self._issue_counter = 0
        self._project_counter = 0

    async def __call__(self, query: str, variables: dict | None = None) -> dict:
        self.calls.append((query, variables))

        if "workflowStates" in query:
            return {
                "workflowStates": {
                    "nodes": [
                        {"id": "state-todo", "name": "Todo", "type": "unstarted"},
                        {"id": "state-progress", "name": "In Progress", "type": "started"},
                        {"id": "state-done", "name": "Done", "type": "completed"},
                    ]
                }
            }
        elif "issueLabels" in query and "issueLabelCreate" not in query:
            return {"issueLabels": {"nodes": []}}
        elif "issueLabelCreate" in query:
            name = variables["input"]["name"]
            return {
                "issueLabelCreate": {
                    "issueLabel": {"id": f"label-{name}"},
                    "success": True,
                }
            }
        elif "projectCreate" in query:
            self._project_counter += 1
            return {
                "projectCreate": {
                    "project": {
                        "id": f"proj-{self._project_counter:03d}",
                        "url": f"https://linear.app/team/project/proj-{self._project_counter:03d}",
                    },
                    "success": True,
                }
            }
        elif "issueCreate" in query:
            self._issue_counter += 1
            return {
                "issueCreate": {
                    "issue": {
                        "id": f"issue-uuid-{self._issue_counter:03d}",
                        "identifier": f"TEAM-{self._issue_counter}",
                        "url": f"https://linear.app/team/issue/TEAM-{self._issue_counter}",
                    },
                    "success": True,
                }
            }
        elif "commentCreate" in query:
            return {"commentCreate": {"success": True}}
        elif "issueRelationCreate" in query:
            return {"issueRelationCreate": {"success": True}}
        elif "documentCreate" in query:
            return {"documentCreate": {"success": True}}

        return {}


@pytest.fixture
def linear_client():
    """Create a LinearClient for testing."""
    return LinearClient(api_key="lin_test_key")


@pytest.fixture
def mock_gql(linear_client):
    """Patch _graphql with MockGraphQL and return the mock."""
    mock = MockGraphQL()
    linear_client._graphql = mock
    return mock


class TestBuildDescription:
    """Tests for LinearClient._build_description."""

    def test_simple_description(self):
        """Plain description without extras."""
        result = LinearClient._build_description("A simple description")
        assert result == "A simple description"

    def test_with_epic_name(self):
        """Prepends epic name to description."""
        result = LinearClient._build_description("Desc", epic_name="Auth")
        assert "**Epic:** Auth" in result
        assert "Desc" in result

    def test_with_acceptance_criteria(self):
        """Appends acceptance criteria as checklist."""
        result = LinearClient._build_description(
            "Desc", acceptance_criteria=["Form renders", "Validates input"]
        )
        assert "## Acceptance Criteria" in result
        assert "- [ ] Form renders" in result
        assert "- [ ] Validates input" in result

    def test_with_implementation_notes(self):
        """Appends implementation notes section."""
        result = LinearClient._build_description(
            "Desc", implementation_notes="Use React Hook Form"
        )
        assert "## Implementation Notes" in result
        assert "Use React Hook Form" in result

    def test_with_all_sections(self):
        """All optional sections present."""
        result = LinearClient._build_description(
            "Main desc",
            acceptance_criteria=["Criterion 1"],
            implementation_notes="Some notes",
            epic_name="My Epic",
        )
        assert "**Epic:** My Epic" in result
        assert "Main desc" in result
        assert "## Acceptance Criteria" in result
        assert "- [ ] Criterion 1" in result
        assert "## Implementation Notes" in result
        assert "Some notes" in result

    def test_empty_acceptance_criteria(self):
        """Empty acceptance criteria list is ignored."""
        result = LinearClient._build_description("Desc", acceptance_criteria=[])
        assert "Acceptance Criteria" not in result


class TestFetchWorkflowStates:
    """Tests for status mapping from Linear workflow states."""

    @pytest.mark.asyncio
    async def test_maps_by_name(self, linear_client, mock_gql):
        """Maps status by exact name match."""
        result = await linear_client._fetch_workflow_states("team-123")
        assert result[Status.NOT_STARTED] == "state-todo"
        assert result[Status.IN_PROGRESS] == "state-progress"
        assert result[Status.COMPLETED] == "state-done"

    @pytest.mark.asyncio
    async def test_blocked_maps_to_todo(self, linear_client, mock_gql):
        """BLOCKED status maps to Todo state."""
        result = await linear_client._fetch_workflow_states("team-123")
        assert result[Status.BLOCKED] == "state-todo"

    @pytest.mark.asyncio
    async def test_fallback_to_type(self, linear_client):
        """Falls back to state type when names don't match."""
        async def custom_gql(query, variables=None):
            return {
                "workflowStates": {
                    "nodes": [
                        {"id": "state-1", "name": "Backlog", "type": "unstarted"},
                        {"id": "state-2", "name": "Working", "type": "started"},
                        {"id": "state-3", "name": "Shipped", "type": "completed"},
                    ]
                }
            }

        linear_client._graphql = custom_gql
        result = await linear_client._fetch_workflow_states("team-123")
        assert result[Status.NOT_STARTED] == "state-1"
        assert result[Status.IN_PROGRESS] == "state-2"
        assert result[Status.COMPLETED] == "state-3"

    @pytest.mark.asyncio
    async def test_missing_state_omitted(self, linear_client):
        """Status with no matching state is omitted from mapping."""
        async def partial_gql(query, variables=None):
            return {
                "workflowStates": {
                    "nodes": [
                        {"id": "state-1", "name": "Todo", "type": "unstarted"},
                    ]
                }
            }

        linear_client._graphql = partial_gql
        result = await linear_client._fetch_workflow_states("team-123")
        assert Status.NOT_STARTED in result
        assert Status.IN_PROGRESS not in result


class TestResolveLabels:
    """Tests for label resolution."""

    @pytest.mark.asyncio
    async def test_creates_missing_label(self, linear_client, mock_gql):
        """Creates a label that doesn't exist in cache."""
        cache: dict[str, str] = {}
        ids = await linear_client._resolve_label_ids("team-123", ["urgent"], cache)
        assert ids == ["label-urgent"]
        assert cache["urgent"] == "label-urgent"

    @pytest.mark.asyncio
    async def test_uses_cache(self, linear_client, mock_gql):
        """Uses cached label ID instead of creating."""
        cache = {"urgent": "cached-id"}
        ids = await linear_client._resolve_label_ids("team-123", ["urgent"], cache)
        assert ids == ["cached-id"]
        # No issueLabelCreate call
        assert not any("issueLabelCreate" in call[0] for call in mock_gql.calls)

    @pytest.mark.asyncio
    async def test_mixed_cached_and_new(self, linear_client, mock_gql):
        """Mix of cached and new labels."""
        cache = {"existing": "existing-id"}
        ids = await linear_client._resolve_label_ids(
            "team-123", ["existing", "new-label"], cache
        )
        assert ids == ["existing-id", "label-new-label"]

    @pytest.mark.asyncio
    async def test_empty_labels(self, linear_client, mock_gql):
        """Empty label list returns empty."""
        ids = await linear_client._resolve_label_ids("team-123", [], {})
        assert ids == []


class TestLinearExport:
    """Tests for the full export flow."""

    @pytest.mark.asyncio
    async def test_requires_team_id(self, linear_client, sample_roadmap):
        """Export raises ValueError without team_id."""
        with pytest.raises(ValueError, match="team_id is required"):
            await linear_client.export(sample_roadmap)

    @pytest.mark.asyncio
    async def test_export_success(self, linear_client, mock_gql, sample_roadmap):
        """Export succeeds with mocked API."""
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.success is True
        assert result.target == "Linear"

    @pytest.mark.asyncio
    async def test_export_item_counts(self, linear_client, mock_gql, sample_roadmap):
        """Correct item count breakdown."""
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        # 1 milestone(project) + 1 story(issue) + 2 tasks(sub-issues)
        assert result.items_created == 4
        assert result.items_by_type == {
            "milestones": 1,
            "stories": 1,
            "tasks": 2,
        }

    @pytest.mark.asyncio
    async def test_export_id_mapping(self, linear_client, mock_gql, sample_roadmap):
        """ID mapping tracks all created items."""
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        # Milestone mapped to project UUID
        assert result.id_mapping["milestone-001"] == "proj-001"
        # Story mapped to issue identifier
        assert result.id_mapping["story-001"] == "TEAM-1"
        # Tasks mapped to sub-issue identifiers
        assert result.id_mapping["task-001"] == "TEAM-2"
        assert result.id_mapping["task-002"] == "TEAM-3"

    @pytest.mark.asyncio
    async def test_export_url(self, linear_client, mock_gql, sample_roadmap):
        """ExportResult includes project URL."""
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.url is not None
        assert "linear.app" in result.url

    @pytest.mark.asyncio
    async def test_export_no_warnings(self, linear_client, mock_gql, sample_roadmap):
        """Clean export produces no warnings."""
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.warnings == []

    @pytest.mark.asyncio
    async def test_epic_not_in_item_types(self, linear_client, mock_gql, sample_roadmap):
        """Epics are not exported as separate items."""
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert "epics" not in result.items_by_type

    @pytest.mark.asyncio
    async def test_epic_name_in_story_description(self, linear_client, mock_gql, sample_roadmap):
        """Story descriptions include epic name context."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        issue_creates = [
            (q, v) for q, v in mock_gql.calls if "issueCreate" in q
        ]
        # First issueCreate is the story
        story_input = issue_creates[0][1]["input"]
        assert "**Epic:** Authentication" in story_input["description"]

    @pytest.mark.asyncio
    async def test_story_has_project_id(self, linear_client, mock_gql, sample_roadmap):
        """Stories are linked to the milestone project."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        issue_creates = [
            (q, v) for q, v in mock_gql.calls if "issueCreate" in q
        ]
        story_input = issue_creates[0][1]["input"]
        assert story_input["projectId"] == "proj-001"

    @pytest.mark.asyncio
    async def test_task_has_parent_id(self, linear_client, mock_gql, sample_roadmap):
        """Tasks are created as sub-issues of their story."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        issue_creates = [
            (q, v) for q, v in mock_gql.calls if "issueCreate" in q
        ]
        # Second and third issueCreates are tasks
        task_input = issue_creates[1][1]["input"]
        assert task_input["parentId"] == "issue-uuid-001"  # story UUID

    @pytest.mark.asyncio
    async def test_priority_mapping(self, linear_client, mock_gql, sample_roadmap):
        """Priorities are mapped to Linear integer values."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        issue_creates = [
            (q, v) for q, v in mock_gql.calls if "issueCreate" in q
        ]
        # Story priority is CRITICAL → 1
        assert issue_creates[0][1]["input"]["priority"] == 1
        # task-001 priority is HIGH → 2
        assert issue_creates[1][1]["input"]["priority"] == 2
        # task-002 priority is MEDIUM → 3
        assert issue_creates[2][1]["input"]["priority"] == 3

    @pytest.mark.asyncio
    async def test_status_state_id(self, linear_client, mock_gql, sample_roadmap):
        """Status is mapped to workflow state ID."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        issue_creates = [
            (q, v) for q, v in mock_gql.calls if "issueCreate" in q
        ]
        # All items are NOT_STARTED → "state-todo"
        assert issue_creates[0][1]["input"]["stateId"] == "state-todo"

    @pytest.mark.asyncio
    async def test_estimate_set(self, linear_client, mock_gql, sample_roadmap):
        """Estimated hours are passed as estimate points."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        issue_creates = [
            (q, v) for q, v in mock_gql.calls if "issueCreate" in q
        ]
        # Story estimate = sum of tasks (4 + 2 = 6)
        assert issue_creates[0][1]["input"]["estimate"] == 6
        # task-001 estimate = 4
        assert issue_creates[1][1]["input"]["estimate"] == 4
        # task-002 estimate = 2
        assert issue_creates[2][1]["input"]["estimate"] == 2


class TestLinearExportProgress:
    """Tests for progress callback during export."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self, linear_client, mock_gql, sample_roadmap):
        """Progress callback receives all items."""
        calls: list[tuple[str, str]] = []

        def callback(item_type: str, item_name: str):
            calls.append((item_type, item_name))

        await linear_client.export(
            sample_roadmap, team_id="team-123", progress_callback=callback
        )
        assert len(calls) == 4
        assert calls[0] == ("Project", "MVP")
        assert calls[1] == ("Issue", "User Login")
        assert calls[2][0] == "Sub-Issue"
        assert calls[3][0] == "Sub-Issue"

    @pytest.mark.asyncio
    async def test_export_without_callback(self, linear_client, mock_gql, sample_roadmap):
        """Export works when progress_callback is None."""
        result = await linear_client.export(
            sample_roadmap, team_id="team-123", progress_callback=None
        )
        assert result.success is True


class TestLinearExportRelations:
    """Tests for prerequisite relation creation."""

    @pytest.mark.asyncio
    async def test_creates_prerequisite_relations(self, linear_client, mock_gql, sample_roadmap):
        """task-002 prerequisite on task-001 creates a blocks relation."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        relation_calls = [
            (q, v) for q, v in mock_gql.calls if "issueRelationCreate" in q
        ]
        assert len(relation_calls) == 1
        relation_input = relation_calls[0][1]["input"]
        assert relation_input["type"] == "blocks"
        # task-001 (blocker) UUID = issue-uuid-002, task-002 (blocked) UUID = issue-uuid-003
        assert relation_input["issueId"] == "issue-uuid-002"
        assert relation_input["relatedIssueId"] == "issue-uuid-003"

    @pytest.mark.asyncio
    async def test_missing_prerequisite_adds_warning(self, linear_client, mock_gql, sample_roadmap):
        """Missing prerequisite ID generates a warning."""
        # Add a nonexistent prerequisite
        sample_roadmap.milestones[0].epics[0].stories[0].tasks[0].prerequisites = [
            "nonexistent-task"
        ]
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.success is True
        assert any("nonexistent-task" in w for w in result.warnings)


class TestLinearExportComments:
    """Tests for claude_code_prompt comment creation."""

    @pytest.mark.asyncio
    async def test_creates_comments_for_tasks(self, linear_client, mock_gql, sample_roadmap):
        """Comments are created for tasks with claude_code_prompt."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        comment_calls = [
            (q, v) for q, v in mock_gql.calls if "commentCreate" in q
        ]
        assert len(comment_calls) == 2
        assert "Claude Code Prompt" in comment_calls[0][1]["input"]["body"]

    @pytest.mark.asyncio
    async def test_no_comment_for_empty_prompt(self, linear_client, mock_gql, sample_roadmap):
        """No comment created when claude_code_prompt is empty."""
        for task in sample_roadmap.milestones[0].epics[0].stories[0].tasks:
            task.claude_code_prompt = ""
        await linear_client.export(sample_roadmap, team_id="team-123")
        comment_calls = [
            (q, v) for q, v in mock_gql.calls if "commentCreate" in q
        ]
        assert len(comment_calls) == 0

    @pytest.mark.asyncio
    async def test_comment_error_adds_warning(self, linear_client, sample_roadmap):
        """Comment failure adds warning, doesn't fail export."""
        mock = MockGraphQL()

        async def gql_with_comment_error(query, variables=None):
            if "commentCreate" in query:
                raise LinearAPIError([{"message": "Comment failed"}])
            return await mock(query, variables)

        linear_client._graphql = gql_with_comment_error
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.success is True
        assert len(result.warnings) >= 2
        assert any("comment" in w.lower() for w in result.warnings)


class TestLinearExportDocuments:
    """Tests for documentation page creation."""

    @pytest.mark.asyncio
    async def test_creates_four_doc_pages(self, linear_client, mock_gql, sample_roadmap):
        """Creates all 4 documentation pages."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        doc_calls = [
            (q, v) for q, v in mock_gql.calls if "documentCreate" in q
        ]
        assert len(doc_calls) == 4
        titles = [c[1]["input"]["title"] for c in doc_calls]
        assert "Project Overview" in titles
        assert "Requirements" in titles
        assert "Technical Decisions" in titles
        assert "Team & Constraints" in titles

    @pytest.mark.asyncio
    async def test_docs_linked_to_first_project(self, linear_client, mock_gql, sample_roadmap):
        """Documents are associated with the first project."""
        await linear_client.export(sample_roadmap, team_id="team-123")
        doc_calls = [
            (q, v) for q, v in mock_gql.calls if "documentCreate" in q
        ]
        for _, v in doc_calls:
            assert v["input"]["projectId"] == "proj-001"

    @pytest.mark.asyncio
    async def test_doc_error_adds_warning(self, linear_client, sample_roadmap):
        """Document creation failure adds warning."""
        mock = MockGraphQL()

        async def gql_with_doc_error(query, variables=None):
            if "documentCreate" in query:
                raise LinearAPIError([{"message": "Doc creation failed"}])
            return await mock(query, variables)

        linear_client._graphql = gql_with_doc_error
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.success is True
        assert len(result.warnings) == 4  # All 4 docs failed
        assert any("document" in w.lower() for w in result.warnings)


class TestLinearExportErrors:
    """Tests for error handling during export."""

    @pytest.mark.asyncio
    async def test_api_error_returns_failure(self, linear_client, sample_roadmap):
        """Fatal API error returns ExportResult with success=False."""

        async def failing_gql(query, variables=None):
            raise LinearAPIError([{"message": "Rate limited"}])

        linear_client._graphql = failing_gql
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.success is False
        assert "Rate limited" in result.errors[0]

    @pytest.mark.asyncio
    async def test_partial_failure_reports_created_items(self, linear_client, sample_roadmap):
        """Mid-export failure reports items created before the error."""
        mock = MockGraphQL()
        call_count = 0

        async def fail_on_third_issue(query, variables=None):
            nonlocal call_count
            if "issueCreate" in query:
                call_count += 1
                if call_count >= 3:
                    raise LinearAPIError([{"message": "Server error"}])
            return await mock(query, variables)

        linear_client._graphql = fail_on_third_issue
        result = await linear_client.export(sample_roadmap, team_id="team-123")
        assert result.success is False
        # Should have created project + story + first task before failure
        assert result.items_created >= 3


class TestLinearAPIError:
    """Tests for the LinearAPIError exception."""

    def test_single_error(self):
        """Formats single error message."""
        err = LinearAPIError([{"message": "Not found"}])
        assert "Not found" in str(err)
        assert len(err.errors) == 1

    def test_multiple_errors(self):
        """Formats multiple error messages."""
        err = LinearAPIError([
            {"message": "Error 1"},
            {"message": "Error 2"},
        ])
        msg = str(err)
        assert "Error 1" in msg
        assert "Error 2" in msg

    def test_error_without_message(self):
        """Handles error dict without message key."""
        err = LinearAPIError([{"code": "UNKNOWN"}])
        assert "UNKNOWN" in str(err)
