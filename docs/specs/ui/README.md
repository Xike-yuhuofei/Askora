# Askora UI Specification Set

> 状态：**Canonical UI/UX Implementation Contract Index — Current Only**  
> 校准日期：2026-08-11  
> 上游产品定义：`docs/product/PRODUCT-DEFINITION.md`  
> Governing Experience：`docs/design/experience/EXPERIENCE-ARCHITECTURE.md`、`LEARNING-EXPERIENCE.md`、`INTERACTION-MODEL.md`  
> Governing ADR：ADR-0014、ADR-0015、ADR-0018、ADR-0019

---

## 1. Purpose

本目录回答：

> **已经由 Product Definition 冻结的能力，用户具体如何看到、导航、理解和操作，以及 UI 如何被实现与验收。**

UI Specs 不拥有 Product Capability、v1 Feature inclusion、Product Rule、Teaching Policy、domain ownership 或 Product Acceptance。

正式职责边界：

```text
Product Definition = WHAT
Experience Design  = HOW USER USES IT / stable experience model
UI / UX Spec       = WHAT THE INTERFACE MUST IMPLEMENT
Technical Spec     = HOW DATA / SOFTWARE INTERFACES WORK
```

---

## 2. Current Canonical UI Contracts

当前 UI/UX 实现只需以以下 4 份长期合同为主：

1. [`screen-and-navigation-contracts.md`](screen-and-navigation-contracts.md)  
   user-facing IA、Navigation、routes、shell、Today/Learning/Library/Settings/Welcome、responsive screen rules。

2. [`learning-interaction-contracts.md`](learning-interaction-contracts.md)  
   Learning Canvas、Question/Attempt/Feedback/Hint/Remediation、streaming、assistance、citation、SourceSpan、UserNote、Context Drawer、long-session interaction。

3. [`design-system.md`](design-system.md)  
   semantic tokens、typography、spacing、components、states、patterns、motion、visual accessibility。

4. [`quality-and-regression.md`](quality-and-regression.md)  
   semantic regression、responsive、keyboard/a11y、Workspace isolation、security、UX acceptance 与 completion claim boundary。

UI read-model / query / ownership contract 已移到技术层：

- [`../frontend/ui-read-model-contracts.md`](../frontend/ui-read-model-contracts.md)

它继续保留原 `UI-DATA-* / UXA-DATA-*` 精确技术条款，但不再属于 Experience Design Authority。

---

## 3. Product Definition Traceability

主要映射：

| UI Area | Product Definition Trace |
|---|---|
| Workspace / Material / Notes | `CAP-01`、`CAP-07`、`PD-REQ-0101..0104`、`PD-RULE-006/009/011` |
| Goal / Plan / Next Activity | `CAP-02`、`CAP-03`、`CAP-07`、`PD-REQ-0201..0303` |
| Learning Canvas / Attempt / Feedback | `CAP-04`、`CAP-05`、`PD-REQ-0401..0503` |
| Review / validation / continuity | `CAP-06`、`CAP-07`、`PD-REQ-0601..0703` |
| Local data / BYOK / Recovery | `CAP-08`、`PD-REQ-0801..0804`、`PD-RULE-008/010/011` |
| Accessibility / usability | `PD-NFR-005` |

新建或实质重构 UI Contract / Vertical Slice / EXEC 必须引用适用 Product Definition；如果 Product Definition 缺失，报告 `PRODUCT DEFINITION GAP`。

---

## 4. Current Experience Invariants

当前实现不得突破：

1. L0 Product Domains 只有：

```text
今天 / 学习 / 资料库
```

2. Settings / Recovery 是 App Utility。
3. Chat/Tutor 是 LearningActivity interaction mode，不是 Product Domain。
4. Learning 不再暴露 Goal / Plan / Progress / History 常驻管理中心；domain truth 保留并按明确 user job contextually expose。
5. Today 有可靠 canonical activity 时只允许一个 Primary Learning Task。
6. Workspace 是 Left / Center / Right / Drawer 共享的 canonical context。
7. Center 是唯一 Primary Learning Canvas。
8. Right Rail v1 只允许 User-authored Learning Notes + Current Material / Source Context。
9. Context Drawer 默认收起，只呈现 stage / stage goal / next 1..3。
10. Library v1 normal UI 不暴露 OCR；deferred candidates 不建立 placeholder。
11. 7 semantic interaction primitives 保持：Navigation / Action / Control / Selection / Disclosure / InteractiveContent / StatusFeedback。
12. UI 不得通过 frontend-only state 改写 Workspace、Plan、Evidence、TeachingAction、UserNote 等 canonical truth。

---

## 5. Authority Chain

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ Learning / Domain Canonical Design
→ Current Experience Canonical Design
→ Accepted ADR
→ Current UI/UX Contracts（本目录）
→ Frontend / Interface Technical Specs
→ Vertical Slice / Linear / EXEC
→ Code / Tests
```

冲突处理：

- Product Definition ↔ Experience/UI：`DESIGN–DEFINITION GAP`；
- Experience ↔ UI Spec：`SPEC GAP`；
- UI Spec ↔ technical owner/security contract：`SPEC GAP`；
- current UI Contract ↔ code：`DESIGN–IMPLEMENTATION GAP` / implementation drift。

下游不得自行选择冲突的一套 truth。

---

## 6. Historical UI Contract Set

以下文件继续保留为**历史/迁移参考**，不再作为新实现 current Authority：

- `interactive-element-system.md`
- `information-architecture.md`
- `screen-contracts.md`
- `visual-system.md`
- `component-state-contracts.md`
- `quality-and-migration.md`
- `data-contracts.md`

这些文件记录 ADR-0014 → ADR-0018 / UI-03 → UI-04 的演进，并包含 supersession matrices、旧 route/facet、一次性 migration 与历史 EXEC 语境。

新的 implementation task **不得**要求 Agent 通过这些文件中的旧条款 + Supersession Matrix 自行推导 current truth。

如需追踪历史 clause ID（`UI-*` / `UXA-*`），可以读取历史文件或 Vertical Slice；当前行为必须最终回到本 README 所列 current contracts。

---

## 7. Technical UI Read Model Boundary

`docs/specs/frontend/ui-read-model-contracts.md` 管理：

- UI read-model aggregation；
- source/version/freshness；
- query / endpoint contract；
- frontend no-owner rule；
- current Workspace / Drawer / Goal / Path / Evidence 等技术 projection；
- compatibility data boundary。

Experience/UI Spec 只决定“哪些事实必须被用户理解、如何呈现”，不定义第二份 API/owner truth。

---

## 8. Design System Boundary

Design System 管理：

```text
Token
Typography
Spacing
Component
State
Pattern
Visual Accessibility
```

不管理：

```text
Product Capability
IA
Navigation Decision
Screen Responsibility
Learning Flow
Domain State
```

`.design_library/Askora/**` 是 supporting asset；frontend code 是 implementation。二者都不是第二 Design System Authority。

---

## 9. Quality / Acceptance Boundary

必须分开报告：

```text
Product Acceptance
UX Acceptance
UI Engineering / Contract Acceptance
Accessibility / Security Acceptance
Learning Evidence
```

UI/UX PASS 不得自动升级为 Product Acceptance，也不得声称 retention / transfer / mastery 已改善。

---

## 10. Working Rule

> **新实现只读取 current Product / Experience / UI Contracts；历史 Delta、旧 UI Spec 和 Migration Matrix 用来解释过去，不再要求 Codex 从历史冲突中推断现在。**
