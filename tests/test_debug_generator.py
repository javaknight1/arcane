"""Tests for debug mode generator with LLM reasoning capture."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from arcane.engines.generation.debug_generator import (
    DebugGenerator,
    DebugSession,
    GenerationReasoning,
    ConfidenceLevel,
)


class TestGenerationReasoning:
    """Tests for GenerationReasoning dataclass."""

    def test_creation(self):
        """Test creating a GenerationReasoning instance."""
        reasoning = GenerationReasoning(
            item_id="1.0",
            item_type="epic",
            reasoning="Chose this structure because...",
            assumptions=["Assumption 1", "Assumption 2"],
            uncertainties=["Uncertainty 1"],
            confidence_level=ConfidenceLevel.HIGH,
        )

        assert reasoning.item_id == "1.0"
        assert reasoning.item_type == "epic"
        assert len(reasoning.assumptions) == 2
        assert len(reasoning.uncertainties) == 1
        assert reasoning.confidence_level == ConfidenceLevel.HIGH

    def test_to_dict(self):
        """Test serialization to dictionary."""
        reasoning = GenerationReasoning(
            item_id="1.0.1",
            item_type="story",
            reasoning="Because login is essential",
            assumptions=["Users need accounts"],
            uncertainties=[],
            confidence_level=ConfidenceLevel.MEDIUM,
        )

        result = reasoning.to_dict()

        assert result['item_id'] == "1.0.1"
        assert result['item_type'] == "story"
        assert result['confidence_level'] == "medium"
        assert 'timestamp' in result


class TestDebugSession:
    """Tests for DebugSession class."""

    def test_creation(self):
        """Test creating a debug session."""
        session = DebugSession(
            session_id="test_session",
            started_at=datetime.now()
        )

        assert session.session_id == "test_session"
        assert len(session.entries) == 0

    def test_add_entry(self):
        """Test adding entries to session."""
        session = DebugSession(
            session_id="test",
            started_at=datetime.now()
        )

        entry = GenerationReasoning(
            item_id="1",
            item_type="milestone",
            reasoning="Test",
            assumptions=[],
            uncertainties=[],
            confidence_level=ConfidenceLevel.HIGH,
        )

        session.add_entry(entry)
        assert len(session.entries) == 1

    def test_get_low_confidence_items(self):
        """Test filtering low confidence items."""
        session = DebugSession(
            session_id="test",
            started_at=datetime.now()
        )

        session.add_entry(GenerationReasoning(
            item_id="1", item_type="milestone",
            reasoning="", assumptions=[], uncertainties=[],
            confidence_level=ConfidenceLevel.HIGH,
        ))
        session.add_entry(GenerationReasoning(
            item_id="2", item_type="epic",
            reasoning="", assumptions=[], uncertainties=[],
            confidence_level=ConfidenceLevel.LOW,
        ))
        session.add_entry(GenerationReasoning(
            item_id="3", item_type="story",
            reasoning="", assumptions=[], uncertainties=[],
            confidence_level=ConfidenceLevel.LOW,
        ))

        low_confidence = session.get_low_confidence_items()
        assert len(low_confidence) == 2
        assert all(e.confidence_level == ConfidenceLevel.LOW for e in low_confidence)

    def test_get_items_with_uncertainties(self):
        """Test filtering items with uncertainties."""
        session = DebugSession(
            session_id="test",
            started_at=datetime.now()
        )

        session.add_entry(GenerationReasoning(
            item_id="1", item_type="milestone",
            reasoning="", assumptions=[], uncertainties=["Not sure about X"],
            confidence_level=ConfidenceLevel.MEDIUM,
        ))
        session.add_entry(GenerationReasoning(
            item_id="2", item_type="epic",
            reasoning="", assumptions=[], uncertainties=[],
            confidence_level=ConfidenceLevel.HIGH,
        ))

        uncertain = session.get_items_with_uncertainties()
        assert len(uncertain) == 1
        assert uncertain[0].item_id == "1"

    def test_get_summary(self):
        """Test summary statistics."""
        session = DebugSession(
            session_id="test",
            started_at=datetime.now()
        )

        session.add_entry(GenerationReasoning(
            item_id="1", item_type="milestone",
            reasoning="", assumptions=["A1", "A2"], uncertainties=["U1"],
            confidence_level=ConfidenceLevel.HIGH,
        ))
        session.add_entry(GenerationReasoning(
            item_id="2", item_type="epic",
            reasoning="", assumptions=["A3"], uncertainties=[],
            confidence_level=ConfidenceLevel.MEDIUM,
        ))
        session.add_entry(GenerationReasoning(
            item_id="3", item_type="story",
            reasoning="", assumptions=[], uncertainties=["U2", "U3"],
            confidence_level=ConfidenceLevel.LOW,
        ))

        summary = session.get_summary()

        assert summary['total_items'] == 3
        assert summary['confidence_distribution']['high'] == 1
        assert summary['confidence_distribution']['medium'] == 1
        assert summary['confidence_distribution']['low'] == 1
        assert summary['total_assumptions'] == 3
        assert summary['total_uncertainties'] == 3
        assert summary['items_with_uncertainties'] == 2


class TestDebugGeneratorInit:
    """Tests for DebugGenerator initialization."""

    def test_init_debug_disabled(self):
        """Test initialization with debug disabled."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=False)

        assert generator.llm_client is mock_client
        assert generator.debug_enabled is False
        assert generator.session is None
        assert len(generator.reasoning_log) == 0

    def test_init_debug_enabled(self):
        """Test initialization with debug enabled."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=True)

        assert generator.debug_enabled is True
        assert generator.session is not None
        assert generator.session.session_id is not None

    def test_init_with_custom_session_id(self):
        """Test initialization with custom session ID."""
        mock_client = MagicMock()
        generator = DebugGenerator(
            mock_client,
            debug_enabled=True,
            session_id="custom_session_123"
        )

        assert generator.session.session_id == "custom_session_123"


class TestDebugGeneratorGenerate:
    """Tests for DebugGenerator generation methods."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return MagicMock()

    def test_generate_debug_disabled(self, mock_llm_client):
        """Test generation with debug disabled."""
        mock_llm_client.generate.return_value = "Generated content"

        generator = DebugGenerator(mock_llm_client, debug_enabled=False)
        result = generator.generate("Test prompt", item_id="1.0")

        assert result == "Generated content"
        # Should not add debug suffix
        call_args = mock_llm_client.generate.call_args[0][0]
        assert "REASONING" not in call_args

    def test_generate_debug_enabled(self, mock_llm_client):
        """Test generation with debug enabled adds suffix."""
        mock_llm_client.generate.return_value = """
Generated content here.

=== REASONING (Required in debug mode) ===

**Why This Structure:**
Because it makes sense.

**Assumptions Made:**
- Assumption 1
- Assumption 2

**Uncertainties:**
- Uncertainty 1

**Confidence Level:**
HIGH

=== END REASONING ===
"""
        generator = DebugGenerator(mock_llm_client, debug_enabled=True)
        result = generator.generate("Test prompt", item_id="1.0", item_type="epic")

        # Should not include reasoning in returned content
        assert "=== REASONING" not in result
        assert "Generated content" in result

        # Should capture reasoning
        assert len(generator.reasoning_log) == 1

    def test_generate_with_reasoning_returns_both(self, mock_llm_client):
        """Test generate_with_reasoning returns content and reasoning."""
        mock_llm_client.generate.return_value = """
Content here.

=== REASONING (Required in debug mode) ===

**Why This Structure:**
Explanation.

**Assumptions Made:**
- Assumption 1

**Uncertainties:**
- None

**Confidence Level:**
MEDIUM

=== END REASONING ===
"""
        generator = DebugGenerator(mock_llm_client, debug_enabled=True)
        content, reasoning = generator.generate_with_reasoning(
            "Test prompt",
            item_id="1.0.1",
            item_type="story"
        )

        assert "Content here" in content
        assert reasoning is not None
        assert reasoning.item_id == "1.0.1"
        assert reasoning.item_type == "story"
        assert reasoning.confidence_level == ConfidenceLevel.MEDIUM

    def test_generate_with_reasoning_disabled(self, mock_llm_client):
        """Test generate_with_reasoning when debug disabled."""
        mock_llm_client.generate.return_value = "Plain content"

        generator = DebugGenerator(mock_llm_client, debug_enabled=False)
        content, reasoning = generator.generate_with_reasoning(
            "Test prompt",
            item_id="1.0"
        )

        assert content == "Plain content"
        assert reasoning is None


class TestDebugGeneratorParsing:
    """Tests for debug response parsing."""

    @pytest.fixture
    def generator(self):
        """Create a debug-enabled generator."""
        mock_client = MagicMock()
        return DebugGenerator(mock_client, debug_enabled=True)

    def test_parse_complete_response(self, generator):
        """Test parsing a complete debug response."""
        response = """
This is the generated content.
It has multiple lines.

=== REASONING (Required in debug mode) ===

**Why This Structure:**
I chose this structure because it aligns with best practices
and the project requirements.

**Assumptions Made:**
- The project uses Python
- The team is familiar with REST APIs
- Database is PostgreSQL

**Uncertainties:**
- Not sure about authentication method
- Timeline might be aggressive

**Confidence Level:**
MEDIUM

=== END REASONING ===
"""
        content, reasoning = generator._parse_debug_response(
            response, "1.0", "epic"
        )

        assert "This is the generated content" in content
        assert "=== REASONING" not in content

        assert reasoning is not None
        assert len(reasoning.assumptions) == 3
        assert len(reasoning.uncertainties) == 2
        assert reasoning.confidence_level == ConfidenceLevel.MEDIUM
        assert "best practices" in reasoning.reasoning

    def test_parse_response_without_reasoning(self, generator):
        """Test parsing response without reasoning section."""
        response = "Just plain content without reasoning."

        content, reasoning = generator._parse_debug_response(
            response, "1.0", "milestone"
        )

        assert content == response
        assert reasoning is None

    def test_parse_high_confidence(self, generator):
        """Test parsing HIGH confidence level."""
        response = """
Content.

=== REASONING (Required in debug mode) ===

**Why This Structure:**
Clear requirements.

**Assumptions Made:**
- None

**Uncertainties:**
- None

**Confidence Level:**
HIGH - Very clear requirements

=== END REASONING ===
"""
        _, reasoning = generator._parse_debug_response(response, "1", "milestone")
        assert reasoning.confidence_level == ConfidenceLevel.HIGH

    def test_parse_low_confidence(self, generator):
        """Test parsing LOW confidence level."""
        response = """
Content.

=== REASONING (Required in debug mode) ===

**Why This Structure:**
Had to guess.

**Assumptions Made:**
- Many assumptions

**Uncertainties:**
- Everything

**Confidence Level:**
LOW

=== END REASONING ===
"""
        _, reasoning = generator._parse_debug_response(response, "1", "milestone")
        assert reasoning.confidence_level == ConfidenceLevel.LOW

    def test_parse_unknown_confidence(self, generator):
        """Test parsing when confidence level is missing."""
        response = """
Content.

=== REASONING (Required in debug mode) ===

**Why This Structure:**
Reason.

**Assumptions Made:**
- Assumption

**Uncertainties:**
- Uncertainty

=== END REASONING ===
"""
        _, reasoning = generator._parse_debug_response(response, "1", "milestone")
        assert reasoning.confidence_level == ConfidenceLevel.UNKNOWN

    def test_extract_list_items(self, generator):
        """Test extracting bullet list items."""
        text = """
**Assumptions Made:**
- First assumption
- Second assumption
- Third assumption

**Uncertainties:**
- Some uncertainty
"""
        assumptions = generator._extract_list_items(text, "Assumptions Made")
        assert len(assumptions) == 3
        assert "First assumption" in assumptions

        uncertainties = generator._extract_list_items(text, "Uncertainties")
        assert len(uncertainties) == 1

    def test_extract_list_with_asterisks(self, generator):
        """Test extracting lists with asterisk bullets."""
        text = """
**Assumptions Made:**
* Assumption with asterisk
* Another one

**Other:**
"""
        assumptions = generator._extract_list_items(text, "Assumptions Made")
        assert len(assumptions) == 2


class TestDebugGeneratorHelpers:
    """Tests for debug generator helper methods."""

    @pytest.fixture
    def populated_generator(self):
        """Create generator with populated reasoning log."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=True)

        # Add some entries directly
        generator.reasoning_log = [
            GenerationReasoning(
                item_id="1", item_type="milestone",
                reasoning="R1", assumptions=["A1"], uncertainties=[],
                confidence_level=ConfidenceLevel.HIGH,
            ),
            GenerationReasoning(
                item_id="1.0", item_type="epic",
                reasoning="R2", assumptions=[], uncertainties=["U1"],
                confidence_level=ConfidenceLevel.LOW,
            ),
            GenerationReasoning(
                item_id="1.0.1", item_type="story",
                reasoning="R3", assumptions=["A2"], uncertainties=["U2"],
                confidence_level=ConfidenceLevel.LOW,
            ),
        ]
        generator.session.entries = generator.reasoning_log.copy()

        return generator

    def test_get_reasoning_log(self, populated_generator):
        """Test getting the reasoning log."""
        log = populated_generator.get_reasoning_log()
        assert len(log) == 3
        # Should be a copy
        assert log is not populated_generator.reasoning_log

    def test_get_session(self, populated_generator):
        """Test getting the debug session."""
        session = populated_generator.get_session()
        assert session is not None
        assert len(session.entries) == 3

    def test_get_low_confidence_items(self, populated_generator):
        """Test getting low confidence items."""
        low = populated_generator.get_low_confidence_items()
        assert len(low) == 2
        assert all(r.confidence_level == ConfidenceLevel.LOW for r in low)

    def test_get_uncertain_items(self, populated_generator):
        """Test getting items with uncertainties."""
        uncertain = populated_generator.get_uncertain_items()
        assert len(uncertain) == 2
        assert all(len(r.uncertainties) > 0 for r in uncertain)

    def test_clear_log(self, populated_generator):
        """Test clearing the reasoning log."""
        assert len(populated_generator.reasoning_log) == 3

        populated_generator.clear_log()

        assert len(populated_generator.reasoning_log) == 0
        assert len(populated_generator.session.entries) == 0

    def test_export_session(self, populated_generator):
        """Test exporting the session."""
        export = populated_generator.export_session()

        assert 'session_id' in export
        assert 'entries' in export
        assert len(export['entries']) == 3
        assert 'summary' in export

    def test_export_session_debug_disabled(self):
        """Test exporting when debug disabled."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=False)

        export = generator.export_session()
        assert export['debug_enabled'] is False


class TestDebugGeneratorReport:
    """Tests for reasoning report generation."""

    def test_format_reasoning_report_empty(self):
        """Test report with no reasoning captured."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=True)

        report = generator.format_reasoning_report()
        assert "No reasoning captured" in report

    def test_format_reasoning_report_with_entries(self):
        """Test report with reasoning entries."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=True)

        generator.reasoning_log = [
            GenerationReasoning(
                item_id="1", item_type="milestone",
                reasoning="Foundation first approach",
                assumptions=["Team knows Python"],
                uncertainties=["Timeline unclear"],
                confidence_level=ConfidenceLevel.MEDIUM,
            ),
            GenerationReasoning(
                item_id="1.0", item_type="epic",
                reasoning="Auth is critical",
                assumptions=[],
                uncertainties=["OAuth vs JWT"],
                confidence_level=ConfidenceLevel.LOW,
            ),
        ]
        generator.session.entries = generator.reasoning_log.copy()

        report = generator.format_reasoning_report()

        assert "Generation Reasoning Report" in report
        assert "Summary" in report
        assert "Low Confidence Items" in report
        assert "milestone" in report.lower()
        assert "Foundation first approach" in report
        assert "OAuth vs JWT" in report


class TestConfidenceLevel:
    """Tests for ConfidenceLevel enum."""

    def test_values(self):
        """Test enum values."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.UNKNOWN.value == "unknown"


class TestDebugReportingMethods:
    """Tests for get_debug_report, save_debug_log, and get_summary_stats methods."""

    @pytest.fixture
    def populated_generator(self):
        """Create generator with populated reasoning log."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=True)

        generator.reasoning_log = [
            GenerationReasoning(
                item_id="1", item_type="milestone",
                reasoning="Foundation first approach",
                assumptions=["Team knows Python", "Using PostgreSQL"],
                uncertainties=[],
                confidence_level=ConfidenceLevel.HIGH,
            ),
            GenerationReasoning(
                item_id="1.0", item_type="epic",
                reasoning="Auth is critical",
                assumptions=["Team knows Python"],  # Same assumption for testing
                uncertainties=["OAuth vs JWT"],
                confidence_level=ConfidenceLevel.LOW,
            ),
            GenerationReasoning(
                item_id="1.0.1", item_type="story",
                reasoning="Login first",
                assumptions=[],
                uncertainties=["Session management approach"],
                confidence_level=ConfidenceLevel.MEDIUM,
            ),
        ]
        generator.session.entries = generator.reasoning_log.copy()

        return generator

    def test_get_summary_stats_empty(self):
        """Test summary stats with no entries."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=True)

        stats = generator.get_summary_stats()

        assert stats['total_items'] == 0
        assert stats['by_confidence']['high'] == 0
        assert stats['by_confidence']['medium'] == 0
        assert stats['by_confidence']['low'] == 0
        assert stats['total_assumptions'] == 0
        assert stats['total_uncertainties'] == 0

    def test_get_summary_stats_populated(self, populated_generator):
        """Test summary stats with entries."""
        stats = populated_generator.get_summary_stats()

        assert stats['total_items'] == 3
        assert stats['by_confidence']['high'] == 1
        assert stats['by_confidence']['medium'] == 1
        assert stats['by_confidence']['low'] == 1
        assert stats['by_type']['milestone'] == 1
        assert stats['by_type']['epic'] == 1
        assert stats['by_type']['story'] == 1
        assert stats['total_assumptions'] == 3
        assert stats['total_uncertainties'] == 2
        assert stats['items_with_uncertainties'] == 2

    def test_get_debug_report_empty(self):
        """Test get_debug_report with no entries."""
        mock_client = MagicMock()
        generator = DebugGenerator(mock_client, debug_enabled=True)

        report = generator.get_debug_report()

        assert "No reasoning captured" in report
        assert "--debug flag" in report

    def test_get_debug_report_populated(self, populated_generator):
        """Test get_debug_report with entries."""
        report = populated_generator.get_debug_report()

        # Check structure
        assert "Generation Debug Report" in report
        assert "Total items generated: 3" in report

        # Check confidence breakdown
        assert "High confidence:" in report
        assert "Medium confidence:" in report
        assert "Low confidence:" in report

        # Check items by type
        assert "Milestone:" in report or "milestone:" in report.lower()
        assert "Epic:" in report or "epic:" in report.lower()

        # Check low confidence warning
        assert "Low Confidence Items" in report
        assert "Epic 1.0" in report

        # Check common assumptions section
        assert "Common Assumptions" in report
        assert "Team knows Python" in report

    def test_get_debug_report_shows_uncertainties(self, populated_generator):
        """Test that debug report shows uncertainties for low confidence items."""
        report = populated_generator.get_debug_report()

        # Low confidence items should show their uncertainties
        assert "OAuth vs JWT" in report

    def test_save_debug_log_creates_file(self, populated_generator, tmp_path):
        """Test save_debug_log creates valid JSON file."""
        import json

        output_file = tmp_path / "debug_log.json"
        populated_generator.save_debug_log(str(output_file))

        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert 'generated_at' in data
        assert 'summary' in data
        assert 'items' in data
        assert len(data['items']) == 3
        assert 'low_confidence_items' in data
        assert len(data['low_confidence_items']) == 1

    def test_save_debug_log_creates_parent_dirs(self, populated_generator, tmp_path):
        """Test save_debug_log creates parent directories."""
        import json

        output_file = tmp_path / "nested" / "deep" / "debug_log.json"
        populated_generator.save_debug_log(str(output_file))

        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data['summary']['total_items'] == 3

    def test_save_debug_log_contains_all_sections(self, populated_generator, tmp_path):
        """Test save_debug_log contains all expected sections."""
        import json

        output_file = tmp_path / "debug_log.json"
        populated_generator.save_debug_log(str(output_file))

        with open(output_file) as f:
            data = json.load(f)

        # Check summary section
        assert data['summary']['by_confidence']['high'] == 1
        assert data['summary']['by_confidence']['low'] == 1

        # Check items section
        assert all('item_id' in item for item in data['items'])
        assert all('confidence_level' in item for item in data['items'])
        assert all('reasoning' in item for item in data['items'])

        # Check specialized sections
        assert 'items_with_uncertainties' in data
        assert len(data['items_with_uncertainties']) == 2

    def test_get_item_reasoning(self, populated_generator):
        """Test getting reasoning for specific item."""
        reasoning = populated_generator.get_item_reasoning("1.0")

        assert reasoning is not None
        assert reasoning.item_id == "1.0"
        assert reasoning.item_type == "epic"
        assert reasoning.confidence_level == ConfidenceLevel.LOW

    def test_get_item_reasoning_not_found(self, populated_generator):
        """Test getting reasoning for non-existent item."""
        reasoning = populated_generator.get_item_reasoning("999")

        assert reasoning is None

    def test_get_items_by_type(self, populated_generator):
        """Test getting items by type."""
        milestones = populated_generator.get_items_by_type("milestone")
        epics = populated_generator.get_items_by_type("epic")

        assert len(milestones) == 1
        assert milestones[0].item_id == "1"

        assert len(epics) == 1
        assert epics[0].item_id == "1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
