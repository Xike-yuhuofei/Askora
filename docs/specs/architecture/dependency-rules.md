# Askora Dependency Rules

> Spec ID 范围：`DEP-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. 目的

本规范定义各系统允许的依赖方向、跨边界调用方式以及 legacy 迁移限制。违反本文件的实现必须先通过 Design/ADR/Spec 变更，MUST NOT 由执行代理临场重定义架构。

## 2. 基本规则

### DEP-001：单一 owner 写入

领域模块 MUST NOT 通过 ORM/repository 直接写其他领域状态。跨领域变更只能通过 public command、append-only event/evidence、只读 query 或 owner application service。

### DEP-002：公共 Schema 唯一

`LearningEvent`、`AssessmentResult`、`MasteryEstimate`、`TeachingContext`、`TeachingAction`、`PolicyBundle`、`LearningPlan`、`ReviewSchedule`、`EvidenceBundle`、`OutcomeObservation`、`ExperimentAssignment` 等跨系统对象 MUST 在公共 contract 中有唯一 canonical schema；MUST NOT 复制“几乎一样”的长期本地 schema。

### DEP-003：领域与基础设施分离

Domain logic MUST NOT 依赖 FastAPI transport、Electron、Redis/Kafka client、具体模型 SDK 或隐式全局 SQLAlchemy Session；这些能力 SHOULD 通过 port/adapter 注入。

### DEP-004：API 是 transport adapter

API 只负责 auth、transport validation、command/query、HTTP/WebSocket/streaming mapping 与 error mapping；MUST NOT 持有 mastery、Teaching Policy、assessment、plan、review 算法。

### DEP-005：SYS08 执行，不拥有 SYS01～SYS07 规则

SYS08 MAY 决定 workflow/retry/model/tool route，但 MUST NOT 复制/覆盖领域规则。例如：

- “hint 从 `CONCEPTUAL_STRATEGIC` 是否升级到 `SUBGOAL` / 是否 fade scaffold”属于 SYS05；
- “某 AssessmentResult 是否可形成高权 LearnerEvidence”属于 SYS03 eligibility contract；
- “下次建议复习时间”属于 SYS07；
- SYS08 只能在 TeachingAction envelope 内执行，且 MAY 收紧、MUST NOT 扩大。

### DEP-006：同步 query，异步/显式反馈

读取 snapshot MAY 同步；跨系统产生新状态 SHOULD 通过 command/event 形成新版本。MUST NOT 用一个巨大 service method 在单调用栈直接修改所有系统表。

## 3. Allowed Logical Dependency Matrix

符号：`Q` read-only query；`C` public command；`E` event；`X` execute decided action；`-` no direct business dependency。

| From \ To | SYS01 | SYS02 | SYS03 | SYS04 | SYS05 | SYS06 | SYS07 | SYS08 |
|---|---|---|---|---|---|---|---|---|
| SYS01 | - | E/Q | E/Q | E/Q | - | E/Q | - | E |
| SYS02 | Q | - | - | Q | E | - | - | E/X |
| SYS03 | Q | - | - | Q | E/Q | E/Q | E/Q | E |
| SYS04 | Q | Q | Q/E | - | E | - | E | C/E |
| SYS05 | Q | C | Q | Q | - | Q | Q | C |
| SYS06 | Q | - | Q | - | E | - | Q | C/E |
| SYS07 | - | - | Q/E | Q | E | E | - | E |
| SYS08 | Q | C | E | C | C | C | C | - |

矩阵表示逻辑协作，不授权 import 对方内部实现或越权写入。

## 4. v0.3 Adaptive Teaching Dependencies

### DEP-200 — TeachingContext Assembly

SYS05 构造 TeachingContext 时 MAY 读取 SYS03/SYS04/SYS06/SYS07 exact versioned refs 与用户请求/experiment refs；MUST NOT 把这些 source snapshot 变成 SYS05 可写副本。

### DEP-201 — Policy Execution Boundary

```text
SYS05 TeachingAction
→ SYS02 evidence supply (tighten only)
→ SYS08 execution (tighten only)
→ SYS04 actual assistance/Attempt/AssessmentResult
→ SYS03 evidence/state update
→ new material evidence
→ SYS05 next decision
```

任何环节需要改变 StrategyFamily/InteractionMove/envelope 语义时 MUST 回到 SYS05 创建新 TeachingAction。

### DEP-202 — Validation Obligation

SYS05 owns validation obligation；SYS04 creates fresh independent evidence；SYS03 evaluates evidence eligibility。SYS03/SYS08 MUST NOT 直接 clear/complete obligation。

### DEP-203 — Decision / Outcome

DecisionTrace payload 由 decision owner 定义并可由 SYS08 ledger 托管；OutcomeObservation/ExperimentAssignment MAY 由 analytics ledger 托管，但 MUST NOT 回写 DecisionTrace 或取得 TeachingAction/LearnerState ownership。

## 5. Python Package Rules

```text
contracts  ← domains can depend
    ↑
domains/*  ← own domain + contracts + ports
    ↑
orchestration ← public application ports/contracts
    ↑
api/workers ← orchestration/application facade

infrastructure → implements ports
```

### DEP-020

`domains/<A>/` MUST NOT import `domains/<B>/internal_*`、repository implementation 或 ORM model。

### DEP-021

跨 domain 只允许依赖 public contract/query/command/event schema。

### DEP-022

Infrastructure MAY 依赖 DB/Redis/model SDK；domain MUST NOT 反向依赖 infrastructure implementation。

### DEP-023

API MUST NOT 直接调用 repository。

## 6. Transaction / Delivery

### DEP-030

一个 domain transaction SHOULD 只修改该 owner 的业务状态，加同一事务的 outbox/event record。

### DEP-031

关键跨系统事件 MUST 与 owner state update 可靠写入 outbox/等价机制。

### DEP-032

Consumers MUST 假设 at-least-once delivery，因此必须幂等。

### DEP-033

默认采用 local transaction → outbox → idempotent consumer/projection → eventual convergence；MUST NOT 为 v0.3 默认引入 2PC。

## 7. Legacy Governance

### DEP-040

现有 `services/*`、`engines/*` MAY 在迁移期保留，但新增能力 SHOULD 朝 canonical owner/adapter 边界收敛；legacy path MUST NOT 扩大越权。

### DEP-041 — Socratic

`engines/socratic/strategy_selector.py` / state graph MUST NOT 成为 final TeachingAction owner。迁移期 MAY 作为 bounded InteractionMove provider、legacy adapter、stage-definition source 或 execution component；final policy ownership 必须回到 SYS05。

### DEP-042 — Documents

`services/documents/` 中 parser/model/provenance → SYS01；retrieval/ranking/EvidenceBundle → SYS02；storage → infrastructure；security scan → trust/security adapter，不得改变知识业务语义。

### DEP-043 — KT/DKT

SYS03 MUST 只有一个 canonical state projector。DKT/Deep KT 若保留只能是 challenger/辅助预测，不能独立持有 learner truth。

### DEP-204 — No Legacy Dual Truth

旧 strategy enum、integer scaffold/hint/exposure、old policy config/propensity MAY 只读兼容/audit；MUST NOT 与 v0.3 canonical fields 永久双写。

## 8. Prohibited Dependencies

- SYS04 MUST NOT direct-update SYS03 mastery repository；
- SYS08/LLM MUST NOT direct-update SYS03/SYS05/SYS06/SYS07 truth；
- SYS06 MUST NOT 调用 SYS05 private implementation 决定 hint/explanation；
- SYS02 MUST NOT 写 LearnerState；
- SYS07 MUST NOT 修改 LearningPlan；
- 任一 domain MUST NOT 从聊天文本直接更新关键 state；
- SYS08/SYS02 MUST NOT expand TeachingAction envelope；
- experiment layer MUST NOT restore hard-filtered action。

## 9. Architecture Tests

代码库 SHOULD 验证：domains 不 import api/infrastructure implementation；cross-owner repository writes 不可达；SYS08 no direct mastery/plan/review/action write；legacy direct paths 单调减少；SYS02/SYS08 tightening-only；legacy Socratic no final action owner；Outcome/Experiment ledger hosting no domain takeover。

## 10. Acceptance Criteria

- `DEP-AC-201`：TeachingContext assembly 只读 exact owner refs。
- `DEP-AC-202`：SYS02/SYS08 无扩大 scaffold/hint/exposure 路径。
- `DEP-AC-203`：validation obligation 只能由 SYS05 policy-control 管理，并由 fresh SYS04 evidence 满足。
- `DEP-AC-204`：legacy Socratic 无 final TeachingAction ownership。
- `DEP-AC-205`：无 legacy/v0.3 permanent dual truth。