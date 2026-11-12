"""Check whether the configured SQLite database is ready for requests."""

from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.engine import create_db_engine
from app.db.model_registry import EXPECTED_TABLES


def database_is_ready(settings: Settings) -> bool:
    database_path = make_url(settings.database_url).database
    if database_path != ":memory:" and (
        database_path is None or not Path(database_path).is_file()
    ):
        return False

    engine = create_db_engine(settings)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            existing_tables = set(inspect(connection).get_table_names())
        return EXPECTED_TABLES.issubset(existing_tables)
    except SQLAlchemyError:
        return False
    finally:
        engine.dispose()
