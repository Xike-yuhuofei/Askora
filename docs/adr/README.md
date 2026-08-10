# Askora Architecture Decision Records

> `docs/adr/` 记录已经被接受、会改变或解释 Implementation Spec 的重大架构决策。  
> 所有 ADR 均受上位 `docs/product/PRODUCT-POSITIONING.md` 约束。

## 1. 何时必须建立 ADR

以下变化必须先有 ADR，再改 Spec 和代码，且不得突破已冻结 Product Positioning：

- 八类技术系统职责/所有权变化；
- 公共领域对象语义变化；
- 新的核心状态事实源；
- 模块化单体 → 微服务等部署架构变化；
- 数据库/事件基础设施重大替换；
- baseline 算法被新的生产主算法替换；
- 新增高权限 Agent/tool 执行模型；
- 破坏性公共 Schema/API 演进策略；
- 对安全、隐私、重放或审计不变量的改变；
- Local Web / Workspace / LocalOwner / local-first runtime 等上位边界的实现方式发生重大变化。

局部实现细节、私有重构、等价性能优化通常不需要 ADR。

若拟议变化会突破 `PRODUCT-POSITIONING.md` 的 v1 Hard Constraints / Non-goals，必须先修改并重新冻结 Product Positioning，而不是创建下位 ADR 绕过它。

## 2. 权威链

```text
PRODUCT-POSITIONING.md
→ Canonical Design / Design Delta
→ Accepted ADR
→ Updated Implementation Spec
→ EXEC Plan
→ Code/Test
```

ADR 不能长期与 Product Positioning 或 Spec 冲突。ADR 接受后必须同步更新受影响 Spec；Codex 仍以最新上位约束 + 最新 Spec 作为直接实现合同。

历史 ADR 如果被新的 Product Positioning / Canonical Design 部分 supersede，应保留原始决策记录，并明确标记：

- 哪些 mechanics 已 superseded；
- 哪些 invariant 继续有效；
- 当前 implementation contract 在哪里；
- 禁止历史 ADR 反向覆盖当前上位产品定位。

## 3. 文件模板

```markdown
# ADR-XXXX — Title

Status: proposed | accepted | partially superseded | superseded | rejected
Date: YYYY-MM-DD
Decision owners: ...
Upper authority: docs/product/PRODUCT-POSITIONING.md
Affected specs: ...

## Current Supersession (if any)
## Context
## Decision
## Alternatives Considered
## Consequences
## Migration / Rollback
## Validation
## Supersedes / Superseded By
```

## 4. Codex 权限

Codex 可以指出需要 ADR 的 `SPEC GAP`。当用户已明确授权目标或明确委托架构自治时，Codex 可以为该目标创建并接受 ADR，并继续同步 Spec、EXEC、代码和测试；不再要求另一次顶层人工批准。

由 Codex 接受的 ADR 必须记录：

- `Decision authority: user-delegated Codex`；
- 对应用户目标/任务范围；
- 至少一个真实备选方案与未采用原因；
- 状态所有权、重复 truth 风险、迁移/回滚或 forward-fix；
- 安全、隐私、replay、idempotency 与验证门禁；
- 对 Engineering / Policy / Learning Evidence 声明边界的影响。

Codex 的架构自治权限只作用于下位设计，**不得自行突破 Frozen Product Positioning**。没有明确用户目标授权时，Codex 只能提出 `proposed` ADR，不能自行标记为 `accepted`。

## 5. ADR Index

| ADR | Title | Status | Date |
|---|---|---|---|
| `ADR-0001` | Teaching Strategy Ontology | accepted | 2026-08-07 |
| `ADR-0002` | Constrained Deterministic Teaching Policy Architecture | accepted | 2026-08-07 |
| `ADR-0003` | Policy Runtime Profile Source and Activation Resolution | accepted | 2026-08-08 |
| `ADR-0004` | Guided Book Learning and Durable Transcript | accepted | 2026-08-08 |
| `ADR-0005` | Policy-bound Real-model Rendering | accepted | 2026-08-08 |
| `ADR-0006` | Workspace Read-model Scope and Missing Objective Metadata | accepted; workspace semantics additionally governed by Product Positioning | 2026-08-09 |
| `ADR-0007` | SYS06 Activity Lifecycle and Completion | accepted | 2026-08-09 |
| `ADR-0008` | Library Management, Deduplication and OCR Governance | **partially superseded by Product Positioning** — OCR-as-core/global-library/archive mechanics retired | 2026-08-09 |
| `ADR-0009` | Local-first Identity and Privacy Lifecycle | partially superseded by ADR-0015 | 2026-08-09 |
| `ADR-0010` | Goal Definition, State, Draft and Safe Replan | accepted | 2026-08-09 |
| `ADR-0011` | Goal Achievement Measurement and Evidence Gate | accepted | 2026-08-09 |
| `ADR-0012` | Unified Recovery Control Plane and Bootstrap Diagnostics | accepted | 2026-08-09 |
| `ADR-0013` | Desktop Model Credential and Activation | **partially superseded by Product Positioning** — Desktop/Electron mechanics retired; routing/secret invariants retained | 2026-08-09 |
| `ADR-0014` | User-job-driven Information and Interaction Architecture | accepted | 2026-08-10 |
| `ADR-0015` | Local Single-User Identity Without Authentication | accepted | 2026-08-10 |
| `ADR-0103` | Local Data Recovery, Portability and Erasure | accepted; account-specific language subject to ADR-0015/Product Positioning | 2026-08-09 |
| `ADR-0106` | Fact-driven Onboarding Readiness and Presentation Preferences | accepted | 2026-08-09 |
| `ADR-0107` | Account Deletion Uses the Canonical Data Erasure Workflow | partially superseded by ADR-0015 | 2026-08-09 |

### v0.3 ADR-C Resolution

`TeachingEpisode`、`LearningTrajectory`、`OutcomeObservation`、`ExperimentAssignment` 当前仍是 additive Design / Spec Delta，不改变八系统事实所有权，也没有形成新的核心 aggregate/service owner，因此该议题当时**不需要新增 ADR**。`ADR-0003` 后续用于独立的 Policy Runtime Profile 来源与激活解析决策。

### Local Single-User Identity Supersession

ADR-0015 明确 supersede ADR-0009 / ADR-0107 中以下当前产品语义：Account、Login、Password、JWT、AuthSession、Recovery Kit、Account Deletion Lifecycle。

owner-safe erasure、privacy/no-resurrection 等仍有独立数据治理价值的原则继续由最新 `LID-*` 与 P1-03 合同承接。

### Product Positioning Supersession — ADR-0008 / ADR-0013

`PRODUCT-POSITIONING.md` 在 2026-08-10 成为 Askora v1 及后续设计的上位 Frozen Baseline，并直接改变两份历史 ADR 的适用范围：

#### ADR-0008

已 supersede：

- 完整 OCR Pipeline 是 v1 core/release requirement；
- current-user global library scope；
- archive/restore 作为普通删除的最高产品语义。

继续保留：

- SYS01 metadata/content ownership；
- duplicate detection 只形成 suggestion，不自动 merge；
- search/index projection 可重建；
- provenance / version / idempotency；
- optional OCR candidate 未接纳不得进入 learner-visible truth。

当前合同：`systems/01-library-management.md` + `interfaces/content-ingestion-contract.md`。

#### ADR-0013

已 supersede：

- Electron `safeStorage` 必需路径；
- Desktop vault/main/preload IPC；
- desktop child-backend/launcher mechanics；
- macOS App 是 v1 正式产品 shell。

继续保留：

- SYS08 owns ModelRouteProfile semantics；
- secret/routing separation；
- secure local secret persistence；
- probe-before-activation；
- version/concurrency/rollback；
- no silent failover / no secret leakage。

当前合同：`systems/08-model-configuration.md`。

## 6. v0.3 ADR Breaking Change Register

| ID | ADR | Breaking Surface | Current | New | Migration Required | Spec Delta Target |
|---|---|---|---|---|---|---|
| `BC-001` | ADR-0001 | Strategy enum | 9 top-level strategy families | 6 Strategy Families + move/pattern/modifier/deferred mapping | Yes | Domain Model + SYS05 (`SD-01`) |
| `BC-002` | ADR-0001 | TeachingAction semantics | `strategy_id + action_type` 承担混合语义 | Strategy Family + action template/move plan + modifiers + immutable semantic envelope | Yes | Domain Model + SYS05 (`SD-01`, `SD-05`) |
| `BC-003` | ADR-0001 / ADR-0002 | Support / exposure | integer `scaffold_level`, `hint_level`, `answer_exposure_max: 0..4` | orthogonal scaffold control + hint specificity + answer exposure + actual assistance | Yes | Domain Model + SYS03/SYS04/SYS05 (`SD-05`) |
| `BC-004` | ADR-0002 | Policy configuration | loose policy version / weights / state-machine config | immutable component-versioned `PolicyBundle` + atomic activation | Yes | SYS05 + Domain config (`SD-06`, `SD-07`) |
| `BC-005` | ADR-0002 | DecisionTrace probability / replay | generic `experiment.propensity` + incomplete replay inputs | assignment probability separated from `action_propensity`; deterministic propensity = null; explicit replayability | Yes | Decision Contract (`SD-08`) |
| `BC-006` | ADR-0001 / ADR-0002 | Legacy Socratic selector | Socratic selector/state machine can act as implicit policy owner | bounded move/legacy adapter behind SYS05 canonical selector | Yes | SYS05 + legacy adapter (`SD-01`, `SD-06`) |
| `BC-V1-001` | Product Positioning / ADR-0013 history | Product shell | Electron/Desktop target | Local Web Browser → loopback Local Server | Yes | Architecture + MODEL-CONFIG |
| `BC-V1-002` | Product Positioning / ADR-0008 history | Material scope | owner/global library | Workspace-scoped Material / no Global Library | Yes | Domain + SYS01 + SYS02 |
| `BC-V1-003` | Product Positioning | Persistence | SQLite/PostgreSQL service-compatible framing | SQLite is v1 production baseline; distributed infra non-required | Yes | Persistence/Architecture |

## 7. v0.3 Migration Candidate Register

| Candidate | Classification | Required handling |
|---|---|---|
| historical strategy records | `BEST_EFFORT` | preserve original value; project through versioned legacy mapping; mark ambiguous/deferred cases |
| historical TeachingAction | `BEST_EFFORT` | retain original payload; project family/move/modifier/support semantics where reconstructable |
| old `scaffold_level` | `AMBIGUOUS` | cannot assume integer encodes cognitive control independently; require explicit mapping/version or unknown |
| old `hint_level` | `AMBIGUOUS` | cannot safely infer new hint-specificity taxonomy without mapping provenance |
| old answer exposure scale | `BEST_EFFORT` | map 0–4 only through documented versioned conversion; uncertain values remain ambiguous |
| legacy Socratic selector/state machine | `DEFER_TO_SPEC` | migrate ownership to SYS05; retain only adapter/stage-definition/execution roles allowed by Spec Delta |
| old policy config | `BEST_EFFORT` | package reconstructable components into PolicyBundle; missing component versions degrade replayability |
| DecisionTrace old propensity field | `AMBIGUOUS` | do not assume historical `propensity` is action propensity; unresolved values project to null/unknown with migration reason |
| historical replay | `BEST_EFFORT` | full replay only when exact historical inputs/config exist; otherwise mark partial/not replayable |
| Desktop model vault / IPC | `DEFER_TO_SPEC` | migrate to Local Web ModelRouteProfile + LocalSecretStore; preserve secure secret/no-resurrection semantics |
| owner/global library document scope | `DEFER_TO_SPEC` | assign Workspace/Material ownership before new writes; no cross-workspace default search |

Migration candidates must preserve old data/replay provenance without keeping retired product mechanics as permanent second truth.
