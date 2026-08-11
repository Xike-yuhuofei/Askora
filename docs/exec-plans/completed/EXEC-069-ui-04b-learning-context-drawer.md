# EXEC-069 — UI-04B Learning Context Drawer Query and UI

> Status: **DONE / ARCHIVED**
> Priority: P1 UX Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0018, ADR-0019, `UXA-IA-004`, `UXA-SCREEN-120..124`, `UXA-DATA-220..223`, `UXA-IES-01`, `UXA-COMP-071`, UI-04 Vertical Slice
> Depends on: `EXEC-068 DONE`

## Objective

实现 Learning Context Drawer：固定在中栏 composer/输入区正上方，默认收起，收起只显示一行 `当前阶段 · 接下来`；展开只显示当前阶段、阶段目标与接下来 1..3 个动态知识点/教学方向。内容来自 canonical/versioned query，前端不得推断。

## Dependency Gate

- `EXEC-068 DONE`；
- ADR-0019 Drawer canonical read query contract 已冻结；
- 无其他 active EXEC 修改 Drawer 相关 frontend files。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0018
- ADR-0019
- `UXA-IA-004`、`UXA-SCREEN-120..124`、`UXA-DATA-220..222`
- UI-04 Vertical Slice

## Current Reality

PR #30 已加入名为 `LearningContextDrawer` 的材料管理 dialog，但它读取 `MOCK_RESOURCES`/React state、并非 composer 上方的 stage/goal/next Disclosure。该实现不得因文件名相同被视为完成；本 EXEC 只把它收敛到 ADR-0019 query 和冻结状态矩阵。

## Allowed Files

```text
apps/frontend/src/components/LearningContextDrawer*.jsx   # new
apps/frontend/src/components/LearningContextDrawer*.css
apps/frontend/src/api/workspace.js
apps/frontend/src/pages/ActivityLearning.jsx              # composer region integration
apps/frontend/src/pages/ActivityLearning.css
apps/frontend/src/pages/TutorWorkspace.jsx
apps/frontend/src/pages/TutorWorkspace.css
apps/frontend/src/pages/LearningWorkspace.jsx
apps/frontend/src/pages/LearningWorkspace.css
apps/frontend/src/test/**ContextDrawer**
apps/frontend/src/test/ActivityLearning.test.jsx
apps/frontend/src/test/TutorWorkspace.test.jsx
apps/backend/app/contracts/workspace.py
apps/backend/app/queries/workspace.py
apps/backend/app/api/v1/workspace.py
apps/backend/tests/**ui04*learning_context**
docs/adr/ADR-0019-ui-workspace-read-projections.md
docs/adr/README.md
docs/specs/architecture/state-ownership.md
docs/specs/interfaces/api-contract.md
docs/specs/ui/data-contracts.md
docs/specs/vertical-slices/ui-04-ux-workspace-context.md
docs/document-inventory.md
docs/exec-plans/active/EXEC-069-ui-04b-learning-context-drawer.md
docs/exec-plans/completed/EXEC-069-ui-04b-learning-context-drawer.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

## Forbidden Changes

- 实现 Drawer 的 owner / command / schema；
- 从 chat 文本、heading 顺序或 probability threshold 推断 stage / goal / next；
- LLM 输出写成 canonical next knowledge point；
- 在 Drawer 加入完整 Goal editor / Plan / Progress / Evidence 管理 / mastery / ReviewSchedule / TeachingAction 控制；
- expand/collapse 触发 owner command；
- 修改 database schema / migration / Teaching Policy；除 ADR-0019 只读 query 外修改 backend API。

## Implementation Tasks

1. 记录当前 composer 上方 UI 与运行查询方式。
2. 先写 RED tests：默认收起；收起只显示 `当前阶段 · 接下来` 一行；展开只显示 stage/stage goal/next 1..3；`MISSING/PARTIAL/STALE` 诚实呈现；expand/collapse 不触发 command；失败不阻断主任务。
3. 建立 Drawer 组件，接入 canonical/versioned query 或显式 `MISSING/PARTIAL/STALE`。
4. 实现收起/展开（presentation-only，`aria-expanded`），focus 返回触发点。
5. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC069-AC-001`：适用的 `UXA04-AC-005..006,013..014` PASS；
- `EXEC069-AC-002`：Drawer 默认收起，收起只显示一行方向信息；
- `EXEC069-AC-003`：展开只显示 stage / stage goal / next 1..3；
- `EXEC069-AC-004`：内容来自 canonical/versioned query 或 `MISSING/PARTIAL/STALE`，前端不推断；
- `EXEC069-AC-005`：expand/collapse 不触发 owner command，失败不阻断主任务；
- `EXEC069-AC-006`：无 owner command / schema / migration change。

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

至少提供：Drawer collapsed/expanded/missing/partial/stale/error、presentation-only、focus return、keyboard/touch/screen reader 证据。

## Completion Report Format

报告：修改文件、Drawer 状态矩阵、canonical query 来源、前端不推断证据、SPEC GAP（若 Drawer query 未冻结）、gates、commit。
