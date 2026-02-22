from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://arcane:arcane_dev@localhost:5432/arcane"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-20250514"

    model_config = {"env_prefix": "ARCANE_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
