from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.passwords import verify_password
from app.db.engine import create_db_engine
from app.db.init_db import initialize_database
from app.models.course import Course
from app.models.operation_log import OperationLog
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserUpdateRequest
from app.services.auth import (
    AdminAlreadyExistsError,
    AdminSelfChangeForbiddenError,
    CourseTransferRequiredError,
    admin_exists,
    create_initial_admin,
    list_users,
    register_user,
    update_user,
)


def test_bootstrap_creates_only_first_admin_with_hashed_password(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{(tmp_path / 'admin.db').as_posix()}",
        jwt_secret_key="test-only-secret-key-for-admin-1234",
    )
    initialize_database(settings)
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            assert not admin_exists(session)
            data = RegisterRequest(
                username="first_admin",
                password="example-pass-123",
                display_name="First Admin",
            )
            admin = create_initial_admin(session, data)
            assert admin.role == "admin"
            assert admin_exists(session)
            assert admin.password_hash != data.password
            assert verify_password(data.password, admin.password_hash)

            with pytest.raises(AdminAlreadyExistsError):
                create_initial_admin(session, data)
    finally:
        engine.dispose()


def test_user_update_guards_admin_and_teacher_and_writes_audit_log(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{(tmp_path / 'updates.db').as_posix()}",
        jwt_secret_key="test-only-secret-key-for-admin-1234",
    )
    initialize_database(settings)
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            admin = create_initial_admin(
                session,
                RegisterRequest(
                    username="manager",
                    password="example-pass-123",
                    display_name="Manager",
                ),
            )
            student = register_user(
                session,
                RegisterRequest(
                    username="alice",
                    password="example-pass-123",
                    display_name="Alice",
                ),
            )
            teacher = register_user(
                session,
                RegisterRequest(
                    username="teacher",
                    password="example-pass-123",
                    display_name="Teacher",
                ),
            )
            teacher.role = "teacher"
            session.add(Course(code="MATH1", title="Math", teacher_id=teacher.id))
            session.commit()

            request_id = str(uuid4())
            changed = update_user(
                session,
                actor=admin,
                target_id=student.id,
                data=UserUpdateRequest(role="teacher"),
                request_id=request_id,
            )
            assert changed.role == "teacher"
            log = session.scalar(
                select(OperationLog).where(OperationLog.request_id == request_id)
            )
            assert log is not None
            assert (log.actor_id, log.target_id, log.action) == (
                admin.id,
                student.id,
                "user.update",
            )

            with pytest.raises(AdminSelfChangeForbiddenError):
                update_user(
                    session,
                    actor=admin,
                    target_id=admin.id,
                    data=UserUpdateRequest(is_active=False),
                    request_id=str(uuid4()),
                )
            with pytest.raises(CourseTransferRequiredError):
                update_user(
                    session,
                    actor=admin,
                    target_id=teacher.id,
                    data=UserUpdateRequest(role="student"),
                    request_id=str(uuid4()),
                )
            assert teacher.role == "teacher"
            assert session.query(OperationLog).count() == 1
    finally:
        engine.dispose()


def test_user_list_applies_filters_before_pagination(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{(tmp_path / 'users.db').as_posix()}",
        jwt_secret_key="test-only-secret-key-for-admin-1234",
    )
    initialize_database(settings)
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            for username in ("alice", "bob", "albert"):
                register_user(
                    session,
                    RegisterRequest(
                        username=username,
                        password="example-pass-123",
                        display_name=username,
                    ),
                )

            users, total = list_users(
                session,
                page=1,
                page_size=1,
                role="student",
                is_active=True,
                query="al",
            )
            assert total == 2
            assert [user.username for user in users] == ["albert"]

            next_page, next_total = list_users(
                session,
                page=2,
                page_size=1,
                role="student",
                is_active=True,
                query="al",
            )
            assert next_total == 2
            assert [user.username for user in next_page] == ["alice"]

            literal_wildcard, wildcard_total = list_users(
                session,
                page=1,
                page_size=20,
                role=None,
                is_active=None,
                query="%",
            )
            assert literal_wildcard == []
            assert wildcard_total == 0
    finally:
        engine.dispose()
