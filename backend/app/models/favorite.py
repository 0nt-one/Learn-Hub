from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.time import utc_now


class Favorite(Base):
    __tablename__ = "favorites"

    __table_args__ = (
        UniqueConstraint("user_id", "resource_id", name="uq_favorites_user_resource"),
        Index("ix_favorites_user_created", "user_id", "created_at"),
        Index("ix_favorites_resource_id", "resource_id"),
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
