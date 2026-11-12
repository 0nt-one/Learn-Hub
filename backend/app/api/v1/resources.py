from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db_session
from app.models.category import Category
from app.models.course import Course
from app.models.favorite import Favorite
from app.models.resource import Resource
from app.models.user import User
from app.schemas.resource import (
    ResourceCreateRequest,
    ResourceArchiveRequest,
    ResourceEnvelope,
    ResourceListData,
    ResourceListEnvelope,
    ResourcePublic,
    ResourceSubmitRequest,
    ResourceUpdateRequest,
    ResourceWithdrawRequest,
)
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewEnvelope,
    ReviewListData,
    ReviewListEnvelope,
    ReviewPublic,
    ReviewResult,
)
from app.services.resource_submission import (
    SubmissionForbiddenError,
    SubmissionMetadataError,
    SubmissionReferenceInactiveError,
    SubmissionReferenceNotFoundError,
    SubmissionStateError,
    SubmissionVersionError,
)
from app.services.resources import (
    ResourceMetadataError,
    ResourceNotFoundError,
    ResourceInvalidStateError,
    ResourcePermissionError,
    ResourceReferenceInactiveError,
    ResourceReferenceNotFoundError,
    ResourceVersionConflictError,
    archive_resource,
    create_resource,
    get_visible_resource,
    list_my_resources,
    list_admin_resources,
    list_public_resources,
    submit_resource,
    update_resource,
    withdraw_resource,
)
from app.services.reviews import (
    ReviewForbiddenError,
    ReviewNotFoundError,
    ReviewReferenceInactiveError,
    ReviewStateError,
    ReviewVersionError,
    SelfReviewForbiddenError,
    list_resource_reviews,
    review_resource,
)


resources_router = APIRouter(prefix="/resources")


def resource_public_items(session: Session, user_id: int, resources: list[Resource]) -> list[ResourcePublic]:
    if not resources:
        return []
    course_ids = {resource.course_id for resource in resources}
    category_ids = {resource.category_id for resource in resources}
    courses = {
        course_id: (title, teacher_id)
        for course_id, title, teacher_id in session.execute(
            select(Course.id, Course.title, Course.teacher_id).where(Course.id.in_(course_ids))
        ).all()
    }
    user_ids = {resource.owner_id for resource in resources}
    user_ids.update(teacher_id for _, teacher_id in courses.values())
    user_names = dict(
        session.execute(select(User.id, User.display_name).where(User.id.in_(user_ids))).all()
    )
    category_names = dict(
        session.execute(select(Category.id, Category.name).where(Category.id.in_(category_ids))).all()
    )
    favorited_ids = set(
        session.scalars(
            select(Favorite.resource_id).where(
                Favorite.user_id == user_id,
                Favorite.resource_id.in_({resource.id for resource in resources}),
            )
        ).all()
    )
    return [
        ResourcePublic.model_validate(
            {
                **resource.__dict__,
                "course_title": courses[resource.course_id][0],
                "course_teacher_id": courses[resource.course_id][1],
                "course_teacher_display_name": user_names[courses[resource.course_id][1]],
                "category_name": category_names[resource.category_id],
                "owner_display_name": user_names[resource.owner_id],
                "is_favorited": resource.id in favorited_ids,
            }
        )
        for resource in resources
    ]


def resource_error(status_code: int, code: str, message: str, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers={"X-Request-ID": request_id},
        content={"error": {"code": code, "message": message}, "request_id": request_id},
    )


@resources_router.get("/mine", response_model=ResourceListEnvelope)
def get_my_resources(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Literal["draft", "pending", "approved", "rejected", "archived"] | None = None,
) -> JSONResponse:
    items, total = list_my_resources(
        session,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )
    request_id = str(uuid4())
    body = ResourceListEnvelope(
        data=ResourceListData(
            items=resource_public_items(session, current_user.id, items),
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


@resources_router.get("/admin", response_model=ResourceListEnvelope)
def get_admin_resources(
    session: Annotated[Session, Depends(get_db_session)],
    _admin_user: Annotated[User, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    status: Literal["draft", "pending", "approved", "rejected", "archived"] | None = None,
    course_id: Annotated[int | None, Query(gt=0)] = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    resource_type: Literal["document", "video", "link"] | None = None,
    sort: Literal["newest", "title"] = "newest",
) -> JSONResponse:
    items, total = list_admin_resources(
        session,
        page=page,
        page_size=page_size,
        query=q,
        status=status,
        course_id=course_id,
        category_id=category_id,
        resource_type=resource_type,
        sort=sort,
    )
    request_id = str(uuid4())
    body = ResourceListEnvelope(
        data=ResourceListData(
            items=resource_public_items(session, _admin_user.id, items),
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


@resources_router.get("", response_model=ResourceListEnvelope)
def get_public_resources(
    session: Annotated[Session, Depends(get_db_session)],
    _current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    course_id: Annotated[int | None, Query(gt=0)] = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    resource_type: Literal["document", "video", "link"] | None = None,
    sort: Literal["newest", "title"] = "newest",
) -> JSONResponse:
    items, total = list_public_resources(
        session,
        page=page,
        page_size=page_size,
        query=q,
        course_id=course_id,
        category_id=category_id,
        resource_type=resource_type,
        sort=sort,
    )
    request_id = str(uuid4())
    body = ResourceListEnvelope(
        data=ResourceListData(
            items=resource_public_items(session, _current_user.id, items),
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


@resources_router.get("/{resource_id}", response_model=ResourceEnvelope)
def get_resource(
    resource_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        resource = get_visible_resource(
            session,
            actor=current_user,
            resource_id=resource_id,
        )
    except ResourceNotFoundError:
        return resource_error(404, "NOT_FOUND", "资源不存在", request_id)

    body = ResourceEnvelope(
        data=resource_public_items(session, current_user.id, [resource])[0],
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@resources_router.post("", response_model=ResourceEnvelope, status_code=201)
def post_resource(
    data: ResourceCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-ID": request_id}
    try:
        resource = create_resource(
            session,
            actor=current_user,
            data=data,
            request_id=request_id,
        )
    except (
        ResourcePermissionError,
        ResourceReferenceNotFoundError,
        ResourceReferenceInactiveError,
        ResourceMetadataError,
    ) as exc:
        status_code, code, message = {
            ResourcePermissionError: (403, "FORBIDDEN", "无权创建资源"),
            ResourceReferenceNotFoundError: (404, "NOT_FOUND", "课程或分类不存在"),
            ResourceReferenceInactiveError: (409, "REFERENCE_INACTIVE", "课程或分类已停用"),
            ResourceMetadataError: (422, "VALIDATION_ERROR", str(exc)),
        }[type(exc)]
        return JSONResponse(
            status_code=status_code,
            headers=headers,
            content={"error": {"code": code, "message": message}, "request_id": request_id},
        )

    body = ResourceEnvelope(
        data=resource_public_items(session, current_user.id, [resource])[0],
        request_id=request_id,
    )
    return JSONResponse(
        status_code=201,
        headers=headers,
        content=body.model_dump(mode="json"),
    )


@resources_router.patch("/{resource_id}", response_model=ResourceEnvelope)
def patch_resource(
    resource_id: Annotated[int, Path(gt=0)],
    data: ResourceUpdateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        resource = update_resource(
            session,
            actor=current_user,
            resource_id=resource_id,
            data=data,
            request_id=request_id,
        )
    except (ResourceNotFoundError, ResourceReferenceNotFoundError):
        return resource_error(404, "NOT_FOUND", "资源或关联对象不存在", request_id)
    except ResourcePermissionError:
        return resource_error(403, "FORBIDDEN", "无权修改此资源", request_id)
    except ResourceInvalidStateError:
        return resource_error(409, "INVALID_STATE", "当前状态不能编辑", request_id)
    except ResourceVersionConflictError:
        return resource_error(409, "VERSION_CONFLICT", "资源版本已变化，请刷新后重试", request_id)
    except ResourceReferenceInactiveError:
        return resource_error(409, "REFERENCE_INACTIVE", "课程或分类已停用", request_id)
    except ResourceMetadataError as exc:
        return resource_error(422, "VALIDATION_ERROR", str(exc), request_id)

    body = ResourceEnvelope(data=resource_public_items(session, current_user.id, [resource])[0], request_id=request_id)
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@resources_router.post("/{resource_id}/submit", response_model=ResourceEnvelope)
def post_resource_submit(
    resource_id: Annotated[int, Path(gt=0)],
    data: ResourceSubmitRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        resource = submit_resource(
            session,
            actor=current_user,
            resource_id=resource_id,
            expected_version=data.expected_version,
            request_id=request_id,
        )
    except (ResourceNotFoundError, SubmissionReferenceNotFoundError):
        return resource_error(404, "NOT_FOUND", "资源或关联对象不存在", request_id)
    except SubmissionForbiddenError:
        return resource_error(403, "FORBIDDEN", "无权提交此资源", request_id)
    except SubmissionStateError:
        return resource_error(409, "INVALID_STATE", "当前状态不能提交审核", request_id)
    except SubmissionVersionError:
        return resource_error(409, "VERSION_CONFLICT", "资源版本已变化，请刷新后重试", request_id)
    except SubmissionReferenceInactiveError:
        return resource_error(409, "REFERENCE_INACTIVE", "课程或分类已停用", request_id)
    except SubmissionMetadataError as exc:
        return resource_error(422, "VALIDATION_ERROR", str(exc), request_id)

    body = ResourceEnvelope(data=resource_public_items(session, current_user.id, [resource])[0], request_id=request_id)
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@resources_router.post("/{resource_id}/archive", response_model=ResourceEnvelope)
def post_resource_archive(
    resource_id: Annotated[int, Path(gt=0)],
    data: ResourceArchiveRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        resource = archive_resource(
            session,
            actor=current_user,
            resource_id=resource_id,
            expected_version=data.expected_version,
            reason=data.reason,
            request_id=request_id,
        )
    except ResourceNotFoundError:
        return resource_error(404, "NOT_FOUND", "资源不存在", request_id)
    except ResourcePermissionError:
        return resource_error(403, "FORBIDDEN", "无权归档此资源", request_id)
    except ResourceInvalidStateError:
        return resource_error(409, "INVALID_STATE", "资源已归档", request_id)
    except ResourceVersionConflictError:
        return resource_error(409, "VERSION_CONFLICT", "资源版本已变化，请刷新后重试", request_id)

    body = ResourceEnvelope(data=resource_public_items(session, current_user.id, [resource])[0], request_id=request_id)
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@resources_router.post("/{resource_id}/withdraw", response_model=ResourceEnvelope)
def post_resource_withdraw(
    resource_id: Annotated[int, Path(gt=0)],
    data: ResourceWithdrawRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        resource = withdraw_resource(
            session,
            actor=current_user,
            resource_id=resource_id,
            expected_version=data.expected_version,
            request_id=request_id,
        )
    except ResourceNotFoundError:
        return resource_error(404, "NOT_FOUND", "资源不存在", request_id)
    except ResourcePermissionError:
        return resource_error(403, "FORBIDDEN", "无权撤回此资源", request_id)
    except ResourceInvalidStateError:
        return resource_error(409, "INVALID_STATE", "当前状态不能撤回", request_id)
    except ResourceVersionConflictError:
        return resource_error(409, "VERSION_CONFLICT", "资源版本已变化，请刷新后重试", request_id)

    body = ResourceEnvelope(data=resource_public_items(session, current_user.id, [resource])[0], request_id=request_id)
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@resources_router.get("/{resource_id}/reviews", response_model=ReviewListEnvelope)
def get_resource_reviews(
    resource_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        items, total = list_resource_reviews(
            session,
            actor=current_user,
            resource_id=resource_id,
            page=page,
            page_size=page_size,
        )
    except ReviewNotFoundError:
        return resource_error(404, "NOT_FOUND", "资源不存在", request_id)

    body = ReviewListEnvelope(
        data=ReviewListData(
            items=[ReviewPublic.model_validate(item) for item in items],
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


@resources_router.post("/{resource_id}/reviews", response_model=ReviewEnvelope, status_code=201)
def post_resource_review(
    resource_id: Annotated[int, Path(gt=0)],
    data: ReviewCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        review, resource = review_resource(
            session,
            actor=current_user,
            resource_id=resource_id,
            data=data,
            request_id=request_id,
            dispatcher=request.app.state.review_dispatcher,
        )
    except ReviewNotFoundError:
        return resource_error(404, "NOT_FOUND", "资源不存在", request_id)
    except ReviewForbiddenError:
        return resource_error(403, "FORBIDDEN", "无权审核此资源", request_id)
    except SelfReviewForbiddenError:
        return resource_error(403, "SELF_REVIEW_FORBIDDEN", "不能审核自己的资源", request_id)
    except ReviewStateError:
        return resource_error(409, "INVALID_STATE", "资源当前不在待审状态", request_id)
    except ReviewVersionError:
        return resource_error(409, "VERSION_CONFLICT", "资源版本已变化，请刷新后重试", request_id)
    except ReviewReferenceInactiveError:
        return resource_error(409, "REFERENCE_INACTIVE", "课程或分类已停用", request_id)

    body = ReviewEnvelope(
        data=ReviewResult(
            review=ReviewPublic.model_validate(review),
            resource=resource_public_items(session, current_user.id, [resource])[0],
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=201,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )
