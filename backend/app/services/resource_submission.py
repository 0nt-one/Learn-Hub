from dataclasses import dataclass
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.course import Course
from app.models.resource import Resource
from app.models.user import User
from app.services.resource_validation import validator_for


class SubmissionForbiddenError(Exception):
    pass


class SubmissionStateError(Exception):
    pass


class SubmissionVersionError(Exception):
    pass


class SubmissionReferenceNotFoundError(Exception):
    pass


class SubmissionReferenceInactiveError(Exception):
    pass


class SubmissionMetadataError(Exception):
    pass


@dataclass(frozen=True)
class SubmissionContext:
    session: Session
    actor: User
    resource: Resource
    expected_version: int


def check_owner(context: SubmissionContext) -> None:
    if (
        not context.actor.is_active
        or context.actor.role not in {"student", "teacher"}
        or context.resource.owner_id != context.actor.id
    ):
        raise SubmissionForbiddenError


def check_state_version(context: SubmissionContext) -> None:
    if context.resource.status not in {"draft", "rejected"}:
        raise SubmissionStateError
    if context.resource.version_id != context.expected_version:
        raise SubmissionVersionError


def check_placement(context: SubmissionContext) -> None:
    course = context.session.get(Course, context.resource.course_id)
    category = context.session.get(Category, context.resource.category_id)
    if course is None or category is None:
        raise SubmissionReferenceNotFoundError
    if not course.is_active or not category.is_active:
        raise SubmissionReferenceInactiveError


def check_metadata(context: SubmissionContext) -> None:
    try:
        validate = validator_for(context.resource.resource_type)
        validate(context.resource.duration_seconds, context.resource.page_count)
    except ValueError as exc:
        raise SubmissionMetadataError(str(exc)) from exc


SUBMISSION_CHECKS: tuple[Callable[[SubmissionContext], None], ...] = (
    check_owner,
    check_state_version,
    check_placement,
    check_metadata,
)


def validate_submission(context: SubmissionContext) -> None:
    for check in SUBMISSION_CHECKS:
        check(context)
