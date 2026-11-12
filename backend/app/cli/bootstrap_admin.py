"""Create the first administrator through a local interactive command."""

from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.engine import create_db_engine
from app.db.health import database_is_ready
from app.schemas.auth import RegisterRequest
from app.services.auth import (
    AdminAlreadyExistsError,
    UsernameExistsError,
    admin_exists,
    create_initial_admin,
)


def main() -> int:
    settings = get_settings()
    if not database_is_ready(settings):
        print("数据库尚未初始化，请先运行 python -m app.db.init_db")
        return 1

    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            if admin_exists(session):
                print("管理员已存在；此命令只能创建首位管理员")
                return 1

            try:
                username = input("管理员用户名：")
                display_name = input("显示名称：")
                password = getpass("密码：")
                confirmation = getpass("再次输入密码：")
            except (EOFError, KeyboardInterrupt):
                print("\n已取消")
                return 1

            if password != confirmation:
                print("两次密码不一致")
                return 1

            try:
                data = RegisterRequest(
                    username=username,
                    password=password,
                    display_name=display_name,
                )
            except ValidationError:
                print("输入不符合要求：用户名 3–32 位，密码 12–128 位，显示名 1–64 位")
                return 1

            try:
                admin = create_initial_admin(session, data)
            except AdminAlreadyExistsError:
                print("管理员已存在；此命令只能创建首位管理员")
                return 1
            except UsernameExistsError:
                print("用户名已存在")
                return 1

            print(f"已创建管理员：{admin.username}（ID {admin.id}）")
            return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
