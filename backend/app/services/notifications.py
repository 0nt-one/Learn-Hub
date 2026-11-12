from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.time import utc_now
from app.models.notification import Notification


class NotificationNotFoundError(Exception):
    pass


def list_my_notifications(
    session: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    unread_only: bool,
) -> tuple[list[Notification], int]:
    statement = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        statement = statement.where(Notification.read_at.is_(None))
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = list(
        session.scalars(
            statement.order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def mark_notification_read(
    session: Session,
    *,
    user_id: int,
    notification_id: int,
) -> Notification:
    notification = session.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotificationNotFoundError
    if notification.read_at is None:
        try:
            session.execute(
                update(Notification)
                .where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                )
                .values(read_at=utc_now())
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        session.refresh(notification)
    return notification
