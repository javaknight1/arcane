"""Settings and default configuration values."""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LLMSettings:
    """LLM-specific settings."""
    default_provider: str = 'claude'
    default_model: str = 'claude-3-sonnet'
    max_tokens: int = 4000
    temperature: float = 0.7
    enable_cost_estimation: bool = True
    cost_threshold_warning: float = 1.0
    rate_limit_delay: float = 1.0
    api_keys: Dict[str, str] = field(default_factory=dict)


@dataclass
class GenerationSettings:
    """Content generation settings."""
    interactive_mode: bool = True
    save_outputs: bool = True
    cache_templates: bool = True
    validate_inputs: bool = True
    max_retries: int = 3
    request_timeout: float = 30.0

    # Prompt compression settings
    compression_level: str = 'moderate'  # none, light, moderate, aggressive
    show_compression_stats: bool = False

    # Model selection settings
    model_mode: str = 'tiered'  # tiered, premium, economy, standard

    # Roadmap generation defaults
    default_timeline: str = '6-months'
    default_complexity: str = 'moderate'
    default_team_size: int = 3

    # Item count estimation defaults
    milestones_per_timeline: Dict[str, int] = field(default_factory=lambda: {
        '3-months': 3,
        '6-months': 4,
        '12-months': 6
    })

    epics_per_milestone: Dict[str, float] = field(default_factory=lambda: {
        'simple': 1.5,
        'moderate': 2.0,
        'complex': 3.0
    })

    stories_per_epic: Dict[str, int] = field(default_factory=lambda: {
        'simple': 2,
        'moderate': 2,
        'complex': 3
    })

    tasks_per_story: Dict[str, int] = field(default_factory=lambda: {
        'simple': 3,
        'moderate': 4,
        'complex': 5
    })


@dataclass
class FileSettings:
    """File operation settings."""
    default_output_dir: str = './output'
    template_cache_dir: str = './cache/templates'
    progress_save_dir: str = './output/progress'

    # Directory naming pattern for each run
    run_directory_pattern: str = "{timestamp}"

    # File naming patterns (timestamps now in directory, not filename)
    outline_filename_pattern: str = "{project_name}_outline.md"
    roadmap_filename_pattern: str = "{project_name}_complete.md"
    progress_filename_pattern: str = "{project_name}_progress.json"

    # File extensions
    supported_export_formats: List[str] = field(default_factory=lambda: [
        'md', 'json', 'csv', 'yaml', 'html'
    ])


@dataclass
class DisplaySettings:
    """Display and console settings."""
    console_width: int = 120
    show_progress: bool = True
    use_rich_formatting: bool = True
    show_cost_warnings: bool = True
    verbose_logging: bool = False
    debug: bool = False

    # Color scheme
    success_color: str = "green"
    warning_color: str = "yellow"
    error_color: str = "red"
    info_color: str = "cyan"
    highlight_color: str = "bold cyan"


@dataclass
class Settings:
    """Main settings container."""
    llm: LLMSettings = field(default_factory=LLMSettings)
    generation: GenerationSettings = field(default_factory=GenerationSettings)
    files: FileSettings = field(default_factory=FileSettings)
    display: DisplaySettings = field(default_factory=DisplaySettings)

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'llm': self.llm.__dict__,
            'generation': self.generation.__dict__,
            'files': self.files.__dict__,
            'display': self.display.__dict__
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary."""
        return cls(
            llm=LLMSettings(**data.get('llm', {})),
            generation=GenerationSettings(**data.get('generation', {})),
            files=FileSettings(**data.get('files', {})),
            display=DisplaySettings(**data.get('display', {}))
        )


# Default settings instance
DefaultSettings = Settings()


# Hardcoded values that should be moved to config
HARDCODED_VALUES = {
    # Cost estimation
    'COST_WARNING_THRESHOLD': 1.0,
    'DEFAULT_OUTPUT_TOKENS': {
        'outline': 3000,
        'milestone': 400,
        'epic': 800,
        'story': 1200
    },

    # Generation prompts
    'GENERATION_MODE_CHOICES': ['automatic', 'interactive'],
    'GENERATION_MODE_DEFAULT': 'automatic',

    # Validation
    'MIN_MILESTONE_COUNT': 1,
    'MAX_MILESTONE_COUNT': 10,
    'MIN_EPIC_COUNT': 1,
    'MAX_EPIC_COUNT': 50,

    # Display
    'PROGRESS_UPDATE_INTERVAL': 0.1,
    'STATUS_SPINNER': 'dots',
    'CONSOLE_MARKUP': True,

    # File operations
    'TIMESTAMP_FORMAT': '%Y%m%d_%H%M%S',
    'DEFAULT_PROJECT_NAME': 'roadmap',

    # Template system
    'TEMPLATE_CACHE_TTL': 3600,  # 1 hour
    'TEMPLATE_ENCODING': 'utf-8',
}