# EXEC-010 — Adaptive Transition + Anti-Oscillation

> Priority：P0 Core  
> Status：READY_AFTER_EXEC-009  
> Depends on：EXEC-009

## Objective

在已完成的 deterministic policy kernel 上，实现跨轮教学策略转换、支架升降、错误补救与 independent-validation obligation，使 Adaptive Teaching Loop 对 material evidence 响应，但不会因重复调用、措辞变化或微小时间变化发生策略抖动。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与：

- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/07-review-scheduler.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`

## Current Reality

EXEC-009 完成后应已有可 replay 的单次 B3 decision kernel，但尚不能假设跨轮 transition 已满足 v0.3 语义。本 EXEC 必须基于 exact previous decision / assistance / assessment / learner-state evidence 做 sequential decision，不得引入另一个 selector/state owner。

## Allowed Files

```text
apps/backend/app/domains/teaching_policy/**
apps/backend/app/contracts/**                 # 仅必要 contract implementation fix
apps/backend/app/domains/assessment/**        # 仅 integration contract/diagnosis support
apps/backend/app/domains/learner_model/**     # 仅 evidence/obligation consumption boundary
apps/backend/app/domains/review_scheduler/**  # 仅 meaningful delay/review signal boundary
apps/backend/tests/evals/**
apps/backend/tests/integration/**
apps/backend/tests/fixtures/**
apps/backend/tests/contracts/**
```

## Forbidden Changes

- 不以 chat turn count 直接驱动 strategy switch；
- 不以 wording change 或重复 policy invocation 作为 material evidence；
- 不以数秒 wall-clock 变化模拟 meaningful delay；
- 不让 LLM 判断“已经掌握”从而完成 validation obligation；
- 不让 scheduled validation 等于 completed validation；
- UNKNOWN diagnosis 不得被强制映射到某个具体 misconception；
- 不使用 universal hard-coded dwell/failure thresholds；参数必须 PolicyBundle/versioned；
- 不修改 Spec/ADR/Design。

## Implementation Tasks

### T1 — Material Evidence Gate

建立 typed material-evidence classification。至少支持：

```text
new AssessmentResult
fresh independent Attempt
diagnostic probe result
LearnerState/MasteryEstimate update
explicit user request
prerequisite evidence
actual answer exposure/assistance event
meaningful review/delay transition
```

以下默认不是 material evidence：

```text
same context re-evaluation
chat turn count alone
wording variation
re-render
few-second wall-clock drift
```

### T2 — Sticky Continuity

在无 material evidence 或差异不足时优先保持当前合法 strategy/action envelope。continuity 不能覆盖 hard constraint。

### T3 — Minimum Dwell by Evidence Opportunity

实现基于“有效 evidence opportunity”而不是纯轮次的 minimum dwell：

- 参数来自 PolicyBundle；
- 可被 hard rule/repeated-failure override；
- DecisionTrace 记录 dwell evidence/reason。

### T4 — Hysteresis

实现 versioned switch margin/hysteresis，防止接近阈值时来回切换；不得将 hysteresis 变成对 hard constraint 的豁免。

### T5 — Transition Priority

实现 deterministic transition priority，使同时出现多种转换信号时结果稳定、可解释。

### T6 — Repeated Failure Override

当 repeated failure 达到 versioned ceiling 时，应可合法：

- 打破 sticky continuity；
- 增加 support；
- 触发重新诊断；
- 进入 prerequisite remediation；
- 进入 ERROR_REMEDIATION candidate path。

具体动作仍由 SYS05 policy stack 决定，不由 assessment/LLM 直接写 TeachingAction。

### T7 — Independent Validation Obligation

`ASSISTED` 或 `ANSWER_EXPOSED` success 必须创建 `INDEPENDENT_VALIDATION_REQUIRED`。

只有 fresh independent Attempt + AssessmentResult 可以满足 obligation。以下都不能自动完成：

```text
validation scheduled
time elapsed
conversation continued
LLM confidence
assisted retry
answer-exposed retry
```

### T8 — Error Remediation / UNKNOWN

消费 SYS04 7+UNKNOWN ErrorType 与 diagnostic confidence：

- sufficiently supported diagnosis 可进入对应 remediation candidate；
- UNKNOWN/low-confidence 应选择 conservative probe/remediation path；
- `assessment_confidence != diagnostic_confidence`。

### T9 — Deterministic Time Injection

为 delayed/review transition 注入/freeze time source，测试不得真实等待小时/天。

## Acceptance Criteria

- `EXEC010-AC-001`：无 material evidence 的重复 evaluation 不发生 StrategyFamily oscillation。
- `EXEC010-AC-002`：chat turn/wording/re-render 不单独触发 major transition。
- `EXEC010-AC-003`：minimum dwell 基于 evidence opportunity，并由 PolicyBundle version 控制。
- `EXEC010-AC-004`：hysteresis 结果 deterministic，且不能覆盖 hard constraint。
- `EXEC010-AC-005`：多 transition signals 有稳定 priority/reason code。
- `EXEC010-AC-006`：repeated failure ceiling 能合法突破 continuity并产生 remediation/support escalation path。
- `EXEC010-AC-007`：ASSISTED success 创建 validation obligation，不能直接当 independent validation。
- `EXEC010-AC-008`：ANSWER_EXPOSED success 创建 validation obligation，不能直接当 independent validation。
- `EXEC010-AC-009`：只有 fresh independent Attempt/AssessmentResult 能满足 obligation。
- `EXEC010-AC-010`：UNKNOWN/low diagnostic confidence 不被猜测成具体 misconception。
- `EXEC010-AC-011`：sequential replay 使用固定 time 后结果稳定一致。
- `EXEC010-AC-012`：无 blocking `SPEC GAP`。

## Required Tests

必须包括 sequential replay/property tests：

```text
no-material-evidence repeat
threshold-near oscillation
minimum-dwell evidence opportunity
repeated failure override
assisted -> independent validation
answer-exposed -> independent validation
UNKNOWN diagnosis conservative path
fixed-time delayed retrieval/review transition
hard-constraint vs continuity/hysteresis precedence
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

Transition stack:
- material evidence gate
- sticky continuity
- dwell
- hysteresis
- priority
- failure override

Validation obligation:
- create condition
- satisfy condition
- negative cases

Diagnosis:
- UNKNOWN/low-confidence behavior

Sequential replay:
- fixture -> expected -> actual

AC Matrix:
- EXEC010-AC-001 ... EXEC010-AC-012

Tests:
- command -> result

SPEC GAP:
- none / details
```

只有 `Status: DONE` 才允许 EXEC-011 把 adaptive policy 接入 SYS02/SYS08/SYS04/SYS03 主链。