"""Load and validate backend configuration without creating external resources."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Environment variables take precedence over backend/.env and defaults."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    app_env: Literal["development", "testing", "production"] = "development"
    database_url: str = "sqlite:///data/learn_hub.db"
    cors_origins: list[str] = Field(default_factory=list)
    jwt_secret_key: SecretStr | None = None
    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        try:
            url = make_url(value)
        except ArgumentError as exc:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL") from exc
        if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
            raise ValueError("DATABASE_URL must use synchronous SQLite")
        if url.host is not None or url.username is not None or url.password is not None:
            raise ValueError("SQLite configuration must not contain a host or credentials")
        if not url.database:
            raise ValueError("SQLite database path must not be empty")
        if url.database != ":memory:":
            database_path = Path(url.database)
            if not database_path.is_absolute():
                database_path = BACKEND_DIR / database_path
            url = url.set(database=database_path.resolve().as_posix())
        return url.render_as_string(hide_password=False)

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, values: list[str]) -> list[str]:
        origins: list[str] = []
        for value in values:
            parsed = urlsplit(value)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or "*" in value
                or any(character.isspace() for character in value)
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or "?" in value
                or "#" in value
            ):
                raise ValueError("CORS_ORIGINS must contain exact HTTP(S) origins")
            # Accessing port also validates its syntax and range.
            _ = parsed.port
            origin = value.rstrip("/")
            if origin not in origins:
                origins.append(origin)
        return origins


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process; tests may inject an explicit Settings."""

    return Settings()

