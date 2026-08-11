# EXEC-071 — UI-04D Learning Management Exposure Removal

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UX Architecture  
> Product Traceability: `CAP-02`、`CAP-03`、`CAP-07`、`PD-REQ-0201..0303`、`PD-REQ-0701..0703`  
> Governing: `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`, `docs/specs/ui/screen-and-navigation-contracts.md`, `docs/design/experience/INTERACTION-MODEL.md`, ADR-0018, UI-04 Vertical Slice  
> Depends on: `EXEC-070 DONE`

## Objective

Learning 主界面不再暴露 Goal/Plan/Progress/History 常驻管理 facet。这不删除 LearningGoal / LearningPlan / LearnerState / Evidence / ReviewSchedule / History canonical truth，它们继续驱动教学。必要创建/纠正/确认/恢复/审计在明确 user job 下进入 contextual task flow，不恢复长期管理中心。

## Dependency Gate

- `EXEC-070 DONE`；
- 无其他 active EXEC 修改 Learning 管理页面相关 files。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- `docs/design/experience/INTERACTION-MODEL.md`
- `docs/specs/ui/screen-and-navigation-contracts.md`（`UI-NAV-003`、`UI-ROUTE-003..005`、`UI-LEARN-001..003`）
- ADR-0018
- UI-04 Vertical Slice

## Current Reality

执行起点必须重新读取 current `main` 判断 `/learning` 与 compatibility routes 的真实暴露状态。本 EXEC 不以历史四-facet 实现作为 current truth。

## Allowed Files

```text
apps/frontend/src/pages/Learning.jsx
apps/frontend/src/pages/Goals.jsx
apps/frontend/src/pages/LearningPath.jsx
apps/frontend/src/pages/Evidence.jsx
apps/frontend/src/pages/History.jsx
apps/frontend/src/components/LearningNavigation.jsx
apps/frontend/src/components/LearningShell.jsx
apps/frontend/src/test/**Learning**
apps/frontend/src/test/**Goals**
apps/frontend/src/test/**LearningPath**
apps/frontend/src/test/**Evidence**
apps/frontend/src/test/**History**
docs/exec-plans/active/EXEC-071-ui-04d-learning-management-exposure-removal.md
docs/exec-plans/completed/EXEC-071-ui-04d-learning-management-exposure-removal.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

## Forbidden Changes

- 删除 LearningGoal / LearningPlan / LearnerState / Evidence / ReviewSchedule / History 数据或 owner；
- 修改 Teaching Policy / mastery / review 算法；
- 恢复常驻管理中心 / 四等权管理 Card；
- 删除旧 `/learning/**` 路由（保迁移）；
- 修改 backend API / schema / migration。

## Implementation Tasks

1. 记录 current `main` 中 Learning 管理 facet 暴露方式。
2. 先写 RED tests：Learning 不暴露常驻 Goal/Plan/Progress/History 管理；必要创建/纠正/确认/恢复/审计仅在明确 user job 下进入 contextual task-flow；domain truth 数据保留。
3. 移除常驻管理 facet 暴露，改为 contextual task-flow 入口（仅明确 user job）。
4. 保留旧 `/learning/**` 迁移与 deep-link 兼容，不产生 route side effect。
5. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC071-AC-001`：`UI-SN-AC-002/005/010` 与适用 `UI-QR-*` PASS；
- `EXEC071-AC-002`：Learning 不暴露常驻 Goal/Plan/Progress/History 管理 facet；
- `EXEC071-AC-003`：LearningGoal/LearningPlan/LearnerState/Evidence/ReviewSchedule/History canonical truth 无删除；
- `EXEC071-AC-004`：contextual task-flow 仅在明确 user job 下进入，不恢复长期管理中心；
- `EXEC071-AC-005`：旧 `/learning/**` 路由保留迁移与 deep-link 且无业务副作用；
- `EXEC071-AC-006`：无 owner 数据 / schema / migration 删除；
- `EXEC071-AC-007`：UX Acceptance 与 Product Acceptance / Learning Evidence 分开报告。

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

至少提供：de-management 暴露移除、contextual task-flow gate、canonical truth 保留、route/deep-link 兼容/no-side-effect、keyboard/accessibility 证据。

## Completion Report Format

报告：修改文件、de-management 暴露矩阵、contextual task-flow 入口证据、canonical truth 保留证据、route/deep-link 兼容、gates、commit。