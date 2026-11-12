from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.notification import Notification
from app.models.resource import Resource
from app.models.review_record import ReviewRecord
from app.models.user import User
from app.schemas.notification import (
    NotificationEnvelope,
    NotificationListData,
    NotificationListEnvelope,
    NotificationPublic,
)
from app.services.notifications import (
    NotificationNotFoundError,
    list_my_notifications,
    mark_notification_read,
)


notifications_router = APIRouter(prefix="/users/me/notifications")


def notification_public_items(
    session: Session, notifications: list[Notification]
) -> list[NotificationPublic]:
    """补上审核类通知关联的资源，供前端点击跳到审核历史。

    通知表本身不存 resource_id，这里用 review_record_id 反查 review_records，
    再取资源标题；每页最多几十条，是两次按主键的 IN 查询，开销可忽略。
    """
    review_ids = [item.review_record_id for item in notifications if item.review_record_id is not None]
    meta: dict[int, tuple[int, str]] = {}

    if review_ids:
        review_rows = session.execute(
            select(ReviewRecord.id, ReviewRecord.resource_id).where(ReviewRecord.id.in_(review_ids))
        ).all()
        resource_ids = {row.resource_id for row in review_rows}
        titles: dict[int, str] = {}
        if resource_ids:
            titles = dict(
                session.execute(
                    select(Resource.id, Resource.title).where(Resource.id.in_(resource_ids))
                ).all()
            )
        meta = {
            row.id: (row.resource_id, titles.get(row.resource_id, ""))
            for row in review_rows
        }

    items: list[NotificationPublic] = []
    for item in notifications:
        resource_id, resource_title = meta.get(item.review_record_id, (None, None))
        items.append(
            NotificationPublic.model_validate(
                {
                    **item.__dict__,
                    "resource_id": resource_id,
                    "resource_title": resource_title or None,
                }
            )
        )
    return items


@notifications_router.get("", response_model=NotificationListEnvelope)
def get_my_notifications(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    unread_only: bool = False,
) -> JSONResponse:
    items, total = list_my_notifications(
        session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    request_id = str(uuid4())
    body = NotificationListEnvelope(
        data=NotificationListData(
            items=notification_public_items(session, items),
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


@notifications_router.patch("/{notification_id}/read", response_model=NotificationEnvelope)
def patch_notification_read(
    notification_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        notification = mark_notification_read(
            session,
            user_id=current_user.id,
            notification_id=notification_id,
        )
    except NotificationNotFoundError:
        return JSONResponse(
            status_code=404,
            headers={"X-Request-ID": request_id},
            content={
                "error": {"code": "NOT_FOUND", "message": "通知不存在"},
                "request_id": request_id,
            },
        )
    body = NotificationEnvelope(
        # 已读后前端会用这个响应替换列表行，所以同样要带 resource_id，否则卡片会失去可点击性
        data=notification_public_items(session, [notification])[0],
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )
