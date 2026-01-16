"""Configuration manager for loading and managing settings."""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from arcane.protocols.file_protocols import ConfigurationProtocol
from .settings import Settings, DefaultSettings
from .environment import Environment, detect_environment, get_environment_config, get_llm_config
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigManager(ConfigurationProtocol):
    """Manages configuration loading, validation, and access."""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / '.arcane'
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.environment = detect_environment()
        self.settings = DefaultSettings
        self._config_cache: Dict[str, Any] = {}

        # Load configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from files and environment."""
        try:
            # Load base configuration
            base_config_file = self.config_dir / 'config.yaml'
            if base_config_file.exists():
                self._load_config_file(str(base_config_file))

            # Load environment-specific configuration
            env_config_file = self.config_dir / f'config.{self.environment.value}.yaml'
            if env_config_file.exists():
                self._load_config_file(str(env_config_file))

            # Apply environment defaults
            self._apply_environment_config()

            # Override with environment variables
            self._load_environment_variables()

            logger.info("Configuration loaded for environment: %s", self.environment.value)

        except Exception as e:
            logger.warning("Failed to load configuration: %s", e)
            logger.info("Using default configuration")

    def _load_config_file(self, filepath: str) -> None:
        """Load configuration from a file."""
        config_path = Path(filepath)

        if not config_path.exists():
            logger.debug("Config file not found: %s", filepath)
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    logger.warning("Unsupported config file format: %s", filepath)
                    return

            if data:
                self._merge_config(data)
                logger.debug("Loaded config from: %s", filepath)

        except Exception as e:
            logger.error("Failed to load config file %s: %s", filepath, e)

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Merge new configuration with current settings."""
        try:
            # Convert current settings to dict
            current_dict = self.settings.to_dict()

            # Deep merge the configurations
            merged = self._deep_merge(current_dict, new_config)

            # Create new settings from merged config
            self.settings = Settings.from_dict(merged)

        except Exception as e:
            logger.error("Failed to merge configuration: %s", e)

    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_environment_config(self) -> None:
        """Apply environment-specific defaults."""
        env_config = get_environment_config(self.environment)
        llm_config = get_llm_config(self.environment)

        # Apply general environment config
        for key, value in env_config.items():
            if hasattr(self.settings.generation, key):
                setattr(self.settings.generation, key, value)
            elif hasattr(self.settings.display, key):
                setattr(self.settings.display, key, value)

        # Apply LLM environment config
        for key, value in llm_config.items():
            if hasattr(self.settings.llm, key):
                setattr(self.settings.llm, key, value)

    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            'ARCANE_DEBUG': ('display', 'debug', bool),
            'ARCANE_VERBOSE': ('display', 'verbose_logging', bool),
            'ARCANE_SAVE_OUTPUTS': ('generation', 'save_outputs', bool),
            'ARCANE_INTERACTIVE': ('generation', 'interactive_mode', bool),
            'ARCANE_OUTPUT_DIR': ('files', 'default_output_dir', str),
            'ARCANE_LLM_PROVIDER': ('llm', 'default_provider', str),
            'ARCANE_LLM_MODEL': ('llm', 'default_model', str),
            'ARCANE_MAX_TOKENS': ('llm', 'max_tokens', int),
            'ARCANE_TEMPERATURE': ('llm', 'temperature', float),
            'ARCANE_COST_WARNING': ('llm', 'cost_threshold_warning', float),
            'ARCANE_COMPRESSION_LEVEL': ('generation', 'compression_level', str),
            'ARCANE_SHOW_COMPRESSION_STATS': ('generation', 'show_compression_stats', bool),
            'ARCANE_MODEL_MODE': ('generation', 'model_mode', str),
        }

        for env_var, (section, key, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if value_type == bool:
                        parsed_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        parsed_value = value_type(env_value)

                    section_obj = getattr(self.settings, section)
                    setattr(section_obj, key, parsed_value)
                    logger.debug("Set %s.%s = %s from environment", section, key, parsed_value)

                except (ValueError, TypeError) as e:
                    logger.warning("Invalid environment variable %s=%s: %s", env_var, env_value, e)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        try:
            keys = key.split('.')
            value = self.settings

            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default

            return value

        except Exception:
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        try:
            keys = key.split('.')
            obj = self.settings

            # Navigate to the parent object
            for k in keys[:-1]:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                else:
                    raise ValueError(f"Invalid configuration path: {key}")

            # Set the final value
            final_key = keys[-1]
            if hasattr(obj, final_key):
                setattr(obj, final_key, value)
                logger.debug("Set configuration %s = %s", key, value)
            else:
                raise ValueError(f"Invalid configuration key: {key}")

        except Exception as e:
            logger.error("Failed to set configuration %s = %s: %s", key, value, e)
            raise

    def load_from_file(self, filepath: str) -> None:
        """Load configuration from file."""
        self._load_config_file(filepath)

    def save_to_file(self, filepath: str) -> None:
        """Save current configuration to file."""
        config_path = Path(filepath)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            config_dict = self.settings.to_dict()

            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(config_dict, f, default_flow_style=False, indent=2)
                elif config_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2)
                else:
                    raise ValueError(f"Unsupported file format: {config_path.suffix}")

            logger.info("Configuration saved to: %s", filepath)

        except Exception as e:
            logger.error("Failed to save configuration to %s: %s", filepath, e)
            raise

    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        return {
            'environment': self.environment.value,
            'config_dir': str(self.config_dir),
            'settings': self.settings.to_dict()
        }

    def validate_config(self) -> List[str]:
        """Validate configuration and return any issues."""
        issues = []

        # Validate LLM settings
        if self.settings.llm.max_tokens <= 0:
            issues.append("LLM max_tokens must be positive")

        if not (0.0 <= self.settings.llm.temperature <= 2.0):
            issues.append("LLM temperature must be between 0.0 and 2.0")

        if self.settings.llm.cost_threshold_warning < 0:
            issues.append("Cost threshold warning must be non-negative")

        # Validate generation settings
        if self.settings.generation.max_retries < 0:
            issues.append("Max retries must be non-negative")

        if self.settings.generation.request_timeout <= 0:
            issues.append("Request timeout must be positive")

        # Validate file settings
        try:
            Path(self.settings.files.default_output_dir)
        except Exception:
            issues.append("Invalid default output directory path")

        # Validate display settings
        if self.settings.display.console_width <= 0:
            issues.append("Console width must be positive")

        return issues


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reset_config() -> None:
    """Reset the global configuration manager (mainly for testing)."""
    global _config_manager
    _config_manager = None