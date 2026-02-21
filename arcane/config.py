"""Configuration settings for Arcane.

Uses pydantic-settings to load configuration from environment variables
and .env files. All env vars are prefixed with ARCANE_.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables are prefixed with ARCANE_, e.g.:
    - ARCANE_ANTHROPIC_API_KEY -> anthropic_api_key
    - ARCANE_MODEL -> model
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ARCANE_",
        extra="ignore",  # Ignore extra fields from env that aren't in the model
    )

    # Required for generation
    anthropic_api_key: str = ""
    model: str = "sonnet"
    max_retries: int = 3

    # Optional - Project Management integrations
    linear_api_key: str | None = None
    jira_domain: str | None = None
    jira_email: str | None = None
    jira_api_token: str | None = None
    notion_api_key: str | None = None

    # Behavior settings
    interactive: bool = True  # Whether to pause for user review between levels
    auto_save: bool = True
    output_dir: str = "./"
