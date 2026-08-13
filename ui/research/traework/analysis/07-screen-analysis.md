# 07 — Screen Analysis（Light Mode 主截图）

**Phase**: 1 · **Generated**: 2026-08-12 · **Evidence**: 截图实测 [S]

---

## 截图确认

- **文件名**: `20260812-091658-TraeCode主界面.png`
- **路径**: `/Users/xike/Documents/Docs/Askora/TraeWork/截图/`
- **分辨率**: 2291×1299（**1x**，非 Retina 2x —— traffic light 中心间距 20px 符合 macOS 标准 1x）
- **修改时间**: 2026-08-12 09:17
- **模式**: Light Mode ✅（无 Dark 旧图）

## 同类截图（8 张，均为 2026-08-12，Light Mode）

| 文件 | 用途 |
|---|---|
| 20260812-091658-TraeCode主界面.png | **主分析对象**（Code Welcome） |
| 20260812-091735-插件市场.png | 插件市场（IA 扩展） |
| 20260812-091742-自动化任务模板.png | 自动化模板 |
| 20260812-091753-办公助理绑定通讯工具.png | 办公助理 |
| 20260812-091800-模板库.png | 模板库 |
| 20260812-091818-Askora学习消息系统任务预览.png | 任务预览 |
| 20260812-091843-Askora任务Work视图.png | Work 视图 |
| 20260812-091905-TraeWork设置通用.png | 设置通用 |

## Window Bounds

| 项 | 值 [S] |
|---|---|
| 窗口宽 | 2291 px |
| 窗口高 | 1299 px |
| 顶部 macOS 标题栏 | y≈0..40（含 traffic lights） |
| Traffic lights | 红 x≈35 / 黄 x≈55 / 绿 x≈75，y≈24..37 |

## Sidebar Bounds

| 项 | 值 [S] | 逻辑推断 |
|---|---|---|
| Sidebar 宽 | **301 px**（x=0..301） | 固定宽列 |
| 背景 | `#f5f5f5` = `bg-base-secondary` | ✅ 与 token 一致 |
| 右缘分隔 | x=301 `#efefef`（≈ border-neutral-l1 叠加） | 1px 分隔 |
| 内部元素行高 | 14px 文本行，行距约 40px（166/206/246/286...） | 待确认 exact row height |
| 搜索区 | y≈64..95（`#e6e6e6` ≈ bg-base-tertiary） | 搜索框 |
| 模式切换器 | y≈116..149 | Mode switcher |
| 底部账户区 | y≈1259..1282（h24） | 用户行 |

## Main Workspace Bounds

| 项 | 值 [S] |
|---|---|
| Workspace x | 302..2291 |
| 背景 | `#ffffff` = `bg-base-default` ✅ |
| 内容中心 x | ≈ 1296（workspace 几何中心） |

## Welcome Surface / Composer

| 项 | 值 [S] | 推断 |
|---|---|---|
| 标题文字区 | y≈461..476（深色 `#181818`） | Heading 标题 |
| 副标题/占位 | y≈537..566（`#8d9399` 灰） | 次级文字 |
| **Composer 容器** | **x=892..1691（宽 800），y=654..708（高 55）** | Prompt Composer |
| Composer 背景 | `#f5f5f5`（bg-base-secondary） | ✅ |
| Composer 上边框 | y=664 `#e7e7e7`（≈ border） | 1px |
| Composer 中心 | x≈1292, y≈681 | ≈ workspace 几何中心偏上 |
| 发送按钮 | x≈1663..1678，色 `#4b3fe3` = bg-brand | ✅ |
| Quick Actions | y≈741..778（含 1px 分隔线） | 快捷操作行 |

## 主要元素坐标汇总

| 元素 | X | Y | W | H |
|---|---|---|---|---|
| Sidebar | 0 | 0 | 301 | 1299 |
| Workspace | 302 | 0 | 1989 | 1299 |
| 标题区 | 900+ | 461 | ~ | ~75 |
| Composer | 892 | 654 | 800 | 55 |
| Send btn | 1663 | 668 | 15 | 14 |
| Quick Actions | 900+ | 741 | ~ | ~37 |

## 对齐规律

- Composer 居中于 **Workspace 几何中心**（x≈1296）而非窗口中心（1145）。[C][S]
- Sidebar 为固定宽列，Workspace flex 填充剩余。[C][S]
- 垂直节奏：标题→副标题→Composer→Quick Actions，均沿中心轴分布。[C][S]

## Open questions 预记

- Row height 精确值需更高采样（截图文字小）。[U]
- Mode switcher 具体三项（Work/Code/Design）文字需 OCR/放大确认。[U]
