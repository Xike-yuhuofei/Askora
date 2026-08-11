# EXEC-025 — UI-02B1 Material-to-Learning Launch

> Status：DONE
>
> Priority：P0 Product Usability
>
> Frozen Slice：`docs/archive/specs/vertical-slices/ui-02b1-material-learning-launch.md`

## Objective

实现 `/library → /book-learning/:documentId → first/current canonical teaching rounds` 的真实最小 UI 路径，并补齐 learner-visible diagnostic item 的安全只读 payload。

## Dependencies

- UI-02A / EXEC-016 DONE；
- Book-to-Learning EXEC-017～024 DONE；
- v0.3 Adaptive Teaching Loop DONE；
- 用户已于 2026-08-08 授权冻结并执行 UI-02B1。

## Required Specs

- `docs/archive/specs/vertical-slices/ui-02b1-material-learning-launch.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/06-goal-knowledge-mapping.md`
- `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/definition-of-done.md`

## Current Reality / Baseline

- Backend 已有 readiness、Goal、mapping、diagnostic、plan、activity selection、teaching endpoints；
- active diagnostic 只公开 `assessment_item_ref`，没有 learner-visible prompt/options；
- frontend `/goals`、`/path`、`/evidence` 仍为 honest unavailable；`/learn/:activityId` 仍无 durable link；
- Library 已有 current-user document/map/query；没有资料学习入口；
- 修改前：frontend 10 files / 39 tests PASS，production build PASS；backend Book Learning targeted 6 PASS；
- 工作区已有 EPUB 安全修复未提交，其中 `Library.jsx`/`Library.test.jsx` 各有独立一行修改，必须保留且不得混入本 EXEC commit。

## Allowed Files

```text
docs/specs/README.md
docs/specs/ui/README.md
docs/specs/frontend/ui-read-model-contracts.md
docs/archive/specs/ui/quality-and-migration.md
docs/archive/specs/vertical-slices/ui-02b1-material-learning-launch.md
docs/planning/README.md
docs/planning/execs/EXEC-025-ui-02b1-material-learning-launch.md
docs/archive/exec-plans/EXEC-025-ui-02b1-material-learning-launch.md
docs/archive/exec-plans/README.md
docs/archive/releases/ui-02b1-material-learning-launch.md
docs/archive/releases/README.md
docs/governance/document-inventory.md
apps/backend/app/contracts/book_learning.py
apps/backend/app/queries/diagnostic_assessment.py
apps/backend/app/queries/book_learning.py
apps/backend/app/application/book_learning.py
apps/backend/app/api/v1/book_learning.py
apps/backend/app/services/auth/canonical_identity.py
apps/backend/app/services/learning_goals.py
apps/backend/app/services/assessment/diagnostic_bootstrap.py
apps/backend/tests/contracts/test_book_learning_contract.py
apps/backend/tests/integration/test_book_learning_orchestration.py
apps/backend/tests/unit/test_canonical_identity.py
apps/frontend/src/App.jsx
apps/frontend/src/api/bookLearning.js
apps/frontend/src/pages/Library.jsx
apps/frontend/src/pages/BookLearningLaunch.jsx
apps/frontend/src/pages/BookLearningLaunch.css
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/Library.test.jsx
apps/frontend/src/test/BookLearningLaunch.test.jsx
```

## Forbidden Changes

- 不修改 DB schema/migration、owner、Teaching Policy、planner/assessment/mastery 算法；
- 不实现完整 `/goals`、`/path`、`/evidence` 或 Focus；
- 不让前端自动选择多 target mapping；
- 不返回 answer/rubric/explanation/grader-only 字段；
- 不把 sessionStorage 当 activity/session truth 或宣称 durable resume；
- 不新增生产依赖、第二 message renderer、第二 tutor path；
- 不覆盖、格式化、暂存或提交现有 EPUB 安全修复。

## Implementation Tasks

1. 新增 learner-visible diagnostic projection contract/query/application payload，并验证 current-user need/item exact binding 与 grader-only isolation。
2. 新增 frontend Book Learning API adapter，严格校验 v1 readiness major/state。
3. 新增 `/book-learning/:documentId` protected route 和 Library 入口。
4. 实现 readiness-driven Goal/confirm/map/diagnostic/plan/select flow；每步真实 command 后刷新。
5. 多 target、unknown state、missing ref、blocked/partial/auth/version conflict fail closed。
6. 实现当前页面内 canonical teaching rounds，复用 RichMessage，明确非 durable history。
7. 补 route/component/API/error/accessibility/security tests。
8. 运行 frontend、backend targeted/full applicable、lint/type/audit/docs/diff gates。
9. 形成 release evidence，归档 EXEC-025，并创建独立本地 commit；不 push。

## Acceptance Criteria

- `EXEC025-AC-001`：`UI02B1-AC-001～012` 全部有实现与验证证据。
- `EXEC025-AC-002`：learner-visible diagnostic payload 只含冻结字段，grader-only zero leakage。
- `EXEC025-AC-003`：刷新/重试通过 readiness + stable idempotency 恢复，无 frontend canonical truth。
- `EXEC025-AC-004`：真实组件路径闭合到 canonical teaching response，不用 legacy quick session 冒充。
- `EXEC025-AC-005`：现有 Goals/Path/Evidence deferred 边界不变。
- `EXEC025-AC-006`：现有用户修改保持未覆盖、未混入 commit。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts/test_book_learning_contract.py \
  tests/integration/test_book_learning_orchestration.py \
  tests/e2e/test_book_to_adaptive_learning.py
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report Format

- Status / commit hash / push status；
- 修改文件；
- AC 与 test evidence；
- worktree preservation；
- SPEC GAP / residual risks；
- Engineering/UI Contract/Accessibility 与 Learning Evidence 分层结论。
