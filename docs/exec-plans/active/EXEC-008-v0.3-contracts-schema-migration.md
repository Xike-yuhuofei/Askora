# EXEC-008 — v0.3 Contracts + Schema Migration

> Priority：P0 Foundation  
> Status：READY_AFTER_EXEC-007  
> Depends on：EXEC-007

## Objective

把 v0.3 Spec Delta 的公共对象、枚举、持久化语义与兼容迁移正式落到代码，使 v0.3 canonical writer 只写新合同，并为后续 SYS05 policy kernel 提供稳定、可 replay 的 typed foundation。

本 EXEC 不实现完整 policy scoring/transition 算法。

## Required Specs

开始前 MUST 读取根 `AGENTS.md` 与：

- `docs/specs/README.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`

## Current Reality

当前 `apps/backend/app/contracts/learning.py` 仍是 v0.2 contract baseline：

- `TeachingAction.strategy_id` / `strategy_version`；
- `action_type` 包含 legacy top-level `socratic_question` 等；
- `scaffold_level: int`；
- `hint_level: int`；
- `answer_exposure_max: 0..4`；
- `AssessmentResult.error_type` 仍含 `condition_omission`、`expression_incomplete`、`metacognitive` 等旧 taxonomy。

当前 `apps/backend/app/contracts/decisions.py`：

- `DecisionTrace.schema_version = "1.0"`；
- `DecisionExperiment.propensity` 未区分 experiment assignment probability 与 action propensity。

这些结构不能作为 v0.3 canonical writer contract 继续扩展。

## Allowed Files

```text
apps/backend/app/contracts/**
apps/backend/app/models/**
apps/backend/app/infrastructure/**
apps/backend/alembic/**
apps/backend/migrations/**             # 如仓库实际使用该目录
apps/backend/tests/contracts/**
apps/backend/tests/migrations/**
apps/backend/tests/fixtures/**
apps/backend/tests/replay/**           # 如需新建
apps/backend/tests/architecture/**
```

为 upcaster/compatibility reader 可修改最小必要 adapter 文件，但不得在此 EXEC 实现 policy engine。

## Forbidden Changes

- 不把旧九类 strategy enum 继续作为 canonical top-level enum；
- 不 permanent dual-write v0.2/v0.3 TeachingAction；
- 不猜测 lossy historical mapping；
- 不用当前 PolicyBundle/当前 learner state 补齐历史 exact-version 缺失；
- 不实现 executable policy DSL/Python rules；
- 不将 TeachingStage 写入 LearnerState；
- 不把 `assignment_probability` 填到 `action_propensity`；
- deterministic B3 不得写 `action_propensity=1.0`；
- 不修改 Design、ADR、Spec。

## Implementation Tasks

### T1 — v0.3 Canonical Ontology Contracts

实现唯一 canonical top-level `StrategyFamily`：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

同时实现四层 ontology 所需 typed contracts：

```text
StrategyFamily
TeachingAction
InteractionMove
ActionModifier
```

`SOCRATIC_PROBE` 只能是 bounded InteractionMove，不得成为 StrategyFamily。

### T2 — Assistance / Assessment Contracts

实现 canonical orthogonal axes：

```text
scaffold_control = NONE | LOW | MEDIUM | HIGH
hint_specificity = NONE | ORIENTATION | CONCEPTUAL_STRATEGIC | SUBGOAL | PARTIAL_STEP | BOTTOM_OUT
answer_exposure = NONE | PARTIAL | COMPLETE
assistance_state = INDEPENDENT | ASSISTED | ANSWER_EXPOSED
```

实现 canonical ErrorType 7 + UNKNOWN：

```text
KNOWLEDGE_GAP
CONCEPTUAL_MISCONCEPTION
METHOD_SELECTION
EXECUTION
RETRIEVAL_FAILURE
TRANSFER_FAILURE
EXPRESSION_FORMAT
UNKNOWN
```

`assessment_confidence` 与 `diagnostic_confidence` MUST 独立。

### T3 — TeachingContext / PolicyBundle / Validation Contracts

实现：

- immutable/exact-version TeachingContext snapshot；
- explicit missing/stale/low-confidence semantics；
- TeachingStage derived contract，但不得成为 learner truth；
- immutable/versioned PolicyBundle reference + digest + activation metadata；
- `INDEPENDENT_VALIDATION_REQUIRED` obligation contract/state reference。

### T4 — DecisionTrace v0.3

升级 DecisionTrace 以支持：

- exact TeachingContext/PolicyBundle/assignment refs；
- typed hard-constraint results；
- candidates/features/normalized scores；
- anti-oscillation/tie-break reason；
- `behavior_policy_type = DETERMINISTIC`；
- deterministic B3 `action_propensity = null`；
- experiment `assignment_probability` 独立字段；
- explicit replayability status/reason。

历史 v1 trace 保留 compatibility read/audit，不得静默重解释。

### T5 — Outcome / Experiment Data Contracts

仅建立最小 canonical foundation：

- TeachingEpisode；
- LearningTrajectory；
- OutcomeObservation；
- ExperimentAssignment。

不得在本 EXEC 实现学习效果因果归因算法。

### T6 — Persistence Migration

建立 schema migration/upcaster，使：

- 新 writer 只写 v0.3 canonical schema；
- legacy reader 可读取历史记录；
- 不创建永久 dual truth；
- migration 幂等/可检测；
- rollback/forward-fix 边界明确。

### T7 — Nine Migration Candidate Fixtures

为以下 9 类建立 executable fixtures：

1. historical strategy records；
2. historical TeachingAction；
3. old `scaffold_level`；
4. old `hint_level`；
5. old answer exposure scale；
6. legacy Socratic selector/state machine；
7. old policy config；
8. old DecisionTrace propensity；
9. historical replay。

每类 fixture MUST 输出：canonical target、compatibility behavior、ambiguity/lossiness、replay status、retirement condition。

## Acceptance Criteria

- `EXEC008-AC-001`：六类 StrategyFamily 是唯一 active canonical top-level strategy enum。
- `EXEC008-AC-002`：四层 ontology 可由 typed contract 验证，Socratic 无 top-level ownership。
- `EXEC008-AC-003`：orthogonal assistance axes 与 actual assistance contract 可序列化/持久化。
- `EXEC008-AC-004`：ErrorType 仅 7 + UNKNOWN，assessment/diagnostic confidence 分离。
- `EXEC008-AC-005`：TeachingContext immutable/exact-version；TeachingStage 不进入 LearnerState truth。
- `EXEC008-AC-006`：PolicyBundle immutable/versioned/digestable，历史 exact version 可引用。
- `EXEC008-AC-007`：deterministic DecisionTrace 的 `action_propensity is None`，assignment probability 独立。
- `EXEC008-AC-008`：9 migration fixtures 全覆盖，lossy/unknown mapping 不被猜测。
- `EXEC008-AC-009`：新 writer 不产生旧 integer assistance/legacy strategy canonical fields。
- `EXEC008-AC-010`：migration/upcaster 可重复执行且不改变已迁移语义。
- `EXEC008-AC-011`：historical exact refs 缺失时显式 `PARTIAL|NON_REPLAYABLE`。
- `EXEC008-AC-012`：无 blocking `SPEC GAP`。

## Required Tests

至少覆盖：

```text
contract serialization/deserialization
frozen/immutable semantics
invalid enum rejection
old -> v0.3 compatibility reads
9 migration fixtures
DecisionTrace probability separation
migration upgrade/check/replay
architecture ownership regression
```

最低命令：

```bash
cd apps/backend
uv run pytest tests/contracts tests/migrations tests/architecture
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic upgrade head
uv run alembic check
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Schema/contracts added or changed:
- ...

Migration matrix:
- candidate -> target -> replay status -> retirement condition

Writer cutover:
- old fields still writable? yes/no
- permanent dual-write? yes/no

Decision probability:
- behavior policy type
- action propensity
- assignment probability

AC Matrix:
- EXEC008-AC-001 ... EXEC008-AC-012

Tests:
- command -> result

SPEC GAP:
- none / details
```

只有 `Status: DONE` 才允许 EXEC-009 建立 SYS05 deterministic policy kernel。