# 06 — UI Patterns Mining（UIKit）

**Phase**: 1 · **Generated**: 2026-08-12 · **Evidence**: `ui_kits/*/index.html` 全量实读 [L]

目标：提取**设计模式**，不是复制 UIKit 页面。

---

## 桌面式外壳的两种模式

### A. 自由形式 Desktop 工作台（dev-explorer）—— 最接近产品目标

```
.solo-home-shell (flex, max 1680px, height 960px, radius-8, border)
├── aside.task-list-panel (fixed ~300px)
│   ├── .topbar (h64): traffic lights + actions(32px icon btn)
│   ├── .mode-switch (Work/Code/Design 分段控件 + 滑动指示条)
│   ├── .quick-actions (New Task / Skills / Automation, 行高34)
│   ├── .content (滚动): Pinned + Task List(cluster→task-row)
│   └── .user-row (h56): avatar + name + Free tag
└── main.solo-home-main (白色画布)
    ├── corner-action (Toggle right panel)
    ├── title (WORK WITH TRAE 标题)
    ├── div[data-mode]  .solo-chatbox
    │   ├── prompt composer (slashes 命令 / attach / plugins / model 下拉 / voice / send)
    │   └── runtime source (Local / Solo workspace)
    └── suggestions (Web Reading / Research / Data Mining / Content Creation)
```

**关键**：`previewClassReuseRate 0.01`，全自定义语义类（solo-*/task-*/cluster-*），**无 `.ds-*` 复用**。图标用 `data-asset-icon` 外链占位。

### B. 栅格控制台（dashboard / dashboard-2 / settings）

```
.app-shell
├── aside.sidebar
│   ├── .brand
│   ├── .sidebar__section (title + nav-item×N, is-active 高亮)
│   └── .sidebar__footer
└── .workspace
    ├── header.topbar (mobile menu / global actions icon btns / user-menu)
    └── main.main
        ├── .page-header (title + toolbar)
        └── section.grid (span-3..12 十二栅格 + ds-card)
```

- settings：`.settings` grid = `260px minmax(0,1fr)`，侧栏导航 + 右表单/表格；表单控件高 32px；`<820px` 侧栏变顶栏。
- dashboard 用 `nav-item--active`，tabs 用 `aria-selected`。

## 提取的设计模式（供 Desktop Shell 复用）

| Pattern | 结构要点 | 来源 | 复用等级 |
|---|---|---|---|
| Sidebar | `sidebar__section`(title) + `nav-item`(icon+label+count) + active 态 | dashboard/settings | High |
| Mode Switcher | 分段控件 Work/Code/Design + 滑动指示 | dev-explorer | High |
| Task Tree | cluster → task-row，pin-slot + title + status + actions | dev-explorer | High |
| Topbar | 全局 actions 图标按钮 + divider + user-menu | dashboard | Medium |
| Prompt Composer | textarea + control-row + model dropdown + send | dev-explorer | High |
| Settings 双栏 | 260px 导航 + field-grid 表单 + ds-table-card | settings | Medium |
| Quick Actions | 34px 行图标动作（New Task/Skills/Automation） | dev-explorer | High |
| User Row | avatar + name + badge(tag) | dev-explorer | High |

## 组件复用证据（quality-report）

| ui_kit | reuseRate | basis | core components |
|---|---|---|---|
| dev-explorer | 0.01 | semantic-fallback | (无 .ds-*) |
| dashboard | 0.16 | ds-class | buttons, cards, progress, tag |
| dashboard-2 | 0.18 | ds-class | buttons, cards, progress, tag |
| settings | 0.23 | ds-class | alert, buttons, forms, tag |
| skills-library | 0.31 | ds-class | buttons, cards, forms, tag |
| landing | 0.31 | ds-class | buttons, cards, tag |
| 其他 doc | 0.01~0.17 | ds-class | 文档页 |

> html-effectiveness-doc 的 quality-report 声明 ds-class 但标记实测 0 个 `.ds-*`，属不一致，记录。[U]

## 结论

1. [L] **dev-explorer 是 App Shell 结构的最强参考**，但因其 0.01 复用率 + semantic-fallback，只能提取结构模式，不能作为 Figma 直接组件来源。
2. [L] **.ds-* 组件库**（btn/card/tag/table/avatar/progress/alert/input/select/switch）是共享语义基础，9/10 页面复用。
3. [L] 交互激活标准：`is-active` / `--active` / `aria-selected`，页面共用 `#traework-interaction-root` 脚本。
4. [I] 图标机制双轨：内联 SVG（icon--16） vs 外链 `data-asset-icon`。
