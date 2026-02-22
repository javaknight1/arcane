"""Tests for arcane.project_management.notion module."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from arcane.project_management.docs import DocSection
from arcane.project_management.notion import (
    PRIORITY_MAP,
    STATUS_MAP,
    NotionClient,
)


# -- Helpers --


def _make_page_response(page_id: str) -> dict:
    """Create a fake Notion API page response."""
    return {"id": page_id, "object": "page"}


def _make_db_response(db_id: str) -> dict:
    """Create a fake Notion API database response."""
    return {"id": db_id, "object": "database"}


def _make_block_response() -> dict:
    """Create a fake Notion API block append response."""
    return {"object": "list", "results": []}


class TestNotionBlockBuilders:
    """Unit tests for block-building helpers."""

    def test_description_blocks(self):
        blocks = NotionClient._build_description_blocks("My description")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"
        text = blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]
        assert text == "My description"

    def test_acceptance_criteria_blocks(self):
        criteria = ["Criterion A", "Criterion B"]
        blocks = NotionClient._build_acceptance_criteria_blocks(criteria)
        assert blocks[0]["type"] == "heading_2"
        assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Acceptance Criteria"
        assert blocks[1]["type"] == "to_do"
        assert blocks[1]["to_do"]["rich_text"][0]["text"]["content"] == "Criterion A"
        assert blocks[1]["to_do"]["checked"] is False
        assert blocks[2]["type"] == "to_do"
        assert blocks[2]["to_do"]["rich_text"][0]["text"]["content"] == "Criterion B"

    def test_implementation_notes_blocks(self):
        blocks = NotionClient._build_implementation_notes_blocks("Use pattern X")
        assert len(blocks) == 2
        assert blocks[0]["type"] == "heading_2"
        assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Implementation Notes"
        assert blocks[1]["type"] == "paragraph"
        assert blocks[1]["paragraph"]["rich_text"][0]["text"]["content"] == "Use pattern X"

    def test_claude_code_prompt_blocks(self):
        blocks = NotionClient._build_claude_code_prompt_blocks("Do the thing")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "toggle"
        toggle = blocks[0]["toggle"]
        assert toggle["rich_text"][0]["text"]["content"] == "Claude Code Prompt"
        children = toggle["children"]
        assert len(children) == 1
        assert children[0]["type"] == "code"
        assert children[0]["code"]["rich_text"][0]["text"]["content"] == "Do the thing"

    def test_doc_section_paragraph(self):
        section = DocSection(
            title="Overview", content_type="paragraph", items=["Line one", "Line two"]
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "paragraph"
        assert blocks[1]["paragraph"]["rich_text"][0]["text"]["content"] == "Line one"
        assert blocks[2]["type"] == "paragraph"
        assert blocks[2]["paragraph"]["rich_text"][0]["text"]["content"] == "Line two"

    def test_doc_section_bullet_list(self):
        section = DocSection(
            title="Items", content_type="bullet_list", items=["A", "B"]
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "bulleted_list_item"
        assert blocks[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "A"
        assert blocks[2]["type"] == "bulleted_list_item"

    def test_doc_section_checklist(self):
        section = DocSection(
            title="Todo", content_type="checklist", items=["Do X", "Do Y"]
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "to_do"
        assert blocks[1]["to_do"]["checked"] is False
        assert blocks[2]["type"] == "to_do"

    def test_doc_section_callout(self):
        section = DocSection(
            title="Note", content_type="callout", items=["Important info"], icon="⚠️"
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "callout"
        callout = blocks[1]["callout"]
        assert callout["rich_text"][0]["text"]["content"] == "Important info"
        assert callout["icon"]["emoji"] == "⚠️"

    def test_doc_section_callout_default_icon(self):
        section = DocSection(
            title="Note", content_type="callout", items=["Info"]
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        callout = blocks[1]["callout"]
        assert callout["icon"]["emoji"] == "💡"

    def test_doc_section_paragraph_long_text(self):
        """Paragraph items exceeding 2000 chars are chunked into multiple rich_text elements."""
        long_text = "a" * 2500
        section = DocSection(
            title="Overview", content_type="paragraph", items=[long_text]
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[1]["type"] == "paragraph"
        rich_text = blocks[1]["paragraph"]["rich_text"]
        assert len(rich_text) >= 2
        assert all(len(e["text"]["content"]) <= 2000 for e in rich_text)
        reconstructed = "".join(e["text"]["content"] for e in rich_text)
        assert reconstructed == long_text

    def test_doc_section_bullet_list_long_text(self):
        """Bullet list items exceeding 2000 chars are chunked."""
        long_text = "b" * 2500
        section = DocSection(
            title="Items", content_type="bullet_list", items=[long_text]
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[1]["type"] == "bulleted_list_item"
        rich_text = blocks[1]["bulleted_list_item"]["rich_text"]
        assert len(rich_text) >= 2
        assert all(len(e["text"]["content"]) <= 2000 for e in rich_text)

    def test_doc_section_checklist_long_text(self):
        """Checklist items exceeding 2000 chars are chunked."""
        long_text = "c" * 2500
        section = DocSection(
            title="Todo", content_type="checklist", items=[long_text]
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[1]["type"] == "to_do"
        rich_text = blocks[1]["to_do"]["rich_text"]
        assert len(rich_text) >= 2
        assert all(len(e["text"]["content"]) <= 2000 for e in rich_text)

    def test_doc_section_callout_long_text(self):
        """Callout content exceeding 2000 chars is chunked."""
        long_text = "d" * 2500
        section = DocSection(
            title="Note", content_type="callout", items=[long_text], icon="⚠️"
        )
        blocks = NotionClient._doc_section_to_blocks(section)
        assert blocks[1]["type"] == "callout"
        rich_text = blocks[1]["callout"]["rich_text"]
        assert len(rich_text) >= 2
        assert all(len(e["text"]["content"]) <= 2000 for e in rich_text)

    def test_acceptance_criteria_long_text(self):
        """Long acceptance criteria items are chunked into multiple rich_text elements."""
        long_criterion = "e" * 2500
        blocks = NotionClient._build_acceptance_criteria_blocks([long_criterion])
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "to_do"
        rich_text = blocks[1]["to_do"]["rich_text"]
        assert len(rich_text) >= 2
        assert all(len(e["text"]["content"]) <= 2000 for e in rich_text)


class TestNotionChunkRichText:
    """Tests for _chunk_rich_text helper."""

    def test_short_text_single_element(self):
        result = NotionClient._chunk_rich_text("Hello world")
        assert len(result) == 1
        assert result[0]["text"]["content"] == "Hello world"

    def test_exact_limit_single_element(self):
        text = "a" * 2000
        result = NotionClient._chunk_rich_text(text)
        assert len(result) == 1
        assert result[0]["text"]["content"] == text

    def test_over_limit_splits(self):
        text = "a" * 2001
        result = NotionClient._chunk_rich_text(text)
        assert len(result) == 2
        assert all(len(e["text"]["content"]) <= 2000 for e in result)

    def test_splits_on_newline(self):
        text = "a" * 1999 + "\n" + "b" * 100
        result = NotionClient._chunk_rich_text(text)
        assert len(result) == 2
        assert result[0]["text"]["content"] == "a" * 1999
        assert result[1]["text"]["content"] == "b" * 100

    def test_splits_on_space(self):
        text = "a" * 1999 + " " + "b" * 100
        result = NotionClient._chunk_rich_text(text)
        assert len(result) == 2
        assert result[0]["text"]["content"] == "a" * 1999

    def test_hard_split_no_boundary(self):
        text = "a" * 3000  # No spaces or newlines
        result = NotionClient._chunk_rich_text(text)
        assert len(result) == 2
        assert len(result[0]["text"]["content"]) == 2000
        assert len(result[1]["text"]["content"]) == 1000

    def test_custom_max_len(self):
        text = "hello world foo bar"
        result = NotionClient._chunk_rich_text(text, max_len=11)
        assert len(result) == 3
        assert result[0]["text"]["content"] == "hello"
        assert all(len(e["text"]["content"]) <= 11 for e in result)

    def test_empty_text(self):
        result = NotionClient._chunk_rich_text("")
        assert len(result) == 1
        assert result[0]["text"]["content"] == ""

    def test_long_text_multiple_chunks(self):
        # 5000 chars with spaces every 100 chars
        text = " ".join(["a" * 99] * 50)  # ~5000 chars
        result = NotionClient._chunk_rich_text(text)
        assert all(len(e["text"]["content"]) <= 2000 for e in result)
        # Reconstruct should contain all content
        reconstructed = "".join(e["text"]["content"] for e in result)
        # Some leading spaces may be consumed at split points, but all 'a' chars preserved
        assert reconstructed.count("a") == text.count("a")


class TestNotionTOC:
    """Tests for table of contents block builder."""

    def test_toc_has_divider_and_heading(self, sample_roadmap):
        blocks = NotionClient._build_toc_blocks(sample_roadmap)
        assert blocks[0]["type"] == "divider"
        assert blocks[1]["type"] == "heading_1"
        assert blocks[1]["heading_1"]["rich_text"][0]["text"]["content"] == "Roadmap Overview"

    def test_toc_has_summary_paragraph(self, sample_roadmap):
        blocks = NotionClient._build_toc_blocks(sample_roadmap)
        para = blocks[2]
        assert para["type"] == "paragraph"
        text_parts = [rt["text"]["content"] for rt in para["paragraph"]["rich_text"]]
        full_text = "".join(text_parts)
        assert "6 hours" in full_text
        assert "1 milestones" in full_text
        assert "2 tasks" in full_text

    def test_toc_has_milestone_entry(self, sample_roadmap):
        blocks = NotionClient._build_toc_blocks(sample_roadmap)
        # blocks[3] should be the milestone bullet
        ms_block = blocks[3]
        assert ms_block["type"] == "bulleted_list_item"
        text = ms_block["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        assert "MVP" in text

    def test_toc_nests_epics_under_milestones(self, sample_roadmap):
        blocks = NotionClient._build_toc_blocks(sample_roadmap)
        ms_block = blocks[3]
        children = ms_block["bulleted_list_item"]["children"]
        assert len(children) == 1
        epic_text = children[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        assert "Authentication" in epic_text

    def test_toc_epics_show_story_count(self, sample_roadmap):
        blocks = NotionClient._build_toc_blocks(sample_roadmap)
        epic_block = blocks[3]["bulleted_list_item"]["children"][0]
        epic_texts = [
            rt["text"]["content"]
            for rt in epic_block["bulleted_list_item"]["rich_text"]
        ]
        full_text = "".join(epic_texts)
        assert "1 stories" in full_text

    def test_toc_does_not_nest_stories(self, sample_roadmap):
        """TOC only goes to epics level, not stories/tasks."""
        blocks = NotionClient._build_toc_blocks(sample_roadmap)
        epic_block = blocks[3]["bulleted_list_item"]["children"][0]
        assert "children" not in epic_block["bulleted_list_item"]

    def test_toc_includes_hours(self, sample_roadmap):
        blocks = NotionClient._build_toc_blocks(sample_roadmap)
        # Check milestone has hours
        ms_texts = [
            rt["text"]["content"]
            for rt in blocks[3]["bulleted_list_item"]["rich_text"]
        ]
        assert any("6h" in t for t in ms_texts)

    def test_toc_header_blocks_separate(self, sample_roadmap):
        header = NotionClient._build_toc_header_blocks(sample_roadmap)
        assert len(header) == 3
        assert header[0]["type"] == "divider"
        assert header[1]["type"] == "heading_1"
        assert header[2]["type"] == "paragraph"

    def test_toc_milestone_block_separate(self, sample_roadmap):
        milestone = sample_roadmap.milestones[0]
        block = NotionClient._build_toc_milestone_block(milestone)
        assert block["type"] == "bulleted_list_item"
        text = block["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        assert "MVP" in text


class TestNotionDatabaseSchemas:
    """Unit tests for database property builders."""

    def test_milestones_db_properties(self):
        client = NotionClient(api_key="test")
        props = client._build_milestones_db_properties()
        assert "Name" in props
        assert "title" in props["Name"]
        assert "Goal" in props
        assert "rich_text" in props["Goal"]
        assert "Target Date" in props
        assert "date" in props["Target Date"]
        assert "Priority" in props
        assert "select" in props["Priority"]
        assert "Stage" in props
        assert "Labels" in props
        assert "multi_select" in props["Labels"]
        assert "Estimated Points" in props
        assert "number" in props["Estimated Points"]

    def test_epics_db_properties(self):
        client = NotionClient(api_key="test")
        props = client._build_epics_db_properties("ms-db-id")
        assert "Name" in props
        assert "Goal" in props
        assert "Milestone" in props
        relation = props["Milestone"]["relation"]
        assert relation["database_id"] == "ms-db-id"

    def test_stories_db_properties(self):
        client = NotionClient(api_key="test")
        props = client._build_stories_db_properties("ep-db-id")
        assert "Name" in props
        assert "Epic" in props
        relation = props["Epic"]["relation"]
        assert relation["database_id"] == "ep-db-id"

    def test_tasks_db_properties(self):
        client = NotionClient(api_key="test")
        props = client._build_tasks_db_properties("st-db-id")
        assert "Name" in props
        assert "Story" in props
        assert "Prerequisites" in props
        assert "rich_text" in props["Prerequisites"]
        relation = props["Story"]["relation"]
        assert relation["database_id"] == "st-db-id"


class TestNotionStatusMapping:
    """Tests for status enum mapping."""

    def test_all_statuses_mapped(self):
        expected = {"not_started", "in_progress", "blocked", "completed"}
        assert set(STATUS_MAP.keys()) == expected

    def test_not_started(self):
        assert STATUS_MAP["not_started"] == "Not Started"

    def test_in_progress(self):
        assert STATUS_MAP["in_progress"] == "In Progress"

    def test_blocked(self):
        assert STATUS_MAP["blocked"] == "Blocked"

    def test_completed(self):
        assert STATUS_MAP["completed"] == "Completed"


class TestNotionPriorityMapping:
    """Tests for priority enum mapping."""

    def test_all_priorities_mapped(self):
        expected = {"critical", "high", "medium", "low"}
        assert set(PRIORITY_MAP.keys()) == expected

    def test_critical(self):
        assert PRIORITY_MAP["critical"] == "Critical"

    def test_high(self):
        assert PRIORITY_MAP["high"] == "High"

    def test_medium(self):
        assert PRIORITY_MAP["medium"] == "Medium"

    def test_low(self):
        assert PRIORITY_MAP["low"] == "Low"


class TestNotionExport:
    """Integration tests for export flow with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_export_requires_parent_page_id(self, sample_roadmap):
        client = NotionClient(api_key="test")
        with pytest.raises(ValueError, match="parent_page_id is required"):
            await client.export(sample_roadmap)

    @pytest.mark.asyncio
    async def test_export_creates_databases(self, sample_roadmap):
        client = NotionClient(api_key="test")
        db_call_count = 0

        async def mock_request(method, endpoint, json=None):
            nonlocal db_call_count
            if endpoint == "/databases":
                db_call_count += 1
                return _make_db_response(f"db-{db_call_count}")
            if endpoint == "/pages":
                return _make_page_response(f"page-{id(json)}")
            if "/children" in endpoint:
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        await client.export(sample_roadmap, parent_page_id="parent-123")
        assert db_call_count == 4

    @pytest.mark.asyncio
    async def test_export_creates_all_items(self, sample_roadmap):
        """Verifies correct page count: 1 milestone + 1 epic + 1 story + 2 tasks = 5."""
        client = NotionClient(api_key="test")
        page_calls = []
        db_count = 0

        async def mock_request(method, endpoint, json=None):
            nonlocal db_count
            if endpoint == "/databases":
                db_count += 1
                return _make_db_response(f"db-{db_count}")
            if endpoint == "/pages":
                page_calls.append(json)
                return _make_page_response(f"page-{len(page_calls)}")
            if "/children" in endpoint:
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        result = await client.export(sample_roadmap, parent_page_id="parent-123")

        assert result.success is True
        assert result.items_created == 5
        # 5 item pages + 4 doc pages = 9 total page creation calls
        assert len(page_calls) == 9

    @pytest.mark.asyncio
    async def test_export_returns_id_mapping(self, sample_roadmap):
        client = NotionClient(api_key="test")
        call_count = 0
        db_count = 0

        async def mock_request(method, endpoint, json=None):
            nonlocal call_count, db_count
            if endpoint == "/databases":
                db_count += 1
                return _make_db_response(f"db-{db_count}")
            if endpoint == "/pages":
                call_count += 1
                return _make_page_response(f"notion-page-{call_count}")
            if "/children" in endpoint:
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        result = await client.export(sample_roadmap, parent_page_id="parent-123")

        assert "milestone-001" in result.id_mapping
        assert "epic-001" in result.id_mapping
        assert "story-001" in result.id_mapping
        assert "task-001" in result.id_mapping
        assert "task-002" in result.id_mapping
        assert len(result.id_mapping) == 5

    @pytest.mark.asyncio
    async def test_export_returns_items_by_type(self, sample_roadmap):
        client = NotionClient(api_key="test")
        db_count = 0

        async def mock_request(method, endpoint, json=None):
            nonlocal db_count
            if endpoint == "/databases":
                db_count += 1
                return _make_db_response(f"db-{db_count}")
            if endpoint == "/pages":
                return _make_page_response("page-id")
            if "/children" in endpoint:
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        result = await client.export(sample_roadmap, parent_page_id="parent-123")

        assert result.items_by_type == {
            "milestones": 1,
            "epics": 1,
            "stories": 1,
            "tasks": 2,
        }

    @pytest.mark.asyncio
    async def test_export_creates_doc_pages(self, sample_roadmap):
        client = NotionClient(api_key="test")
        doc_page_calls = []
        db_count = 0

        async def mock_request(method, endpoint, json=None):
            nonlocal db_count
            if endpoint == "/databases":
                db_count += 1
                return _make_db_response(f"db-{db_count}")
            if endpoint == "/pages":
                # Doc pages have parent.page_id, item pages have parent.database_id
                if json and "parent" in json and "page_id" in json.get("parent", {}):
                    doc_page_calls.append(json)
                return _make_page_response("page-id")
            if "/children" in endpoint:
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        await client.export(sample_roadmap, parent_page_id="parent-123")

        # 4 doc pages: Project Overview, Requirements, Technical Decisions, Team & Constraints
        assert len(doc_page_calls) == 4

    @pytest.mark.asyncio
    async def test_export_sets_relations(self, sample_roadmap):
        """Epic page has milestone relation, story has epic, task has story."""
        client = NotionClient(api_key="test")
        item_pages = []
        db_count = 0
        page_count = 0

        async def mock_request(method, endpoint, json=None):
            nonlocal db_count, page_count
            if endpoint == "/databases":
                db_count += 1
                return _make_db_response(f"db-{db_count}")
            if endpoint == "/pages":
                page_count += 1
                page_id = f"page-{page_count}"
                # Track item pages (those with database_id parent)
                if json and "parent" in json and "database_id" in json.get("parent", {}):
                    item_pages.append({"page_id": page_id, "props": json["properties"]})
                return _make_page_response(page_id)
            if "/children" in endpoint:
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        await client.export(sample_roadmap, parent_page_id="parent-123")

        # item_pages order: milestone, epic, story, task1, task2
        assert len(item_pages) == 5

        # Epic should reference milestone page
        epic_page = item_pages[1]
        assert "Milestone" in epic_page["props"]
        ms_relation = epic_page["props"]["Milestone"]["relation"]
        assert len(ms_relation) == 1
        assert ms_relation[0]["id"] == item_pages[0]["page_id"]

        # Story should reference epic page
        story_page = item_pages[2]
        assert "Epic" in story_page["props"]
        ep_relation = story_page["props"]["Epic"]["relation"]
        assert ep_relation[0]["id"] == item_pages[1]["page_id"]

        # Task should reference story page
        task_page = item_pages[3]
        assert "Story" in task_page["props"]
        st_relation = task_page["props"]["Story"]["relation"]
        assert st_relation[0]["id"] == item_pages[2]["page_id"]

    @pytest.mark.asyncio
    async def test_export_handles_api_error(self, sample_roadmap):
        """Single page failure results in warning, not overall failure."""
        client = NotionClient(api_key="test")
        db_count = 0
        page_count = 0

        async def mock_request(method, endpoint, json=None):
            nonlocal db_count, page_count
            if endpoint == "/databases":
                db_count += 1
                return _make_db_response(f"db-{db_count}")
            if endpoint == "/pages":
                page_count += 1
                # Fail the epic page creation (5th call = after 4 doc pages + milestone)
                if page_count == 6:
                    raise httpx.HTTPStatusError(
                        "Bad Request",
                        request=httpx.Request("POST", "https://api.notion.com/v1/pages"),
                        response=httpx.Response(400),
                    )
                return _make_page_response(f"page-{page_count}")
            if "/children" in endpoint:
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        result = await client.export(sample_roadmap, parent_page_id="parent-123")

        # Export should still succeed overall
        assert result.success is True
        # But should have warnings about the failed epic
        assert len(result.warnings) >= 1
        assert any("epic" in w.lower() or "Epic" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_export_rate_limited_retries(self, sample_roadmap):
        """429 response triggers retry."""
        client = NotionClient(api_key="test")
        call_count = 0

        # We'll test _request directly with a mocked httpx client
        async def mock_request_fn(method, url, headers=None, json=None, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(
                    429,
                    headers={"Retry-After": "0.01"},
                    request=httpx.Request(method, url),
                )
            return httpx.Response(
                200,
                json=_make_db_response("db-1"),
                request=httpx.Request(method, url),
            )

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request = AsyncMock(side_effect=mock_request_fn)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            mock_async_client.return_value = mock_client_instance

            result = await client._request("POST", "/databases", json={})
            assert result["id"] == "db-1"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_export_appends_toc_to_parent(self, sample_roadmap):
        """Export appends a table of contents to the parent page in chunks."""
        client = NotionClient(api_key="test")
        db_count = 0
        append_calls = []

        async def mock_request(method, endpoint, json=None):
            nonlocal db_count
            if endpoint == "/databases":
                db_count += 1
                return _make_db_response(f"db-{db_count}")
            if endpoint == "/pages":
                return _make_page_response("page-id")
            if "/children" in endpoint:
                append_calls.append({"endpoint": endpoint, "json": json})
                return _make_block_response()
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        await client.export(sample_roadmap, parent_page_id="parent-123")

        # TOC is appended in chunks: header (1 call) + 1 per milestone
        toc_calls = [c for c in append_calls if "parent-123" in c["endpoint"]]
        assert len(toc_calls) == 2  # header + 1 milestone

        # First call has the header blocks (divider, heading, paragraph)
        header_blocks = toc_calls[0]["json"]["children"]
        header_types = [b["type"] for b in header_blocks]
        assert "divider" in header_types
        assert "heading_1" in header_types

        # Second call has the milestone block
        ms_blocks = toc_calls[1]["json"]["children"]
        assert len(ms_blocks) == 1
        assert ms_blocks[0]["type"] == "bulleted_list_item"

    @pytest.mark.asyncio
    async def test_export_database_failure_returns_failure(self, sample_roadmap):
        """If database creation fails, export returns success=False."""
        client = NotionClient(api_key="test")

        async def mock_request(method, endpoint, json=None):
            if endpoint == "/databases":
                raise httpx.HTTPStatusError(
                    "Forbidden",
                    request=httpx.Request("POST", "https://api.notion.com/v1/databases"),
                    response=httpx.Response(403),
                )
            return {}

        client._request = AsyncMock(side_effect=mock_request)
        result = await client.export(sample_roadmap, parent_page_id="parent-123")

        assert result.success is False
        assert len(result.errors) >= 1
        assert "databases" in result.errors[0].lower() or "Failed" in result.errors[0]
