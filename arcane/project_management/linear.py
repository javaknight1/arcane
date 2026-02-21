"""Linear exporter for roadmaps.

Exports roadmaps to Linear via the GraphQL API.

Entity mapping:
- Milestone → Project
- Epic → flattened (stories go directly under Project)
- Story → Issue (linked to Project)
- Task → Sub-Issue (child of Story issue)

Epics are flattened because Linear has no native epic concept.
Epic context is preserved by adding "Epic: {name}" to story descriptions.
"""

import httpx

from arcane.items import Priority, Roadmap, Status

from .base import BasePMClient, ExportResult, ProgressCallback
from .docs import build_all_pages, render_markdown


class LinearAPIError(Exception):
    """Raised when a Linear GraphQL request returns errors."""

    def __init__(self, errors: list[dict]):
        self.errors = errors
        messages = [e.get("message", str(e)) for e in errors]
        super().__init__(f"Linear API error: {'; '.join(messages)}")


class LinearClient(BasePMClient):
    """Exports roadmap to Linear via GraphQL API.

    Entity mapping:
    - Milestone → Project
    - Epic → flattened (stories go directly under Project)
    - Story → Issue (linked to Project)
    - Task → Sub-Issue (child of Story issue)
    """

    GRAPHQL_URL = "https://api.linear.app/graphql"

    PRIORITY_MAP = {
        Priority.CRITICAL: 1,  # Urgent
        Priority.HIGH: 2,
        Priority.MEDIUM: 3,
        Priority.LOW: 4,
    }

    STATUS_NAME_MAP = {
        Status.NOT_STARTED: "Todo",
        Status.IN_PROGRESS: "In Progress",
        Status.BLOCKED: "Todo",
        Status.COMPLETED: "Done",
    }

    STATUS_TYPE_FALLBACK = {
        Status.NOT_STARTED: "unstarted",
        Status.IN_PROGRESS: "started",
        Status.BLOCKED: "unstarted",
        Status.COMPLETED: "completed",
    }

    def __init__(self, api_key: str):
        """Initialize Linear client.

        Args:
            api_key: Linear API key for authentication.
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        self._http: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        """Return the client name."""
        return "Linear"

    async def _graphql(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL request and return the data dict."""
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        client = self._http or httpx.AsyncClient()
        own_client = self._http is None
        try:
            resp = await client.post(
                self.GRAPHQL_URL, headers=self.headers, json=payload
            )
            resp.raise_for_status()
            result = resp.json()
            if "errors" in result:
                raise LinearAPIError(result["errors"])
            return result.get("data", {})
        finally:
            if own_client:
                await client.aclose()

    async def validate_credentials(self) -> bool:
        """Test that API key is valid."""
        try:
            data = await self._graphql("{ viewer { id name } }")
            return "viewer" in data
        except (httpx.HTTPError, LinearAPIError):
            return False

    async def _fetch_workflow_states(self, team_id: str) -> dict[Status, str]:
        """Fetch workflow states and return Status → state_id mapping.

        Tries exact name match first (e.g. "Todo"), then falls back
        to matching by state type (e.g. "unstarted").
        """
        query = """
        query($teamId: String!) {
            workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                nodes { id name type }
            }
        }
        """
        data = await self._graphql(query, {"teamId": team_id})
        states = data["workflowStates"]["nodes"]

        mapping: dict[Status, str] = {}
        for status in Status:
            target_name = self.STATUS_NAME_MAP[status]
            matched = next(
                (s for s in states if s["name"].lower() == target_name.lower()),
                None,
            )
            if not matched:
                target_type = self.STATUS_TYPE_FALLBACK[status]
                matched = next(
                    (s for s in states if s["type"] == target_type), None
                )
            if matched:
                mapping[status] = matched["id"]

        return mapping

    async def _fetch_labels(self, team_id: str) -> dict[str, str]:
        """Fetch existing labels for a team. Returns name → id mapping."""
        query = """
        query($teamId: String!) {
            issueLabels(filter: { team: { id: { eq: $teamId } } }) {
                nodes { id name }
            }
        }
        """
        data = await self._graphql(query, {"teamId": team_id})
        return {
            label["name"]: label["id"]
            for label in data["issueLabels"]["nodes"]
        }

    async def _create_label(self, team_id: str, label_name: str) -> str:
        """Create a label and return its ID."""
        mutation = """
        mutation($input: IssueLabelCreateInput!) {
            issueLabelCreate(input: $input) {
                issueLabel { id }
                success
            }
        }
        """
        data = await self._graphql(
            mutation, {"input": {"name": label_name, "teamId": team_id}}
        )
        return data["issueLabelCreate"]["issueLabel"]["id"]

    async def _resolve_label_ids(
        self,
        team_id: str,
        label_names: list[str],
        label_cache: dict[str, str],
    ) -> list[str]:
        """Resolve label names to IDs, creating any that don't exist."""
        ids: list[str] = []
        for name in label_names:
            if name not in label_cache:
                label_cache[name] = await self._create_label(team_id, name)
            ids.append(label_cache[name])
        return ids

    @staticmethod
    def _build_description(
        description: str,
        acceptance_criteria: list[str] | None = None,
        implementation_notes: str | None = None,
        epic_name: str | None = None,
    ) -> str:
        """Build markdown description with optional extra sections."""
        parts: list[str] = []
        if epic_name:
            parts.append(f"**Epic:** {epic_name}\n")
        parts.append(description)
        if acceptance_criteria:
            parts.append("\n\n## Acceptance Criteria\n")
            for criterion in acceptance_criteria:
                parts.append(f"- [ ] {criterion}")
        if implementation_notes:
            parts.append(f"\n\n## Implementation Notes\n\n{implementation_notes}")
        return "\n".join(parts)

    async def _create_project(
        self,
        team_ids: list[str],
        name: str,
        description: str | None = None,
        target_date: str | None = None,
    ) -> dict:
        """Create a Linear Project. Returns {id, url}."""
        mutation = """
        mutation($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                project { id url }
                success
            }
        }
        """
        input_data: dict = {"name": name, "teamIds": team_ids}
        if description:
            input_data["description"] = description
        if target_date:
            input_data["targetDate"] = target_date

        data = await self._graphql(mutation, {"input": input_data})
        project = data["projectCreate"]["project"]
        return {"id": project["id"], "url": project.get("url", "")}

    async def _create_issue(
        self,
        team_id: str,
        title: str,
        description: str,
        priority: int,
        state_id: str | None = None,
        label_ids: list[str] | None = None,
        estimate: int | None = None,
        project_id: str | None = None,
        parent_id: str | None = None,
    ) -> dict:
        """Create a Linear Issue. Returns {id, identifier, url}."""
        mutation = """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                issue { id identifier url }
                success
            }
        }
        """
        input_data: dict = {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
        if state_id:
            input_data["stateId"] = state_id
        if label_ids:
            input_data["labelIds"] = label_ids
        if estimate is not None:
            input_data["estimate"] = estimate
        if project_id:
            input_data["projectId"] = project_id
        if parent_id:
            input_data["parentId"] = parent_id

        data = await self._graphql(mutation, {"input": input_data})
        issue = data["issueCreate"]["issue"]
        return {
            "id": issue["id"],
            "identifier": issue["identifier"],
            "url": issue.get("url", ""),
        }

    async def _create_comment(self, issue_id: str, body: str) -> None:
        """Post a comment on an issue."""
        mutation = """
        mutation($input: CommentCreateInput!) {
            commentCreate(input: $input) { success }
        }
        """
        await self._graphql(
            mutation, {"input": {"issueId": issue_id, "body": body}}
        )

    async def _create_relation(
        self, blocker_id: str, blocked_id: str
    ) -> None:
        """Create a 'blocks' relation (blocker blocks blocked)."""
        mutation = """
        mutation($input: IssueRelationCreateInput!) {
            issueRelationCreate(input: $input) { success }
        }
        """
        await self._graphql(
            mutation,
            {
                "input": {
                    "issueId": blocker_id,
                    "relatedIssueId": blocked_id,
                    "type": "blocks",
                }
            },
        )

    async def _create_document(
        self, title: str, content: str, project_id: str | None = None
    ) -> None:
        """Create a Linear Document."""
        mutation = """
        mutation($input: DocumentCreateInput!) {
            documentCreate(input: $input) { success }
        }
        """
        input_data: dict = {"title": title, "content": content}
        if project_id:
            input_data["projectId"] = project_id
        await self._graphql(mutation, {"input": input_data})

    async def export(
        self,
        roadmap: Roadmap,
        progress_callback: ProgressCallback | None = None,
        team_id: str | None = None,
        **kwargs,
    ) -> ExportResult:
        """Export roadmap to Linear.

        Args:
            roadmap: The Roadmap to export.
            progress_callback: Optional callback for progress reporting.
            team_id: Linear team ID (required).
        """
        if not team_id:
            raise ValueError("team_id is required for Linear export")

        warnings: list[str] = []
        id_mapping: dict[str, str] = {}
        uuid_map: dict[str, str] = {}
        items_by_type: dict[str, int] = {"milestones": 0, "stories": 0, "tasks": 0}
        items_created = 0
        first_url: str | None = None
        pending_relations: list[tuple[str, str]] = []

        self._http = httpx.AsyncClient()
        try:
            # Setup: fetch workflow states and existing labels
            status_map = await self._fetch_workflow_states(team_id)
            label_cache = await self._fetch_labels(team_id)

            for milestone in roadmap.milestones:
                # Create Project from Milestone
                project = await self._create_project(
                    team_ids=[team_id],
                    name=milestone.name,
                    description=milestone.goal,
                    target_date=milestone.target_date,
                )
                id_mapping[milestone.id] = project["id"]
                uuid_map[milestone.id] = project["id"]
                items_by_type["milestones"] += 1
                items_created += 1
                if not first_url and project.get("url"):
                    first_url = project["url"]
                if progress_callback:
                    progress_callback("Project", milestone.name)

                # Flatten epics: stories go directly under the project
                for epic in milestone.epics:
                    for story in epic.stories:
                        desc = self._build_description(
                            story.description,
                            acceptance_criteria=story.acceptance_criteria,
                            epic_name=epic.name,
                        )
                        label_ids = await self._resolve_label_ids(
                            team_id, list(story.labels), label_cache
                        )
                        state_id = status_map.get(story.status)
                        if story.status == Status.BLOCKED:
                            label_ids.extend(
                                await self._resolve_label_ids(
                                    team_id, ["blocked"], label_cache
                                )
                            )

                        issue = await self._create_issue(
                            team_id=team_id,
                            title=story.name,
                            description=desc,
                            priority=self.PRIORITY_MAP[story.priority],
                            state_id=state_id,
                            label_ids=label_ids or None,
                            estimate=story.estimated_hours,
                            project_id=project["id"],
                        )
                        id_mapping[story.id] = issue["identifier"]
                        uuid_map[story.id] = issue["id"]
                        items_by_type["stories"] += 1
                        items_created += 1
                        if progress_callback:
                            progress_callback("Issue", story.name)

                        # Create tasks as sub-issues
                        for task in story.tasks:
                            task_desc = self._build_description(
                                task.description,
                                acceptance_criteria=task.acceptance_criteria,
                                implementation_notes=task.implementation_notes,
                            )
                            task_label_ids = await self._resolve_label_ids(
                                team_id, list(task.labels), label_cache
                            )
                            task_state_id = status_map.get(task.status)
                            if task.status == Status.BLOCKED:
                                task_label_ids.extend(
                                    await self._resolve_label_ids(
                                        team_id, ["blocked"], label_cache
                                    )
                                )

                            task_issue = await self._create_issue(
                                team_id=team_id,
                                title=task.name,
                                description=task_desc,
                                priority=self.PRIORITY_MAP[task.priority],
                                state_id=task_state_id,
                                label_ids=task_label_ids or None,
                                estimate=task.estimated_hours,
                                project_id=project["id"],
                                parent_id=issue["id"],
                            )
                            id_mapping[task.id] = task_issue["identifier"]
                            uuid_map[task.id] = task_issue["id"]
                            items_by_type["tasks"] += 1
                            items_created += 1
                            if progress_callback:
                                progress_callback("Sub-Issue", task.name)

                            # Post claude_code_prompt as comment
                            if task.claude_code_prompt:
                                try:
                                    await self._create_comment(
                                        task_issue["id"],
                                        f"## Claude Code Prompt\n\n{task.claude_code_prompt}",
                                    )
                                except (LinearAPIError, httpx.HTTPError) as e:
                                    warnings.append(
                                        f"Could not add comment for {task.name}: {e}"
                                    )

                            # Collect prerequisites for relation creation
                            for prereq_id in task.prerequisites:
                                pending_relations.append((prereq_id, task.id))

            # Phase 2: Create prerequisite relations
            for prereq_arcane_id, blocked_arcane_id in pending_relations:
                if prereq_arcane_id in uuid_map and blocked_arcane_id in uuid_map:
                    try:
                        await self._create_relation(
                            uuid_map[prereq_arcane_id],
                            uuid_map[blocked_arcane_id],
                        )
                    except (LinearAPIError, httpx.HTTPError) as e:
                        warnings.append(
                            f"Could not create relation "
                            f"{prereq_arcane_id} \u2192 {blocked_arcane_id}: {e}"
                        )
                else:
                    warnings.append(
                        f"Prerequisite {prereq_arcane_id} not found for relation"
                    )

            # Phase 3: Create documentation pages
            first_project_id = next(
                (uuid_map[ms.id] for ms in roadmap.milestones if ms.id in uuid_map),
                None,
            )
            for page in build_all_pages(roadmap.context):
                try:
                    await self._create_document(
                        title=page.title,
                        content=render_markdown([page]),
                        project_id=first_project_id,
                    )
                except (LinearAPIError, httpx.HTTPError) as e:
                    warnings.append(f"Could not create document '{page.title}': {e}")

        except (LinearAPIError, httpx.HTTPError) as e:
            return ExportResult(
                success=False,
                target="Linear",
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
            target="Linear",
            items_created=items_created,
            items_by_type=items_by_type,
            id_mapping=id_mapping,
            warnings=warnings,
            url=first_url,
        )
