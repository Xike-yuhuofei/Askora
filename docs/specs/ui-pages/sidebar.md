# 侧边栏（`Sidebar`，全局 shell 组件）

> **页面职责**：空间中心 IA 的一级导航与空间切换——「资料库」一级项、主按钮「空间管理」、分组标签「已有对话」、footer「设置」。仅在空间中心模式下呈现。Welcome 仍是 Default Destination（`EXP-IA-001`），由产品标识（logo）链接承接，不再单设一级导航项。
> **对应契约**：`EXP-IA-001`、`UI-NAV-001/002`、`UI-SHELL-001~005`
> **现状基准**：`apps/frontend/src/components/Sidebar.jsx`（已与空间中心 IA 一致：logo→Welcome/空间管理/已有对话/资料库/设置）

---

## 1. 页面目标

1. 一级导航只含「资料库」与「空间管理」，保持 IA 冻结（无「今天/学习/Chat」）。Welcome 作为 Default Destination 由 logo 链接（`/welcome`）承接，不单设导航项。
2. 「空间管理」按钮跳转到 `/spaces`，承载空间的创建、浏览、重命名与进入。
3. 「已有对话」分组列出最近空间，可切换、可继续；**无对话时整组隐藏**，不呈现空态占位区。
4. footer「设置」进入 Settings 对话框；RecoveryIndicator 反映待处理问题。

**不做什么**：不恢复被退役的导航项（学习/知识图谱/个人档案/Chat）；不恢复「欢迎」一级导航项与「已有对话」空态占位。

## 2. 布局区划

```
┌─────────────┐
│ ● Askora     │  ← logo 链接 → /welcome（Default Destination）
│ [空间管理 · primary 主按钮] │
├─────────────┤
│ 已有对话（有对话时才显示） │
│  · 空间 1  · 空间 2 │
│ [资料库 FolderOpen] │
├─────────────┤
│ {n} 个问题待处理   │
│ [设置]        │
└─────────────┘
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| SB-01 | 产品标识 | 文本/logo（链接→/welcome） | Askora | Navigation（Default Destination） | — | Brand | — |
| SB-02 | 空间管理 | 按钮（Plus） | 空间管理 | **Action**（→ /spaces，`EXP-IA-001`） | Primary | Button primary | DEFAULT/LOADING |
| SB-04 | 一级导航 | 链接 | 资料库（FolderOpen） | Navigation | — | NavItem | ACTIVE/DEFAULT |
| SB-05 | 分组标签 | 文本 | 已有对话 | — | — | label | 无对话时整组隐藏 |
| SB-06 | 对话行 | row | 空间标题 | InteractiveContent（切换空间） | — | Row | ACTIVE/DEFAULT/HOVER |
| SB-07 | 恢复指示 | 文本+icon | {n} 个问题待处理 | StatusFeedback | — | Badge+AlertTriangle | 0 隐藏；>0 显示 |
| SB-08 | 设置 | 链接 | 设置 | Navigation（→ Settings Dialog） | — | NavItem | DEFAULT |

> SB-03「欢迎」一级导航项与 SB-09「已有对话」空态占位已按用户决定移除：Welcome 由 SB-01 logo 链接承接；无对话时 SB-05/SB-06 整组不渲染。
> 
> **v1 变更说明**：原「新建对话」按钮改为「空间管理」。按钮从直接创建对话（`/courses/new`）变为跳转到 `/spaces` 空间管理页，承载空间 CRUD 入口。

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | ERROR |
|---|---|---|---|---|---|
| 空间列表 | 正在读取空间… | 整组隐藏（无空态占位） | 对话行 | 部分加载 | 空间列表暂时不可用。 |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 当前空间行 `aria-current`；nav 项语义化（`UI-NAV-001`）。 |
| A-02 | 「空间管理」可键盘直达；恢复指示 `role="status"`。 |
| A-03 | 折叠/展开符合 Disclosure 原语（`INT-005`）；focus 管理。 |

## 6. 禁止事项与现状 GAP

| GAP | 处理 |
|---|---|
| （无关键冲突） | 现状与空间中心 IA 一致；保持 FolderOpen 一级项，Welcome 由 logo 链接承接。 |

禁止：恢复「今天」「学习」「Chat」等一级导航（`EXP-IA-001`/`UI-NAV-004`）；在主按钮外再放一个「新建对话」；恢复「欢迎」一级导航项或「已有对话」空态占位。
