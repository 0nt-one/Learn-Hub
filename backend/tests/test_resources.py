import asyncio
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.engine import create_db_engine
from app.db.init_db import initialize_database
from app.main import create_app
from app.models.category import Category
from app.models.course import Course
from app.models.favorite import Favorite
from app.models.operation_log import OperationLog
from app.models.notification import Notification
from app.models.resource import Resource
from app.models.review_record import ReviewRecord
from app.models.user import User
from app.services.resources import ResourcePermissionError, archive_resource


def test_create_resource_uses_video_validation_and_audits(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{(tmp_path / 'resources.db').as_posix()}",
        cors_origins=[],
        jwt_secret_key="test-only-secret-key-for-resources-1234",
    )
    initialize_database(settings)

    async def exercise() -> tuple[httpx.Response, ...]:
        transport = httpx.ASGITransport(app=create_app(settings))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            registered = await client.post(
                "/api/v1/auth/register",
                json={"username": "student", "password": "example-pass-123", "display_name": "Student"},
            )
            assert registered.status_code == 201
            user_id = registered.json()["data"]["id"]
            other_registered = await client.post(
                "/api/v1/auth/register",
                json={"username": "other", "password": "example-pass-123", "display_name": "Other"},
            )
            assert other_registered.status_code == 201
            other_token, _ = create_access_token(other_registered.json()["data"]["id"], settings)
            other_headers = {"Authorization": f"Bearer {other_token}"}

            engine = create_db_engine(settings)
            try:
                with Session(engine) as session:
                    teacher = User(
                        username="teacher",
                        display_name="Teacher",
                        password_hash="not-used-in-this-test",
                        role="teacher",
                    )
                    session.add(teacher)
                    session.flush()
                    course = Course(code="TEST-101", title="Test", teacher_id=teacher.id)
                    category = Category(name="Notes")
                    session.add_all([course, category])
                    session.commit()
                    course_id, category_id = course.id, category.id
                    teacher_id = teacher.id
            finally:
                engine.dispose()

            logged_in = await client.post(
                "/api/v1/auth/login",
                json={"username": "student", "password": "example-pass-123"},
            )
            assert logged_in.status_code == 200
            headers = {"Authorization": f"Bearer {logged_in.json()['data']['access_token']}"}
            payload = {
                "title": "Video lesson",
                "resource_type": "video",
                "url": "https://example.org/video",
                "duration_seconds": 120,
                "course_id": course_id,
                "category_id": category_id,
            }
            created = await client.post("/api/v1/resources", headers=headers, json=payload)
            resource_path = f"/api/v1/resources/{created.json()['data']['id']}"
            owner_draft = await client.get(resource_path, headers=headers)
            other_draft = await client.get(resource_path, headers=other_headers)
            assert owner_draft.status_code == 200
            assert other_draft.status_code == 404
            bad_edit = await client.patch(
                resource_path,
                headers=headers,
                json={"expected_version": 1, "resource_type": "link"},
            )
            edited = await client.patch(
                resource_path,
                headers=headers,
                json={"expected_version": 1, "title": "Updated lesson"},
            )
            stale_edit = await client.patch(
                resource_path,
                headers=headers,
                json={"expected_version": 1, "title": "Stale title"},
            )
            invalid = await client.post(
                "/api/v1/resources",
                headers=headers,
                json={**payload, "page_count": 3},
            )
            mine = await client.get("/api/v1/resources/mine", headers=headers)
            pending = await client.get("/api/v1/resources/mine?status=pending", headers=headers)
            submit_path = f"/api/v1/resources/{created.json()['data']['id']}/submit"
            stale = await client.post(submit_path, headers=headers, json={"expected_version": 1})
            submitted = await client.post(submit_path, headers=headers, json={"expected_version": 2})
            public_before_review = await client.get("/api/v1/resources", headers=headers)
            repeated = await client.post(submit_path, headers=headers, json={"expected_version": 2})
            pending_edit = await client.patch(
                resource_path,
                headers=headers,
                json={"expected_version": 3, "title": "Cannot edit pending"},
            )
            self_review = await client.post(
                f"{resource_path}/reviews",
                headers=headers,
                json={"expected_version": 3, "decision": "approved"},
            )
            teacher_token, _ = create_access_token(teacher_id, settings)
            teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
            teacher_pending_detail = await client.get(resource_path, headers=teacher_headers)
            assert teacher_pending_detail.status_code == 200
            teacher_queue = await client.get("/api/v1/reviews/pending", headers=teacher_headers)
            student_queue = await client.get("/api/v1/reviews/pending", headers=headers)
            other_course_queue = await client.get(
                "/api/v1/reviews/pending?course_id=999", headers=teacher_headers
            )
            reviewed = await client.post(
                f"{resource_path}/reviews",
                headers=teacher_headers,
                json={"expected_version": 3, "decision": "approved"},
            )
            history_path = f"{resource_path}/reviews"
            owner_history = await client.get(history_path, headers=headers)
            teacher_history = await client.get(history_path, headers=teacher_headers)
            other_history = await client.get(history_path, headers=other_headers)
            second_page = await client.get(f"{history_path}?page=2&page_size=1", headers=headers)
            assert owner_history.status_code == 200
            assert owner_history.json()["data"]["total"] == 1
            assert owner_history.json()["data"]["items"][0]["id"] == reviewed.json()["data"]["review"]["id"]
            assert teacher_history.status_code == 200
            assert other_history.status_code == 404
            assert second_page.json()["data"]["items"] == []
            owner_notifications = await client.get(
                "/api/v1/users/me/notifications?unread_only=true", headers=headers
            )
            other_notifications = await client.get(
                "/api/v1/users/me/notifications", headers=other_headers
            )
            assert owner_notifications.status_code == 200
            assert owner_notifications.json()["data"]["total"] == 1
            assert other_notifications.json()["data"]["total"] == 0
            notification_id = owner_notifications.json()["data"]["items"][0]["id"]
            read_path = f"/api/v1/users/me/notifications/{notification_id}/read"
            other_read = await client.patch(read_path, headers=other_headers)
            first_read = await client.patch(read_path, headers=headers)
            second_read = await client.patch(read_path, headers=headers)
            unread_after_read = await client.get(
                "/api/v1/users/me/notifications?unread_only=true", headers=headers
            )
            assert other_read.status_code == 404
            assert first_read.status_code == 200
            assert first_read.json()["data"]["read_at"] is not None
            assert second_read.json()["data"]["read_at"] == first_read.json()["data"]["read_at"]
            assert unread_after_read.json()["data"]["total"] == 0
            public_after_review = await client.get(
                "/api/v1/resources?q=Updated&resource_type=video&sort=title",
                headers=headers,
            )
            other_before_favorite = await client.get(resource_path, headers=other_headers)
            assert other_before_favorite.json()["data"]["is_favorited"] is False
            favorite_path = f"/api/v1/users/me/favorites/{created.json()['data']['id']}"
            first_favorite = await client.put(favorite_path, headers=other_headers)
            repeated_favorite = await client.put(favorite_path, headers=other_headers)
            owner_favorite = await client.put(favorite_path, headers=headers)
            assert first_favorite.status_code == 200
            assert repeated_favorite.status_code == 200
            assert owner_favorite.status_code == 200
            assert first_favorite.json()["data"]["id"] == repeated_favorite.json()["data"]["id"]
            favorite_list = await client.get("/api/v1/users/me/favorites", headers=other_headers)
            assert favorite_list.status_code == 200
            assert favorite_list.json()["data"]["total"] == 1
            assert favorite_list.json()["data"]["items"][0]["resource"]["title"] == "Updated lesson"
            assert favorite_list.json()["data"]["items"][0]["resource"]["is_favorited"] is True
            other_approved = await client.get(resource_path, headers=other_headers)
            assert other_approved.status_code == 200
            assert other_approved.json()["data"]["is_favorited"] is True
            public_wrong_course = await client.get(
                "/api/v1/resources?course_id=999", headers=headers
            )
            repeated_review = await client.post(
                f"{resource_path}/reviews",
                headers=teacher_headers,
                json={"expected_version": 3, "decision": "approved"},
            )
            queue_after_review = await client.get("/api/v1/reviews/pending", headers=teacher_headers)
            withdraw_path = f"{resource_path}/withdraw"
            stale_withdraw = await client.post(
                withdraw_path, headers=headers, json={"expected_version": 3}
            )
            other_withdraw = await client.post(
                withdraw_path, headers=other_headers, json={"expected_version": 4}
            )
            withdrawn = await client.post(
                withdraw_path, headers=headers, json={"expected_version": 4}
            )
            repeated_withdraw = await client.post(
                withdraw_path, headers=headers, json={"expected_version": 5}
            )
            public_after_withdraw = await client.get("/api/v1/resources", headers=headers)
            assert stale_withdraw.status_code == 409
            assert stale_withdraw.json()["error"]["code"] == "VERSION_CONFLICT"
            assert other_withdraw.status_code == 403
            assert withdrawn.status_code == 200
            assert withdrawn.json()["data"]["status"] == "draft"
            assert withdrawn.json()["data"]["version_id"] == 5
            assert repeated_withdraw.status_code == 409
            assert public_after_withdraw.json()["data"]["total"] == 0
            owner_draft_after_withdraw = await client.get(resource_path, headers=headers)
            assert owner_draft_after_withdraw.json()["data"]["is_favorited"] is True
            hidden_favorite_list = await client.get(
                "/api/v1/users/me/favorites", headers=other_headers
            )
            assert hidden_favorite_list.json()["data"]["total"] == 1
            assert hidden_favorite_list.json()["data"]["items"][0]["resource"] is None
            hidden_favorite = await client.put(favorite_path, headers=other_headers)
            removed_favorite = await client.delete(favorite_path, headers=other_headers)
            repeated_remove = await client.delete(favorite_path, headers=other_headers)
            owner_remove = await client.delete(favorite_path, headers=headers)
            owner_after_remove = await client.get(resource_path, headers=headers)
            assert hidden_favorite.status_code == 404
            assert removed_favorite.status_code == 200
            assert repeated_remove.status_code == 200
            assert owner_remove.status_code == 200
            assert owner_after_remove.json()["data"]["is_favorited"] is False
            archive_path = f"{resource_path}/archive"
            blank_archive = await client.post(
                archive_path, headers=headers, json={"expected_version": 5, "reason": "   "}
            )
            other_archive = await client.post(
                archive_path, headers=other_headers, json={"expected_version": 5, "reason": "Other"}
            )
            stale_archive = await client.post(
                archive_path, headers=headers, json={"expected_version": 4, "reason": "Old"}
            )
            archived = await client.post(
                archive_path, headers=headers, json={"expected_version": 5, "reason": "  内容过时  "}
            )
            repeated_archive = await client.post(
                archive_path, headers=headers, json={"expected_version": 6, "reason": "Again"}
            )
            assert blank_archive.status_code == 422
            assert other_archive.status_code == 403
            assert stale_archive.status_code == 409
            assert archived.status_code == 200
            assert archived.json()["data"]["status"] == "archived"
            assert archived.json()["data"]["version_id"] == 6
            assert repeated_archive.status_code == 409
            engine = create_db_engine(settings)
            try:
                with Session(engine) as session:
                    category = session.get(Category, category_id)
                    assert category is not None
                    category.is_active = False
                    session.commit()
            finally:
                engine.dispose()
            public_after_disable = await client.get("/api/v1/resources", headers=headers)
            other_after_disable = await client.get(resource_path, headers=other_headers)
            owner_after_disable = await client.get(resource_path, headers=headers)
            assert other_after_disable.status_code == 404
            assert owner_after_disable.status_code == 200
            assert created.json()["data"]["owner_id"] == user_id
            return created, bad_edit, edited, stale_edit, invalid, mine, pending, stale, submitted, public_before_review, repeated, pending_edit, self_review, teacher_queue, student_queue, other_course_queue, reviewed, public_after_review, public_wrong_course, repeated_review, queue_after_review, public_after_disable

    created, bad_edit, edited, stale_edit, invalid, mine, pending, stale, submitted, public_before_review, repeated, pending_edit, self_review, teacher_queue, student_queue, other_course_queue, reviewed, public_after_review, public_wrong_course, repeated_review, queue_after_review, public_after_disable = asyncio.run(exercise())
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "draft"
    assert created.json()["data"]["course_title"] == "Test"
    assert created.json()["data"]["category_name"] == "Notes"
    assert created.json()["data"]["course_teacher_id"] == reviewed.json()["data"]["review"]["reviewer_id"]
    assert created.json()["data"]["course_teacher_display_name"] == "Teacher"
    assert created.json()["data"]["owner_display_name"] == "Student"
    assert bad_edit.status_code == 422
    assert edited.status_code == 200
    assert edited.json()["data"]["title"] == "Updated lesson"
    assert edited.json()["data"]["version_id"] == 2
    assert stale_edit.status_code == 409
    assert stale_edit.json()["error"]["code"] == "VERSION_CONFLICT"
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert mine.status_code == 200
    assert mine.json()["data"]["total"] == 1
    assert mine.json()["data"]["items"][0]["id"] == created.json()["data"]["id"]
    assert mine.json()["data"]["items"][0]["course_title"] == "Test"
    assert mine.json()["data"]["items"][0]["course_teacher_display_name"] == "Teacher"
    assert pending.status_code == 200
    assert pending.json()["data"]["total"] == 0
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "pending"
    assert submitted.json()["data"]["version_id"] == 3
    assert public_before_review.json()["data"]["total"] == 0
    assert repeated.status_code == 409
    assert repeated.json()["error"]["code"] == "INVALID_STATE"
    assert pending_edit.status_code == 409
    assert pending_edit.json()["error"]["code"] == "INVALID_STATE"
    assert self_review.status_code == 403
    assert self_review.json()["error"]["code"] == "FORBIDDEN"
    assert teacher_queue.status_code == 200
    assert teacher_queue.json()["data"]["total"] == 1
    assert teacher_queue.json()["data"]["items"][0]["id"] == created.json()["data"]["id"]
    assert student_queue.status_code == 403
    assert other_course_queue.json()["data"]["total"] == 0
    assert reviewed.status_code == 201
    assert reviewed.json()["data"]["review"]["resource_version"] == 3
    assert reviewed.json()["data"]["resource"]["status"] == "approved"
    assert reviewed.json()["data"]["resource"]["version_id"] == 4
    assert public_after_review.status_code == 200
    assert public_after_review.json()["data"]["total"] == 1
    assert public_after_review.json()["data"]["items"][0]["id"] == created.json()["data"]["id"]
    assert public_after_review.json()["data"]["items"][0]["owner_display_name"] == "Student"
    assert public_wrong_course.json()["data"]["total"] == 0
    assert public_after_disable.json()["data"]["total"] == 0
    assert repeated_review.status_code == 409
    assert queue_after_review.json()["data"]["total"] == 0

    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            assert len(session.scalars(select(Resource)).all()) == 1
            logs = session.scalars(select(OperationLog).where(OperationLog.action == "resource.create")).all()
            assert len(logs) == 1
            assert logs[0].request_id == created.json()["request_id"]
            submit_logs = session.scalars(
                select(OperationLog).where(OperationLog.action == "resource.submit")
            ).all()
            assert len(submit_logs) == 1
            assert submit_logs[0].request_id == submitted.json()["request_id"]
            update_logs = session.scalars(
                select(OperationLog).where(OperationLog.action == "resource.update")
            ).all()
            assert len(update_logs) == 1
            assert len(session.scalars(select(ReviewRecord)).all()) == 1
            notifications = session.scalars(select(Notification)).all()
            assert len(notifications) == 1
            assert notifications[0].review_record_id == reviewed.json()["data"]["review"]["id"]
            review_logs = session.scalars(
                select(OperationLog).where(OperationLog.action == "resource.review")
            ).all()
            assert len(review_logs) == 1
            withdraw_logs = session.scalars(
                select(OperationLog).where(OperationLog.action == "resource.withdraw")
            ).all()
            assert len(withdraw_logs) == 1
            archive_logs = session.scalars(
                select(OperationLog).where(OperationLog.action == "resource.archive")
            ).all()
            assert len(archive_logs) == 1
            assert archive_logs[0].summary == "内容过时"
            assert session.scalars(select(Favorite)).all() == []
    finally:
        engine.dispose()


def test_admin_can_archive_pending_resource_but_owner_cannot(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{(tmp_path / 'admin_archive.db').as_posix()}",
        cors_origins=[],
        jwt_secret_key="test-only-secret-key-for-resources-1234",
    )
    initialize_database(settings)
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            owner = User(username="owner", display_name="Owner", password_hash="test", role="student")
            teacher = User(username="teacher", display_name="Teacher", password_hash="test", role="teacher")
            admin = User(username="admin", display_name="Admin", password_hash="test", role="admin")
            session.add_all([owner, teacher, admin])
            session.flush()
            course = Course(code="COURSE-1", title="Course", teacher_id=teacher.id)
            category = Category(name="Category")
            session.add_all([course, category])
            session.flush()
            resource = Resource(
                title="Pending resource",
                resource_type="link",
                url="https://example.org/resource",
                course_id=course.id,
                category_id=category.id,
                owner_id=owner.id,
                status="pending",
            )
            session.add(resource)
            session.commit()

            with pytest.raises(ResourcePermissionError):
                archive_resource(
                    session,
                    actor=owner,
                    resource_id=resource.id,
                    expected_version=1,
                    reason="Owner cannot skip withdrawal",
                    request_id=str(uuid4()),
                )
            archived = archive_resource(
                session,
                actor=admin,
                resource_id=resource.id,
                expected_version=1,
                reason="Platform rule violation",
                request_id=str(uuid4()),
            )
            assert archived.status == "archived"
            assert archived.version_id == 2
            logs = session.scalars(
                select(OperationLog).where(OperationLog.action == "resource.archive")
            ).all()
            assert len(logs) == 1
            assert logs[0].actor_id == admin.id
            admin_id, owner_id, resource_id = admin.id, owner.id, resource.id

        async def check_admin_list() -> None:
            transport = httpx.ASGITransport(app=create_app(settings))
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                admin_token, _ = create_access_token(admin_id, settings)
                owner_token, _ = create_access_token(owner_id, settings)
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                owner_headers = {"Authorization": f"Bearer {owner_token}"}
                listed = await client.get(
                    "/api/v1/resources/admin?status=archived&q=Pending&sort=title",
                    headers=admin_headers,
                )
                denied = await client.get("/api/v1/resources/admin", headers=owner_headers)
                empty = await client.get(
                    "/api/v1/resources/admin?status=pending", headers=admin_headers
                )
                assert listed.status_code == 200
                assert listed.json()["data"]["total"] == 1
                assert listed.json()["data"]["items"][0]["id"] == resource_id
                assert listed.json()["data"]["items"][0]["owner_display_name"] == "Owner"
                assert denied.status_code == 403
                assert empty.json()["data"]["total"] == 0

        asyncio.run(check_admin_list())
    finally:
        engine.dispose()
