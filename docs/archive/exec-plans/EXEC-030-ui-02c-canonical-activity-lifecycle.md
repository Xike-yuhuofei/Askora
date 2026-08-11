# EXEC-030 — UI-02C Canonical Activity Lifecycle

> Priority：P0 Product Completion
> Status：DONE
> Depends on：UI-02B DONE；durable activity transcript / policy-bound Book Learning baseline committed
> Governing decision：ADR-0007

## Objective

实现 SYS06-owned activity lifecycle，使 Today/Path 能开始、恢复和完成 exact LearningActivity，并原子推进下一项；不得用 transcript/UI/模型结果充当 completion truth。

## Required Specs

- `AGENTS.md`
- `docs/architecture/decisions/ADR-0007-sys06-activity-lifecycle-and-completion.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/lifecycle-state-machines.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/06-activity-lifecycle.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/frontend/ui-read-model-contracts.md`
- `docs/archive/specs/ui/screen-contracts.md`
- `docs/archive/specs/ui/visual-system.md`
- `docs/archive/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md`

## Dependency Gate

执行前必须确认 durable activity transcript / policy-bound Book Learning 的代码、migration 与 tests 已形成独立可引用 commit。当前工作区存在相关未提交改动，因此本 EXEC 仅冻结，不授权在依赖未落地时修改产品代码。

Gate accepted：`0f4ebb6`（decision trace persistence prerequisite）与 `6172928`
（durable transcript / policy-bound Book Learning baseline）已作为可引用 commits 落地；
EXEC-030 自此进入实现阶段。为完成 cutover，Allowed Files 显式增加 plan 创建 adapter
与现有 Book Learning selection/read adapters，旧 `ActivitySelected` event reader 必须退休，
不得与 lifecycle 形成双 truth。

## Allowed Files

```text
docs/architecture/decisions/ADR-0007-sys06-activity-lifecycle-and-completion.md
docs/architecture/README.md
docs/governance/document-inventory.md
docs/specs/README.md
docs/specs/domain/lifecycle-state-machines.md
docs/specs/systems/06-activity-lifecycle.md
docs/specs/frontend/ui-read-model-contracts.md
docs/archive/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md
docs/planning/README.md
docs/archive/exec-plans/README.md
docs/planning/execs/EXEC-030-ui-02c-canonical-activity-lifecycle.md
docs/archive/exec-plans/EXEC-030-ui-02c-canonical-activity-lifecycle.md
docs/archive/releases/ui-02c-canonical-activity-lifecycle.md
docs/archive/releases/README.md
apps/backend/alembic/versions/<exec030_activity_lifecycle>.py
apps/backend/app/contracts/activity_lifecycle.py
apps/backend/app/models/planning.py
apps/backend/app/models/__init__.py
apps/backend/app/infrastructure/activity_lifecycle.py
apps/backend/app/infrastructure/planning_records.py
apps/backend/app/services/activity_lifecycle.py
apps/backend/app/application/book_learning.py
apps/backend/app/api/v1/workspace.py
apps/backend/app/contracts/workspace.py
apps/backend/app/queries/workspace.py
apps/backend/app/queries/book_learning.py
apps/backend/tests/architecture/test_activity_lifecycle_boundary.py
apps/backend/tests/contracts/test_activity_lifecycle_contract.py
apps/backend/tests/integration/test_activity_lifecycle.py
apps/backend/tests/integration/test_activity_lifecycle_migration.py
apps/backend/tests/integration/test_book_learning_orchestration.py
apps/backend/tests/integration/test_workspace_product_views.py
apps/backend/tests/e2e/test_book_to_adaptive_learning.py
apps/backend/tests/recovery/test_activity_lifecycle_recovery.py
apps/frontend/src/App.jsx
apps/frontend/src/api/workspace.js
apps/frontend/src/pages/Today.jsx
apps/frontend/src/pages/LearningPath.jsx
apps/frontend/src/pages/ActivityLearning.jsx
apps/frontend/src/pages/ActivityLearning.css
apps/frontend/src/pages/BookLearningLaunch.jsx
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/Today.test.jsx
apps/frontend/src/test/LearningPath.test.jsx
apps/frontend/src/test/ActivityLearning.test.jsx
apps/frontend/src/test/BookLearningLaunch.test.jsx
```

## Forbidden Changes

- 不修改 SYS03 mastery、SYS04 score、SYS05 action/obligation 或 SYS07 schedule；
- 不把 completed 自动解释为 objective satisfied、goal achieved 或 learning effectiveness；
- 不由 transcript/UI/event recency独立推断 current state；
- 不允许 unsupported activity type 由客户端自报完成；
- 不形成永久 payload-status + lifecycle 双写；
- 不覆盖或提交 Allowed Files 之外的用户改动。

## Implementation Tasks

1. 先收口并引用 dependency commit；重新核对 clean baseline。
2. 新增 strict lifecycle contracts、migration、backfill 与 reconciliation。
3. 实现 SYS06 repository/service、atomic event/outbox、idempotency 与 version conflict。
4. 接入 select→available、start→active、complete→completed→next available。
5. 增加 owner-scoped activity query 与 transport-only endpoints。
6. 实现 `/learn/:activityId`、Today/Path CTA、恢复/完成/冲突 UI。
7. 覆盖 contract/architecture/SQLite/PostgreSQL/recovery/frontend/browser tests。
8. 运行 full gates、写 release evidence、归档并独立提交。

## Acceptance Criteria

- `EXEC030-AC-001`：依赖 commit 已明确，clean baseline 可复现。
- `EXEC030-AC-002`：`SYS06-ACT-AC-001..007` 与 `UI02C-AC-001..009` 全部满足。
- `EXEC030-AC-003`：state/event/outbox 原子；duplicate/concurrent start/complete 不重复推进。
- `EXEC030-AC-004`：migration/backfill 不从模糊 transcript/model result 推断 completed。
- `EXEC030-AC-005`：cross-owner architecture tests 证明只有 SYS06 写 lifecycle。
- `EXEC030-AC-006`：真实浏览器完成 start→resume→complete→next；刷新与重启一致。
- `EXEC030-AC-007`：无 blocking SPEC GAP；Learning Evidence 为 `LEARNING_EVIDENCE_INSUFFICIENT`。

## Required Tests

```bash
cd apps/backend
pytest tests/contracts/test_activity_lifecycle_contract.py tests/architecture/test_activity_lifecycle_boundary.py tests/integration/test_activity_lifecycle.py tests/integration/test_activity_lifecycle_migration.py tests/recovery/test_activity_lifecycle_recovery.py
pytest
ruff check app tests
mypy app
alembic check

cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report

实现提交以前的候选证据见 `docs/archive/releases/ui-02c-canonical-activity-lifecycle.md`。
Engineering、Policy/Ownership 均为 PASS；Learning Evidence 保持
`LEARNING_EVIDENCE_INSUFFICIENT`。Blocking SPEC GAP：none。
