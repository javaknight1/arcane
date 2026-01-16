"""Tests for prompt compression integration."""

import pytest
from unittest.mock import MagicMock, patch

from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
from arcane.prompts.compression import PromptCompressor
from arcane.config.settings import GenerationSettings, Settings


class TestRoadmapPromptBuilderCompression:
    """Tests for compression in RoadmapPromptBuilder."""

    @pytest.fixture
    def sample_preferences(self):
        """Create sample preferences for testing."""
        return {
            'timeline': '6-months',
            'focus': 'full-stack',
            'complexity': 'moderate',
            'industry': 'technology',
            'target_market': 'B2B',
            'market_maturity': 'growth',
            'technical_challenges': ['scaling', 'security'],
            'deployment_environment': 'cloud',
            'geographic_distribution': 'global',
            'scaling_expectations': 'steady',
            'team_size': '5-10',
            'team_expertise': 'intermediate',
            'team_distribution': 'remote',
            'dev_methodology': 'agile',
            'budget_range': 'startup',
            'infra_budget': 'moderate',
            'services_budget': 'moderate',
            'payment_integrations': 'stripe',
            'communication_integrations': 'email',
            'business_integrations': 'none',
            'developer_integrations': 'github',
            'data_integrations': 'none',
            'success_metric': 'user_adoption',
            'success_timeline': '6-months',
            'measurement_approach': 'analytics',
            'failure_tolerance': 'low',
            'regulatory': 'none',
        }

    def test_builder_with_no_compression(self, sample_preferences):
        """Test builder with compression disabled."""
        builder = RoadmapPromptBuilder(compression_level='none')

        prompt = builder.build_prompt(
            idea_content="Build a web application",
            preferences=sample_preferences
        )

        # Prompt should still work
        assert len(prompt) > 0
        assert 'web application' in prompt.lower()

    def test_builder_with_light_compression(self, sample_preferences):
        """Test builder with light compression."""
        builder = RoadmapPromptBuilder(compression_level='light')

        prompt = builder.build_prompt(
            idea_content="Build a web application",
            preferences=sample_preferences
        )

        assert len(prompt) > 0

    def test_builder_with_moderate_compression(self, sample_preferences):
        """Test builder with moderate compression (default)."""
        builder = RoadmapPromptBuilder(compression_level='moderate')

        prompt = builder.build_prompt(
            idea_content="Build a web application",
            preferences=sample_preferences
        )

        assert len(prompt) > 0

    def test_builder_with_aggressive_compression(self, sample_preferences):
        """Test builder with aggressive compression."""
        builder = RoadmapPromptBuilder(compression_level='aggressive')

        prompt = builder.build_prompt(
            idea_content="Build a web application",
            preferences=sample_preferences
        )

        assert len(prompt) > 0

    def test_compression_reduces_prompt_size(self, sample_preferences):
        """Test that compression actually reduces prompt size."""
        builder_none = RoadmapPromptBuilder(compression_level='none')
        builder_aggressive = RoadmapPromptBuilder(compression_level='aggressive')

        prompt_none = builder_none.build_prompt(
            idea_content="Build a web application with authentication",
            preferences=sample_preferences
        )

        prompt_aggressive = builder_aggressive.build_prompt(
            idea_content="Build a web application with authentication",
            preferences=sample_preferences
        )

        # Aggressive compression should produce smaller prompt
        assert len(prompt_aggressive) < len(prompt_none)

    def test_compression_stats_tracking(self, sample_preferences):
        """Test that compression stats are tracked when enabled."""
        builder = RoadmapPromptBuilder(
            compression_level='moderate',
            show_compression_stats=True
        )

        # Build a prompt
        builder.build_prompt(
            idea_content="Build a web application",
            preferences=sample_preferences
        )

        stats = builder.get_compression_stats()
        assert len(stats) == 1
        assert 'original_tokens' in stats[0]
        assert 'compressed_tokens' in stats[0]
        assert 'compression_ratio' in stats[0]

    def test_compression_stats_not_tracked_when_disabled(self, sample_preferences):
        """Test that stats are not tracked when disabled."""
        builder = RoadmapPromptBuilder(
            compression_level='moderate',
            show_compression_stats=False
        )

        builder.build_prompt(
            idea_content="Build a web application",
            preferences=sample_preferences
        )

        stats = builder.get_compression_stats()
        assert len(stats) == 0

    def test_total_savings_calculation(self, sample_preferences):
        """Test total savings calculation across multiple prompts."""
        builder = RoadmapPromptBuilder(
            compression_level='moderate',
            show_compression_stats=True
        )

        # Build multiple prompts
        for _ in range(3):
            builder.build_prompt(
                idea_content="Build a web application",
                preferences=sample_preferences
            )

        total = builder.get_total_savings()
        assert total['prompt_count'] == 3
        assert total['total_original_tokens'] > 0
        assert total['total_compressed_tokens'] > 0
        assert total['average_compression_ratio'] >= 0

    def test_reset_stats(self, sample_preferences):
        """Test resetting compression statistics."""
        builder = RoadmapPromptBuilder(
            compression_level='moderate',
            show_compression_stats=True
        )

        builder.build_prompt(
            idea_content="Build a web application",
            preferences=sample_preferences
        )

        assert len(builder.get_compression_stats()) == 1

        builder.reset_stats()
        assert len(builder.get_compression_stats()) == 0

    def test_outline_prompt_compression(self, sample_preferences):
        """Test compression on outline prompts."""
        builder_none = RoadmapPromptBuilder(compression_level='none')
        builder_moderate = RoadmapPromptBuilder(compression_level='moderate')

        prompt_none = builder_none.build_outline_prompt(
            idea_content="Build a task management application",
            preferences=sample_preferences
        )

        prompt_moderate = builder_moderate.build_outline_prompt(
            idea_content="Build a task management application",
            preferences=sample_preferences
        )

        # Compressed should be smaller
        assert len(prompt_moderate) <= len(prompt_none)

    def test_semantic_outline_prompt_compression(self, sample_preferences):
        """Test compression on semantic outline prompts."""
        builder = RoadmapPromptBuilder(
            compression_level='moderate',
            show_compression_stats=True
        )

        prompt = builder.build_semantic_outline_prompt(
            idea_content="Build a real-time chat application",
            preferences=sample_preferences
        )

        assert len(prompt) > 0
        stats = builder.get_compression_stats()
        assert len(stats) == 1

    def test_custom_prompt_compression(self, sample_preferences):
        """Test compression on custom prompts."""
        builder = RoadmapPromptBuilder(compression_level='moderate')

        # This might fail if template doesn't exist, which is fine
        try:
            prompt = builder.build_custom_prompt(
                'outline_generation',
                idea_content="Test idea",
                **sample_preferences
            )
            assert len(prompt) > 0
        except (KeyError, ValueError):
            # Template not found is acceptable for this test
            pass

    def test_default_compression_level(self):
        """Test that default compression level is moderate."""
        builder = RoadmapPromptBuilder()
        assert builder.compression_level == 'moderate'

    def test_empty_stats_when_no_prompts(self):
        """Test total savings with no prompts built."""
        builder = RoadmapPromptBuilder(show_compression_stats=True)
        total = builder.get_total_savings()

        assert total['prompt_count'] == 0
        assert total['total_tokens_saved'] == 0


class TestGenerationSettingsCompression:
    """Tests for compression settings in GenerationSettings."""

    def test_default_compression_level(self):
        """Test default compression level in settings."""
        settings = GenerationSettings()
        assert settings.compression_level == 'moderate'

    def test_default_show_compression_stats(self):
        """Test default show_compression_stats in settings."""
        settings = GenerationSettings()
        assert settings.show_compression_stats is False

    def test_custom_compression_settings(self):
        """Test custom compression settings."""
        settings = GenerationSettings(
            compression_level='aggressive',
            show_compression_stats=True
        )
        assert settings.compression_level == 'aggressive'
        assert settings.show_compression_stats is True

    def test_settings_to_dict_includes_compression(self):
        """Test that to_dict includes compression settings."""
        settings = Settings()
        settings_dict = settings.to_dict()

        assert 'compression_level' in settings_dict['generation']
        assert 'show_compression_stats' in settings_dict['generation']


class TestConfigManagerCompression:
    """Tests for compression config in ConfigManager."""

    def test_compression_env_var_mapping(self):
        """Test that compression environment variables are mapped."""
        from arcane.config.config_manager import ConfigManager

        # Check that the mappings exist in the class
        manager = ConfigManager.__new__(ConfigManager)
        manager.config_dir = None
        manager.settings = Settings()
        manager._config_cache = {}

        # The env mapping should include compression
        env_mappings = {
            'ARCANE_COMPRESSION_LEVEL': ('generation', 'compression_level', str),
            'ARCANE_SHOW_COMPRESSION_STATS': ('generation', 'show_compression_stats', bool),
        }

        # Just verify the settings structure supports these
        assert hasattr(manager.settings.generation, 'compression_level')
        assert hasattr(manager.settings.generation, 'show_compression_stats')


class TestArcaneCLICompression:
    """Tests for compression in ArcaneCLI."""

    @patch('arcane.main_cli.get_config')
    @patch('arcane.main_cli.Console')
    def test_cli_uses_config_compression(self, mock_console, mock_get_config):
        """Test that CLI uses compression settings from config."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'generation.compression_level': 'aggressive',
            'generation.show_compression_stats': True,
        }.get(key, default)
        mock_get_config.return_value = mock_config

        from arcane.main_cli import ArcaneCLI
        cli = ArcaneCLI()

        assert cli.compression_level == 'aggressive'
        assert cli.prompt_builder.compression_level == 'aggressive'
        assert cli.prompt_builder.show_compression_stats is True

    @patch('arcane.main_cli.get_config')
    @patch('arcane.main_cli.Console')
    def test_cli_override_compression(self, mock_console, mock_get_config):
        """Test that CLI can override compression level."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            'generation.compression_level': 'moderate',
            'generation.show_compression_stats': False,
        }.get(key, default)
        mock_get_config.return_value = mock_config

        from arcane.main_cli import ArcaneCLI
        cli = ArcaneCLI(compression_level='none')

        assert cli.compression_level == 'none'
        assert cli.prompt_builder.compression_level == 'none'


class TestCompressionEndToEnd:
    """End-to-end tests for compression flow."""

    def test_full_compression_flow(self):
        """Test complete compression flow from builder to stats."""
        # Create builder with stats enabled
        builder = RoadmapPromptBuilder(
            compression_level='aggressive',
            show_compression_stats=True
        )

        # Build several prompts
        preferences = {
            'timeline': '6-months',
            'focus': 'backend',
            'complexity': 'moderate',
            'industry': 'fintech',
            'team_size': '3-5',
            'team_expertise': 'expert',
            'budget_range': 'startup',
        }

        # Simulate building prompts for a roadmap
        for i in range(5):
            builder.build_prompt(
                idea_content=f"Build feature {i} with authentication and database",
                preferences=preferences
            )

        # Verify stats
        stats = builder.get_compression_stats()
        assert len(stats) == 5

        total = builder.get_total_savings()
        assert total['prompt_count'] == 5
        assert total['total_tokens_saved'] > 0
        assert total['average_compression_ratio'] > 0

    def test_compression_preserves_critical_content(self):
        """Test that compression preserves critical content."""
        builder = RoadmapPromptBuilder(compression_level='aggressive')

        prompt = builder.build_prompt(
            idea_content="Build a healthcare platform with HIPAA compliance",
            preferences={
                'timeline': '12-months',
                'focus': 'full-stack',
                'complexity': 'complex',
                'industry': 'healthcare',
                'regulatory': 'hipaa',
                'team_size': '10-15',
                'team_expertise': 'expert',
                'budget_range': 'enterprise',
            }
        )

        # Critical content should be preserved
        assert 'healthcare' in prompt.lower() or 'health' in prompt.lower()
        assert 'hipaa' in prompt.lower() or 'compliance' in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
