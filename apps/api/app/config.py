from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PPT Single-Slide Optimizer API"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://ppt_agent:ppt_agent@localhost:5432/ppt_agent"
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "default"

    storage_backend: Literal["local"] = "local"
    storage_root: Path = Path("/app/storage")
    artifact_ttl_days: int = Field(default=7, gt=0)

    libreoffice_bin: str = "libreoffice"
    pdftoppm_bin: str = "pdftoppm"
    render_dpi: int = Field(default=150, gt=0)
    render_timeout_seconds: int = Field(default=90, gt=0)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", "redis_url", "libreoffice_bin", "pdftoppm_bin")
    @classmethod
    def _reject_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
