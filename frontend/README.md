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

## 页面架构（布局阶段）

- `src/assets/main.css`：设计令牌、基础元素和通用无障碍规则；不放某一页的卡片布局。
- `src/layouts/StudentLayout.vue`：学生端顶栏、内容宽度和页脚。
- `src/layouts/DashboardLayout.vue`：教师和管理员共用的侧栏、工具栏及移动抽屉；`TeacherLayout.vue` 与 `AdminLayout.vue` 提供角色导航配置。
- `src/components/common/`：`BaseCard` 提供卡片表面与插槽，`EmptyState` 和 `StatCard` 提供状态展示，`ServiceHealthPanel` 单独负责真实健康检查。
- `Breadcrumbs` 接收页面层级数组；首页不显示，后台布局默认显示“首页 / 当前页”，学生端后续页面可通过布局插槽传入。
- `src/pages/`：只组合布局和内容组件；页面特有的 Hero 与 Bento 样式留在页面内。

`/` 为学生首页，`/teacher`、`/admin` 为工作台**布局预览**。后两页没有业务权限和数据接入，正式接入时需增加认证与路由守卫，并以服务端授权为准。规划中的侧栏项目只显示文字，不提供无效链接。

## 当前验证状态

任务四验证：`npm run build` 与 Vue/TypeScript 类型检查通过；真实启动 Vite 与后端后，Vite 代理的 `/health` 返回 200。浏览器内的首页状态切换尚未单独验证。

2026-10-24，任务二第 2 步已执行：

- `npm install --strict-peer-deps` 成功，安装 363 个依赖包，未报告 engine 或 peer dependency 冲突。
- `npm ls --depth=0` 成功，9 项直接依赖均与固定版本一致；`package-lock.json` 与 `package.json` 对照检查通过。
- JSON 配置解析、必要文件和 UTF-8 文本检查通过。

依赖审计仍报告 1 项低危漏洞：[esbuild GHSA-g7r4-m6w7-qqqr](https://github.com/advisories/GHSA-g7r4-m6w7-qqqr)。当前链路为 `@nuxt/ui → @nuxt/fonts → fontless → esbuild@0.27.7`；上游 fontless 使用 `^0.27.0` 约束。已执行不带 `--force` 的 `npm audit fix --strict-peer-deps`，未能消除该报告。后续需评估上游更新或经兼容性验证的修复方案。

2026-10-24，任务二第 3 步实际验证结果：

| 检查项 | 实际结果 |
| --- | --- |
| `npm run build` | 退出码 0；Vite 8.3.5 完成生产构建，753 个模块转换并生成 dist |
| build 内的 `vue-tsc` 和 `tsc` | 均通过；分别检查 Vue 应用和 Vite 配置 |
| `npm run preview` | 成功在本机回环地址 4173 启动；浏览器正常显示首页 |
| Nuxt UI 样式 | 1280 × 720 桌面视口中，卡片、徽章和按钮显示正常；没有横向溢出 |
| 组件交互 | 生产页面鼠标点击两次、键盘 Enter 一次，计数显示“已响应 3 次点击” |
| 首页链接 | 点击 Learn-Hub 链接仍在首页，组件计数保留 |
| 生产页面控制台 | 本次操作范围内未捕获 warn/error |
| 默认开发端口 | 5173 已被占用，启动按 strictPort 配置报错；未停止占用进程 |
| `npm run dev -- --port 5174` | 临时端口启动成功；浏览器点击按钮后显示“已响应 1 次点击” |
| 开发页面控制台 | 本次仅观察到 Vite connecting/connected 调试输出，未捕获 warn/error |
| `npm audit --json` 复核 | 仍有上述 1 项 esbuild 低危报告，审计命令退出码 1 |

浏览器首次无法连接沙箱内的预览服务；改为在本机 `127.0.0.1` 启动后完成验证，未修改监听配置或防火墙。截图保存到本地 `.verification/`，该目录已忽略提交。

上述结果只覆盖当前最小首页的桌面样式和交互，不代表已验证业务页面、后端联调、移动端或全部浏览器兼容性。
