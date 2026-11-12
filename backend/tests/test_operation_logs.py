import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.engine import create_db_engine
from app.db.init_db import initialize_database
from app.main import create_app
from app.models.operation_log import OperationLog
from app.models.user import User


def test_operation_logs_are_admin_only_and_filter_by_time(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{(tmp_path / 'logs.db').as_posix()}",
        cors_origins=[],
        jwt_secret_key="test-only-secret-key-for-operation-logs-1234",
    )
    initialize_database(settings)
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            admin = User(username="admin", display_name="Admin", password_hash="test", role="admin")
            student = User(username="student", display_name="Student", password_hash="test", role="student")
            session.add_all([admin, student])
            session.flush()
            admin_id, student_id = admin.id, student.id
            session.add_all(
                [
                    OperationLog(
                        actor_id=student_id,
                        action="resource.create",
                        target_type="resource",
                        target_id=1,
                        request_id=str(uuid4()),
                        summary="创建资源",
                        created_at=datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc),
                    ),
                    OperationLog(
                        actor_id=admin_id,
                        action="resource.archive",
                        target_type="resource",
                        target_id=1,
                        request_id=str(uuid4()),
                        summary="违规资源",
                        created_at=datetime(2026, 11, 11, 8, 0, tzinfo=timezone.utc),
                    ),
                ]
            )
            session.commit()
    finally:
        engine.dispose()

    async def exercise() -> None:
        transport = httpx.ASGITransport(app=create_app(settings))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin_token, _ = create_access_token(admin_id, settings)
            student_token, _ = create_access_token(student_id, settings)
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            student_headers = {"Authorization": f"Bearer {student_token}"}
            denied = await client.get("/api/v1/operation-logs", headers=student_headers)
            listed = await client.get("/api/v1/operation-logs?page_size=1", headers=admin_headers)
            filtered = await client.get(
                "/api/v1/operation-logs",
                headers=admin_headers,
                params={
                    "actor_id": student_id,
                    "action": "resource.create",
                    "target_type": "resource",
                    "target_id": 1,
                    "created_from": "2026-11-10T15:00:00+08:00",
                    "created_to": "2026-11-11T00:00:00+08:00",
                },
            )
            naive_time = await client.get(
                "/api/v1/operation-logs?created_from=2026-11-10T08:00:00",
                headers=admin_headers,
            )
            reversed_time = await client.get(
                "/api/v1/operation-logs?created_from=2026-11-12T00:00:00Z&created_to=2026-11-11T00:00:00Z",
                headers=admin_headers,
            )
            assert denied.status_code == 403
            assert listed.status_code == 200
            assert listed.json()["data"]["total"] == 2
            assert listed.json()["data"]["items"][0]["action"] == "resource.archive"
            assert filtered.status_code == 200
            assert filtered.json()["data"]["total"] == 1
            assert filtered.json()["data"]["items"][0]["actor_id"] == student_id
            assert naive_time.status_code == 422
            assert reversed_time.status_code == 422

    asyncio.run(exercise())
