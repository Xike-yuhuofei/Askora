# EXEC-073 — UI-04F Responsive / Accessibility / Release Acceptance

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UX Architecture  
> Product Traceability: `PD-NFR-005` + applicable `CAP-01/04/07/08` user paths  
> Governing: `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`, `docs/design/experience/LEARNING-EXPERIENCE.md`, `docs/design/experience/INTERACTION-MODEL.md`, `docs/specs/ui/screen-and-navigation-contracts.md`, `docs/specs/ui/learning-interaction-contracts.md`, `docs/specs/ui/design-system.md`, `docs/specs/ui/quality-and-regression.md`, ADR-0018, UI-04 Vertical Slice  
> Depends on: `EXEC-072 DONE`

## Objective

完成 UI-04 的响应式、可访问性与 release acceptance：1440×900 / 1024×768 / 768×1024 / 360×800 与 200% zoom 下主任务可完成且无页面横向滚动；keyboard / touch / screen reader 可操作核心 shell、Drawer 与 Right Rail，focus 返回合理位置；no critical nested scroll；no silent data loss。

## Dependency Gate

- `EXEC-072 DONE`；
- current `UI-QR-*` gates 可执行；
- 无其他 active EXEC 修改 UI-04 Allowed Files。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- `docs/design/experience/LEARNING-EXPERIENCE.md`
- `docs/design/experience/INTERACTION-MODEL.md`
- `docs/specs/ui/screen-and-navigation-contracts.md`（`UI-RESP-*`）
- `docs/specs/ui/learning-interaction-contracts.md`（`UI-LRN-130..132`）
- `docs/specs/ui/design-system.md`（`UI-DS-A11Y-*`）
- `docs/specs/ui/quality-and-regression.md`
- ADR-0018
- UI-04 Vertical Slice

## Current Reality

实时完成状态不得由本文件静态描述推断。执行起点必须读取 Linear + current `main` 确认 EXEC-068..072 的实际完成状态；本 EXEC 只在 dependency gate 满足后开始最终验收。

## Allowed Files

```text
apps/frontend/src/**                    # only responsive/a11y/release fixes within UI-04 scope
apps/frontend/src/test/**
docs/planning/execs/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md
docs/archive/exec-plans/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md
docs/planning/README.md
docs/archive/exec-plans/README.md
docs/archive/releases/ux-workspace-context.md    # new release evidence
```

## Forbidden Changes

- 新增未冻结的 owner command / schema / migration；
- 用 UI 测试声称真人学习效果；
- 隐藏 error / citation / help / validation obligation 换取响应式简洁；
- 修改 Teaching Policy / mastery / review 算法；
- 顺带清理无关技术债。

## Implementation Tasks

1. 记录 1440/1024/768/360 与 200% zoom 响应式 baseline。
2. 先写 RED tests：breakpoints 主任务可完成；无页面横向滚动；右栏/Drawer 窄屏为可访问替代 surface；focus return；no critical nested scroll；no silent data loss。
3. 修复响应式 / 可访问性 / focus 回归。
4. 运行全量 gates 并产出 release evidence（`docs/archive/releases/ux-workspace-context.md`）。
5. 独立 commit；归档 UI-04 全部 EXEC。

## Acceptance Criteria

- `EXEC073-AC-001`：适用 `UI-SN-AC-009..011`、`UI-LRN-AC-012`、`UI-DS-AC-005..007`、`UI-QR-AC-001..008` PASS；
- `EXEC073-AC-002`：1440/1024/768/360 与 200% zoom 下主任务可完成且无页面横向滚动；
- `EXEC073-AC-003`：keyboard/touch/screen reader 可操作核心 shell、Drawer、Right Rail 与 Material tabs，focus 返回合理位置；
- `EXEC073-AC-004`：no critical nested scroll、no silent data loss；
- `EXEC073-AC-005`：frontend unit/integration/E2E/build/audit/docs/diff gates PASS；
- `EXEC073-AC-006`：Product Acceptance / UX Contract / Engineering / Accessibility / Learning Evidence 分开报告；不声称真人学习效果。

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

至少提供：breakpoint 矩阵、200% zoom、keyboard-only primary path、focus order/return、screen reader、no-horizontal-scroll、no-critical-nested-scroll、no-silent-data-loss、E2E 证据。

## Completion Report Format

报告：修改文件、breakpoint 矩阵、a11y 证据、no-scroll/no-data-loss 证据、release evidence、gates、commit、UI-04 归档状态。