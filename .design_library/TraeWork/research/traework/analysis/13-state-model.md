# 13 — State Model

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: Component contracts states [L]

---

## 状态分类

### Global Component States（通用，跨组件）

| 状态 | Token/表现 | 来源组件 |
|---|---|---|
| default | 基础色 | 全部 |
| hover | bg-overlay-l1 / text-hover | buttons, menu, nav |
| pressed/active | bg-overlay-l2/l3 / active 色 | buttons |
| focused | border-brand / focus ring | forms, ai-input |
| selected | --active 类 | nav-item, tabs, task-tree |
| disabled | text-disabled / bg-invert-disabled / opacity | buttons, forms |
| loading | skeleton / progress | buttons, ai-input |

### Agent-specific States（组件/场景专属）

| 状态 | 组件 |
|---|---|
| empty | skeleton 占位 |
| typing | ai-input（textarea 自适应） |
| expanded | ai-input（max 300px） |
| running/submitting | ai-input loading |
| dirty/saved | code-editor |
| search-active | code-editor |
| split-view / zen-mode | code-editor |
| completed/current/pending | task-tree |
| favorite-active | card-template |

## 状态归属判定

| 归属 | 状态 | 依据 |
|---|---|---|
| Global Component State | default/hover/pressed/focused/selected/disabled/loading | 跨组件契约一致出现 [L] |
| Agent-specific State | typing/expanded/running/dirty/saved/completed/current/pending/split/zen/favorite | 仅特定组件契约定义 [L] |

## 视觉映射建议（Phase 2）

- Global 态 → 组件变体（Figma Variant）系统化
- Agent-specific → 属性/组件属性（Component Properties）

## 结论

1. [C][L] 7 个通用状态有 token 级证据。
2. [C][L] 11+ 个 Agent-specific 状态按组件隔离建模。
3. [I] Figma 用 Variant（global）+ Component Property（specific）双轨表达。
