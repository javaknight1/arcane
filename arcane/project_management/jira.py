"""Jira Cloud exporter for roadmaps.

Exports roadmaps to Jira Cloud via the REST API v3.

Entity mapping:
- Milestone -> Version (Fix Version)
- Epic -> Epic (issue type)
- Story -> Story (issue type), linked to Epic via epic link custom field
- Task -> Sub-task (issue type), parent = Story issue

ADF (Atlassian Document Format) is used for all description and comment fields.
"""

import logging

import httpx

from arcane.items import Priority, Roadmap, Status

from .base import BasePMClient, ExportResult, ProgressCallback

logger = logging.getLogger(__name__)


class JiraAPIError(Exception):
    """Raised when a Jira REST API request fails."""

    def __init__(self, status_code: int, message: str, endpoint: str):
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__(
            f"Jira API error ({status_code}) on {endpoint}: {message}"
        )


PRIORITY_NAME_MAP = {
    Priority.CRITICAL: "Highest",
    Priority.HIGH: "High",
    Priority.MEDIUM: "Medium",
    Priority.LOW: "Low",
}

STATUS_TARGET_MAP = {
    Status.NOT_STARTED: "To Do",
    Status.IN_PROGRESS: "In Progress",
    Status.BLOCKED: "To Do",
    Status.COMPLETED: "Done",
}


class JiraClient(BasePMClient):
    """Exports roadmap to Jira Cloud via REST API v3.

    Entity mapping:
    - Milestone -> Version (Fix Version)
    - Epic -> Epic (issue type)
    - Story -> Story (issue type), linked to Epic via epic link custom field
    - Task -> Sub-task (issue type), parent = Story issue
    """

    def __init__(self, domain: str, email: str, api_token: str):
        self.base_url = f"https://{domain}/rest/api/3"
        self.auth = (email, api_token)
        self.domain = domain
        self._http: httpx.AsyncClient | None = None

        # Populated by _discover_* during export setup
        self._issue_type_ids: dict[str, str] = {}
        self._story_points_field: str | None = None
        self._epic_link_field: str | None = None
        self._priority_ids: dict[str, str] = {}

    @property
    def name(self) -> str:
        return "Jira Cloud"

    async def validate_credentials(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/myself",
                    auth=self.auth,
                )
                return resp.status_code == 200
        except httpx.RequestError:
            return False

    # -- ADF (Atlassian Document Format) builders --

    @staticmethod
    def _adf_doc(content: list[dict]) -> dict:
        """Wrap content nodes in an ADF document."""
        return {"type": "doc", "version": 1, "content": content}

    @staticmethod
    def _adf_paragraph(text: str) -> dict:
        """Create an ADF paragraph node."""
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": text}],
        }

    @staticmethod
    def _adf_heading(text: str, level: int = 2) -> dict:
        """Create an ADF heading node."""
        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": [{"type": "text", "text": text}],
        }

    @staticmethod
    def _adf_bullet_list(items: list[str]) -> dict:
        """Create an ADF bulletList node."""
        list_items = []
        for item in items:
            list_items.append(
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": item}],
                        }
                    ],
                }
            )
        return {"type": "bulletList", "content": list_items}

    @staticmethod
    def _adf_code_block(code: str, language: str = "plain") -> dict:
        """Create an ADF codeBlock node."""
        return {
            "type": "codeBlock",
            "attrs": {"language": language},
            "content": [{"type": "text", "text": code}],
        }

    @staticmethod
    def _adf_rule() -> dict:
        """Create an ADF horizontal rule node."""
        return {"type": "rule"}

    @classmethod
    def _build_adf_description(
        cls,
        description: str,
        acceptance_criteria: list[str] | None = None,
        implementation_notes: str | None = None,
        goal: str | None = None,
    ) -> dict:
        """Build a complete ADF document for an issue description."""
        content: list[dict] = []

        if goal:
            content.append(cls._adf_heading("Goal"))
            content.append(cls._adf_paragraph(goal))
            content.append(cls._adf_rule())

        content.append(cls._adf_paragraph(description))

        if acceptance_criteria:
            content.append(cls._adf_rule())
            content.append(cls._adf_heading("Acceptance Criteria"))
            content.append(cls._adf_bullet_list(acceptance_criteria))

        if implementation_notes:
            content.append(cls._adf_rule())
            content.append(cls._adf_heading("Implementation Notes"))
            content.append(cls._adf_paragraph(implementation_notes))

        return cls._adf_doc(content)

    # -- API request helper --

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
    ) -> dict:
        """Make an authenticated API request. Raises JiraAPIError on non-2xx."""
        client = self._http or httpx.AsyncClient()
        own_client = self._http is None
        try:
            resp = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                auth=self.auth,
                json=json,
                timeout=30.0,
            )
            if resp.status_code >= 400:
                try:
                    error_body = resp.json()
                    messages = error_body.get("errorMessages", [])
                    errors = error_body.get("errors", {})
                    msg = "; ".join(messages) if messages else str(errors)
                except Exception:
                    msg = resp.text
                raise JiraAPIError(resp.status_code, msg, endpoint)
            if resp.status_code == 204:
                return {}
            return resp.json()
        finally:
            if own_client:
                await client.aclose()

    # -- Discovery methods --

    async def _discover_project(self, project_key: str) -> None:
        """Validate project exists and discover issue type IDs."""
        data = await self._request("GET", f"/project/{project_key}")

        # Find issue type IDs
        issue_types = data.get("issueTypes", [])
        type_name_map = {it["name"].lower(): it["id"] for it in issue_types}

        for needed in ("epic", "story", "sub-task"):
            if needed in type_name_map:
                self._issue_type_ids[needed] = type_name_map[needed]
            else:
                # Try alternative names
                alternatives = {
                    "sub-task": ["subtask", "sub task"],
                }
                found = False
                for alt in alternatives.get(needed, []):
                    if alt in type_name_map:
                        self._issue_type_ids[needed] = type_name_map[alt]
                        found = True
                        break
                if not found:
                    raise JiraAPIError(
                        404,
                        f"Issue type '{needed}' not found in project {project_key}. "
                        f"Available: {', '.join(type_name_map.keys())}",
                        f"/project/{project_key}",
                    )

    async def _discover_fields(self) -> list[str]:
        """Discover custom field IDs for story points and epic link.

        Returns a list of warnings for fields that could not be found.
        """
        warnings: list[str] = []
        fields = await self._request("GET", "/field")

        for field in fields:
            name = field.get("name", "").lower()
            field_id = field.get("id", "")
            schema = field.get("schema", {})
            custom = schema.get("custom", "")

            # Story points field
            if (
                not self._story_points_field
                and (
                    "story point" in name
                    or "com.atlassian.jira.plugin.system.customfieldtypes:float" in custom
                    and "story" in name.lower()
                )
            ):
                self._story_points_field = field_id

            # Epic link field
            if (
                not self._epic_link_field
                and "com.pyxis.greenhopper.jira:gh-epic-link" in custom
            ):
                self._epic_link_field = field_id

        if not self._story_points_field:
            warnings.append(
                "Could not find Story Points custom field. "
                "Estimates will not be set on issues."
            )
        if not self._epic_link_field:
            warnings.append(
                "Could not find Epic Link custom field. "
                "Stories will not be linked to epics."
            )

        return warnings

    async def _discover_priorities(self) -> list[str]:
        """Discover priority name -> ID mapping.

        Returns a list of warnings for priorities that could not be mapped.
        """
        warnings: list[str] = []
        priorities = await self._request("GET", "/priority")

        priority_name_to_id = {p["name"].lower(): p["id"] for p in priorities}

        for arcane_priority, jira_name in PRIORITY_NAME_MAP.items():
            jira_lower = jira_name.lower()
            if jira_lower in priority_name_to_id:
                self._priority_ids[jira_name] = priority_name_to_id[jira_lower]
            else:
                warnings.append(
                    f"Priority '{jira_name}' not found in Jira. "
                    f"Available: {', '.join(priority_name_to_id.keys())}"
                )

        return warnings

    # -- Create methods --

    async def _create_version(
        self,
        project_key: str,
        name: str,
        description: str | None = None,
        release_date: str | None = None,
    ) -> dict:
        """Create a Jira Version (Fix Version). Returns version dict."""
        body: dict = {
            "name": name,
            "projectId": None,  # Will be set below
            "project": project_key,
        }
        if description:
            body["description"] = description
        if release_date:
            body["releaseDate"] = release_date

        # Get project ID
        project = await self._request("GET", f"/project/{project_key}")
        body["projectId"] = int(project["id"])
        del body["project"]

        return await self._request("POST", "/version", json=body)

    async def _create_issue(
        self,
        project_key: str,
        type_id: str,
        summary: str,
        adf_description: dict,
        priority_id: str | None = None,
        fix_versions: list[str] | None = None,
        epic_link: str | None = None,
        parent_key: str | None = None,
        labels: list[str] | None = None,
        story_points: int | None = None,
    ) -> dict:
        """Create a Jira issue. Returns {id, key, self}."""
        fields: dict = {
            "project": {"key": project_key},
            "issuetype": {"id": type_id},
            "summary": summary,
            "description": adf_description,
        }

        if priority_id:
            fields["priority"] = {"id": priority_id}
        if fix_versions:
            fields["fixVersions"] = [{"id": vid} for vid in fix_versions]
        if epic_link and self._epic_link_field:
            fields[self._epic_link_field] = epic_link
        if parent_key:
            fields["parent"] = {"key": parent_key}
        if labels:
            fields["labels"] = labels
        if story_points is not None and self._story_points_field:
            fields[self._story_points_field] = story_points

        result = await self._request("POST", "/issue", json={"fields": fields})
        return {
            "id": result["id"],
            "key": result["key"],
            "self": result.get("self", ""),
        }

    async def _transition_issue(
        self,
        issue_id_or_key: str,
        target_status_name: str,
    ) -> bool:
        """Transition an issue to a target status. Returns True if successful."""
        data = await self._request(
            "GET", f"/issue/{issue_id_or_key}/transitions"
        )
        transitions = data.get("transitions", [])

        matched = next(
            (
                t
                for t in transitions
                if t["name"].lower() == target_status_name.lower()
                or t.get("to", {}).get("name", "").lower()
                == target_status_name.lower()
            ),
            None,
        )

        if not matched:
            logger.warning(
                "Transition to '%s' not available for %s. "
                "Available: %s",
                target_status_name,
                issue_id_or_key,
                ", ".join(t["name"] for t in transitions),
            )
            return False

        await self._request(
            "POST",
            f"/issue/{issue_id_or_key}/transitions",
            json={"transition": {"id": matched["id"]}},
        )
        return True

    async def _create_issue_link(
        self,
        blocker_key: str,
        blocked_key: str,
    ) -> None:
        """Create a 'Blocks' issue link."""
        await self._request(
            "POST",
            "/issueLink",
            json={
                "type": {"name": "Blocks"},
                "inwardIssue": {"key": blocked_key},
                "outwardIssue": {"key": blocker_key},
            },
        )

    async def _add_comment(
        self,
        issue_id_or_key: str,
        adf_body: dict,
    ) -> None:
        """Add a comment to an issue using ADF format."""
        await self._request(
            "POST",
            f"/issue/{issue_id_or_key}/comment",
            json={"body": adf_body},
        )

    # -- Main export --

    async def export(
        self,
        roadmap: Roadmap,
        progress_callback: ProgressCallback | None = None,
        project_key: str | None = None,
        **kwargs,
    ) -> ExportResult:
        """Export roadmap to Jira Cloud.

        Args:
            roadmap: The Roadmap to export.
            progress_callback: Optional callback for progress reporting.
            project_key: Jira project key (required, e.g., 'PROJ').
        """
        if not project_key:
            raise ValueError(
                "project_key is required for Jira export. "
                "Pass the Jira project key (e.g., 'PROJ')."
            )

        warnings: list[str] = []
        id_mapping: dict[str, str] = {}
        uuid_map: dict[str, str] = {}
        items_by_type: dict[str, int] = {
            "milestones": 0,
            "epics": 0,
            "stories": 0,
            "tasks": 0,
        }
        items_created = 0
        first_url: str | None = None
        pending_transitions: list[tuple[str, Status]] = []
        pending_links: list[tuple[str, str]] = []

        self._http = httpx.AsyncClient()
        try:
            # Phase 0: Setup — discover project, fields, priorities
            await self._discover_project(project_key)
            field_warnings = await self._discover_fields()
            warnings.extend(field_warnings)
            priority_warnings = await self._discover_priorities()
            warnings.extend(priority_warnings)

            # Phase 1: Create Versions (milestones)
            for milestone in roadmap.milestones:
                version = await self._create_version(
                    project_key,
                    name=milestone.name,
                    description=milestone.goal,
                    release_date=milestone.target_date,
                )
                version_id = version["id"]
                id_mapping[milestone.id] = version.get("name", version_id)
                uuid_map[milestone.id] = version_id
                items_by_type["milestones"] += 1
                items_created += 1
                if progress_callback:
                    progress_callback("Version", milestone.name)

                if milestone.status != Status.NOT_STARTED:
                    pending_transitions.append(
                        (version_id, milestone.status)
                    )

                # Phase 2: Create issues
                for epic in milestone.epics:
                    epic_desc = self._build_adf_description(
                        epic.description,
                        goal=epic.goal,
                    )
                    epic_priority_id = self._priority_ids.get(
                        PRIORITY_NAME_MAP[epic.priority]
                    )
                    epic_labels = list(epic.labels)

                    epic_issue = await self._create_issue(
                        project_key,
                        type_id=self._issue_type_ids["epic"],
                        summary=epic.name,
                        adf_description=epic_desc,
                        priority_id=epic_priority_id,
                        fix_versions=[version_id],
                        labels=epic_labels or None,
                        story_points=epic.estimated_hours,
                    )
                    id_mapping[epic.id] = epic_issue["key"]
                    uuid_map[epic.id] = epic_issue["id"]
                    items_by_type["epics"] += 1
                    items_created += 1
                    if not first_url:
                        first_url = (
                            f"https://{self.domain}/browse/{epic_issue['key']}"
                        )
                    if progress_callback:
                        progress_callback("Epic", epic.name)

                    if epic.status != Status.NOT_STARTED:
                        pending_transitions.append(
                            (epic_issue["key"], epic.status)
                        )

                    for story in epic.stories:
                        story_desc = self._build_adf_description(
                            story.description,
                            acceptance_criteria=story.acceptance_criteria,
                        )
                        story_priority_id = self._priority_ids.get(
                            PRIORITY_NAME_MAP[story.priority]
                        )
                        story_labels = list(story.labels)
                        if story.status == Status.BLOCKED:
                            story_labels.append("blocked")

                        story_issue = await self._create_issue(
                            project_key,
                            type_id=self._issue_type_ids["story"],
                            summary=story.name,
                            adf_description=story_desc,
                            priority_id=story_priority_id,
                            fix_versions=[version_id],
                            epic_link=epic_issue["key"],
                            labels=story_labels or None,
                            story_points=story.estimated_hours,
                        )
                        id_mapping[story.id] = story_issue["key"]
                        uuid_map[story.id] = story_issue["id"]
                        items_by_type["stories"] += 1
                        items_created += 1
                        if progress_callback:
                            progress_callback("Story", story.name)

                        if story.status != Status.NOT_STARTED:
                            pending_transitions.append(
                                (story_issue["key"], story.status)
                            )

                        for task in story.tasks:
                            task_desc = self._build_adf_description(
                                task.description,
                                acceptance_criteria=task.acceptance_criteria,
                                implementation_notes=task.implementation_notes,
                            )
                            task_priority_id = self._priority_ids.get(
                                PRIORITY_NAME_MAP[task.priority]
                            )
                            task_labels = list(task.labels)
                            if task.status == Status.BLOCKED:
                                task_labels.append("blocked")

                            task_issue = await self._create_issue(
                                project_key,
                                type_id=self._issue_type_ids["sub-task"],
                                summary=task.name,
                                adf_description=task_desc,
                                priority_id=task_priority_id,
                                parent_key=story_issue["key"],
                                labels=task_labels or None,
                                story_points=task.estimated_hours,
                            )
                            id_mapping[task.id] = task_issue["key"]
                            uuid_map[task.id] = task_issue["id"]
                            items_by_type["tasks"] += 1
                            items_created += 1
                            if progress_callback:
                                progress_callback("Sub-task", task.name)

                            if task.status != Status.NOT_STARTED:
                                pending_transitions.append(
                                    (task_issue["key"], task.status)
                                )

                            # Collect prerequisites for link creation
                            for prereq_id in task.prerequisites:
                                pending_links.append((prereq_id, task.id))

                            # Post claude_code_prompt as comment
                            if task.claude_code_prompt:
                                try:
                                    prompt_adf = self._adf_doc(
                                        [
                                            self._adf_heading(
                                                "Claude Code Prompt"
                                            ),
                                            self._adf_code_block(
                                                task.claude_code_prompt
                                            ),
                                        ]
                                    )
                                    await self._add_comment(
                                        task_issue["key"], prompt_adf
                                    )
                                except (
                                    JiraAPIError,
                                    httpx.HTTPError,
                                ) as e:
                                    warnings.append(
                                        f"Could not add comment for "
                                        f"{task.name}: {e}"
                                    )

            # Phase 3: Status transitions
            for issue_id_or_key, status in pending_transitions:
                target_name = STATUS_TARGET_MAP[status]
                try:
                    success = await self._transition_issue(
                        issue_id_or_key, target_name
                    )
                    if not success:
                        warnings.append(
                            f"Could not transition {issue_id_or_key} "
                            f"to '{target_name}'"
                        )
                except (JiraAPIError, httpx.HTTPError) as e:
                    warnings.append(
                        f"Could not transition {issue_id_or_key} "
                        f"to '{target_name}': {e}"
                    )

            # Phase 4: Issue links (prerequisites -> "Blocks")
            for prereq_arcane_id, blocked_arcane_id in pending_links:
                if (
                    prereq_arcane_id in id_mapping
                    and blocked_arcane_id in id_mapping
                ):
                    try:
                        await self._create_issue_link(
                            id_mapping[prereq_arcane_id],
                            id_mapping[blocked_arcane_id],
                        )
                    except (JiraAPIError, httpx.HTTPError) as e:
                        warnings.append(
                            f"Could not create link "
                            f"{prereq_arcane_id} -> {blocked_arcane_id}: {e}"
                        )
                else:
                    warnings.append(
                        f"Prerequisite {prereq_arcane_id} not found "
                        f"for link"
                    )

            # Documentation pages require Confluence (separate product)
            logger.info(
                "Documentation pages require Confluence - skipped."
            )

        except (JiraAPIError, httpx.HTTPError) as e:
            return ExportResult(
                success=False,
                target="Jira Cloud",
                items_created=items_created,
                items_by_type=items_by_type,
                id_mapping=id_mapping,
                errors=[str(e)],
                warnings=warnings,
            )
        finally:
            await self._http.aclose()
            self._http = None

        return ExportResult(
            success=True,
            target="Jira Cloud",
            items_created=items_created,
            items_by_type=items_by_type,
            id_mapping=id_mapping,
            warnings=warnings,
            url=first_url,
        )
