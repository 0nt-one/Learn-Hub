from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import AuthFailure, get_current_user
from app.db.session import get_db_session
from app.models.course import Course
from app.models.user import User
from app.schemas.course import (
    CourseCreateRequest,
    CourseEnvelope,
    CourseListData,
    CourseListEnvelope,
    CoursePublic,
    CourseUpdateRequest,
)
from app.services.courses import (
    CourseCodeExistsError,
    CourseNotFoundError,
    CoursePermissionError,
    TeacherIdForbiddenError,
    TeacherIdRequiredError,
    TeacherNotFoundError,
    TeacherUnavailableError,
    create_course,
    find_course_by_id,
    list_courses,
    update_course,
)


courses_router = APIRouter(prefix="/courses")


def course_public_items(session: Session, courses: list[Course]) -> list[CoursePublic]:
    if not courses:
        return []
    teacher_ids = {course.teacher_id for course in courses}
    teacher_names = dict(
        session.execute(
            select(User.id, User.display_name).where(User.id.in_(teacher_ids))
        ).all()
    )
    return [
        CoursePublic(
            id=course.id,
            code=course.code,
            title=course.title,
            description=course.description,
            teacher_id=course.teacher_id,
            teacher_display_name=teacher_names[course.teacher_id],
            is_active=course.is_active,
            created_at=course.created_at,
            updated_at=course.updated_at,
        )
        for course in courses
    ]


@courses_router.get("", response_model=CourseListEnvelope)
def get_courses(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    is_active: bool | None = None,
) -> JSONResponse:
    if current_user.role != "admin":
        if is_active is False:
            raise AuthFailure(403, "FORBIDDEN", "无权查看停用课程")
        effective_is_active = True
    else:
        effective_is_active = is_active

    courses, total = list_courses(
        session,
        page=page,
        page_size=page_size,
        query=q,
        is_active=effective_is_active,
    )
    request_id = str(uuid4())
    body = CourseListEnvelope(
        data=CourseListData(
            items=course_public_items(session, courses),
            total=total,
            page=page,
            page_size=page_size,
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@courses_router.get("/mine", response_model=CourseListEnvelope)
def get_my_courses(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    is_active: bool | None = None,
) -> JSONResponse:
    if current_user.role != "teacher":
        raise AuthFailure(403, "FORBIDDEN", "只有教师可以查看本人课程")

    courses, total = list_courses(
        session,
        page=page,
        page_size=page_size,
        query=q,
        is_active=is_active,
        teacher_id=current_user.id,
    )
    request_id = str(uuid4())
    body = CourseListEnvelope(
        data=CourseListData(
            items=course_public_items(session, courses),
            total=total,
            page=page,
            page_size=page_size,
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@courses_router.get("/{course_id}", response_model=CourseEnvelope)
def get_course(
    course_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    course = find_course_by_id(session, course_id)
    if course is None or (
        not course.is_active
        and current_user.role != "admin"
        and not (
            current_user.role == "teacher" and course.teacher_id == current_user.id
        )
    ):
        raise AuthFailure(404, "NOT_FOUND", "课程不存在")

    request_id = str(uuid4())
    body = CourseEnvelope(
        data=course_public_items(session, [course])[0],
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@courses_router.post("", response_model=CourseEnvelope, status_code=201)
def post_course(
    data: CourseCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-ID": request_id}

    try:
        course = create_course(
            session,
            actor=current_user,
            data=data,
            request_id=request_id,
        )
    except CoursePermissionError:
        status_code, code, message = 403, "FORBIDDEN", "无权创建课程"
    except (TeacherIdForbiddenError, TeacherIdRequiredError):
        status_code, code, message = 422, "VALIDATION_ERROR", "负责人字段不符合当前角色要求"
    except TeacherNotFoundError:
        status_code, code, message = 404, "NOT_FOUND", "指定的教师不存在"
    except TeacherUnavailableError:
        status_code, code, message = 409, "REFERENCE_INACTIVE", "负责人必须是启用的教师"
    except CourseCodeExistsError:
        status_code, code, message = 409, "COURSE_CODE_EXISTS", "课程代码已存在"
    else:
        body = CourseEnvelope(
            data=course_public_items(session, [course])[0],
            request_id=request_id,
        )
        return JSONResponse(
            status_code=201,
            headers=headers,
            content=body.model_dump(mode="json"),
        )

    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "error": {"code": code, "message": message},
            "request_id": request_id,
        },
    )


@courses_router.patch("/{course_id}", response_model=CourseEnvelope)
def patch_course(
    course_id: Annotated[int, Path(gt=0)],
    data: CourseUpdateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-ID": request_id}
    try:
        course = update_course(
            session,
            actor=current_user,
            course_id=course_id,
            data=data,
            request_id=request_id,
        )
    except CourseNotFoundError:
        status_code, code, message = 404, "NOT_FOUND", "课程不存在"
    except CoursePermissionError:
        status_code, code, message = 403, "FORBIDDEN", "无权修改课程"
    except (TeacherIdForbiddenError, TeacherIdRequiredError):
        status_code, code, message = 422, "VALIDATION_ERROR", "负责人字段不符合当前角色要求"
    except TeacherNotFoundError:
        status_code, code, message = 404, "NOT_FOUND", "指定的教师不存在"
    except TeacherUnavailableError:
        status_code, code, message = 409, "REFERENCE_INACTIVE", "负责人必须是启用的教师"
    except CourseCodeExistsError:
        status_code, code, message = 409, "COURSE_CODE_EXISTS", "课程代码已存在"
    else:
        body = CourseEnvelope(
            data=course_public_items(session, [course])[0],
            request_id=request_id,
        )
        return JSONResponse(
            status_code=200,
            headers=headers,
            content=body.model_dump(mode="json"),
        )

    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "error": {"code": code, "message": message},
            "request_id": request_id,
        },
    )
