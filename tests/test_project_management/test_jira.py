"""Tests for Jira Cloud integration."""

import pytest

from arcane.core.items import Priority, Status
from arcane.core.project_management import JiraClient
from arcane.core.project_management.jira import JiraAPIError, PRIORITY_NAME_MAP, STATUS_TARGET_MAP


class MockJiraAPI:
    """Mock for JiraClient._request that returns canned REST responses."""

    def __init__(self):
        self.calls: list[tuple[str, str, dict | None]] = []
        self._issue_counter = 0
        self._version_counter = 0

    async def __call__(
        self, method: str, endpoint: str, json: dict | None = None
    ) -> dict:
        self.calls.append((method, endpoint, json))

        # GET /project/{key}
        if method == "GET" and endpoint.startswith("/project/"):
            return {
                "id": "10001",
                "key": "PROJ",
                "issueTypes": [
                    {"id": "10000", "name": "Epic"},
                    {"id": "10001", "name": "Story"},
                    {"id": "10002", "name": "Sub-task"},
                    {"id": "10003", "name": "Bug"},
                ],
            }

        # GET /field
        if method == "GET" and endpoint == "/field":
            return [
                {
                    "id": "customfield_10016",
                    "name": "Story Points",
                    "schema": {
                        "custom": "com.atlassian.jira.plugin.system.customfieldtypes:float"
                    },
                },
                {
                    "id": "customfield_10014",
                    "name": "Epic Link",
                    "schema": {
                        "custom": "com.pyxis.greenhopper.jira:gh-epic-link"
                    },
                },
                {
                    "id": "summary",
                    "name": "Summary",
                    "schema": {},
                },
            ]

        # GET /priority
        if method == "GET" and endpoint == "/priority":
            return [
                {"id": "1", "name": "Highest"},
                {"id": "2", "name": "High"},
                {"id": "3", "name": "Medium"},
                {"id": "4", "name": "Low"},
                {"id": "5", "name": "Lowest"},
            ]

        # POST /version
        if method == "POST" and endpoint == "/version":
            self._version_counter += 1
            return {
                "id": f"ver-{self._version_counter:03d}",
                "name": json.get("name", ""),
                "self": f"https://test.atlassian.net/rest/api/3/version/ver-{self._version_counter:03d}",
            }

        # POST /issue
        if method == "POST" and endpoint == "/issue":
            self._issue_counter += 1
            key = f"PROJ-{self._issue_counter}"
            return {
                "id": f"issue-{self._issue_counter:03d}",
                "key": key,
                "self": f"https://test.atlassian.net/rest/api/3/issue/{key}",
            }

        # GET /issue/{key}/transitions
        if method == "GET" and "/transitions" in endpoint:
            return {
                "transitions": [
                    {"id": "11", "name": "To Do", "to": {"name": "To Do"}},
                    {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}},
                    {"id": "31", "name": "Done", "to": {"name": "Done"}},
                ]
            }

        # POST /issue/{key}/transitions
        if method == "POST" and "/transitions" in endpoint:
            return {}

        # POST /issueLink
        if method == "POST" and endpoint == "/issueLink":
            return {}

        # POST /issue/{key}/comment
        if method == "POST" and "/comment" in endpoint:
            return {"id": "comment-001"}

        return {}


@pytest.fixture
def jira_client():
    """Create a JiraClient for testing."""
    return JiraClient(
        domain="test.atlassian.net",
        email="user@example.com",
        api_token="token123",
    )


@pytest.fixture
def mock_api(jira_client):
    """Patch _request with MockJiraAPI and return the mock."""
    mock = MockJiraAPI()
    jira_client._request = mock
    return mock


class TestADFBuilder:
    """Tests for ADF document format builders."""

    def test_adf_paragraph(self):
        """Creates valid ADF paragraph node."""
        result = JiraClient._adf_paragraph("Hello world")
        assert result["type"] == "paragraph"
        assert result["content"][0]["text"] == "Hello world"

    def test_adf_heading(self):
        """Creates valid ADF heading node with level."""
        result = JiraClient._adf_heading("Title", level=3)
        assert result["type"] == "heading"
        assert result["attrs"]["level"] == 3
        assert result["content"][0]["text"] == "Title"

    def test_adf_bullet_list(self):
        """Creates valid ADF bullet list node."""
        result = JiraClient._adf_bullet_list(["Item 1", "Item 2"])
        assert result["type"] == "bulletList"
        assert len(result["content"]) == 2
        assert result["content"][0]["type"] == "listItem"
        # Each list item contains a paragraph with text
        para = result["content"][0]["content"][0]
        assert para["type"] == "paragraph"
        assert para["content"][0]["text"] == "Item 1"

    def test_adf_code_block(self):
        """Creates valid ADF code block node."""
        result = JiraClient._adf_code_block("print('hello')", "python")
        assert result["type"] == "codeBlock"
        assert result["attrs"]["language"] == "python"
        assert result["content"][0]["text"] == "print('hello')"

    def test_adf_rule(self):
        """Creates valid ADF horizontal rule."""
        result = JiraClient._adf_rule()
        assert result["type"] == "rule"

    def test_build_adf_description_full(self):
        """Builds complete ADF description with all sections."""
        result = JiraClient._build_adf_description(
            "Main description",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            implementation_notes="Use React",
            goal="Build auth system",
        )
        assert result["type"] == "doc"
        assert result["version"] == 1
        content = result["content"]
        # Should contain: heading(Goal), paragraph(goal text), rule,
        # paragraph(desc), rule, heading(AC), bullet list, rule,
        # heading(Notes), paragraph(notes)
        types = [node["type"] for node in content]
        assert "heading" in types
        assert "paragraph" in types
        assert "bulletList" in types
        assert "rule" in types

    def test_build_adf_description_simple(self):
        """Builds minimal ADF description with just text."""
        result = JiraClient._build_adf_description("Just a description")
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "paragraph"
        assert result["content"][0]["content"][0]["text"] == "Just a description"


class TestDiscoverProject:
    """Tests for project discovery."""

    @pytest.mark.asyncio
    async def test_discovers_issue_types(self, jira_client, mock_api):
        """Discovers all required issue type IDs."""
        await jira_client._discover_project("PROJ")
        assert jira_client._issue_type_ids["epic"] == "10000"
        assert jira_client._issue_type_ids["story"] == "10001"
        assert jira_client._issue_type_ids["sub-task"] == "10002"

    @pytest.mark.asyncio
    async def test_missing_issue_type_raises(self, jira_client):
        """Raises JiraAPIError when required issue type is missing."""

        async def partial_project(method, endpoint, json=None):
            return {
                "id": "10001",
                "key": "PROJ",
                "issueTypes": [
                    {"id": "10000", "name": "Epic"},
                    {"id": "10001", "name": "Story"},
                    # Missing Sub-task
                ],
            }

        jira_client._request = partial_project
        with pytest.raises(JiraAPIError, match="sub-task.*not found"):
            await jira_client._discover_project("PROJ")

    @pytest.mark.asyncio
    async def test_subtask_alternative_name(self, jira_client):
        """Accepts 'subtask' as alternative to 'sub-task'."""

        async def alt_project(method, endpoint, json=None):
            return {
                "id": "10001",
                "key": "PROJ",
                "issueTypes": [
                    {"id": "10000", "name": "Epic"},
                    {"id": "10001", "name": "Story"},
                    {"id": "10002", "name": "Subtask"},
                ],
            }

        jira_client._request = alt_project
        await jira_client._discover_project("PROJ")
        assert jira_client._issue_type_ids["sub-task"] == "10002"


class TestDiscoverFields:
    """Tests for custom field discovery."""

    @pytest.mark.asyncio
    async def test_finds_story_points(self, jira_client, mock_api):
        """Discovers story points custom field ID."""
        await jira_client._discover_fields()
        assert jira_client._story_points_field == "customfield_10016"

    @pytest.mark.asyncio
    async def test_finds_epic_link(self, jira_client, mock_api):
        """Discovers epic link custom field ID."""
        await jira_client._discover_fields()
        assert jira_client._epic_link_field == "customfield_10014"

    @pytest.mark.asyncio
    async def test_missing_field_warning(self, jira_client):
        """Warns when custom fields are not found."""

        async def no_custom_fields(method, endpoint, json=None):
            return [
                {"id": "summary", "name": "Summary", "schema": {}},
            ]

        jira_client._request = no_custom_fields
        warnings = await jira_client._discover_fields()
        assert any("Story Points" in w for w in warnings)
        assert any("Epic Link" in w for w in warnings)


class TestDiscoverPriorities:
    """Tests for priority discovery."""

    @pytest.mark.asyncio
    async def test_maps_all_priorities(self, jira_client, mock_api):
        """Maps all arcane priorities to Jira priority IDs."""
        await jira_client._discover_priorities()
        assert jira_client._priority_ids["Highest"] == "1"
        assert jira_client._priority_ids["High"] == "2"
        assert jira_client._priority_ids["Medium"] == "3"
        assert jira_client._priority_ids["Low"] == "4"

    @pytest.mark.asyncio
    async def test_missing_priority_warning(self, jira_client):
        """Warns when expected priority not found."""

        async def partial_priorities(method, endpoint, json=None):
            return [
                {"id": "1", "name": "Highest"},
                {"id": "2", "name": "High"},
                # Missing Medium and Low
            ]

        jira_client._request = partial_priorities
        warnings = await jira_client._discover_priorities()
        assert any("Medium" in w for w in warnings)
        assert any("Low" in w for w in warnings)


class TestJiraExport:
    """Tests for the full export flow."""

    @pytest.mark.asyncio
    async def test_requires_project_key(self, jira_client, sample_roadmap):
        """Export raises ValueError without project_key."""
        with pytest.raises(ValueError, match="project_key is required"):
            await jira_client.export(sample_roadmap)

    @pytest.mark.asyncio
    async def test_export_success(self, jira_client, mock_api, sample_roadmap):
        """Export succeeds with mocked API."""
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        assert result.success is True
        assert result.target == "Jira Cloud"

    @pytest.mark.asyncio
    async def test_export_item_counts(self, jira_client, mock_api, sample_roadmap):
        """Correct item count breakdown."""
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        # 1 milestone(version) + 1 epic + 1 story + 2 tasks
        assert result.items_created == 5
        assert result.items_by_type == {
            "milestones": 1,
            "epics": 1,
            "stories": 1,
            "tasks": 2,
        }

    @pytest.mark.asyncio
    async def test_export_id_mapping(self, jira_client, mock_api, sample_roadmap):
        """ID mapping tracks all created items."""
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        # Milestone mapped to version name
        assert "milestone-001" in result.id_mapping
        # Epic mapped to issue key
        assert result.id_mapping["epic-001"] == "PROJ-1"
        # Story mapped to issue key
        assert result.id_mapping["story-001"] == "PROJ-2"
        # Tasks mapped to issue keys
        assert result.id_mapping["task-001"] == "PROJ-3"
        assert result.id_mapping["task-002"] == "PROJ-4"

    @pytest.mark.asyncio
    async def test_export_url(self, jira_client, mock_api, sample_roadmap):
        """ExportResult includes browsable URL."""
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        assert result.url is not None
        assert "test.atlassian.net" in result.url
        assert "PROJ-1" in result.url

    @pytest.mark.asyncio
    async def test_versions_created(self, jira_client, mock_api, sample_roadmap):
        """Milestones create Jira Versions."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        version_calls = [
            (m, e, j) for m, e, j in mock_api.calls
            if m == "POST" and e == "/version"
        ]
        assert len(version_calls) == 1
        assert version_calls[0][2]["name"] == "MVP"

    @pytest.mark.asyncio
    async def test_epics_have_fix_versions(self, jira_client, mock_api, sample_roadmap):
        """Epics are linked to milestone via fixVersions."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        issue_calls = [
            (m, e, j) for m, e, j in mock_api.calls
            if m == "POST" and e == "/issue"
        ]
        # First issue is Epic
        epic_fields = issue_calls[0][2]["fields"]
        assert epic_fields["fixVersions"] == [{"id": "ver-001"}]

    @pytest.mark.asyncio
    async def test_stories_have_epic_link(self, jira_client, mock_api, sample_roadmap):
        """Stories are linked to epics via epic link custom field."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        issue_calls = [
            (m, e, j) for m, e, j in mock_api.calls
            if m == "POST" and e == "/issue"
        ]
        # Second issue is Story
        story_fields = issue_calls[1][2]["fields"]
        assert story_fields["customfield_10014"] == "PROJ-1"  # epic key

    @pytest.mark.asyncio
    async def test_subtasks_have_parent(self, jira_client, mock_api, sample_roadmap):
        """Sub-tasks are linked to story as parent."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        issue_calls = [
            (m, e, j) for m, e, j in mock_api.calls
            if m == "POST" and e == "/issue"
        ]
        # Third and fourth issues are tasks
        task_fields = issue_calls[2][2]["fields"]
        assert task_fields["parent"] == {"key": "PROJ-2"}  # story key

    @pytest.mark.asyncio
    async def test_priorities_mapped(self, jira_client, mock_api, sample_roadmap):
        """Priorities are mapped to Jira priority IDs."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        issue_calls = [
            (m, e, j) for m, e, j in mock_api.calls
            if m == "POST" and e == "/issue"
        ]
        # Epic is CRITICAL -> Highest -> id "1"
        assert issue_calls[0][2]["fields"]["priority"] == {"id": "1"}
        # Story is CRITICAL -> Highest -> id "1"
        assert issue_calls[1][2]["fields"]["priority"] == {"id": "1"}
        # task-001 is HIGH -> High -> id "2"
        assert issue_calls[2][2]["fields"]["priority"] == {"id": "2"}
        # task-002 is MEDIUM -> Medium -> id "3"
        assert issue_calls[3][2]["fields"]["priority"] == {"id": "3"}

    @pytest.mark.asyncio
    async def test_story_points_set(self, jira_client, mock_api, sample_roadmap):
        """Estimated hours are set as story points."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        issue_calls = [
            (m, e, j) for m, e, j in mock_api.calls
            if m == "POST" and e == "/issue"
        ]
        # task-001 estimated_hours = 4
        assert issue_calls[2][2]["fields"]["customfield_10016"] == 4
        # task-002 estimated_hours = 2
        assert issue_calls[3][2]["fields"]["customfield_10016"] == 2


class TestJiraExportProgress:
    """Tests for progress callback during export."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self, jira_client, mock_api, sample_roadmap):
        """Progress callback receives all items."""
        calls: list[tuple[str, str]] = []

        def callback(item_type: str, item_name: str):
            calls.append((item_type, item_name))

        await jira_client.export(
            sample_roadmap, project_key="PROJ", progress_callback=callback
        )
        assert len(calls) == 5
        assert calls[0] == ("Version", "MVP")
        assert calls[1] == ("Epic", "Authentication")
        assert calls[2] == ("Story", "User Login")
        assert calls[3][0] == "Sub-task"
        assert calls[4][0] == "Sub-task"

    @pytest.mark.asyncio
    async def test_export_without_callback(self, jira_client, mock_api, sample_roadmap):
        """Export works when progress_callback is None."""
        result = await jira_client.export(
            sample_roadmap, project_key="PROJ", progress_callback=None
        )
        assert result.success is True


class TestJiraExportTransitions:
    """Tests for status transitions."""

    @pytest.mark.asyncio
    async def test_transitions_non_initial_status(self, jira_client, mock_api, sample_roadmap):
        """Issues with non-initial status get transitioned."""
        sample_roadmap.milestones[0].epics[0].stories[0].tasks[0].status = (
            Status.IN_PROGRESS
        )
        await jira_client.export(sample_roadmap, project_key="PROJ")
        transition_posts = [
            (m, e, j)
            for m, e, j in mock_api.calls
            if m == "POST" and "/transitions" in e and "/issue/" in e
        ]
        assert len(transition_posts) >= 1
        # Should transition to "In Progress" (transition id "21")
        assert transition_posts[0][2]["transition"]["id"] == "21"

    @pytest.mark.asyncio
    async def test_skips_initial_status(self, jira_client, mock_api, sample_roadmap):
        """No transition for NOT_STARTED (initial state)."""
        # Default sample_roadmap has all NOT_STARTED
        await jira_client.export(sample_roadmap, project_key="PROJ")
        transition_posts = [
            (m, e, j)
            for m, e, j in mock_api.calls
            if m == "POST" and "/transitions" in e and "/issue/" in e
        ]
        assert len(transition_posts) == 0

    @pytest.mark.asyncio
    async def test_warns_on_unavailable_transition(self, jira_client, sample_roadmap):
        """Warns when requested transition is not available."""
        mock = MockJiraAPI()

        async def api_with_limited_transitions(method, endpoint, json=None):
            if method == "GET" and "/transitions" in endpoint:
                return {"transitions": [
                    {"id": "11", "name": "To Do", "to": {"name": "To Do"}},
                ]}
            return await mock(method, endpoint, json)

        jira_client._request = api_with_limited_transitions
        sample_roadmap.milestones[0].epics[0].status = Status.COMPLETED
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        assert result.success is True
        assert any("transition" in w.lower() or "Done" in w for w in result.warnings)


class TestJiraExportLinks:
    """Tests for prerequisite issue links."""

    @pytest.mark.asyncio
    async def test_creates_blocks_link(self, jira_client, mock_api, sample_roadmap):
        """Prerequisites create 'Blocks' issue links."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        link_calls = [
            (m, e, j)
            for m, e, j in mock_api.calls
            if m == "POST" and e == "/issueLink"
        ]
        assert len(link_calls) == 1
        link_json = link_calls[0][2]
        assert link_json["type"]["name"] == "Blocks"
        # task-001 blocks task-002
        assert link_json["outwardIssue"]["key"] == "PROJ-3"  # task-001
        assert link_json["inwardIssue"]["key"] == "PROJ-4"  # task-002

    @pytest.mark.asyncio
    async def test_missing_prereq_warns(self, jira_client, mock_api, sample_roadmap):
        """Missing prerequisite ID generates a warning."""
        sample_roadmap.milestones[0].epics[0].stories[0].tasks[0].prerequisites = [
            "nonexistent-task"
        ]
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        assert result.success is True
        assert any("nonexistent-task" in w for w in result.warnings)


class TestJiraExportComments:
    """Tests for claude_code_prompt comment creation."""

    @pytest.mark.asyncio
    async def test_creates_comments(self, jira_client, mock_api, sample_roadmap):
        """Comments are created for tasks with claude_code_prompt."""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        comment_calls = [
            (m, e, j)
            for m, e, j in mock_api.calls
            if m == "POST" and "/comment" in e
        ]
        assert len(comment_calls) == 2
        # Comment body is ADF
        assert comment_calls[0][2]["body"]["type"] == "doc"

    @pytest.mark.asyncio
    async def test_no_comment_for_empty_prompt(self, jira_client, mock_api, sample_roadmap):
        """No comment created when claude_code_prompt is empty."""
        for task in sample_roadmap.milestones[0].epics[0].stories[0].tasks:
            task.claude_code_prompt = ""
        await jira_client.export(sample_roadmap, project_key="PROJ")
        comment_calls = [
            (m, e, j)
            for m, e, j in mock_api.calls
            if m == "POST" and "/comment" in e
        ]
        assert len(comment_calls) == 0

    @pytest.mark.asyncio
    async def test_comment_error_warns(self, jira_client, sample_roadmap):
        """Comment failure adds warning, doesn't fail export."""
        mock = MockJiraAPI()

        async def api_with_comment_error(method, endpoint, json=None):
            if method == "POST" and "/comment" in endpoint:
                raise JiraAPIError(500, "Comment failed", endpoint)
            return await mock(method, endpoint, json)

        jira_client._request = api_with_comment_error
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        assert result.success is True
        assert len(result.warnings) >= 2
        assert any("comment" in w.lower() for w in result.warnings)


class TestJiraExportErrors:
    """Tests for error handling during export."""

    @pytest.mark.asyncio
    async def test_fatal_error_returns_failure(self, jira_client, sample_roadmap):
        """Fatal API error returns ExportResult with success=False."""

        async def failing_api(method, endpoint, json=None):
            raise JiraAPIError(500, "Internal server error", endpoint)

        jira_client._request = failing_api
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        assert result.success is False
        assert "Internal server error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_partial_failure_reports_created(self, jira_client, sample_roadmap):
        """Mid-export failure reports items created before the error."""
        mock = MockJiraAPI()
        issue_count = 0

        async def fail_on_third_issue(method, endpoint, json=None):
            nonlocal issue_count
            if method == "POST" and endpoint == "/issue":
                issue_count += 1
                if issue_count >= 3:
                    raise JiraAPIError(500, "Server error", endpoint)
            return await mock(method, endpoint, json)

        jira_client._request = fail_on_third_issue
        result = await jira_client.export(sample_roadmap, project_key="PROJ")
        assert result.success is False
        # Should have created version + epic + story before failure
        assert result.items_created >= 3


class TestJiraAPIError:
    """Tests for the JiraAPIError exception."""

    def test_error_formatting(self):
        """Formats error with status code, endpoint, and message."""
        err = JiraAPIError(404, "Not found", "/issue/ABC-1")
        msg = str(err)
        assert "404" in msg
        assert "Not found" in msg
        assert "/issue/ABC-1" in msg

    def test_attributes(self):
        """Error stores status_code and endpoint."""
        err = JiraAPIError(400, "Bad request", "/version")
        assert err.status_code == 400
        assert err.endpoint == "/version"
