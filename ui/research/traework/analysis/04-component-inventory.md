# 04 — Component Inventory

**Phase**: 1 · **Generated**: 2026-08-12 · **Evidence**: `components/*.json` 全量实读 [L]

共 **20 个组件契约**。两类来源：
- **preview-contract**（14，medium）：由 preview HTML + components.css 推导，CSS 已入库。
- **reverse-engineered**（6，low）：由产品截图反推，CSS 待入库，均含 newTokensProposed。

---

## 总览表

| # | slug | name | category | 来源 | confidence | tokens | states | 图标资产 |
|---|---|---|---|---|---|---|---|---|
| 1 | alert | Notifications | feedback | preview-contract | medium | 37 | hover | 6 |
| 2 | avatar | Avatar | data-display | preview-contract | medium | 8 | — | 0 |
| 3 | breadcrumb | Breadcrumb | navigation | preview-contract | medium | 5 | hover | 1 |
| 4 | buttons | Button | action | preview-contract | medium | 48 | hover/active/disabled | 11 |
| 5 | cards | Card / List | layout | preview-contract | medium | 12 | — | 4 |
| 6 | dialog | Dialog / Modal | overlay | preview-contract | medium | 25 | hover/focus | 4 |
| 7 | forms | Form | input | preview-contract | medium | 30 | hover/focus/disabled/selected | 9 |
| 8 | menu | Menu | navigation | preview-contract | medium | 22 | hover | 9 |
| 9 | pagination | Pagination | navigation | preview-contract | medium | 16 | hover/active/disabled | 1 |
| 10 | progress | Progress / Slider | feedback | preview-contract | medium | 4 | — | 0 |
| 11 | skeleton | Skeleton | feedback | preview-contract | medium | 4 | — | 0 |
| 12 | table | Table | data-display | preview-contract | medium | 15 | — | 1 |
| 13 | tabs | Tabs | navigation | preview-contract | medium | 16 | hover/active | 0 |
| 14 | tag | Tag | feedback | preview-contract | medium | 16 | — | 0 |
| 15 | shell-three-panel | Three-Panel Shell | layout | reverse-engineered | low | 18 | 6 状态 | 9 |
| 16 | ai-input | AI Input Box | input | reverse-engineered | low | 28 | 6 状态 | 7 |
| 17 | task-tree | Task Hierarchy Tree | navigation | reverse-engineered | low | 24 | 7 状态 | 11 |
| 18 | status-bar | Status Bar | feedback | reverse-engineered | low | 21 | 3 状态 | 8 |
| 19 | card-template | Rich Template Card | layout | reverse-engineered | low | 23 | 3 状态 | 5 |
| 20 | code-editor | Code Editor | input | reverse-engineered | low | 42 | 8 状态 | 30 |

## 分类汇总

| 分类 | 组件 |
|---|---|
| feedback (5) | alert, progress, skeleton, tag, status-bar |
| navigation (5) | breadcrumb, menu, pagination, tabs, task-tree |
| input (3) | forms, ai-input, code-editor |
| layout (3) | cards, shell-three-panel, card-template |
| data-display (2) | avatar, table |
| action (1) | buttons |
| overlay (1) | dialog |

## 与 Code Welcome Screen 直接相关的组件（本轮重点）

### buttons（48 tokens）[L]
- 变体：`--primary/--secondary/--tertiary/--ghost/--link/--danger/--danger-strong/--warning/--icon/--sm/--md/--lg`
- 尺寸以修饰符 + icon-size token 表达，无显式 px（preview-contract 通病）
- 状态：hover/active/disabled
- 图标：add/check/close/copy/delete/download/settings 等 11 个

### ai-input（28 tokens，reverse-engineered）[L]
- **高优先级**：Prompt Composer 的核心输入组件
- 结构：`.ds-ai-input` = `__textarea` + `__control-row`
- 状态：idle/focused/typing/expanded/disabled/loading
- 尺寸规格（契约显式）：default-height ≈ **100px**（72px textarea + 28px control-row）；textarea min-height 72px（4 行）；send-btn **28×28 圆形**；radius **12px**；border `1px solid border-neutral-l1`
- newTokensProposed：`--ai-input-min-height(100px)`, `--ai-input-max-height(300px)`, `--ai-input-radius(12px)`, `--ai-input-shadow-focus`
- 图标：attachment/Down/Send/Plus/PaperPlane/Seed/Code

### task-tree（24 tokens，reverse-engineered）[L]
- 结构：`.ds-task-tree` = `__group(+__group-header/__group-title/__group-count)` + `__item(+__item-icon/__item-label/__item-status)` + `__chevron` + `__level-1/2/3`
- 状态：hover/selected/completed/current/pending/expanded/collapsed
- 尺寸规格：`level-indent` **16px/级**；`item-height` **28px**（padding 0 8px、radius 6px）；`group-title-height` 24px；`status-dot-size` 12px
- 三级嵌套：Workspace → Project → Task

### status-bar（21 tokens，reverse-engineered）[L]
- 结构：`.ds-status-bar` = `__left`(user/avatar/info/name/badge/credits) + `__right`(action/divider)
- 尺寸：**height 32px**，padding 0 12px；avatar 24px；action 28×28 radius 6px
- 底部 fixed 全宽条

### shell-three-panel（18 tokens，reverse-engineered）[L]
- 网格：`200px minmax(480px,1fr) 360px`，height 100vh
- left-panel 200px（折叠至 48px）；right-panel 360px（折叠至 0px）；center min 480px；min viewport 960px
- **这是 App Shell 布局的系统级参考**

### code-editor（42 tokens，reverse-engineered）[L]
- 状态：default/focused/dirty/saved/search-active/split-view/minimap-visible/zen-mode
- 结构：tab-bar(36px) → content → status-bar(24px)；gutter 20px；minimap 60px；font 13px/LH 20px
- 图标资产 30 个（全库最重）

## 关键观察

1. [L] **preview-contract 组件无显式 px 尺寸**，尺寸表达在 CSS 类/修饰符中；**reverse-engineered 组件有精确 px 规格**（shell/ai-input/task-tree/status-bar/card-template/code-editor）。
2. [L] token 消费密度：buttons(48) 与 code-editor(42) 最高；progress/skeleton(4) 最低。
3. [L] status-bar 引用非标准 `--brand-grey-700`，疑为待新增 token。[U]
4. [L] 6 个 reverse-engineered 组件合计提出 ~46 个 newTokensProposed，Phase 2 需收敛决策。
5. [L] `assets/icons/` 为唯一图标来源（contract 明示）。
