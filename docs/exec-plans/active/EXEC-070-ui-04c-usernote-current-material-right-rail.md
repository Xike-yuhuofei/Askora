# EXEC-070 — UI-04C UserNote + Current Material Right Rail

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UX Architecture  
> Product Traceability: `CAP-01`、`CAP-04`、`CAP-07`、`PD-REQ-0103`、`PD-REQ-0401..0403`、`PD-REQ-0701..0703`  
> Governing: `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`, `docs/design/experience/LEARNING-EXPERIENCE.md`, `docs/specs/ui/learning-interaction-contracts.md`, `docs/specs/ui/screen-and-navigation-contracts.md`, `docs/specs/frontend/ui-read-model-contracts.md`, ADR-0018/0019, UI-04 Vertical Slice  
> Depends on: `EXEC-069 DONE`

## Objective

实现可隐藏的右栏（Reference / Notes）：V1 只支持 Learning Notes（user-authored durable、Workspace-scoped、anchored、versioned）与 Current Material（由 citation / "view source" 在当前 Workspace 上下文打开）。Notes 区分 `SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE`；Current Material / SourceSpan 来自 canonical Workspace refs，跨 Workspace fail closed。

## Dependency Gate

- `EXEC-069 DONE`；
- UserNote durable owner 与 Current Material canonical refs / owner 已冻结（否则返回 `BLOCKED_BY_SPEC_GAP`，不以前端局部 note / localStorage 冒充 durable truth）；
- 无其他 active EXEC 修改右栏相关 frontend files。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- `docs/design/experience/LEARNING-EXPERIENCE.md`
- `docs/design/experience/INTERACTION-MODEL.md`
- `docs/specs/ui/learning-interaction-contracts.md`（`UI-LRN-080..105`）
- `docs/specs/ui/screen-and-navigation-contracts.md`（`UI-SHELL-001..005`）
- `docs/specs/frontend/ui-read-model-contracts.md`（current `UXA-DATA-*` / `UI-DATA-*` technical projections）
- ADR-0018 / ADR-0019
- UI-04 Vertical Slice

## Current Reality

右栏或为旧 Context Inspector 语义；durable UserNote / Current Material 是否已具备完整 owner/command contract 必须在执行起点重新核对 current `main`。不得根据本 EXEC 的历史文字假设 dependency 已满足。

## Allowed Files

```text
apps/frontend/src/components/RightRail*.jsx            # new: hide/show + tabs
apps/frontend/src/components/LearningNotes*.jsx        # new: notes UI
apps/frontend/src/components/CurrentMaterial*.jsx      # new: material tabs
apps/frontend/src/test/**RightRail**
apps/frontend/src/test/**LearningNotes**
apps/frontend/src/test/**CurrentMaterial**
docs/exec-plans/active/EXEC-070-ui-04c-usernote-current-material-right-rail.md
docs/exec-plans/completed/EXEC-070-ui-04c-usernote-current-material-right-rail.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

## Forbidden Changes

- 实现 UserNote 或 Current Material 的 owner / command / schema；
- 用 localStorage / frontend state 作为 note 或 material 的 durable truth；
- 跨 Workspace 聚合或全局 material 库；
- 隐藏右栏时丢失完成任务所需的唯一引用 / 帮助 / validation obligation；
- 未持久化时显示"已保存"；
- 修改 backend API / schema / migration / Teaching Policy。

## Implementation Tasks

1. 记录当前右栏 / Inspector / 笔记现状及 Product/Spec dependency gate。
2. 先写 RED tests：右栏可隐藏且重开恢复上下文；Notes 区分 SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE；Current Material 来自 canonical Workspace refs；跨 Workspace fail closed；无全局 note 库。
3. 建立右栏 hide/show（Control，`aria-expanded`）与 V1 tabs（Learning Notes / Current Material）。
4. Notes 接入 durable UserNote query / autosave / conflict / recovery（若 owner 冻结；否则 `BLOCKED_BY_SPEC_GAP`）。
5. Current Material 接入 citation / "view source"，缺失 SourceSpan 诚实显示不可用。
6. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC070-AC-001`：适用 `UI-SN-AC-003/011`、`UI-LRN-AC-007..010` PASS；
- `EXEC070-AC-002`：右栏可隐藏且重开恢复上下文，无静默数据丢失；
- `EXEC070-AC-003`：Notes 区分 SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE；
- `EXEC070-AC-004`：Current Material / SourceSpan 来自 canonical Workspace refs，跨 Workspace fail closed；
- `EXEC070-AC-005`：无 generic "+" extension host；deferred candidates 不建 placeholder tab；
- `EXEC070-AC-006`：无 owner command / schema / migration change；未冻结的 UserNote / Material ref 标记 `BLOCKED_BY_SPEC_GAP`；
- `EXEC070-AC-007`：Product Acceptance / UX Contract / Engineering Gate 分开报告。

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

至少提供：right rail hide/show、Notes autosave/conflict/recovery、Material tabs、SourceSpan missing、cross-Workspace fail-closed、keyboard/touch/focus 证据。

## Completion Report Format

报告：修改文件、Product/Spec dependency gate、right rail 状态矩阵、Notes 状态矩阵、Material tab / SourceSpan 证据、cross-Workspace fail-closed、SPEC GAP（若 owner 未冻结）、gates、commit。