# EXEC-068 — UI-04A Workspace Context / Shell / Route Migration

> Status: **DONE / ARCHIVED**
> Priority: P1 UX Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0018, ADR-0019, `UXA-IA-*`, `UXA-SCREEN-100..114`, `UXA-DATA-200`, `UXA-COMP-070..073`, UI-04 Vertical Slice
> Depends on: `EXEC-1062 DONE` + Workspace Product Architecture entry gate（XIK-171 / XIK-177 / XIK-172 / XIK-175 / XIK-179 / XIK-165 where applicable）

## Objective

建立 `UX-Architecture-Canonical-Design-Delta.md` 经 `ADR-0018` 吸收后的三栏外壳与 Workspace 上下文：

```text
Left (Where)      Center (Learn)                    Right (Reference / Notes)
Global Nav        Teaching content                  User-authored notes
Current Workspace Questions                          Current source material
Workspace switch  Learner answers                   Citation / source context
                  Feedback
                  Learning Context Drawer
                  Composer
```

本 EXEC 只做 shell / 导航 / Workspace 上下文的呈现与 route 迁移，不实现 Workspace 的 owner/command，不实现 Drawer / Notes / Material 内容。

## Dependency Gate

- `ADR-0018` accepted 并登记于 `docs/architecture/README.md`；
- UI Spec set（`UXA-*`）FROZEN；
- `EXEC-1062` DONE（shared frontend files non-overlap）；
- ADR-0019 canonical current Workspace read query 已冻结；V1 单一 Workspace 不需要 switch command，也不得显示 selector。未来多 Workspace switch 仍需独立 command contract。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0014、ADR-0018
- ADR-0019
- `UXA-IA-*`、`UXA-SCREEN-100..114`、`UXA-COMP-*`
- UI-04 Vertical Slice
- `ADR-0016` / `WSP-*`（Workspace 语义）

## Current Reality

当前 `main` 已有 durable default Workspace 与三栏视觉骨架，但 `WorkspaceProvider` 仍以 `default/默认工作区` 前端常量冒充 canonical Workspace；部分三栏内容提前实现为本地 React/mock truth；Learning 默认 route 尚未稳定进入 canonical Workspace shell。ADR-0019 已冻结只读 query，允许本 EXEC 只修这些实际 Gap。

## Allowed Files

```text
apps/frontend/src/App.jsx
apps/frontend/src/router.jsx
apps/frontend/src/api/workspace.js
apps/frontend/src/components/AppShell.jsx
apps/frontend/src/components/AppShell.css
apps/frontend/src/components/Sidebar.jsx
apps/frontend/src/components/WorkspaceContext*.jsx   # new, shell-only
apps/frontend/src/components/WorkspaceContext*.css
apps/frontend/src/components/RightRail.jsx            # only remove premature local truth / keep shell placeholder
apps/frontend/src/components/RightRail.css
apps/frontend/src/pages/LearningWorkspace.jsx         # only remove mock truth / establish primary-canvas compatibility state
apps/frontend/src/pages/LearningWorkspace.css
apps/frontend/src/test/**WorkspaceContext**
apps/frontend/src/test/**appRoutes**
apps/frontend/src/test/AppRoutes.test.jsx
apps/backend/app/contracts/workspace.py
apps/backend/app/queries/workspace.py
apps/backend/app/api/v1/workspace.py
apps/backend/tests/**ui04*workspace**
docs/architecture/decisions/ADR-0019-ui-workspace-read-projections.md
docs/architecture/README.md
docs/specs/architecture/state-ownership.md
docs/specs/interfaces/api-contract.md
docs/specs/frontend/ui-read-model-contracts.md
docs/specs/vertical-slices/ui-04-ux-workspace-context.md
docs/governance/document-inventory.md
docs/planning/execs/EXEC-068-ui-04a-workspace-context-shell-routes.md
docs/archive/exec-plans/EXEC-068-ui-04a-workspace-context-shell-routes.md
docs/planning/README.md
docs/archive/exec-plans/README.md
```

## Forbidden Changes

- 实现 Workspace owner / command / 持久化；
- 用 route / subject / session / localStorage 冒充 Workspace truth；
- Workspace 切换静默丢弃 draft / stream / note / session / material-tab；
- 删除旧 `/learning/**` 路由或删除 Goal/Plan/Evidence/History 数据；
- 建立 placeholder / disabled tab 代表 deferred candidates；
- 修改 Teaching Policy / mastery / review / database schema / migration；除 ADR-0019 只读 query 外修改 backend API；
- 修改其他 UI-04 EXEC 的 Allowed Files。

## Implementation Tasks

1. 记录当前 shell / route baseline 与 Workspace 相关状态。
2. 先写 RED tests：三栏解析同一 canonical `current_workspace_id`；单一 Workspace 无虚假 selector；旧 `/learning/**` 迁移无业务副作用；deferred candidates 不建 placeholder。
3. 建立三栏 shell：Left = Where（导航 + current Workspace 可见性），Center = Learn（唯一 Primary Canvas），Right = Reference/Notes（可隐藏占位，内容由后续 EXEC 填充）。
4. 接入 ADR-0019 current Workspace query；显示 `LOADING/EMPTY/READY/PARTIAL/STALE/ERROR`，不得由 route/frontend state 构造 Workspace。
5. V1 单一 Workspace 不显示 selector/switch；未来多 Workspace command 未冻结前保持只读，不假装切换成功。
6. 旧 `/learning/goals|plan|progress|history` 迁移为 contextual / task-flow 可达（仅明确 user job），保留 deep-link。
7. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC068-AC-001`：适用的 `UXA04-AC-001..004` PASS；
- `EXEC068-AC-002`：三栏解析同一 canonical `current_workspace_id`；
- `EXEC068-AC-003`：单一 Workspace 不显示虚假 selector；
- `EXEC068-AC-004`：旧 `/learning/**` route 无副作用迁移，deep link 保留；
- `EXEC068-AC-005`：deferred candidates 不建 placeholder / disabled tab；
- `EXEC068-AC-006`：无 owner command / schema / migration change；未冻结的 Workspace switch 标记 `BLOCKED_BY_SPEC_GAP`。

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

至少提供：shell 三栏、current Workspace 状态、route 无副作用迁移、deferred no-placeholder、360/768/1024/1440 responsive、keyboard/focus 证据。

## Completion Report Format

报告：修改文件、三栏 shell 证据、Workspace 状态矩阵、route 迁移矩阵、deferred candidates disposition、SPEC GAP（若 Workspace switch owner 未冻结）、gates、commit。

## Completion Evidence (2026-08-11)

- ADR-0019 已冻结 canonical current Workspace read projection；无 Workspace command/schema/migration。
- frontend `default/默认工作区` 常量与 route-derived Workspace 已移除；Left/Center/Right 共享 owner query 返回的 exact id。
- V1 `SINGLE_WORKSPACE` 无 selector；query error 不制造默认 Workspace，且不阻断 Primary Canvas。
- PR #30 提前加入的 Note/Material/browser state 已降为诚实不可用状态，不再冒充 durable truth。
- `/learning` 进入 Workspace shell；历史 `/learning/**` deep link 与 no-side-effect route mapping 保留。
- targeted backend/frontend tests、frontend full tests/build/audit、docs/diff gates PASS；最终全量 backend gates 随 EXEC-069 PR evidence 一并提供。
- `POSITIONING GAP`: none；`SPEC GAP`: none（ADR-0019 closed the read-query gap）。
