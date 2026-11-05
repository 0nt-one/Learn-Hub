from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now

class Course(Base):
    __tablename__ = "courses"

    __table_args__ = (
        CheckConstraint(
            "length(code) BETWEEN 1 AND 32",
            name="ck_courses_code_length"
        ),
        CheckConstraint(
            "length(title) BETWEEN 1 AND 200",
            name="ck_courses_title_length"
        ),
        CheckConstraint(
            "length(description) <= 5000",
            name="ck_courses_description_length"
        ),
        Index(
            "ix_courses_teacher_id",
            "teacher_id"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(
            32,
            collation='NOCASE',
        ),
        nullable=False,
        unique=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean(create_constraint=True, name="ck_courses_is_active"),
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
