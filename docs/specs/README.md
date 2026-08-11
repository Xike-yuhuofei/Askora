# Askora Implementation Specifications

> 状态：Canonical Implementation Contract Index  
> 上位产品基线：`docs/product/PRODUCT-POSITIONING.md` + `docs/product/PRODUCT-DEFINITION.md`  
> 当前架构基线：v0.3 Learning Core + v1 Local Web / LocalOwner / Workspace / Local-first Alignment  
> 最近校准：2026-08-11

## 1. Authority and Purpose

`docs/specs/**` 将已冻结 Product Positioning、Product Definition、Canonical Design 与 Accepted ADR 转换为可直接约束实现、迁移、replay、测试和 release 的合同。

```text
PRODUCT-POSITIONING.md
        ↓ product boundary
PRODUCT-DEFINITION.md
        ↓ capabilities / requirements / product acceptance
Canonical Design / Design Delta
        ↓
Accepted ADR
        ↓
Implementation / Quality Specs
        ↓
Vertical Slice / EXEC / Linear Issue
        ↓
Code / Test / Release Evidence
```

任何下位 Spec / EXEC / code 与 Product Positioning 或 Product Definition 冲突时，必须收敛下位层；不得用历史实现或历史 PASS 反向降低产品边界、改变 Capability 或扩大 v1 Feature Scope。

当前 v1 产品要求由 `PRODUCT-DEFINITION.md` 的 `CAP-*`、`PD-RULE-*`、`PD-REQ-*` 与 Product Acceptance 管理；本目录负责 HOW，不创建第二套 Product Capability taxonomy。

当前 v1 技术硬约束：

- single-user / single-device；
- Browser → loopback Local Server；
- no Account/Login/RBAC/Tenant；
- LocalOwner 是本地数据归属主体；
- Workspace 是真实数据隔离边界；
- SQLite + managed local files 是 production-local baseline；
- Redis/PostgreSQL/Docker/Kafka 不得成为最终用户运行前提；
- Import = ingest + copy；
- LearningEvidence 是 LearnerState 的事实基础；LearnerState/MasteryEstimate 是 SYS03 canonical rebuildable projections；
- SourceChunk/Embedding/Index/cache 是 rebuildable infrastructure data；
- BYOK secret 只在本地 OS-backed secure storage；
- v1 core import：EPUB、文本 PDF、Markdown、TXT；完整 OCR 非 v1 core；
- ordinary Material delete = Trash，不是物理文件删除；
- LLM 不直接写 canonical state；
- SYS01～SYS08 Learning Core 继续保持 single-writer ownership。

## 2. Current Formation Chains

### v0.3 Learning Core

```text
PRODUCT-DEFINITION CAP-02..07 / PD-RULE-001..007
+
Research Synthesis
→ Canonical Design
→ ADR-0001 / ADR-0002
→ v0.3 Specs
→ Vertical Slice / EXEC
→ Implementation / verification
```

v1 platform/runtime changes MUST NOT silently redesign the six Strategy Families、TeachingContext、TeachingAction、Assessment、LearnerState、Review 或 DecisionTrace semantics。

### LocalOwner / Workspace / Learning Scope

```text
PRODUCT-POSITIONING
→ PRODUCT-DEFINITION CAP-01 / CAP-08
→ Local Identity Delta / ADR-0015
→ ADR-0016
→ LID-* + WSP-*
→ Workspace / Project / Session persistence migration
→ learner-state scope propagation
→ Workspace-scoped Retrieval
```

### Local Web BYOK

```text
PRODUCT-POSITIONING
→ PRODUCT-DEFINITION CAP-08 / PD-REQ-0801..0804
→ historical ADR-0013 invariants
→ ADR-0017
→ MODEL-CONFIG-* + LSS-* + SEC-*
→ LocalSecretStore / profile / activation journal
→ Local Web Settings / real provider E2E
```

### Material Lifecycle

```text
PRODUCT-DEFINITION CAP-01 / PD-REQ-0104
→ LIB-045/046 + PERSIST-080..083 + DATA DOCUMENT erasure
→ MATLIFE-*
→ Trash / Restore / Permanent Delete implementation
```

## 3. Canonical Spec Index

### Domain

- [Domain Model](domain/domain-model.md) — SYS01～SYS08 public objects plus v1 LocalOwner/Workspace/Material/Project/Session/Retrieval/Durable-Derived interpretation.
- [Decision Contract](domain/decision-contract.md) — DecisionTrace, deterministic probability/replay semantics.
- [Event Contract](domain/event-contract.md) — LearningEvent, assistance/outcome/experiment semantics.
- [Lifecycle State Machines](domain/lifecycle-state-machines.md) — existing domain lifecycle contracts; v1 Material lifecycle uses MATLIFE when conflicts exist.

### Architecture

- [System Architecture](architecture/system-architecture.md) — Browser → loopback Local Server; SQLite/local files/local jobs; SYS01～SYS08 Learning Core.
- [State Ownership](architecture/state-ownership.md) — Learning Core single writers + Platform owners; no cross-owner ORM writes.
- [Dependency Rules](architecture/dependency-rules.md) — LocalOwner/Workspace application boundary; no Electron/Redis/PostgreSQL/Docker/Kafka production prerequisite.

### Platform

- [Local Identity and Privacy Lifecycle](platform/identity-privacy-lifecycle.md) — ADR-0015 / `LID-*`: LocalOwner, no Login/JWT/AuthSession, loopback boundary and legacy identity migration.
- [Workspace / LearningProject / LearningSession Scope](platform/workspace-project-session-scope.md) — ADR-0016 / `WSP-*`: durable Workspace/Project/Session ownership, stable Material identity, SourceFile normalization, default Workspace migration and same-workspace invariants.
- [Local SecretStore](platform/local-secret-store.md) — ADR-0017 / `LSS-*`: exact OS-backed keyring adapters, backend allowlist, opaque refs, non-secret activation journal and crash reconciliation.

### Systems

- [SYS01 Content & Knowledge](systems/01-content-knowledge.md) — content/knowledge canonical owner.
- [SYS01 Workspace Material Management](systems/01-library-management.md) — Workspace Material metadata/search/dedup/Project relation/Trash; OCR only optional/legacy.
- [SYS01 Content Granularity](systems/01-content-granularity.md) — EvidenceSpan/SemanticUnit/RetrievalChunk/HierarchyNode boundaries.
- [SYS01 Knowledge Publish Pipeline](systems/01-knowledge-publish-pipeline.md) — candidate→verify→publish.
- [SYS02 Retrieval](systems/02-retrieval.md) — Workspace-scoped RetrievalScope; no Global Library; index/cache rebuildable.
- [SYS03 Learner Model](systems/03-learner-model.md) — LearnerEvidence/MasteryEstimate/LearnerState; evidence-backed, replayable, Workspace-specific under WSP.
- [SYS04 Assessment](systems/04-assessment.md) — Attempt/AssessmentResult/diagnosis/actual assistance.
- [SYS05 Teaching Policy](systems/05-teaching-policy.md) — six Strategy Families, deterministic B3 policy, anti-oscillation, DecisionTrace.
- [SYS06 Learning Planner](systems/06-learning-planner.md) — Goal/Objectives/Activities/Plan.
- [SYS06 Goal Management](systems/06-goal-management.md) — versioned Goal definition/state/draft/replan/achievement.
- [SYS06 Goal → Knowledge Mapping](systems/06-goal-knowledge-mapping.md) — Goal-specific Knowledge mapping.
- [SYS06 Prerequisite Diagnostic Bootstrap](systems/06-prerequisite-diagnostic-bootstrap.md) — SYS06/SYS04/SYS03 bootstrap boundary.
- [SYS06 Activity Lifecycle](systems/06-activity-lifecycle.md) — start/resume/completion/next activity.
- [SYS07 Review Scheduler](systems/07-review-scheduler.md) — deterministic/explainable review scheduling owner.
- [SYS08 AI Orchestration](systems/08-ai-orchestration.md) — execution/model/tool orchestration only.
- [SYS08 Model Configuration](systems/08-model-configuration.md) — Local Web BYOK, route/profile semantics, LocalSecretStore binding and crash-consistent activation.

SYS01～SYS08 是技术/教学 ownership，不是 Product Capability。Product Capability 以 `PRODUCT-DEFINITION.md` 的 `CAP-01`～`CAP-08` 为准。

### Interfaces

- [Content Ingestion & Source Locator](interfaces/content-ingestion-contract.md) — managed source copy, structure-preserving pipeline, local jobs, v1 core formats.
- [Persistence Contract](interfaces/persistence-contract.md) — SQLite production baseline, durable/derived, local jobs, backup/migration/trash/no-resurrection.
- [Material Lifecycle](interfaces/material-lifecycle-contract.md) — `MATLIFE-*`: Trash/Restore/Permanent Delete commands, legacy migration, Data Control handoff, job/retrieval/backup semantics.
- [API Contract](interfaces/api-contract.md) — transport contract; v1 identity/network/scope semantics defer to LID/WSP/MATLIFE/MODEL-CONFIG where newer.
- [Error Contract](interfaces/error-contract.md) — stable public error semantics.
- [Recovery Contract](interfaces/recovery-contract.md) — recovery issue/action/result.
- [Data Control and Recovery](interfaces/data-control-contract.md) — Backup/Export/DOCUMENT erasure/no-resurrection; historical account/Desktop language is subordinate to current Product Positioning/LID.
- [First-use Onboarding](interfaces/onboarding-contract.md) — LocalOwner bootstrap and first learning readiness; no register/login.
- [Rich Response Rendering](interfaces/render-content-contract.md) — rendering boundary only.
- [Schema Versioning](interfaces/schema-versioning.md) — schema evolution/startup compatibility.

### Quality

- [Testing Standard](quality/testing-standard.md) — L0～L6 + OPVE/G0/G1/G2.
- [Test Oracle Classification](quality/test-oracle-classification.md) — Required/Optional/Informational oracle semantics.
- [CI Infrastructure Standard](quality/ci-infrastructure-standard.md) — v1 Local Web Required CI and optional compatibility evidence.
- [v1 Local Web Quality Reconciliation](quality/v1-local-web-quality-reconciliation.md) — Product Positioning ↔ Quality alignment.
- [Observability Standard](quality/observability-standard.md) — local diagnostics + decision/outcome observability.
- [Definition of Done](quality/definition-of-done.md) — Engineering / Policy Correctness / Learning Evidence gate separation.
- [Security Standard](quality/security-standard.md) — Learning Core hard rules plus LocalOwner/Workspace/LocalSecretStore security.

Quality Specs own technical/quality gates. Product Acceptance remains upstream in `PRODUCT-DEFINITION.md` or an explicit Product Feature Spec.

### UI

- [UI Spec Index](ui/README.md)
- [Interactive Element System](ui/interactive-element-system.md)
- [Information Architecture](ui/information-architecture.md)
- [Screen Contracts](ui/screen-contracts.md)
- [Data Contracts](ui/data-contracts.md)
- [Visual System](ui/visual-system.md)
- [Quality and Migration](ui/quality-and-migration.md)
- [Component State Contracts](ui/component-state-contracts.md)

UI 导航/布局/控件继续由 current UI Design/ADR/UI specs 管理，不得创建第二 domain truth 或自行决定 v1 Product Scope。

## 4. Vertical Slice / Historical Supersession

Current implementation slices remain useful only inside current Product Definition / ADR / Spec authority.

Primary current/historical references include：

- [v0.3 Adaptive Teaching Loop](vertical-slices/v0.3-adaptive-teaching-loop.md) — Learning Core slice.
- [Book-to-Adaptive-Learning](vertical-slices/book-to-adaptive-learning.md) — book-learning E2E, with current v1 material/scope/runtime rules applied.
- [Local Single-User Authentication Removal](vertical-slices/local-single-user-authentication-removal.md) — identity migration.
- [UI-03 Interactive Element System](vertical-slices/ui-03-interactive-element-system-refactor.md) — UI architecture slice.
- [P1-03 Data Control](vertical-slices/p1-03-data-control-recovery.md) — local backup/export/erasure reference.
- [P1-06 First-use Onboarding](vertical-slices/p1-06-first-use-onboarding.md) — no-auth LocalOwner semantics.

Historical/partially superseded：

- [P1-05 Account Lifecycle](vertical-slices/p1-05-account-lifecycle.md) — historical only; no Account/Auth resurrection.
- [P1-04C OCR Review](vertical-slices/p1-04c-library-ocr-review.md) — implemented optional/historical; not v1 core/release prerequisite.
- [P1-02 Model Settings](vertical-slices/p1-02-model-settings.md) — historical Desktop implementation; current new writes use ADR-0017/LSS/MODEL-CONFIG.

Vertical Slice 可以实现一个或多个 Product Capability，但不能以自身存在作为新 Product Requirement 的来源。实时工作状态属于 Linear；EXEC index 不复制 Product Backlog。

## 5. v0.3 Learning Core Invariants

```text
Knowledge truth / relations     → SYS01
EvidenceBundle                  → SYS02
LearnerState / MasteryEstimate  → SYS03
AssessmentResult                → SYS04
TeachingAction                  → SYS05
LearningPlan / Activity         → SYS06
ReviewSchedule / next_due       → SYS07
Model / Tool execution          → SYS08
```

And：

```text
TeachingStage != LearnerState
AssessmentResult != MasteryEstimate
DecisionTrace != OutcomeObservation
Experiment assignment probability != action selection propensity
SYS02/SYS08 may tighten but not expand TeachingAction envelope
LLM/Agent never owns final TeachingAction or canonical learner/assessment/plan/review truth
```

## 6. Product Definition → Spec Traceability

Specs SHOULD reference relevant `CAP-*` / `PD-REQ-*` when new or substantially refactored contracts are created. Existing stable Spec IDs do not need bulk renaming.

| Product Definition / Constraint | Primary Contracts |
|---|---|
| `CAP-01` Material grounding | Domain, SPEC-D01, SYS01, SYS02, WSP, LIB, MATLIFE |
| `CAP-02` Goal / success | SYS06 Goal Management, Goal Mapping, Domain |
| `CAP-03` Readiness / diagnosis / planning | SYS06 Planner, Diagnostic Bootstrap, SYS04, SYS03 |
| `CAP-04` Adaptive Learning Activity | SYS05, SYS08, Activity Lifecycle, rendering/UI contracts |
| `CAP-05` Attempt / Assessment / Evidence | SYS04, SYS03, Event/Domain contracts |
| `CAP-06` Review / retention / transfer | SYS07, SYS03/04/05, Outcome/Experiment contracts |
| `CAP-07` Continuity / next-step | Workspace scope, query/UI contracts, Activity lifecycle |
| `CAP-08` Local Data & AI Control | LID, WSP, Persistence, Data Control, LSS, MODEL-CONFIG, Security |
| Local Web / loopback | System Architecture, Dependency Rules, LID-* |
| No Account/Login | LID-*, State Ownership, Security |
| LocalOwner | LID-*, Domain, Persistence |
| Workspace isolation / `PD-RULE-009` | ADR-0016, WSP-*, Domain, State Ownership |
| LearningSession != DialogSession | ADR-0016, WSP-* |
| Import = ingest + copy | SPEC-D01, WSP SourceFile, Persistence |
| SQLite production baseline | Architecture, Persistence |
| No external infra prerequisite / `PD-REQ-0804` | Architecture, Dependency Rules, Persistence, CI Standard |
| LearnerState from Evidence / `PD-RULE-007` | WSP-033, SYS03, State Ownership |
| Workspace-scoped Retrieval | WSP-073, SYS02 |
| Trash → Restore/Permanent Delete / `PD-REQ-0104` | MATLIFE-*, LIB-*, Persistence, Data Control |
| BYOK local secret / `PD-REQ-0803` | ADR-0017, LSS-*, MODEL-CONFIG, Security |
| Source-grounded provenance / `PD-RULE-006` | Domain, SPEC-D01, SYS02 |
| local durable jobs | Architecture, Persistence, SPEC-D01 |
| Backup != Export | Persistence, Data Control |
| v1 core formats / `PD-REQ-0102` | SPEC-D01, LIB-* |
| Full OCR not v1 core | `PRODUCT-DEFINITION` scope, LIB-050, ADR-0008 supersession |
| No open-ended autonomous Agent | Product Positioning, Architecture, SYS08, SYS05 |

## 7. Current ADR Supersession Relevant to Specs

### ADR-0008

Partially superseded. OCR-as-core/global-library/archive mechanics are historical. Current Material scope/delete contracts are Product Definition + WSP/LIB/MATLIFE.

### ADR-0013

Partially superseded. Electron/safeStorage/Desktop IPC mechanics are historical. Current credential implementation uses ADR-0017 + LSS + MODEL-CONFIG.

### ADR-0015

Current LocalOwner/no-auth authority. Historical Account/JWT/AuthSession product semantics do not apply to new v1 code.

### ADR-0016

Current Workspace/Project/Session ownership and migration authority. `user_documents.id` remains stable Material identity; no second Material truth.

### ADR-0017

Current LocalSecretStore authority. Production supports exact approved OS-backed keyring adapters with fail-closed backend selection and non-secret activation journal.

## 8. Migration and Compatibility Rules

- Legacy fields MAY remain read-compatible only with explicit canonical target and retirement condition.
- `user_id` / `pseudonym_id` MAY temporarily be storage compatibility for LocalOwner/Learner; never Account semantics.
- existing `user_documents.id` migrates as stable Material identity; no parallel writable Material table.
- embedded file columns migrate toward normalized managed SourceFile; no permanent dual-write.
- owner-global records migrate to deterministic default Workspace before Workspace scope becomes strict.
- legacy DialogSession is not promoted to LearningSession by naming; unprovable historical bindings remain null.
- legacy retrieval/cache keys must migrate to Workspace scope.
- environment/Desktop model credentials are not silently imported into production LocalSecretStore.
- legacy deleted rows migrate per MATLIFE source-present/source-missing rules.
- historical OCR MAY remain immutable/optional；v1 new ingest does not require OCR.
- PostgreSQL/Redis compatibility MAY remain Optional；production-local correctness does not depend on them.

Compatibility existence does not make a retired feature `CURRENT/COMMITTED` in Product Definition.

## 9. Spec-ID Governance

Existing requirement IDs MUST NOT be reused to change unrelated meaning.

Current v1 additive families include：

```text
LID-*      LocalOwner / no-auth identity
WSP-*      Workspace / Project / LearningSession scope
LSS-*      Local SecretStore / model activation
MATLIFE-*  Material Trash / Restore / Permanent Delete
```

Product-level IDs use `CAP-*` / `PD-RULE-*` / `PD-REQ-*` / `PD-AC-*` and remain distinct from technical Spec IDs。

Historical requirements remain traceable with supersession notes rather than silently changing their meaning。

## 10. Acceptance / Release Claim Boundary

Every delivery must separate：

```text
Product Acceptance
UX Acceptance
Engineering / Technical Gate
Quality / Security Gate
Policy / Contract Correctness Gate when applicable
Learning Evidence Gate
```

Local Web、SQLite、Workspace、BYOK、Trash、安全存储、CI 或 UI correctness **do not prove learning efficacy**.

Primary real-user learning outcomes remain：independent success、delayed retention、transfer、unit-time capability gain. Engagement/turn count/usage time are not primary learning KPIs.

## 11. Implementation Rule

Before any Codex/TraeCode task：

1. read `docs/product/PRODUCT-STRATEGY.md`；
2. read `docs/product/PRODUCT-POSITIONING.md`；
3. read `docs/product/PRODUCT-DEFINITION.md` and identify applicable `CAP-*` / `PD-REQ-*` / Product Acceptance；
4. read the applicable current Canonical Design / ADR / Spec family；
5. check supersession before using historical ADR/Vertical Slice；
6. treat code-vs-Spec mismatch as implementation drift by default；
7. stop with `POSITIONING GAP` if implementation would violate the frozen product boundary；
8. stop with `PRODUCT DEFINITION GAP` if Capability / Feature Scope / Product Rule / Product Acceptance is missing or contradicted；
9. stop with `BLOCKED_BY_SPEC_GAP` if a required ownership/security/data decision is still ambiguous；
10. otherwise execute mechanically and prove the applicable Product / UX / Technical / Quality Acceptance with current evidence。
