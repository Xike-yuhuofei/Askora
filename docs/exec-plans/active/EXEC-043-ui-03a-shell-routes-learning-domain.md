# EXEC-043 — UI-03A Shell, Routes and Learning Domain

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P0 Interaction Architecture  
> Governing: ADR-0014, `UI-IES-*`, `UI-IA-*`, `UI-SCREEN-*`, UI-03 Vertical Slice  
> Depends on: `EXEC-1062 DONE`

## Objective

完成 ADR-0014 的结构基础：把全局产品导航收敛为 Today/Learning/Library，建立 Learning L1 facets，并将旧 Goals/Path/Evidence/History routes 无副作用迁移到 `/learning/**`。

本 EXEC 不改 Today 内容层级、不改 Library 管理方式、不重构 Settings 业务页面；这些属于后续 EXEC。

## Dependency Gate

执行前必须确认：

- EXEC-1062 已归档 DONE；
- P1-06 default route/deep-link/Settings reopen tests 当前绿色；
- UI Specs 当前 FROZEN；
- 无其他 active EXEC 修改本 EXEC Allowed Files。

未满足：返回 `BLOCKED_BY_DEPENDENCY`，不得开始代码修改。

## Required Specs

- `AGENTS.md`
- `docs/adr/ADR-0014-user-job-driven-interaction-architecture.md`
- `docs/specs/ui/interactive-element-system.md`
- `docs/specs/ui/information-architecture.md`
- `docs/specs/ui/screen-contracts.md`
- `docs/specs/ui/visual-system.md`
- `docs/specs/ui/quality-and-migration.md`
- `docs/specs/vertical-slices/ui-03-interactive-element-system-refactor.md`
- Goal/P1-01 specs for route behavior preservation

## Current Reality

当前 `App.jsx` canonical standard pages 仍直接暴露 `/goals`、`/path`、`/evidence`、`/history`；`Sidebar.jsx` 把 Today/Goals/Path/Library/Evidence/History/Settings 作为同级 nav items。

Goal create/detail/edit 已实现，必须迁移 route 而非降级为只读。

## Allowed Files

```text
apps/frontend/src/App.jsx
apps/frontend/src/router.jsx
apps/frontend/src/components/AppShell.jsx
apps/frontend/src/components/AppShell.css
apps/frontend/src/components/Sidebar.jsx
apps/frontend/src/components/Sidebar.css
apps/frontend/src/components/LearningNavigation.*           # new if needed
apps/frontend/src/components/LearningShell.*                # new if needed
apps/frontend/src/pages/Goals.jsx
apps/frontend/src/pages/Goals.css
apps/frontend/src/pages/GoalDetail.jsx
apps/frontend/src/pages/GoalEditor.jsx
apps/frontend/src/pages/GoalEditor.css
apps/frontend/src/pages/LearningPath.jsx
apps/frontend/src/pages/LearningPath.css
apps/frontend/src/pages/Evidence.jsx
apps/frontend/src/pages/Evidence.css
apps/frontend/src/pages/History.jsx
apps/frontend/src/pages/History.css
apps/frontend/src/pages/Learning.jsx                         # new if needed
apps/frontend/src/pages/Learning.css                         # new if needed
apps/frontend/src/test/**route**
apps/frontend/src/test/**Sidebar**
apps/frontend/src/test/**Learning**
apps/frontend/src/test/AppRoutes.test.jsx
docs/exec-plans/active/EXEC-043-ui-03a-shell-routes-learning-domain.md
docs/exec-plans/completed/EXEC-043-ui-03a-shell-routes-learning-domain.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

若真实测试文件名称不同，可修改与本 scope 直接相关的现有 frontend tests；不得借通配说明扩大到无关页面。

## Forbidden Changes

- backend/domain/API/schema changes；
- Today Quick Start redesign；
- Library batch/OCR redesign；
- Settings content hierarchy redesign；
- TeachingAction/LearnerState/Plan semantics；
- 删除 `/quick/:sessionId` compatibility workspace；
- 用 route state 持久化 focused goal；
- 新增 global search；
- 恢复七项平级 navigation。

## Implementation Tasks

1. 记录 base commit、git status、frontend test/build baseline。
2. 先补 RED tests：L0 nav、Learning facets、新 routes、legacy redirects、no-side-effect route behavior。
3. 将 Product Domain navigation 改为 Today/Learning/Library；Settings/Recovery 放 utility group。
4. 实现 `/learning` shell/local navigation，复用现有 Goal/Plan/Evidence/History 页面。
5. 将 Goal list/detail/new/draft/edit canonical routes 迁到 `/learning/goals/**`。
6. 将 Path/Evidence/History canonical routes 迁到 `/learning/plan|progress|history`。
7. 保留 `/goals/**`、`/path`、`/evidence`、`/history`、`/profile` 的无副作用 redirect，并保留参数。
8. 验证 `/welcome`、`/today`、explicit deep links 与 P1-06 contract 不回归。
9. 完成 keyboard/focus/360px navigation tests。
10. 跑 required gates；全部 AC 后独立 commit 并归档 EXEC-043。

## Acceptance Criteria

- `EXEC043-AC-001`：`UI03-AC-001..005` PASS。
- `EXEC043-AC-002`：Sidebar/Product Nav 只有 Today/Learning/Library；Settings/Recovery 明确 utility 分组。
- `EXEC043-AC-003`：Learning 四 facets 可达且 facet navigation 无业务写入。
- `EXEC043-AC-004`：Goal create/detail/edit/draft 在新 route 行为与 owner contract 不变。
- `EXEC043-AC-005`：legacy routes preserve params，并只 redirect。
- `EXEC043-AC-006`：`/welcome` 和 explicit deep-link preservation 不回归。
- `EXEC043-AC-007`：360/768/1024/1440 下 navigation 可操作；keyboard focus 可见。
- `EXEC043-AC-008`：无 backend/public schema change。

## Required Tests

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

至少提供 route resolver、Sidebar/Learning navigation、legacy redirect、Goal route、keyboard/accessibility 的 targeted test evidence。

## Completion Report Format

报告：base/final commit、修改文件、UI03/EXEC AC、测试命令结果、route matrix、responsive/keyboard evidence、P1-06 regression evidence、未完成项、SPEC GAP。
