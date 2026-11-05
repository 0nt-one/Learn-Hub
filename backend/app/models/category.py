from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Text, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


class Category(Base):
    __tablename__ = "categories"

    __table_args__ = (
        CheckConstraint(
            "length(description) <= 1000",
            name="ck_categories_description_length",
        ),
        CheckConstraint(
            "length(name) BETWEEN 1 AND 64",
            name="ck_categories_name_length",

        )
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name:Mapped[str] = mapped_column(
        String(64,collation='NOCASE'),
        unique=True,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean(create_constraint=True, name="ck_categories_is_active"),
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

