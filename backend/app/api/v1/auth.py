from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.auth import RegisterRequest,LoginRequest, TokenEnvelope, TokenPublic
from app.schemas.user import UserEnvelope, UserPublic
from app.services.auth import UsernameExistsError, register_user, authenticate_user
from app.core.config import Settings
from app.core.tokens import create_access_token

auth_router = APIRouter(prefix="/auth")

@auth_router.post("/register", response_model=UserEnvelope, status_code=201)
def register(
    data: RegisterRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-ID": request_id}

    try:
        user = register_user(session, data)
    except UsernameExistsError:
        return JSONResponse(
            status_code=409,
            headers=headers,
            content={
                "error": {"code": "USERNAME_EXISTS", "message": "用户名已存在"},
                "request_id": request_id,
            },
        )
    body = UserEnvelope(
        data=UserPublic.model_validate(user),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=201,
        headers=headers,
        content=body.model_dump(mode="json"),
    )

@auth_router.post("/login", response_model=TokenEnvelope, status_code=200)
def login(
        data: LoginRequest,
        session: Annotated[Session, Depends(get_db_session)],
        request: Request,
) -> JSONResponse:
    request_id = str(uuid4())
    headers = {"X-Request-ID": request_id}

    user = authenticate_user(session, data.username, data.password)
    if user is None:
        return JSONResponse(
            status_code=401,
            headers={**headers, "WWW-Authenticate": "Bearer"},
            content={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message":"用户名或密码错误",
                },
                "request_id": request_id,
            },
        )
    settings: Settings = request.app.state.settings
    access_token, expires_in = create_access_token(user.id, settings)
    body = TokenEnvelope(
        data=TokenPublic(
            access_token=access_token,
            expires_in=expires_in,
            user=UserPublic.model_validate(user),
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=200,
        headers=headers,
        content=body.model_dump(mode="json"),
    )