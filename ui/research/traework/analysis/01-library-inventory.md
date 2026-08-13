# 01 — Library Inventory

**Phase**: 1 · **Generated**: 2026-08-12 · **Evidence basis**: 实读 `/Users/xike/Documents/Docs/Askora/TraeWork/TraeWork/`

---

## Files

| 层 | 路径 | 说明 |
|---|---|---|
| Tokens | `colors_and_type.css` (16,449 B) | Light-mode token CSS，canonical + 兼容别名 |
| Tokens | `css.json` (39,543 B) | 机器可读 token 分组 JSON |
| Components | `components.css` (38,077 B) | 组件样式聚合（按组件 marker 分块） |
| Components | `components/index.json` | 组件清单（20 个契约摘要） |
| Components | `components/{slug}.json` × 20 | 组件契约 |
| Previews | `preview/component-*.html` × 20 | 组件预览页 |
| Icons | `assets/icons/*.svg` | SVG 图标库 |
| UI Kits | `ui_kits/{type}/index.html` × 10 | 页面级 showcase |
| UI Kits | `ui_kits/{type}/quality-report.json` | 复用率证据 |
| Plan | `uikit-plan.json` | UIKit 规划 |
| Contract | `library-consumption.json` | 下游消费路由契约 |
| Docs | `README.md`, `SKILL.md` | 文档 |

## 实际数量（脚本实测，非描述假定）

- **Icons**: 671 个 SVG
- **Components**: 20 个契约 JSON
- **Component previews**: 20 个 HTML
- **UI Kits**: 10 个目录

## Tokens

`css.json` 顶层分组：

| 组 | 数量 | 内容 |
|---|---|---|
| color | 12 子组 | bg-brand(10) / bg(24) / icon(13) / text(20) / border(10) / status(35) / brand(102) / code(11) / accent(9) / viz(23) / special(4) / layout aliases(8) |
| font | 8 子组 | family / familyTokens / textStyles(22) / textStyleFamilyTokens / size / weight / lineHeight / letterSpacing |
| radius | 17 | radius-0..32, radius-full, 语义别名 xs-xl |
| spacing | 15 | spacer-0..64 |
| size | 6 | border-width-default, icon-size-12..24 |
| shadow | 0 | 空（依赖组件内 shadow） |

## Components

契约 `sourceKind` 两类：

- **preview-contract**（14，confidence=medium）：由 preview + components.css 推导，已入 components.css。
- **reverse-engineered**（6，confidence=low）：由产品截图反推，CSS 待入库，均含 `newTokensProposed`。

| slug | name | category | tokens |
|---|---|---|---|
| alert | Notifications | feedback | 37 |
| avatar | Avatar | data-display | 8 |
| breadcrumb | Breadcrumb | navigation | 5 |
| buttons | Button | action | 48 |
| cards | Card / List | layout | 12 |
| dialog | Dialog / Modal | overlay | 25 |
| forms | Form | input | 30 |
| menu | Menu | navigation | 22 |
| pagination | Pagination | navigation | 16 |
| progress | Progress / Slider | feedback | 4 |
| skeleton | Skeleton | feedback | 4 |
| table | Table | data-display | 15 |
| tabs | Tabs | navigation | 16 |
| tag | Tag | feedback | 16 |
| shell-three-panel | Three-Panel Shell | layout | 18 |
| ai-input | AI Input Box | input | 28 |
| task-tree | Task Hierarchy Tree | navigation | 24 |
| status-bar | Status Bar | feedback | 21 |
| card-template | Rich Template Card | layout | 23 |
| code-editor | Code Editor | input | 42 |

## Icons

- 总数 671
- 主规格 **16×16**（578 个，占 86%）；其余 28×28(8)、40×40(21)、14×14(18)、18×18(10) 等
- 656 个为 fill 型，15 个 stroke 型
- **545 个含 currentColor**（单色可 token 化）
- 多色（品牌/彩色）约 54 个
- 分类粗判：file/folder(63)、action(52)、code/terminal(27)、arrow/chevron(17)、network(14)、agent/ai(12)、search(11)、media(10)、communication(8)、status(7)、settings(4)、other(446)

## UI Kits

| type | title | previewClassReuseRate | basis | 类型 |
|---|---|---|---|---|
| dev-explorer | Dev Explorer | 0.01 | semantic-fallback | 桌面工作台 |
| dashboard | Mosaic Dashboard Case | 0.16 | ds-class | SaaS 控制台 |
| dashboard-2 | Adminator Dashboard | 0.18 | ds-class | 控制台 |
| settings | Settings | 0.23 | ds-class | 桌面设置 |
| skills-library | TraeWork Skills Overview | 0.31 | ds-class | 技能库 |
| comment-threads-plan | Implementation Plan | 0.15 | ds-class | 文档 |
| html-effectiveness-doc | HTML Effectiveness Examples | 0.01 | ds-class* | 示例画廊 |
| landing | TraeWork for Teams | 0.31 | ds-class | 营销页 |
| pricing-doc | TraeWork Pricing | 0.12 | ds-class | 定价文档 |
| product-overview | TraeWork Product Overview | 0.17 | ds-class | 产品概览 |

> html-effectiveness-doc 质量报告声明 ds-class，但标记实测无 `.ds-*` 类，属文档-标记不一致，记录待核。[U]

## Preview Pages

20 个，对应 20 个组件契约（见上表）。均为静态 HTML，引用共享 `colors_and_type.css` + `components.css`。

## CSS

- `colors_and_type.css`：Light canonical tokens。语义分组优先：radius → spacers → font → body → heading → code → bg → bg-brand → text → icon → border → accent → status → brand。
- `components.css`：按 `/* @component-css-start */` marker 分块，聚合 preview 的组件样式。

## JSON Contracts

- `library-consumption.json`：schemaVersion 2，tokenSource=css.json，消费层 tokens/components/icons/uikit，iconCount=671，icon 规则（modeA `<img>` / modeB currentColor mask，无 runtime sprite），下游场景，uikit 外壳上限 1184px。
- `uikit-plan.json`：schemaVersion 1，corePreviewComponents 8 个（buttons/cards/forms/menu/pagination/table/tabs/tag），support 6 个（alert/avatar/breadcrumb/dialog/progress/skeleton），10 个 screenBlueprints，productType="AI workspace and work management surfaces"。
- `components/index.json`：schemaVersion 2，sourceKind="preview-contract + reverse-engineered"，明确不要求对齐 TRAE 2 组件数。

## Documentation

- `README.md`：Library 消费契约、token highlights、已知限制（预览 shell CSS 已移除；契约 medium-confidence）。
- `SKILL.md`（12,143 B）：library 制作技能说明。

## 关键结论

1. [L] TraeWork 是 **Light-only** 设计库，canonical token 带 `--color-*` 兼容别名。
2. [L] 组件契约分两代：14 preview-contract（medium）+ 6 reverse-engineered（low，来自产品截图，含 newTokensProposed）。
3. [L] **icons 唯一来源 = assets/icons**，无 runtime sprite。
4. [L] dev-explorer 是最接近 Desktop App Shell 的 UIKit（sidebar+workspace，macOS traffic lights），但复用率 0.01 且走 semantic-fallback —— **不能作为正式 App Shell 模板，仅作结构参考**。
5. [L] UIKit 外壳上限 1184px，不可直接当生产页模板。
