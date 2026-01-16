"""Compression presets for different use cases."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CompressionPreset:
    """A named compression preset with configuration."""
    name: str
    level: str
    description: str
    shorthand_overrides: Optional[Dict[str, str]] = None
    additional_patterns: Optional[List[tuple]] = None
    max_section_length: int = 500

    def __post_init__(self):
        if self.shorthand_overrides is None:
            self.shorthand_overrides = {}
        if self.additional_patterns is None:
            self.additional_patterns = []


# Predefined compression presets
COMPRESSION_PRESETS: Dict[str, CompressionPreset] = {
    'default': CompressionPreset(
        name='default',
        level='moderate',
        description='Balanced compression for general use',
    ),

    'cost_saving': CompressionPreset(
        name='cost_saving',
        level='aggressive',
        description='Maximum compression for cost reduction',
        max_section_length=300,
    ),

    'quality_first': CompressionPreset(
        name='quality_first',
        level='light',
        description='Minimal compression to preserve prompt quality',
        max_section_length=1000,
    ),

    'roadmap': CompressionPreset(
        name='roadmap',
        level='moderate',
        description='Optimized for roadmap generation prompts',
        shorthand_overrides={
            'acceptance criteria': 'AC',
            'user story': 'story',
            'sprint': 'sp',
            'backlog': 'BL',
        },
    ),

    'code_generation': CompressionPreset(
        name='code_generation',
        level='light',
        description='Preserve code examples and technical details',
        max_section_length=800,
    ),

    'summarization': CompressionPreset(
        name='summarization',
        level='aggressive',
        description='Heavy compression for context summarization',
        max_section_length=200,
        additional_patterns=[
            (r'(?s)Details:.*?(?=\n\n|\Z)', '[details omitted]'),
            (r'(?s)Background:.*?(?=\n\n|\Z)', '[background omitted]'),
        ],
    ),
}


def get_preset(name: str) -> CompressionPreset:
    """Get a compression preset by name.

    Args:
        name: Name of the preset

    Returns:
        CompressionPreset object

    Raises:
        KeyError: If preset name not found
    """
    if name not in COMPRESSION_PRESETS:
        available = ', '.join(COMPRESSION_PRESETS.keys())
        raise KeyError(f"Unknown preset '{name}'. Available: {available}")
    return COMPRESSION_PRESETS[name]


def list_presets() -> List[str]:
    """List all available preset names.

    Returns:
        List of preset names
    """
    return list(COMPRESSION_PRESETS.keys())


def get_preset_descriptions() -> Dict[str, str]:
    """Get descriptions for all presets.

    Returns:
        Dictionary mapping preset names to descriptions
    """
    return {name: preset.description for name, preset in COMPRESSION_PRESETS.items()}
