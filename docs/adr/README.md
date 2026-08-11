# Askora Architecture Decision Records

> `docs/adr/` 记录已经被接受、会改变或解释 Canonical Design / Implementation Spec 的重大架构决策。  
> 所有 ADR 均受上位 `docs/product/PRODUCT-POSITIONING.md` 与 `docs/product/PRODUCT-DEFINITION.md` 约束；ADR 不拥有 Product Capability、v1 Feature Scope、Product Rule 或 Product Acceptance。

## 1. 何时必须建立 ADR

以下变化通常必须先有 ADR，再改 Spec 和代码，且不得突破已冻结 Product Positioning / Product Definition：

- 八类技术系统职责/所有权变化；
- 公共技术领域对象语义变化；
- 新的核心状态事实源；
- 模块化单体 → 微服务等部署架构变化；
- 数据库/事件基础设施重大替换；
- baseline 算法被新的生产主算法替换；
- 新增高权限 Agent/tool 执行模型；
- 破坏性公共 Schema/API 演进策略；
- 对安全、隐私、重放或审计不变量的改变；
- Local Web / Workspace / LocalOwner / local-first runtime 等已定义产品边界的重大实现方式变化；
- 多个 Design / Spec 方案都会满足同一个 Product Requirement，但会形成不同长期 architecture ownership / migration / security consequences。

局部实现细节、私有重构、等价性能优化通常不需要 ADR。

若拟议变化会：

- 突破 `PRODUCT-POSITIONING.md` 的 Category / Product Shape / Hard Constraints / Non-goals → 先处理 `POSITIONING GAP`；
- 新增/删除 Product Capability、改变 v1 Feature inclusion、Product Rule、Product Requirement 或 Product Acceptance → 先处理 `PRODUCT DEFINITION GAP`；
- 只是在已定义 Product WHAT 下选择新的 architecture / ownership / migration 方案 → 才由 ADR 拥有该决策。

不得创建下位 ADR 绕过 Product Positioning / Product Definition。

## 2. 权威链

```text
PRODUCT-STRATEGY.md
→ PRODUCT-POSITIONING.md
→ PRODUCT-DEFINITION.md
→ Current Canonical Design
→ Accepted ADR
→ Updated Implementation Spec
→ Linear Issue / EXEC
→ Code / Test
```

ADR 回答的是：

> **在既定 Product WHAT 与 Design 语义下，为什么选择这一重大系统/架构决策，以及它如何迁移、回滚和验证。**

ADR 不回答：

- 产品为什么值得做；
- 某 Capability 是否存在；
- 某 Feature 是否属于 v1；
- Product Acceptance 何时成立；
- 当前 Issue 是否 Done。

ADR 接受后必须同步更新受影响 current Design consolidation / Spec（适用时）；Codex 仍以最新 Product docs + current Design + applicable ADR + 最新 Spec 作为直接执行约束。

历史 ADR 如果被新的 Product Positioning / Product Definition / Canonical Design 部分 supersede，应保留原始决策记录，并明确标记：

- 哪些 Product Scope / mechanics 已 superseded；
- 哪些 architecture invariant 继续有效；
- current Experience / Design / implementation contract 在哪里；
- 禁止历史 ADR 反向覆盖当前上位产品定义。

## 3. 文件模板

```markdown
# ADR-XXXX — Title

Status: proposed | accepted | partially superseded | superseded | rejected
Date: YYYY-MM-DD
Decision owners: ...
Upper authority:
  - docs/product/PRODUCT-POSITIONING.md
  - docs/product/PRODUCT-DEFINITION.md
Product trace: CAP-* / PD-REQ-* / PD-RULE-* | N/A — infrastructure-only
Current design input: ...
Affected specs: ...

## Current Supersession / Authority Interpretation (if any)
## Context
## Decision
## Alternatives Considered
## Consequences
## Migration / Rollback
## Validation
## Supersedes / Superseded By
```

`Product trace` 的目的只是说明 ADR 服务哪个已定义 Product Requirement；不得在 ADR 中自行创造新的 `CAP-* / PD-REQ-* / PD-AC-*`。

## 4. Codex 权限

Codex 可以指出需要 ADR 的 `DESIGN GAP` / `SPEC GAP`。当用户已明确授权目标或明确委托架构自治时，Codex 可以为该目标创建并接受**下位架构 ADR**，并继续同步 Design/Spec、EXEC、代码和测试；不再要求另一次顶层人工批准。

由 Codex 接受的 ADR 必须记录：

- `Decision authority: user-delegated Codex`；
- 对应用户目标/任务范围；
- applicable Product trace；
- 至少一个真实备选方案与未采用原因；
- 状态所有权、重复 truth 风险、迁移/回滚或 forward-fix；
- 安全、隐私、replay、idempotency 与验证门禁；
- 对 Product / UX / Engineering / Policy / Learning Evidence 声明边界的影响。

Codex 的架构自治权限只作用于下位设计/架构，**不得自行突破 Frozen Product Positioning 或 Product Definition**。若发现目标本身需要改变 Product Scope，必须先报告正确的上游 GAP，而不是用 accepted ADR 制造既成事实。

## 5. ADR Index

| ADR | Title | Status | Date |
|---|---|---|---|
| `ADR-0001` | Teaching Strategy Ontology | accepted | 2026-08-07 |
| `ADR-0002` | Constrained Deterministic Teaching Policy Architecture | accepted | 2026-08-07 |
| `ADR-0003` | Policy Runtime Profile Source and Activation Resolution | accepted | 2026-08-08 |
| `ADR-0004` | Guided Book Learning and Durable Transcript | accepted | 2026-08-08 |
| `ADR-0005` | Policy-bound Real-model Rendering | accepted | 2026-08-08 |
| `ADR-0006` | Workspace Read-model Scope and Missing Objective Metadata | accepted; current Workspace product meaning governed by Product Definition | 2026-08-09 |
| `ADR-0007` | SYS06 Activity Lifecycle and Completion | accepted | 2026-08-09 |
| `ADR-0008` | Library Management, Deduplication and OCR Governance | **partially superseded by Product Positioning / Product Definition** — OCR-as-core/global-library/archive mechanics retired | 2026-08-09 |
| `ADR-0009` | Local-first Identity and Privacy Lifecycle | partially superseded by ADR-0015 | 2026-08-09 |
| `ADR-0010` | Goal Definition, State, Draft and Safe Replan | accepted | 2026-08-09 |
| `ADR-0011` | Goal Achievement Measurement and Evidence Gate | accepted | 2026-08-09 |
| `ADR-0012` | Unified Recovery Control Plane and Bootstrap Diagnostics | accepted | 2026-08-09 |
| `ADR-0013` | Desktop Model Credential and Activation | **partially superseded** — Desktop mechanics retired; current CAP-08/BYOK semantics = Product Definition + ADR-0017 + LSS | 2026-08-09 |
| `ADR-0014` | User-job-driven Information and Interaction Architecture | **partially superseded by ADR-0018**; retained semantics consolidated into current Experience Design | 2026-08-10 |
| `ADR-0015` | Local Single-User Identity Without Authentication | accepted | 2026-08-10 |
| `ADR-0016` | Workspace, LearningProject and LearningSession Scope Ownership | accepted | 2026-08-10 |
| `ADR-0017` | OS-backed LocalSecretStore and Crash-consistent Model Activation | accepted | 2026-08-10 |
| `ADR-0018` | UX Workspace Context and Three-Column Learning Architecture | accepted; current experience representation consolidated under `docs/design/experience/**` | 2026-08-10 |
| `ADR-0019` | UI Workspace Context and Learning Context Read Projections | accepted | 2026-08-11 |
| `ADR-0020` | Learning Conversation Message Presentation and Interaction Boundary | accepted | 2026-08-11 |
| `ADR-0103` | Local Data Recovery, Portability and Erasure | accepted; account-specific language subject to ADR-0015/current Product Definition | 2026-08-09 |
| `ADR-0106` | Fact-driven Onboarding Readiness and Presentation Preferences | accepted | 2026-08-09 |
| `ADR-0107` | Account Deletion Uses the Canonical Data Erasure Workflow | partially superseded by ADR-0015 | 2026-08-09 |

## 6. Current v1 Architecture Decisions

### ADR-0016 — Workspace / Project / LearningSession

ADR-0016 closes the implementation ownership gap for `PRODUCT-DEFINITION.md` 中的 `Workspace / LearningProject / LearningSession` product objects；它不重新定义这些 Product Objects 的产品意义。

Current decisions：

- Workspace → Platform Workspace Registry；
- LearningProject / ProjectMaterial → Platform Workspace / Product Organization；
- LearningSession → Platform Learning Session Registry；
- LearningSession is not DialogSession and owns no transcript/TeachingAction/Assessment/Mastery truth；
- existing `user_documents.id` remains stable Material identity during migration；
- do not create a parallel writable `materials` truth；
- normalize managed SourceFile separately；
- existing LocalOwner-global data migrates idempotently into one default Workspace；
- LearnerEvidence/Mastery/LearnerState/Review become Workspace-specific；
- cross-workspace refs fail closed。

Direct contract：`docs/specs/platform/workspace-project-session-scope.md` (`WSP-*`)。

### ADR-0017 — LocalSecretStore

ADR-0017 closes the security-sensitive Local Web BYOK adapter gap under `CAP-08 / PD-REQ-0803`。

Current decisions：

```text
macOS   → keyring.backends.macOS.Keyring
Windows → keyring.backends.Windows.WinVaultKeyring
```

with：

- exact production backend allowlist；
- no automatic/third-party/Null/file fallback；
- Windows local-machine persistence；
- opaque random secret refs；
- browser/public API cannot read stored secrets；
- ordinary SQLite stores only non-secret profile/ref/activation journal；
- durable phase journal reconciles SQLite + OS credential-store crash consistency；
- clear commits disabled routing before best-effort orphan-secret cleanup；
- restore missing secret → degraded/re-enter, never `.env` resurrection。

Direct contracts：`docs/specs/platform/local-secret-store.md` (`LSS-*`) + `systems/08-model-configuration.md` + `quality/security-standard.md`。

### ADR-0018 — UX Workspace Context / Three-Column Learning

ADR-0018 partially supersedes ADR-0014；其 current retained experience semantics 已 consolidation 到：

- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`；
- `docs/design/experience/LEARNING-EXPERIENCE.md`；
- `docs/design/experience/INTERACTION-MODEL.md`。

Retained decision consequences：

- Learning no longer exposes Goal/Plan/Progress/History as permanent L1 management facets；
- left rail = Where (product nav + canonical Workspace), center = Learn (sole Primary Canvas), right rail = hideable Reference/Notes；
- default-collapsed Learning Context Drawer above the composer；
- Workspace is shared canonical context across all three columns；
- Library normal v1 UI does not expose OCR。

其中 “OCR 是否是 v1 core / deferred candidate 是否进入 v1” 的 Product Scope authority 属于 Product Definition；ADR-0018 / Experience Design 拥有其 UX consequence，不是第二份 Product Scope owner。

Direct contracts：current Experience Design + `docs/specs/ui/**` + applicable UI vertical slice。历史 clause-level supersession matrix 保留在 ADR-0018 Section 8 解释演进。

### ADR-0019 — UI Workspace Read Projections

ADR-0019 closes the read-query gaps intentionally left open by ADR-0018:

- canonical current Workspace comes from Platform Workspace Registry, never route/frontend state；
- Drawer stage comes from exact SYS05 TeachingAction；
- next 1..3 directions come from exact ordered SYS06 LearningActivity refs；
- stage-goal copy is a versioned server-side presentation catalog, not a second Goal/Policy truth；
- query assembly is read-only, current-Workspace scoped, side-effect free and uses honest MISSING/PARTIAL/STALE semantics；
- no database schema or migration change。

Direct contracts：`state-ownership.md` + `api-contract.md` + `ui/data-contracts.md` (`UXA-DATA-200/220..223`)。

### ADR-0020 — Learning Conversation Message Boundary

ADR-0020 closes the Message System Prototype governance gap：

- canonical target = LearningActivity-scoped、SYS08-owned presentation/transcript artifact；
- Conversation/Message/Block do not become LearningEvidence or a ninth learning owner；
- new `LearningMessageV1` is separate from unchanged, non-interactive `RenderPayloadV1`；
- six typed blocks use exact owner/provenance/trace refs；
- frontend only renders server-issued capabilities and dispatches narrow owner commands；
- assessment/mastery/teaching/activity/review states remain split across SYS03～SYS07；
- legacy Dialog/RenderPayload paths are bounded adapters with explicit retirement conditions。

Direct contracts：`docs/specs/interfaces/learning-conversation-message-system-spec-delta.md` (`LCMS-*`) + LCMS Vertical Slice / EXEC-075。

## 7. Historical Supersession Notes

### Local Single-User Identity Supersession

ADR-0015 supersedes ADR-0009 / ADR-0107 current product semantics for Account、Login、Password、JWT、AuthSession、Recovery Kit、Account Deletion Lifecycle。

Owner-safe erasure、privacy/no-resurrection 等仍有独立数据治理价值的原则继续由最新 `LID-*` 与 P1-03 contracts 承接。Product no-auth meaning 由 Product Definition / Positioning 拥有；ADR-0015 拥有其 identity architecture consequence。

### ADR-0008

Product Positioning / Product Definition superseded：

- full OCR Pipeline as v1 core/release requirement；
- current-user global library scope；
- archive/restore as the primary ordinary-delete product model。

Retained：

- SYS01 metadata/content ownership；
- duplicate suggestion, no automatic merge；
- rebuildable search/index projections；
- provenance/version/idempotency；
- optional OCR candidate safety。

Current contracts：`systems/01-library-management.md` + `interfaces/content-ingestion-contract.md` + `interfaces/material-lifecycle-contract.md`。

### ADR-0013

Product Positioning / Product Definition / ADR-0017 superseded：

- Electron `safeStorage` required path；
- Desktop vault/main/preload IPC；
- desktop child-backend/launcher mechanics；
- macOS App as v1 product shell。

Retained：

- SYS08 owns ModelRouteProfile；
- secret/routing separation；
- secure local persistence；
- probe-before-activation；
- revision/concurrency/rollback；
- no silent failover/no secret leakage。

Current contract：Product Definition `CAP-08 / PD-REQ-0803` + ADR-0017 + `LSS-*` + `MODEL-CONFIG-*`。

## 8. v0.3 ADR Breaking Change Register

| ID | ADR | Breaking Surface | Current | New | Migration Required | Spec Delta Target |
|---|---|---|---|---|---|---|
| `BC-001` | ADR-0001 | Strategy enum | 9 top-level strategy families | 6 Strategy Families + move/pattern/modifier/deferred mapping | Yes | Domain Model + SYS05 (`SD-01`) |
| `BC-002` | ADR-0001 | TeachingAction semantics | `strategy_id + action_type` mixed semantics | Strategy Family + immutable action/move/modifier/envelope | Yes | Domain Model + SYS05 |
| `BC-003` | ADR-0001 / ADR-0002 | Support / exposure | integer fields | orthogonal scaffold/hint/exposure/assistance | Yes | Domain + SYS03/04/05 |
| `BC-004` | ADR-0002 | Policy configuration | loose config | immutable component-versioned PolicyBundle | Yes | SYS05 |
| `BC-005` | ADR-0002 | DecisionTrace probability / replay | generic propensity | assignment probability separated; deterministic action propensity null | Yes | Decision Contract |
| `BC-006` | ADR-0001 / ADR-0002 | Legacy Socratic selector | implicit policy owner | bounded adapter behind SYS05 | Yes | SYS05 |
| `BC-V1-001` | Product Positioning / ADR-0013 history | Product shell | Electron/Desktop target | Local Web Browser → loopback Local Server | Yes | Architecture + MODEL-CONFIG |
| `BC-V1-002` | Product Definition / ADR-0016 | Material/scope | owner-global | real Workspace + Project/Session scope | Yes | WSP + Domain/SYS01/SYS02 |
| `BC-V1-003` | Product Positioning / Product Definition | Persistence | service-compatible framing | SQLite production-local; distributed infra optional | Yes | Persistence/Architecture |
| `BC-V1-004` | ADR-0017 | Provider credential | Electron vault/env | OS-backed LocalSecretStore + activation journal | Yes | LSS + MODEL-CONFIG + SEC |

## 9. Migration Candidate Register

| Candidate | Classification | Required handling |
|---|---|---|
| historical strategy records | `BEST_EFFORT` | preserve original value; versioned legacy mapping |
| historical TeachingAction | `BEST_EFFORT` | retain payload; project when reconstructable |
| old scaffold/hint/exposure fields | `AMBIGUOUS` | explicit mapping or unknown; never guess |
| legacy Socratic selector | `DEFER_TO_SPEC` | bounded adapter only; SYS05 final owner |
| old policy config | `BEST_EFFORT` | exact PolicyBundle where reconstructable |
| old DecisionTrace propensity | `AMBIGUOUS` | unresolved → null/unknown + reason |
| historical replay | `BEST_EFFORT` | FULL only with exact historical refs/config |
| Desktop model vault / IPC | `DEFER_TO_SPEC` | v1 new writes use ADR-0017/LSS; no silent vault/env import |
| owner-global library/goal/learner scope | `DEFER_TO_SPEC` | migrate through default Workspace per ADR-0016/WSP |
| legacy `UserDocument` material storage | `DEFER_TO_SPEC` | preserve ID as Material; normalize SourceFile; no second truth |
| legacy ordinary document delete | `DEFER_TO_SPEC` | source-present deleted rows → Trash; already-removed source → terminal legacy tombstone per MATLIFE |

All migration work MUST preserve provenance and must not keep retired mechanics as permanent dual truth。
