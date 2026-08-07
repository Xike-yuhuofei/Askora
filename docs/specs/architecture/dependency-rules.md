# Askora Dependency Rules

> Spec ID 范围：`DEP-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 目的

本规范定义 Askora 各系统允许的依赖方向、跨边界调用方式以及 legacy 迁移期间的限制。任何违反本文件的实现都必须先通过 ADR 修改架构，而不能由 Codex 临场决定。

## 2. 基本规则

### DEP-001：领域模块不得通过 ORM 直接写其他领域状态

跨领域业务变更必须通过以下之一发生：

- 显式 application command；
- append-only domain/learning event；
- 只读 query contract；
- 领域 owner 明确暴露的 application service。

禁止直接 import 其他领域 persistence model 后执行 INSERT/UPDATE/DELETE。

### DEP-002：公共 Schema 必须集中定义

跨系统使用的 `LearningEvent`、`AssessmentResult`、`MasteryEstimate`、`TeachingAction`、`LearningPlan`、`ReviewSchedule`、`EvidenceBundle` 等公共对象 MUST 在公共 contracts/domain schema 中有唯一版本定义。

各模块禁止复制一份“几乎一样”的本地 dataclass/Pydantic model 作为长期公共协议。

### DEP-003：领域依赖与基础设施依赖分离

领域逻辑 MUST NOT 依赖：

- FastAPI Request/Response；
- Electron；
- Redis 客户端；
- Kafka 客户端；
- 具体模型供应商 SDK；
- SQLAlchemy Session 的隐式全局状态。

上述能力应通过 adapter/port 注入。

### DEP-004：API 是 transport adapter

`apps/backend/app/api/` 只负责：

- 认证/授权；
- transport schema 校验；
- command/query 调用；
- HTTP/WebSocket/streaming 映射；
- 错误到 transport response 的转换。

API 层 MUST NOT 持有 mastery、教学策略、评分、计划或复习算法。

### DEP-005：4.8 编排不拥有 4.1～4.7 的领域规则

Orchestrator MAY 决定工作流步骤、重试、模型/工具 route，但不能把领域规则复制进 orchestration 代码。

例如：

- “什么时候从 hint L2 升到 L3”属于 4.5；
- “评分 0.8 是否 evidence eligible”属于 4.4/证据合同；
- “下次复习 3 天后”属于 4.7；
- orchestrator 只能执行这些结果。

### DEP-006：同步 query，异步反馈

读取最新 snapshot MAY 使用同步 query；跨系统产生新的状态反馈 SHOULD 通过 command/event 形成新版本。

不允许为了方便把整个闭环实现成一个巨大 service method，在一个调用栈内修改所有系统表。

## 3. 允许依赖矩阵

符号：

- `Q`：只读 query；
- `C`：可发 command；
- `E`：可发/消费 event；
- `X`：执行已决定动作；
- `-`：无直接业务依赖。

| From \ To | 4.1 | 4.2 | 4.3 | 4.4 | 4.5 | 4.6 | 4.7 | 4.8 |
|---|---|---|---|---|---|---|---|---|
| 4.1 Content | - | E/Q | E/Q | E/Q | - | E/Q | - | E |
| 4.2 Retrieval | Q | - | - | Q | E | - | - | E/X |
| 4.3 Learner | Q | - | - | Q | E/Q | E/Q | E/Q | E |
| 4.4 Assessment | Q | Q | Q/E | - | E | - | E | C/E |
| 4.5 Teaching Policy | Q | C | Q | Q | - | Q | Q | C |
| 4.6 Planner | Q | - | Q | - | E | - | Q | C/E |
| 4.7 Review | - | - | Q/E | Q | E | E | - | E |
| 4.8 Orchestration | Q | C | E | C | C | C | C | - |

矩阵表示允许出现的**逻辑协作**，不意味着允许互相 import 内部实现。

## 4. Python 包依赖规则

目标结构下：

```text
contracts  ← 所有领域可以依赖
    ↑
domains/*  ← 可依赖自己的 domain + contracts + ports
    ↑
orchestration ← 可依赖各领域公开 application ports/contracts
    ↑
api/workers ← 可依赖 orchestration/application facade

infrastructure → 实现 domains/orchestration 定义的 ports
```

### DEP-020

`domains/<A>/` MUST NOT import `domains/<B>/internal_*`、repository implementation 或 ORM persistence model。

### DEP-021

跨领域只允许依赖对方的：

- public contract；
- public query interface；
- public command interface；
- event schema。

### DEP-022

`infrastructure/` 可以依赖具体数据库/Redis/模型 SDK；domain 不得反向依赖 infrastructure implementation。

### DEP-023

`api/` 不得直接调用 repository；必须通过 application/orchestration facade。

## 5. 事务规则

### DEP-030：单 owner 事务

一个领域事务 SHOULD 只修改该领域拥有的业务状态，加上同一事务中的 Outbox/Event record。

### DEP-031：Transactional Outbox

需要可靠向其他系统传播的关键事件 MUST 与领域状态更新在同一事务写入 outbox。

### DEP-032：消费者至少一次语义

事件消费者 MUST 假设至少一次交付，因此必须幂等。

### DEP-033：禁止分布式事务作为默认方案

v0.2 禁止为跨领域一致性引入 2PC/分布式事务。采用：

```text
local transaction
→ outbox
→ idempotent projection/consumer
→ eventual convergence
```

## 6. 当前 Legacy 代码的依赖治理

### DEP-040：现有 service 可以暂存，但不能扩大越权

以下现有路径在迁移期允许保留：

- `app/services/documents/`
- `app/services/assessment/`
- `app/services/kt/`
- `app/services/dkt/`
- `app/services/knowledge_graph/`
- `app/engines/`
- `app/services/dialog/`

修 bug 可以在原位置进行，但新增架构能力 SHOULD 放入目标边界或通过 adapter 包装。

### DEP-041：Socratic 逻辑拆分方向

`engines/socratic/strategy_selector.py` 中与“选择教学动作”有关的逻辑最终归 4.5；语言生成、提示表达、guardrail 执行归 4.8。

### DEP-042：Documents 拆分方向

`services/documents/` 中：

- parser/document model/provenance → 4.1；
- retrieval/ranking/EvidenceBundle → 4.2；
- 文件存储 → infrastructure；
- injection/security scan → 4.8/shared security adapter，但不得改变知识业务语义。

### DEP-043：KT/DKT

`services/kt/` 与 `services/dkt/` 不能分别持有不同 learner truth。

- 4.3 MUST 有一个 canonical state projector；
- DKT 若保留，只能作为 challenger/辅助预测；
- 任何 challenger 输出必须通过 4.3 接纳规则后才能影响 canonical MasteryEstimate。

## 7. 禁止依赖

### DEP-050

4.4 Assessment MUST NOT 调用 4.3 repository 直接更新 mastery。

### DEP-051

4.8 Orchestrator/LLM MUST NOT 调用 4.3/4.6/4.7 repository 直接更新状态。

### DEP-052

4.6 Planner MUST NOT 调用 4.5 private strategy implementation 决定提示/讲解。

### DEP-053

4.2 Retrieval MUST NOT 调用 4.3 写接口，也不得生成 LearnerState 副本作为长期状态。

### DEP-054

4.7 Review MUST NOT 修改 LearningPlan；它只能发布 due/risk，4.6 决定是否进入实际计划。

### DEP-055

任何领域模块 MUST NOT 以聊天文本解析结果直接更新关键业务状态；必须先形成对应 command/evidence/result。

## 8. 自动化验证建议

代码库 SHOULD 建立 architecture tests，至少验证：

- `domains/` 不 import `api/`；
- `domains/` 不 import `infrastructure/` implementation；
- 4.4 不 import 4.3 persistence；
- 4.8 不 import 4.3/4.6/4.7 persistence；
- legacy direct paths 数量随迁移单调减少。

若使用 import-linter、grimp 或自定义 AST 测试，需要 ADR/Spec 明确批准新增生产/开发依赖；也可先用 Python AST 标准库实现，无需新增依赖。
