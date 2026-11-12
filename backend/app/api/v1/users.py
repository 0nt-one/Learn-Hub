from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.user import (
    UserEnvelope,
    UserListData,
    UserListEnvelope,
    UserPublic,
    UserUpdateRequest,
)
from app.services.auth import (
    AdminSelfChangeForbiddenError,
    CourseTransferRequiredError,
    UserNotFoundError,
    list_users,
    update_user,
)

users_router = APIRouter(prefix="/users")

@users_router.get("/me", response_model=UserEnvelope)
def get_my_profile(
        current_user: Annotated[User, Depends(get_current_user)],

) -> JSONResponse:
    request_id = str(uuid4())
    body = UserEnvelope(
        data=UserPublic.model_validate(current_user),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-Id": request_id},
        content=body.model_dump(mode="json"),
    )

@users_router.get("", response_model=UserListEnvelope)
def get_users(
        session: Annotated[Session, Depends(get_db_session)],
        admin_user: Annotated[User,Depends(require_admin)],
        page: Annotated[int,Query(ge=1)] = 1,
        page_size: Annotated[int,Query(ge=1,le=100)] = 20,
        role: Literal["student", "teacher", "admin"] | None = None,
        is_active: bool | None = None,
        q: Annotated[str | None,Query(min_length=1,max_length=100)] = None,

) -> JSONResponse:
    users,total = list_users(
        session,
        page=page,
        page_size=page_size,
        role=role,
        is_active=is_active,
        query=q,

    )
    request_id = str(uuid4())
    body = UserListEnvelope(
        data=UserListData(
            items=[UserPublic.model_validate(user) for user in users],
            total=total,
            page=page,
            page_size=page_size,
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-Id": request_id},
        content=body.model_dump(mode="json"),
    )

@users_router.patch("/{target_id}", response_model=UserEnvelope)
def patch_user(
        target_id:Annotated[int,Path(gt=0)],
        data:UserUpdateRequest,
        session: Annotated[Session,Depends(get_db_session)],
        admin_user:Annotated[User,Depends(require_admin)],
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-Id": request_id}

    try:
        updated_user = update_user(
            session,
            actor=admin_user,
            target_id=target_id,
            data=data,
            request_id=request_id,
        )
    except UserNotFoundError:
        status_code, code, message = 404, "NOT_FOUND", "用户不存在"
    except AdminSelfChangeForbiddenError:
        status_code, code, message = (
            409, "ADMIN_SELF_CHANGE_FORBIDDEN", "不能停用或降级自己"
        )
    except CourseTransferRequiredError:
        status_code, code, message = (
            409, "COURSE_TRANSFER_REQUIRED", "请先转移教师负责的课程"
        )
    else:
        body = UserEnvelope(
            data=UserPublic.model_validate(updated_user),
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
            "error":{"code":code,"message":message},
            "request_id":request_id,
        },
    )
