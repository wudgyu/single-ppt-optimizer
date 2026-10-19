from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PPT Single-Slide Optimizer API"
    log_level: str = "INFO"
    storage_backend: str = "local"
    storage_root: str = "/app/storage"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
