from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.tokens import InvalidAccessTokenError, decode_access_token
from app.db.session import get_db_session
from app.models.user import User
from app.services.auth import find_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)

class AuthFailure(Exception):
    def __init__(self, status_code: int, code: str, message: str ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message

def get_current_user(
    credentials:Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme)
        ],
    session:Annotated[Session, Depends(get_db_session)],
    request:Request,
) -> User:
    if credentials is None:
        raise AuthFailure(401, "AUTH_REQUIRED","请先登录")
    settings: Settings = request.app.state.settings
    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except InvalidAccessTokenError as exc:
        raise AuthFailure(401,"INVALID_TOKEN","登录凭证无效或已过期") from exc
    user = find_user_by_id(session, user_id)
    if user is None:
        raise AuthFailure(401,"INVALID_TOKEN","登录凭证无效或已过期")
    if not user.is_active:
        raise AuthFailure(403, "ACCOUNT_DISABLED", "账户已停用")
    return user

def require_admin(
        current_user:Annotated[User,Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise AuthFailure(403,"FORBIDDEN", "无权执行此操作")
    return current_user