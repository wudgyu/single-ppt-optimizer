from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]
ENV_KEYS = (
    "APP_NAME",
    "APP_ENV",
    "APP_HOST",
    "APP_PORT",
    "LOG_LEVEL",
    "DATABASE_URL",
    "REDIS_URL",
    "QUEUE_NAME",
    "STORAGE_BACKEND",
    "STORAGE_ROOT",
    "ARTIFACT_TTL_DAYS",
    "LIBREOFFICE_BIN",
    "PDFTOPPM_BIN",
    "RENDER_DPI",
    "RENDER_TIMEOUT_SECONDS",
)


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _load_settings(env_file: str | Path | None = None) -> Settings:
    # pydantic-settings accepts _env_file at runtime but omits it from the typed signature.
    return Settings(_env_file=env_file)  # type: ignore[call-arg]


def test_defaults_are_usable_without_environment() -> None:
    settings = _load_settings()

    assert settings.app_name == "PPT Single-Slide Optimizer API"
    assert settings.app_env == "local"
    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 8000
    assert settings.log_level == "INFO"
    assert settings.database_url == (
        "postgresql+psycopg://ppt_agent:ppt_agent@localhost:5432/ppt_agent"
    )
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.queue_name == "default"
    assert settings.storage_backend == "local"
    assert settings.storage_root == Path("/app/storage")
    assert settings.artifact_ttl_days == 7
    assert settings.libreoffice_bin == "libreoffice"
    assert settings.pdftoppm_bin == "pdftoppm"
    assert settings.render_dpi == 150
    assert settings.render_timeout_seconds == 90


def test_environment_overrides_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    overrides = {
        "APP_ENV": "test",
        "APP_HOST": "127.0.0.1",
        "APP_PORT": "8123",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "postgresql+psycopg://user:secret@db:5432/custom",
        "REDIS_URL": "redis://cache:6379/2",
        "QUEUE_NAME": "custom",
        "STORAGE_BACKEND": "local",
        "STORAGE_ROOT": "/var/lib/ppt-agent",
        "ARTIFACT_TTL_DAYS": "14",
        "LIBREOFFICE_BIN": "/opt/libreoffice",
        "PDFTOPPM_BIN": "/opt/pdftoppm",
        "RENDER_DPI": "200",
        "RENDER_TIMEOUT_SECONDS": "30",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    settings = _load_settings()

    assert settings.app_env == "test"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8123
    assert settings.log_level == "DEBUG"
    assert settings.database_url == "postgresql+psycopg://user:secret@db:5432/custom"
    assert settings.redis_url == "redis://cache:6379/2"
    assert settings.queue_name == "custom"
    assert settings.storage_root == Path("/var/lib/ppt-agent")
    assert settings.artifact_ttl_days == 14
    assert settings.libreoffice_bin == "/opt/libreoffice"
    assert settings.pdftoppm_bin == "/opt/pdftoppm"
    assert settings.render_dpi == 200
    assert settings.render_timeout_seconds == 30


def test_environment_names_are_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("app_port", "8124")

    settings = _load_settings()

    assert settings.app_port == 8124


def test_relative_storage_root_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_ROOT", "storage")

    settings = _load_settings()

    assert settings.storage_root == Path("storage")


def test_unknown_environment_variables_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNKNOWN_SETTING", "ignored")

    settings = _load_settings()

    assert settings.queue_name == "default"


def test_example_environment_file_is_parseable() -> None:
    example_path = REPO_ROOT / ".env.example"

    settings = _load_settings(example_path)
    example_text = example_path.read_text(encoding="utf-8")

    assert settings.app_port == 8000
    assert settings.database_url == (
        "postgresql+psycopg://ppt_agent:ppt_agent@postgres:5432/ppt_agent"
    )
    assert settings.redis_url == "redis://redis:6379/0"
    assert settings.queue_name == "default"
    assert settings.storage_root == Path("/app/storage")
    assert settings.libreoffice_bin == "/usr/bin/libreoffice"
    assert settings.pdftoppm_bin == "/usr/bin/pdftoppm"
    assert "LLM_API_KEY=set-in-secret-manager" in example_text


def test_get_settings_is_cached() -> None:
    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()

    assert get_settings() is not first


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("APP_PORT", "0"),
        ("APP_PORT", "70000"),
        ("APP_PORT", "not-a-number"),
        ("RENDER_DPI", "0"),
        ("RENDER_DPI", "-1"),
        ("RENDER_TIMEOUT_SECONDS", "0"),
        ("ARTIFACT_TTL_DAYS", "0"),
        ("DATABASE_URL", ""),
        ("REDIS_URL", ""),
        ("LIBREOFFICE_BIN", ""),
        ("PDFTOPPM_BIN", ""),
        ("STORAGE_BACKEND", "s3"),
    ],
)
def test_invalid_settings_are_rejected(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)

    with pytest.raises(ValidationError):
        _load_settings()
