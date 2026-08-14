# 05 — Icon Inventory

**Phase**: 1 · **Generated**: 2026-08-12 · **Evidence**: `assets/icons/*.svg` 脚本扫描（671 个）[L]

---

## 总量与规格

| 指标 | 值 |
|---|---|
| 总图标数 | **671** |
| 主规格 | **16×16**（578 个，86%） |
| 其他规格 | 40×40(21)、14×14(18)、18×18(10)、28×28(8)、20×20(6)、17×16(6)、24×24(8) 等 |
| 填充型 | 656（fill） |
| 描边型 | 15（stroke） |
| 含 currentColor | **545**（可 token 化单色） |
| 多色/品牌（粗判） | ~54 |

## 图标规格分布

| viewBox | 数量 |
|---|---|
| 0 0 16 16 | 578 |
| 0 0 40 40 | 21 |
| 0 0 14 14 | 18 |
| 0 0 18 18 | 10 |
| 0 0 28 28 | 8 |
| 0 0 20 20 / 24 24 | 各 6~8 |
| 其他 | 少量 |

## 分类（按文件名粗判）

| 类别 | 数量 | 示例命名 |
|---|---|---|
| file/folder | 63 | file, folder, doc, dir |
| action | 52 | add, close, check, plus, minus, delete, edit |
| code/terminal | 27 | terminal, code, bracket, braces, debug |
| arrow/chevron | 17 | chevron, arrow, caret |
| network | 14 | cloud, upload, download, sync, link |
| agent/ai | 12 | agent, ai_, spark, assistant |
| search | 11 | search, filter, funnel |
| media | 10 | play, pause, video, audio |
| communication | 8 | message, chat, comment, mail |
| status | 7 | star, heart, bookmark, pin |
| settings | 4 | setting, gear |
| other | 446 | 其余（含大量命名未规整） |

## 与 Code Welcome Screen 直接相关的图标

**Sidebar / Shell**：chevron-down/right、plus、search、folder、file、layout、grid、split、sidebar-left/right、agent、task、project、dot、circle、check

**Prompt Composer**：attachment、plus、send、paperplane、seed、code、down、voice/mic（若存在）、model

## 命名规则观察

1. 命名不统一：存在 `add.svg` / `Add.svg` / `add-circle-filled.svg` / `add-circle-outline.svg` 混用（大小写 + 连字符）。
2. 核心语义图标有 currentColor 支持（545 个），可在 token-colored 控件内用 CSS mask 复用。
3. [L] `library-consumption.json` 规定：单色图标用 `modeB currentColor mask`，多色品牌用 `<img>`；**无 runtime sprite**。
4. [U] 少量图标（如 Voice/Mic、Model selector 图标）需核对是否存在；Composer 交互所需图标集待确认。

## 建议（Phase 2 输入）

1. 仅导入当前 Screenshot 实际使用的图标进入 Figma（第一阶段）。
2. Icon Component 用 Instance Swap + 分类组织，不铺满一页。
3. 命名规范化建议单独记录为 Open Question。[U]
