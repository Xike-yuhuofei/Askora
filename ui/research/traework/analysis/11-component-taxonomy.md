# 11 — Component Taxonomy

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: Library contracts [L] + UIKit [L] + Screenshot [S]

---

## 分层体系

```
Primitive → Component → Composite → Pattern → Screen
```

### Primitive

| 类别 | 项 |
|---|---|
| Icon | `assets/icons/*.svg`（671，单色 currentColor） |
| Text | body-xs..lg / heading-3xs..display |
| Divider | border-neutral-l1 1px |
| Status Dot | 12px（task-tree） |

### Component（.ds-* 库）

| 分类 | 组件 |
|---|---|
| Action | Button（buttons） |
| Navigation | Tabs, Menu, Breadcrumb, Pagination, TaskTree |
| Input | Input/Select/Textarea/Switch/Search（forms）, AIInput, CodeEditor |
| Feedback | Alert, Progress, Skeleton, Tag, StatusBar |
| Data Display | Avatar, Table |
| Layout | Card/List |
| Overlay | Dialog/Drawer |

### Composite（App 专属组合）

| Composite | 组成 |
|---|---|
| ModeSwitcher | 分段控件（Work/Code/Design） |
| SidebarSection | section title + nav-items |
| SidebarAction | icon + label 行 |
| WorkspaceGroup | 可展开分组（task-tree __group） |
| TaskItem | task-row（icon+label+status） |
| PromptComposer | ai-input（editor+control-row） |
| QuickAction | 快捷动作行 |
| UserRow | avatar + name + badge |

### Pattern

| Pattern | 组成 |
|---|---|
| Sidebar | Window Controls + Global + ModeSwitcher + Navigation + Pinned + TaskList + Account |
| MainWorkspace | flex 区域 + 内容 surface |
| WorkspaceNavigation | 分组树 |

### Screen

| Screen | 组成 |
|---|---|
| CodeWelcomePage | App Shell + Hero + PromptComposer + QuickActions |

## 与库契约的对齐

- 契约分类（index.json）：feedback(5)/navigation(5)/input(3)/layout(3)/data-display(2)/action(1)/overlay(1)。
- 本次 taxonomy 新增 **Composite / Pattern / Screen** 三层，契约只覆盖到 Component 级。[I]
- reverse-engineered 组件（ai-input/task-tree/status-bar/shell/code-editor/card-template）天然是 Composite 候选。[L]

## 结论

1. [C][L] 基础组件层有 20 个契约，覆盖完备。
2. [C][I] App 级 Composite/Pattern/Screen 需在图谱中显式建模（Sidebar, PromptComposer, CodeWelcomePage）。
3. [I] Figma 构建时按 Primitive → Component → Composite → Pattern → Screen 顺序。
