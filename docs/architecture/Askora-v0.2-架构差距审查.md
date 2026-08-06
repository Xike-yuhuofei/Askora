# Askora v0.2 架构差距审查

> 审查日期：2026-08-06  
> 审查对象：当前 Askora 仓库实现与[《个人 AI 辅助学习平台设计方案》v0.2](../product-design/个人AI辅助学习平台设计方案.md)执行基线  
> 审查性质：代码现状审查与实施排序，不代表功能已经完成  
> 测试基线：后端 `pytest` 共 63 项通过，0 项失败，存在 4 条非阻断弃用/临时目录清理警告

---

## 1. 执行结论

当前代码已经具备一个结构良好的 AI 教学应用原型：FastAPI 服务边界清楚，教学引擎接口已抽象，Orchestrator 具备初步的统一编排能力，文档解析、RAG、测评、知识追踪、鉴权、迁移与测试也已有独立模块。

但当前实现仍存在两套教学主链路，学习状态主要由引擎直接给出的浮点增量更新，测评、RAG、知识追踪与复习尚未形成可审计的学习证据闭环。因此，它符合“可验证原型”的工程水平，尚不符合 v0.2 定义的“证据驱动、可恢复、可迁移、可评估”的生产级 AI 教学架构。

最关键的判断不是“是否使用了足够多的 AI 技术”，而是：

1. 学习行为是否先形成不可歧义的事件与证据；
2. 所有教学交互是否经过同一编排、策略和状态提交路径；
3. 掌握度是否可以追溯到题目、作答、帮助、来源和延迟验证；
4. AI 输出、文档处理与后台任务是否能重试、回放和恢复；
5. 教学效果是否有独立于模型主观判断的测量与发布门槛。

当前五项均未完整满足。M0—M3 应优先解决这些基础问题，不应先扩展更多引擎或复杂多智能体能力。

---

## 2. 当前实现的可保留基础

| 现有能力 | 判断 | v0.2 处理方式 |
|---|---|---|
| FastAPI API、Service、Model 分层 | 基础清晰，可继续演进 | 保留，并把学习事件、证据投影和作业系统纳入领域层 |
| `TeachingEngine` / TEI 接口 | 已形成可替换的教学引擎边界 | 保留，收紧输入输出 Schema，禁止直接表达任意掌握度增量 |
| Orchestrator | 已具备路由、共享上下文与统一副作用入口的雏形 | 升级为唯一主链路，并接入数据库事务、事件存储与 Outbox |
| Socratic、Explain、Inquiry、Quiz、Drill 引擎 | 覆盖核心教学交互类型 | 保留教学策略；测评与状态更新改用正式契约 |
| 文档安全扫描、解析、分块与 RAG 服务 | 已有知识接入基础 | 增加文档修订、内容哈希、稳定定位、检索版本和引用契约 |
| SQLAlchemy / Alembic | 适合桌面优先的持久化演进 | 继续使用；所有新状态必须通过迁移创建，不在运行时隐式建表 |
| Redis 可选能力 | 可作为缓存、分布式协调或后续服务化基础 | 桌面版不得依赖 Redis 才能保证正确性，SQLite 是本地事实源 |
| 后端自动化测试 | 当前 63 项全部通过 | 保留为回归基线，增加契约、重放、故障恢复与教学质量测试 |

---

## 3. 目标架构与代码现状对照

| v0.2 目标 | 当前代码 | 差距等级 | 结论 |
|---|---|---:|---|
| Orchestrator 是普通与流式对话的唯一主链路 | 普通对话按开关选择 Orchestrator；默认仍直连 Socratic；流式路径直连 Socratic | P0 | 必须统一 |
| 学习事件是唯一可回放事实源 | 主要保存会话消息与聚合掌握度，无版本化事件信封 | P0 | 必须新增 |
| 掌握度来自合格的学习证据投影 | 多处直接应用模型或引擎给出的浮点增量 | P0 | 必须替换 |
| 正式评估保存题目、尝试、修订、帮助与评分来源 | 测评对象较简化，部分 Quiz 使用自由文本 JSON 和关键词评分 | P0 | 必须重构 |
| RAG 回答带稳定来源与可定位引用 | RAG 是独立 API，默认教学链路未使用；来源元数据不足以稳定回溯 | P0 | 必须接入 |
| 文档和 AI 长任务持久化、可租约、可重试、可恢复 | 文档 API 使用进程内 `asyncio.create_task`；队列 Redis `LPOP` 或内存降级 | P0 | 必须替换 |
| 状态提交具备数据库原子性与乐观并发 | Orchestrator 会话以内存/Redis 最佳努力保存，副作用缺少事件事务 | P0 | 必须补齐 |
| 学习者画像不由缺失信息武断推断 | 缺失 persona 时默认 `k12_high` | P1 | 改为未知/成人通用并提示校准 |
| KT、DKT、评估与对话共享同一证据源 | 各模块独立维护 Redis/内存状态，未形成统一投影 | P1 | 合并读写边界 |
| 模型选择基于能力、隐私和结构化输出 | 当前以自由文本 Provider 路由和手工 JSON 解析为主 | P1 | 增加能力注册与 Schema 校验 |
| QTI、CASE、Caliper 具备映射边界 | 当前模型没有标准 ID、版本和适配器 | P1 | 先内部契约，再建适配层 |
| WCAG 2.2 / UDL 3.0 可测试 | 前端尚无系统可访问性门槛；知识图谱页仍是占位页 | P1 | 纳入 UI 测试和发布门槛 |

---

## 4. P0 差距与代码证据

### P0-1：存在两套教学主链路

**代码证据**

- `apps/backend/app/services/dialog/dialog_service.py:58-65`：是否使用 Orchestrator 由会话 metadata 或环境变量决定。
- `apps/backend/app/services/dialog/dialog_service.py:183-223`：未启用时直接调用 Socratic，并直接修改 `mastery_estimate`。
- `apps/backend/app/services/dialog/dialog_service.py:412-468`：流式响应继续绕过 Orchestrator。
- `apps/backend/app/services/dialog/dialog_service.py:270-286`：服务层通过私有 `_sessions` 访问编排器状态。

**风险**

相同输入在普通、开关模式和流式模式下可能产生不同策略、状态提交、审计和掌握度结果。后续任何安全规则、引用规则或评测规则都要实现多次，很容易漂移。

**验收条件**

- 所有用户消息只调用一个公开的 `Orchestrator.run_turn()` / `stream_turn()` 边界；
- 删除运行时教学路径开关，保留兼容迁移期的显式测试适配器；
- `DialogService` 不访问 Orchestrator 私有成员；
- 普通与流式模式产生同构的最终事件、引用、使用量和状态投影；
- 建立路径一致性集成测试。

### P0-2：缺少学习事件、尝试与证据事实源

**代码证据**

- `apps/backend/app/models/dialog.py:56-118`：会话只保存一个标量 `mastery_estimate`。
- `apps/backend/app/models/dialog.py:129-199`：消息没有关联事件、评估尝试、证据、引用修订或 Schema 版本。
- `apps/backend/app/engines/base.py:179-212`：引擎副作用允许返回任意 `mastery_updates`，结果结构未表达证据资格。
- `apps/backend/app/services/dialog/dialog_service.py:216-223`：直接把引擎的 `mastery_delta` 加到会话标量。

**风险**

系统无法回答“为什么判定已掌握”“这次变化源于哪道题”“是否使用了提示”“算法升级后如何重算”等基本审计问题，也无法区分回忆、迁移、解释和受助完成。

**验收条件**

- 新增版本化 `LearningEventEnvelope`、`AssessmentAttempt`、`LearnerEvidence`；
- 每个状态变化可以追溯到事件 ID 和证据 ID；
- 引擎只能提出教学动作和候选观测，不能直接写掌握度；
- 投影可从事件重新构建，并与在线投影结果一致；
- 幂等键、期望版本和冲突策略有自动化测试。

### P0-3：Quiz / Drill 尚未构成可靠评估系统

**代码证据**

- `apps/backend/app/models/assessment.py`：题目只关联单个知识点，结果以聚合分数和 JSON 明细为主，缺少完整尝试修订、帮助轨迹、来源和评分器版本。
- `apps/backend/app/engines/quiz_engine.py:323-418`：使用提示词要求模型返回 JSON，再从自由文本/Markdown 中手工解析。
- `apps/backend/app/engines/quiz_engine.py:434-459`：部分答案使用字符串或关键词规则判分。
- `apps/backend/app/engines/quiz_engine.py:228-241`：以整组正确率阈值生成固定掌握度增量。
- `apps/backend/app/engines/drill_engine.py:331`、`:589`：练习结果同样通过固定副作用增量影响掌握度。

**风险**

题目生成、判分与掌握度更新的误差被叠加；模型输出格式漂移会造成静默降级；关键词命中不能可靠证明理解，更不能证明迁移。

**验收条件**

- 题目生成必须通过 JSON Schema / 类型校验，失败时显式重试或降级；
- 每次作答生成不可变 `AssessmentAttempt`，包含题目修订、响应、帮助、耗时、评分器和来源；
- 只有符合证据资格矩阵的尝试才能产生 `LearnerEvidence`；
- 客观题采用确定性评分，开放题采用 rubric、置信度和人工复核策略；
- 不再由 Quiz / Drill 直接返回掌握度增量。

### P0-4：RAG 未进入教学闭环，来源不能稳定回溯

**代码证据**

- `apps/backend/app/services/documents/rag_service.py:94-168`：RAG 作为独立检索服务存在。
- `apps/backend/app/services/documents/rag_service.py:189-247`：当前主要采用关键词匹配与简化评分。
- `apps/backend/app/models/document.py`：缺少强制的内容哈希、解析器版本、分块器版本、索引修订与稳定定位字段。
- 默认 `DialogService -> SocraticEngine` 路径没有检索、引用和来源许可步骤。

**风险**

系统虽能“检索”，却无法保证教学回答真正基于学习者资料；文档重传或重新分块后，旧引用可能失效；检索内容中的指令可能被模型当作系统指令执行。

**验收条件**

- 文档、修订、文块和检索运行都有稳定 ID 与版本；
- Orchestrator 在需要事实依据时显式调用检索，并把检索运行 ID 传给引擎；
- 最终回答的每条实质性来源声明映射到可点击定位；
- 未检索到支持材料时不得伪造引用；
- 检索内容始终作为不可信数据处理，具备注入测试集。

### P0-5：后台任务不能跨进程恢复

**代码证据**

- `apps/backend/app/api/v1/documents.py:348-388`：文档处理通过 `asyncio.create_task` 启动，进程退出后任务与状态可能丢失。
- `apps/backend/app/workers/task_queue.py:95-203`：队列使用 Redis 或内存降级；Redis 获取采用 `LPOP`，没有数据库租约、认领超时与恢复扫描。

**风险**

桌面应用关闭、更新、崩溃或系统休眠时可能留下永久处理中状态；任务被取出后进程崩溃会丢失；用户无法可靠重试或解释失败原因。

**验收条件**

- SQLite `jobs` 表是桌面版持久化事实源；
- 任务具备 `queued/running/succeeded/failed/cancelled`、租约、重试次数、幂等键和错误摘要；
- 启动时回收过期租约并继续安全任务；
- 文档处理、嵌入、重建索引均可重入；
- 强制终止进程后的恢复测试通过。

### P0-6：Orchestrator 状态提交不是数据库原子事务

**代码证据**

- `apps/backend/app/engines/orchestrator.py:52-75`：会话保存在进程内字典，并以 Redis Repository 作最佳努力持久化。
- `apps/backend/app/engines/orchestrator.py:147-209`：执行引擎后直接应用副作用，未在同一数据库事务中提交事件、消息、Outbox 和投影版本。
- `apps/backend/app/engines/repository.py`：Redis 不可用时回退内存，正确性依赖进程生命周期。

**风险**

消息写入成功但学习状态失败、或状态成功但响应未记录时，会产生不可修复的部分提交；并发请求可能覆盖新状态。

**验收条件**

- 一个教学回合的输入事件、输出事件、消息、证据和投影版本在同一数据库事务提交；
- 外部调用使用 Outbox / Inbox 或等价模式隔离；
- 使用 `expected_version` 或数据库版本列防止丢失更新；
- Redis 只承担缓存或协调，不是桌面正确性的必要条件；
- 建立重复提交、并发回合、提交中断测试。

---

## 5. P1 差距

### P1-1：默认学习者画像带有未经确认的年龄假设

`apps/backend/app/services/dialog/dialog_service.py:405-410` 在画像缺失时返回 `k12_high`。这会影响语言难度、示例、隐私和安全策略。默认值应改为 `unknown` 或 `adult_general`，由首次校准、明确设置或可靠上下文决定；年龄相关策略不得仅依赖模型推断。

### P1-2：评估、KT、DKT 与会话状态各自维护真相

`assessment_service.py`、`knowledge_tracing_service.py` 和 `dkt_service.py` 分别维护 Redis/内存状态；对话又维护会话标量。简化 KT 可以作为首期投影算法保留，但输入必须统一来自 `LearnerEvidence`。现有 DKT 是实验性启发式服务，并非训练、校准、漂移监控完整的深度知识追踪模型；在有足够纵向数据前，应标记为实验功能，不进入生产掌握度决策。

### P1-3：模型路由缺少能力、隐私与结构化输出契约

`apps/backend/app/services/llm/model_router.py` 已统一多个 Provider，但主要输出仍是自由文本，业务层手工提取 JSON。需要增加模型能力注册表，至少表达结构化输出、工具调用、上下文上限、数据离境策略、超时与成本等级。教学决策输出必须经过类型校验，不能把“JSON 看起来可解析”视为契约成功。

### P1-4：教育标准尚未形成内部映射点

当前数据模型没有稳定的题目修订、学习标准关联、Caliper 事件映射和 QTI 导入导出边界。v0.2 不要求首期完整实现所有标准，但内部 ID、版本和语义必须能无损映射，避免后期被现有表结构锁死。

### P1-5：可访问性与 UDL 尚未进入工程门槛

前端已有基本页面与交互，但没有看到系统性的键盘操作、焦点管理、语义化状态、对比度、减少动画或屏幕阅读器回归门槛。`apps/frontend/src/pages/Knowledge.jsx:13` 仍是“知识图谱建设中”占位页。知识图谱可视化不应成为核心学习链路的前置依赖；先提供可访问的列表、搜索与关系文本表达。

---

## 6. 组件处置清单

### 保留

- FastAPI / SQLAlchemy / Alembic 技术栈；
- TEI 的引擎可替换思想；
- Orchestrator 的统一编排职责；
- Socratic、Explain、Inquiry 的教学策略实现；
- 文件安全扫描、解析器注册和 RAG 服务边界；
- 现有鉴权、异常处理、指标和自动化测试基础。

### 修改

- `DialogService`：退化为 API 协调层，所有教学回合统一调用 Orchestrator；
- `EngineStepResult`：改为版本化结构，返回教学动作、候选观测、引用需求与 UI 意图；
- `Orchestrator`：接管事件事务、证据资格、投影和 Outbox；
- `QuizEngine` / `DrillEngine`：只负责出题、交互与候选评分，不直接更新掌握度；
- Document / Chunk / RAG：增加修订、稳定定位、检索运行和引用；
- Model Router：增加能力注册、隐私路由和结构化输出校验；
- KT：从统一证据投影，不再接受分散业务服务的直接写入。

### 暂停或降级

- 默认直连 Socratic 的生产路径；
- 依赖内存或 Redis 的学习状态事实源；
- 未经验证的 DKT 对生产掌握度的影响；
- 由模型自由输出掌握度增量；
- 用关键词命中替代正式开放题 rubric 评分；
- 在核心闭环完成前扩张多智能体数量或自主工具权限。

### 新增

- 学习事件、评估尝试、学习证据、知识投影领域模型；
- SQLite 事件存储、投影器、Outbox、持久化作业与租约；
- 文档修订、检索运行、引用与来源许可模型；
- FSRS 风格复习状态，以及与掌握投影分离的记忆调度器；
- Prompt / Policy 注册表和离线评测夹具；
- QTI、CASE、Caliper 的适配层；
- WCAG / UDL 自动化和人工验收清单。

---

## 7. 推荐实施顺序与文件落点

### M0：契约和迁移基线

建议新增：

```text
apps/backend/app/domain/learning_events.py
apps/backend/app/domain/assessment_contracts.py
apps/backend/app/domain/evidence.py
apps/backend/app/models/learning.py
apps/backend/app/services/learning/event_store.py
apps/backend/app/services/learning/evidence_service.py
apps/backend/app/services/learning/projection_service.py
apps/backend/alembic/versions/<revision>_learning_event_baseline.py
```

首个迁移至少创建：`learning_events`、`assessment_attempts`、`learner_evidence`、`learner_knowledge_projections`、`outbox_messages`、`jobs`。先完成数据契约、序列化、幂等与重放测试，不改变用户可见教学行为。

### M1：统一教学主链路

主要修改：

```text
apps/backend/app/services/dialog/dialog_service.py
apps/backend/app/engines/base.py
apps/backend/app/engines/orchestrator.py
apps/backend/app/engines/repository.py
apps/backend/app/api/v1/dialog.py
apps/backend/app/api/v1/ws.py
```

普通、流式和 WebSocket 必须共享同一运行内核。保留流式 token 体验，但最终状态只在经过校验并持久提交后生效。

### M2：RAG 与来源闭环

主要修改：

```text
apps/backend/app/models/document.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/documents/rag_service.py
apps/backend/app/engines/orchestrator.py
apps/frontend/src/pages/Knowledge.jsx
```

先支持一个可验证的资料问答场景：导入文档、持久任务处理、检索、教学回答、可点击引用、文档修订后旧引用仍可解释。

### M3：评估与掌握证据闭环

主要修改：

```text
apps/backend/app/models/assessment.py
apps/backend/app/services/assessment/assessment_service.py
apps/backend/app/services/kt/knowledge_tracing_service.py
apps/backend/app/engines/quiz_engine.py
apps/backend/app/engines/drill_engine.py
```

用 `AssessmentAttempt -> LearnerEvidence -> Projection` 代替所有直接掌握度增量；建立无提示正确、提示后正确、迁移题、延迟复测等不同证据权重。

### M4—M5：复习、评测和生产门槛

在证据链稳定后再接入 FSRS 风格调度、N-of-1 效果评估、模型切换回归、安全红队、WCAG/UDL 门槛和备份恢复演练。

---

## 8. 首个垂直切片验收场景

建议用下面一条用户旅程作为架构验收，而不是同时改造全部页面：

1. 用户导入一份带页码或章节的学习资料；
2. 持久化作业完成解析、分块和索引，重启应用后仍可继续；
3. 用户针对一个知识组件提问，Orchestrator 检索资料并给出可点击引用；
4. 系统生成一题经过 Schema 校验且带来源的检查题；
5. 用户首次回答错误，查看一级提示后修正；
6. 系统保存两次完整尝试，只生成“受助完成”的有限证据，不判定完全掌握；
7. 隔日安排无提示复测；
8. 复测成功后生成新的回忆证据，并更新可追溯的知识投影；
9. 任意时刻可从事件重建相同状态，并解释每次掌握变化的来源。

该场景通过，才说明 Askora 真正形成了“资料—教学—评估—证据—复习”的最小闭环。

---

## 9. 发布阻断项

在以下条件满足前，不应把当前实现描述为生产级自适应学习系统：

- 仍有用户流量绕过 Orchestrator；
- 掌握度仍可由 LLM 或教学引擎直接增加；
- 作答没有完整尝试与帮助轨迹；
- 引用不能回到稳定的文档修订与位置；
- 文档处理或学习状态在进程退出后可能丢失；
- 无法从事件重建学习状态；
- 缺少模型切换、提示注入、备份恢复和可访问性发布门槛；
- 教学效果只有满意度或模型评分，没有学习增益和延迟保持证据。

---

## 10. 本轮交付边界

本审查已经把产品设计中的目标架构落到当前仓库的具体代码与实施顺序，并建立后续重构的验收基线。本轮未修改运行时代码、数据库结构或用户数据；下一执行阶段应从 M0 的领域契约、迁移与重放测试开始。
