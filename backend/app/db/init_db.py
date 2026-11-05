from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.engine import create_db_engine
from app.db import model_registry

def initialize_database(settings: Settings) -> None:
    if set(Base.metadata.tables) != model_registry.EXPECTED_TABLES:
        raise RuntimeError("模型表未注册完整")

    database_path = make_url(settings.database_url).database
    if database_path is None:
        raise ValueError("SQLite 数据库路径不能为空")
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_db_engine(settings)
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    initialize_database(get_settings())
    print("数据库初始化完成")
