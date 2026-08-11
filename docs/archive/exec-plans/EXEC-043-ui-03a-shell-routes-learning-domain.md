# EXEC-043 — UI-03A Shell, Routes and Learning Domain

> Status: **DONE / archived 2026-08-10**  
> Priority: P0 Interaction Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0014, `UI-IES-*`, `UI-IA-*`, `UI-SCREEN-*`, UI-03 Vertical Slice  
> Depends on: `EXEC-1062 DONE` + `EXEC-051 DONE`

## Objective

完成 ADR-0014 的结构基础：把全局产品导航收敛为 Today/Learning/Library，建立 Learning L1 facets，并将旧 Goals/Path/Evidence/History routes 无副作用迁移到 `/learning/**`。

本 EXEC 不改 Today 内容层级、不改 Library 管理方式、不重构 Settings 业务页面；这些属于后续 EXEC。

本 EXEC 必须基于 ADR-0015 已完成的 no-auth LocalOwner shell，不得恢复 Login、ProtectedRoute、AuthProvider 或账号 utility。

所有 route/shell 设计同时必须服从 PRODUCT-POSITIONING：Askora v1 是单用户 Local Web Application；Workspace 是高层数据隔离边界而不是 Tenant；Learning Project 不是开始学习的强制门禁；不得通过 UI route 形成跨 Workspace 的隐式全局学习状态。

## Dependency Gate

执行前必须确认：

- EXEC-1062 已归档 DONE；
- EXEC-047～051 已归档 DONE，ADR-0015 / `LID-*` release evidence PASS；
- P1-06 default route/deep-link/Settings reopen tests 当前绿色；
- UI Specs 当前 FROZEN；
- 无其他 active EXEC 修改本 EXEC Allowed Files。

未满足：返回 `BLOCKED_BY_DEPENDENCY`，不得开始代码修改。

## Required Product Positioning

必须读取 `docs/product/PRODUCT-POSITIONING.md`，至少核对：

- v1 = single-user Local Web Application；
- no-auth / no account；
- Workspace 是学习数据与 Retrieval Scope 的高层隔离边界，不是 Tenant / Organization；
- Learning Project 是可选的长期学习组织单位，不得成为直接从 Material 开始学习的门禁；
- v1 不建设跨 Workspace Global Material Library；
- Conversation / Message 不得成为核心学习领域模型。

如当前 UI Spec 与以上上位约束冲突，必须返回 `BLOCKED_BY_SPEC_GAP`，不得用下位 UI Spec 覆盖 Product Positioning。

## Required Specs

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/architecture/decisions/ADR-0014-user-job-driven-interaction-architecture.md`
- `docs/architecture/decisions/ADR-0015-local-single-user-identity-without-authentication.md`
- `docs/specs/platform/identity-privacy-lifecycle.md`
- `docs/archive/specs/ui/interactive-element-system.md`
- `docs/archive/specs/ui/information-architecture.md`
- `docs/archive/specs/ui/screen-contracts.md`
- `docs/archive/specs/ui/visual-system.md`
- `docs/archive/specs/ui/quality-and-migration.md`
- `docs/archive/specs/vertical-slices/ui-03-interactive-element-system-refactor.md`
- Goal/P1-01 specs for route behavior preservation

## Current Reality

进入本 EXEC 时，Authentication Removal 必须已完成：App 无 Login/AuthProvider/ProtectedRoute，frontend/backend 使用 LocalOwnerContext；本 EXEC 只能在该 baseline 上重构 IA。

当前 UI-03 baseline 的 Goal create/detail/edit 已实现，必须迁移 route 而非降级为只读。

当前 route 迁移还必须避免把 Workspace 误建模为账号/租户选择器，也不得因为 Learning 域重组把 Project 变成所有学习动作的必经入口。

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
docs/planning/execs/EXEC-043-ui-03a-shell-routes-learning-domain.md
docs/archive/exec-plans/EXEC-043-ui-03a-shell-routes-learning-domain.md
docs/planning/README.md
docs/archive/exec-plans/README.md
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
- 恢复七项平级 navigation；
- 恢复 Login/Account/AuthSession/ProtectedRoute/AuthProvider 等被 ADR-0015 supersede 的语义；
- 把 Workspace 建模为 Tenant / Organization 或账号容器；
- 通过 Learning shell 默认聚合多个 Workspace 的 Goal、Evidence、History 或 Learner State；
- 把 Learning Project 变成从 Material 启动学习的强制 route gate。

## Implementation Tasks

1. 记录 base commit、git status、frontend test/build baseline。
2. 先补 RED tests：L0 nav、Learning facets、新 routes、legacy redirects、no-side-effect route behavior。
3. 将 Product Domain navigation 改为 Today/Learning/Library；Settings/Recovery 放 utility group。
4. 实现 `/learning` shell/local navigation，复用现有 Goal/Plan/Evidence/History 页面。
5. 将 Goal list/detail/new/draft/edit canonical routes 迁到 `/learning/goals/**`。
6. 将 Path/Evidence/History canonical routes 迁到 `/learning/plan|progress|history`。
7. 保留 `/goals/**`、`/path`、`/evidence`、`/history`、`/profile` 的无副作用 redirect，并保留参数。
8. 验证 `/welcome`、`/today`、explicit deep links 与 P1-06 contract 不回归。
9. 验证 no-auth LocalOwner baseline 不回归。
10. 验证 Learning facets 继续遵守当前 Workspace scope；route 迁移不得创建跨 Workspace global aggregation。
11. 验证直接基于 Material 开始学习的既有能力不因 Learning Project route hierarchy 被门禁化。
12. 完成 keyboard/focus/360px navigation tests。
13. 跑 required gates；全部 AC 后独立 commit 并归档 EXEC-043。

## Acceptance Criteria

- `EXEC043-AC-001`：`UI03-AC-001..005` PASS。
- `EXEC043-AC-002`：Sidebar/Product Nav 只有 Today/Learning/Library；Settings/Recovery 明确 utility 分组。
- `EXEC043-AC-003`：Learning 四 facets 可达且 facet navigation 无业务写入。
- `EXEC043-AC-004`：Goal create/detail/edit/draft 在新 route 行为与 owner contract 不变。
- `EXEC043-AC-005`：legacy routes preserve params，并只 redirect。
- `EXEC043-AC-006`：`/welcome` 和 explicit deep-link preservation 不回归。
- `EXEC043-AC-007`：360/768/1024/1440 下 navigation 可操作；keyboard focus 可见。
- `EXEC043-AC-008`：无 backend/public schema change。
- `EXEC043-AC-009`：ADR-0015 no-auth LocalOwner baseline 不回归。
- `EXEC043-AC-010`：Workspace 仍是高层学习数据隔离边界，不出现 Tenant/Organization/account 语义，也不默认跨 Workspace 聚合 Learning 数据。
- `EXEC043-AC-011`：Learning Project 仍为可选组织单位；route/IA 不阻止直接从 Material 进入学习。

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

至少提供 route resolver、Sidebar/Learning navigation、legacy redirect、Goal route、keyboard/accessibility、no-auth shell、Workspace-scope 与 direct-Material learning regression evidence。

## Completion Report Format

报告：base/final commit、修改文件、UI03/EXEC AC、测试命令结果、route matrix、responsive/keyboard evidence、P1-06 regression evidence、ADR-0015 regression evidence、Workspace-scope/direct-Material evidence、未完成项、SPEC GAP。
