from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError

from app.models.category import Category
from app.models.course import Course
from app.models.resource import Resource
from app.models.review_record import ReviewRecord
from app.models.user import User
from app.schemas.review import ReviewCreateRequest
from app.services.review_events import ResourceReviewed, ReviewEventDispatcher


class ReviewNotFoundError(Exception):
    pass


class ReviewForbiddenError(Exception):
    pass


class SelfReviewForbiddenError(Exception):
    pass


class ReviewStateError(Exception):
    pass


class ReviewVersionError(Exception):
    pass


class ReviewReferenceInactiveError(Exception):
    pass


def list_pending_reviews(
    session: Session,
    *,
    actor: User,
    page: int,
    page_size: int,
    course_id: int | None,
) -> tuple[list[Resource], int]:
    if actor.role not in {"teacher", "admin"}:
        raise ReviewForbiddenError
    statement = (
        select(Resource)
        .join(Course, Course.id == Resource.course_id)
        .where(Resource.status == "pending", Resource.owner_id != actor.id)
    )
    if actor.role == "teacher":
        statement = statement.where(Course.teacher_id == actor.id)
    if course_id is not None:
        statement = statement.where(Resource.course_id == course_id)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = list(
        session.scalars(
            statement.order_by(Resource.created_at.asc(), Resource.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def list_resource_reviews(
    session: Session,
    *,
    actor: User,
    resource_id: int,
    page: int,
    page_size: int,
) -> tuple[list[ReviewRecord], int]:
    resource = session.get(Resource, resource_id)
    if resource is None:
        raise ReviewNotFoundError
    if actor.role != "admin" and resource.owner_id != actor.id:
        course = session.get(Course, resource.course_id)
        if course is None or actor.role != "teacher" or course.teacher_id != actor.id:
            raise ReviewNotFoundError

    statement = select(ReviewRecord).where(ReviewRecord.resource_id == resource_id)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = list(
        session.scalars(
            statement.order_by(ReviewRecord.created_at.desc(), ReviewRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def review_resource(
    session: Session,
    *,
    actor: User,
    resource_id: int,
    data: ReviewCreateRequest,
    request_id: str,
    dispatcher: ReviewEventDispatcher,
) -> tuple[ReviewRecord, Resource]:
    resource = session.get(Resource, resource_id)
    if resource is None:
        raise ReviewNotFoundError
    course = session.get(Course, resource.course_id)
    if course is None:
        raise ReviewNotFoundError
    if actor.role != "admin" and not (
        actor.role == "teacher" and course.teacher_id == actor.id
    ):
        raise ReviewForbiddenError
    if resource.owner_id == actor.id:
        raise SelfReviewForbiddenError
    if resource.status != "pending":
        raise ReviewStateError
    if resource.version_id != data.expected_version:
        raise ReviewVersionError
    if data.decision == "approved":
        category = session.get(Category, resource.category_id)
        if category is None or not course.is_active or not category.is_active:
            raise ReviewReferenceInactiveError

    review = ReviewRecord(
        resource_id=resource.id,
        reviewer_id=actor.id,
        resource_version=resource.version_id,
        decision=data.decision,
        comment=data.comment,
    )
    try:
        session.add(review)
        session.flush()
        resource.status = data.decision
        dispatcher.publish(
            session,
            ResourceReviewed(
                review_id=review.id,
                resource_id=resource.id,
                owner_id=resource.owner_id,
                reviewer_id=actor.id,
                decision=data.decision,
                request_id=request_id,
            ),
        )
        session.commit()
    except StaleDataError as exc:
        session.rollback()
        raise ReviewVersionError from exc
    except IntegrityError as exc:
        session.rollback()
        if "review_records.resource_id, review_records.resource_version" in str(exc.orig):
            raise ReviewVersionError from exc
        raise
    except Exception:
        session.rollback()
        raise
    session.refresh(review)
    session.refresh(resource)
    return review, resource
