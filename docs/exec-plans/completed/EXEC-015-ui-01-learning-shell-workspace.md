# EXEC-015 — UI-01 Learning Shell and Compatibility Tutor Workspace

> Priority：P1 Product Experience
> Status：READY
> Depends on：EXEC-014
> Archive metadata：final status DONE；completion evidence 见 `docs/releases/ui-01-learning-shell-workspace.md`。READY 保留为历史入口条件。

## Objective

实现冻结的 UI-01 Vertical Slice：修复登录白屏，交付 learning-loop-first App Shell、Today Query/页面、明确标记的兼容导师工作台、历史与设置，同时保留 canonical dialog/RichMessage、安全与状态 ownership。

## Dependencies

- EXEC-014 DONE；
- UI Redesign Spec Set FROZEN；
- `ui-01-learning-shell-workspace.md` FROZEN；
- baseline 已记录：frontend 11 tests/build/audit PASS；backend 249 passed / 1 skipped。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与：

- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/lifecycle-state-machines.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/07-review-scheduler.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/render-content-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/ui/README.md`
- `docs/specs/ui/information-architecture.md`
- `docs/specs/ui/screen-contracts.md`
- `docs/specs/ui/data-contracts.md`
- `docs/specs/ui/visual-system.md`
- `docs/specs/ui/quality-and-migration.md`
- `docs/specs/vertical-slices/ui-01-learning-shell-workspace.md`

## Current Reality

- `/` 是 hard-coded subject picker/chat-first 首页；global CSS 使用渐变、玻璃态和卡片海洋。
- Sidebar 只有四项 legacy navigation。
- Chat 已复用 canonical dialog facade 与 RichMessage，但没有 activity/session link。
- Goal/Plan 持久层没有当前用户可安全查询的公开 owner query；不得猜测 ownership。
- ReviewSchedule 和 dialog session 可按 user 只读查询。
- 登录页因 `User` icon 未导入而运行时白屏。

## Allowed Files

```text
docs/specs/README.md
docs/specs/ui/**
docs/specs/vertical-slices/ui-01-learning-shell-workspace.md
docs/exec-plans/**
docs/document-inventory.md
docs/releases/**
apps/backend/app/contracts/__init__.py
apps/backend/app/contracts/workspace.py
apps/backend/app/queries/__init__.py
apps/backend/app/queries/workspace.py
apps/backend/app/api/v1/__init__.py
apps/backend/app/api/v1/workspace.py
apps/backend/app/main.py
apps/backend/tests/contracts/test_workspace_contract.py
apps/backend/tests/architecture/test_workspace_query_boundary.py
apps/backend/tests/integration/test_workspace_today_query.py
apps/frontend/README.md
apps/frontend/src/App.jsx
apps/frontend/src/router.jsx
apps/frontend/src/styles/global.css
apps/frontend/src/api/workspace.js
apps/frontend/src/components/AppShell.*
apps/frontend/src/components/Sidebar.*
apps/frontend/src/components/SourceStatus.*
apps/frontend/src/pages/Login.*
apps/frontend/src/pages/Today.*
apps/frontend/src/pages/TutorWorkspace.*
apps/frontend/src/pages/History.*
apps/frontend/src/pages/Settings.*
apps/frontend/src/pages/Unavailable.*
apps/frontend/src/test/**
```

## Forbidden Changes

- 不实现 UI-02/UI-03；
- 不新增 Goal/Plan/Activity/Review/Mastery 写命令或 DB migration；
- 不把 dialog session id 当 activity id；
- 不读取无 current-user ownership 的 plan/activity records；
- 不从 legacy mastery/hint/strategy 推断 canonical evidence/assistance；
- 不改变 canonical dialog facade、RichMessage schema 或 TeachingAction envelope；
- 不新增 production dependency、raw HTML/MDX/remote image；
- 不覆盖或提交本 EXEC 之外的用户修改。

## Implementation Tasks

1. 冻结 UI Spec Set、Vertical Slice 与本 EXEC，修正文档索引/清单。
2. 定义 strict immutable Today Workspace v1.0 response contracts。
3. 实现 current-user-scoped `WorkspaceTodayQueryService` 与 `/workspace/today` transport。
4. 增加 contract、architecture、SQLite integration/auth/source/ordering/timezone tests。
5. 修复 Login icon/runtime，增加 render/validation test。
6. 实现 tokens、AppShell、七项 navigation、legacy redirects、responsive drawer/focus。
7. 实现 Today、Unavailable canonical activity route 与 compatibility quick start。
8. 实现 `/quick/:sessionId` 导师工作台，复用 dialog detail/messages/send 与 RichMessage。
9. 实现 History、Settings 与 360px/keyboard/loading/error/empty tests。
10. 运行全部门禁；更新 release evidence、归档 EXEC；独立本地 commit。

## Acceptance Criteria

- `EXEC015-AC-001`：`UI01-VSLICE-AC-001..012` 全部满足。
- `EXEC015-AC-002`：Today response strict schema 1.0、timezone-aware、current-user scoped、private/no-store。
- `EXEC015-AC-003`：SYS06 unavailable、SYS07 due 与 legacy sessions 有明确 source/availability/reason，不形成第二 truth。
- `EXEC015-AC-004`：login render/validation/phone auth 和 dev-auto-login regression tests 通过。
- `EXEC015-AC-005`：七项导航、legacy redirect、unknown route recovery 无业务副作用。
- `EXEC015-AC-006`：兼容工作台 normal/history/RichMessage 可真实运行，session ownership 由后端继续强制。
- `EXEC015-AC-007`：canonical activity 无 link 时不可启动，不调用 create session。
- `EXEC015-AC-008`：loading/empty/partial/error/unauthorized、keyboard/focus、360px/desktop 自动/人工验证通过。
- `EXEC015-AC-009`：frontend/backend/docs gates 全部有真实结果。
- `EXEC015-AC-010`：无 blocking SPEC GAP、无新依赖/迁移/ownership regression，Learning Evidence 仍为 insufficient。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts/test_workspace_contract.py tests/architecture/test_workspace_query_boundary.py tests/integration/test_workspace_today_query.py
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

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Spec / Query:
- frozen paths
- schema/source/auth behavior

UI:
- shell/routes/today/workspace/history/settings
- responsive/accessibility evidence

AC Matrix:
- EXEC015-AC-001 ... EXEC015-AC-010

Tests:
- command -> result

Learning Evidence Gate:
- LEARNING_EVIDENCE_INSUFFICIENT

SPEC GAP:
- none / details
```
