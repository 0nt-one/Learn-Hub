import asyncio
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.engine import create_db_engine
from app.db.init_db import initialize_database
from app.main import create_app
from app.models.category import Category
from app.models.course import Course
from app.models.learning_record import LearningRecord
from app.models.resource import Resource
from app.models.user import User


def test_learning_history_keeps_title_but_hides_unavailable_url(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{(tmp_path / 'learning.db').as_posix()}",
        cors_origins=[],
        jwt_secret_key="test-only-secret-key-for-learning-records-1234",
    )
    initialize_database(settings)
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            owner = User(username="owner", display_name="Owner", password_hash="test", role="student")
            teacher = User(username="teacher", display_name="Teacher", password_hash="test", role="teacher")
            other = User(username="other", display_name="Other", password_hash="test", role="student")
            session.add_all([owner, teacher, other])
            session.flush()
            course = Course(code="LEARN-1", title="Learning Course", teacher_id=teacher.id)
            category = Category(name="Learning Category")
            session.add_all([course, category])
            session.flush()
            resource = Resource(
                title="Learning Resource",
                resource_type="link",
                url="https://example.org/learn",
                course_id=course.id,
                category_id=category.id,
                owner_id=owner.id,
                status="approved",
            )
            session.add(resource)
            session.commit()
            owner_id, other_id, resource_id = owner.id, other.id, resource.id

        async def exercise() -> None:
            transport = httpx.ASGITransport(app=create_app(settings))
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                owner_token, _ = create_access_token(owner_id, settings)
                other_token, _ = create_access_token(other_id, settings)
                headers = {"Authorization": f"Bearer {owner_token}"}
                other_headers = {"Authorization": f"Bearer {other_token}"}
                path = f"/api/v1/users/me/learning-records/{resource_id}"
                first = await client.put(path, headers=headers, json={"progress": 40})
                updated = await client.put(path, headers=headers, json={"progress": 100})
                listed = await client.get("/api/v1/users/me/learning-records", headers=headers)
                other_list = await client.get(
                    "/api/v1/users/me/learning-records", headers=other_headers
                )
                invalid = await client.put(path, headers=headers, json={"progress": 101})
                assert first.status_code == updated.status_code == 200
                assert first.json()["data"]["id"] == updated.json()["data"]["id"]
                assert updated.json()["data"]["progress"] == 100
                assert listed.json()["data"]["total"] == 1
                assert listed.json()["data"]["items"][0]["resource"]["url"] == "https://example.org/learn"
                assert other_list.json()["data"]["total"] == 0
                assert invalid.status_code == 422

                with Session(engine) as session:
                    stored = session.get(Resource, resource_id)
                    assert stored is not None
                    stored.status = "archived"
                    session.commit()

                history = await client.get("/api/v1/users/me/learning-records", headers=headers)
                hidden_write = await client.put(path, headers=headers, json={"progress": 50})
                item = history.json()["data"]["items"][0]
                assert item["resource"]["title"] == "Learning Resource"
                assert item["resource"]["course_title"] == "Learning Course"
                assert item["resource"]["is_available"] is False
                assert item["resource"]["url"] is None
                assert hidden_write.status_code == 404

        asyncio.run(exercise())
        with Session(engine) as session:
            assert len(session.scalars(select(LearningRecord)).all()) == 1
    finally:
        engine.dispose()
