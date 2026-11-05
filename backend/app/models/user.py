from datetime import datetime
from sqlalchemy import CheckConstraint, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


class User(Base):
    __tablename__ = 'users'

    __table_args__ = (
        CheckConstraint(
            "length(username) BETWEEN 3 AND 32",
            name="ck_users_username_length"
        ),
        CheckConstraint(
            "role IN ('student', 'teacher', 'admin')",
            name="ck_users_role"
        ),
        CheckConstraint(
            "length(display_name) BETWEEN 1 AND 64",
            name="ck_users_display_name_length"
        ),
        CheckConstraint(
            "length(password_hash) BETWEEN 1 AND 255",
            name="ck_users_password_hash_length"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(32,collation='NOCASE'),
        nullable=False,
        unique=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(16),
        default="student",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean(
            create_constraint=True,
            name="ck_users_is_active",
        ),
        nullable=False,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

