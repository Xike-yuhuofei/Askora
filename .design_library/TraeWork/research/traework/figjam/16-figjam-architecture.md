# 16 — FigJam Board Architecture（Phase 1 规划）

**Phase**: 1 · **Generated**: 2026-08-12
**状态**: 规划文档。按用户确认，Phase 1 不实际创建 FigJam，此文档作为 Phase 2 FigJam 构建规格。

---

## Board 信息

- **Board 名**: `TraeWork — UI Reverse Engineering`
- 用途边界：仅 Architecture / Relationships / Flows / Taxonomy / State / Evidence / Hypothesis / Unknown。
- **禁止**：不用 FigJam 制作高保真 UI。

## Sections（16 个）

| # | Section | 内容来源 |
|---|---|---|
| 00 | Reverse Engineering Map | 总览图（Source→Analysis→Screens→Figma） |
| 01 | Source Inventory | analysis/01 数据 |
| 02 | Screenshot Evidence | 8 张 Light 截图 + 关键标注 |
| 03 | Information Architecture | analysis/08 导航层级 |
| 04 | Application Shell | analysis/09 App Shell 图 |
| 05 | Sidebar Architecture | analysis/09b 分区结构 |
| 06 | Workspace Architecture | Workspace 布局 + 三栏参考 |
| 07 | Component Taxonomy | analysis/11 分层 |
| 08 | Prompt Composer Anatomy | analysis/10 拆解 |
| 09 | Design Tokens | analysis/02 Token 结构 |
| 10 | Interaction Model | analysis/12 交互清单 |
| 11 | State Model | analysis/13 状态分类 |
| 12 | Resize Model | analysis/14 约束 |
| 13 | Evidence Matrix | [C]/[I]/[U] 汇总 |
| 14 | Open Questions | analysis/16 |
| 15 | Figma Build Plan | 本目录 17 文档 |

## 建 Board 顺序（Phase 2）

1. 00 Map（占位框架）
2. 01 → 02（证据层）
3. 03 → 04 → 05 → 06（架构层）
4. 07 → 08（组件层）
5. 09（Token 层）
6. 10 → 11 → 12（行为层）
7. 13 → 14 → 15（决策层）

## 工具依赖

- FigJam 通过 `figma-mcp-rust` / `open-figma-mcp` 创建。两个 MCP 均 Connected（`claude mcp list` 确认）。
- Phase 1 已确认：**不创建实际 FigJam**，仅此规划。[用户决策]

## 验收

- 每个 Section 有明确标题与对应分析文档引用。
- 证据等级标注保留。
- Unknown 显式呈现，不消灭。
