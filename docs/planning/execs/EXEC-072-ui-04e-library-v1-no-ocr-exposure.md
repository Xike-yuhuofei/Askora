# EXEC-072 — UI-04E Library v1 No-OCR Exposure

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UX Architecture  
> Product Traceability: `CAP-01`、`PD-REQ-0101..0104`、`PD-RULE-006/011`  
> Governing: `docs/product/PRODUCT-DEFINITION.md`, `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`, `docs/design/experience/LEARNING-EXPERIENCE.md`, `docs/specs/ui/screen-and-navigation-contracts.md`, `docs/specs/ui/design-system.md`, ADR-0018, UI-04 Vertical Slice  
> Depends on: `EXEC-071 DONE`

## Objective

Library v1 正常 UI 不得暴露 OCR。扫描 PDF 无可靠文本时诚实显示 `unsupported / partial extraction` 并建议受支持的文本型资料。历史/optional OCR runtime 是否保留由 current Product/Architecture contracts 决定，但正常 v1 UI 不可达。

## Dependency Gate

- `EXEC-071 DONE`；
- 无其他 active EXEC 修改 Library 相关 files。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- `docs/design/experience/LEARNING-EXPERIENCE.md`
- `docs/specs/ui/screen-and-navigation-contracts.md`（`UI-LIB-001..004`）
- `docs/specs/ui/design-system.md`
- ADR-0018
- UI-04 Vertical Slice

## Current Reality

执行起点必须重新读取 current `main` 检查 OCR UI reachability。历史 P1-04C release/optional runtime 只作为迁移事实，不构成 v1 normal UI capability。

## Allowed Files

```text
apps/frontend/src/pages/Library.jsx
apps/frontend/src/pages/Library.css
apps/frontend/src/components/**Library**            # only Library-specific UI exposure
apps/frontend/src/test/**Library**
apps/frontend/src/test/**library**
docs/planning/execs/EXEC-072-ui-04e-library-v1-no-ocr-exposure.md
docs/archive/exec-plans/EXEC-072-ui-04e-library-v1-no-ocr-exposure.md
docs/planning/README.md
docs/archive/exec-plans/README.md
```

## Forbidden Changes

- 扩展 OCR；
- 删除历史 OCR 数据 files（除非 current Product/Architecture cleanup 已批准并冻结）；
- 删除受支持文本型资料处理；
- 隐藏 processing/error/quarantine/partial status 换取视觉安静；
- 修改 backend OCR runtime / schema / migration / Teaching Policy。

## Implementation Tasks

1. 记录 current Library OCR 暴露点与 Product Definition v1 format boundary。
2. 先写 RED tests：Library 正常 UI 不暴露 OCR 入口/状态/candidate/review/confidence/bbox/hash 文案；扫描 PDF 诚实显示 unsupported/partial；不建 placeholder。
3. 移除正常 UI 的 OCR 暴露；扫描 PDF 显示 `unsupported / partial extraction` 与建议。
4. 历史 OCR runtime 若仍存在，确认其不在正常 v1 UI 可达路径。
5. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC072-AC-001`：`UI-SN-AC-006` 与适用 `UI-QR-*` PASS；
- `EXEC072-AC-002`：Library v1 正常 UI 不暴露 OCR 入口/状态/review/confidence/bbox/hash/核心能力文案；
- `EXEC072-AC-003`：扫描 PDF 诚实显示 unsupported/partial 并建议当前受支持文本型资料；
- `EXEC072-AC-004`：历史 OCR runtime 在正常 v1 UI 不可达；
- `EXEC072-AC-005`：受支持文本型资料处理与 processing/error/partial 状态无回归；
- `EXEC072-AC-006`：无 OCR 扩展 / schema / migration 删除；
- `EXEC072-AC-007`：UI no-OCR exposure 作为 Product Definition 的呈现落实，不被解释为 UI 自行改变 Product Scope。

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

至少提供：normal UI no-OCR、scanned-PDF unsupported/partial、runtime unreachable、supported text-type processing 无回归、keyboard/accessibility 证据。

## Completion Report Format

报告：修改文件、OCR exposure 移除矩阵、scanned-PDF disposition、runtime reachability、supported-type 回归、gates、commit。