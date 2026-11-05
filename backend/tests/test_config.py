"""Configuration boundaries used by application startup."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.engine import make_url

from app.core.config import BACKEND_DIR, Settings


def make_settings(**overrides: object) -> Settings:
    values = {
        "app_env": "testing",
        "database_url": "sqlite:///:memory:",
        "cors_origins": [],
        **overrides,
    }
    return Settings(_env_file=None, **values)


def test_relative_database_path_is_independent_of_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    settings = make_settings(database_url="sqlite:///data/learn_hub.db")

    assert make_url(settings.database_url).database == (
        BACKEND_DIR / "data" / "learn_hub.db"
    ).resolve().as_posix()
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize(
    "database_url",
    ["not-a-database-url", "postgresql://localhost/example", "sqlite+aiosqlite:///example.db"],
)
def test_invalid_or_unsupported_database_urls_are_rejected(database_url: str) -> None:
    with pytest.raises(ValidationError):
        make_settings(database_url=database_url)


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.example.com",
        "https://user:password@example.com",
        "https://example.com/private",
        "https://example.com?query=value",
        "https://example.com#fragment",
        "http://example.com:99999",
    ],
)
def test_non_origin_cors_values_are_rejected(origin: str) -> None:
    with pytest.raises(ValidationError):
        make_settings(cors_origins=[origin])
