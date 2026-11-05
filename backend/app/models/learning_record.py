from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


class LearningRecord(Base):
    __tablename__ = "learning_records"

    __table_args__ = (
        UniqueConstraint("user_id", "resource_id", name="uq_learning_user_resource"),
        Index("ix_learning_user_accessed", "user_id", "last_accessed_at"),
        Index("ix_learning_resource_id", "resource_id"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_learning_progress_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
