# Learn-Hub

在线学习资源管理与共享平台，面向学生、教师和管理员。

任务一至任务四的设计、工程初始化、九张数据库表模型与最小联调已完成。当前首页会调用后端健康检查；业务接口、身份认证和权限规则仍按设计文档在后续阶段实现。

## 项目结构

```text
Learn-Hub/
  docs/                     # 需求、架构、数据、设计模式和 API 契约
  frontend/                 # Vue 3 + TypeScript + Vite + Nuxt UI
  backend/                  # Python + FastAPI + Pydantic + SQLAlchemy
```

- [需求与业务规则](docs/requirements.md)
- [架构设计](docs/architecture.md)
- [数据库设计](docs/database-design.md)
- [设计模式调用关系](docs/design-patterns.md)
- [API 契约](docs/api-contract.md)
- [前端配置与验证记录](frontend/README.md)
- [后端配置与验证记录](backend/README.md)

## 运行环境

本次验证环境：Windows、Node.js 24.10.0、npm 11.6.1、Python 3.12.4。前端要求 Node.js `^20.19.0 || >=22.12.0`；后端要求 Python 3.12+。不同平台和其他版本尚未逐一验证。

前后端分别安装依赖、分别启动。以下为 PowerShell 命令，每个终端保持对应服务运行；按 Ctrl+C 停止。

## 前端启动

首次安装或更新锁文件后：

```powershell
cd C:\Users\liyi\Learn-Hub\frontend
npm ci
```

日常启动：

```powershell
npm run dev
```

打开 <http://127.0.0.1:5173>。如果默认端口已占用，保留现有进程，可显式运行 `npm run dev -- --port 5174`，再打开 <http://127.0.0.1:5174>。

首页包含 Nuxt UI 卡片、徽章和按钮，挂载时请求 `/health` 并显示连接状态，可点击重试。项目采用 Vue Router 显式路由与 Nuxt UI 的独立 Vue 集成方式。

## 后端安装与启动

另开一个终端，首次安装：

```powershell
cd C:\Users\liyi\Learn-Hub\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements.lock.txt -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

首次启动先在 backend 目录初始化数据库：

```powershell
.\.venv\Scripts\python.exe -m app.db.init_db
```

日常从项目根目录启动：

```powershell
cd C:\Users\liyi\Learn-Hub
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000 --reload --reload-dir backend/app
```

API 文档：<http://127.0.0.1:8000/docs>；健康检查：<http://127.0.0.1:8000/health>。数据库未初始化时健康检查返回 503，九张表已就绪时返回 200。业务路由尚未实现。

默认配置可以直接使用。需要覆盖时，前端复制 `frontend/.env.example` 为 `.env.local`，后端复制 `backend/.env.example` 为 `.env`。前端 `VITE_` 变量可被浏览器读取，不存放密钥；后端 `.env` 不提交。

前端已配置 `/api` 和 `/health` 开发代理至 `http://127.0.0.1:8000`，后端默认关闭跨域。先启动后端，再打开首页即可查看实际连接状态。

## 构建与自动化检查

前端在 frontend 目录执行：

```powershell
npm run build
```

该命令先构建并生成组件声明，再检查 Vue 应用和 Vite 配置类型。可用 `npm run preview` 在 <http://127.0.0.1:4173> 预览产物；preview 不提供开发 API 代理。

后端在 backend 目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 验收结果与问题

任务四验证：前端 `npm run build` 与类型检查通过；后端 `17 passed in 0.77s`；独立端口下真实 HTTP 请求至后端 `/health` 和 Vite 代理 `/health` 均返回 200。测试服务已停止，临时联调数据库已删除。浏览器中的首页状态变化尚未单独验证。

2026-10-24 的实际验证记录：

| 项目 | 结果 |
| --- | --- |
| 前端依赖安装与版本锁定 | 完成，无未解决的 engine / peer dependency 冲突 |
| 前端生产构建与类型检查 | 通过 |
| Nuxt UI 浏览器验证 | 桌面首页样式、鼠标和键盘交互通过，操作范围内无控制台 warn/error |
| 后端依赖检查 | `pip check` 通过，27 项依赖版本已记录 |
| 后端实际启动 | factory 和 reload 模式启动成功 |
| 后端文档与 OpenAPI HTTP 访问 | `/docs`、`/redoc`、`/openapi.json` 均返回 200 |
| 后端自动化检查 | 16 项通过，覆盖配置、CORS、OpenAPI 和不隐式创建数据库的行为 |

前端依赖审计仍有 1 项 esbuild 间接依赖低危报告，常规 `npm audit fix` 未解决，详情见 [前端记录](frontend/README.md)。前端验证时默认 5173 被占用，因此使用临时 5174；没有停止原有占用进程。

后端测试首次遇到临时目录准备错误，沙箱内后续执行未返回；最终在本机完整重跑并通过，详情见 [后端记录](backend/README.md)。浏览器验证只覆盖当前桌面首页，尚不代表移动端、业务页面、权限或数据库功能的验证。

## 下一阶段

按功能切片实现身份认证、后端权限校验和资源业务流程，并让设计模式进入真实调用链。
