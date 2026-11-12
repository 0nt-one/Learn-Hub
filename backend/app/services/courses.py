from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.course import CourseCreateRequest, CourseUpdateRequest

class TeacherIdForbiddenError(Exception):
    pass


class TeacherIdRequiredError(Exception):
    pass


class TeacherNotFoundError(Exception):
    pass


class TeacherUnavailableError(Exception):
    pass


class CoursePermissionError(Exception):
    pass


class CourseCodeExistsError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass

def resolve_teacher_id(
        session:Session,
        *,
        actor:User,
        data:CourseCreateRequest,
) -> int:
    if actor.role == "teacher":
        if "teacher_id" in data.model_fields_set:
            raise TeacherIdForbiddenError
        return actor.id

    if actor.role == "admin":
        if  data.teacher_id is None:
            raise TeacherIdRequiredError

        teacher = session.get(User, data.teacher_id)
        if teacher is None:
            raise TeacherNotFoundError
        if teacher.role != "teacher" or not teacher.is_active:
            raise TeacherUnavailableError
        return teacher.id

    raise CoursePermissionError


def create_course(
    session: Session,
    *,
    actor: User,
    data: CourseCreateRequest,
    request_id: str,
) -> Course:
    teacher_id = resolve_teacher_id(session, actor=actor, data=data)
    course = Course(
        code=data.code,
        title=data.title,
        description=data.description,
        teacher_id=teacher_id,
    )
    session.add(course)
    try:
        session.flush()
        session.add(
            OperationLog(
                actor_id=actor.id,
                action="course.create",
                target_type="course",
                target_id=course.id,
                request_id=request_id,
                summary="创建课程",
            )
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if str(exc.orig) == "UNIQUE constraint failed: courses.code":
            raise CourseCodeExistsError from exc
        raise
    session.refresh(course)
    return course


def list_courses(
    session: Session,
    *,
    page: int,
    page_size: int,
    query: str | None,
    is_active: bool | None,
    teacher_id: int | None = None,
) -> tuple[list[Course], int]:
    statement = select(Course)
    if query:
        statement = statement.where(Course.title.contains(query, autoescape=True))
    if is_active is not None:
        statement = statement.where(Course.is_active == is_active)
    if teacher_id is not None:
        statement = statement.where(Course.teacher_id == teacher_id)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.scalar(count_statement) or 0
    offset = (page - 1) * page_size
    courses = list(
        session.scalars(
            statement
            .order_by(Course.created_at.desc(), Course.id.desc())
            .offset(offset)
            .limit(page_size)
        ).all()
    )
    return courses, total


def find_course_by_id(session: Session, course_id: int) -> Course | None:
    return session.get(Course, course_id)

def resolve_updated_teacher_id(
        session:Session,
        *,
        actor:User,
        course:Course,
        data:CourseUpdateRequest
) -> int:
    is_admin = actor.role == "admin"
    is_owner = actor.role == "teacher" and course.teacher_id == actor.id

    if not is_admin and not is_owner:
        raise CoursePermissionError

    if "teacher_id" not in data.model_fields_set:
        return course.teacher_id
    if not is_admin:
        raise TeacherIdForbiddenError
    if data.teacher_id is None:
        raise TeacherIdRequiredError

    teacher = session.get(User, data.teacher_id)
    if teacher is None:
        raise TeacherNotFoundError
    if teacher.role != "teacher" or not teacher.is_active:
        raise TeacherUnavailableError

    return teacher.id


def update_course(
    session: Session,
    *,
    actor: User,
    course_id: int,
    data: CourseUpdateRequest,
    request_id: str,
) -> Course:
    course = session.get(Course, course_id)
    if course is None:
        raise CourseNotFoundError

    teacher_id = resolve_updated_teacher_id(
        session,
        actor=actor,
        course=course,
        data=data,
    )
    if data.code is not None:
        course.code = data.code
    if data.title is not None:
        course.title = data.title
    if data.description is not None:
        course.description = data.description
    if data.is_active is not None:
        course.is_active = data.is_active
    course.teacher_id = teacher_id

    session.add(
        OperationLog(
            actor_id=actor.id,
            action="course.update",
            target_type="course",
            target_id=course.id,
            request_id=request_id,
            summary="修改课程",
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if str(exc.orig) == "UNIQUE constraint failed: courses.code":
            raise CourseCodeExistsError from exc
        raise
    session.refresh(course)
    return course
