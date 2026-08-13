# 17 — Figma Build Spec（Phase 1 规划）

**Phase**: 1 · **Generated**: 2026-08-12
**状态**: 规划文档。按用户确认，Phase 1 不实际创建 Figma 资产，此文档作为 Phase 2 Figma 构建规格。

---

## Figma 文件

- **文件名**: `TraeWork Reverse Engineering`
- 目标：先 FigJam 架构（Phase 2 前半）→ 再 Figma Design File（Phase 2 后半）。
- 当前只构建 **Code Welcome Screen / Light Mode**，不复刻整个 TraeWork。

## Pages（13）

| # | Page | 内容 |
|---|---|---|
| 00 | Cover | 封面 |
| 01 | Sources | 截图 + 素材证据 |
| 02 | Foundations | Tokens（Variables） |
| 03 | Icons | Icon Components |
| 04 | Components | Base 组件 |
| 05 | Composite Components | ModeSwitcher / PromptComposer 等 |
| 06 | Patterns | Sidebar / Workspace |
| 07 | App Shell | 应用外壳 |
| 08 | Code Mode | Code Welcome 专属 |
| 09 | Screens | CodeWelcomePage |
| 10 | Prototype | 交互原型 |
| 11 | Validation | Pixel Validation |
| 99 | Archive | 归档 |

## Variables 三层

### Core（Primitive）
- 原始色板（brand ramp / grey ramp / accent）
- Spacing（spacer-0..64）
- Radius（radius-0..full）
- Size（icon-size / border-width）

### Semantic
- Background / Surface / Text / Icon / Border / Brand / Status
- Typography（body/heading/code）
- 结构上允许未来加 Dark Mode（不硬编码进组件）

### Component
- Button / Input / Sidebar / Tab / Composer 专属 token

> 当前只需 Light Mode，但组件不得硬编码颜色，须消费 Semantic Variable。[文档第三十节]

## Typography

| 组 | 来源 |
|---|---|
| Body | body-xs..lg |
| Heading | heading-3xs..display |
| Code Editor | code-editor 13px |
| Terminal | code-terminal 12px |
| Label | body-sm/md strong |

> 字体缺失检查：SF Pro / JetBrains Mono 若 Mac 无 → 记录 Font Missing，不静默替换。[U]

## Icon 策略

- 导入原始 SVG（`assets/icons/`）
- Icon Component + Instance Swap
- 分类组织，不全铺一页
- 第一阶段只导当前 Screenshot 实际使用的图标

## Component Architecture（推荐）

```
Primitive: Icon, Divider
Base: Button, IconButton, Input, Tab, ListItem, TreeItem, SectionHeader, Tooltip
Composite: ModeSwitcher, SidebarAction, SidebarSection, WorkspaceGroup, TaskItem, PromptComposer, QuickAction
Pattern: Sidebar, MainWorkspace
Screen: CodeWelcomePage
```

实际结构结合现有 Component Contract 调整。

## Auto Layout 规则

- 优先 Auto Layout / Fill / Hug / Min-Max / Variables / Variants / Component Properties / Instance Swap
- 禁止：大量独立 Frame、复制组件、绝对定位、Detached Instance

## 屏幕重建目标

**TraeWork → Code Mode → Welcome Page → Light Mode**

通过此 Screen 验证：Tokens、Components、App Shell、Sidebar、Prompt Composer、Spacing、Typography、Icon System。

## 验证流程

1. 按原截图 2291×1299 导出
2. Reference vs Reconstruction Overlay
3. 检查：Sidebar Boundary / Workspace / Background / Border / Radius / Typography / Icon Alignment / Composer / Quick Actions / Spacing / Center Position
4. 输出 `analysis/15-visual-validation.md` 记录 Delta 与 Cause

## MCP 可用性

- `figma-mcp-rust`：Connected ✅
- `open-figma-mcp`：Connected ✅
- Phase 2 可用其创建实际资产；若无写权限则只输出 Build Spec（本文件已可充当）。

## 验收

- Variables 三层结构齐备，Light Mode 可用。
- 组件全部 Auto Layout + 消费 Variable。
- CodeWelcomePage 像素级对齐（Design System Consistency + High Fidelity，非逐像素机械一致）。
