# 16 — Open Questions

**Phase**: 1 · **Generated**: 2026-08-12

Unknown 是 Reverse Engineering 的正常结果。以下均不作猜测。

---

## Need More Screenshot

| # | 问题 | 相关 |
|---|---|---|
| 1 | Mode Switcher 确切三项文案（Work/Code/Design？）与外观 | 主截图 [U] |
| 2 | Pinned 与 Workspace Navigation 的分界 | 主截图 [U] |
| 3 | Sidebar 默认/最小/最大宽度（仅 Observed 301px 确认） | 09b [U] |
| 4 | 右侧面板是否常驻（当前 Code Welcome 无） | 09 [U] |
| 5 | Status 色的实际呈现（无 status 色块） | 03 [U] |
| 6 | Composer 圆角精确值 | 07 [U] |
| 7 | 行高精确值（文本 14px vs 整行） | 07 [U] |

## Need Interaction Verification

| # | 问题 |
|---|---|
| 8 | Resize 拖拽细节 |
| 9 | Sidebar 是否可折叠/可调宽 |
| 10 | 键盘快捷键（App 级） |
| 11 | 任务拖拽重排 |

## Need Resize Verification

| # | 问题 |
|---|---|
| 12 | Window 最小宽度 |
| 13 | 极窄窗口下 Sidebar 行为 |
| 14 | Workspace min-width（480px 是推断） |

## Need Component Verification

| # | 问题 |
|---|---|
| 15 | Composer 高度 55px(截图) vs 100px(契约) 差异 |
| 16 | send-btn 实测 15×14 vs 契约 28×28（含 padding 差异） |
| 17 | html-effectiveness-doc 质量报告与标记不一致 |

## Need Token Verification

| # | 问题 |
|---|---|
| 18 | status-bar 引用的 `--brand-grey-700` 是否新增 canonical token |
| 19 | 6 个 reverse-engineered 组件的 ~46 个 newTokensProposed 是否纳入 |
| 20 | shadow token（css.json shadow 组为空）需定义 --shadow-1..N |

## Other

| # | 问题 |
|---|---|
| 21 | SF Pro / JetBrains Mono 字体是否安装（缺失则 Font Missing） |
| 22 | 图标命名规范（add.svg vs Add.svg 混用）是否统一 |
| 23 | Composer Voice / Model selector 图标是否存在于 assets |
