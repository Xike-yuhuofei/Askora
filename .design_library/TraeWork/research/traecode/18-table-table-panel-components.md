# Official Table / Table Panel Figma Evidence

> 状态：Research / Supporting，Phase 9 已完成  
> Source：`TraeCode Copy/components/table.json`、`table-panel.json`、`tag.json`、`avatar.json` 与对应 preview HTML  
> Figma：`03 Components`，live audit 2026-08-12  
> Authority：TraeCode 外部设计资产；不是 Askora Canonical UI 或生产交互合同

## 1. 本阶段结论

Phase 9 没有把 Application Shell 中的 Change Summary / Change Review 强行替换为 Table。Shell `57:6` 的相关区域是 File Link、Badge、Button 与内容 Frame 的组合，不是截图或官方合同可确认的数据表格 `[C current Figma]`。

因此本阶段采用 migration-ready 策略：先建立可复用的官方 Table Library、Table Panel Library 与展示板；只有未来 Screen 证据确认真实表格时，才在对应 Screen / Pattern 中使用实例。

## 2. Source-backed Contracts

| Contract | Confirmed source rules | 保持 Unknown 的行为 |
|---|---|---|
| `table` | regular density；Header / Text / Avatar+Text / Tag / Action cells；12px vertical / 8px horizontal；status 只出现在 inline Tag | selection、sort、column resize、pagination integration |
| `table-panel` | external Header pairing；top corners = 0；bottom corners = `radius-4`；12px vertical / 16px horizontal；numeric mono + right aligned | selection、sort、column resize、sticky header、vertical scrolling |
| `tag` | Default / Success / Warning / Danger / Brand；source preview 另含 Count / Neutral Strong；leading dot 只在来源支持时显示 | dismiss / close、leading icon |
| `avatar` | 24 / 32 / 40；circle / square；neutral / accent；stack ring = 2px `bg-base-default` | image fallback chain、status dot |

## 3. Foundations 增量

### 3.1 Color variables

| Variable | Figma ID | Source / binding |
|---|---|---|
| `bg-overlay-l4` | `VariableID:106:478` | source raw value |
| `text-brand` | `VariableID:106:479` | source raw value |
| `status-warning-surface-l1` | `VariableID:106:480` | source raw value |
| `status-error-surface-l1` | `VariableID:106:481` | source raw value |
| `bg-layout-1` | `VariableID:106:482` | alias → `bg-base-secondary` |
| `border-1` | `VariableID:106:483` | alias → `border-neutral-l1` |

所有变量具有明确 scope 与 `var(--token-name)` WEB syntax；最终 alias audit 为 0 broken aliases `[C implementation]`。

### 3.2 Text styles

| Style | Font / size | 用途 |
|---|---|---|
| `TraeCode Official / Data / Table Header` | Inter fallback 10 / 14、4% tracking | uppercase table headers |
| `TraeCode Official / Data / Numeric Header` | JetBrains Mono 10 / 14、4% tracking | numeric table-panel headers |
| `TraeCode Official / Data / Numeric SM` | JetBrains Mono 11 / 16 | numeric body cells |
| `TraeCode Official / Component / Avatar / XS` | Inter fallback Semi Bold 10 / 14 | 24px avatar |
| `TraeCode Official / Component / Avatar / SM` | Inter fallback Semi Bold 11 / 16 | 32 / 40px avatar |

Inter 是当前 Figma runtime 对官方 system UI font 的展示 fallback；不改变官方字体来源记录。

## 4. Component Architecture

```text
Tag (107:499)
Avatar (109:502)
└── Avatar Group (110:478)

Table Cell (116:4599)
├── Header
├── Text
├── Numeric
├── Avatar + Text → linked Avatar
├── Tag → linked Tag
└── Action → linked Icon Button

Table Row (118:4618)
├── Header → linked Table Cell instances
└── Body → linked Table Cell instances

Table (124:687)
├── Bare
└── Wrapper = Toolbar + Rows + Footer

Table Panel Cell (125:4794)
├── Header
├── Header Numeric
├── Text
└── Numeric

Table Panel Row (125:4813)
├── Header
└── Body

Table Panel (126:695)
├── Panel body
│   ├── Header Row
│   └── 6 × Body Row
└── Footer
```

Supporting Arrow Left `120:513` 与 Arrow Right `120:517` 直接由官方 bundled SVG 创建；没有手绘或 detach。

## 5. Geometry / Layout Handoff

| Asset | Width | Height | Padding / gap | Surface / radius | Evidence |
|---|---:|---:|---|---|---|
| Table Header Cell | representative column width | 39 | 12 vertical / 8 horizontal | bottom separator | `[C source]` |
| Table Body Cell | representative column width | 55 | 12 vertical / 8 horizontal | bottom separator | `[C source]` |
| Table Row | 900 | 39 / 55 | 5 representative columns | transparent | `[C implementation]` |
| Bare Table | 900 | 204 | Header + 3 rows | `bg-base-secondary`、border、`radius-4` | `[C source + implementation]` |
| Wrapped Table | 900 | 363 | Toolbar 52 + Header 39 + 4×55 + Footer 52 | `radius-8` | `[C source + implementation]` |
| Table Panel Cell | representative column width | 39 / 55 | 12 vertical / 16 horizontal | `border-1` separator | `[C source]` |
| Table Panel body | 900 | 369 | Header + 6 rows | top radius 0、bottom `radius-4`、no top border | `[C source + implementation]` |
| Table Panel Footer | 900 | 30 | 8 vertical / 16 horizontal、gap 12 | inherited `bg-base-default` made explicit | `[C source inheritance + implementation]` |
| External Header example | 900 | 44 | 12 vertical / 16 horizontal | top `radius-4`、no bottom border | preview-local composition `[C source example]` |

这些宽度是代表性 Figma composition，不是生产 table width、column min/max 或 resize contract。

## 6. Table 与 Table Panel 的使用边界

| Need | 使用 |
|---|---|
| 单独出现、自己拥有 Toolbar 与 Footer | `Table / Chrome=Wrapper` |
| 只需一个有边界的静态表体 | `Table / Chrome=Bare` |
| 外部 Card/Header 已拥有 title / toolbar | `Table Panel`，由外部 Header 拥有 top rounding |
| 数值列对齐 | Table Panel Numeric Cell / Header Numeric，JetBrains Mono + right align |
| 状态表达 | inline Tag；禁止整行状态底色 |

## 7. Documentation Board

Documentation Board `126:4859`：1200 × 1722，包含：

1. Tag tone matrix；
2. Avatar size/tone matrix 与 Avatar Group；
3. Bare Table；
4. Wrapped Table；
5. Table Panel + external Header pairing；
6. `[C] / [U]` 证据边界说明。

Board 与所有代表组件均使用 linked instances；没有 detached component，也没有把 pagination controls 声明为真实分页行为。

## 8. Live Audit

| Check | Result |
|---|---:|
| `03 Components` Component Sets | 21 |
| Component nodes | 119 |
| Standalone components | 31 |
| Phase 9 authored nodes | 141 |
| Variable-bound nodes | 115 |
| Real instances | 61 |
| Linked instances | 61 / 61 |
| Placeholder | 0 |
| Missing authored key | 0 |
| Duplicate authored key | 0 |
| Broken variable alias | 0 |
| Forbidden named anatomy (`selection / sort / resize / sticky`) | 0 |
| Phase 9 font families | Inter fallback + JetBrains Mono |

## 9. Developer Mapping

```css
.table-cell {
  padding: var(--spacer-12) var(--spacer-8);
  border-bottom: 1px solid var(--border-neutral-l1);
}

.table-panel-cell {
  padding: var(--spacer-12) var(--spacer-16);
  border-bottom: 1px solid var(--border-1);
}

.table-panel {
  background: var(--bg-layout-1);
  border: 1px solid var(--border-1);
  border-top: 0;
  border-radius: 0 0 var(--radius-4) var(--radius-4);
}

.numeric-cell {
  font-family: var(--code-editor-font-family);
  font-variant-numeric: tabular-nums;
  text-align: right;
}
```

这是 TraeCode source-to-Figma 映射证据，不是 Askora production CSS 授权。

## 10. Remaining Unknowns

- pagination control 与 `pagination` 官方合同尚未集成 `[U]`；
- selection、sort、column resize、sticky header 均未定义 `[U]`；
- Table Panel 超过固定行数后的 vertical scroll 行为 `[U]`；
- column min/max、内容截断与 keyboard navigation `[U]`；
- 真实 TraeCode runtime 是否在当前截图场景使用这些官方 Table 组件 `[U]`。

下一步只有在新截图或可交互 runtime 证据到达后，才为这些行为建立 state / prototype。
