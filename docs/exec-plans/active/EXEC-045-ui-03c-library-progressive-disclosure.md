# EXEC-045 — UI-03C Library Progressive Disclosure

> Status: **SUPERSEDED / DO NOT EXECUTE**  
> Superseded on: 2026-08-11  
> Replacement: `EXEC-072-ui-04e-library-v1-no-ocr-exposure.md` + current UI contracts  
> Reason: ADR-0018 / current Product Definition / Experience consolidation superseded the UI-03 Library exposure model.

## Disposition

本 EXEC 不再是可执行合同。

其仍有效的设计意图已经被 current contracts 吸收：

```text
Current Workspace
→ Import / Search / Filter
→ Material List
→ Selected Material Context
→ Contextual Actions
```

以及：

- repeated Material 优先 row/list；
- batch actions 只在 selection/context 下出现；
- duplicate / metadata / destructive operations 不长期占据主层级；
- processing / partial / failed / source 状态必须诚实；
- Material 必须服从 Workspace scope；
- 不建立跨 Workspace Global Library。

当前 Authority：

- `docs/product/PRODUCT-DEFINITION.md` — `CAP-01` / Material scope / v1 formats；
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`；
- `docs/design/experience/LEARNING-EXPERIENCE.md`；
- `docs/specs/ui/screen-and-navigation-contracts.md` — `UI-LIB-001..004`；
- `docs/specs/ui/design-system.md`；
- `docs/specs/ui/quality-and-regression.md`；
- `EXEC-072` — current Library v1 exposure implementation task。

## Why Superseded Instead of Executed

原 EXEC-045 允许已有 OCR capability 继续以 compatibility / advanced context 暴露；当前 Product Definition + ADR-0018 + `UI-LIB-003` 已明确：

> **Library v1 normal UI 不暴露 OCR action/status/review。**

同时 `EXEC-072 / XIK-165` 已承担 current Library exposure 收口。如果继续先执行 045，再执行 072，会产生重复修改、重复验收和不必要返工。

因此：

```text
EXEC-044 DONE
→ EXEC-045 SUPERSEDED

Library current work
→ EXEC-072（服从其 UI-04 dependency chain）
```

## Historical Value

本文件保留用于解释 UI-03 → UI-04 的迁移历史。原完整 implementation tasks / AC 可从 Git history 追溯，但不得再交给 TraeCode / Codex 机械执行。

## Explicit Rule

- 不把本状态标记为 `DONE`；它是 **superseded**，不是完成证据。
- 不因 supersede 删除任何 Material / OCR runtime / domain data。
- 不创建新的替代 Issue；使用现有 `EXEC-072 / XIK-165`。
