# EXEC-024 — Book-to-Learning E2E, Replay, Security & Release Gate

> Priority：P0 Release Gate  
> Status：READY  
> Depends on：EXEC-023 DONE  
> Primary Spec：SPEC-D06  
> Completion target：Book-to-Learning Engineering/Contract Gate PASS；Learning Evidence remains insufficient unless real human evidence exists.

## Objective

以一个**合法、最小、固定 EPUB fixture** 对 Book-to-Adaptive-Learning 全链做真实 release gate：

```text
upload
→ durable process
→ DocumentIR / DocumentNode
→ SourceSpan replay
→ SemanticUnit
→ knowledge candidate / verification / publication
→ retrieval projection
→ natural-language Goal
→ confirm
→ GoalKnowledgeMapping / subgraph
→ DiagnosticNeed
→ AssessmentResult
→ LearnerState
→ LearningPlan / Activity
→ existing TeachingContext / Policy / TeachingAction
→ EvidenceBundle / bounded model execution
→ Attempt / AssessmentResult
→ LearnerState update
→ second TeachingAction
```

本 EXEC 主要做 E2E 证明、修复切片内集成缺陷、release evidence 与归档，不得借 release gate 新增未冻结产品范围。

## Dependencies

- EXEC-017～023 全部 DONE；
- SPEC-D01～D06 FROZEN；
- v0.3 Engineering / Policy baselines 保持可用。

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
- `docs/specs/interfaces/content-ingestion-contract.md`
- `docs/specs/systems/01-content-granularity.md`
- `docs/specs/systems/01-knowledge-publish-pipeline.md`
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/06-goal-knowledge-mapping.md`
- `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md`
- `docs/specs/systems/07-review-scheduler.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/quality/observability-standard.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Allowed Files

```text
docs/exec-plans/**
docs/releases/**
docs/document-inventory.md
docs/specs/README.md          # 仅更新 implementation status，不改变 frozen semantics
apps/backend/tests/**
apps/frontend/src/test/**
apps/backend/app/**           # 仅修复 EXEC-017～023 已授权范围内的集成缺陷
apps/frontend/src/**          # 同上，仅修复已冻结 bootstrap/UI hook
.github/workflows/**          # 仅在现有 gate 无法覆盖已冻结 release evidence 时做最小 additive validation
```

任何需要新 domain semantics / new production dependency / 新产品范围的修复 MUST `BLOCKED_BY_SPEC_GAP`，不得使用本 EXEC 的宽 allowed range 越权。

## Forbidden Changes

- 不改变 SPEC-D01～D06 语义以迁就实现；
- 不新增新 StrategyFamily / Teaching Policy；
- 不引入 RL / complex CAT / GraphRAG default / Deep KT truth；
- 不把 synthetic fixture 结果称为真人学习效果；
- 不删除/弱化测试、扩大 ignore、跳过安全 gate；
- 不允许 E2E 通过 mock knowledge/mapping/mastery/TeachingAction shortcut；
- 不允许 replay 调在线 LLM 重构历史判断。

## Implementation Tasks

1. 建立/冻结合法最小 EPUB E2E fixture：包含结构、两个以上可教学 KU、至少一个可验证 prerequisite 或明确 relation fixture、可 deterministic assessment 的内容。
2. 建立 G0 Contract gate：D01～D05 ownership/schema/forbidden rules。
3. G1 Content gate：structure/replay/semantic-unit/publish/relation/cycle/projection。
4. G2 Goal/Diagnostic gate：natural-language goal、scope、mapping、subgraph、unknown prerequisite、budget、Assessment→SYS03。
5. G3 Planning gate：真实 owner inputs → existing LearningPlanner / Activity。
6. G4 Teaching integration gate：Activity → existing TeachingContext/Policy/Action → EvidenceBundle；无第二 tutor。
7. 完成一次真实 Attempt/Assessment/State update，证明新的 material evidence 触发 second TeachingAction。
8. G5 Recovery/Security gate：duplicate upload/process、restart/retry、quarantine、prompt injection、grader-only、auth/scope、model/system failure != learner failure。
9. Replay gate：fixed content/extraction/mapping/diagnostic/policy refs 重放 deterministic；历史 replay 不在线调用 LLM。
10. 运行 full repository CI-equivalent gates，并记录精确结果。
11. 创建 `docs/releases/book-to-adaptive-learning.md`，分别声明 Engineering/Contract、Policy regression、Learning Evidence 状态。
12. 更新 `docs/releases/README.md`、`docs/specs/README.md` implementation status、`docs/exec-plans` 索引、document inventory；将 EXEC-024 及前序已完成 active contracts 依规则归档。
13. 最终 Git diff/commit/CI evidence 校验。

## Acceptance Criteria

- `EXEC024-AC-001`：`D06-AC-001..012` 全部满足。
- `EXEC024-AC-002`：G0～G6 全部 PASS，且证据来自真实代码路径，不是 mock shortcut。
- `EXEC024-AC-003`：固定 EPUB 从 upload 闭合到 second canonical TeachingAction。
- `EXEC024-AC-004`：正式 plan 只引用 eligible published knowledge/relation + replayable source evidence。
- `EXEC024-AC-005`：natural-language Goal 无需 UUID 输入即可确认/映射/诊断/规划。
- `EXEC024-AC-006`：Assessment → SYS03 → Planner/Policy material evidence 链可审计。
- `EXEC024-AC-007`：recovery/idempotency/security/auth/exposure/grader-only gates PASS。
- `EXEC024-AC-008`：fixed historical replay 不在线调用 LLM。
- `EXEC024-AC-009`：v0.3 Teaching Policy/ownership regression PASS，无第二 truth/teaching path。
- `EXEC024-AC-010`：Learning Evidence 状态诚实保持 `LEARNING_EVIDENCE_INSUFFICIENT`，除非另有真实 human outcome evidence。

## Required Tests

```bash
cd apps/backend
uv run pytest tests --cov=app --cov-report=term-missing --cov-fail-under=45
uv run python test_document_service.py
uv run python test_optimizations.py
uv run ruff check app tests
uv run black --check app tests
uv run mypy app --no-error-summary
uv run alembic check
uv run pip-audit

cd ../frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

若 CI 的真实命令与上述本地命令已发生变化，必须以当前 `.github/workflows/ci.yml` 为准并在报告中说明，不得沿用过时命令伪造 PASS。

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

E2E:
- fixture
- upload → second TeachingAction evidence

Gate Matrix:
- G0 Contract
- G1 Content
- G2 Goal/Diagnostic
- G3 Planning
- G4 Teaching
- G5 Recovery/Security
- G6 Product Contract

Replay / Idempotency:
- evidence

Full Tests:
- command -> result

Release:
- Engineering/Contract Gate
- Policy Regression Gate
- Learning Evidence Gate

SPEC GAP:
- none / details

Commit:
- <sha>
```
