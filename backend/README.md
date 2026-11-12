# Learn-Hub 后端

FastAPI + Pydantic 2 + SQLAlchemy 2.0.x 的独立 Python 工程，要求 Python 3.12 或以上版本。包含九张表模型、数据库初始化、`/health`、身份权限及业务接口。

## 目录与职责

```text
backend/
  pyproject.toml             # 包元数据、直接依赖及 pytest 配置
  requirements.lock.txt      # 本阶段安装后生成的运行与开发依赖版本清单
  .env.example
  app/
    main.py                 # create_app、应用状态与 CORS 装配
    core/config.py          # Pydantic Settings 配置校验
    api/v1/router.py         # /api/v1 路由装配入口
    api/health.py             # GET /health
    db/model_registry.py      # 九张模型表注册
    db/engine.py              # SQLite 连接与外键开关
    db/init_db.py             # 建表命令
    db/health.py              # 数据库就绪检查
  tests/
    test_app.py              # HTTPX ASGI / CORS 边界
    test_config.py           # 配置拒绝与路径解析
```

九个模型位于 `app/models/`。`/api/v1` 已装配认证、用户、课程、分类、资源、审核、收藏、学习记录、通知与操作日志接口。

## 环境与安装

以下 PowerShell 命令均在 backend 目录执行。依赖安装到本地 `.venv`，不修改系统 Python 的应用依赖；直接调用虚拟环境解释器，无需调整 PowerShell 执行策略。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements.lock.txt -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

`pyproject.toml` 是直接依赖的唯一来源；`requirements.lock.txt` 是本次 Windows / Python 3.12 环境解析出的确切依赖版本，作为安装约束使用，包含 pytest 和 HTTPX。其他平台仍由 pip 根据 Python 及平台标记解析，不宣称已经验证全部平台。

如需调整配置，将 `.env.example` 复制为 `.env`。系统环境变量优先于 `.env`，`.env` 优先于代码默认值。配置文件位置固定在 backend 目录，不随启动目录变化。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| APP_ENV | development | development / testing / production |
| DATABASE_URL | sqlite:///data/learn_hub.db | 文件路径相对 backend 解析为绝对路径；也支持 sqlite:///:memory: |
| CORS_ORIGINS | [] | JSON 数组；只接受精确 HTTP(S) origin，不允许通配符、凭据、查询或业务路径 |
| JWT_SECRET_KEY | 无 | 至少 32 字节的随机密钥；启动 API 时必填，保存在本地 `.env`，不要提交 |

配置校验不创建目录、连接或数据库文件。默认不启用跨域，前端通过 Vite 的 `/api` 和 `/health` 同源代理访问；需要直接跨域访问时显式填写允许的 origin。`APP_ENV` 只标识环境，不会自动配置生产部署。

## 启动方式

首次启动先将 `.env.example` 复制为 `.env` 并设置至少 32 字节的 `JWT_SECRET_KEY`，再初始化默认 SQLite 数据库（自动创建 `backend/data/` 和九张表）：

```powershell
.\.venv\Scripts\python.exe -m app.db.init_db
```

首次创建管理员时，在 backend 目录的交互终端运行下列命令。密码会隐藏输入；已有管理员时命令拒绝再次创建。不要把密码写在命令行参数中。

```powershell
.\.venv\Scripts\python.exe -m app.cli.bootstrap_admin
```

再启动 API：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

FastAPI 文档入口：<http://127.0.0.1:8000/docs>；健康检查：<http://127.0.0.1:8000/health>。健康检查执行查询并确认九张表存在；数据库未初始化或不可连接时返回 503。

## 独立演示数据

想直接浏览填充后的系统，首次可在 `backend/` 目录运行（如果演示数据库已生成，跳过第一行）：

```powershell
.\.venv\Scripts\python.exe -m app.cli.seed_demo
$env:DATABASE_URL = "sqlite:///data/learn_hub_demo.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8010 --reload
```

命令创建单独的 `backend/data/learn_hub_demo.db`，不会修改默认的 `learn_hub.db`。内含 6 位用户、5 门课程、5 个分类、14 条资源，覆盖已通过、待审核、草稿、被拒绝四种状态，以及审核通知、操作日志、收藏和学习进度。数据库文件已被 Git 忽略。再次运行会拒绝覆盖已有文件；若要重新生成，请先自行备份或移走旧的演示数据库。

所有演示账号密码都是 `LearnHubDemo2026!`：管理员 `demo_admin`；教师 `demo_chen`、`demo_wang`；学生 `demo_zhou`、`demo_li`、`demo_sun`。这些账号只适合本地演示，不要将演示数据库用于公开部署。资源的 `example.org` 地址是占位链接，不包含真实文件或视频。

前端 Vite 代理需要指向同一后端端口。在 `frontend/` 目录启动前，当前 PowerShell 窗口先执行 `$env:VITE_API_PROXY_TARGET = "http://127.0.0.1:8010"`，然后运行 `npm run dev`。切回原数据库时，关闭演示后端，在新 PowerShell 窗口不设置 `DATABASE_URL` 即可按上面的常规启动命令运行；如同一窗口继续使用，先执行 `Remove-Item Env:DATABASE_URL`。

从项目根目录启动时增加 `--app-dir backend` 并使用 `backend/.venv/Scripts/python.exe`。生产部署不使用 `--reload`，部署方案另行制定。

## 工程初始化时的历史验证记录

2026-10-24，任务二第 4 步已完成：

- 在 `backend/.venv` 创建 Python 3.12.4 虚拟环境，从官方 PyPI 安装本地工程及运行、开发依赖。
- `pip check` 退出码 0，输出 `No broken requirements found.`。
- 生成 `requirements.lock.txt`，包含 27 项确切依赖版本，不包含本地工程的绝对路径。
- `pyproject.toml` 解析和 7 个 Python 源文件的 AST 语法检查通过。该检查不执行应用代码。
- 初次创建虚拟环境时，沙箱临时目录写入失败；随后在同一项目目录重试成功，未改为全局安装。

实际安装的主要版本：

| 依赖 | 版本 |
| --- | --- |
| FastAPI | 0.162.0 |
| Pydantic | 2.14.1 |
| pydantic-settings | 2.16.1 |
| SQLAlchemy | 2.0.55 |
| Uvicorn | 0.54.0 |
| pytest | 9.1.1 |
| HTTPX | 0.28.1 |

2026-10-24，任务二第 5 步的历史验证结果：

| 检查项 | 结果 |
| --- | --- |
| 从项目根目录运行 Uvicorn factory + reload | `127.0.0.1:8000` 启动成功，日志显示 `Application startup complete` |
| HTTPX 请求 `/docs`、`/redoc` | 均返回 200，Content-Type 为 text/html；未据此宣称浏览器中的外部脚本已验证 |
| HTTPX 请求 `/openapi.json` | 返回 200，标题 Learn-Hub API，业务 paths 数量为 0 |
| HTTPX 请求 `/api/v1/health` | 当时返回预期的 404；正式健康检查位于 `/health` |
| pytest + HTTPX 自动化检查 | 本机 Python 3.12.4 / pytest 9.1.1 环境，`16 passed in 0.75s`，退出码 0 |
| 数据库副作用检查 | 没有创建默认 data 目录或数据库文件 |

首次指定测试 basetemp 时遗漏父目录，出现 6 项准备阶段错误；创建父目录后，沙箱内的完整执行未返回，已中止。随后在本机运行同一套件，16 项全部通过。以上最终通过结果来自本机实际输出，不是将早期失败忽略为成功。

## 自动化检查

在 backend 目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

2026-11-11：现有 35 项测试通过，覆盖身份权限、资源、审核、收藏、学习记录、通知及操作日志等接口。以下任务四数字是工程初始化时的历史结果。

检查覆盖：OpenAPI 可访问且不创建数据库、默认不开启跨域、允许 origin 的预检成功、不同端口和未授权 origin 被拒绝、数据库路径不依赖当前工作目录、无效数据库 URL 及不合法 CORS 配置被拒绝。

任务四在 2026-10-24 的验证结果为 `17 passed in 0.77s`，覆盖当时的健康检查与数据库初始化。该数字是历史记录，当前业务接口的检查应重新运行上述 pytest 命令。
