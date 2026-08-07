# EXEC-009 — Deterministic Teaching Policy Kernel

> Priority：P0 Core  
> Status：READY_AFTER_EXEC-008  
> Depends on：EXEC-008

## Objective

实现 SYS05 的 B3 constrained deterministic Teaching Policy kernel，把已冻结的 TeachingContext + PolicyBundle 转换为唯一、可解释、可 replay 的 TeachingAction + DecisionTrace。

本 EXEC 只负责单次 decision kernel，不负责跨轮 anti-oscillation state transition 的完整实现；后者属于 EXEC-010。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与：

- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/observability-standard.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`

## Current Reality

v0.2 已有 canonical learning facade/orchestration，但当前 `apps/backend/app/domains/` 已确认没有 `teaching_policy/` bounded implementation；v0.2 `TeachingAction` 主要是公共 contract，而不是符合 ADR-0002 的完整 B3 policy stack。

EXEC-008 完成后应已有 v0.3 TeachingContext、PolicyBundle、TeachingAction、DecisionTrace contracts。本 EXEC MUST 在这些 contract 上实现，不得回退到旧 `strategy_id/scaffold_level/hint_level` selector。

## Allowed Files

优先：

```text
apps/backend/app/domains/teaching_policy/**
apps/backend/app/contracts/**              # 仅修复与已冻结 Spec 一致的实现缺陷
apps/backend/app/infrastructure/**         # PolicyBundle persistence/config adapter
apps/backend/tests/unit/**
apps/backend/tests/integration/**
apps/backend/tests/evals/**
apps/backend/tests/fixtures/**
apps/backend/tests/architecture/**
```

如现有仓库无 `tests/unit/`，可放入最相近的现有测试目录；不得为了目录统一重构其他 domain。

## Forbidden Changes

- LLM/Agent 不得选择 final TeachingAction；
- hard constraint 不得被 score、experiment、fallback、legacy selector 恢复；
- 不实现 RL/Bandit；
- 不实现 executable policy DSL/free-form Python policy rules；
- 不把 TeachingStage 持久化为 LearnerState；
- 不写 `action_propensity=1.0`；
- 不使用 engagement/turns/likes 作为 learning-value reward；
- 不把 arbitrary threshold 写成不可版本化常量；
- 不修改 Spec/ADR/Design。

## Implementation Tasks

### T1 — TeachingContext Validation

建立 SYS05 decision entry：

- 校验 exact refs/version/fingerprint；
- 显式处理 unavailable/missing/stale/low-confidence input；
- 禁止从 live mutable state 临时补值后伪装 exact snapshot；
- experiment assignment 若存在必须 exact-ref。

### T2 — Typed Hard Constraints

实现 `SYS05-241` 所要求的 hard-constraint families；每条必须具有：

```text
stable rule id
versioned parameters
input refs
pass/fail
reason code
forbidden candidate/action semantics
```

hard filter 后的 candidate 不允许复活。

### T3 — TeachingStage Derivation

从 TeachingContext 派生 TeachingStage：

- deterministic；
- versioned mapper；
- 可独立测试；
- 不写入 SYS03 learner truth。

### T4 — Candidate Generation

基于六类 StrategyFamily + typed TeachingAction vocabulary 构造 legal candidate set。

要求：

- candidate table/version 可追溯；
- candidate generation 与 scoring 解耦；
- UNKNOWN/low confidence 可产生 conservative probe/remediation candidate；
- candidate set 为空时返回 typed terminal/fallback reason，不让 LLM 自由补动作。

### T5 — Feature Builder & Normalization

建立 deterministic feature builder：

- feature provenance 指向 TeachingContext refs；
- missing semantics 明确；
- normalization 参数属于 PolicyBundle；
- feature 不可引用 outcome future data。

### T6 — Weighted Scoring

实现 normalized weighted scoring：

- weights exact-pin 到 PolicyBundle；
- score 只是 soft preference；
- hard constraint 优先级绝对高于 score；
- deterministic numeric behavior 有测试容差/排序规则。

### T7 — Stable Tie-break

实现稳定 tie-break：

- 明确 deterministic precedence；
- 不依赖 hash/random/unordered iteration；
- tie-break reason 写入 DecisionTrace。

### T8 — Immutable Output + DecisionTrace

输出 immutable TeachingAction + DecisionTrace，至少记录：

```text
context ref/fingerprint
policy bundle id/version/digest
hard-rule results
TeachingStage
candidate set
features
normalized scores
selected candidate
tie-break reason
behavior_policy_type=DETERMINISTIC
action_propensity=null
experiment assignment ref/probability if any
algorithm/version/reason codes
```

## Acceptance Criteria

- `EXEC009-AC-001`：same TeachingContext + PolicyBundle + ExperimentAssignment => same semantic TeachingAction。
- `EXEC009-AC-002`：hard-filtered candidate 无任何 code path 可被恢复。
- `EXEC009-AC-003`：required hard-constraint families 均有 typed rule + stable reason code。
- `EXEC009-AC-004`：TeachingStage deterministic 且不成为 LearnerState writer。
- `EXEC009-AC-005`：candidate generation 与 scoring 可独立测试。
- `EXEC009-AC-006`：feature provenance/missing semantics 可审计。
- `EXEC009-AC-007`：normalization/weights 均由 exact PolicyBundle 决定。
- `EXEC009-AC-008`：stable tie-break 不依赖 runtime randomness/order。
- `EXEC009-AC-009`：DecisionTrace 足以离线 replay 单次 decision，且 B3 `action_propensity is None`。
- `EXEC009-AC-010`：六类 StrategyFamily 均可由固定 context fixture 合法进入 candidate/selection 测试。
- `EXEC009-AC-011`：G0 hard-rule fixtures forbidden action = 0。
- `EXEC009-AC-012`：无 blocking `SPEC GAP`。

## Required Tests

至少：

```text
hard-rule unit/property tests
stage mapper tests
candidate table tests
feature/normalization tests
score determinism tests
tie-break determinism tests
same-input replay tests
six StrategyFamily fixtures
G0 forbidden-action tests
architecture ownership tests
```

最低命令：

```bash
cd apps/backend
uv run pytest tests/evals tests/integration tests/architecture
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Policy stack:
- context validation
- hard constraints
- stage mapper
- candidate generator
- feature builder
- normalization
- scoring
- tie-break

PolicyBundle:
- id/version/digest used by tests

Determinism:
- replay fixture -> result

G0:
- cases/pass rate/forbidden action count

AC Matrix:
- EXEC009-AC-001 ... EXEC009-AC-012

Tests:
- command -> result

SPEC GAP:
- none / details
```

只有 `Status: DONE` 才允许 EXEC-010 在该 kernel 上实现 sequential transition/anti-oscillation。