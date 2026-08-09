# EXEC-026 — UI-02B2 Guided Book Learning

> Status：ACTIVE / FROZEN
>
> Priority：P0 Product Continuity
>
> Decision authority：user-delegated Codex
>
> Frozen Slice：`docs/specs/vertical-slices/ui-02b2-guided-book-learning.md`

## Objective

实现从 Goal 确认到第一节可恢复 canonical 教学的系统带领流程，移除内部 pipeline 按钮，补齐
SYS06 primary diagnostic target 与 SYS08 durable transcript。

## Dependencies

- UI-02B1 / EXEC-025 DONE；
- Book-to-Learning EXEC-017～024 DONE；
- ADR-0004 accepted；
- 用户于 2026-08-08 委托 Codex 接受重大架构决定并修改产品代码。

## Required Specs

- `docs/adr/ADR-0004-guided-book-learning-and-durable-transcript.md`
- `docs/specs/vertical-slices/ui-02b2-guided-book-learning.md`
- `docs/specs/systems/06-goal-knowledge-mapping.md`
- `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/quality/definition-of-done.md`

## Current Reality

- B1 要求用户依次点击 mapping、diagnostic bootstrap、plan、activity selection；
- broad mapping 可能返回 2～3 个稳定 ranked targets，但 B1 fail closed；
- teaching response 已含 learner-visible EvidenceBundle，UI 未展示；
- teaching message 仅 React/sessionStorage，刷新丢失；
- 工作区已有用户 EPUB 安全、ledger migration 与 UI 小修，必须保留并避免覆盖。

## Allowed Files

```text
AGENTS.md
docs/adr/**
docs/specs/**
docs/exec-plans/**
docs/document-inventory.md
docs/releases/**
apps/backend/alembic/versions/*book_learning_transcript*.py
apps/backend/app/contracts/book_learning.py
apps/backend/app/contracts/planning.py
apps/backend/app/domains/learning_planner/goal_mapping.py
apps/backend/app/models/book_learning.py
apps/backend/app/models/__init__.py
apps/backend/app/infrastructure/book_learning_transcript.py
apps/backend/app/application/book_learning.py
apps/backend/app/api/v1/book_learning.py
apps/backend/tests/contracts/test_book_learning_contract.py
apps/backend/tests/integration/test_book_learning_orchestration.py
apps/backend/tests/integration/test_book_learning_transcript_migration.py
apps/backend/tests/e2e/test_book_to_adaptive_learning.py
apps/frontend/src/api/bookLearning.js
apps/frontend/src/pages/BookLearningLaunch.jsx
apps/frontend/src/pages/BookLearningLaunch.css
apps/frontend/src/test/BookLearningLaunch.test.jsx
```

## Forbidden Changes

- 不改变八系统 owner 或 TeachingAction/Assessment/Mastery/Plan 语义；
- 不复用 legacy dialog 为 Book Learning canonical transcript；
- 不自动确认 Goal、代答诊断或把 system_start 当 learner evidence；
- 不新增生产依赖、外部服务或遥测；
- 不修改、清理、格式化或提交范围外的现有用户改动；
- 不宣称 UI/engagement/synthetic tests 证明学习有效。

## Implementation Tasks

1. 为 SYS06 mapping 固定 ranked primary diagnostic target 与兼容验证。
2. 新增单步 safe auto-advance application/API，严格 allowlist/idempotency/current-user。
3. 新增 append-only transcript model/repository/migration/query。
4. teaching start 支持 learner/system_start，重复请求重放 exact accepted response。
5. 前端用 bounded auto-advance 替代内部按钮，重做三段式状态与单一主动作。
6. READY 页面以 system_start 进入第一课，刷新加载 transcript 和 learner-visible citations。
7. 补 contract/integration/migration/component/E2E 与安全测试。
8. 运行 backend/frontend/docs/diff gates，形成 release evidence 并归档 EXEC。

## Acceptance Criteria

- `EXEC026-AC-001`：UI02B2-AC-001～012 均有实现与当前验证证据。
- `EXEC026-AC-002`：没有第二 owner、第二 tutor 或 legacy dialog 双写。
- `EXEC026-AC-003`：重复/恢复不会重复模型、事件或 transcript。
- `EXEC026-AC-004`：现有用户工作区改动保持完整且未被混入治理结论。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts/test_book_learning_contract.py \
  tests/integration/test_book_learning_orchestration.py \
  tests/integration/test_book_learning_transcript_migration.py \
  tests/e2e/test_book_to_adaptive_learning.py
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd apps/frontend
npm test -- --run src/test/BookLearningLaunch.test.jsx
npm test -- --run
npm run build

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report Format

- Status；修改文件；migration/rollback；AC/test evidence；worktree preservation；
- SPEC GAP / residual risks；Engineering/UI/Policy/Learning Evidence 分层结论；
- 未经用户要求不 push。
