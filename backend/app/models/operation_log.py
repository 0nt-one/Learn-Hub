from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


def new_request_id() -> str:
    return str(uuid4())


class OperationLog(Base):
    __tablename__ = "operation_logs"

    __table_args__ = (
        CheckConstraint("length(action) BETWEEN 1 AND 64", name="ck_logs_action_length"),
        CheckConstraint("length(request_id) = 36", name="ck_logs_request_id_length"),
        CheckConstraint("length(summary) <= 2000", name="ck_logs_summary_length"),
        CheckConstraint("target_type IN ('user', 'course', 'category', 'resource')", name="ck_logs_target_type"),
        CheckConstraint("target_id > 0",name="ck_logs_target_id_positive"),
        Index("ix_logs_actor_created", "actor_id", "created_at"),
        Index("ix_logs_target_created", "target_type", "target_id", "created_at"),
        Index("ix_logs_created", "created_at"),
        Index("ix_logs_request_id", "request_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int] = mapped_column(nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_request_id)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
