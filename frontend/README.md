# Learn-Hub 前端

独立 Vue 3 + TypeScript + Vite 工程，使用 Vue Router 和 Nuxt UI 组件库。

## 安装与启动

需要 Node.js `^20.19.0 || >=22.12.0` 和 npm。在本目录执行：

```powershell
npm ci
npm run dev
```

开发地址为 <http://127.0.0.1:5173>，端口占用时直接报错，不自动切换。首页挂载时请求 `/health`，显示“检查中 / 服务正常 / 连接失败”，并可重试；请先初始化并启动后端。

若默认端口已被其他服务占用，可显式指定临时端口，不必停止现有进程：

```powershell
npm run dev -- --port 5174
```

默认配置可直接使用；需要覆盖配置时，将 `.env.example` 复制为 `.env.local` 并修改。所有 `VITE_` 变量均可被浏览器读取，不得包含密钥。

`/api` 和 `/health` 的开发代理目标默认是 `http://127.0.0.1:8000`，保留原请求路径。首页通过 `src/api/health.ts` 发起健康检查，5 秒超时。生产环境需另行配置同源反向代理，Vite preview 不提供开发 API 代理。

## 构建与类型检查

```powershell
npm run build
npm run preview
```

build 先运行 Vite，生成 Nuxt UI 的组件声明，再运行应用及 Vite 配置的 TypeScript 检查。预览地址为 <http://127.0.0.1:4173>。

已有生成声明后可单独执行 `npm run type-check`；干净检出应先执行 `npm run build`。`auto-imports.d.ts`、`components.d.ts`、`node_modules/.nuxt-ui` 均由工具生成，不手工维护。

Nuxt UI 按[官方独立 Vue 集成指南](https://ui.nuxt.com/docs/getting-started/installation/vue)配置：Vite 插件、Vue 插件、CSS 导入、`UApp` 和根容器 `isolate`。直接依赖固定版本，完整依赖树由 `package-lock.json` 锁定。

## 页面架构

- `src/assets/main.css`：唯一的主题层。`--lh-*` 是 Learn-Hub 自有令牌（品牌色、状态色、布局尺寸、装饰色），并映射到 Nuxt UI 的 `--ui-*` 语义令牌；圆角比例尺按 UI 规范重定为 8 / 12 / 20 / 24，页面不再写死色值。
- `src/layouts/StudentLayout.vue`：学生端顶栏、1440 内容宽与页脚。
- `src/layouts/DashboardLayout.vue`：教师 / 管理员共用的 `USidebar` 壳（240 展开 / 72 图标折叠、1024 断点、移动端 Slideover、折叠偏好持久化）。后台是“平铺”结构：**页面标题就是顶栏里的 `h1`**（16px），内容区直接从数据开始，不再重复标题与说明；`TeacherLayout.vue` 与 `AdminLayout.vue` 只提供角色与标题配置。
- `src/components/common/`：`BaseCard`（UCard）、`EmptyState`（UEmpty）、`StatCard`（UCard）、`ServiceHealthPanel`（UCard + UBadge + 真实健康检查）、`AppBrand`（CSS 品牌标记）、`PageHeader`、`ErrorState`、`AsyncRegion`。
- `src/components/resources/`：`ResourceCard`（资源卡，含 loading 骨架）、`ResourceFilterPanel`（课程/分类/类型筛选）、`ResourceToolbar`（总数与排序）、`StatusBadge`（资源状态）、`ResourceTypeBadge`（document / video / link）。
- `src/components/illustrations/`：`HeroIllustration`（首屏装饰插画，纯 SVG 几何、颜色走主题令牌、无外部素材与授权问题）。换成位图插画时放在 `src/assets/illustrations/`，用 `<img>` 引入并固定宽高。
- `src/types/`：`resource.ts` 放与 API 契约一致的前端枚举和展示模型，不用数据库模型代替。
- `src/pages/`：只组合布局和内容组件；首页特有的 Hero 与 Bento 样式留在页面内。
- 后台（教师 / 管理员）**不使用面包屑**：侧栏当前项已经表达位置，再加一行会与页面标题重复。学生端在有三级页面（如资源详情）时再用 `UBreadcrumb`；学生首页与资源中心目前只有两级，顶部导航足够。

`/` 为学生首页，`/resources` 为学生资源目录，`/teacher`、`/admin` 为工作台**布局预览**。后两页没有业务权限和数据接入，正式接入时需增加认证与路由守卫，并以服务端授权为准。规划中的侧栏项目只显示文字与“规划中”徽章，不提供无效链接。

### 资源中心（已接入目录接口）

已接入 GET /resources 的标题搜索、课程/分类/类型筛选、最新/标题排序、20/40 条分页。筛选与页码保存在 URL，非法参数规整为默认值；新请求使旧响应失效，会话退出时清空结果。未登录显示登录引导，登录后返回原目录条件。

课程与分类使用启用字典，每次加载 100 条，可继续加载下一页；字典请求失败单独显示重试，不阻塞标题搜索。桌面采用左侧筛选栏，移动端采用带草稿的 Nuxt UI 抽屉；关闭放弃修改，应用后才更新结果。

卡片和列表复用 ResourceCard，点击打开 Nuxt UI 资源信息弹窗，通过 GET /resources/{id} 加载最新详情，支持加载提示、失败重试和资源不存在提示。关闭弹窗或切换会话后忽略旧请求结果。外链只允许 HTTPS，明确显示域名并在新窗口打开；详情弹窗提供收藏操作，未设置独立页面。

2026-11-10：生产构建及类型检查通过；目录 URL 的筛选往返、非法参数、长度与分页边界检查通过。真实登录数据和浏览器视觉验收由用户执行。
### 通知

学生、教师和管理员登录后均可从顶部铃铛打开通知面板。GET /users/me/notifications 支持全部/未读筛选和每页 10 条分页，PATCH /users/me/notifications/{id}/read 逐条标记已读；只在接口成功后更新状态。未读数取未读查询的 total，进入页面、打开面板、窗口重新获得焦点及可见页面每 60 秒更新。支持手动刷新、空态、失败重试，会话变化或组件卸载时忽略旧请求并清理定时器。接口暂不提供全部已读和资源跳转目标，因此不展示对应操作。

### 视觉方向

后续样式统一遵循 [Learn-Hub 视觉方向](../docs/visual-direction.md)：极简几何、蓝白品牌色，主色 #155EEF。PageHeader 必须传入英文 eyebrow，资源卡片使用克制的几何点缀，避免大面积渐变与发光效果。

### 公共组件约定

| 组件 | 状态口径 | 约束 |
| --- | --- | --- |
| `PageHeader` | 静态 props | 学生端页面用它（标题 + 说明 + 右侧动作）；后台不用，标题在顶栏里 |
| `AsyncRegion` | `status: loading / ready / empty / error / unavailable` | 单一判别字段，不允许 `loading + empty` 这类矛盾组合；`error` 时必须给 `retry` 事件 |
| `ErrorState` | 静态 props + `retry` 事件 | 只展示安全信息；`request_id` 原样显示便于报障 |
| `EmptyState` | 静态 props | `unavailable`（未接入）与 `empty`（真的没有）文案必须分开 |
| `StatusBadge` | `ResourceStatus` + `context` | 文字 + 图标，不只靠颜色；`approved` 在审核语境下读作“已通过” |
| `ResourceTypeBadge` | `ResourceType` | 只区分文档 / 视频 / 链接，不按文件格式细分 |
| `ResourceCard` | `ResourceSummary` + `loading` | 缺封面用类型渐变与图标占位；通过 open 事件交给页面展示资源信息，不在卡片内请求数据 |
| `ResourceFilterPanel` | `ResourceFilters` | 每维单选，`null` = 全部；字典分页加载，失败时可单独重试 |
| `ResourceToolbar` | `total` + `sort` | 总数只认服务端 `total`，缺失时显示 “—”，不写死 0 |

这些公共组件由当前业务页面按需要调用，实际使用情况以 `src/pages/` 和构建结果为准。

### Nuxt UI 接入台账

| 场景 | 组件 | 说明 |
| --- | --- | --- |
| 根容器 | `UApp` | `main.ts` 安装 Vue 插件 |
| 后台壳 | `USidebar` | 图标折叠、移动抽屉与抽屉焦点管理由库提供 |
| 卡片表面 | `UCard` | 边框、底色、圆角、分隔线来自主题 |
| 空 / 未接入状态 | `UEmpty` | `variant="naked"`，放在卡片内部 |
| 标签与状态 | `UBadge` | “规划中”“待接入”、健康检查状态 |
| 动作 | `UButton` | 含图标按钮与 `to` 路由链接 |
| 图标 | `UIcon` + `@iconify-json/lucide` | 构建期打包，不请求 iconify CDN |
| 面包屑 | `UBreadcrumb` | 当前未使用；留给学生端三级页面，后台不用 |

### 主题与图标配置

`vite.config.ts` 中 `ui()` 有两处非默认配置：

- `colorMode: false`：首版只有浅色设计，避免系统深色时页面自动变黑。
- `icon: { clientBundle: { scan: true } }`：把模板里出现的 `i-lucide-*` 打包进产物。

`@iconify-json/lucide` 是 devDependency，只在构建期读取图标数据。新增图标时先在模板写 `i-lucide-<name>`，名字必须存在于该图标集，否则构建会报错并列出未解析的图标。

注意：图标扫描在开发服务器启动时做一次，之后只增量扫描被修改的文件。**新建组件文件里的图标可能要重启开发服务器才会进包**；`npm run build` 不受影响。如果新图标显示成空白，先重启再判断是否为拼写问题。

## 当前检查与历史验证记录

2026-11-11：`npm run build` 与随后的 TypeScript 检查通过；用户已完成页面基本检查。以下表格记录的是较早的组件整理阶段，不代表当前构建状态。

2026-11-05，前端结构与组件层整理：

| 检查项 | 实际结果 |
| --- | --- |
| `npm run type-check` | 通过，`vue-tsc` 与 `tsc` 退出码 0（含新增组件与 `src/types`） |
| 运行中的 Vite 开发服务器 | 改动的 24 个页面/组件/样式/类型模块全部返回 200；`/resources` 入口返回 200 |
| 新增组件 | `PageHeader`、`ErrorState`、`AsyncRegion`、`StatusBadge`、`ResourceTypeBadge`、`ResourceCard`、`ResourceFilterPanel`、`ResourceToolbar` 均通过编译与类型检查 |
| `virtual:nuxt-ui-icons` | 已包含实际使用的图标，也包含库默认的 `chevron-right`、`close`，确认离线可用 |
| `virtual:nuxt-ui-plugins` | 不再包含 color-mode 插件，确认浅色主题不会被系统深色覆盖 |
| 样式产物 | 编译后的 CSS 同时包含 `--lh-*`、`--ui-*` 映射与重定后的 `--radius-*` |
| `npm run build` | 未执行（受限环境无法运行 Vite 构建） |
| 浏览器视觉验收 | 未执行（1440 / 1024 / 390 三个宽度待人工检查） |

历次记录：

- 2026-10-24：依赖安装与锁文件、`npm run build`、`npm run preview`、桌面视口渲染与控制台检查通过，覆盖的是当时的最小首页；首页此后已重写，该记录的界面部分不再代表当前实现。
- 依赖审计仍报告 1 项低危漏洞：[esbuild GHSA-g7r4-m6w7-qqqr](https://github.com/advisories/GHSA-g7r4-m6w7-qqqr)，链路为 `@nuxt/ui → @nuxt/fonts → fontless → esbuild`，上游未修复，`npm audit fix` 无效。

以上是当时的验证记录；当前代码以重新运行构建及用户的页面检查为准。
