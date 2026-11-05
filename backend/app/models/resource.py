from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


class Resource(Base):
    __tablename__ = "resources"

    __table_args__ = (
        CheckConstraint("length(title) BETWEEN 1 AND 200", name="ck_resources_title_length"),
        CheckConstraint("length(description) <= 5000", name="ck_resources_description_length"),
        CheckConstraint("length(url) BETWEEN 1 AND 2048", name="ck_resources_url_length"),
        CheckConstraint(
            "resource_type IN ('document', 'video', 'link')",
            name="ck_resources_type",
        ),
        CheckConstraint(
            "status IN ('draft', 'pending', 'approved', 'rejected', 'archived')",
            name="ck_resources_status",
        ),
        CheckConstraint(
            """
            (resource_type = 'video'
                AND duration_seconds IS NOT NULL
                AND duration_seconds > 0 
                AND page_count IS NULL)
            OR
            (resource_type = 'document'
                AND duration_seconds IS NULL
                AND (page_count IS NULL OR page_count > 0))
            OR
            (resource_type = 'link'
                AND duration_seconds IS NULL
                AND page_count IS NULL)
                
            """,
            name="ck_resources_type_metadata",
        ),
        CheckConstraint(
            "version_id > 0",
            name="ck_resources_version_positive",
        ),

        Index("ix_resources_course_status_created", "course_id", "status", "created_at"),
        Index("ix_resources_category_status_created", "category_id", "status", "created_at"),
        Index("ix_resources_status_created", "status", "created_at"),
        Index("ix_resources_owner_created", "owner_id", "created_at"),

    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    resource_type: Mapped[str] = mapped_column(String(16), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    duration_seconds: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    page_count: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="draft"
    )
    version_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    __mapper_args__ = {
        "version_id_col": version_id,
    }