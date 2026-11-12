from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest

class CategoryNameExistsError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass

def create_category(
        session: Session,
        *,
        actor: User,
        data: CategoryCreateRequest,
        request_id:str,
)-> Category:
    category = Category(
        name=data.name,
        description=data.description,
    )
    session.add(category)

    try:
        session.flush()
        session.add(
            OperationLog(
                actor_id=actor.id,
                action="category.create",
                target_type="category",
                target_id=category.id,
                request_id=request_id,
                summary="创建分类",
            )
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if str(exc.orig) == "UNIQUE constraint failed: categories.name":
            raise CategoryNameExistsError from exc
        raise
    session.refresh(category)
    return category

def list_categories(
        session: Session,
        *,
        page:int,
        page_size:int,
        is_active:bool | None,
) -> tuple[list[Category], int]:
    statement = select(Category)

    if is_active is not None:
        statement = statement.where(Category.is_active == is_active)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.scalar(count_statement) or 0

    offset = (page - 1) * page_size
    categories = list(
        session.scalars(
            statement
            .order_by(Category.name.asc(), Category.id.asc())
            .offset(offset)
            .limit(page_size)
        ).all()
    )
    return categories, total


def update_category(
    session: Session,
    *,
    actor: User,
    category_id: int,
    data: CategoryUpdateRequest,
    request_id: str,
) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError

    if data.name is not None:
        category.name = data.name
    if data.description is not None:
        category.description = data.description
    if data.is_active is not None:
        category.is_active = data.is_active

    session.add(
        OperationLog(
            actor_id=actor.id,
            action="category.update",
            target_type="category",
            target_id=category.id,
            request_id=request_id,
            summary="修改分类",
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if str(exc.orig) == "UNIQUE constraint failed: categories.name":
            raise CategoryNameExistsError from exc
        raise
    session.refresh(category)
    return category
