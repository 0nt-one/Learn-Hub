
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.core.config import Settings

def create_db_engine(settings: Settings) -> Engine:
    engine = create_engine(settings.database_url)

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection,connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine
