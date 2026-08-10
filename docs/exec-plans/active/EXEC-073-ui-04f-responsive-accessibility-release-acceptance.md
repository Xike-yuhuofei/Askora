# EXEC-073 — UI-04F Responsive / Accessibility / Release Acceptance

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UX Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0018, `UXA-SCREEN-200..203`, `UXA-COMP-075..079`, `UXA-QUAL-*`, UI-04 Vertical Slice  
> Depends on: `EXEC-072 DONE`

## Objective

完成 UI-04 的响应式、可访问性与 release acceptance：1440×900 / 1024×768 / 768×1024 / 360×800 与 200% zoom 下主任务可完成且无页面横向滚动；keyboard / touch / screen reader 可操作三栏与 Drawer，focus 返回触发点；no critical nested scroll；no silent data loss。

## Dependency Gate

- `EXEC-072 DONE`；
- `UXA-QUAL-*` gates 可执行；
- 无其他 active EXEC 修改 UI-04 Allowed Files。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0018
- `UXA-SCREEN-200..203`、`UXA-COMP-075..079`、`UXA-QUAL-*`
- UI-04 Vertical Slice

## Current Reality

UI-04 的三栏 shell / Drawer / right rail / de-management / no-OCR 已由 EXEC-068..072 完成；本 EXEC 负责全链验收与 release evidence。

## Allowed Files

```text
apps/frontend/src/**                    # only responsive/a11y/release fixes within UI-04 scope
apps/frontend/src/test/**
docs/exec-plans/active/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md
docs/exec-plans/completed/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
docs/releases/ux-workspace-context.md    # new release evidence
```

## Forbidden Changes

- 新增未冻结的 owner command / schema / migration；
- 用 UI 测试声称真人学习效果；
- 隐藏 error / citation / help / validation obligation 换取响应式简洁；
- 修改 Teaching Policy / mastery / review 算法；
- 顺带清理无关技术债。

## Implementation Tasks

1. 记录 1440/1024/768/360 与 200% zoom 响应式 baseline。
2. 先写 RED tests：breakpoints 主任务可完成；无页面横向滚动；右栏/Drawer 窄屏为可访问 sheet；focus return；no critical nested scroll；no silent data loss。
3. 修复响应式 / 可访问性 / focus 回归。
4. 运行全量 gates 并产出 release evidence（`docs/releases/ux-workspace-context.md`）。
5. 独立 commit；归档 UI-04 全部 EXEC。

## Acceptance Criteria

- `EXEC073-AC-001`：适用的 `UXA04-AC-012..015` 全部 PASS；
- `EXEC073-AC-002`：1440/1024/768/360 与 200% zoom 下主任务可完成且无页面横向滚动；
- `EXEC073-AC-003`：keyboard/touch/screen reader 可操作三栏与 Drawer，focus 返回触发点；
- `EXEC073-AC-004`：no critical nested scroll、no silent data loss；
- `EXEC073-AC-005`：frontend unit/integration/E2E/build/audit/docs/diff gates PASS；
- `EXEC073-AC-006`：Engineering / Contract / Accessibility 与 Learning Evidence 分开报告；不声称真人学习效果。

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