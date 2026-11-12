"""FastAPI application assembly."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.health import health_router
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.db.engine import create_db_engine
from app.services.review_events import (
    ReviewEventDispatcher,
    add_review_audit,
    add_review_notification,
)

def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble an application without connecting to or initializing a database."""

    config = settings if settings is not None else get_settings()
    if config.jwt_secret_key is None:
        raise RuntimeError("JWT_SECRET_KEY is required")

    secret_key_bytes = config.jwt_secret_key.get_secret_value().encode("utf-8")
    if len(secret_key_bytes) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 bytes")
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
    register_exception_handlers(application)
    application.state.settings = config
    application.state.db_engine = db_engine
    application.state.review_dispatcher = ReviewEventDispatcher(
        (add_review_notification, add_review_audit)
    )
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

