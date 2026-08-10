# EXEC-045 — UI-03C Library Progressive Disclosure

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 Interaction Architecture  
> Governing: ADR-0014, `UI-IES-*`, `UI-SCREEN-090..095`, `UI-VIS-090..091`, UI-03 Vertical Slice  
> Depends on: `EXEC-044 DONE`

## Objective

在不改变 P1-04A/B/C 资料管理、去重、OCR、reinspection、metadata、安全和 owner command semantics 的前提下，把 `/library` 从 always-visible management console 收敛为：

```text
Search / Filter / Import
→ Document List
→ Selected Document / Knowledge Context
→ Contextual Actions
```

批量动作只在 selection 后出现；OCR、duplicate、metadata advanced actions 等按对象上下文暴露。

## Dependency Gate

- EXEC-044 DONE；
- Library P1-04 tests 当前绿色；
- 无其他 active EXEC 修改 Library files。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Specs

- `AGENTS.md`
- ADR-0014
- `UI-IES-*`
- `UI-SCREEN-090..095`
- `UI-VIS-090..091`
- `UI-QUAL-*`
- UI-03 Vertical Slice
- SYS01 Library Management / P1-04A/B/C specs
- recovery/security contracts relevant to document operations

## Current Reality

当前 `Library.jsx` 同屏永久展示 search/filter、上传、批量标签/集合/归档、新建标签/集合、duplicate review、document list、OCR/metadata/knowledge context 等大量 controls。能力本身多数有效，但 discoverability hierarchy 过度展开。

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

- document/library backend API or schema changes；
- P1-04 command semantics、idempotency、version/conflict changes；
- OCR publish/review truth changes；
- duplicate auto-merge；
- reinspection security weakening；
- removal of keyboard/touch access to contextual actions；
- hiding processing/error/quarantine status for visual quietness。

## Implementation Tasks

1. 记录 current Library states、P1-04 targeted tests、DOM baseline。
2. 先写 RED tests：no selection → no batch toolbar；selection → contextual batch actions；selected document → advanced actions discoverable；keyboard/touch equivalent。
3. 保留 Search/Filter/Import 作为默认高可见能力。
4. Document collection 使用 row/list hierarchy；selection 与 open/select semantics 清晰分离。
5. 把 tag/collection/archive batch actions 放入 selection contextual toolbar/surface。
6. 把 duplicate/OCR/metadata/reinspection/destructive actions 放到适当 document context / inspector / disclosure / menu；不得删除真实能力。
7. 保留 processing/knowledge/source status 的诚实呈现。
8. 验证 selection 清除、分页/filter 后 selection consistency、pending operations 和 focus return。
9. 验证 360/768/1024/1440、200% zoom、keyboard/touch-equivalent path。
10. 运行 gates；独立 commit/归档。

## Acceptance Criteria

- `EXEC045-AC-001`：`UI03-AC-008..009,014` PASS。
- `EXEC045-AC-002`：无 selection 时不显示永久 batch management primary panel。
- `EXEC045-AC-003`：selection 后 tag/collection/archive 等 batch action 可发现且功能与 P1-04 baseline 等价。
- `EXEC045-AC-004`：OCR/duplicate/metadata/reinspection 在正确 object context 可发现，不依赖 hover-only。
- `EXEC045-AC-005`：quarantine/rejected/processing/error/source semantics 无回归。
- `EXEC045-AC-006`：document/knowledge distinction 无回归。
- `EXEC045-AC-007`：无 backend/public schema change。

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

## Completion Report Format

报告：修改文件、default vs contextual action matrix、P1-04 regression evidence、responsive/keyboard/touch evidence、UI03/EXEC AC、gates、commit、SPEC GAP。
