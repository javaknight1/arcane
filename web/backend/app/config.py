from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://arcane:arcane_dev@localhost:5432/arcane"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-20250514"

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str = ""  # Fernet key; empty = PM credential encryption disabled

    model_config = {"env_prefix": "ARCANE_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
