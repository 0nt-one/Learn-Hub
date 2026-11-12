from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.passwords import hash_password, verify_password
from app.models.course import Course
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserUpdateRequest

class UsernameExistsError(Exception):
    pass
# 注册用户（教师 学生）
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

def find_user_by_id(session: Session, user_id:int) -> User | None:
    return session.get(User, user_id)

# 是否有管理员：已有管理员时，不再允许用这个命令创建第二位
def admin_exists(session: Session) -> bool:
    statement = select(User.id).where(User.role == "admin").limit(1)
    return session.scalar(statement) is not None

class AdminAlreadyExistsError(Exception):
    pass

def create_initial_admin(session: Session, data: RegisterRequest) -> User:
    if admin_exists(session):
        raise AdminAlreadyExistsError
    admin = User(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        role="admin",
    )
    session.add(admin)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if str(exc.orig) == "UNIQUE constraint failed: users.username":
            raise UsernameExistsError from exc
        raise
    session.refresh(admin)
    return admin

def list_users(
        session: Session,
        *,
        page: int ,
        page_size: int,
        role: str | None,
        is_active: bool | None,
        query: str | None,
) -> tuple[list[User], int]:
    statement = select(User)
    if role is not None:
        statement = statement.where(User.role == role)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    if query:
        statement = statement.where(User.username.contains(query,autoescape=True))
    count_statement = select(func.count()).select_from(statement.subquery())

    total = session.scalar(count_statement) or 0

    offset = (page - 1) * page_size
    users = list(
                session.scalars(
                    statement.order_by(User.id.desc()).offset(offset).limit(page_size)
                ).all()
            )
    return users, total

# 管理员修改用户
class UserNotFoundError(Exception):
    pass

class AdminSelfChangeForbiddenError(Exception):
    pass

class CourseTransferRequiredError(Exception):
    pass

def update_user(
        session: Session,
        *,
        actor: User,
        target_id: int,
        data: UserUpdateRequest,
        request_id: str,
) -> User:
    target = session.get(User, target_id)
    if target is None:
        raise UserNotFoundError
    next_role = data.role if data.role is not None else target.role
    next_is_active = (data.is_active if data.is_active is not None else target.is_active)

    if actor.id == target.id and(
      next_role != "admin" or not next_is_active
    ):
        raise AdminSelfChangeForbiddenError
    removing_teacher_access = (
            target.role == "teacher"
            and (next_role != "teacher" or not next_is_active)
    )
    if removing_teacher_access:
        course_id = session.scalar(
            select(Course.id)
            .where(Course.teacher_id == target.id)
            .limit(1)
        )
        if course_id is not None:
            raise CourseTransferRequiredError

    old_role = target.role
    old_is_active = target.is_active
    target.role = next_role
    target.is_active = next_is_active
    session.add(
        OperationLog(
            actor_id=actor.id,
            action="user.update",
            target_type="user",
            target_id=target.id,
            request_id=request_id,
            summary=(
                f"role:{old_role}->{next_role};"
                f"is_active:{old_is_active}->{next_is_active}"
            ),
        )
    )
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(target)
    return target
