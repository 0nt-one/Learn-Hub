# Learn-Hub 第一版 API 契约

状态：设计基线 v1。`GET /health` 已在任务四实现；其余 API 仍为业务规划，尚未实现。

## 1. 通用约定

- 基础路径 `/api/v1`，JSON UTF-8；ID 为正整数，字段名 snake_case；时间为 UTC ISO 8601，例如 `2026-10-23T06:30:00Z`。
- 除 health、register、login 外，全部接口要求 `Authorization: Bearer <access_token>`。角色、启用状态、所有权、课程范围和资源可见性均在后端校验。
- 成功响应包含 `data`、`request_id`；错误响应包含 `error`、`request_id`。服务端为每次请求生成 UUID，并在 `X-Request-ID` 响应头返回，不盲目信任客户端传入值。
- 创建实体返回 201；查询、更新和幂等关系操作返回 200，不使用空响应 204，以保持统一包络。没有 DELETE 硬删除用户、课程、分类或资源接口。
- 未声明的请求字段拒绝（Pydantic `extra='forbid'`）；所有关联对象与最终角色均从数据库验证。PATCH 至少一个字段，未提交字段不变，非可空字段不接受 null。
- 普通列表参数 `page` 默认 1、最小 1；`page_size` 默认 20、范围 1–100；返回 `{items, total, page, page_size}`。排序必须有 id 作为第二排序键，禁止将排序参数直接拼接 SQL。
- 下文列出的业务接口属于同一个 v1 契约，按切片实现。尚未实现的路径不得作为成功 API 对外宣传。

成功示例：

```json
{
  "data": { "id": 12, "title": "线性代数入门" },
  "request_id": "2b6fd8ab-872c-4442-93b7-8e3e249ff3b5"
}
```

分页示例：

```json
{
  "data": { "items": [], "total": 0, "page": 1, "page_size": 20 },
  "request_id": "2b6fd8ab-872c-4442-93b7-8e3e249ff3b5"
}
```

## 2. 响应数据结构

| DTO | data 内字段 |
| --- | --- |
| User | id, username, display_name, role, is_active, created_at, updated_at |
| Token | access_token, token_type（固定 bearer）, expires_in（秒）, user: User |
| Course | id, code, title, description, teacher_id, is_active, created_at, updated_at |
| Category | id, name, description, is_active, created_at, updated_at |
| Resource | id, title, description, resource_type, url, duration_seconds, page_count, course_id, category_id, owner_id, status, version_id, created_at, updated_at |
| ReviewRecord | id, resource_id, reviewer_id, resource_version, decision, comment, created_at |
| LearningRecord | id, user_id, resource_id, progress, last_accessed_at, created_at, updated_at |
| Favorite | id, resource_id, created_at |
| Notification | id, kind, title, content, review_record_id, read_at, created_at |
| OperationLog | id, actor_id, action, target_type, target_id, request_id, summary, created_at |

任何响应都不含 password_hash；学习记录的 user_id 永远为当前用户。收藏与学习记录列表项在上述字段之外增加 `resource`：资源常规可见时为 `{id,title,resource_type}`，不可见时为 `{id,unavailable:true}`，不返回其标题或 URL。资源 URL 仅通过有权限的详情或资源列表返回。

## 3. 工程阶段最小接口：健康检查

### GET /health

公开；不接收参数。检查数据库 `SELECT 1` 以及九张预期表是否存在。检查成功才返回 200：

```json
{
  "data": { "status": "ok", "service": "learn-hub-api", "database": "ready" },
  "request_id": "2b6fd8ab-872c-4442-93b7-8e3e249ff3b5"
}
```

数据库不可连接或未初始化返回 503、错误码 `SERVICE_UNAVAILABLE`，公开消息固定为“服务暂不可用”，不返回数据库路径或 SQL。设置 `Cache-Control: no-store`，防止页面显示缓存中的健康结果。

首页挂载时通过 API 模块请求此接口，设置超时，展示“检查中 / 服务正常 / 连接失败”，失败时提供重试。不能以写死的成功消息代替联调。

## 4. 身份与用户（后续切片）

| 方法与路径 | 输入 | 权限 | 成功响应 data |
| --- | --- | --- | --- |
| POST /auth/register | JSON: username, password, display_name | 公开；不接受 role/is_active | 201 User，角色固定 student |
| POST /auth/login | JSON: username, password | 公开 | 200 Token |
| GET /users/me | 无 | 已登录 | 200 User |
| GET /users | 分页；可选 role、is_active、q（用户名，1–100 字符） | 管理员 | 200 分页 User，id 倒序 |
| PATCH /users/{id} | JSON: role?、is_active?；至少一个 | 管理员 | 200 User |

用户名 3–32 字符、密码 12–128 字符、display_name 1–64 字符。注册前规范化 username；重复注册返回 409 `USERNAME_EXISTS`。登录失败（含用户不存在、密码错误、停用）统一 401 `INVALID_CREDENTIALS`，避免提供账户枚举信息。

用户角色仅 student / teacher / admin。禁止管理员降级或停用自己，返回 409 `ADMIN_SELF_CHANGE_FORBIDDEN`；教师降级或停用前若仍负责课程，返回 409 `COURSE_TRANSFER_REQUIRED`。未登录 401 含 `WWW-Authenticate: Bearer`；已认证但停用返回 403 `ACCOUNT_DISABLED`。

不提供 refresh/logout API：客户端退出清除内存令牌；令牌有效期和退出限制见 requirements.md。

## 5. 课程与分类（后续切片）

| 方法与路径 | 输入 | 权限 | 成功响应 data |
| --- | --- | --- | --- |
| GET /courses | 分页；q?（标题，1–100 字符）、is_active? | 登录；非管理员只能查启用课程 | 200 分页 Course，created_at/id 倒序 |
| GET /courses/{id} | 路径 id | 登录；非管理员仅启用课程 | 200 Course |
| POST /courses | JSON: code, title, description?, teacher_id? | 教师/管理员 | 201 Course |
| PATCH /courses/{id} | JSON: code?、title?、description?、is_active?、teacher_id? | 负责人/管理员 | 200 Course |
| GET /categories | 分页；is_active? | 登录；非管理员只能查启用分类 | 200 分页 Category，name/id 升序 |
| POST /categories | JSON: name, description? | 管理员 | 201 Category |
| PATCH /categories/{id} | JSON: name?、description?、is_active? | 管理员 | 200 Category |

code 1–32 字符，仅 ASCII 字母、数字、短横线，规范化为大写；title 1–200，description 最多 5000。教师创建时 teacher_id 由后端固定为本人，不接受该字段；管理员创建时 teacher_id 必填，修改时也只有管理员可以转移负责人，目标必须为启用教师。课程代码冲突 409 `COURSE_CODE_EXISTS`。

分类 name 1–64，description 最多 1000；名称去首尾空格后唯一，冲突 409 `CATEGORY_NAME_EXISTS`。非管理员显式查询 is_active=false 返回 403，不扩大可见范围。

## 6. 资源与提交（后续切片）

| 方法与路径 | 输入 | 权限 | 成功响应 data |
| --- | --- | --- | --- |
| GET /resources | 分页；q?、course_id?、category_id?、resource_type?、sort? | 登录；仅常规可见资源 | 200 分页 Resource |
| GET /resources/mine | 分页；status? | 登录；仅本人资源，包含历史角色拥有资源 | 200 分页 Resource |
| GET /resources/{id} | 路径 id | 常规可见、本人的资源、授权待审资源或管理员 | 200 Resource |
| POST /resources | JSON 见下 | 学生/教师 | 201 Resource，status=draft |
| PATCH /resources/{id} | JSON: expected_version + 可编辑字段 | 学生/教师且本人；draft/rejected | 200 Resource |
| POST /resources/{id}/submit | JSON: expected_version | 学生/教师且本人；draft/rejected | 200 Resource，pending |
| POST /resources/{id}/withdraw | JSON: expected_version | 本人；pending/approved，包括历史角色拥有资源 | 200 Resource，draft |
| POST /resources/{id}/archive | JSON: expected_version, reason | 本人非待审资源或管理员；非 archived | 200 Resource，archived |

创建示例（视频）：

```json
{
  "title": "矩阵基础讲解",
  "description": "课程配套视频",
  "resource_type": "video",
  "url": "https://example.org/lessons/matrices",
  "duration_seconds": 1200,
  "course_id": 1,
  "category_id": 2
}
```

创建必填 title、resource_type、url、course_id、category_id；description 默认空字符串；duration_seconds 与 page_count 默认 null。owner_id、status、version_id 由后端生成，不允许传入。

可编辑字段仅 title、description、resource_type、url、duration_seconds、page_count、course_id、category_id。编辑必须将已有数据与 PATCH 合并后再检查跨字段约束，切换类型时客户端应显式清空不兼容的元数据字段。规则与长度见 requirements.md。

所有资源变更 expected_version 为大于零的整数，成功返回递增后的 version_id。archive 的 reason 去空白后 1–2000 字符，写入操作日志；管理员可强制归档 pending，其他人先撤回。archived 不可恢复，重复归档返回 409。

列表 q 按标题进行字面子串匹配，1–100 字符，转义 `%` 与 `_`；sort 仅支持 `newest`（默认 created_at/id 倒序）、`title`（title/id 升序），不预设热度统计字段。筛选 course_id 等也必须验证 ID 形式。`/resources/mine` 固定路由先于 `/{id}` 注册。

## 7. 审核（后续切片）

| 方法与路径 | 输入 | 权限 | 成功响应 data |
| --- | --- | --- | --- |
| GET /reviews/pending | 分页；course_id? | 教师负责课程内或管理员，排除本人资源 | 200 分页 Resource，created_at/id 升序 |
| POST /resources/{id}/reviews | JSON: expected_version, decision, comment? | 授权审核人，禁止自审，资源 pending | 201 `{review: ReviewRecord, resource: Resource}` |
| GET /resources/{id}/reviews | 分页 | 资源本人、负责课程教师或管理员 | 200 分页 ReviewRecord，created_at/id 倒序 |

decision 仅 approved / rejected；comment 最多 2000 字符，拒绝时去空白后必填，通过时默认空字符串。review.resource_version 保存审核前版本，响应 resource.version_id 为审核成功后版本。

课程或分类停用时仍可查看授权待审队列并拒绝，但不能通过审核。审核结果、审核记录、通知、日志原子提交。请求携带旧版本、被撤回或已审核时返回 409；不做自动重放或隐式覆盖。

## 8. 个人学习、收藏与通知（后续切片）

| 方法与路径 | 输入 | 权限 | 成功响应 data |
| --- | --- | --- | --- |
| PUT /users/me/favorites/{resource_id} | 无 body | 当前用户；资源常规可见 | 200 Favorite，重复请求回读已有记录 |
| DELETE /users/me/favorites/{resource_id} | 无 body | 当前用户 | 200 `{resource_id, favorited:false}`，不存在也成功 |
| GET /users/me/favorites | 分页 | 当前用户 | 200 分页 Favorite + resource，created_at/id 倒序 |
| PUT /users/me/learning-records/{resource_id} | JSON: progress，0–100 整数 | 当前用户；资源常规可见 | 200 LearningRecord，不存在则创建 |
| GET /users/me/learning-records | 分页 | 当前用户 | 200 分页 LearningRecord + resource，last_accessed_at/id 倒序 |
| GET /users/me/notifications | 分页；unread_only? 布尔，默认 false | 当前用户 | 200 分页 Notification，created_at/id 倒序 |
| PATCH /users/me/notifications/{id}/read | 无 body | 仅通知接收人 | 200 Notification，重复标记保留首次 read_at |

上述路径不接受 user_id；后端从当前身份取得。收藏记录不可见不影响取消收藏；学习进度更新采用最后成功写入值，不提供多端版本合并。并发首次写入由唯一约束和安全 upsert/回读保证不重复，不捕获后忽略所有 IntegrityError。

## 9. 操作日志（后续切片）

`GET /operation-logs`：仅管理员；支持分页，actor_id?、action?（1–64 字符精确匹配）、target_type?、target_id?、created_from?、created_to?（带时区 ISO 8601，起点包含、终点不包含）。起点不得晚于终点。返回分页 OperationLog，created_at/id 倒序。仅查询，不提供创建、修改或删除日志 API。

## 10. 错误响应和状态码

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数不合法",
    "details": [{ "field": "body.progress", "message": "必须为 0 到 100 的整数" }]
  },
  "request_id": "2b6fd8ab-872c-4442-93b7-8e3e249ff3b5"
}
```

details 固定为数组；非字段错误时为空数组。Pydantic 错误需转换，不直接透传可能含密码的 input / ctx。API 未知路径、HTTP 方法不允许等错误也使用同一包络；保留必要的 WWW-Authenticate、Allow 等响应头。

| HTTP | code | 场景 |
| --- | --- | --- |
| 401 | AUTH_REQUIRED / INVALID_TOKEN / INVALID_CREDENTIALS | 未登录、令牌无效/过期、登录失败 |
| 403 | FORBIDDEN / ACCOUNT_DISABLED / SELF_REVIEW_FORBIDDEN | 角色/操作范围不符、账户停用、禁止自审 |
| 404 | NOT_FOUND | 对象不存在，或对该用户不可见 |
| 405 | METHOD_NOT_ALLOWED | 路径存在但不支持该方法 |
| 409 | USERNAME_EXISTS / COURSE_CODE_EXISTS / CATEGORY_NAME_EXISTS | 已知唯一键冲突 |
| 409 | VERSION_CONFLICT / INVALID_STATE | 资源版本过期、状态流转不合法 |
| 409 | REFERENCE_INACTIVE / COURSE_TRANSFER_REQUIRED / ADMIN_SELF_CHANGE_FORBIDDEN | 引用停用对象、课程须转移、禁止管理员自降权或自停用 |
| 422 | VALIDATION_ERROR | 字段、枚举、长度、URL、跨字段组合不合法或多余字段 |
| 503 | SERVICE_UNAVAILABLE | 健康检查失败；数据库写锁超时等临时不可用 |
| 500 | INTERNAL_ERROR | 未预期服务端错误；不泄露内部细节 |

引用 ID 不存在返回 404；引用存在但停用返回 409。只有能识别的数据库约束冲突才转换为明确的 409，其余记录异常并按 500 处理，不能把所有数据库错误都包装成“重复数据”。

客户端对 401 清理令牌并引导登录；对 403/404 展示访问结果；对 409 提示刷新当前资源再操作，不自动重试审核；对 422 定位字段；对网络超时、503 提供手动重试。登录和变更操作不由通用客户端自动重试。

## 11. 后续契约验证要求

健康检查首先使用 HTTPX 验证 200/503 与包络；后续每个切片增加对应请求/响应 schema、越权和冲突测试。业务实现后 `/openapi.json` 必须与本文件保持一致；OpenAPI 是运行时接口证据，本文件是设计基线。当前没有执行这些验证。
