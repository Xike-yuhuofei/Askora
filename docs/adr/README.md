# Askora Architecture Decision Records

> `docs/adr/` 记录已经被接受、会改变或解释 Implementation Spec 的重大架构决策。

## 1. 何时必须建立 ADR

以下变化必须先有 ADR，再改 Spec 和代码：

- 八类技术系统职责/所有权变化；
- 公共领域对象语义变化；
- 新的核心状态事实源；
- 模块化单体 → 微服务等部署架构变化；
- 数据库/事件基础设施重大替换；
- baseline 算法被新的生产主算法替换；
- 新增高权限 Agent/tool 执行模型；
- 破坏性公共 Schema/API 演进策略；
- 对安全、隐私、重放或审计不变量的改变。

局部实现细节、私有重构、等价性能优化通常不需要 ADR。

## 2. 权威链

```text
Canonical Design
→ Accepted ADR
→ Updated Implementation Spec
→ EXEC Plan
→ Code/Test
```

ADR 不能长期与 Spec 冲突。ADR 接受后必须同步更新受影响 Spec；Codex 仍以最新 Spec 作为直接实现合同。

## 3. 文件模板

```markdown
# ADR-XXXX — Title

Status: proposed | accepted | superseded | rejected
Date: YYYY-MM-DD
Decision owners: ...
Affected specs: ...

## Context
## Decision
## Alternatives Considered
## Consequences
## Migration / Rollback
## Validation
## Supersedes / Superseded By
```

## 4. Codex 权限

Codex 可以指出需要 ADR 的 `SPEC GAP`。当用户已明确授权目标或明确委托架构自治时，
Codex 可以为该目标创建并接受 ADR，并继续同步 Spec、EXEC、代码和测试；不再要求另一次
顶层人工批准。

由 Codex 接受的 ADR 必须记录：

- `Decision authority: user-delegated Codex`；
- 对应用户目标/任务范围；
- 至少一个真实备选方案与未采用原因；
- 状态所有权、重复 truth 风险、迁移/回滚或 forward-fix；
- 安全、隐私、replay、idempotency 与验证门禁；
- 对 Engineering / Policy / Learning Evidence 声明边界的影响。

没有明确用户目标授权时，Codex 仍只能提出 `proposed` ADR，不能自行标记为 `accepted`。

## 5. ADR Index

| ADR | Title | Status | Date |
|---|---|---|---|
| `ADR-0001` | Teaching Strategy Ontology | accepted | 2026-08-07 |
| `ADR-0002` | Constrained Deterministic Teaching Policy Architecture | accepted | 2026-08-07 |
| `ADR-0003` | Policy Runtime Profile Source and Activation Resolution | accepted | 2026-08-08 |
| `ADR-0004` | Guided Book Learning and Durable Transcript | accepted | 2026-08-08 |
| `ADR-0005` | Policy-bound Real-model Rendering | accepted | 2026-08-08 |
| `ADR-0006` | Workspace Read-model Scope and Missing Objective Metadata | accepted | 2026-08-09 |
| `ADR-0007` | SYS06 Activity Lifecycle and Completion | accepted | 2026-08-09 |
| `ADR-0008` | Library Management, Deduplication and OCR Governance | accepted | 2026-08-09 |
| `ADR-0012` | Unified Recovery Control Plane and Bootstrap Diagnostics | accepted | 2026-08-09 |
| `ADR-0013` | Desktop Model Credential and Activation | accepted | 2026-08-09 |
| `ADR-0103` | Local Data Recovery, Portability and Erasure | accepted | 2026-08-09 |
| `ADR-0106` | Fact-driven Onboarding Readiness and Presentation Preferences | accepted | 2026-08-09 |

### v0.3 ADR-C Resolution

`TeachingEpisode`、`LearningTrajectory`、`OutcomeObservation`、`ExperimentAssignment` 当前仍是 additive Design / Spec Delta，不改变八系统事实所有权，也没有形成新的核心 aggregate/service owner，因此该议题当时**不需要新增 ADR**。`ADR-0003` 后续用于独立的 Policy Runtime Profile 来源与激活解析决策。

## 6. v0.3 ADR Breaking Change Register

| ID | ADR | Breaking Surface | Current | New | Migration Required | Spec Delta Target |
|---|---|---|---|---|---|---|
| `BC-001` | ADR-0001 | Strategy enum | 9 top-level strategy families | 6 Strategy Families + move/pattern/modifier/deferred mapping | Yes | Domain Model + SYS05 (`SD-01`) |
| `BC-002` | ADR-0001 | TeachingAction semantics | `strategy_id + action_type` 承担混合语义 | Strategy Family + action template/move plan + modifiers + immutable semantic envelope | Yes | Domain Model + SYS05 (`SD-01`, `SD-05`) |
| `BC-003` | ADR-0001 / ADR-0002 | Support / exposure | integer `scaffold_level`, `hint_level`, `answer_exposure_max: 0..4` | orthogonal scaffold control + hint specificity + answer exposure + actual assistance | Yes | Domain Model + SYS03/SYS04/SYS05 (`SD-05`) |
| `BC-004` | ADR-0002 | Policy configuration | loose policy version / weights / state-machine config | immutable component-versioned `PolicyBundle` + atomic activation | Yes | SYS05 + Domain config (`SD-06`, `SD-07`) |
| `BC-005` | ADR-0002 | DecisionTrace probability / replay | generic `experiment.propensity` + incomplete replay inputs | assignment probability separated from `action_propensity`; deterministic propensity = null; explicit replayability | Yes | Decision Contract (`SD-08`) |
| `BC-006` | ADR-0001 / ADR-0002 | Legacy Socratic selector | Socratic selector/state machine can act as implicit policy owner | bounded move/legacy adapter behind SYS05 canonical selector | Yes | SYS05 + legacy adapter (`SD-01`, `SD-06`) |

Breaking change count: **6**.

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

Migration candidate count: **9**.
