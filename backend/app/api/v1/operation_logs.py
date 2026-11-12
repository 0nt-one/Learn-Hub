from datetime import datetime
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.operation_log import (
    OperationLogListData,
    OperationLogListEnvelope,
    OperationLogPublic,
)
from app.services.operation_logs import list_operation_logs


operation_logs_router = APIRouter(prefix="/operation-logs")


@operation_logs_router.get("", response_model=OperationLogListEnvelope)
def get_operation_logs(
    session: Annotated[Session, Depends(get_db_session)],
    _admin_user: Annotated[User, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    actor_id: Annotated[int | None, Query(gt=0)] = None,
    action: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    target_type: Literal["user", "course", "category", "resource"] | None = None,
    target_id: Annotated[int | None, Query(gt=0)] = None,
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
) -> JSONResponse:
    request_id = str(uuid4())
    for value in (created_from, created_to):
        if value is not None and value.utcoffset() is None:
            return _invalid_time_range(request_id)
    if created_from is not None and created_to is not None and created_from > created_to:
        return _invalid_time_range(request_id)

    items, total = list_operation_logs(
        session,
        page=page,
        page_size=page_size,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        created_from=created_from,
        created_to=created_to,
    )
    body = OperationLogListEnvelope(
        data=OperationLogListData(
            items=[OperationLogPublic.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


def _invalid_time_range(request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        headers={"X-Request-ID": request_id},
        content={
            "error": {"code": "VALIDATION_ERROR", "message": "时间必须带时区，且起点不能晚于终点"},
            "request_id": request_id,
        },
    )
