from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.db.health import database_is_ready

health_router = APIRouter()

@health_router.get("/health")
def get_health(request: Request) -> JSONResponse:
    request_id = str(uuid4())
    headers = {
        "X-Request-ID": request_id,
        "Cache-Control": "no-store",
    }

    if database_is_ready(request.app.state.settings):
        return JSONResponse(
            status_code=200,
            headers=headers,
            content={
                "data":{
                    "status": "ok",
                    "service": "learn-hub-api",
                    "database": "ready",
                },
                "request_id": request_id,
            },
        )
    return JSONResponse(
        status_code=503,
        headers=headers,
        content={
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "服务暂不可用",
            },
            "request_id": request_id,
        }
    )
