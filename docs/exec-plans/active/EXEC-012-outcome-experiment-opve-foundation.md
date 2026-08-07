# EXEC-012 — Outcome / Experiment / OPVE Foundation

> Priority：P0 Evaluation Foundation  
> Status：READY_AFTER_EXEC-011  
> Depends on：EXEC-011

## Objective

建立 v0.3 的 OutcomeObservation、TeachingEpisode、LearningTrajectory、ExperimentAssignment 与 OPVE（Offline Policy Verification & Evaluation）基础，使 Askora 能区分“决策时依据”和“后来学习结果”，能够离线验证 policy correctness，并为未来受控学习效果实验留下正确数据契约。

本 EXEC 不声称 adaptive policy 已证明提升学习效果，也不实现 RL/OPE。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与：

- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/observability-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`

## Current Reality

EXEC-008 应已建立 v0.3 Outcome/Experiment 最小 contracts，但 v0.2 主链没有完整 outcome attribution / OPVE gate。当前测试目录已存在 `tests/evals/`、`tests/fixtures/`、`tests/e2e/` 等基础，可在其上建立可执行 policy verification，而不是引入第二套实验平台。

## Allowed Files

```text
apps/backend/app/contracts/**
apps/backend/app/domains/teaching_policy/**
apps/backend/app/domains/assessment/**
apps/backend/app/infrastructure/**
apps/backend/app/observability.py
apps/backend/app/metrics.py
apps/backend/tests/evals/**
apps/backend/tests/fixtures/**
apps/backend/tests/integration/**
apps/backend/tests/property/**              # 如需
apps/backend/tests/synthetic/**             # 如需
```

可新增最小 outcome/experiment persistence adapter，但不得创建新的“第九个 domain truth owner”。

## Forbidden Changes

- DecisionTrace 不得被 OutcomeObservation 回写；
- delayed outcome 不得自动 last-touch 给最后 TeachingAction；
- 未满足实验识别条件不得标 `EXPERIMENTALLY_CAUSAL`；
- assignment probability 不得写入 action propensity；
- OPVE 不得包装成 causal RL OPE；
- synthetic learner 不得作为 human learning efficacy evidence；
- engagement/turns/likes/hints/tokens/session duration 不得成为 primary learning outcomes；
- 不把当前阶段称为“已证明 adaptive teaching 更有效”；
- 不修改 Design/ADR/Spec。

## Implementation Tasks

### T1 — TeachingEpisode / LearningTrajectory Persistence

建立最小 episode/trajectory linkage，使后续 outcome 可关联多个 TeachingAction/Assessment/Review measurement，而不破坏既有 domain ownership。

要求：

- refs/version 可追溯；
- 不复制 learner/assessment truth 成第二事实源；
- episode/trajectory 是组织与归因边界，不是新的 mastery owner。

### T2 — OutcomeObservation Recording

至少支持记录：

```text
measurement_reference
independence / actual assistance
actual delay
transfer distance / novelty
score / success
measurement confidence
active learning time / time cost / hint cost
contamination status
attribution_scope
episode / trajectory refs
experiment association
```

### T3 — Decision / Outcome Separation

实现不可变审计关系：

```text
DecisionTrace = decision-time reasoning
OutcomeObservation = later measurement
```

Outcome 写入后不得修改历史 candidate features/scores/reason codes。

### T4 — Attribution Scope

只允许：

```text
ACTION_DIRECT
EPISODE_ASSOCIATED
TRAJECTORY_ASSOCIATED
EXPERIMENTALLY_CAUSAL
UNATTRIBUTABLE
```

默认 delayed learning outcome 不自动归因到最后 action。`EXPERIMENTALLY_CAUSAL` 必须有明确 ExperimentAssignment/analysis eligibility 证据。

### T5 — ExperimentAssignment Separation

实现/验证：

```text
assignment_id
assignment_version
assignment_unit
variant
assignment_probability
```

与 SYS05 deterministic action selection 完全分离：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

### T6 — Outcome Hierarchy

metrics/observability/test fixtures 必须明确：

Primary learning outcomes：

```text
no-hint independent success
delayed independent performance
independent transfer
unit-time capability gain
```

Process/experience diagnostics：

```text
engagement
conversation turns
likes
hint count
tokens
session duration
```

不得混用。

### T7 — OPVE Layer 1: Contract Verification

验证 schema、enum、probability、owner、immutability、missing semantics。

### T8 — OPVE Layer 2: Scenario Replay

用固定 context/policy fixtures replay 六类 StrategyFamily 与关键 error/support paths。

### T9 — OPVE Layer 3: Sequential Transition Replay

复用 EXEC-010 sequential fixtures，验证 material evidence、anti-oscillation、validation obligation。

### T10 — OPVE Layer 4: Property / Metamorphic Tests

至少验证：

- hard-filtered action 永不复活；
- irrelevant wording/order changes 不改变 semantic decision；
- support/exposure 只能按合法方向变化；
- same exact inputs deterministic。

### T11 — OPVE Layer 5: Baseline Differential Replay

对可定义的 fixed baseline/legacy baseline 只比较 policy behavior/correctness，不把行为差异当学习效果。

### T12 — OPVE Layer 6: Synthetic Learner Stress

允许 synthetic learner 做：

- edge-case coverage；
- oscillation stress；
- rare transition stress；
- throughput/replay engineering checks。

报告必须标注 `ENGINEERING/POLICY EVIDENCE ONLY`。

### T13 — G0 / G1 / G2 Gold Sets

实现：

```text
G0 Hard Constraint Gold
G1 Acceptable Action Set Gold
G2 Research / Calibration Set
```

G0 gate：100% pass，forbidden action = 0。  
G1 gate：`selected_action in acceptable_actions`，不得强制唯一 gold。  
G2 不作为发布 hard gate，除非上游 Spec 明确要求。

## Acceptance Criteria

- `EXEC012-AC-001`：OutcomeObservation 可追到真实 measurement、actual assistance、delay、episode/trajectory refs。
- `EXEC012-AC-002`：Outcome write 不修改历史 DecisionTrace content。
- `EXEC012-AC-003`：delayed outcome 默认不会 last-touch 给最后 action。
- `EXEC012-AC-004`：无实验识别条件时不能使用 `EXPERIMENTALLY_CAUSAL`。
- `EXEC012-AC-005`：assignment probability 与 action propensity 在 schema/tests/metrics 中完全分离。
- `EXEC012-AC-006`：四个 primary learning outcomes 与 process metrics 明确分层。
- `EXEC012-AC-007`：OPVE 六层均有 executable test/fixture entry。
- `EXEC012-AC-008`：G0 = 100%，forbidden action = 0。
- `EXEC012-AC-009`：G1 使用 acceptable-action-set 判定并通过当前 gold set。
- `EXEC012-AC-010`：synthetic learner 输出显式标注为非 human efficacy evidence。
- `EXEC012-AC-011`：Outcome/Experiment 不创建第九个 canonical truth owner。
- `EXEC012-AC-012`：无 blocking `SPEC GAP`。

## Required Tests

至少：

```text
outcome contract/persistence tests
DecisionTrace immutability after outcome
attribution negative/positive cases
experiment probability separation
G0/G1/G2 fixtures
six OPVE layer entry tests
property/metamorphic tests
baseline differential replay
synthetic stress test
```

最低命令：

```bash
cd apps/backend
uv run pytest tests/evals tests/integration
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Outcome model:
- persistence/refs/attribution

Experiment:
- assignment probability handling
- action propensity handling

Outcome hierarchy:
- primary metrics
- process metrics

OPVE:
- L1..L6 entry/result

Gold sets:
- G0 cases/pass rate/forbidden count
- G1 cases/pass rate
- G2 scope

Synthetic evidence label:
- ...

AC Matrix:
- EXEC012-AC-001 ... EXEC012-AC-012

Tests:
- command -> result

SPEC GAP:
- none / details
```

只有 `Status: DONE` 才允许 EXEC-013 执行最终 v0.3 E2E/release gate。