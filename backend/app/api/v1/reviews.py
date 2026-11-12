from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.v1.resources import resource_public_items, resource_error
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.resource import ResourceListData, ResourceListEnvelope
from app.services.reviews import ReviewForbiddenError, list_pending_reviews


reviews_router = APIRouter(prefix="/reviews")


@reviews_router.get("/pending", response_model=ResourceListEnvelope)
def get_pending_reviews(
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    course_id: Annotated[int | None, Query(gt=0)] = None,
) -> JSONResponse:
    request_id = str(uuid4())
    try:
        items, total = list_pending_reviews(
            session,
            actor=current_user,
            page=page,
            page_size=page_size,
            course_id=course_id,
        )
    except ReviewForbiddenError:
        return resource_error(403, "FORBIDDEN", "无权查看待审核资源", request_id)

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
