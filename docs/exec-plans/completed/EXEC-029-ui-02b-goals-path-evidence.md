# EXEC-029 — UI-02B Goals, Learning Path and Evidence

> Priority：P0 Product Completion
> Status：DONE / FROZEN
> Depends on：UI-02A DONE；UI-02B1 committed baseline
> Governing decision：ADR-0006

## Objective

实现冻结的 UI-02B 只读切片：真实 `/goals`、`/path`、`/evidence` workspace Queries/pages，并使 `/today` 诚实呈现唯一 canonical current plan，不引入任何 goal/plan/mastery/activity 写命令。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与相关 architecture/domain/system/interface/quality/UI Specs，尤其：

- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/lifecycle-state-machines.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/07-review-scheduler.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/ui/screen-contracts.md`
- `docs/specs/ui/data-contracts.md`
- `docs/specs/ui/visual-system.md`
- `docs/specs/ui/quality-and-migration.md`
- `docs/specs/vertical-slices/ui-02b-goals-path-evidence.md`

## Current Reality

- Goals/Path/Evidence routes render engineering unavailable pages.
- owner records for LearningGoal/LearningPlan/LearningActivity/MasteryEstimate exist.
- Today intentionally reports SYS06 `OWNER_QUERY_UNAVAILABLE`.
- no durable LearningObjective metadata stream or canonical activity/session link exists.
- worktree contains unrelated and prior-slice user changes; they must not be overwritten or committed.

## Allowed Files

```text
docs/adr/ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md
docs/adr/README.md
docs/document-inventory.md
docs/exec-plans/README.md
docs/specs/ui/data-contracts.md
docs/specs/README.md
docs/specs/vertical-slices/ui-02b-goals-path-evidence.md
docs/exec-plans/active/EXEC-029-ui-02b-goals-path-evidence.md
docs/exec-plans/completed/EXEC-029-ui-02b-goals-path-evidence.md
docs/releases/ui-02b-goals-path-evidence.md
apps/backend/app/contracts/workspace.py
apps/backend/app/queries/workspace.py
apps/backend/app/api/v1/workspace.py
apps/backend/tests/contracts/test_workspace_contract.py
apps/backend/tests/architecture/test_workspace_query_boundary.py
apps/backend/tests/integration/test_workspace_today_query.py
apps/backend/tests/integration/test_workspace_product_views.py
apps/frontend/src/App.jsx
apps/frontend/src/api/workspace.js
apps/frontend/src/pages/Today.jsx
apps/frontend/src/pages/Today.css
apps/frontend/src/pages/Goals.jsx
apps/frontend/src/pages/Goals.css
apps/frontend/src/pages/LearningPath.jsx
apps/frontend/src/pages/LearningPath.css
apps/frontend/src/pages/Evidence.jsx
apps/frontend/src/pages/Evidence.css
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/Today.test.jsx
apps/frontend/src/test/Goals.test.jsx
apps/frontend/src/test/LearningPath.test.jsx
apps/frontend/src/test/Evidence.test.jsx
```

## Forbidden Changes

- 不修改 owner write services、ORM schema、migration、event/command contracts；
- 不实现 goal edit、replanning、mastery edit、activity start/session link/completion；
- 不从 legacy profile/session 推断 canonical goal/plan/evidence；
- 不从 probability threshold 生成 mastered label；
- 不新增 production dependency；
- 不覆盖、重置、格式化或提交 Allowed Files 之外的现有修改。

## Implementation Tasks

1. 接受 ADR-0006、修订 UI Data Contract、冻结 Vertical Slice 与本 EXEC；独立 docs commit。
2. 增加 Goals/Path/Evidence strict v1 contracts。
3. 实现 canonical identity、latest version、goal-owned plan scope、plan activity order、SYS03 evidence 与 owner-safe SYS01 label join。
4. 增加三个 transport-only endpoints、private/no-store 与 explicit goal scope。
5. Today 复用相同 plan selection并保持 activity launch gate。
6. 实现三页产品 UI 与 loading/empty/ready/partial/error/unauthorized。
7. 增加 contract/architecture/SQLite/auth/frontend tests。
8. 运行 targeted/full gates；在 clean worktree 验证本 EXEC commits 独立成立。
9. 写 release evidence、归档 EXEC 并完成独立本地 implementation commit。

## Acceptance Criteria

- `EXEC029-AC-001`：`UI02B-VSLICE-AC-001..010` 全部满足。
- `EXEC029-AC-002`：三 endpoint strict 1.0、current-user、stable order、private/no-store。
- `EXEC029-AC-003`：多 current plan 不猜选，显式 goal scope 可稳定返回 owner plan。
- `EXEC029-AC-004`：objective missing 与 evidence uncertainty/product-label semantics 符合 ADR-0006。
- `EXEC029-AC-005`：Today 复用 owner query且不冒充 activity/session link。
- `EXEC029-AC-006`：API/query/frontend ownership architecture tests PASS。
- `EXEC029-AC-007`：页面状态、360px 与 keyboard/accessibility 自动化/人工验证通过。
- `EXEC029-AC-008`：targeted/full backend/frontend/lint/type/migration/build/audit/diff gates 有真实结果。
- `EXEC029-AC-009`：clean worktree 验证证明 commits 不依赖未提交 UI-02B2/B3/EXEC-028 改动。
- `EXEC029-AC-010`：无 blocking SPEC GAP；Learning Evidence 为 `LEARNING_EVIDENCE_INSUFFICIENT`。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts/test_workspace_contract.py tests/architecture/test_workspace_query_boundary.py tests/integration/test_workspace_today_query.py tests/integration/test_workspace_product_views.py
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

## Completion Report

必须分别报告 Engineering、Policy/Ownership、Learning Evidence，列出修改文件、测试、未完成项、SPEC GAP、独立 commit 与未提交用户改动保持情况。
