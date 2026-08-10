# EXEC-071 — UI-04D Learning Management Exposure Removal

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UX Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0018, `UXA-IA-005`, `UXA-SCREEN-160..161`, UI-04 Vertical Slice  
> Depends on: `EXEC-070 DONE`

## Objective

Learning 主界面不再暴露 Goal/Plan/Progress/History 常驻管理 facet。这不删除 LearningGoal / LearningPlan / LearnerState / Evidence / ReviewSchedule / History canonical truth，它们继续驱动教学。必要创建/纠正/确认/恢复/审计在明确 user job 下进入 contextual task flow，不恢复长期管理中心。

## Dependency Gate

- `EXEC-070 DONE`；
- 无其他 active EXEC 修改 Learning 管理页面相关 files。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0018
- `UXA-IA-005`、`UXA-SCREEN-160..161`
- UI-04 Vertical Slice

## Current Reality

`/learning` 及其子路由仍常驻暴露 Goal/Plan/Progress/History 管理页面与导航。

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

1. 记录当前 Learning 管理 facet 暴露方式。
2. 先写 RED tests：Learning 不暴露常驻 Goal/Plan/Progress/History 管理；必要创建/纠正/确认/恢复/审计仅在明确 user job 下进入 contextual task-flow；domain truth 数据保留。
3. 移除常驻管理 facet 暴露，改为 contextual task-flow 入口（仅明确 user job）。
4. 保留旧 `/learning/**` 迁移与 deep-link 兼容。
5. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC071-AC-001`：适用的 `UXA04-AC-010,014` PASS；
- `EXEC071-AC-002`：Learning 不暴露常驻 Goal/Plan/Progress/History 管理 facet；
- `EXEC071-AC-003`：LearningGoal/LearningPlan/LearnerState/Evidence/ReviewSchedule/History canonical truth 无删除；
- `EXEC071-AC-004`：contextual task-flow 仅在明确 user job 下进入，不恢复长期管理中心；
- `EXEC071-AC-005`：旧 `/learning/**` 路由保留迁移与 deep-link；
- `EXEC071-AC-006`：无 owner 数据 / schema / migration 删除。

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

至少提供：de-management 暴露移除、contextual task-flow gate、canonical truth 保留、route/deep-link 兼容、keyboard/accessibility 证据。

## Completion Report Format

报告：修改文件、de-management 暴露矩阵、contextual task-flow 入口证据、canonical truth 保留证据、route/deep-link 兼容、gates、commit。