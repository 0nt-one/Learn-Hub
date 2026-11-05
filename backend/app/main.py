"""FastAPI application assembly."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import health_router
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.db.engine import create_db_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble an application without connecting to or initializing a database."""

    config = settings if settings is not None else get_settings()
    db_engine = create_db_engine(config)

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        try:
            yield
        finally:
            db_engine.dispose()

    application = FastAPI(
        title="Learn-Hub API",
        version="0.1.0",
        description="Learn-Hub 在线学习资源管理与共享平台 API",
        lifespan=lifespan,
    )
    application.state.settings = config
    application.state.db_engine = db_engine
    application.include_router(health_router)
    application.include_router(api_router)

    if config.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    return application

