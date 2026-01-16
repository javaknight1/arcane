"""Tests for prompt compression system."""

import pytest
from arcane.prompts.compression import (
    PromptCompressor,
    CompressionPreset,
    COMPRESSION_PRESETS,
    get_preset,
)
from arcane.prompts.compression.prompt_compressor import CompressionConfig
from arcane.prompts.compression.presets import list_presets, get_preset_descriptions


class TestPromptCompressor:
    """Tests for PromptCompressor class."""

    @pytest.fixture
    def compressor(self):
        """Create a PromptCompressor instance."""
        return PromptCompressor()

    @pytest.fixture
    def sample_prompt(self):
        """Create a sample verbose prompt."""
        return """Please generate a detailed Milestone for the project.

You should ensure that the implementation includes all necessary components.
It is important to note that the authentication system requires proper configuration.

In order to complete the Task, you need to:
1. Set up the database
2. Configure the application
3. Add documentation

Make sure to include all requirements and specifications.

Example:
```example
Here is an example of a properly formatted milestone.
```

For example: This shows how the output should look.
"""

    def test_compress_none_level(self, compressor, sample_prompt):
        """Test compression with 'none' level."""
        result = compressor.compress(sample_prompt, level='none')

        # Should still clean whitespace and verbose phrases
        assert len(result) <= len(sample_prompt)
        # Examples should still be present
        assert 'example' in result.lower()

    def test_compress_light_level(self, compressor, sample_prompt):
        """Test compression with 'light' level."""
        result = compressor.compress(sample_prompt, level='light')

        # Should compress verbose phrases
        assert 'Please generate' not in result
        # Shorthand should NOT be applied
        assert 'Milestone' in result or 'milestone' in result.lower()

    def test_compress_moderate_level(self, compressor, sample_prompt):
        """Test compression with 'moderate' level."""
        result = compressor.compress(sample_prompt, level='moderate')

        # Shorthand should be applied
        assert 'auth' in result.lower()
        assert 'config' in result.lower()
        # Examples should still be present
        assert 'example' in result.lower() or 'examples omitted' in result.lower()

    def test_compress_aggressive_level(self, compressor, sample_prompt):
        """Test compression with 'aggressive' level."""
        result = compressor.compress(sample_prompt, level='aggressive')

        # Examples should be removed
        assert '[examples omitted]' in result or 'example' not in result.lower()
        # Significant compression
        assert len(result) < len(sample_prompt) * 0.8

    def test_remove_excessive_whitespace(self, compressor):
        """Test whitespace removal."""
        text = "Hello    world\n\n\n\nNew paragraph   here  "
        result = compressor._remove_excessive_whitespace(text)

        assert '    ' not in result
        assert '\n\n\n' not in result
        assert result.endswith('here')

    def test_compress_verbose_phrases(self, compressor):
        """Test verbose phrase compression."""
        text = "Please generate the output. You should ensure that it works."
        result = compressor._compress_verbose_phrases(text)

        assert 'Please generate' not in result
        assert 'Generate' in result
        assert 'You should ensure that' not in result

    def test_apply_shorthand(self, compressor):
        """Test shorthand application."""
        text = "The authentication implementation requires configuration."
        result = compressor._apply_shorthand(text)

        assert 'auth' in result
        assert 'impl' in result
        assert 'config' in result

    def test_shorthand_preserves_case_insensitivity(self, compressor):
        """Test that shorthand works with different cases."""
        text = "AUTHENTICATION and Authentication and authentication"
        result = compressor._apply_shorthand(text)

        # All instances should be converted
        assert result.lower().count('auth') >= 3
        assert 'authentication' not in result.lower()

    def test_truncate_long_sections(self, compressor):
        """Test section truncation."""
        long_section = "A" * 1000
        result = compressor._truncate_long_sections(long_section, max_length=100)

        assert len(result) < 1000
        assert result.endswith('...')

    def test_truncate_preserves_headers(self, compressor):
        """Test that headers are not truncated."""
        text = "# Very Long Header That Should Not Be Truncated\n" + "A" * 1000
        result = compressor._truncate_long_sections(text, max_length=100)

        assert "# Very Long Header" in result

    def test_remove_example_sections(self, compressor):
        """Test example section removal."""
        text = """Before example.

Example: This is an example that should be removed.

After example."""

        result = compressor._remove_example_sections(text)
        assert '[examples omitted]' in result

    def test_remove_code_examples(self, compressor):
        """Test code example block removal."""
        text = """Before.

```example
code here
```

After."""

        result = compressor._remove_example_sections(text)
        assert '[examples omitted]' in result
        assert 'code here' not in result

    def test_get_compression_stats(self, compressor, sample_prompt):
        """Test compression statistics calculation."""
        compressed = compressor.compress(sample_prompt, level='aggressive')
        stats = compressor.get_compression_stats(sample_prompt, compressed)

        assert 'original_chars' in stats
        assert 'compressed_chars' in stats
        assert 'original_tokens' in stats
        assert 'compressed_tokens' in stats
        assert 'tokens_saved' in stats
        assert 'compression_ratio' in stats

        assert stats['original_chars'] > stats['compressed_chars']
        assert stats['tokens_saved'] > 0
        assert stats['compression_ratio'] > 0

    def test_compress_with_stats(self, compressor, sample_prompt):
        """Test compression with statistics return."""
        compressed, stats = compressor.compress_with_stats(sample_prompt, level='moderate')

        assert isinstance(compressed, str)
        assert isinstance(stats, dict)
        assert len(compressed) < len(sample_prompt)

    def test_get_available_levels(self, compressor):
        """Test getting available compression levels."""
        levels = compressor.get_available_levels()

        assert 'none' in levels
        assert 'light' in levels
        assert 'moderate' in levels
        assert 'aggressive' in levels

    def test_estimate_savings(self, compressor, sample_prompt):
        """Test savings estimation."""
        estimate = compressor.estimate_savings(sample_prompt, level='aggressive')

        assert 'original_tokens' in estimate
        assert 'estimated_tokens' in estimate
        assert 'estimated_savings' in estimate
        assert 'estimated_ratio' in estimate

        assert estimate['estimated_tokens'] < estimate['original_tokens']

    def test_custom_config(self):
        """Test compressor with custom configuration."""
        config = CompressionConfig(
            shorthand=True,
            truncate=True,
            max_section_length=200,
        )
        compressor = PromptCompressor(config=config)

        long_text = "The authentication " + "A" * 500
        result = compressor.compress(long_text, level='moderate')

        assert 'auth' in result
        assert len(result) < len(long_text)

    def test_empty_prompt(self, compressor):
        """Test compression of empty prompt."""
        result = compressor.compress('', level='aggressive')
        assert result == ''

    def test_short_prompt(self, compressor):
        """Test compression of very short prompt."""
        result = compressor.compress('Hello', level='aggressive')
        assert result == 'Hello'

    def test_invalid_level_uses_moderate(self, compressor):
        """Test that invalid level falls back to moderate."""
        result = compressor.compress('Test authentication', level='invalid')
        assert 'auth' in result  # Shorthand applied (moderate level)


class TestCompressionPresets:
    """Tests for compression presets."""

    def test_default_preset_exists(self):
        """Test that default preset exists."""
        preset = get_preset('default')
        assert preset.name == 'default'
        assert preset.level == 'moderate'

    def test_cost_saving_preset(self):
        """Test cost saving preset configuration."""
        preset = get_preset('cost_saving')
        assert preset.level == 'aggressive'
        assert preset.max_section_length == 300

    def test_quality_first_preset(self):
        """Test quality first preset configuration."""
        preset = get_preset('quality_first')
        assert preset.level == 'light'
        assert preset.max_section_length == 1000

    def test_roadmap_preset(self):
        """Test roadmap preset has custom shorthand."""
        preset = get_preset('roadmap')
        assert preset.level == 'moderate'
        assert 'acceptance criteria' in preset.shorthand_overrides
        assert preset.shorthand_overrides['acceptance criteria'] == 'AC'

    def test_code_generation_preset(self):
        """Test code generation preset configuration."""
        preset = get_preset('code_generation')
        assert preset.level == 'light'
        assert preset.max_section_length == 800

    def test_summarization_preset(self):
        """Test summarization preset configuration."""
        preset = get_preset('summarization')
        assert preset.level == 'aggressive'
        assert preset.max_section_length == 200
        assert len(preset.additional_patterns) > 0

    def test_invalid_preset_raises_error(self):
        """Test that invalid preset name raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            get_preset('nonexistent')

        assert 'nonexistent' in str(exc_info.value)
        assert 'Available' in str(exc_info.value)

    def test_list_presets(self):
        """Test listing all presets."""
        presets = list_presets()

        assert 'default' in presets
        assert 'cost_saving' in presets
        assert 'quality_first' in presets
        assert len(presets) >= 5

    def test_get_preset_descriptions(self):
        """Test getting preset descriptions."""
        descriptions = get_preset_descriptions()

        assert isinstance(descriptions, dict)
        assert 'default' in descriptions
        assert 'Balanced' in descriptions['default']

    def test_preset_dataclass(self):
        """Test CompressionPreset dataclass."""
        preset = CompressionPreset(
            name='custom',
            level='moderate',
            description='Custom preset',
        )

        assert preset.name == 'custom'
        assert preset.shorthand_overrides == {}
        assert preset.additional_patterns == []


class TestCompressionIntegration:
    """Integration tests for compression system."""

    def test_compress_roadmap_prompt(self):
        """Test compressing a realistic roadmap prompt."""
        prompt = """Please generate a detailed Milestone for the MVP phase.

You should ensure that the implementation includes the following components:

## Authentication System
It is important to note that the authentication implementation requires
proper configuration and documentation. In order to complete this Task,
the development team needs to set up the database and application.

### User Stories
Make sure to include acceptance criteria for each user story.
The specifications should cover all requirements.

Example:
```
Story 1: User Login
As a user, I want to log in securely.
```

For example: Each story should have clear acceptance criteria.
"""
        compressor = PromptCompressor()
        compressed, stats = compressor.compress_with_stats(prompt, level='aggressive')

        # Should achieve significant compression
        assert stats['compression_ratio'] > 20  # At least 20% reduction

        # Key concepts should be preserved
        assert 'MVP' in compressed or 'M' in compressed
        assert 'db' in compressed or 'database' in compressed.lower()

    def test_compression_preserves_structure(self):
        """Test that compression preserves markdown structure."""
        prompt = """# Main Title

## Section 1
Content for section 1.

## Section 2
Content for section 2.

### Subsection
More content here.
"""
        compressor = PromptCompressor()
        compressed = compressor.compress(prompt, level='moderate')

        # Headers should be preserved
        assert '# Main Title' in compressed
        assert '## Section' in compressed
        assert '### Subsection' in compressed

    def test_multiple_compression_passes(self):
        """Test that multiple compressions don't break the text."""
        original = "Please generate the authentication implementation configuration."

        compressor = PromptCompressor()

        # First compression
        pass1 = compressor.compress(original, level='moderate')

        # Second compression should not significantly change
        pass2 = compressor.compress(pass1, level='moderate')

        # Should be stable after first pass
        assert len(pass2) <= len(pass1)
        # Not too different
        assert abs(len(pass1) - len(pass2)) < len(pass1) * 0.1

    def test_preserves_code_blocks(self):
        """Test that regular code blocks are preserved."""
        prompt = """Generate a function:

```python
def hello():
    return "Hello, World!"
```

The function should work correctly.
"""
        compressor = PromptCompressor()
        compressed = compressor.compress(prompt, level='moderate')

        # Code block should be preserved
        assert 'def hello():' in compressed
        assert 'return "Hello, World!"' in compressed

    def test_unicode_handling(self):
        """Test compression handles unicode correctly."""
        prompt = "Please generate: émoji 🎉 and symbols ™ © ®"
        compressor = PromptCompressor()

        result = compressor.compress(prompt, level='aggressive')

        assert '🎉' in result
        assert '™' in result


class TestCompressionConfig:
    """Tests for CompressionConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CompressionConfig()

        assert config.shorthand is False
        assert config.truncate is False
        assert config.remove_examples is False
        assert config.max_section_length == 500
        assert config.preserve_structure is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = CompressionConfig(
            shorthand=True,
            truncate=True,
            remove_examples=True,
            max_section_length=200,
        )

        assert config.shorthand is True
        assert config.max_section_length == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
