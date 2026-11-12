from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.v1.resources import resource_public_items
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.favorite import (
    FavoriteDeleteData,
    FavoriteDeleteEnvelope,
    FavoriteEnvelope,
    FavoriteListData,
    FavoriteListEnvelope,
    FavoriteListItem,
    FavoritePublic,
)
from app.services.favorites import add_favorite, list_my_favorites, remove_favorite
from app.services.resources import ResourceNotFoundError


favorites_router = APIRouter(prefix="/users/me/favorites")


@favorites_router.get("", response_model=FavoriteListEnvelope)
def get_my_favorites(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    favorites, visible, total = list_my_favorites(
        session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    public_resources = {
        resource.id: resource
        for resource in resource_public_items(session, current_user.id, list(visible.values()))
    }
    request_id = str(uuid4())
    body = FavoriteListEnvelope(
        data=FavoriteListData(
            items=[
                FavoriteListItem.model_validate(
                    {**favorite.__dict__, "resource": public_resources.get(favorite.resource_id)}
                )
                for favorite in favorites
            ],
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


@favorites_router.put("/{resource_id}", response_model=FavoriteEnvelope)
def put_favorite(
    resource_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        favorite = add_favorite(session, user_id=current_user.id, resource_id=resource_id)
    except ResourceNotFoundError:
        return JSONResponse(
            status_code=404,
            headers={"X-Request-ID": request_id},
            content={"error": {"code": "NOT_FOUND", "message": "资源不存在"}, "request_id": request_id},
        )
    body = FavoriteEnvelope(data=FavoritePublic.model_validate(favorite), request_id=request_id)
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )


@favorites_router.delete("/{resource_id}", response_model=FavoriteDeleteEnvelope)
def delete_favorite(
    resource_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    remove_favorite(session, user_id=current_user.id, resource_id=resource_id)
    request_id = str(uuid4())
    body = FavoriteDeleteEnvelope(
        data=FavoriteDeleteData(resource_id=resource_id),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers={"X-Request-ID": request_id},
        content=body.model_dump(mode="json"),
    )
