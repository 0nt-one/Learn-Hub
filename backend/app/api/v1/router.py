"""Versioned router; feature routers are added as their use cases are implemented."""

from fastapi import APIRouter

from app.api.v1.auth import auth_router
from app.api.v1.categories import categories_router
from app.api.v1.courses import courses_router
from app.api.v1.favorites import favorites_router
from app.api.v1.learning import learning_router
from app.api.v1.notifications import notifications_router
from app.api.v1.operation_logs import operation_logs_router
from app.api.v1.resources import resources_router
from app.api.v1.reviews import reviews_router
from app.api.v1.users import users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(courses_router)
api_router.include_router(favorites_router)
api_router.include_router(learning_router)
api_router.include_router(notifications_router)
api_router.include_router(operation_logs_router)
api_router.include_router(resources_router)
api_router.include_router(reviews_router)
api_router.include_router(users_router)
