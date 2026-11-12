from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.models.favorite import Favorite
from app.models.category import Category
from app.models.course import Course
from app.models.resource import Resource
from app.services.resources import get_public_resource


def add_favorite(session: Session, *, user_id: int, resource_id: int) -> Favorite:
    get_public_resource(session, resource_id)
    try:
        statement = (
            insert(Favorite)
            .values(user_id=user_id, resource_id=resource_id)
            .on_conflict_do_nothing(index_elements=[Favorite.user_id, Favorite.resource_id])
        )
        session.execute(statement)
        favorite = session.scalar(
            select(Favorite).where(Favorite.user_id == user_id, Favorite.resource_id == resource_id)
        )
        assert favorite is not None
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(favorite)
    return favorite


def remove_favorite(session: Session, *, user_id: int, resource_id: int) -> None:
    try:
        session.execute(
            delete(Favorite).where(Favorite.user_id == user_id, Favorite.resource_id == resource_id)
        )
        session.commit()
    except Exception:
        session.rollback()
        raise


def list_my_favorites(
    session: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[Favorite], dict[int, Resource], int]:
    statement = select(Favorite).where(Favorite.user_id == user_id)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    favorites = list(
        session.scalars(
            statement.order_by(Favorite.created_at.desc(), Favorite.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    ids = {favorite.resource_id for favorite in favorites}
    visible = {}
    if ids:
        resources = session.scalars(
            select(Resource)
            .join(Course, Course.id == Resource.course_id)
            .join(Category, Category.id == Resource.category_id)
            .where(
                Resource.id.in_(ids),
                Resource.status == "approved",
                Course.is_active.is_(True),
                Category.is_active.is_(True),
            )
        ).all()
        visible = {resource.id: resource for resource in resources}
    return favorites, visible, total
