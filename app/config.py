"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "notes_db"

    # Application
    app_env: str = "development"
    secret_key: str = "change-this-secret-key-in-production"
    app_name: str = "NoteFlow"
    app_version: str = "1.0.0"
    app_tagline: str = "Capture ideas. Organize thoughts. Get things done."

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
