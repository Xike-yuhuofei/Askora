# 14 — Desktop Resize Model

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: shell-three-panel contract [L] + Screenshot [S] + UIKit [L]

---

## 原则

不使用传统 Mobile Responsive 思路。桌面布局基于「固定列 + Flex」与「Min/Max 约束」。

## 实测 / 契约数据

| 项 | 值 | Evidence |
|---|---|---|
| Window（截图） | 2291×1299 | [C][S] |
| Sidebar Observed Width | 301px | [C][S] |
| Sidebar Default Width | Unknown | [U] |
| Sidebar Min Width | Unknown（shell 折叠 48px 是三栏场景） | [U] |
| Sidebar Max Width | Unknown | [U] |
| Workspace | flex 填充（302..窗口右缘） | [C][S] |
| Workspace Min Width | 480px（shell-three-panel center min） | [I][L] |
| Shell Min Viewport | 960px（shell-three-panel） | [I][L] |
| Left Panel（三栏） | 200px / 折叠 48px | [L] |
| Right Panel（三栏） | 360px / 折叠 0px | [L] |
| Gutter | 1px border + 4px gap | [L] |

## 布局行为假设

| 行为 | 判定 | 依据 |
|---|---|---|
| Window Resize | Workspace flex 吸收宽度变化 | [I][S] |
| Sidebar Resize | Unknown（无拖拽证据） | [U] |
| Workspace Flex | 是（内容居中，两边留白） | [C][S] Composer 居中验证 |
| Min Content Width | 480px（center panel min） | [I][L] |
| Overflow | 侧栏内容区滚动 | [I][L] dev-explorer |
| Scroll | 侧栏内容滚动，account 固定 | [I][L] |
| Collapse | 三栏 shell 支持 left/right 折叠 | [L]（但非当前视图） |

## 假设（hypothesis）与 Unknown

- [I] Composer 在 Workspace 内居中，不随内容变宽而左移。
- [U] Sidebar 是否可拖拽调宽。
- [U] Window 最小宽度。
- [U] 极窄窗口下 Sidebar 是否折叠/覆盖。

## 结论

1. [C][S] 当前视图：固定 Sidebar（301px）+ Flex Workspace。
2. [L] 三栏 shell 提供 min-width 与折叠的系统级规则（Phase 2 扩展用）。
3. [U] 明确 Unknown 项，避免猜测。
