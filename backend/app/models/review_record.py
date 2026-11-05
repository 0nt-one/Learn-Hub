from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


class ReviewRecord(Base):
    __tablename__ = "review_records"

    __table_args__ = (
        CheckConstraint("resource_version > 0", name="ck_reviews_resource_version_positive"),
        CheckConstraint("decision IN ('approved', 'rejected')", name="ck_reviews_decision"),
        CheckConstraint("length(comment) <= 2000", name="ck_reviews_comment_length"),
        CheckConstraint(
            "decision != 'rejected' OR length(trim(comment)) > 0",
            name="ck_reviews_rejection_comment",
        ),
        Index("ix_reviews_reviewer_created", "reviewer_id", "created_at"),
        UniqueConstraint(
            "resource_id",
            "resource_version",
            name="uq_reviews_resource_version"
        ),

    )

    id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_version: Mapped[int] = mapped_column(nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
