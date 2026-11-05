"""Versioned router; feature routers are added as their use cases are implemented."""

from fastapi import APIRouter

from app.api.v1.auth import auth_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)

