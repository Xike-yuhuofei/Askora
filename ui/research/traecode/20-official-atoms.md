# TraeCode Official Atoms

> 状态：Research / Supporting，Phase 11 source-backed Figma evidence  
> Source：\`TraeCode Copy/components/atoms.json\`、\`preview/component-atoms.html\`、\`components.css\`、\`colors_and_type.css\`  
> Authority：TraeCode 外部静态设计资产；不是 Askora Canonical Design System、runtime interaction contract 或 accessibility implementation

## 1. Scope Lock

官方 \`atoms\` contract 同时包含组件、文字 utility 与布局 utility。Figma 按语义类型消费，不把每个 CSS class 都制造成 Component：

| Source group | Figma representation | Evidence |
|---|---|---|
| \`.ds-tooltip\` | standalone Component \`171:1416\` | \`[C source + implementation]\` |
| \`.ds-popover\` | standalone slot Component \`172:1416\` | \`[C source + implementation]\` |
| \`.ds-empty\` | standalone Component \`175:1416\` | \`[C source + implementation]\` |
| \`.ds-code\` | standalone Component \`176:1421\` | \`[C source + implementation]\` |
| \`.h1/.h2/.h3/.eyebrow\` | Text Styles + specimens | \`[C source + implementation]\` |
| \`.mono/.num\` | Code / Numeric Text Styles + specimens | \`[C source + implementation]\` |
| \`.ds-row/.ds-col/.ds-grid-*/.ds-stack-*\` | Auto Layout recipes；不建立组件 | \`[C source / I Figma mapping]\` |
| \`.ds-hero-title/.ds-section-title\` | fluid range annotation；不冻结固定 Text Style | \`[C source / I Figma documentation]\` |

既有 Inline Code \`20:50\` 只用于说明 inline 与 block code 的边界；Phase 11 没有复制第二个 Inline Code。

## 2. Foundations

### 2.1 Variable

| Variable | ID | Source value | Scope / code syntax |
|---|---|---|---|
| \`bg-tooltip\` | \`VariableID:170:2\` | \`#1A1B1D\` | \`FRAME_FILL, SHAPE_FILL\` / \`var(--bg-tooltip)\` |

### 2.2 Effect Styles

| Style | ID | Source mapping |
|---|---|---|
| Tooltip | \`S:760bdc105b7d63fd2df2b6e40aa67334d0991a0b,\` | \`0 8 24 rgba(0,0,0,.36)\` |
| Popover | \`S:675d088f6fde8d84754db68459b31c0b2229577a,\` | \`0 12 32 rgba(0,0,0,.36)\` |

### 2.3 Text Styles

| Style | ID | Source role |
|---|---|---|
| Heading / 2XL | \`S:46c36dc5bfaf1cfeee0d55cbdb018d23cf50dfc2,\` | \`.h1\` |
| Heading / SM | \`S:3d092c17ca31914f213e34f3aedadde458048a6a,\` | \`.h3\` |
| Utility / Eyebrow | \`S:c9f9bee21c4b27ac48568e7fb06f33a5777a1ba4,\` | uppercase Body XS + 8% tracking |
| Body / Base Strong | \`S:9eefc82e51339f6ef0593e39301816795c3cd10b,\` | Empty State title |

Heading / MD、Body、Code / Editor 与 Numeric styles 复用既有 official styles。官方 UI font source 是 SF Pro Text / SF Pro；当前 Figma runtime 使用 Inter fallback，JetBrains Mono 保持原样 \`[C implementation]\`。

Fluid headline 不创建单点 style：

- Hero：\`clamp(40px, 6vw, 72px)\`；
- Hero subline：\`clamp(28px, 4vw, 56px)\`；
- Section title：\`clamp(24px, 2.4vw, 32px)\`。

## 3. Component Contracts

| Component | Size | Properties | Confirmed static contract | Runtime boundary |
|---|---:|---|---|---|
| Tooltip \`171:1416\` | 49 × 22 default | \`Text\` | official padding、gap、radius、border、Body XS、Tooltip shadow | trigger、delay、placement、dismissal、focus、keyboard \`[U]\` |
| Popover Surface \`172:1416\` | 280 × 48 default | \`Content SLOT\` | overlay surface、border、radius、12px padding、Popover shadow；Slot transparent | trigger、anchor、placement、dismissal、focus management \`[U]\` |
| Empty State \`175:1416\` | 520 × 172 default | \`Title\`、\`Description\`、\`Icon INSTANCE_SWAP\` | 40px icon slot、title/description、dashed border、无 CTA | empty-state selection、CTA policy、announcements \`[U]\` |
| Code Block \`176:1421\` | 520 × 44 default | \`Code\` | pre-like surface、12 × 16 padding、Code / Editor style、horizontal overflow mapping | scrollbar affordance、copy、language、line number behavior \`[U]\` |

\`dashPattern=[4,4]\` 是 Figma 对 CSS \`dashed\` 的显示映射 \`[I]\`。Code Block 的 \`overflowDirection=HORIZONTAL\` 表示静态 scenegraph 映射，不证明真实应用的 scrollbar 或 keyboard scrolling。

## 4. Documentation Board

Board：\`Phase 11 / Official Atoms\`，ID \`177:1421\`，1200 × 2186。

Sections：

1. Source-backed Components；
2. Utilities, Not Components；
3. Evidence & Scope。

Board 中有 5 个直接 linked documentation instances：

- Tooltip \`178:1422\`；
- 既有 Inline Code \`178:1424\`；
- Popover \`178:5527\`；
- Code Block \`178:5530\`；
- Empty State \`178:5538\`。

Utilities 明确展示：

- H1 / H2 / H3 / Eyebrow styles；
- Hero / Section fluid ranges；
- Mono / numeric tabular specimens；
- Row / Column / Grid 的 Auto Layout mapping。

## 5. Live Audit

2026-08-12 live Plugin API audit：

| Check | Result |
|---|---:|
| New components | 4 |
| Linked documentation samples | 5 / 5 |
| Component copies in Board | 0 |
| Authored nodes | 92 |
| Virtual inherited nodes excluded | 20 |
| Variable-bound nodes | 90 |
| Bound variables consumed | 18 |
| Missing / duplicate authored \`dsb\` keys | 0 / 0 |
| Placeholder nodes | 0 |
| Unbound solid fills / strokes | 0 |
| Clipped text nodes | 0 |
| Unlinked instances | 0 |
| Fonts | Inter fallback + JetBrains Mono |

视觉审计额外清除了纯布局 Frame 的 Figma 默认白色 fill，并将 Popover \`Content Slot\` 修正为透明；最终组件、Utilities 与 Evidence 区段均已截图复核 \`[C implementation]\`。

## 6. Evidence Boundary

### Confirmed

- 官方 CSS、DOM anatomy、tokens consumed；
- 4 个静态 atoms、heading/mono utilities 与 layout helper 列表；
- 当前 Figma components、properties、bindings、styles 与 Board scenegraph。

### Inferred

- CSS dashed 到 Figma \`[4,4]\`；
- 文档展示宽度；
- CSS flex/grid 到 Figma Auto Layout recipe；
- fluid CSS 在 Figma 中只以 range annotation 表达。

### Unknown

- Tooltip / Popover 的 trigger、placement、delay、dismissal、focus、keyboard 与 transition；
- Code Block 的真实 scroll affordance、copy、language 和 line-number behavior；
- Empty State 的业务选择规则、CTA 与 accessibility announcement。

TraeCode atoms 仍是 Askora 外部 reference-only 资产。任何进入 Askora 的组件或 token 必须先通过 Askora Product / Design / ADR / Spec adoption gate。
