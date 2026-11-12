from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from pydantic import ValidationError

from app.models.category import Category
from app.models.course import Course
from app.models.operation_log import OperationLog
from app.models.resource import Resource
from app.models.user import User
from app.schemas.resource import ResourceCreateRequest, ResourceUpdateRequest
from app.services.resource_validation import validator_for
from app.services.resource_submission import (
    SubmissionContext,
    SubmissionVersionError,
    validate_submission,
)


class ResourcePermissionError(Exception):
    pass


class ResourceReferenceNotFoundError(Exception):
    pass


class ResourceReferenceInactiveError(Exception):
    pass


class ResourceMetadataError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


class ResourceInvalidStateError(Exception):
    pass


class ResourceVersionConflictError(Exception):
    pass


def create_resource(
    session: Session,
    *,
    actor: User,
    data: ResourceCreateRequest,
    request_id: str,
) -> Resource:
    if actor.role not in {"student", "teacher"}:
        raise ResourcePermissionError

    validate_metadata = validator_for(data.resource_type)
    try:
        validate_metadata(data.duration_seconds, data.page_count)
    except ValueError as exc:
        raise ResourceMetadataError(str(exc)) from exc

    course = session.get(Course, data.course_id)
    category = session.get(Category, data.category_id)
    if course is None or category is None:
        raise ResourceReferenceNotFoundError
    if not course.is_active or not category.is_active:
        raise ResourceReferenceInactiveError

    resource = Resource(
        title=data.title,
        description=data.description,
        resource_type=data.resource_type,
        url=data.url,
        duration_seconds=data.duration_seconds,
        page_count=data.page_count,
        course_id=course.id,
        category_id=category.id,
        owner_id=actor.id,
        status="draft",
    )
    try:
        session.add(resource)
        session.flush()
        session.add(
            OperationLog(
                actor_id=actor.id,
                action="resource.create",
                target_type="resource",
                target_id=resource.id,
                request_id=request_id,
                summary="创建资源草稿",
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(resource)
    return resource


def list_my_resources(
    session: Session,
    *,
    owner_id: int,
    page: int,
    page_size: int,
    status: str | None,
) -> tuple[list[Resource], int]:
    statement = select(Resource).where(Resource.owner_id == owner_id)
    if status is not None:
        statement = statement.where(Resource.status == status)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = list(
        session.scalars(
            statement.order_by(Resource.created_at.desc(), Resource.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def list_public_resources(
    session: Session,
    *,
    page: int,
    page_size: int,
    query: str | None,
    course_id: int | None,
    category_id: int | None,
    resource_type: str | None,
    sort: str,
) -> tuple[list[Resource], int]:
    statement = (
        select(Resource)
        .join(Course, Course.id == Resource.course_id)
        .join(Category, Category.id == Resource.category_id)
        .where(
            Resource.status == "approved",
            Course.is_active.is_(True),
            Category.is_active.is_(True),
        )
    )
    if query:
        statement = statement.where(Resource.title.contains(query, autoescape=True))
    if course_id is not None:
        statement = statement.where(Resource.course_id == course_id)
    if category_id is not None:
        statement = statement.where(Resource.category_id == category_id)
    if resource_type is not None:
        statement = statement.where(Resource.resource_type == resource_type)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    if sort == "title":
        statement = statement.order_by(Resource.title.asc(), Resource.id.asc())
    else:
        statement = statement.order_by(Resource.created_at.desc(), Resource.id.desc())
    items = list(session.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all())
    return items, total


def list_admin_resources(
    session: Session,
    *,
    page: int,
    page_size: int,
    query: str | None,
    status: str | None,
    course_id: int | None,
    category_id: int | None,
    resource_type: str | None,
    sort: str,
) -> tuple[list[Resource], int]:
    statement = select(Resource)
    if query:
        statement = statement.where(Resource.title.contains(query, autoescape=True))
    if status is not None:
        statement = statement.where(Resource.status == status)
    if course_id is not None:
        statement = statement.where(Resource.course_id == course_id)
    if category_id is not None:
        statement = statement.where(Resource.category_id == category_id)
    if resource_type is not None:
        statement = statement.where(Resource.resource_type == resource_type)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    if sort == "title":
        statement = statement.order_by(Resource.title.asc(), Resource.id.asc())
    else:
        statement = statement.order_by(Resource.created_at.desc(), Resource.id.desc())
    items = list(session.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all())
    return items, total


def get_visible_resource(
    session: Session,
    *,
    actor: User,
    resource_id: int,
) -> Resource:
    resource = session.get(Resource, resource_id)
    if resource is None:
        raise ResourceNotFoundError
    if actor.role == "admin" or resource.owner_id == actor.id:
        return resource

    course = session.get(Course, resource.course_id)
    if course is None:
        raise ResourceNotFoundError
    if resource.status == "pending" and actor.role == "teacher" and course.teacher_id == actor.id:
        return resource
    if resource.status == "approved" and course.is_active:
        category = session.get(Category, resource.category_id)
        if category is not None and category.is_active:
            return resource
    raise ResourceNotFoundError


def get_public_resource(session: Session, resource_id: int) -> Resource:
    resource = session.scalar(
        select(Resource)
        .join(Course, Course.id == Resource.course_id)
        .join(Category, Category.id == Resource.category_id)
        .where(
            Resource.id == resource_id,
            Resource.status == "approved",
            Course.is_active.is_(True),
            Category.is_active.is_(True),
        )
    )
    if resource is None:
        raise ResourceNotFoundError
    return resource


def update_resource(
    session: Session,
    *,
    actor: User,
    resource_id: int,
    data: ResourceUpdateRequest,
    request_id: str,
) -> Resource:
    resource = session.get(Resource, resource_id)
    if resource is None:
        raise ResourceNotFoundError
    if actor.role not in {"student", "teacher"} or resource.owner_id != actor.id:
        raise ResourcePermissionError
    if resource.status not in {"draft", "rejected"}:
        raise ResourceInvalidStateError
    if resource.version_id != data.expected_version:
        raise ResourceVersionConflictError

    current = {
        "title": resource.title,
        "description": resource.description,
        "resource_type": resource.resource_type,
        "url": resource.url,
        "duration_seconds": resource.duration_seconds,
        "page_count": resource.page_count,
        "course_id": resource.course_id,
        "category_id": resource.category_id,
    }
    changes = data.model_dump(exclude_unset=True, exclude={"expected_version"})
    try:
        merged = ResourceCreateRequest.model_validate({**current, **changes})
        validator_for(merged.resource_type)(merged.duration_seconds, merged.page_count)
    except (ValidationError, ValueError) as exc:
        raise ResourceMetadataError("修改后资源字段组合无效") from exc

    course = session.get(Course, merged.course_id)
    category = session.get(Category, merged.category_id)
    if course is None or category is None:
        raise ResourceReferenceNotFoundError
    if not course.is_active or not category.is_active:
        raise ResourceReferenceInactiveError

    for field_name in current:
        setattr(resource, field_name, getattr(merged, field_name))
    session.add(
        OperationLog(
            actor_id=actor.id,
            action="resource.update",
            target_type="resource",
            target_id=resource.id,
            request_id=request_id,
            summary="修改资源",
        )
    )
    try:
        session.commit()
    except StaleDataError as exc:
        session.rollback()
        raise ResourceVersionConflictError from exc
    except Exception:
        session.rollback()
        raise
    session.refresh(resource)
    return resource


def submit_resource(
    session: Session,
    *,
    actor: User,
    resource_id: int,
    expected_version: int,
    request_id: str,
) -> Resource:
    resource = session.get(Resource, resource_id)
    if resource is None:
        raise ResourceNotFoundError
    validate_submission(
        SubmissionContext(
            session=session,
            actor=actor,
            resource=resource,
            expected_version=expected_version,
        )
    )
    resource.status = "pending"
    session.add(
        OperationLog(
            actor_id=actor.id,
            action="resource.submit",
            target_type="resource",
            target_id=resource.id,
            request_id=request_id,
            summary="提交资源审核",
        )
    )
    try:
        session.commit()
    except StaleDataError as exc:
        session.rollback()
        raise SubmissionVersionError from exc
    except Exception:
        session.rollback()
        raise
    session.refresh(resource)
    return resource


def withdraw_resource(
    session: Session,
    *,
    actor: User,
    resource_id: int,
    expected_version: int,
    request_id: str,
) -> Resource:
    resource = session.get(Resource, resource_id)
    if resource is None:
        raise ResourceNotFoundError
    if resource.owner_id != actor.id:
        raise ResourcePermissionError
    if resource.status not in {"pending", "approved"}:
        raise ResourceInvalidStateError
    if resource.version_id != expected_version:
        raise ResourceVersionConflictError

    resource.status = "draft"
    session.add(
        OperationLog(
            actor_id=actor.id,
            action="resource.withdraw",
            target_type="resource",
            target_id=resource.id,
            request_id=request_id,
            summary="撤回资源",
        )
    )
    try:
        session.commit()
    except StaleDataError as exc:
        session.rollback()
        raise ResourceVersionConflictError from exc
    except Exception:
        session.rollback()
        raise
    session.refresh(resource)
    return resource


def archive_resource(
    session: Session,
    *,
    actor: User,
    resource_id: int,
    expected_version: int,
    reason: str,
    request_id: str,
) -> Resource:
    resource = session.get(Resource, resource_id)
    if resource is None:
        raise ResourceNotFoundError
    if resource.status == "archived":
        raise ResourceInvalidStateError
    if actor.role != "admin" and resource.owner_id != actor.id:
        raise ResourcePermissionError
    if resource.status == "pending" and actor.role != "admin":
        raise ResourcePermissionError
    if resource.version_id != expected_version:
        raise ResourceVersionConflictError

    resource.status = "archived"
    session.add(
        OperationLog(
            actor_id=actor.id,
            action="resource.archive",
            target_type="resource",
            target_id=resource.id,
            request_id=request_id,
            summary=reason,
        )
    )
    try:
        session.commit()
    except StaleDataError as exc:
        session.rollback()
        raise ResourceVersionConflictError from exc
    except Exception:
        session.rollback()
        raise
    session.refresh(resource)
    return resource
