# EXEC-045 — UI-03C Library Progressive Disclosure

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 Interaction Architecture  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0014, `UI-IES-*`, `UI-SCREEN-090..095`, `UI-VIS-090..091`, UI-03 Vertical Slice  
> Depends on: `EXEC-044 DONE`

## Objective

在不改变 P1-04A/B/C 资料管理、去重、metadata、安全和 owner command semantics 的前提下，把 `/library` 从 always-visible management console 收敛为 **当前 Workspace 内的 Material 管理与知识上下文界面**：

```text
Current Workspace
→ Search / Filter / Import
→ Material List
→ Selected Material / Knowledge Context
→ Contextual Actions
```

批量动作只在 selection 后出现；duplicate、metadata、reinspection 等 advanced actions 按对象上下文暴露。

本 EXEC 不得把 Library 演进成跨 Workspace Global Material Library，也不得把 Material 错误建模为 Project 的从属实体。Material 必须属于 Workspace，与 Learning Project 保持多对多关系；用户可以直接基于 Material 开始学习。

OCR 不属于 Askora v1 核心能力。若仓库已有 OCR 兼容能力，可保留其非核心/兼容入口，但 **OCR 不得成为 UI-03/v1 release Required Acceptance**；扫描 PDF 允许被识别为无法可靠提取文本或 partial/unsupported，而不是为了通过本 EXEC 新建完整 OCR Pipeline。

## Dependency Gate

- EXEC-044 DONE；
- Library P1-04 tests 当前绿色；
- 无其他 active EXEC 修改 Library files。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Product Positioning

必须读取 `docs/product/PRODUCT-POSITIONING.md`，至少核对：

- Material 必须归属于 Workspace；
- Material 与 Learning Project 是多对多关系；
- 从 Project 移除 Material 只解除关系，不删除 Material 本体；
- v1 不建设跨 Workspace Global Material Library；
- Import = ingest + copy，原始资料进入 Askora 管理的数据目录；
- v1 核心格式为 EPUB / PDF / Markdown / TXT；
- v1 不建设完整 OCR Pipeline；
- Detect duplicate，不强制 Deduplicate；
- processing / partial / failed 等 pipeline 状态必须诚实呈现。

如现有 UI Spec / P1-04 文档要求“完整 OCR 是 v1 Required”或“Library 默认跨 Workspace”，必须返回 `BLOCKED_BY_SPEC_GAP`，不得以下位文档突破 Product Positioning。

## Required Specs

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0014
- `UI-IES-*`
- `UI-SCREEN-090..095`
- `UI-VIS-090..091`
- `UI-QUAL-*`
- UI-03 Vertical Slice
- SYS01 Library Management / P1-04A/B/C specs
- recovery/security contracts relevant to Material operations

## Current Reality

当前 `Library.jsx` 同屏永久展示 search/filter、上传、批量标签/集合/归档、新建标签/集合、duplicate review、document list、OCR/metadata/knowledge context 等大量 controls。能力本身多数有效，但 discoverability hierarchy 过度展开。

当前实现与文档还残留较强的 `Document` / management-console 视角；本 EXEC 的 UI 可以继续复用现有 document API/组件命名，但产品语义必须收敛为 Workspace-scoped Material。不得为了术语整洁在本 EXEC 改 backend schema，也不得把已有 OCR 能力升级为 v1 核心承诺。

## Allowed Files

```text
apps/frontend/src/pages/Library.jsx
apps/frontend/src/pages/Library.css
apps/frontend/src/components/**Library**                    # new/refactor only if Library-specific
apps/frontend/src/test/**Library**
apps/frontend/src/test/**library**
docs/exec-plans/active/EXEC-045-ui-03c-library-progressive-disclosure.md
docs/exec-plans/completed/EXEC-045-ui-03c-library-progressive-disclosure.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

## Forbidden Changes

- document/material library backend API or schema changes；
- P1-04 command semantics、idempotency、version/conflict changes；
- duplicate auto-merge 或强制 deduplicate；
- reinspection security weakening；
- removal of keyboard/touch access to contextual actions；
- hiding processing/error/quarantine/partial status for visual quietness；
- 建立跨 Workspace Global Material Library / default global search；
- 把 Workspace 建模为 Tenant / Organization；
- 把 Material 变成只能从 Project 访问的子对象；
- 从 Project 移除 Material 时删除 Material 本体；
- 为本 EXEC 新建完整 OCR / layout / table / formula / vision pipeline；
- 把已有 OCR compatibility failure 作为 v1/UI-03 release blocker，除非当前 Frozen Spec 明确要求且已完成 Product Positioning reconciliation。

## Implementation Tasks

1. 记录 current Library states、P1-04 targeted tests、DOM baseline 与当前 Workspace scope 行为。
2. 先写 RED tests：no selection → no batch toolbar；selection → contextual batch actions；selected Material → advanced actions discoverable；keyboard/touch equivalent；Workspace isolation；no global-library fallback。
3. 保留当前 Workspace 下的 Search/Filter/Import 作为默认高可见能力。
4. Material collection 使用 row/list hierarchy；selection 与 open/select semantics 清晰分离。UI 文案优先使用 Material/资料语义；backend `document` 命名若仍存在，仅作为实现兼容细节。
5. 把 tag/collection/archive batch actions 放入 selection contextual toolbar/surface。
6. 把 duplicate/metadata/reinspection/destructive actions 放到适当 Material context / inspector / disclosure / menu；不得删除真实能力。
7. OCR：若现有能力仍合法存在，仅放入兼容/advanced context；扫描 PDF 无可靠文本时允许明确显示 unsupported/partial。不得新增 OCR 核心承诺，也不得要求 OCR PASS 才完成本 EXEC。
8. 保留 processing/knowledge/source status 的诚实呈现，至少不掩盖 pending/processing/ready/partial/failed 等当前真实状态。
9. 验证所有 list/search/filter/selection/action 均受当前 Workspace scope 约束；切换 Workspace 后不得泄漏前一 Workspace 的 Material selection/result。
10. 保持 Material 独立于 Project 的产品语义；若 UI 显示 Project 关系，只能表达关联，不得表现为 Material owner 或访问门禁。
11. 验证从 Project 移除与删除 Material 的 UI 意图不混淆；若本 EXEC 页面不拥有该 command，则至少不得引入错误 copy/interaction。
12. 验证 360/768/1024/1440、200% zoom、keyboard/touch-equivalent path。
13. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC045-AC-001`：适用的 `UI03-AC-008..009,014` PASS；如其中存在与 Product Positioning 冲突的 OCR/global-library 旧要求，必须先报告 SPEC GAP，而不是执行旧要求。
- `EXEC045-AC-002`：无 selection 时不显示永久 batch management primary panel。
- `EXEC045-AC-003`：selection 后 tag/collection/archive 等 batch action 可发现且功能与 P1-04 baseline 等价。
- `EXEC045-AC-004`：duplicate/metadata/reinspection 在正确 Material context 可发现，不依赖 hover-only。
- `EXEC045-AC-005`：quarantine/rejected/processing/partial/error/source semantics 无回归。
- `EXEC045-AC-006`：Material / SourceFile / Knowledge Context distinction 无回归；Chunk/derived knowledge 不被表现为 Material 本体。
- `EXEC045-AC-007`：无 backend/public schema change。
- `EXEC045-AC-008`：Library 默认只显示/搜索当前 Workspace 的 Material，不建立跨 Workspace Global Material Library。
- `EXEC045-AC-009`：Material 不以 Learning Project 为 owner；Project 不是访问/开始学习 Material 的门禁。
- `EXEC045-AC-010`：已有 OCR 若保留仅属 compatibility/advanced capability；完整 OCR 不属于本 EXEC/v1 Required release gate。
- `EXEC045-AC-011`：duplicate 行为遵守 Detect duplicate / user decision，不新增强制自动合并。

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

若现有 P1-04 backend integration tests 是 frontend behavior 的必要回归证据，应只运行 targeted tests，不修改 backend。

至少提供：default vs contextual actions、Workspace isolation、no-global-library、Material/Project boundary、duplicate semantics、processing/partial states、responsive/keyboard/touch evidence。OCR compatibility tests 仅在现有实现仍保留该能力时运行，不得成为 v1 Required Gate。

## Completion Report Format

报告：修改文件、default vs contextual action matrix、Workspace scope evidence、Material/Project boundary、OCR disposition、P1-04 regression evidence、responsive/keyboard/touch evidence、UI03/EXEC AC、gates、commit、SPEC GAP。
