# Askora Dependency Rules

> Spec ID 范围：`DEP-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + v1 Product Positioning Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. Purpose

本规范定义各系统允许的依赖方向、跨边界调用方式以及 legacy 迁移限制。违反本文件的实现必须先通过 Product Positioning / Design / ADR / Spec 治理，MUST NOT 由执行代理在产品代码中临场或隐式重定义架构。

## 2. Core Dependency Rules

### DEP-001 — No Cross-owner ORM Writes

领域模块 MUST NOT 通过 ORM/repository 直接写其他领域状态。跨领域变更只能通过 public command、append-only event/evidence、read-only query 或 owner application service。

### DEP-002 — One Public Schema

`LearningEvent`、`AssessmentResult`、`MasteryEstimate`、`TeachingContext`、`TeachingAction`、`PolicyBundle`、`LearningPlan`、`ReviewSchedule`、`EvidenceBundle`、`OutcomeObservation`、`ExperimentAssignment` 等跨系统对象 MUST 有唯一 canonical contract；MUST NOT 复制长期本地副本作为第二协议。

LocalOwner / Workspace / Material / LearningProject 等 platform/product objects 同样 MUST 有唯一公共语义。

### DEP-003 — Domain / Infrastructure Separation

Domain logic MUST NOT 依赖 FastAPI transport、browser runtime、Redis/Kafka client、具体 model SDK、OS secret API 或隐式 global SQLAlchemy Session；这些能力 SHOULD 通过 port/adapter 注入。

Electron/Desktop 不属于 v1 Canonical Runtime，新 domain code MUST NOT 依赖 Electron IPC/safeStorage。

### DEP-004 — API Is a Local Transport Adapter

API 只负责 loopback transport validation、LocalOwnerContext resolution、command/query、HTTP/WebSocket/streaming mapping 与 error mapping；MUST NOT 持有 mastery、Teaching Policy、assessment、plan、review 算法。

v1 API MUST NOT 以 Account/JWT/AuthSession 作为业务 owner resolution。网络安全边界由 loopback/origin + LocalOwnerContext 共同承担。

### DEP-005 — SYS08 Executes, Does Not Own SYS01～SYS07 Rules

SYS08 MAY 决定 workflow/retry/model/tool route，但 MUST NOT 复制/覆盖领域规则。例如 support/hint transition 属 SYS05、evidence eligibility 属 SYS03、next_due 属 SYS07；SYS08 只能在 TeachingAction envelope 内执行并 MAY 收紧、MUST NOT 扩大。

### DEP-006 — Sync Query, Explicit Feedback

读取 snapshot MAY 同步；跨系统产生新 state SHOULD 通过 command/event 形成新版本。MUST NOT 用一个巨大 service method 在单调用栈修改所有系统表。

### DEP-007 — Platform Scope Before Learning Domain

learner-owned command/query 进入 Learning Core 前 MUST 已解析：

```text
LocalOwnerContext
→ WorkspaceContext (when object is workspace-scoped)
→ owner application/domain service
```

平台 scope resolution 不得越权修改领域状态。

### DEP-008 — Workspace Scope Is a Hard Filter

Workspace scope MUST 在 search/retrieval、material access、goal/session access、learner projection query 与 background rebuild task 中先于 soft ranking/LLM logic 生效。

跨 Workspace 数据不得因为“同一 LocalOwner”而自动可见或自动融合。

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

LocalOwner/Workspace/Product Organization 属 platform boundary，不进入八系统矩阵。Learning Core MAY 只读其 exact scope refs；不得回写 Workspace membership。

## 4. Package / Transaction Rules

```text
contracts  ← domains can depend
    ↑
domains/*  ← own domain + contracts + ports
    ↑
application/orchestration ← public application ports/contracts
    ↑
api/local_workers ← application facade

platform/* → identity/workspace/jobs/backup/config lifecycle
infrastructure → implements ports (SQLite/files/index/secret/provider)
```

### DEP-020

`domains/<A>/` MUST NOT import `domains/<B>/internal_*`、repository implementation 或 ORM model。

### DEP-021

跨 domain 只允许依赖 public contract/query/command/event schema。

### DEP-022

Infrastructure MAY 依赖 SQLite driver、file APIs、index libraries、model SDK；domain MUST NOT 反向依赖 infrastructure implementation。

Redis/PostgreSQL MAY 存在于开发/CI adapter，但 production-local domain semantics MUST NOT 假设它们存在。

### DEP-023

API MUST NOT 直接调用 repository；LocalOwner/Workspace resolver 是 transport/application prerequisite，不是 repository bypass 许可。

### DEP-024 — Browser Is Presentation, Not State Owner

Browser/localStorage/sessionStorage MAY 保存短期 UI preference/cache，但 MUST NOT 成为 LocalOwner、Workspace、Material membership、LearningGoal、LearnerState、TeachingAction、ModelRouteProfile、API Key 或 background job truth。

Current Workspace selection is specifically a Platform Workspace Registry preference governed by `CWSP-*`。Browser MAY preserve per-Workspace draft/tab position for recovery, but MUST NOT claim switch success before the owner command receipt。

### DEP-025 — Workspace Selection Before Scoped Command

Application startup MAY read canonical WorkspaceSelection；explicit deep links MAY supply a validated Workspace scope without mutating selection。Every workspace-scoped write still carries/resolves exact route/body scope and MUST NOT depend only on ambient current selection。Course Activity query may read SYS06 exact refs；it MUST NOT import/write SYS06 private persistence as a second owner。

### DEP-030 — Single-owner Transaction

一个 domain transaction SHOULD 只修改该 owner 的业务状态，并写同一事务的 outbox/event record。

### DEP-031 — Transactional Outbox

关键跨系统事件 MUST 与 owner state update 可靠写入 outbox/等价本地 durable mechanism。

### DEP-032 — At-least-once Consumers

Consumers MUST 假设 at-least-once delivery，因此必须 idempotent。

### DEP-033 — No Default 2PC

采用 local transaction → outbox → idempotent consumer/projection → eventual convergence；MUST NOT 为 v1 默认引入 2PC/distributed transaction。

### DEP-034 — Local Job Runtime

Background jobs MUST 通过 Platform Job Runtime 读取持久化 job state，并调用对应 owner application service。Worker MAY 与 Local Server 同进程或受控子进程运行，但 MUST NOT 要求 Redis/Celery/Kafka 等独立服务才能保证正确性。

## 5. Legacy Governance

### DEP-040

现有 `services/*`、`engines/*` MAY 在迁移期保留，但新增能力 SHOULD 朝 canonical owner/adapter 边界收敛；legacy path MUST NOT 扩大越权。

### DEP-041 — Socratic Split Direction

Legacy Socratic 的教学动作选择逻辑最终归 SYS05；语言生成/表达/guardrail execution 归 SYS08。`strategy_selector.py` / state graph MUST NOT 成为 final TeachingAction owner，迁移期 MAY bounded InteractionMove provider/adapter/stage-definition source/execution component。

### DEP-042 — Documents Split Direction

`services/documents/` 中 parser/model/provenance → SYS01；retrieval/ranking/EvidenceBundle → SYS02；storage → infrastructure；security scan → trust/security adapter，不得改变知识业务语义。

Material/SourceFile/Workspace membership 必须按最新 Domain/Workspace contract 分离，旧 `Document.user_id` 不能继续充当全局资料 scope。

### DEP-043 — KT/DKT

SYS03 MUST 只有一个 canonical state projector。DKT/Deep KT MAY challenger/auxiliary predictor，MUST NOT 独立持有 learner truth。

### DEP-044 — Desktop/Auth/Distributed Infrastructure Retirement

Electron main/preload、desktop vault、JWT/AuthSession、Redis-required worker、PostgreSQL-required runtime MAY 作为 legacy implementation 存在于迁移期；新 canonical code MUST NOT 依赖它们。每条 compatibility path 必须有 target owner 与 retirement condition。

## 6. Prohibited Dependencies

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

### DEP-056

任何 domain MUST NOT 绕过 WorkspaceContext 执行 cross-workspace query/retrieval，因为 owner_id 相同并不等于 workspace scope 相同。

### DEP-057

LLM/provider adapter MUST NOT 直接写 SQLite、Workspace membership、LearningEvidence、LearnerState、Goal、Plan 或 TeachingAction；structured output 必须经过 schema/application/domain rules。

## 7. Adaptive Teaching Dependencies

### DEP-200 — TeachingContext Assembly

SYS05 MAY 读取 SYS03/SYS04/SYS06/SYS07 exact versioned refs 与用户请求/experiment refs 构造 TeachingContext；MUST NOT 将 source snapshots 变成 SYS05 可写副本。

TeachingContext 所引用的 workspace-scoped facts MUST 属于同一 Workspace，除非未来显式合同允许跨 Workspace。

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

### DEP-206 — Local Model Configuration Adapter

Browser Settings MAY 通过 loopback API 提交一次性 candidate provider/model/API Key。API/application layer MUST 把 secret 交给 local SecretStore adapter、把 routing metadata 交给 SYS08 `ModelRouteProfile` owner；Browser MUST NOT 读取已保存 Key。

SecretStore MAY 使用 OS-backed credential storage；domain/SYS08 routing logic MUST NOT 依赖具体 OS API。Development/test environment variables MAY 作为非生产 compatibility input，但不得成为 production Local 的第二配置 truth或在 clear 后静默复活配置。

## 8. Architecture Tests

代码库 SHOULD 验证：

- domains 不 import api/infrastructure implementation；
- cross-owner writes 不可达；
- SYS04 no SYS03 persistence write；
- SYS08 no mastery/plan/review/action write；
- SYS02/SYS08 tightening-only；
- legacy Socratic no final owner；
- Outcome/Experiment ledger hosting no domain takeover；
- LocalOwner/Workspace scope 无第二 writer；
- production retrieval 无 cross-workspace leak；
- browser 无 persistent secret truth；
- Local Server 不依赖 Redis/PostgreSQL/Docker 才能启动；
- local job restart/duplicate execution 仍幂等。

## 9. Acceptance Criteria

- `DEP-AC-201`：TeachingContext assembly 只读 exact owner refs。
- `DEP-AC-202`：SYS02/SYS08 无扩大 scaffold/hint/exposure 路径。
- `DEP-AC-203`：validation obligation 由 SYS05 policy-control 管理，并由 fresh SYS04 evidence 满足。
- `DEP-AC-204`：legacy Socratic 无 final TeachingAction ownership。
- `DEP-AC-205`：无 legacy/v0.3 permanent dual truth。
- `DEP-AC-206`：existing `DEP-050..057` prohibited dependencies 可由 architecture tests 强制。
- `DEP-AC-207`：browser/普通 API 无持久化 secret truth；SecretStore 与 SYS08 profile owner 分离。
- `DEP-AC-208`：learner-owned request 解析 LocalOwnerContext；workspace-scoped request 解析 WorkspaceContext。
- `DEP-AC-209`：SYS02/cache/background rebuild 默认严格 workspace scoped。
- `DEP-AC-210`：production-local dependency graph 不要求 Redis/PostgreSQL/Docker/Kafka/Electron。

## 10. Forbidden Implementations

禁止 cross-owner repository writes；SYS08/LLM direct canonical writes；SYS06 private-policy dependency；SYS02 learner-state writer；SYS07 plan writer；chat-text direct state update；SYS02/SYS08 envelope expansion；experiment hard-rule restoration；browser 获取已保存明文模型密钥；公网/普通 API 暴露 secret；permanent legacy dual truth；Workspace 被当作 Tenant；owner_id 代替 workspace filter；production-local worker 必须依赖 Redis/Kafka；Electron IPC 成为 v1 model configuration requirement。

## 11. P1-06 Onboarding Dependencies

### DEP-300 — Read-only Composition

Onboarding query MAY 读取 Platform Experience Preference、public model summary、SYS01 material eligibility、SYS06 Goal/Activity projections、Data Control capability route 与 RecoveryAction。它 MUST NOT import 或调用这些 owner 的 private repository/write implementation。

### DEP-301 — Command Direction

Onboarding preference command 只能写 presentation preference。模型、资料、Goal、diagnostic、plan、activity 和 recovery side effect 必须继续通过对应现有页面/application command；Onboarding 不得提供跨 owner generic command router。

### DEP-302 — Completion Source

First activity completion dependency 固定为 SYS06 exact lifecycle state + accepted transcript completion source。message/model result/UI state → onboarding completion 的直接依赖 MUST 由 architecture tests 禁止。
