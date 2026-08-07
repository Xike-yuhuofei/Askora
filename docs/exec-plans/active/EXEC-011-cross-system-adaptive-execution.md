# EXEC-011 — Cross-System Adaptive Execution Integration

> Priority：P0 Integration  
> Status：READY_AFTER_EXEC-010  
> Depends on：EXEC-010

## Objective

把 SYS05 已完成的 v0.3 TeachingAction 安全接入现有 canonical learning facade/orchestrator，使 SYS02/SYS08 只能收紧 action envelope，SYS04 记录 learner 实际经历的 assistance/exposure，SYS03 只依据 actual facts 接纳 LearnerEvidence，并彻底切断 legacy Socratic 对 final TeachingAction 的 ownership。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与：

- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`

## Current Reality

v0.2 已建立：

- `apps/backend/app/orchestration/learning_facade.py` canonical learning facade；
- ordinary/streaming 统一主教学入口的 v0.2 基线；
- retrieval、assessment、learner-model、orchestration 等 domain/service 基础；
- legacy `app/engines/**`、`services/dialog/**` 等仍可能承担 compatibility/execution adapter 责任。

本 EXEC 不重建第二个 orchestrator，而是在现有 canonical facade 上接入 v0.3 action/execution semantics。

## Allowed Files

优先：

```text
apps/backend/app/orchestration/**
apps/backend/app/domains/retrieval/**
apps/backend/app/domains/assessment/**
apps/backend/app/domains/learner_model/**
apps/backend/app/domains/teaching_policy/**
apps/backend/app/services/dialog/**
apps/backend/app/engines/**                    # 仅 bounded compatibility/execution adapter
apps/backend/app/contracts/**
apps/backend/app/infrastructure/**
apps/backend/tests/integration/**
apps/backend/tests/e2e/**
apps/backend/tests/security/**
apps/backend/tests/architecture/**
apps/backend/tests/fixtures/**
```

## Forbidden Changes

- SYS02/SYS08 不得扩大 SYS05 action envelope；
- SYS08/LLM 不得改变 StrategyFamily 或 final TeachingAction；
- planned assistance 不得替代 actual assistance；
- assistance unknown 不得默认 `INDEPENDENT`；
- ANSWER_EXPOSED success 不得成为 independent mastery evidence；
- legacy Socratic selector/state machine 不得拥有 final action；
- ordinary 与 streaming 不得重新分叉为两套 teaching policy；
- model output 不得直接更新 MasteryEstimate；
- 不修改 Design/ADR/Spec。

## Implementation Tasks

### T1 — Canonical Facade Uses SYS05 v0.3 Decision

现有 learning facade/orchestrator 必须：

```text
LearningActivity + exact refs
→ TeachingContext
→ SYS05 policy kernel
→ TeachingAction + DecisionTrace
→ SYS02/SYS08 execution
```

不得在 facade 内实现第二套 strategy selector。

### T2 — SYS02 Tightening-Only Evidence Construction

SYS02 根据 TeachingAction 的 evidence/exposure envelope 构建 EvidenceBundle：

- MAY 减少 learner-visible evidence；
- MAY 因安全/缺证据进一步收紧 exposure；
- MUST NOT 增加超过 TeachingAction 上限的 solution/answer evidence；
- missing evidence 必须显式返回，不让模型补造资料事实。

### T3 — SYS08 Tightening-Only Execution

模型/工具执行必须接受 immutable TeachingAction envelope：

- model 负责解释、提示、反馈表达；
- output validator 检查 Strategy/Move/Modifier/assistance envelope；
- fallback 只能保持或收紧，不得放宽；
- unauthorized tool / prompt injection 不能改变 policy ownership。

### T4 — Actual Assistance Event / Snapshot

根据实际 rendered interaction 记录：

```text
assistance_state
scaffold_control
hint_specificity
answer_exposure
```

actual value 必须反映 learner 真正看到/使用的内容，不是计划值的机械复制。

### T5 — SYS04 Assessment Integration

Attempt/AssessmentResult 关联：

- TeachingAction ref；
- actual assistance snapshot；
- ErrorType 7+UNKNOWN；
- assessment_confidence；
- diagnostic_confidence；
- independent validation obligation context（如适用）。

### T6 — SYS03 Evidence Eligibility

SYS03 基于 actual assistance 决定 evidence eligibility/weight：

- INDEPENDENT 与 ASSISTED 语义不同；
- ANSWER_EXPOSED success 不得当 independent mastery evidence；
- unknown assistance conservative；
- 不由 model/orchestrator 直接写 mastery truth。

### T7 — Legacy Socratic Ownership Cutover

定位所有 legacy Socratic selector/state graph：

允许保留为：

```text
SOCRATIC_PROBE InteractionMove provider
render/execution adapter
test fixture
compatibility reader
```

禁止：

```text
final StrategyFamily owner
final TeachingAction owner
envelope override
mastery writer
```

### T8 — Ordinary / Streaming Equivalence

普通和 streaming request 对同一 decision fixture 必须共享：

- same TeachingContext；
- same SYS05 decision；
- same semantic TeachingAction；
- same exposure envelope。

render transport 差异不能改变教学决策语义。

## Acceptance Criteria

- `EXEC011-AC-001`：canonical facade 只调用一个 SYS05 final-action owner。
- `EXEC011-AC-002`：SYS02 无扩大 learner-visible answer/exposure envelope 的成功路径。
- `EXEC011-AC-003`：SYS08/model/fallback 无扩大 TeachingAction envelope 的成功路径。
- `EXEC011-AC-004`：Attempt 记录 actual assistance 四轴且可追溯 execution。
- `EXEC011-AC-005`：planned vs actual assistance 不一致时，SYS04/SYS03 使用 actual facts。
- `EXEC011-AC-006`：ANSWER_EXPOSED success 不产生 independent mastery evidence。
- `EXEC011-AC-007`：ASSISTED 与 INDEPENDENT evidence semantics 可区分。
- `EXEC011-AC-008`：assistance unknown 时 conservative，不默认 independent。
- `EXEC011-AC-009`：legacy Socratic 无 final TeachingAction ownership。
- `EXEC011-AC-010`：ordinary/streaming 同输入得到同 semantic TeachingAction。
- `EXEC011-AC-011`：prompt injection/unauthorized tool 无法改变 policy ownership/envelope。
- `EXEC011-AC-012`：无 blocking `SPEC GAP`。

## Required Tests

至少覆盖：

```text
facade -> SYS05 -> retrieval -> model execution integration
envelope tightening property tests
planned vs actual assistance mismatch
independent/assisted/answer-exposed assessment path
unknown assistance conservative path
legacy Socratic ownership regression
ordinary vs streaming decision equivalence
prompt injection / tool override / answer leakage
```

最低命令：

```bash
cd apps/backend
uv run pytest tests/integration tests/e2e tests/security tests/architecture
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Canonical path:
- entry -> SYS05 -> SYS02/SYS08 -> SYS04 -> SYS03

Envelope checks:
- retrieval
- model execution
- fallback

Actual assistance:
- planned vs actual cases
- assessment/evidence result

Legacy Socratic:
- remaining paths
- allowed role
- final owner proof

Ordinary/streaming:
- equivalence test result

AC Matrix:
- EXEC011-AC-001 ... EXEC011-AC-012

Tests:
- command -> result

SPEC GAP:
- none / details
```

只有 `Status: DONE` 才允许 EXEC-012 建立 Outcome/Experiment/OPVE measurement foundation。