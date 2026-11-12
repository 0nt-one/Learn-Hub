"""Infrastructure behavior checks; no database or business routes are needed."""

import asyncio
from pathlib import Path

import httpx
import pytest
import jwt
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.engine import create_db_engine
from app.main import create_app
from app.db.init_db import initialize_database
from app.models.user import User
from app.models.course import Course
from app.models.operation_log import OperationLog
from app.schemas.auth import RegisterRequest
from app.services.auth import create_initial_admin


# ---------------------------------------------------------------------------
# 辅助函数：方便测试里发请求、造配置
# ---------------------------------------------------------------------------

def request(settings: Settings, method: str, path: str, **kwargs: object) -> httpx.Response:
    """在测试进程内直接调用 FastAPI 应用，不需要真的启动服务器。

    好处：速度快、不用开端口、不会污染本机环境。
    """

    async def send() -> httpx.Response:
        # ASGITransport 让 httpx 直接和 ASGI 应用对话（进程内调用）
        transport = httpx.ASGITransport(app=create_app(settings))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    # httpx 是异步的，这里用 asyncio.run 把它包成同步，测试里写起来更简单
    return asyncio.run(send())


def settings_for(tmp_path: Path, origins: list[str]) -> Settings:
    """造一个测试专用的配置对象。"""
    return Settings(
        _env_file=None,  # 不读取 .env 文件，避免本地环境影响测试结果
        app_env="testing",
        # 数据库指向临时目录下的文件，测试结束后 pytest 会自动清理
        database_url=f"sqlite:///{(tmp_path / 'unused.db').as_posix()}",
        cors_origins=origins,  # 允许跨域的来源列表，不同测试传不同值
        jwt_secret_key="test-only-secret-key-for-login-1234",
    )


@pytest.mark.parametrize(
    ("secret_key", "expected_message"),
    [
        (None, "JWT_SECRET_KEY is required"),
        ("short", "JWT_SECRET_KEY must be at least 32 bytes"),
    ],
)
def test_app_rejects_missing_or_short_jwt_key(
    tmp_path: Path, secret_key: str | None, expected_message: str
) -> None:
    database_path = tmp_path / "unused.db"
    settings = Settings(
        _env_file=None,
        app_env="testing",
        database_url=f"sqlite:///{database_path.as_posix()}",
        cors_origins=[],
        jwt_secret_key=secret_key,
    )

    with pytest.raises(RuntimeError, match=expected_message):
        create_app(settings)
    assert not database_path.exists()


# ---------------------------------------------------------------------------
# 测试 1：OpenAPI 文档能访问，且不会偷偷创建数据库
# ---------------------------------------------------------------------------

def test_openapi_is_available_without_creating_database(tmp_path: Path) -> None:
    # 发一个 GET /openapi.json 请求
    response = request(settings_for(tmp_path, []), "GET", "/openapi.json")

    # 状态码 200 表示成功
    assert response.status_code == 200
    # 文档标题应该是 Learn-Hub API
    assert response.json()["info"]["title"] == "Learn-Hub API"
    # 关键：只是访问文档，不应该创建数据库文件（说明数据库是“用到才初始化”）
    assert not (tmp_path / "unused.db").exists()


# ---------------------------------------------------------------------------
# 测试 2：默认配置下，不允许任何跨域请求
# ---------------------------------------------------------------------------

def test_default_configuration_does_not_allow_cross_origin(tmp_path: Path) -> None:
    # 模拟一个来自其他网站的请求（带 Origin 头）
    response = request(
        settings_for(tmp_path, []),  # cors_origins 传空列表 = 谁都不允许
        "GET",
        "/openapi.json",
        headers={"Origin": "https://other.example"},
    )

    # 请求本身还是能成功
    assert response.status_code == 200
    # 但没有 Access-Control-Allow-Origin 头，浏览器就会拦截跨域读取
    assert "access-control-allow-origin" not in response.headers


# ---------------------------------------------------------------------------
# 测试 3：CORS 预检请求（OPTIONS）必须精确匹配 origin
# ---------------------------------------------------------------------------

# parametrize 表示这组参数会跑多次，每次测一个场景
@pytest.mark.parametrize(
    ("origin", "expected_status", "expected_allowed_origin"),
    [
        # 来源完全匹配配置 -> 放行
        ("http://127.0.0.1:5173", 200, "http://127.0.0.1:5173"),
        # 端口不同 -> 拒绝（说明不是按前缀匹配）
        ("http://127.0.0.1:5174", 400, None),
        # 不可信域名 -> 拒绝
        ("https://untrusted.example", 400, None),
    ],
)
def test_cors_preflight_checks_exact_origin(
    tmp_path: Path,
    origin: str,
    expected_status: int,
    expected_allowed_origin: str | None,
) -> None:
    # 配置里只允许 http://127.0.0.1:5173 这一个来源
    response = request(
        settings_for(tmp_path, ["http://127.0.0.1:5173"]),
        "OPTIONS",  # 预检请求用 OPTIONS
        "/openapi.json",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    # 检查状态码是否符合预期
    assert response.status_code == expected_status
    # 检查返回的允许来源是否和预期一致（被拒绝时应该是 None）
    assert response.headers.get("access-control-allow-origin") == expected_allowed_origin


# ---------------------------------------------------------------------------
# 测试 4：健康检查必须等数据库初始化完成后才返回 200
# ---------------------------------------------------------------------------

def test_health_requires_initialized_database(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, [])

    # 第一次请求：数据库还没初始化，健康检查应该返回 503（服务不可用）
    before = request(settings, "GET", "/health")
    assert before.status_code == 503
    assert before.json()["error"]["code"] == "SERVICE_UNAVAILABLE"

    # 手动初始化数据库
    initialize_database(settings)

    # 第二次请求：数据库就绪，健康检查应该返回 200
    after = request(settings, "GET", "/health")
    assert after.status_code == 200
    assert after.json()["data"]["database"] == "ready"
    # 响应体里的 request_id 应该和响应头 X-Request-ID 一致（方便追踪请求）
    assert after.json()["request_id"] == after.headers["X-Request-ID"]
    # 健康检查结果不能被缓存，否则代理会一直返回旧状态
    assert after.headers["Cache-Control"] == "no-store"


def test_registration_exposes_public_user_and_rejects_duplicate(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, [])
    initialize_database(settings)
    payload = {
        "username": "  Alice  ",
        "password": "example-pass-123",
        "display_name": "Alice",
    }

    created = request(settings, "POST", "/api/v1/auth/register", json=payload)
    assert created.status_code == 201
    assert created.json()["data"]["username"] == "alice"
    assert created.json()["data"]["role"] == "student"
    assert "password_hash" not in created.json()["data"]
    assert created.json()["request_id"] == created.headers["X-Request-ID"]

    duplicate = request(settings, "POST", "/api/v1/auth/register", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "USERNAME_EXISTS"

    injected_role = request(
        settings,
        "POST",
        "/api/v1/auth/register",
        json={**payload, "username": "bob", "role": "admin"},
    )
    assert injected_role.status_code == 422

def test_login_returns_valid_token_and_rejects_wrong_password(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, [])
    initialize_database(settings)

    register_response = request(
        settings,
        "POST",
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "password": "example-pass-123",
            "display_name": "Alice",
        },
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["data"]["id"]

    login_response = request(
        settings,
        "POST",
        "/api/v1/auth/login",
        json={"username": "  ALICE  ", "password": "example-pass-123"},
    )
    assert login_response.status_code == 200

    token_data = login_response.json()["data"]
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == 1800
    assert token_data["user"]["id"] == user_id
    assert "password_hash" not in token_data["user"]

    claims = jwt.decode(
        token_data["access_token"],
        settings.jwt_secret_key.get_secret_value(),
        algorithms=["HS256"],
        issuer="learn-hub",
        audience="learn-hub-api",
    )
    assert claims["sub"] == str(user_id)
    assert "role" not in claims

    wrong_password_response = request(
        settings,
        "POST",
        "/api/v1/auth/login",
        json={"username": "alice", "password": "wrong"},
    )
    assert wrong_password_response.status_code == 401
    assert wrong_password_response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong_password_response.headers["WWW-Authenticate"] == "Bearer"


def test_my_profile_checks_token_and_current_account_status(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, [])
    initialize_database(settings)

    registered = request(
        settings,
        "POST",
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "password": "example-pass-123",
            "display_name": "Alice",
        },
    )
    assert registered.status_code == 201
    user_id = registered.json()["data"]["id"]

    missing_token = request(settings, "GET", "/api/v1/users/me")
    assert missing_token.status_code == 401
    assert missing_token.json()["error"]["code"] == "AUTH_REQUIRED"
    assert missing_token.headers["WWW-Authenticate"] == "Bearer"

    invalid_token = request(
        settings,
        "GET",
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert invalid_token.status_code == 401
    assert invalid_token.json()["error"]["code"] == "INVALID_TOKEN"

    logged_in = request(
        settings,
        "POST",
        "/api/v1/auth/login",
        json={"username": "alice", "password": "example-pass-123"},
    )
    assert logged_in.status_code == 200
    access_token = logged_in.json()["data"]["access_token"]
    authorization = {"Authorization": f"Bearer {access_token}"}

    profile = request(settings, "GET", "/api/v1/users/me", headers=authorization)
    assert profile.status_code == 200
    assert profile.json()["data"]["id"] == user_id
    assert profile.json()["request_id"] == profile.headers["X-Request-ID"]

    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            user = session.get(User, user_id)
            assert user is not None
            user.is_active = False
            session.commit()
    finally:
        engine.dispose()

    disabled = request(settings, "GET", "/api/v1/users/me", headers=authorization)
    assert disabled.status_code == 403
    assert disabled.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_admin_user_list_enforces_role_and_paginates_filtered_results(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, [])
    initialize_database(settings)

    for username in ("alice", "bob", "albert"):
        created = request(
            settings,
            "POST",
            "/api/v1/auth/register",
            json={
                "username": username,
                "password": "example-pass-123",
                "display_name": username,
            },
        )
        assert created.status_code == 201

    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            create_initial_admin(
                session,
                RegisterRequest(
                    username="manager",
                    password="example-pass-123",
                    display_name="Manager",
                ),
            )
    finally:
        engine.dispose()

    def login_as(username: str) -> dict[str, str]:
        response = request(
            settings,
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": "example-pass-123"},
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}

    student_response = request(
        settings, "GET", "/api/v1/users", headers=login_as("alice")
    )
    assert student_response.status_code == 403
    assert student_response.json()["error"]["code"] == "FORBIDDEN"

    admin_headers = login_as("manager")
    first_page = request(
        settings,
        "GET",
        "/api/v1/users?page=1&page_size=1&role=student&q=al",
        headers=admin_headers,
    )
    assert first_page.status_code == 200
    assert first_page.json()["data"]["total"] == 2
    assert [item["username"] for item in first_page.json()["data"]["items"]] == [
        "albert"
    ]
    assert "password_hash" not in first_page.json()["data"]["items"][0]

    second_page = request(
        settings,
        "GET",
        "/api/v1/users?page=2&page_size=1&role=student&q=al",
        headers=admin_headers,
    )
    assert second_page.status_code == 200
    assert [item["username"] for item in second_page.json()["data"]["items"]] == [
        "alice"
    ]
    assert second_page.json()["data"]["total"] == 2

    alice_id = second_page.json()["data"]["items"][0]["id"]
    student_change = request(
        settings,
        "PATCH",
        f"/api/v1/users/{alice_id}",
        headers=login_as("bob"),
        json={"role": "teacher"},
    )
    assert student_change.status_code == 403
    assert student_change.json()["error"]["code"] == "FORBIDDEN"

    promoted = request(
        settings,
        "PATCH",
        f"/api/v1/users/{alice_id}",
        headers=admin_headers,
        json={"role": "teacher"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["data"]["role"] == "teacher"
    assert promoted.json()["request_id"] == promoted.headers["X-Request-ID"]

    admin_profile = request(
        settings, "GET", "/api/v1/users/me", headers=admin_headers
    )
    admin_id = admin_profile.json()["data"]["id"]
    self_disable = request(
        settings,
        "PATCH",
        f"/api/v1/users/{admin_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert self_disable.status_code == 409
    assert self_disable.json()["error"]["code"] == "ADMIN_SELF_CHANGE_FORBIDDEN"


def test_admin_category_creation_is_audited_and_rejects_duplicates(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, [])
    initialize_database(settings)
    student = request(
        settings,
        "POST",
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "password": "example-pass-123",
            "display_name": "Alice",
        },
    )
    assert student.status_code == 201

    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            create_initial_admin(
                session,
                RegisterRequest(
                    username="manager",
                    password="example-pass-123",
                    display_name="Manager",
                ),
            )
    finally:
        engine.dispose()

    def auth_headers(username: str) -> dict[str, str]:
        logged_in = request(
            settings,
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": "example-pass-123"},
        )
        assert logged_in.status_code == 200
        return {"Authorization": f"Bearer {logged_in.json()['data']['access_token']}"}

    student_response = request(
        settings,
        "POST",
        "/api/v1/categories",
        headers=auth_headers("alice"),
        json={"name": "Math"},
    )
    assert student_response.status_code == 403
    assert student_response.json()["error"]["code"] == "FORBIDDEN"

    admin_headers = auth_headers("manager")
    created = request(
        settings,
        "POST",
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "  Math  ", "description": "基础课程"},
    )
    assert created.status_code == 201
    assert created.json()["data"]["name"] == "Math"
    assert created.json()["request_id"] == created.headers["X-Request-ID"]

    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            log = session.query(OperationLog).filter_by(
                request_id=created.json()["request_id"]
            ).one()
            assert (log.action, log.target_type, log.target_id) == (
                "category.create",
                "category",
                created.json()["data"]["id"],
            )
    finally:
        engine.dispose()

    duplicate = request(
        settings,
        "POST",
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "math"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CATEGORY_NAME_EXISTS"

    hidden = request(
        settings,
        "POST",
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Archive"},
    )
    assert hidden.status_code == 201
    hidden_id = hidden.json()["data"]["id"]
    disabled = request(
        settings,
        "PATCH",
        f"/api/v1/categories/{hidden_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["is_active"] is False

    student_headers = auth_headers("alice")
    visible = request(
        settings, "GET", "/api/v1/categories", headers=student_headers
    )
    assert visible.status_code == 200
    assert [item["name"] for item in visible.json()["data"]["items"]] == ["Math"]
    assert visible.json()["data"]["total"] == 1

    forbidden = request(
        settings,
        "GET",
        "/api/v1/categories?is_active=false",
        headers=student_headers,
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    student_change = request(
        settings,
        "PATCH",
        f"/api/v1/categories/{hidden_id}",
        headers=student_headers,
        json={"name": "Hidden"},
    )
    assert student_change.status_code == 403

    invalid_change = request(
        settings,
        "PATCH",
        f"/api/v1/categories/{hidden_id}",
        headers=admin_headers,
        json={"name": None},
    )
    assert invalid_change.status_code == 422

    duplicate_change = request(
        settings,
        "PATCH",
        f"/api/v1/categories/{hidden_id}",
        headers=admin_headers,
        json={"name": "math"},
    )
    assert duplicate_change.status_code == 409
    assert duplicate_change.json()["error"]["code"] == "CATEGORY_NAME_EXISTS"

    admin_all = request(settings, "GET", "/api/v1/categories", headers=admin_headers)
    assert admin_all.status_code == 200
    assert [item["name"] for item in admin_all.json()["data"]["items"]] == [
        "Archive",
        "Math",
    ]
    assert admin_all.json()["data"]["total"] == 2


def test_course_creation_uses_current_role_and_teacher_assignment(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, [])
    initialize_database(settings)

    def register(username: str) -> int:
        response = request(
            settings,
            "POST",
            "/api/v1/auth/register",
            json={
                "username": username,
                "password": "example-pass-123",
                "display_name": username,
            },
        )
        assert response.status_code == 201
        return response.json()["data"]["id"]

    teacher_id = register("teacher")
    register("student")
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            teacher = session.get(User, teacher_id)
            assert teacher is not None
            teacher.role = "teacher"
            create_initial_admin(
                session,
                RegisterRequest(
                    username="manager",
                    password="example-pass-123",
                    display_name="Manager",
                ),
            )
            session.commit()
    finally:
        engine.dispose()

    def auth_headers(username: str) -> dict[str, str]:
        response = request(
            settings,
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": "example-pass-123"},
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}

    teacher_headers = auth_headers("teacher")
    admin_headers = auth_headers("manager")
    student_headers = auth_headers("student")

    created = request(
        settings,
        "POST",
        "/api/v1/courses",
        headers=teacher_headers,
        json={"code": " math-101 ", "title": "  Mathematics  "},
    )
    assert created.status_code == 201
    assert created.json()["data"]["code"] == "MATH-101"
    assert created.json()["data"]["title"] == "Mathematics"
    assert created.json()["data"]["teacher_id"] == teacher_id
    assert created.json()["data"]["teacher_display_name"] == "teacher"

    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            log = session.query(OperationLog).filter_by(
                request_id=created.json()["request_id"]
            ).one()
            assert (log.action, log.target_type) == ("course.create", "course")
    finally:
        engine.dispose()

    teacher_override = request(
        settings,
        "POST",
        "/api/v1/courses",
        headers=teacher_headers,
        json={"code": "OTHER", "title": "Other", "teacher_id": teacher_id},
    )
    assert teacher_override.status_code == 422
    assert teacher_override.json()["error"]["code"] == "VALIDATION_ERROR"

    admin_without_teacher = request(
        settings,
        "POST",
        "/api/v1/courses",
        headers=admin_headers,
        json={"code": "PHYS-1", "title": "Physics"},
    )
    assert admin_without_teacher.status_code == 422

    admin_created = request(
        settings,
        "POST",
        "/api/v1/courses",
        headers=admin_headers,
        json={"code": "PHYS-1", "title": "Physics", "teacher_id": teacher_id},
    )
    assert admin_created.status_code == 201
    assert admin_created.json()["data"]["teacher_id"] == teacher_id

    duplicate_code = request(
        settings,
        "POST",
        "/api/v1/courses",
        headers=admin_headers,
        json={"code": "math-101", "title": "Duplicate", "teacher_id": teacher_id},
    )
    assert duplicate_code.status_code == 409
    assert duplicate_code.json()["error"]["code"] == "COURSE_CODE_EXISTS"

    student_created = request(
        settings,
        "POST",
        "/api/v1/courses",
        headers=student_headers,
        json={"code": "STUDENT", "title": "Denied"},
    )
    assert student_created.status_code == 403

    hidden_course_id = admin_created.json()["data"]["id"]
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            hidden_course = session.get(Course, hidden_course_id)
            assert hidden_course is not None
            hidden_course.is_active = False
            session.commit()
    finally:
        engine.dispose()

    student_list = request(
        settings,
        "GET",
        "/api/v1/courses?q=Math&page=1&page_size=1",
        headers=student_headers,
    )
    assert student_list.status_code == 200
    assert student_list.json()["data"]["total"] == 1
    assert [item["code"] for item in student_list.json()["data"]["items"]] == [
        "MATH-101"
    ]

    forbidden_filter = request(
        settings,
        "GET",
        "/api/v1/courses?is_active=false",
        headers=student_headers,
    )
    assert forbidden_filter.status_code == 403

    hidden_detail = request(
        settings,
        "GET",
        f"/api/v1/courses/{hidden_course_id}",
        headers=student_headers,
    )
    assert hidden_detail.status_code == 404
    owner_hidden_detail = request(
        settings,
        "GET",
        f"/api/v1/courses/{hidden_course_id}",
        headers=teacher_headers,
    )
    assert owner_hidden_detail.status_code == 200
    assert owner_hidden_detail.json()["data"]["teacher_display_name"] == "teacher"

    admin_list = request(
        settings, "GET", "/api/v1/courses", headers=admin_headers
    )
    assert admin_list.status_code == 200
    assert admin_list.json()["data"]["total"] == 2
    assert [item["code"] for item in admin_list.json()["data"]["items"]] == [
        "PHYS-1",
        "MATH-101",
    ]
    assert all(
        item["teacher_display_name"] == "teacher"
        for item in admin_list.json()["data"]["items"]
    )

    teacher_mine = request(
        settings, "GET", "/api/v1/courses/mine", headers=teacher_headers
    )
    assert teacher_mine.status_code == 200
    assert teacher_mine.json()["data"]["total"] == 2
    inactive_mine = request(
        settings,
        "GET",
        "/api/v1/courses/mine?is_active=false",
        headers=teacher_headers,
    )
    assert inactive_mine.status_code == 200
    assert [item["code"] for item in inactive_mine.json()["data"]["items"]] == [
        "PHYS-1"
    ]
    student_mine = request(
        settings, "GET", "/api/v1/courses/mine", headers=student_headers
    )
    assert student_mine.status_code == 403

    admin_detail = request(
        settings,
        "GET",
        f"/api/v1/courses/{hidden_course_id}",
        headers=admin_headers,
    )
    assert admin_detail.status_code == 200
    assert admin_detail.json()["data"]["is_active"] is False

    math_id = created.json()["data"]["id"]
    student_edit = request(
        settings,
        "PATCH",
        f"/api/v1/courses/{math_id}",
        headers=student_headers,
        json={"title": "Student edit"},
    )
    assert student_edit.status_code == 403

    owner_edit = request(
        settings,
        "PATCH",
        f"/api/v1/courses/{math_id}",
        headers=teacher_headers,
        json={"title": "Advanced Math"},
    )
    assert owner_edit.status_code == 200
    assert owner_edit.json()["data"]["title"] == "Advanced Math"
    assert owner_edit.json()["data"]["teacher_id"] == teacher_id

    teacher_transfer = request(
        settings,
        "PATCH",
        f"/api/v1/courses/{math_id}",
        headers=teacher_headers,
        json={"teacher_id": teacher_id},
    )
    assert teacher_transfer.status_code == 422

    second_teacher_id = register("teacher2")
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            second_teacher = session.get(User, second_teacher_id)
            assert second_teacher is not None
            second_teacher.role = "teacher"
            session.commit()
    finally:
        engine.dispose()

    transferred = request(
        settings,
        "PATCH",
        f"/api/v1/courses/{math_id}",
        headers=admin_headers,
        json={"teacher_id": second_teacher_id},
    )
    assert transferred.status_code == 200
    assert transferred.json()["data"]["teacher_id"] == second_teacher_id
    assert transferred.json()["data"]["teacher_display_name"] == "teacher2"
    assert transferred.json()["request_id"] == transferred.headers["X-Request-ID"]
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            transfer_log = session.query(OperationLog).filter_by(
                request_id=transferred.json()["request_id"]
            ).one()
            assert (transfer_log.action, transfer_log.target_id) == (
                "course.update",
                math_id,
            )
    finally:
        engine.dispose()

    former_owner_edit = request(
        settings,
        "PATCH",
        f"/api/v1/courses/{math_id}",
        headers=teacher_headers,
        json={"title": "No longer owner"},
    )
    assert former_owner_edit.status_code == 403
    former_owner_mine = request(
        settings, "GET", "/api/v1/courses/mine", headers=teacher_headers
    )
    assert former_owner_mine.status_code == 200
    assert [item["code"] for item in former_owner_mine.json()["data"]["items"]] == [
        "PHYS-1"
    ]

    duplicate_update = request(
        settings,
        "PATCH",
        f"/api/v1/courses/{math_id}",
        headers=admin_headers,
        json={"code": "PHYS-1"},
    )
    assert duplicate_update.status_code == 409
    assert duplicate_update.json()["error"]["code"] == "COURSE_CODE_EXISTS"
