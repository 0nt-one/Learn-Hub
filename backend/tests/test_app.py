"""Infrastructure behavior checks; no database or business routes are needed."""

import asyncio
from pathlib import Path

import httpx
import pytest
import jwt

from app.core.config import Settings
from app.main import create_app
from app.db.init_db import initialize_database


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