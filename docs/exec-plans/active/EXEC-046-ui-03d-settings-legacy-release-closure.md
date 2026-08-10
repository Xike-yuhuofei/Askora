# EXEC-046 — UI-03D Settings Hierarchy, Legacy Cleanup and Release Closure

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P0/P1 Product Closure  
> Governing: ADR-0014, `UI-IES-*`, `UI-SCREEN-100..110`, `UI-VIS-100..101`, `UI-QUAL-*`, UI-03 Vertical Slice  
> Depends on: `EXEC-045 DONE`

## Objective

完成 UI-03 最终闭环：把 Settings 从 giant control grid 重构为 hierarchical category navigation + secondary task destinations，保持 P1-02/P1-03/P1-05/P1-07 security/data semantics；证明并清理无使用者的 legacy chat-first UI；执行完整 responsive/accessibility/security/E2E gate 并形成 UI-03 release evidence。

## Dependency Gate

- EXEC-045 DONE；
- EXEC-043/044/045 commits 均已归档并保持 frontend gates 绿色；
- Settings P1-02/P1-03/P1-05/P1-07 relevant regression tests 绿色；
- 无其他 active EXEC 修改 Settings/App/route finalization files。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Specs

- `AGENTS.md`
- ADR-0014
- `UI-IES-*`
- `UI-IA-*`
- `UI-SCREEN-100..110`
- `UI-VIS-100..101`
- `UI-QUAL-*`
- UI-03 Vertical Slice
- P1-02 model configuration specs
- P1-03 data control/recovery specs
- P1-05 identity/account lifecycle specs
- P1-07 recovery contract/slice

## Current Reality

当前 `Settings.jsx` 在单页同时展开 Recovery Center、账号信息、运行状态、永久删除、数据导出、隐私事实、修改密码、会话管理、恢复套件等完整流程。真实功能较完整，但 IA 属于 control-panel style。

`Chat.jsx` 仍存在旧 chat-first component；当前 canonical routes 主要使用 `TutorWorkspace`。删除必须基于 route/import/static evidence，而非仅凭命名判断。

## Allowed Files

```text
apps/frontend/src/App.jsx
apps/frontend/src/router.jsx
apps/frontend/src/components/Sidebar.jsx
apps/frontend/src/components/Sidebar.css
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/pages/Chat.jsx                         # delete only after proof
apps/frontend/src/pages/Chat.css                         # delete only after proof
apps/frontend/src/pages/Unavailable.jsx                  # only if route/recovery presentation needs final adjustment
apps/frontend/src/pages/Unavailable.css                  # same restriction
apps/frontend/src/pages/settings/**                      # new category/task components if chosen
apps/frontend/src/components/settings/**                 # new reusable settings components if chosen
apps/frontend/src/test/**Settings**
apps/frontend/src/test/**settings**
apps/frontend/src/test/**Chat**
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/**accessibility**
apps/frontend/src/test/**navigation**
docs/releases/ui-03-interactive-element-system.md       # new
docs/releases/README.md
docs/exec-plans/active/EXEC-046-ui-03d-settings-legacy-release-closure.md
docs/exec-plans/completed/EXEC-046-ui-03d-settings-legacy-release-closure.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

若当前仓库测试文件名不同，可修改本 scope 对应 frontend tests。禁止以通配理由修改 backend/domain。

## Forbidden Changes

- 修改 credential storage/secret lifetime/provider probe semantics；
- 修改 backup/restore/export/erasure owner truth；
- 修改 auth/session/recovery-kit security semantics；
- 修改 RecoveryAction contract；
- 删除或弱化 destructive confirmation；
- 创建第二套 settings business state；
- 删除 `TutorWorkspace` 或 `/quick/:sessionId`；
- 删除 `Chat.jsx` 前没有静态/route proof；
- 新增 global search/backend；
- 把 UI cleanup 扩大成 backend refactor。

## Implementation Tasks

1. 记录 Settings/route/security tests baseline 与 Chat import/route graph。
2. 先写 RED tests：Settings utility placement、category landing、secondary destinations、security flow preservation、legacy Chat route absence。
3. 建立 Settings categories，只为已有真实 capability 建 route/component；不得创建空占位设置项。
4. 将 model、data/privacy、account/recovery、advanced/system capability 组织到对应 category；尽量复用现有 handlers/state/components，避免复制逻辑。
5. normal runtime status 降低主层级；degraded/action-required 仍可见。
6. 保留 Recovery global indicator + Settings fallback entry。
7. 对 `Chat.jsx`/`Chat.css` 执行 route/import/static search；无使用者时删除并补防回归 test；仍有合法依赖时记录 retirement blocker，不强删。
8. 清理只服务旧 7-item IA 的 dead CSS/组件，但不得大范围视觉重写。
9. 跑全 UI-03 E2E：Today→Learning facets、Library contextual actions、Settings categories、legacy deep links、Welcome/default entry。
10. 完成 1440/1024/768/360、200% zoom、keyboard/focus/live region、contextual touch-equivalent、security regression。
11. 运行 full frontend/build/audit/docs/diff gates，形成 UI-03 release report。
12. 全部 AC PASS 后归档 EXEC-046，并将 UI-03 标记 DONE；独立 commit。

## Acceptance Criteria

- `EXEC046-AC-001`：`UI03-AC-010..016` PASS。
- `EXEC046-AC-002`：Settings landing 以 category navigation 为主，不同复杂 flow 不再同屏全部展开。
- `EXEC046-AC-003`：P1-02 credential 完整性/保密性无回归。
- `EXEC046-AC-004`：P1-03 backup/export/restore/erasure truth 与 confirmation 无回归。
- `EXEC046-AC-005`：P1-05 password/session/recovery/account-deletion flows 无回归。
- `EXEC046-AC-006`：P1-07 recovery issue/action semantics 无回归。
- `EXEC046-AC-007`：legacy Chat 仅在无使用者证明后删除；compatibility TutorWorkspace 保留。
- `EXEC046-AC-008`：完整 UI-03 route/navigation/accessibility/security E2E PASS。
- `EXEC046-AC-009`：UI Engineering / Contract / Accessibility-Security PASS；Learning Evidence claim unchanged。

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

另外必须提供 P1-02/P1-03/P1-05/P1-07 relevant frontend/integration/security regression evidence；若其测试位于 backend，可运行 targeted tests，但不得修改 backend。

## Completion Report Format

分别报告：

- Engineering Gate；
- UI Contract Correctness；
- Accessibility/Security；
- P1-02/03/05/07 regression matrix；
- UI03-AC-001..016 final matrix；
- legacy Chat proof/decision；
- responsive/zoom/keyboard evidence；
- tests/build/audit/docs；
- commits；
- release report；
- Learning Evidence unchanged；
- remaining SPEC GAP / retirement items。
