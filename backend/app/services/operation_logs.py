from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog


def list_operation_logs(
    session: Session,
    *,
    page: int,
    page_size: int,
    actor_id: int | None,
    action: str | None,
    target_type: str | None,
    target_id: int | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> tuple[list[OperationLog], int]:
    statement = select(OperationLog)
    if actor_id is not None:
        statement = statement.where(OperationLog.actor_id == actor_id)
    if action is not None:
        statement = statement.where(OperationLog.action == action)
    if target_type is not None:
        statement = statement.where(OperationLog.target_type == target_type)
    if target_id is not None:
        statement = statement.where(OperationLog.target_id == target_id)
    if created_from is not None:
        start = created_from.astimezone(timezone.utc).replace(tzinfo=None)
        statement = statement.where(OperationLog.created_at >= start)
    if created_to is not None:
        end = created_to.astimezone(timezone.utc).replace(tzinfo=None)
        statement = statement.where(OperationLog.created_at < end)

    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = list(
        session.scalars(
            statement.order_by(OperationLog.created_at.desc(), OperationLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total
