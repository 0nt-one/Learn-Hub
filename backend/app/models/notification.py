from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


class Notification(Base):
    __tablename__ = "notifications"

    __table_args__ = (
        CheckConstraint("kind IN ('review_result', 'system')", name="ck_notifications_kind"),
        CheckConstraint("length(title) BETWEEN 1 AND 200", name="ck_notifications_title_length"),
        CheckConstraint("length(content) <= 2000", name="ck_notifications_content_length"),
        CheckConstraint(
            """
            (kind = 'review_result' AND review_record_id IS NOT NULL)
            OR
            (kind = 'system' AND review_record_id IS NULL)
            """,
            name="ck_notifications_kind_review",
        ),
        UniqueConstraint("user_id", "review_record_id", name="uq_notifications_user_review"),
        Index("ix_notifications_user_read_created", "user_id", "read_at", "created_at"),
        Index("ix_notifications_review_record_id", "review_record_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    review_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("review_records.id", ondelete="RESTRICT"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
