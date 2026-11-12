from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import AuthFailure, get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.learning import (
    LearningProgressRequest,
    LearningRecordEnvelope,
    LearningRecordListData,
    LearningRecordListEnvelope,
    LearningRecordListItem,
    LearningRecordPublic,
    LearningRecordResource,
)
from app.services.learning import (
    LearningResourceContext,
    list_my_learning_records,
    upsert_learning_record,
)
from app.services.resources import ResourceNotFoundError

learning_router = APIRouter(prefix="/users/me/learning-records")


def _resource_ref(context: LearningResourceContext) -> LearningRecordResource:
    """把资源上下文转成对外结构：不可公开时只留识别信息，抹掉 url。"""

    resource = context.resource
    return LearningRecordResource(
        id=resource.id,
        title=resource.title,
        resource_type=resource.resource_type,
        course_id=resource.course_id,
        course_title=context.course_title,
        category_id=resource.category_id,
        category_name=context.category_name,
        status=resource.status,
        is_available=context.is_available,
        url=resource.url if context.is_available else None,
    )


@learning_router.get("", response_model=LearningRecordListEnvelope)
def get_my_learning_records(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    records, contexts, total = list_my_learning_records(
        session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    items: list[LearningRecordListItem] = []
    for record in records:
        context = contexts.get(record.resource_id)
        if context is None:
            # 外键为 RESTRICT，资源不会消失；真出现异常数据时跳过而不是 500
            continue
        items.append(
            LearningRecordListItem.model_validate(
                {**record.__dict__, "resource": _resource_ref(context)}
            )
        )

    request_id = str(uuid4())
    body = LearningRecordListEnvelope(
        data=LearningRecordListData(
            items=items,
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


@learning_router.put("/{resource_id}", response_model=LearningRecordEnvelope)
def put_learning_record(
    resource_id: Annotated[int, Path(gt=0)],
    data: LearningProgressRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    try:
        record = upsert_learning_record(
            session,
            user_id=current_user.id,
            resource_id=resource_id,
            progress=data.progress,
        )
    except ResourceNotFoundError as exc:
        # 资源不存在或不可见，一律 404，不区分（避免探测不可见资源）
        raise AuthFailure(404, "NOT_FOUND", "资源不存在") from exc

    request_id = str(uuid4())
    body = LearningRecordEnvelope(
        data=LearningRecordPublic.model_validate(record),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )
