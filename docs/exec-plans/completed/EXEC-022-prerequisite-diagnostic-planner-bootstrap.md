# EXEC-022 — Prerequisite Diagnostic Bootstrap & LearningPlan Handoff

> Priority：P0 Book-to-Learning / SYS06-SYS04-SYS03  
> Status：DONE
> Depends on：EXEC-021 DONE  
> Primary Spec：SPEC-D05  
> Execution rule：完成并归档本 EXEC 后，EXEC-023 仍需等待 EXEC-020 DONE。

## Objective

把 Goal-specific subgraph 与真实 LearnerState 接入 prerequisite diagnosis，并回到现有 Planner：

```text
confirmed GoalKnowledgeMapping
+ GoalSpecificKnowledgeSubgraph
+ LearnerState
→ DiagnosticNeed
→ DIAGNOSTIC activity
→ SYS04 Assessment
→ SYS03 evidence projection
→ prerequisite feasibility re-evaluation
→ existing LearningPlanner / Replan
```

不得实现第二 grader、第二 mastery projector 或第二 planner。

## Dependencies

- EXEC-021 DONE；
- current SYS04 evaluator/assessment、SYS03 learner projector、SYS06 LearningPlanner 可复用；
- fixed deterministic assessment item route 可用于首个 E2E。

## Required Specs

Codex MUST 读取：

- `AGENTS.md`
- `docs/specs/README.md`
- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/06-goal-knowledge-mapping.md`
- `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Current Reality

- existing LearningPlanner 已能把 unknown prerequisite 转为 DIAGNOSTIC candidate；
- existing SYS04/SYS03 已具备 AssessmentResult → LearnerEvidence → MasteryEstimate owner chain；
- 缺少的是围绕 GoalSpecificKnowledgeSubgraph 的 versioned DiagnosticNeed、graph-adaptive stop/descend logic 与 application orchestration；
- 不能把当前 unknown 简化为 mastery=0。

## Allowed Files

```text
docs/exec-plans/**
docs/releases/**
docs/document-inventory.md
apps/backend/app/contracts/planning.py
apps/backend/app/contracts/assessment.py
apps/backend/app/contracts/learner.py
apps/backend/app/contracts/learning.py
apps/backend/app/domains/learning_planner/**
apps/backend/app/domains/assessment/**
apps/backend/app/domains/learner_model/**
apps/backend/app/queries/**
apps/backend/app/services/assessment/**
apps/backend/app/api/v1/**
apps/backend/app/infrastructure/**
apps/backend/tests/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/replay/**
apps/backend/tests/fixtures/**
```

## Forbidden Changes

- SYS06 不得实现 grader；
- SYS04 不得直接写 mastery/plan；
- SYS03 不得创建 AssessmentResult；
- unknown/missing/low-confidence 不得映射为 0 或 1；
- 不新增 complex IRT-CAT / RL；
- 不让 LLM 判断“应该会了”后设置 prerequisite satisfied；
- 不用固定题数/阈值宣称普适教学规律；
- 不重写 existing LearningPlanner。

## Implementation Tasks

1. 实现 SYS06-owned versioned `DiagnosticNeed`，绑定 goal mapping/subgraph/learner state/planner versions。
2. 区分 unknown/unmet/sufficient-current-evidence；只测会改变 feasibility 的 decision-relevant prerequisite。
3. 实现 deterministic graph-adaptive selection：高价值直接 prerequisite → assessment → state update → success stop/skip irrelevant ancestors；failure 向更基础 prerequisite 下钻。
4. 复用 SYS04 active deterministic AssessmentItem；缺 item 时按现有生成→draft→validation contract，禁止未验证 LLM Q/A。
5. Attempt/AssessmentResult 保持 actual assistance / confidence / failure semantics。
6. 通过 SYS03 existing evidence eligibility/projector 更新 LearnerState；系统/模型故障不得产生 learner failure evidence。
7. 实现 versioned diagnostic budget/stop reasons：resolved/ready/remediation/budget/item unavailable/low confidence/user stopped/system blocked。
8. budget exhausted 保留 unknown，并交给 existing uncertainty-aware Planner。
9. material LearnerState change 后调用 existing replan，验证 diagnostic/remediation/learn_new/transfer 等行为。
10. 实现 replay/idempotency：固定 need/item/state 输入重放，不在线调用 LLM；重复 response 不产生第二 result/evidence。
11. full gates + 归档 EXEC-022。

## Acceptance Criteria

- `EXEC022-AC-001`：`D05-AC-001..007` 全部满足。
- `EXEC022-AC-002`：Goal-specific hard prerequisite unknown 可形成真实 DIAGNOSTIC activity。
- `EXEC022-AC-003`：AssessmentResult 只经 SYS03 owner path 影响 LearnerState。
- `EXEC022-AC-004`：success 可减少无决策价值下钻；failure 可下钻到更基础 prerequisite/remediation。
- `EXEC022-AC-005`：budget exhausted / no valid item / system failure 都保留正确 unknown/failure boundary。
- `EXEC022-AC-006`：answer-exposed/assisted evidence 不伪装 independent mastery。
- `EXEC022-AC-007`：diagnostic material change 触发现有 LearningPlanner replan，不创建第二计划表。
- `EXEC022-AC-008`：无第二 Assessment/Mastery/Planner truth。

## Required Tests

```bash
cd apps/backend
uv run pytest tests -k "diagnostic or assessment or learner or planner or mastery"
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Diagnostic:
- DiagnosticNeed
- selection/stop/budget
- descend/stop behavior

Assessment / Learner:
- SYS04 result evidence
- SYS03 projection evidence

Planner:
- replan / activity result

AC Matrix:
- EXEC022-AC-001 ... EXEC022-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

Commit:
- <sha>
```
