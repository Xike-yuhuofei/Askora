# Askora Implementation Specifications

> 状态：Canonical Implementation Contract Index  
> 上位产品基线：`docs/product/PRODUCT-POSITIONING.md`  
> 当前架构基线：v0.3 Learning Core + v1 Local Web / LocalOwner / Workspace / Local-first Alignment

## 1. Authority and Purpose

`docs/specs/**` 将已冻结产品定位、Canonical Design 与 Accepted ADR 转换为可直接约束实现、测试、迁移、replay 与 release 的合同。

权威链固定为：

```text
PRODUCT-POSITIONING.md
        ↓
Canonical Design / Design Delta
        ↓
Accepted ADR
        ↓
Implementation Specs
        ↓
Vertical Slice / EXEC
        ↓
Code / Test / Release Evidence
```

任何下位 Spec / Vertical Slice / EXEC / code 与 `PRODUCT-POSITIONING.md` 冲突时，必须先按上位约束收敛下位文档；不得用历史 ADR、已实现代码或测试反向覆盖产品定位。

当前 v1 上位硬约束包括：

- 单用户、单设备；
- Local Web Application：Browser → loopback Local Server；
- 无 Account/Login/RBAC/Tenant；
- LocalOwner 是本地数据长期归属主体；
- Workspace 是高层隔离边界，不是 Tenant/Organization；
- SQLite + managed local files 是 production-local baseline；
- Redis/PostgreSQL/Docker/Kafka/Kubernetes 不得成为最终用户运行前提；
- Import = ingest + copy；
- LearningEvidence 是 LearnerState 的事实基础；LearnerState 是可重建 canonical projection；
- SourceChunk/Embedding/Index 是可重建 derived data；
- BYOK，secret 仅本地安全存储；
- v1 core import：EPUB、文本 PDF、Markdown、TXT；完整 OCR 非 v1 core；
- LLM 不直接写 canonical state；
- SYS01～SYS08 Learning Core 继续保持 single-writer ownership。

## 2. Current Formation Chains

### v0.3 Adaptive Teaching Loop

```text
Research Synthesis
→ Canonical Design
→ ADR-0001 / ADR-0002
→ v0.3 Specs
→ v0.3 Vertical Slice
→ EXEC-007+
→ Implementation / verification
```

v0.3 Teaching Policy、Assessment、Learner Model、Review 等学习内核语义不因 v1 Local Web 产品定位而重做；外围 runtime/data/platform contracts 必须服从最新 Product Positioning。

### Book-to-Learning

```text
Product Positioning
+ Canonical Design
+ v0.3 Learning Core
→ SPEC-D01～D06
→ EXEC
→ Implementation / verification
```

其中 SPEC-D01 已对齐 managed SourceFile、Workspace scope、阶段化 local job 与 v1 core formats。

### Local Single-User Identity

```text
Product Positioning
→ Local Single-User Identity Canonical Design Delta
→ ADR-0015
→ LID-* v2
→ Authentication Removal Vertical Slice / EXEC
→ Implementation / Migration / Release Evidence
```

旧 Account/AuthSession/P1-05 只允许作为 historical migration reference。

### Interactive Elements / UI

导航、首页职责、页面布局与具体 Interactive Elements 不由 Product Positioning 本文冻结；它们继续由 ADR-0014 + `docs/specs/ui/**` 管理，但不得突破 Local Web、Workspace、LocalOwner 等产品边界。

## 3. Canonical Spec Index

### Domain

- [Domain Model](domain/domain-model.md) — SYS01～SYS08 公共对象；v1 新增规范解释：LocalOwner、Workspace、Material/SourceFile、LearningProject、LearningSession、RetrievalScope、Durable/Derived、local jobs、Trash/Permanent Delete。
- [Decision Contract](domain/decision-contract.md) — DecisionTrace v0.3、probability、replay。
- [Event Contract](domain/event-contract.md) — LearningEvent、assistance/outcome/experiment event semantics。
- [Lifecycle State Machines](domain/lifecycle-state-machines.md) — lifecycle contracts；若旧生命周期与两阶段删除/去账号化冲突，以上位 Product Positioning 与最新 Data Control contract 为准。

### Architecture

- [System Architecture](architecture/system-architecture.md) — **v1 正式 runtime：Browser → loopback Local Server；SQLite/local files/local jobs；SYS01～SYS08 Learning Core。**
- [State Ownership](architecture/state-ownership.md) — Learning Core single-writer + LocalOwner/Workspace platform owner；LearnerState 为 canonical rebuildable projection。
- [Dependency Rules](architecture/dependency-rules.md) — LocalOwnerContext → WorkspaceContext → owner service；production-local 不依赖 Electron/Redis/PostgreSQL/Docker/Kafka。

### Platform

- [Local Identity and Privacy Lifecycle](platform/identity-privacy-lifecycle.md) — ADR-0015 / `LID-*`：单一 LocalOwnerContext、无 Login/JWT/AuthSession、loopback-only 安全边界、旧 learner ownership 无损迁移与去账号化数据治理。

### Systems

- [SYS01 Content & Knowledge](systems/01-content-knowledge.md) — content/knowledge canonical owner。
- [SYS01 Workspace Material Management](systems/01-library-management.md) — Workspace-scoped Material/search/dedup/Trash/Project relation；**OCR 仅 legacy/optional，不是 v1 core/release prerequisite**。
- [SYS02 Retrieval](systems/02-retrieval.md) — `workspace_id` 是 production RetrievalScope hard boundary；no Global Material Library；indexes rebuildable。
- [SYS03 Learner Model](systems/03-learner-model.md) — LearnerEvidence acceptance、MasteryEstimate、LearnerState；结合 State/Domain contract 解释为 evidence-backed canonical projection。
- [SYS04 Assessment](systems/04-assessment.md) — Attempt/AssessmentResult/diagnosis/actual assistance。
- [SYS05 Teaching Policy](systems/05-teaching-policy.md) — six StrategyFamily、deterministic B3 policy、anti-oscillation、DecisionTrace；**保持 v0.3 冻结语义**。
- [SYS06 Learning Planner](systems/06-learning-planner.md) — Goal/Objectives/Activities/Plan；Goal 必须 workspace scoped，Project association 可选。
- [SYS06 Goal Management](systems/06-goal-management.md) — versioned definition/state/draft/replan 与 evidence-gated achievement。
- [SYS06 Activity Lifecycle](systems/06-activity-lifecycle.md) — start/resume/completion 与 next-activity progression。
- [SYS07 Review Scheduler](systems/07-review-scheduler.md) — deterministic/explainable review scheduling owner。
- [SYS08 AI Orchestration](systems/08-ai-orchestration.md) — execution/model/tool orchestration，不能取得学习领域 truth ownership。
- [SYS08 Model Configuration](systems/08-model-configuration.md) — **Local Web BYOK + loopback API + Local SecretStore**；ADR-0013 的 Electron/Desktop mechanics 已 superseded。

### Interfaces

- [Content Ingestion & Source Locator](interfaces/content-ingestion-contract.md) — managed source copy、Workspace scope、阶段化 pipeline、partial/retry/rebuild、EPUB/PDF(text)/Markdown/TXT。
- [Persistence Contract](interfaces/persistence-contract.md) — **SQLite production baseline**、managed local data directory、Durable/Derived、local jobs、Backup/Restore/Migration、Trash/erasure/no-resurrection。
- [API Contract](interfaces/api-contract.md) — transport contract；身份/网络边界必须服从 LID-* 与 loopback Local Web。
- [Error Contract](interfaces/error-contract.md) — stable error semantics。
- [Recovery Contract](interfaces/recovery-contract.md) — unified recovery issue/action/result。
- [Data Control and Recovery](interfaces/data-control-contract.md) — Backup/Export/erasure/recovery；账号认证语义由 Product Positioning + ADR-0015/LID-* supersede。
- [First-use Onboarding](interfaces/onboarding-contract.md) — LocalOwner bootstrap 后 model→material→goal→first activity readiness；无 register/login。
- [Rich Response Rendering](interfaces/render-content-contract.md) — presentation rendering，不取得 TeachingAction/LearningEvidence ownership。
- [Schema Versioning](interfaces/schema-versioning.md) — schema/version evolution；必须与 v1 startup compatibility gate 对齐。

### Quality

- [Testing Standard](quality/testing-standard.md) — L0～L6 + OPVE/G0/G1/G2。
- [Observability Standard](quality/observability-standard.md) — local diagnostics + decision/outcome observability；不得把 remote analytics 设为 runtime prerequisite。
- [Definition of Done](quality/definition-of-done.md) — Engineering / Policy Correctness / Learning Evidence 三类 Gate。
- [Security Standard](quality/security-standard.md) — hard-rule / answer-exposure / grader-only；并服从 loopback/secret/local-data privacy 上位约束。

### UI

- [UI Spec Index](ui/README.md)
- [Interactive Element System](ui/interactive-element-system.md)
- [Information Architecture](ui/information-architecture.md)
- [Screen Contracts](ui/screen-contracts.md)
- [Data Contracts](ui/data-contracts.md)
- [Visual System](ui/visual-system.md)
- [Quality and Migration](ui/quality-and-migration.md)

UI 具体导航、首页职责、页面层级与控件继续在设计系统中冻结，不在本 Index 反向定义。

## 4. Vertical Slice Status and Supersession Rules

以下 Vertical Slice 仍是有效学习/迁移参考，但必须受最新 Product Positioning 约束：

- [v0.3 Adaptive Teaching Loop](vertical-slices/v0.3-adaptive-teaching-loop.md) — Learning Core canonical slice。
- [Book-to-Adaptive-Learning](vertical-slices/book-to-adaptive-learning.md) — Book learning E2E；资料/identity/runtime semantics 服从最新 v1 contracts。
- [Local Single-User Authentication Removal](vertical-slices/local-single-user-authentication-removal.md) — current identity migration slice。
- [UI-03 Interactive Element System](vertical-slices/ui-03-interactive-element-system-refactor.md) — current UI architecture slice，依赖 Local Identity gate。
- [P1-03 Data Control and Recovery](vertical-slices/p1-03-data-control-recovery.md) — 本地数据治理；account semantics superseded。
- [P1-06 First-use Onboarding](vertical-slices/p1-06-first-use-onboarding.md) — LocalOwner/no-auth semantics apply。

历史/部分 superseded：

- [P1-05 Account Lifecycle](vertical-slices/p1-05-account-lifecycle.md) — **HISTORICAL / SUPERSEDED**，不得作为当前产品实现合同。
- [P1-04C Scanned PDF OCR Review](vertical-slices/p1-04c-library-ocr-review.md) — **HISTORICAL IMPLEMENTED OPTIONAL CAPABILITY**；完整 OCR 不属于 v1 core，不得阻塞 v1 release。
- [P1-02 Model Settings](vertical-slices/p1-02-model-settings.md) — 历史 model-settings implementation baseline；**Desktop/Electron mechanics 已被 Local Web `MODEL-CONFIG-*` supersede**，后续修改不得继续扩大 desktop vault/IPC 依赖。

其他 UI-02 / Goal / Library slices仍可作为实现历史与迁移证据，但与 Workspace/LocalOwner/Local Web/Trash/core-format 发生冲突时由最新 v1 contracts supersede。

EXEC 的实时 active/completed 状态以 `docs/exec-plans/README.md` 为准，本 Spec Index 不复制易失的任务队列状态。

## 5. v0.3 Canonical Decisions → Spec Traceability

| Canonical Decision | ADR | Canonical Spec Requirements |
|---|---|---|
| six Strategy Families | ADR-0001 | `DOMAIN-083/086`, `SYS05-201` |
| four-layer ontology | ADR-0001 | `DOMAIN-083..085`, `SYS05-202/203` |
| TeachingContext | ADR-0002 | `DOMAIN-088`, `SYS05-210..212` |
| ErrorType | — | `DOMAIN-072..074`, `SYS04-220..224` |
| hard/soft/experiment separation | ADR-0002 | `SYS05-240..242`, Decision Contract |
| support/exposure orthogonality | ADR-0001 | `DOMAIN-061..063`, SYS02/03/04/05/08 |
| validation obligation | — | `DOMAIN-091`, SYS03/04/05 |
| deterministic policy | ADR-0002 | SYS05 + Decision Contract |
| anti-oscillation | ADR-0002 | SYS05 + Testing Standard |
| PolicyBundle | ADR-0002 | `DOMAIN-089`, SYS05 |
| DecisionTrace replay/probability | ADR-0002 | Decision Contract + SYS05 |
| Outcome/Experiment | — | `DOMAIN-111..113`, Event/Observability contracts |
| release gate separation | — | Definition of Done |

v0.3 Teaching Policy invariants继续有效：

```text
TeachingStage != LearnerState
AssessmentResult != MasteryEstimate
DecisionTrace != OutcomeObservation
Experiment assignment probability != action selection propensity
SYS02/SYS08 may tighten but not expand TeachingAction envelope
LLM/Agent never owns final TeachingAction or learner/assessment/plan/review truth
```

## 6. v1 Product Positioning → Spec Traceability

| Product Constraint | Primary Specs |
|---|---|
| Local Web Browser → loopback Local Server | System Architecture, Dependency Rules, LID-* |
| No Account/Login/RBAC/Tenant | LID-*, State Ownership, Domain Model |
| LocalOwner stable ownership | LID-*, State Ownership, Domain Model, Persistence |
| Workspace isolation | Domain Model, State Ownership, SYS01, SYS02, Persistence |
| Material ↔ Project many-to-many | Domain Model, SYS01 Material Management |
| Import = ingest + copy | SPEC-D01, Persistence |
| SQLite production baseline | System Architecture, Persistence |
| No Redis/Postgres/Docker runtime prerequisite | Architecture, Dependency Rules, Persistence |
| Durable vs Derived | Domain Model, State Ownership, Persistence, SYS02 |
| LearnerState rebuildable from Evidence | Domain Model, State Ownership, SYS03 |
| Trash → Permanent Delete | Domain Model, Persistence, Data Control, SYS01 Material Management |
| BYOK / local secret | MODEL-CONFIG, Architecture, Persistence/Security |
| Source-grounded provenance | Domain Model, SPEC-D01, SYS02 |
| RAG is infrastructure | SYS02, Architecture |
| local persistent background jobs | Architecture, Persistence, SPEC-D01 |
| Backup != Export / formal Migration | Persistence, Data Control, Schema Versioning |
| v1 core formats only | SPEC-D01, SYS01 Material Management |
| Full OCR not v1 core | SYS01 Material Management, ADR-0008 supersession |
| No open-ended autonomous Agent | Architecture, SYS08, Teaching Policy |

## 7. ADR Supersession Relevant to Current Specs

### ADR-0008

**Partially superseded by Product Positioning.**

Superseded mechanics：OCR-as-v1-core、global/current-user library scope、archive-as-primary-delete。

Retained：SYS01 metadata/content ownership、provenance、duplicate-as-suggestion、rebuildable search projection、optional OCR candidate safety。

### ADR-0013

**Partially superseded by Product Positioning.**

Superseded mechanics：Electron safeStorage requirement、desktop vault/main/preload IPC、desktop launcher/child-backend mechanics、macOS App-only release path。

Retained：SYS08 routing owner、secret/routing separation、safe local secret storage、probe、revision/concurrency、rollback、no silent failover、no secret leak。

### ADR-0015

Current authority for local identity/authentication removal. Account/Login/JWT/AuthSession/Recovery Kit/Account Deletion product semantics are superseded; owner-safe data governance remains.

## 8. Migration and Compatibility Rules

- Legacy fields MAY remain read-compatible only with explicit canonical target and retirement condition。
- `user_id` / `pseudonym_id` MAY temporarily represent LocalOwner/Learner storage compatibility；不得恢复 Account semantics。
- legacy `SourceDocument/document_id` MAY remain SYS01 compatibility identity；new product scope MUST resolve Material + Workspace。
- old global retrieval/cache MUST migrate to workspace-scoped keys；不得成为 permanent dual truth。
- old Desktop credential/vault mechanics MAY be read/migrated only to Local SecretStore/Profile；不得继续成为 v1 new-write path。
- historical OCR data MAY remain immutable/audit/optional；v1 new material ingest不得要求 OCR。
- PostgreSQL/Redis development compatibility MAY remain；production-local correctness不得依赖它们。
- old archive lifecycle MAY migrate to Trash semantics where product object matches；不得自动物理删除 durable SourceFile。

## 9. Spec-ID Governance

Existing requirement IDs MUST NOT be reused to change unrelated meaning. 新的 v1 alignment requirement 已使用现有文档内未占用 ranges（例如 `ARCH-008+`、`STATE-005+`、`DOMAIN-200+`、`PERSIST-*` additive IDs、`SYS02-100+`）。

历史 superseded requirement 应在原 ADR/Spec 中保留可追踪记录，而不是删除后让 Git history 成为唯一解释入口。

## 10. Release Claim Boundary

所有 release 必须区分：

```text
Engineering Gate
Policy / Contract Correctness Gate
Learning Evidence Gate
```

产品定位、架构对齐、UI 简化、Local Web migration、SQLite/Workspace correctness 或 OCR/desktop 退役都**不能**被宣称为真实学习效果已经得到证明。

真人学习效果仍以：

- no-hint independent success；
- delayed independent performance；
- independent transfer；
- unit-time capability gain；

为主要结果变量。engagement、对话轮次、使用时长、点击数等不得成为核心学习 KPI。

## 11. Implementation Rule

任何新的 Codex / engineering task 开始前 MUST：

1. 读取 `docs/product/PRODUCT-POSITIONING.md`；
2. 确认涉及的 canonical Spec；
3. 检查历史 ADR 是否已部分 superseded；
4. 若代码事实与 Spec 不同，默认视为 implementation drift；
5. 若必须突破 Product Positioning，停止并报告 PRODUCT POSITIONING GAP，而不是自行实现；
6. 若仅是现有 Spec 的机械落地，按 EXEC 执行并用测试证明，不重新发明架构。
