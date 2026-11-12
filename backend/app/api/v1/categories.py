from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import AuthFailure, get_current_user, require_admin
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryEnvelope,
    CategoryListData,
    CategoryListEnvelope,
    CategoryPublic,
    CategoryUpdateRequest,
)
from app.services.categories import (
    CategoryNameExistsError,
    CategoryNotFoundError,
    create_category,
    list_categories,
    update_category,
)


categories_router = APIRouter(prefix="/categories")


@categories_router.get("", response_model=CategoryListEnvelope)
def get_categories(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    is_active: bool | None = None,
) -> JSONResponse:
    if current_user.role != "admin":
        if is_active is False:
            raise AuthFailure(403, "FORBIDDEN", "无权查看停用分类")
        effective_is_active = True
    else:
        effective_is_active = is_active

    categories, total = list_categories(
        session,
        page=page,
        page_size=page_size,
        is_active=effective_is_active,
    )
    request_id = str(uuid4())
    body = CategoryListEnvelope(
        data=CategoryListData(
            items=[CategoryPublic.model_validate(item) for item in categories],
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


@categories_router.post("", response_model=CategoryEnvelope, status_code=201)
def post_category(
    data: CategoryCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-ID": request_id}

    try:
        category = create_category(
            session,
            actor=admin_user,
            data=data,
            request_id=request_id,
        )
    except CategoryNameExistsError:
        return JSONResponse(
            status_code=409,
            headers=headers,
            content={
                "error": {"code": "CATEGORY_NAME_EXISTS", "message": "分类名称已存在"},
                "request_id": request_id,
            },
        )

    body = CategoryEnvelope(
        data=CategoryPublic.model_validate(category),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=201,
        headers=headers,
        content=body.model_dump(mode="json"),
    )


@categories_router.patch("/{category_id}", response_model=CategoryEnvelope)
def patch_category(
    category_id: Annotated[int, Path(gt=0)],
    data: CategoryUpdateRequest,
    session: Annotated[Session, Depends(get_db_session)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-ID": request_id}
    try:
        category = update_category(
            session,
            actor=admin_user,
            category_id=category_id,
            data=data,
            request_id=request_id,
        )
    except CategoryNotFoundError:
        return JSONResponse(
            status_code=404,
            headers=headers,
            content={
                "error": {"code": "NOT_FOUND", "message": "分类不存在"},
                "request_id": request_id,
            },
        )
    except CategoryNameExistsError:
        return JSONResponse(
            status_code=409,
            headers=headers,
            content={
                "error": {"code": "CATEGORY_NAME_EXISTS", "message": "分类名称已存在"},
                "request_id": request_id,
            },
        )

    body = CategoryEnvelope(
        data=CategoryPublic.model_validate(category),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers=headers,
        content=body.model_dump(mode="json"),
    )
