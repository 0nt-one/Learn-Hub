# Learn-Hub 设计模式与调用关系

状态：设计基线 v1，待确认。本文描述后续真实用例的接入点，不创建演示类。工程初始化阶段只实现数据库工厂；另外三种模式随业务切片落地并以调用链测试验收。

## 1. 工厂：统一创建数据库访问基础设施

| 角色 | 计划名称 | 职责 |
| --- | --- | --- |
| 调用者 | create_app / init_db / pytest fixtures | 按配置取得一组数据库运行对象 |
| 简单工厂 | create_database(database_url) | 创建 engine，注册连接事件，创建 sessionmaker |
| 产品 | DatabaseRuntime | 持有 engine 和 session_factory，提供 dispose 生命周期 |

这是简单工厂函数，不将其包装成没有多态需要的 GoF Factory Method 层级。

真实调用关系：

```text
create_app(config)
  → create_database(config.database_url)
    → engine + 每连接 foreign_keys=ON + sessionmaker
  → app.state.database
  → get_session（每请求创建/关闭 Session）
  → health service → health repository → SQLAlchemy → SQLite

python -m app.db.init_db → 同一工厂 → Base.metadata.create_all
pytest fixture → 同一工厂（独立临时库）→ HTTPX 请求应用
```

选型理由：避免应用、初始化脚本、测试分别创建连接而遗漏 SQLite 外键配置；数据库路径、超时和连接生命周期集中维护。不为尚不存在的多数据库实现创建抽象工厂。

验收：健康检查、初始化和约束测试均使用该工厂；测试验证 PRAGMA 和外键错误确实生效。

## 2. 责任链：资源提交前的顺序检查

| 角色 | 计划名称 | 检查内容 |
| --- | --- | --- |
| 调用者 | ResourceService.submit | 加载当前用户和资源，创建提交上下文 |
| 上下文 | SubmissionContext | user、resource、course、category、expected_version、session |
| 处理节点一 | OwnerCheck | 当前账户启用、角色为学生/教师且为所有者 |
| 处理节点二 | StateVersionCheck | 状态为 draft/rejected，版本匹配 |
| 处理节点三 | PlacementCheck | 课程和分类启用 |
| 处理节点四 | MetadataCheck | 调用资源类型策略校验元数据 |
| 链执行器 | SubmissionPipeline | 顺序执行，首个失败抛稳定业务异常 |

采用有序处理器列表即可；每个节点只校验，不写库、不 commit。链执行完毕后才由 service 将状态改为 pending、递增版本并记录日志。

```text
POST /resources/{id}/submit
  → 认证依赖 → ResourceService.submit
  → OwnerCheck → StateVersionCheck → PlacementCheck
  → MetadataCheck → ResourceValidationStrategy.validate
  → resource.status=pending → OperationLog → commit
```

选型理由：顺序影响错误语义，且检查将随资源类型和共享规则扩展。责任链减少一个巨型提交函数，保留失败即停止的行为。它不能替代路由认证或其他业务入口的授权。

验收：越权请求不执行后续策略；停用分类阻止提交；任何节点失败不得改变资源状态或写入成功日志。

## 3. 策略：按资源类型校验元数据

| 角色 | 计划名称 | 行为 |
| --- | --- | --- |
| 策略协议 | ResourceValidationStrategy | validate(resource_metadata)；成功无返回，失败业务异常 |
| 文档策略 | DocumentValidation | duration 为空，page_count 可空或为正整数 |
| 视频策略 | VideoValidation | duration 为正整数，page_count 为空 |
| 链接策略 | LinkValidation | duration、page_count 均为空 |
| 选择器 | validator_for(resource_type) | 通过显式映射取策略，未知类型拒绝，不动态导入 |
| 调用者 | ResourceService.create/update、MetadataCheck | 输入模型转换后调用，并由提交链复验 |

共同的标题、描述、HTTPS URL 等基础规则由 Pydantic schema 承担；策略负责类型差异，数据库跨字段 CHECK 兜底。策略不访问远程链接，不推断资源内容是否合法或真实存在。

```text
创建/编辑 API → Pydantic 公共规则 → ResourceService
  → validator_for(type) → 对应 validate → repository

提交 API → SubmissionPipeline.MetadataCheck
  → 同一 validator_for(type) → 对应 validate
```

选型理由：创建、编辑和提交共享类型规则，新增资源类型时只增加策略及显式映射、枚举和约束迁移。若未来类型规则仍很简单，可使用同协议函数，避免为了模式数量堆叠类。

验收：三个类型各有正反例，新增未知类型返回 422；两条调用路径不得出现不同的规则。

## 4. 观察者：审核结果触发站内通知和审计日志

| 角色 | 计划名称 | 行为 |
| --- | --- | --- |
| 发布者 | ReviewService.review | 校验范围、禁止自审、状态与版本；写审核结果 |
| 事件 | ResourceReviewed | review_id、resource_id、owner_id、reviewer_id、decision、request_id |
| 同步分发器 | DomainEventDispatcher | 应用装配时显式注册处理器，按固定顺序调用 |
| 观察者一 | ReviewNotificationHandler | 用传入 Session 为资源拥有者新增通知 |
| 观察者二 | ReviewAuditHandler | 用同一 Session 新增 resource.review 操作日志 |

```text
POST /resources/{id}/reviews
  → 认证与审核权限 → ReviewService.review
  → 开启事务 → 检查 expected_version 与 pending
  → 更新状态 + 插入 ReviewRecord + flush（取得 review_id）
  → publish(ResourceReviewed, session)
      → ReviewNotificationHandler → Notification
      → ReviewAuditHandler → OperationLog
  → commit
```

选型理由：审核服务关心审核规则，通知与审计响应同一事件，新增事务内反应不会扩展审核函数。此处使用同步、进程内观察者，适合 SQLite 单实例；它不是持久化消息队列，也不保证跨进程事件投递。

处理器不得吞异常或自行 commit。任意观察者失败，外层整个审核事务回滚。审计只由观察者写一次，service 不重复写；通知唯一约束防止同一次审核重复插入。请求重试由资源版本和审核唯一约束阻止重复审核。

后续如需邮件、Webhook 等外部副作用，应增加事务 outbox 和异步消费者，不在当前事务里调用外部服务，也不先 commit 再依靠内存事件保证通知必达。

验收：审核成功同时出现审核记录、状态、通知和日志；模拟任一观察者失败后四者均回滚；双并发审核只产生一个结果。

## 5. 模式协作与实施顺序

数据库工厂供全应用使用；提交责任链内部调用元数据策略；审核服务发布事件驱动通知和审计观察者。它们分别解决对象创建、一组顺序校验、类型行为变化和一个结果的多个响应。

1. 工程初始化阶段接入并验证数据库工厂和健康检查。
2. 资源创建与提交切片同时接入策略和责任链，不单独提交无业务调用的模式示例。
3. 审核切片同时实现审核记录、通知、日志和观察者原子事务。

所有类名是设计名称，可在实现时调整；必须保留调用关系和业务验收行为。当前没有实现代码或测试结果。
