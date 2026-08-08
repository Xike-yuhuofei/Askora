# EXEC-023 — Book-to-Adaptive Orchestration, Readiness & Additive API

> Priority：P0 Book-to-Learning / Application Integration  
> Status：READY  
> Depends on：EXEC-020 DONE + EXEC-022 DONE  
> Primary Spec：SPEC-D06  
> Execution rule：完成并归档本 EXEC 后，方可进入 EXEC-024。

## Objective

把已经完成的内容、目标、诊断、计划能力接到现有 canonical teaching facade，形成产品/应用可操作的 bootstrap：

```text
BookLearningReadiness
→ Goal candidate / confirm
→ mapping / subgraph
→ diagnostic
→ plan / activity
→ existing canonical teaching entry
→ TeachingContext / Policy / TeachingAction
```

这是**编排与最小 additive API/read model**，不得创建 book-specific Tutor 或 all-in-one session truth。

## Dependencies

- EXEC-020 DONE：published knowledge 已安全进入 SYS02 projection；
- EXEC-022 DONE：goal/diagnostic/planner bootstrap 可用；
- existing v0.3 canonical teaching entry / SYS05 policy / SYS08 bounded execution 可用。

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
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/07-review-scheduler.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/systems/06-goal-knowledge-mapping.md`
- `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Current Reality

- UI-02A 已有 Library/KnowledgeMap read model；
- v0.3 已有 canonical teaching orchestration；
- goal/mapping/diagnostic/plan 能力在前序 EXEC 后存在，但尚缺统一 BookLearningReadiness/read/command façade 与 handoff；
- UI-02B 完整视觉产品仍 out of scope，本 EXEC 只实现最小可操作 API/query 与必要的 honest UI state hook（若已有页面需要）。

## Allowed Files

```text
docs/exec-plans/**
docs/releases/**
docs/document-inventory.md
apps/backend/app/contracts/**
apps/backend/app/queries/**
apps/backend/app/api/v1/**
apps/backend/app/application/**
apps/backend/app/services/dialog/**
apps/backend/app/services/**
apps/backend/app/engines/**
apps/backend/app/infrastructure/**
apps/backend/app/main.py
apps/backend/tests/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/recovery/**
apps/backend/tests/replay/**
apps/frontend/src/api/**
apps/frontend/src/pages/**
apps/frontend/src/components/**
apps/frontend/src/test/**
```

修改 legacy dialog/engines 仅允许作为 canonical facade adapter/ownership convergence；不得把 legacy 路径升级为 Book Tutor owner。

## Forbidden Changes

- 不创建 `book_tutor` / `epub_tutor` free-LLM 默认教学链；
- 不重做 SYS05 Teaching Policy、TeachingStage、anti-oscillation；
- 不复制 LearnerState/Plan/Assessment/TeachingAction 到 all-in-one bootstrap session truth；
- API adapter 不承载 mapping/diagnostic/plan 算法；
- 不实现 UI-02B 完整 Goals/Path/Evidence 视觉范围；
- 不让 CONTENT_PARTIAL/blocked 状态通过“先聊天”绕过；
- 不改变 current-user auth/source-scope/grader-only/quarantine boundary。

## Implementation Tasks

1. 实现 derived `BookLearningReadiness` read model，至少支持 PROCESSING / CONTENT_PARTIAL / READY_FOR_GOAL / GOAL_CONFIRMATION_REQUIRED / DIAGNOSIS_REQUIRED / DIAGNOSING / PLAN_READY / READY_TO_LEARN / BLOCKED，并附 exact owner refs/reasons。
2. 建立 application facade/commands 的组合入口：CreateGoalCandidate、ConfirmGoal、MapGoal、BuildSubgraph、Generate/ContinueDiagnosis、GeneratePlan、SelectNextActivity。
3. 提供最小 additive `/api/v1` command/query endpoints；保持 auth、idempotency、schema/error contract。
4. `LearningActivity` ready 后必须调用现有 canonical teaching entry，禁止新 teaching selector。
5. existing SYS05 创建 TeachingContext/TeachingAction；SYS02/SYS08 继续 tightening-only。
6. 将 bootstrap correlation/causation 贯穿 content → goal → diagnostic → plan → teaching，但 trace 只保存 refs，不复制 truth。
7. 处理 partial/stale/blocked states；错误停在正确 owner，不让 LLM 兜底伪造已就绪。
8. 若前端已有 Library/Learning Shell 需要最小入口，只增加 honest status/action，不扩展完整 UI-02B。
9. architecture tests 证明没有第二 TeachingAction / LearnerState / Plan / Assessment truth 与 second default teaching path。
10. integration 测试至少走到 first canonical TeachingAction/EvidenceBundle。
11. full backend/frontend gates（若修改前端）并归档 EXEC-023。

## Acceptance Criteria

- `EXEC023-AC-001`：BookLearningReadiness 全部状态由 exact owner refs 派生，UI/API 不能手工推进。
- `EXEC023-AC-002`：Goal/mapping/diagnostic/plan commands 通过 owner facade，不在 API 内实现算法。
- `EXEC023-AC-003`：ready LearningActivity 进入现有 v0.3 canonical TeachingContext/Policy/TeachingAction。
- `EXEC023-AC-004`：不存在 book-specific free-LLM TeachingAction owner 或第二 default tutor path。
- `EXEC023-AC-005`：blocked/partial/stale content 不会绕过为 READY_TO_LEARN。
- `EXEC023-AC-006`：current-user/source-scope/quarantine/grader-only 安全语义保持。
- `EXEC023-AC-007`：一次 bootstrap correlation 可追踪 owner refs 而不形成 all-in-one second truth。
- `EXEC023-AC-008`：first canonical TeachingAction 可使用 EXEC-020 的真实 EvidenceBundle。

## Required Tests

```bash
cd apps/backend
uv run pytest tests -k "workspace or goal or diagnostic or planner or orchestrator or teaching or retrieval"
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd ../frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

若未修改前端，可在 completion report 中明确标注 frontend tests 仍作为 regression gate 执行，不得擅自删除。

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Readiness / API:
- readiness states
- commands / queries
- auth/idempotency/errors

Canonical Handoff:
- LearningActivity
- TeachingContext
- TeachingAction
- EvidenceBundle

Architecture:
- no second truth / no second tutor path

AC Matrix:
- EXEC023-AC-001 ... EXEC023-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

Commit:
- <sha>
```
