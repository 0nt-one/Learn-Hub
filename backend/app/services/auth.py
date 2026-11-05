from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.passwords import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest

class UsernameExistsError(Exception):
    pass

def register_user(session: Session,data: RegisterRequest) -> User:
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        role="student",
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if str(exc.orig) == "UNIQUE constraint failed: users.username":
            raise UsernameExistsError from exc
        raise
    session.refresh(user)
    return user

def authenticate_user(session: Session, username:str, password:str) -> User | None:
    statement = select(User).where(User.username == username)
    user = session.scalar(statement)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None

    return user

