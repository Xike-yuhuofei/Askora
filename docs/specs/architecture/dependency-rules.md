# Askora Dependency Rules

> Spec ID 范围：`DEP-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Purpose

本规范定义各系统允许的依赖方向、跨边界调用方式以及 legacy 迁移限制。违反本文件的实现必须先通过 Design/ADR/Spec 变更，MUST NOT 由执行代理在产品代码中临场或隐式重定义架构；用户已委托架构自治时，Codex MAY 先正式接受 ADR、更新 Spec 并冻结 EXEC，再按新合同实现。

## 2. Existing Dependency Rules Retained

### DEP-001 — No Cross-owner ORM Writes

领域模块 MUST NOT 通过 ORM/repository 直接写其他领域状态。跨领域变更只能通过 public command、append-only event/evidence、read-only query 或 owner application service。

### DEP-002 — One Public Schema

`LearningEvent`、`AssessmentResult`、`MasteryEstimate`、`TeachingContext`、`TeachingAction`、`PolicyBundle`、`LearningPlan`、`ReviewSchedule`、`EvidenceBundle`、`OutcomeObservation`、`ExperimentAssignment` 等跨系统对象 MUST 有唯一 canonical contract；MUST NOT 复制长期本地副本作为第二协议。

### DEP-003 — Domain / Infrastructure Separation

Domain logic MUST NOT 依赖 FastAPI transport、Electron、Redis/Kafka client、具体 model SDK 或隐式 global SQLAlchemy Session；这些能力 SHOULD 通过 port/adapter 注入。

### DEP-004 — API Is Transport Adapter

API 只负责 auth、transport validation、command/query、HTTP/WebSocket/streaming mapping、error mapping；MUST NOT 持有 mastery、Teaching Policy、assessment、plan、review 算法。

### DEP-005 — SYS08 Executes, Does Not Own SYS01～SYS07 Rules

SYS08 MAY 决定 workflow/retry/model/tool route，但 MUST NOT 复制/覆盖领域规则。例如 support/hint transition 属 SYS05、evidence eligibility 属 SYS03、next_due 属 SYS07；SYS08 只能在 TeachingAction envelope 内执行并 MAY 收紧、MUST NOT 扩大。

### DEP-006 — Sync Query, Explicit Feedback

读取 snapshot MAY 同步；跨系统产生新 state SHOULD 通过 command/event 形成新版本。MUST NOT 用一个巨大 service method 在单调用栈修改所有系统表。

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

矩阵表示 logical collaboration，不授权 import 对方内部 implementation 或越权写入。

## 4. Existing Package / Transaction Rules Retained

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

### DEP-030 — Single-owner Transaction

一个 domain transaction SHOULD 只修改该 owner 的业务状态，并写同一事务的 outbox/event record。

### DEP-031 — Transactional Outbox

关键跨系统事件 MUST 与 owner state update 可靠写入 outbox/等价机制。

### DEP-032 — At-least-once Consumers

Consumers MUST 假设 at-least-once delivery，因此必须 idempotent。

### DEP-033 — No Default 2PC

采用 local transaction → outbox → idempotent consumer/projection → eventual convergence；MUST NOT 为 v0.3 默认引入 2PC/distributed transaction。

## 5. Existing Legacy Governance Retained

### DEP-040

现有 `services/*`、`engines/*` MAY 在迁移期保留，但新增能力 SHOULD 朝 canonical owner/adapter 边界收敛；legacy path MUST NOT 扩大越权。

### DEP-041 — Socratic Split Direction, v0.3 Clarified

Legacy Socratic 的教学动作选择逻辑最终归 SYS05；语言生成/表达/guardrail execution 归 SYS08。`strategy_selector.py` / state graph MUST NOT 成为 final TeachingAction owner，迁移期 MAY bounded InteractionMove provider/adapter/stage-definition source/execution component。

### DEP-042 — Documents Split Direction

`services/documents/` 中 parser/model/provenance → SYS01；retrieval/ranking/EvidenceBundle → SYS02；storage → infrastructure；security scan → trust/security adapter，不得改变知识业务语义。

### DEP-043 — KT/DKT

SYS03 MUST 只有一个 canonical state projector。DKT/Deep KT MAY challenger/auxiliary predictor，MUST NOT 独立持有 learner truth。

## 6. Existing Prohibited Dependencies Retained

### DEP-050

SYS04 Assessment MUST NOT 调用 SYS03 repository 直接更新 mastery。

### DEP-051

SYS08 Orchestrator/LLM MUST NOT 调用 SYS03/SYS05/SYS06/SYS07 repository 直接更新 canonical state/action。

### DEP-052

SYS06 Planner MUST NOT 调用 SYS05 private implementation 决定 hint/explanation/TeachingAction。

### DEP-053

SYS02 Retrieval MUST NOT 调用 SYS03 write interface，也不得生成长期 LearnerState 副本。

### DEP-054

SYS07 Review MUST NOT 修改 LearningPlan；它只能发布 due/risk，SYS06 决定是否进入实际计划。

### DEP-055

任一 domain MUST NOT 从聊天文本解析结果直接更新关键业务状态；必须先形成对应 command/evidence/result。

## 7. v0.3 Adaptive Teaching Dependencies

### DEP-200 — TeachingContext Assembly

SYS05 MAY 读取 SYS03/SYS04/SYS06/SYS07 exact versioned refs 与用户请求/experiment refs 构造 TeachingContext；MUST NOT 将 source snapshots 变成 SYS05 可写副本。

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

任何环节需要改变 StrategyFamily/InteractionMove/envelope semantics 时 MUST 回到 SYS05 创建新 TeachingAction。

### DEP-202 — Validation Obligation

SYS05 owns validation obligation；SYS04 creates fresh independent evidence；SYS03 evaluates evidence eligibility。SYS03/SYS08 MUST NOT clear/complete obligation without fresh evidence。

### DEP-203 — Decision / Outcome

DecisionTrace payload 由 decision owner 定义并 MAY 由 SYS08 ledger 托管；OutcomeObservation/ExperimentAssignment MAY 由 analytics ledger 托管，但 MUST NOT 回写 DecisionTrace 或取得 TeachingAction/LearnerState ownership。

### DEP-204 — No Legacy Dual Truth

旧 strategy enum、integer scaffold/hint/exposure、old policy config/propensity MAY read-only compatibility/audit；MUST NOT 与 v0.3 canonical fields permanent dual-write。

### DEP-205 — Hard-rule / Envelope Integrity

SYS02/SYS08 MUST NOT expand TeachingAction envelope；experiment layer MUST NOT restore hard-filtered action；LLM/legacy adapters MUST NOT bypass SYS05 hard constraints。

## 8. Architecture Tests

代码库 SHOULD 验证 domains 不 import api/infrastructure implementation；cross-owner writes 不可达；SYS04 no SYS03 persistence write；SYS08 no mastery/plan/review/action write；legacy direct paths 单调减少；SYS02/SYS08 tightening-only；legacy Socratic no final owner；Outcome/Experiment ledger hosting no domain takeover。

## 9. Acceptance Criteria

- `DEP-AC-201`：TeachingContext assembly 只读 exact owner refs。
- `DEP-AC-202`：SYS02/SYS08 无扩大 scaffold/hint/exposure 路径。
- `DEP-AC-203`：validation obligation 由 SYS05 policy-control 管理，并由 fresh SYS04 evidence 满足。
- `DEP-AC-204`：legacy Socratic 无 final TeachingAction ownership。
- `DEP-AC-205`：无 legacy/v0.3 permanent dual truth。
- `DEP-AC-206`：existing `DEP-050..055` prohibited dependencies 仍可由 architecture tests 强制。

## 10. Forbidden Implementations

禁止 cross-owner repository writes；SYS08/LLM direct canonical writes；SYS06 private-policy dependency；SYS02 learner-state writer；SYS07 plan writer；chat-text direct state update；SYS02/SYS08 envelope expansion；experiment hard-rule restoration；permanent legacy dual truth。

## 11. P1-06 Onboarding Dependencies

### DEP-300 — Read-only Composition

Onboarding query MAY 读取 Platform Experience Preference、P1-02 public model summary、SYS01 material
eligibility、SYS06 Goal/Activity projections、P1-03 capability route 与 P1-07 RecoveryAction。它 MUST NOT
import 或调用这些 owner 的 private repository/write implementation。

### DEP-301 — Command Direction

Onboarding preference command 只能写 presentation preference。模型、资料、Goal、diagnostic、plan、
activity 和 recovery side effect 必须继续通过对应现有页面/application command；Onboarding 不得提供
跨 owner generic command router。

### DEP-302 — Completion Source

First activity completion dependency 固定为 SYS06 exact lifecycle state + accepted transcript completion source。
message/model result/UI state → onboarding completion 的直接依赖 MUST 由 architecture tests 禁止。
