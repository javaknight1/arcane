"""Notion exporter for roadmaps.

Exports roadmaps to Notion via the API, creating 4 linked databases
(Milestones, Epics, Stories, Tasks) plus documentation pages.
"""

import asyncio
import logging

import httpx

from arcane.items import Roadmap

from .base import BasePMClient, ExportResult, ProgressCallback
from .docs import DocSection, build_all_pages

logger = logging.getLogger(__name__)

PRIORITY_OPTIONS = [
    {"name": "Critical", "color": "red"},
    {"name": "High", "color": "orange"},
    {"name": "Medium", "color": "yellow"},
    {"name": "Low", "color": "green"},
]

STAGE_OPTIONS = [
    {"name": "Not Started", "color": "default"},
    {"name": "In Progress", "color": "blue"},
    {"name": "Blocked", "color": "red"},
    {"name": "Completed", "color": "green"},
]

STATUS_MAP = {
    "not_started": "Not Started",
    "in_progress": "In Progress",
    "blocked": "Blocked",
    "completed": "Completed",
}

PRIORITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}

ITEM_ICONS = {
    "milestone": "📋",
    "epic": "🏗️",
    "story": "📝",
    "task": "✅",
}

DB_ICONS = {
    "milestones": "📋",
    "epics": "🏗️",
    "stories": "📝",
    "tasks": "✅",
}

DOC_PAGE_ICONS = {
    "Project Overview": "📊",
    "Requirements": "📋",
    "Technical Decisions": "⚙️",
    "Team & Constraints": "👥",
}


class NotionClient(BasePMClient):
    """Exports roadmap to Notion via API.

    Creates 4 linked databases under a parent page:
    - Milestones DB
    - Epics DB (related to Milestones)
    - Stories DB (related to Epics)
    - Tasks DB (related to Stories)

    Plus 4 documentation pages from ProjectContext.
    """

    API_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION,
        }
        self._rate_limiter = asyncio.Semaphore(3)

    @property
    def name(self) -> str:
        return "Notion"

    async def validate_credentials(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.API_URL}/users/me",
                    headers=self.headers,
                )
                return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def _request(
        self, method: str, endpoint: str, json: dict | None = None
    ) -> dict:
        """Make a rate-limited API request with retry on 429."""
        max_retries = 3
        for attempt in range(max_retries):
            async with self._rate_limiter:
                async with httpx.AsyncClient() as client:
                    resp = await client.request(
                        method,
                        f"{self.API_URL}{endpoint}",
                        headers=self.headers,
                        json=json,
                        timeout=30.0,
                    )
                await asyncio.sleep(0.35)

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", "1"))
                if attempt < max_retries - 1:
                    logger.warning(
                        "Rate limited by Notion API, retrying in %ss", retry_after
                    )
                    await asyncio.sleep(retry_after)
                    continue
            resp.raise_for_status()
            return resp.json()

        # Should not reach here, but just in case
        resp.raise_for_status()
        return resp.json()

    # -- Database schema builders --

    def _build_milestones_db_properties(self) -> dict:
        return {
            "Name": {"title": {}},
            "Goal": {"rich_text": {}},
            "Target Date": {"date": {}},
            "Priority": {"select": {"options": PRIORITY_OPTIONS}},
            "Stage": {"select": {"options": STAGE_OPTIONS}},
            "Labels": {"multi_select": {"options": []}},
            "Estimated Points": {"number": {"format": "number"}},
        }

    def _build_epics_db_properties(self, milestones_db_id: str) -> dict:
        return {
            "Name": {"title": {}},
            "Goal": {"rich_text": {}},
            "Priority": {"select": {"options": PRIORITY_OPTIONS}},
            "Stage": {"select": {"options": STAGE_OPTIONS}},
            "Labels": {"multi_select": {"options": []}},
            "Estimated Points": {"number": {"format": "number"}},
            "Milestone": {
                "relation": {
                    "database_id": milestones_db_id,
                    "single_property": {},
                }
            },
        }

    def _build_stories_db_properties(self, epics_db_id: str) -> dict:
        return {
            "Name": {"title": {}},
            "Priority": {"select": {"options": PRIORITY_OPTIONS}},
            "Stage": {"select": {"options": STAGE_OPTIONS}},
            "Labels": {"multi_select": {"options": []}},
            "Estimated Points": {"number": {"format": "number"}},
            "Epic": {
                "relation": {
                    "database_id": epics_db_id,
                    "single_property": {},
                }
            },
        }

    def _build_tasks_db_properties(self, stories_db_id: str) -> dict:
        return {
            "Name": {"title": {}},
            "Priority": {"select": {"options": PRIORITY_OPTIONS}},
            "Stage": {"select": {"options": STAGE_OPTIONS}},
            "Labels": {"multi_select": {"options": []}},
            "Estimated Points": {"number": {"format": "number"}},
            "Prerequisites": {"rich_text": {}},
            "Story": {
                "relation": {
                    "database_id": stories_db_id,
                    "single_property": {},
                }
            },
        }

    # -- Database / page creation --

    @staticmethod
    def _emoji_icon(emoji: str) -> dict:
        return {"type": "emoji", "emoji": emoji}

    async def _ensure_parent_icon(self, parent_page_id: str, emoji: str) -> None:
        """Set the parent page icon if it doesn't already have one."""
        try:
            page = await self._request("GET", f"/pages/{parent_page_id}")
            if not page.get("icon"):
                await self._request(
                    "PATCH",
                    f"/pages/{parent_page_id}",
                    json={"icon": self._emoji_icon(emoji)},
                )
        except (httpx.HTTPStatusError, httpx.RequestError):
            pass  # Non-critical, skip silently

    async def _create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: dict,
        icon: str | None = None,
    ) -> str:
        """Create a Notion database under a parent page. Returns database ID."""
        body: dict = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }
        if icon:
            body["icon"] = self._emoji_icon(icon)
        result = await self._request("POST", "/databases", json=body)
        return result["id"]

    async def _create_page(
        self,
        database_id: str,
        properties: dict,
        children: list[dict] | None = None,
        icon: str | None = None,
    ) -> str:
        """Create a page in a Notion database. Returns page ID."""
        body: dict = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        if children:
            body["children"] = children[:100]
        if icon:
            body["icon"] = self._emoji_icon(icon)
        result = await self._request("POST", "/pages", json=body)
        page_id = result["id"]

        # Append remaining children in batches
        if children and len(children) > 100:
            await self._append_blocks(page_id, children[100:])

        return page_id

    async def _create_child_page(
        self,
        parent_page_id: str,
        title: str,
        children: list[dict] | None = None,
        icon: str | None = None,
    ) -> str:
        """Create a page under a parent page (not in a database). Returns page ID."""
        body: dict = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "properties": {
                "title": [{"type": "text", "text": {"content": title}}],
            },
        }
        if children:
            body["children"] = children[:100]
        if icon:
            body["icon"] = self._emoji_icon(icon)
        result = await self._request("POST", "/pages", json=body)
        page_id = result["id"]

        # Append remaining children in batches
        if children and len(children) > 100:
            await self._append_blocks(page_id, children[100:])

        return page_id

    async def _append_blocks(
        self, page_id: str, children: list[dict]
    ) -> None:
        """Append block children to a page, batching to max 100 per call."""
        for i in range(0, len(children), 100):
            batch = children[i : i + 100]
            await self._request(
                "PATCH",
                f"/blocks/{page_id}/children",
                json={"children": batch},
            )

    # -- Text chunking --

    @staticmethod
    def _chunk_rich_text(text: str, max_len: int = 2000) -> list[dict]:
        """Split text into multiple rich_text elements of ≤max_len chars each.

        Splits on newline or space boundaries to avoid mid-word breaks.
        Notion limits each rich_text content element to 2000 characters.
        """
        if len(text) <= max_len:
            return [{"type": "text", "text": {"content": text}}]

        elements: list[dict] = []
        remaining = text
        while remaining:
            if len(remaining) <= max_len:
                elements.append({"type": "text", "text": {"content": remaining}})
                break

            # Find the best split point within the limit
            chunk = remaining[:max_len]
            # Prefer splitting on newline
            split_pos = chunk.rfind("\n")
            if split_pos == -1:
                # Fall back to space
                split_pos = chunk.rfind(" ")
            if split_pos == -1:
                # No good boundary — hard split
                split_pos = max_len

            elements.append(
                {"type": "text", "text": {"content": remaining[:split_pos]}}
            )
            remaining = remaining[split_pos:].lstrip("\n")

        return elements

    # -- Block builders --

    @classmethod
    def _build_description_blocks(cls, description: str) -> list[dict]:
        return [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": cls._chunk_rich_text(description)
                },
            }
        ]

    @staticmethod
    def _build_acceptance_criteria_blocks(criteria: list[str]) -> list[dict]:
        blocks: list[dict] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Acceptance Criteria"}}
                    ]
                },
            }
        ]
        for item in criteria:
            blocks.append(
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {"type": "text", "text": {"content": item}}
                        ],
                        "checked": False,
                    },
                }
            )
        return blocks

    @classmethod
    def _build_implementation_notes_blocks(cls, notes: str) -> list[dict]:
        return [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Implementation Notes"}}
                    ]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": cls._chunk_rich_text(notes)
                },
            },
        ]

    @classmethod
    def _build_claude_code_prompt_blocks(cls, prompt: str) -> list[dict]:
        return [
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Claude Code Prompt"}}
                    ],
                    "children": [
                        {
                            "object": "block",
                            "type": "code",
                            "code": {
                                "rich_text": cls._chunk_rich_text(prompt),
                                "language": "plain text",
                            },
                        }
                    ],
                },
            }
        ]

    @staticmethod
    def _doc_section_to_blocks(section: DocSection) -> list[dict]:
        """Convert a DocSection to Notion blocks."""
        blocks: list[dict] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": section.title}}
                    ]
                },
            }
        ]

        if section.content_type == "paragraph":
            for item in section.items:
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": item}}
                            ]
                        },
                    }
                )
        elif section.content_type == "bullet_list":
            for item in section.items:
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": item}}
                            ]
                        },
                    }
                )
        elif section.content_type == "checklist":
            for item in section.items:
                blocks.append(
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [
                                {"type": "text", "text": {"content": item}}
                            ],
                            "checked": False,
                        },
                    }
                )
        elif section.content_type == "callout":
            icon = section.icon or "💡"
            content = "\n".join(section.items)
            blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content}}
                        ],
                        "icon": {"type": "emoji", "emoji": icon},
                    },
                }
            )

        return blocks

    # -- Table of contents builder --

    @staticmethod
    def _build_toc_header_blocks(roadmap: Roadmap) -> list[dict]:
        """Build the TOC header: divider, heading, and summary paragraph."""
        return [
            {
                "object": "block",
                "type": "divider",
                "divider": {},
            },
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Roadmap Overview"}}
                    ]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{roadmap.total_hours} hours across "},
                        },
                        {
                            "type": "text",
                            "text": {"content": f"{roadmap.total_items['milestones']} milestones, "},
                            "annotations": {"bold": True},
                        },
                        {
                            "type": "text",
                            "text": {"content": f"{roadmap.total_items['epics']} epics, "},
                        },
                        {
                            "type": "text",
                            "text": {"content": f"{roadmap.total_items['stories']} stories, "},
                        },
                        {
                            "type": "text",
                            "text": {"content": f"{roadmap.total_items['tasks']} tasks"},
                        },
                    ]
                },
            },
        ]

    @staticmethod
    def _build_toc_milestone_block(milestone) -> dict:
        """Build a single milestone TOC entry with nested epics."""
        epic_blocks = []
        for epic in milestone.epics:
            epic_blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"🏗️ {epic.name}"},
                            },
                            {
                                "type": "text",
                                "text": {"content": f" ({epic.estimated_hours}h, {len(epic.stories)} stories)"},
                                "annotations": {"color": "gray"},
                            },
                        ]
                    },
                }
            )

        ms_block: dict = {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"📋 {milestone.name}"},
                        "annotations": {"bold": True},
                    },
                    {
                        "type": "text",
                        "text": {"content": f" — {milestone.goal}"},
                    },
                    {
                        "type": "text",
                        "text": {"content": f" ({milestone.estimated_hours}h)"},
                        "annotations": {"color": "gray"},
                    },
                ]
            },
        }
        if epic_blocks:
            ms_block["bulleted_list_item"]["children"] = epic_blocks
        return ms_block

    @classmethod
    def _build_toc_blocks(cls, roadmap: Roadmap) -> list[dict]:
        """Build a roadmap table of contents (milestones + epics only)."""
        blocks = cls._build_toc_header_blocks(roadmap)
        for milestone in roadmap.milestones:
            blocks.append(cls._build_toc_milestone_block(milestone))
        return blocks

    # -- Property builders for item pages --

    @staticmethod
    def _title_property(text: str) -> dict:
        return {"title": [{"type": "text", "text": {"content": text}}]}

    @classmethod
    def _rich_text_property(cls, text: str) -> dict:
        return {"rich_text": cls._chunk_rich_text(text)}

    @staticmethod
    def _select_property(name: str) -> dict:
        return {"select": {"name": name}}

    @staticmethod
    def _number_property(value: int | float) -> dict:
        return {"number": value}

    @staticmethod
    def _relation_property(page_ids: list[str]) -> dict:
        return {"relation": [{"id": pid} for pid in page_ids]}

    @staticmethod
    def _multi_select_property(names: list[str]) -> dict:
        return {"multi_select": [{"name": n} for n in names]}

    # -- Main export --

    async def export(
        self,
        roadmap: Roadmap,
        progress_callback: ProgressCallback | None = None,
        parent_page_id: str | None = None,
        **kwargs,
    ) -> ExportResult:
        """Export roadmap to Notion.

        Creates 4 databases + documentation pages under the parent page,
        then populates all items with relations preserved.
        """
        if not parent_page_id:
            raise ValueError(
                "parent_page_id is required for Notion export. "
                "Pass the Notion page ID where databases should be created."
            )

        id_mapping: dict[str, str] = {}
        items_by_type: dict[str, int] = {
            "milestones": 0,
            "epics": 0,
            "stories": 0,
            "tasks": 0,
        }
        warnings: list[str] = []

        # Step 0: Set parent page icon if it doesn't have one
        await self._ensure_parent_icon(parent_page_id, "🔮")

        # Step 1: Create databases
        try:
            milestones_db_id = await self._create_database(
                parent_page_id,
                f"{roadmap.project_name} — Milestones",
                self._build_milestones_db_properties(),
                icon=DB_ICONS["milestones"],
            )
            epics_db_id = await self._create_database(
                parent_page_id,
                f"{roadmap.project_name} — Epics",
                self._build_epics_db_properties(milestones_db_id),
                icon=DB_ICONS["epics"],
            )
            stories_db_id = await self._create_database(
                parent_page_id,
                f"{roadmap.project_name} — Stories",
                self._build_stories_db_properties(epics_db_id),
                icon=DB_ICONS["stories"],
            )
            tasks_db_id = await self._create_database(
                parent_page_id,
                f"{roadmap.project_name} — Tasks",
                self._build_tasks_db_properties(stories_db_id),
                icon=DB_ICONS["tasks"],
            )
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            return ExportResult(
                success=False,
                target=self.name,
                items_created=0,
                errors=[f"Failed to create databases: {e}"],
            )

        # Step 2: Create documentation pages
        try:
            await self._create_doc_pages(parent_page_id, roadmap)
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            warnings.append(f"Failed to create documentation pages: {e}")

        # Step 3: Walk hierarchy and create items
        for milestone in roadmap.milestones:
            # Create milestone page
            ms_props = {
                "Name": self._title_property(milestone.name),
                "Goal": self._rich_text_property(milestone.goal),
                "Priority": self._select_property(
                    PRIORITY_MAP[milestone.priority.value]
                ),
                "Stage": self._select_property(
                    STATUS_MAP[milestone.status.value]
                ),
                "Estimated Points": self._number_property(
                    milestone.estimated_hours
                ),
            }
            if milestone.labels:
                ms_props["Labels"] = self._multi_select_property(milestone.labels)
            if milestone.target_date:
                ms_props["Target Date"] = {"date": {"start": milestone.target_date}}

            ms_children = self._build_description_blocks(milestone.description)

            try:
                ms_page_id = await self._create_page(
                    milestones_db_id, ms_props, ms_children,
                    icon=ITEM_ICONS["milestone"],
                )
                id_mapping[milestone.id] = ms_page_id
                items_by_type["milestones"] += 1
                if progress_callback:
                    progress_callback("Milestone", milestone.name)
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                warnings.append(f"Failed to create milestone '{milestone.name}': {e}")
                continue

            for epic in milestone.epics:
                # Create epic page
                ep_props = {
                    "Name": self._title_property(epic.name),
                    "Goal": self._rich_text_property(epic.goal),
                    "Priority": self._select_property(
                        PRIORITY_MAP[epic.priority.value]
                    ),
                    "Stage": self._select_property(
                        STATUS_MAP[epic.status.value]
                    ),
                    "Estimated Points": self._number_property(
                        epic.estimated_hours
                    ),
                    "Milestone": self._relation_property([ms_page_id]),
                }
                if epic.labels:
                    ep_props["Labels"] = self._multi_select_property(epic.labels)

                ep_children = self._build_description_blocks(epic.description)
                ep_children.append(
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {"type": "text", "text": {"content": epic.goal}}
                            ],
                            "icon": {"type": "emoji", "emoji": "🎯"},
                        },
                    }
                )

                try:
                    ep_page_id = await self._create_page(
                        epics_db_id, ep_props, ep_children,
                        icon=ITEM_ICONS["epic"],
                    )
                    id_mapping[epic.id] = ep_page_id
                    items_by_type["epics"] += 1
                    if progress_callback:
                        progress_callback("Epic", epic.name)
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    warnings.append(f"Failed to create epic '{epic.name}': {e}")
                    continue

                for story in epic.stories:
                    # Create story page
                    st_props = {
                        "Name": self._title_property(story.name),
                        "Priority": self._select_property(
                            PRIORITY_MAP[story.priority.value]
                        ),
                        "Stage": self._select_property(
                            STATUS_MAP[story.status.value]
                        ),
                        "Estimated Points": self._number_property(
                            story.estimated_hours
                        ),
                        "Epic": self._relation_property([ep_page_id]),
                    }
                    if story.labels:
                        st_props["Labels"] = self._multi_select_property(
                            story.labels
                        )

                    st_children = self._build_description_blocks(story.description)
                    st_children.extend(
                        self._build_acceptance_criteria_blocks(
                            story.acceptance_criteria
                        )
                    )

                    try:
                        st_page_id = await self._create_page(
                            stories_db_id, st_props, st_children,
                            icon=ITEM_ICONS["story"],
                        )
                        id_mapping[story.id] = st_page_id
                        items_by_type["stories"] += 1
                        if progress_callback:
                            progress_callback("Story", story.name)
                    except (httpx.HTTPStatusError, httpx.RequestError) as e:
                        warnings.append(
                            f"Failed to create story '{story.name}': {e}"
                        )
                        continue

                    for task in story.tasks:
                        # Create task page
                        t_props = {
                            "Name": self._title_property(task.name),
                            "Priority": self._select_property(
                                PRIORITY_MAP[task.priority.value]
                            ),
                            "Stage": self._select_property(
                                STATUS_MAP[task.status.value]
                            ),
                            "Estimated Points": self._number_property(
                                task.estimated_hours
                            ),
                            "Story": self._relation_property([st_page_id]),
                        }
                        if task.labels:
                            t_props["Labels"] = self._multi_select_property(
                                task.labels
                            )
                        if task.prerequisites:
                            t_props["Prerequisites"] = self._rich_text_property(
                                ", ".join(task.prerequisites)
                            )

                        t_children = self._build_description_blocks(
                            task.description
                        )

                        try:
                            t_page_id = await self._create_page(
                                tasks_db_id, t_props, t_children,
                                icon=ITEM_ICONS["task"],
                            )
                            id_mapping[task.id] = t_page_id
                            items_by_type["tasks"] += 1
                            if progress_callback:
                                progress_callback("Task", task.name)
                        except (httpx.HTTPStatusError, httpx.RequestError) as e:
                            warnings.append(
                                f"Failed to create task '{task.name}': {e}"
                            )
                            continue

                        # Append extra content blocks
                        extra_blocks: list[dict] = []
                        if task.acceptance_criteria:
                            extra_blocks.extend(
                                self._build_acceptance_criteria_blocks(
                                    task.acceptance_criteria
                                )
                            )
                        if task.implementation_notes:
                            extra_blocks.extend(
                                self._build_implementation_notes_blocks(
                                    task.implementation_notes
                                )
                            )
                        if task.claude_code_prompt:
                            extra_blocks.extend(
                                self._build_claude_code_prompt_blocks(
                                    task.claude_code_prompt
                                )
                            )

                        if extra_blocks:
                            try:
                                await self._append_blocks(t_page_id, extra_blocks)
                            except (
                                httpx.HTTPStatusError,
                                httpx.RequestError,
                            ) as e:
                                warnings.append(
                                    f"Failed to add content blocks to task "
                                    f"'{task.name}': {e}"
                                )

        # Step 4: Append table of contents to parent page (chunked per-milestone)
        try:
            header_blocks = self._build_toc_header_blocks(roadmap)
            await self._append_blocks(parent_page_id, header_blocks)
            for milestone in roadmap.milestones:
                ms_block = self._build_toc_milestone_block(milestone)
                await self._append_blocks(parent_page_id, [ms_block])
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            warnings.append(f"Failed to add table of contents: {e}")

        total_created = sum(items_by_type.values())
        url = f"https://notion.so/{parent_page_id.replace('-', '')}"

        return ExportResult(
            success=True,
            target=self.name,
            items_created=total_created,
            items_by_type=items_by_type,
            id_mapping=id_mapping,
            warnings=warnings,
            url=url,
        )

    async def _create_doc_pages(
        self, parent_page_id: str, roadmap: Roadmap
    ) -> None:
        """Create documentation pages under the parent page."""
        pages = build_all_pages(roadmap.context)
        for page in pages:
            blocks: list[dict] = []
            for section in page.sections:
                blocks.extend(self._doc_section_to_blocks(section))
            icon = DOC_PAGE_ICONS.get(page.title)
            await self._create_child_page(
                parent_page_id, page.title, blocks, icon=icon
            )
