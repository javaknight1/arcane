"""Environment detection and management."""

import os
from enum import Enum
from typing import Dict, Any, Optional


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    LOCAL = "local"


def detect_environment() -> Environment:
    """Detect current environment based on environment variables and context."""

    # Check explicit environment variable
    env_var = os.getenv('ARCANE_ENV', '').lower()
    if env_var:
        for env in Environment:
            if env_var == env.value:
                return env

    # Check for CI/CD indicators
    if any(os.getenv(var) for var in ['CI', 'GITHUB_ACTIONS', 'TRAVIS', 'JENKINS_URL']):
        return Environment.TESTING

    # Check for production indicators
    if os.getenv('PROD', '').lower() == 'true' or os.getenv('PRODUCTION', '').lower() == 'true':
        return Environment.PRODUCTION

    # Check for development indicators
    if os.getenv('DEV', '').lower() == 'true' or os.getenv('DEVELOPMENT', '').lower() == 'true':
        return Environment.DEVELOPMENT

    # Default to local for development
    return Environment.LOCAL


def get_environment_config(env: Environment) -> Dict[str, Any]:
    """Get environment-specific configuration."""

    base_config = {
        'debug': False,
        'verbose_logging': False,
        'save_outputs': True,
        'cost_warnings': True,
        'interactive_mode': True,
        'cache_templates': True,
        'validate_inputs': True,
        'max_retries': 3,
        'request_timeout': 30.0,
    }

    if env == Environment.DEVELOPMENT:
        return {
            **base_config,
            'debug': True,
            'verbose_logging': True,
            'save_outputs': True,
            'cost_warnings': True,
            'interactive_mode': True,
            'cache_templates': False,  # Don't cache in dev for easier template testing
            'validate_inputs': True,
            'max_retries': 1,  # Fail fast in development
            'request_timeout': 60.0,  # Longer timeout for debugging
        }

    elif env == Environment.TESTING:
        return {
            **base_config,
            'debug': False,
            'verbose_logging': True,
            'save_outputs': False,  # Don't save files during testing
            'cost_warnings': False,  # Skip cost warnings in tests
            'interactive_mode': False,  # Never interactive in tests
            'cache_templates': True,
            'validate_inputs': True,
            'max_retries': 1,  # Fail fast in tests
            'request_timeout': 10.0,  # Shorter timeout for tests
        }

    elif env == Environment.PRODUCTION:
        return {
            **base_config,
            'debug': False,
            'verbose_logging': False,
            'save_outputs': True,
            'cost_warnings': True,
            'interactive_mode': True,
            'cache_templates': True,
            'validate_inputs': True,
            'max_retries': 3,
            'request_timeout': 30.0,
        }

    else:  # LOCAL
        return {
            **base_config,
            'debug': True,
            'verbose_logging': True,
            'save_outputs': True,
            'cost_warnings': True,
            'interactive_mode': True,
            'cache_templates': True,
            'validate_inputs': True,
            'max_retries': 2,
            'request_timeout': 45.0,
        }


def get_llm_config(env: Environment) -> Dict[str, Any]:
    """Get LLM-specific configuration for environment."""

    base_config = {
        'default_provider': 'claude',
        'default_model': 'claude-3-sonnet',
        'max_tokens': 4000,
        'temperature': 0.7,
        'enable_cost_estimation': True,
        'cost_threshold_warning': 1.0,  # Warn if cost exceeds $1
        'rate_limit_delay': 1.0,
    }

    if env == Environment.DEVELOPMENT:
        return {
            **base_config,
            'max_tokens': 2000,  # Smaller tokens for faster dev iteration
            'temperature': 0.5,  # More deterministic for debugging
            'enable_cost_estimation': True,
            'cost_threshold_warning': 0.5,  # Lower threshold in dev
            'rate_limit_delay': 0.5,
        }

    elif env == Environment.TESTING:
        return {
            **base_config,
            'default_provider': 'mock',  # Use mock provider for tests
            'max_tokens': 1000,
            'temperature': 0.0,  # Deterministic for tests
            'enable_cost_estimation': False,  # Skip cost estimation in tests
            'cost_threshold_warning': 999.0,  # Disable warnings
            'rate_limit_delay': 0.0,  # No delays in tests
        }

    elif env == Environment.PRODUCTION:
        return {
            **base_config,
            'max_tokens': 4000,
            'temperature': 0.7,
            'enable_cost_estimation': True,
            'cost_threshold_warning': 2.0,  # Higher threshold for production
            'rate_limit_delay': 1.5,  # More conservative rate limiting
        }

    else:  # LOCAL
        return base_config