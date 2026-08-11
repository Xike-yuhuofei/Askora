# EXEC-021 — LearningGoal Formation & Goal-to-Knowledge Mapping

> Priority：P0 Book-to-Learning / SYS06 Bootstrap  
> Status：DONE
> Depends on：EXEC-019 DONE  
> Primary Spec：SPEC-D04  
> Execution rule：可与 EXEC-020 在 EXEC-019 DONE 后独立实现；EXEC-022 需要本 EXEC DONE。

## Objective

实现从用户自然语言学习目标到可审计 target KnowledgeUnit 的 SYS06 主路径：

```text
natural-language intent
→ LearningGoal candidate
→ measurable capability/success criteria
→ user confirmation
→ GoalKnowledgeMapping
→ GoalSpecificKnowledgeSubgraph
→ existing LearningPlanner-compatible target ids
```

用户不再需要预先提供 KU UUID；LLM 也不得直接生成最终课程计划。

## Dependencies

- EXEC-019 DONE，存在 published/verified/eligible KnowledgeUnit 与 relation；
- existing `LearningPlanner` 保持不重写；
- current runtime `ConfirmedLearningGoal` 是最小输入合同，允许 additive adapter/contract 扩展，但不得改变 owner。

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
- `docs/specs/systems/01-knowledge-publish-pipeline.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/06-goal-knowledge-mapping.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Current Reality

- Domain Spec 已有完整 LearningGoal/LearningObjective 语义；
- runtime `ConfirmedLearningGoal` 主要要求 `goal_id/objective_id/target_knowledge_unit_ids/confirmed_at`；
- Planner 可消费 target ids，但当前缺少自然语言 goal → target KU 的 canonical mapping 主路径；
- UI-02A 没有实现 Goals/Path，这是预期基线，不得用前端假数据绕过。

## Allowed Files

```text
docs/planning/**
docs/archive/releases/**
docs/governance/document-inventory.md
apps/backend/app/contracts/planning.py
apps/backend/app/contracts/learning.py
apps/backend/app/contracts/**
apps/backend/app/domains/learning_planner/**
apps/backend/app/queries/**
apps/backend/app/api/v1/**
apps/backend/app/services/**
apps/backend/app/models/**
apps/backend/app/infrastructure/**
apps/backend/tests/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/replay/**
```

跨目录修改只允许为 SYS06 goal/mapping persistence/application adapters 与现有 model gateway；不得借此修改其他系统业务语义。

## Forbidden Changes

- 不修改 SYS01 KnowledgeUnit/Relation truth；
- 不让 LLM 确认用户 Goal；
- 不让 LLM 直接生成/persist LearningPlan；
- 不扩大 source_document scope；
- 不将 candidate-only KU 静默纳入 executable mapping；
- 不让 LearnerState 改写用户目标语义；
- 不建立第二 knowledge graph；GoalSpecificKnowledgeSubgraph 只能引用 SYS01 relation revisions；
- 不重写 LearningPlanner 算法。

## Implementation Tasks

1. 实现 versioned LearningGoal candidate/confirm persistence/application path，与 DOMAIN-010/011 一致。
2. 将自然语言目标结构化为 title/topic/target capabilities/application context/measurable success criteria/source scope/time constraints。
3. 模型参与只产生 persisted bounded inference/candidate；提供 deterministic fallback / low-confidence clarification。
4. 实现 `GoalKnowledgeMapping` versioned record：candidate/selected/excluded targets、exact knowledge refs、evidence/reason、mapper version。
5. MVP mapper 实现 hard scope filter → lexical/concept recall → optional semantic recall → hierarchy/capability fit → deterministic rank fusion → coverage/redundancy repair → ambiguity gate。
6. candidate-only/review_required KU 只能形成 `CONTENT_MODEL_INCOMPLETE` 等 reason，不得进入 executable selected set。
7. 实现 blocking ambiguity → candidate/blocked + bounded clarification；不得猜最终 target set。
8. 实现 `GoalSpecificKnowledgeSubgraph`，只包含 confirmed target + required published prerequisite closure，引用 exact relation revisions。
9. 提供现有 LearningPlanner 可消费的 adapter/ConfirmedLearningGoal，不改 planner ownership/核心算法。
10. 增加 auth/scope/version/replay/model-unavailable/no-second-graph tests。
11. full gates + 归档 EXEC-021。

## Acceptance Criteria

- `EXEC021-AC-001`：`D04-AC-001..007` 全部满足。
- `EXEC021-AC-002`：用户自然语言 goal 可形成 candidate 并经明确确认成为 confirmed goal。
- `EXEC021-AC-003`：selected target KU 全部有 exact version + mapping reason/evidence。
- `EXEC021-AC-004`：source scope 不被 mapper/LLM 扩大，candidate-only KU 不进入 executable mapping。
- `EXEC021-AC-005`：blocking ambiguity 会明确阻塞/澄清，不静默猜测。
- `EXEC021-AC-006`：GoalSpecificKnowledgeSubgraph 只引用 SYS01 published relation，无第二 graph truth。
- `EXEC021-AC-007`：fixed goal/knowledge/mapper/inference 可 deterministic replay，不在线重跑历史 LLM。
- `EXEC021-AC-008`：existing LearningPlanner 不重写即可消费 selected target ids。

## Required Tests

```bash
cd apps/backend
uv run pytest tests -k "goal or planner or mapping or knowledge"
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

Goal:
- candidate / confirmation
- measurable success criteria

Mapping:
- mapper version
- target selection
- ambiguity/scope behavior
- goal subgraph refs

Planner Compatibility:
- adapter / unchanged planner evidence

AC Matrix:
- EXEC021-AC-001 ... EXEC021-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

Commit:
- <sha>
```
