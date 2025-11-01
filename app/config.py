"""Runtime configuration for the API service."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field(default="Hardware Insight Console API")
    api_prefix: str = Field(default="/api")
    database_url: str = Field(default=f"sqlite:///{Path('data/hic.db').as_posix()}")
    allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    class Config:
        env_prefix = "HIC_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
