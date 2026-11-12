"""HTTP 错误响应的统一出口。

所有错误响应使用同一包络（见 docs/api-contract.md 第 10 节）：

    {
      "error": {"code": ..., "message": ..., "details": [...]},
      "request_id": "..."
    }

`safe` 的含义：处理器只输出我们自己构造的文字，绝不回传异常原文、
Pydantic 的 input/ctx（可能含明文密码）或 SQL 语句。
"""

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.dependencies import AuthFailure

# ---------------------------------------------------------------------------
# 包络构造
# ---------------------------------------------------------------------------


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    """生成一个响应；request_id 同时写入 body 和 X-Request-ID 头。"""

    request_id = str(uuid4())
    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=status_code,
        headers=response_headers,
        content={
            "error": {
                "code": code,
                "message": message,
                # 契约要求 details 固定为数组；非字段错误时为空数组
                "details": details or [],
            },
            "request_id": request_id,
        },
    )


# ---------------------------------------------------------------------------
# 自己抛出的业务/权限异常
# ---------------------------------------------------------------------------


async def handle_auth_failure(_request: Request, exc: AuthFailure) -> JSONResponse:
    headers: dict[str, str] = {}
    # 401 必须带这个头（RFC 7235），客户端据此知道用 Bearer 认证
    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return error_response(exc.status_code, exc.code, exc.message, headers)


# ---------------------------------------------------------------------------
# 字段校验失败（422）
# ---------------------------------------------------------------------------

# 只翻译常见错误类型；未覆盖的退回 Pydantic 的原文（英文，但不含敏感数据）。
_VALIDATION_MESSAGES = {
    "missing": "该字段必填",
    "extra_forbidden": "不允许提交该字段",
    "string_type": "应为字符串",
    "string_too_short": "长度不足",
    "string_too_long": "长度超出上限",
    "string_pattern_mismatch": "格式不符合要求",
    "int_type": "应为整数",
    "int_parsing": "应为整数",
    "bool_parsing": "应为布尔值",
    "greater_than_equal": "数值小于允许的最小值",
    "less_than_equal": "数值大于允许的最大值",
    "literal_error": "取值不在允许范围内",
    "json_invalid": "请求体不是合法的 JSON",
}


async def handle_validation_error(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """把 Pydantic 的错误转成契约规定的 details 数组。

    只取 loc/type/msg，**不输出 input 与 ctx**：原始输入里可能带明文密码。
    """

    details: list[dict[str, str]] = []
    for error in exc.errors():
        location = error.get("loc", ())
        details.append(
            {
                "field": ".".join(str(part) for part in location) or "body",
                "message": _VALIDATION_MESSAGES.get(
                    str(error.get("type")), str(error.get("msg", "参数不合法"))
                ),
            }
        )
    return error_response(422, "VALIDATION_ERROR", "请求参数不合法", details=details)


# ---------------------------------------------------------------------------
# 框架抛出的 HTTP 异常（未知路径 404、方法不允许 405 等）
# ---------------------------------------------------------------------------

_HTTP_STATUS_MAP = {
    400: ("VALIDATION_ERROR", "请求不合法"),
    401: ("AUTH_REQUIRED", "请先登录"),
    403: ("FORBIDDEN", "无权执行此操作"),
    404: ("NOT_FOUND", "请求的资源不存在"),
    405: ("METHOD_NOT_ALLOWED", "不支持该请求方法"),
    409: ("INVALID_STATE", "当前状态不允许该操作"),
    503: ("SERVICE_UNAVAILABLE", "服务暂不可用"),
}


async def handle_http_exception(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code, message = _HTTP_STATUS_MAP.get(exc.status_code, ("HTTP_ERROR", "请求失败"))
    # 保留 Allow 等必要响应头；不使用 exc.detail，避免泄露内部细节
    return error_response(exc.status_code, code, message, exc.headers)


# ---------------------------------------------------------------------------
# 未预期异常（500）
# ---------------------------------------------------------------------------


async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    """不输出异常信息或堆栈。Starlette 仍会把 traceback 打到服务端日志。"""

    return error_response(500, "INTERNAL_ERROR", "服务器内部错误")


# ---------------------------------------------------------------------------


def register_exception_handlers(application: FastAPI) -> None:
    """在 create_app() 里调用一次；处理器属于 app 实例，不能全局注册。"""

    application.add_exception_handler(AuthFailure, handle_auth_failure)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(StarletteHTTPException, handle_http_exception)
    application.add_exception_handler(Exception, handle_unexpected_error)
