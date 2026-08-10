# EXEC-068 — UI-04A Workspace Context / Shell / Route Migration

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UX Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0018, `UXA-IA-*`, `UXA-SCREEN-100..114`, `UXA-COMP-070..073`, UI-04 Vertical Slice  
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

- `ADR-0018` accepted 并登记于 `docs/adr/README.md`；
- UI Spec set（`UXA-*`）FROZEN；
- `EXEC-1062` DONE（shared frontend files non-overlap）；
- Workspace 产品架构 entry gate：若 Workspace switch command owner 未由现有上位合同冻结，返回 `BLOCKED_BY_SPEC_GAP`，不得用前端本地 state 或 mock Workspace。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0014、ADR-0018
- `UXA-IA-*`、`UXA-SCREEN-100..114`、`UXA-COMP-*`
- UI-04 Vertical Slice
- `ADR-0016` / `WSP-*`（Workspace 语义）

## Current Reality

当前 `main` 已有 Today/Learning/Library 三域导航、`/learning/**` 路由、Tutor Workspace 中央对话画布与左栏 session-history rail。旧 `/learning/goals|plan|progress|history` 仍作为常驻管理页面。Workspace durable 实现尚未完成。

## Allowed Files

```text
apps/frontend/src/App.jsx
apps/frontend/src/router.jsx
apps/frontend/src/components/AppShell.jsx
apps/frontend/src/components/Sidebar.jsx
apps/frontend/src/components/WorkspaceContext*.jsx   # new, shell-only
apps/frontend/src/test/**WorkspaceContext**
apps/frontend/src/test/**appRoutes**
docs/exec-plans/active/EXEC-068-ui-04a-workspace-context-shell-routes.md
docs/exec-plans/completed/EXEC-068-ui-04a-workspace-context-shell-routes.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

## Forbidden Changes

- 实现 Workspace owner / command / 持久化；
- 用 route / subject / session / localStorage 冒充 Workspace truth；
- Workspace 切换静默丢弃 draft / stream / note / session / material-tab；
- 删除旧 `/learning/**` 路由或删除 Goal/Plan/Evidence/History 数据；
- 建立 placeholder / disabled tab 代表 deferred candidates；
- 修改 Teaching Policy / mastery / review / backend API / schema / migration；
- 修改其他 UI-04 EXEC 的 Allowed Files。

## Implementation Tasks

1. 记录当前 shell / route baseline 与 Workspace 相关状态。
2. 先写 RED tests：三栏解析同一 canonical `current_workspace_id`；单一 Workspace 无虚假 selector；旧 `/learning/**` 迁移无业务副作用；deferred candidates 不建 placeholder。
3. 建立三栏 shell：Left = Where（导航 + current Workspace 可见性），Center = Learn（唯一 Primary Canvas），Right = Reference/Notes（可隐藏占位，内容由后续 EXEC 填充）。
4. current Workspace 显示 `LOADING/EMPTY/READY/PARTIAL/STALE/ERROR`；切换为 `saved/saving/failed/recoverable`。
5. 若 Workspace switch command owner 未冻结，报告 `BLOCKED_BY_SPEC_GAP` 并以兼容/只读方式呈现，不假装切换成功。
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