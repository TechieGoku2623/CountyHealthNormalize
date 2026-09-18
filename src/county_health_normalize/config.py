"""Application settings and runtime configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional .env."""

    model_config = SettingsConfigDict(
        env_prefix="CHN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_source: str = Field(
        default="generic_csv",
        description="Default adapter used when no source is specified.",
    )
    output_dir: Path = Field(
        default=Path("data/processed"),
        description="Directory for normalized outputs.",
    )
    strict: bool = Field(
        default=True,
        description="Drop rows that fail schema validation when True.",
    )
    log_level: str = Field(default="INFO", description="Root log level.")


def get_settings() -> Settings:
    return Settings()
