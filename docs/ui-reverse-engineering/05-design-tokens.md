# Design Token 假设清单

> 状态：Research / Supporting，Working Hypothesis  
> 适用范围：TraeCode screenshot reconstruction  
> 禁止：覆盖 Askora current light baseline 或直接作为生产 token contract

## 0. 2026-08-11 官方来源更新

用户后续提供 `TraeCode Copy/` 并确认其为 TraeCode 官方 Design System `[C]`。因此本文件原有 `bg/app`、`space/2`、`radius/s` 等内容继续保留为 screenshot candidate，不再作为 Figma component 的默认 token truth。

当前优先级：

```text
TraeCode Copy/colors_and_type.css + css.json [C]
→ components/*.json + preview/component-*.html [C]
→ screenshot-to-token mapping [I]
→ 本文件原始视觉候选 [I]
```

Figma 当前 official subset：39 个 Color Core variables、9 个 spacing、6 个 radius、16 个 official text styles 与 2 个 official effect styles；完整来源和字体 fallback 见 [Official Design System Consumption](12-official-design-system-consumption.md)。

### 0.1 Phase 9 Table foundations `[C implementation]`

Table / Table Panel 引入 6 个 source-backed Color Core variables：`bg-overlay-l4`、`text-brand`、`status-warning-surface-l1`、`status-error-surface-l1`、`bg-layout-1` 与 `border-1`。后两者保留官方 alias 关系：

```text
bg-layout-1 → bg-base-secondary
border-1 → border-neutral-l1
```

新增 5 个 data/avatar text styles：Table Header、Numeric Header、Numeric SM、Avatar XS 与 Avatar SM。Numeric styles 使用 JetBrains Mono；UI / Avatar styles 使用当前 Figma runtime 的 Inter system-ui fallback。Phase 9 live audit 为 0 broken alias，且所有新增变量都有明确 scope 与 WEB code syntax。

### 0.2 Phase 10 Button token consumption `[C implementation]`

Button 没有创建第二套 component token collection，而是直接复用现有官方变量：

- Primary：`text-default / text-default-hover / text-secondary`；
- Secondary / Tertiary：`bg-overlay-l1 / l2 / l3` 与 `border-neutral-l1 / l2`；
- Danger / Warning：`status-error-*` 与 `status-warning-default`；
- Brand：`bg-brand / bg-brand-hover / bg-brand-disabled`；
- Link：`text-default / text-default-hover / text-secondary / text-tertiary`；
- geometry：`spacer-6 / 8 / 12 / 16` 与 `radius-4`。

Phase 10 live audit 识别 31 个被 Button authored nodes 消费的变量，0 missing binding、0 broken alias。官方静态四态不新增 `focus`、`loading`、`spinner` 或 `tooltip` token；这些行为在 TraeCode runtime 仍为 `[U]`，Askora 则继续服从自己的 Canonical Design System。

### 0.3 Phase 11 Atoms foundations `[C implementation]`

Atoms 新增官方 `bg-tooltip` variable `VariableID:170:2`，值为 `#1A1B1D`，scope 为 `FRAME_FILL, SHAPE_FILL`，WEB code syntax 为 `var(--bg-tooltip)`。

新增两个 source-backed Effect Styles：

- Tooltip：`0 8 24 rgba(0,0,0,.36)`；
- Popover：`0 12 32 rgba(0,0,0,.36)`。

新增 Heading / 2XL、Heading / SM、Utility / Eyebrow 与 Body / Base Strong 四个 Text Styles；Heading / MD、Body、Code / Editor 与 Numeric styles 复用既有 official styles。Hero / Section title 的 `clamp()` range 只作为 Figma annotation，不冻结为单一 Text Style。

Phase 11 live audit 共消费 18 个 official variables，90 / 92 authored nodes 有 variable binding，0 missing binding、0 unbound solid paint。完整证据见 [Official Atoms](20-official-atoms.md)。

## 1. Token 策略

本节记录最初仅凭截图形成的 Semantic Token 候选。颜色像素可以采样 `[C]`，但将某个像素命名为 `bg/panel`、`interaction/selected` 等语义动作仍属于推断 `[I]`。

官方 token 使用 `TraeCode Official / …` collection；仍需截图实验的值使用 `TraeCode RE / Screenshot Candidates / …`，两者都与 Askora Foundations 隔离。

## 2. Color

| Semantic token candidate | Candidate value | Evidence | 当前用途假设 |
|---|---|---|---|
| `bg/app` | `#1A1A1D` | 像素样本 `[C]`；语义 `[I]` | Editor / preview 主背景 |
| `bg/panel` | `#222327` | 像素样本 `[C]`；语义 `[I]` | Task Rail / panel surface |
| `bg/control` | `#27272B` | 像素样本 `[C]`；语义 `[I]` | toolbar、composer、control surface |
| `bg/elevated` | `#292B2F` | 像素样本 `[C]`；语义 `[I]` | selected card / code block / elevated row |
| `border/default` | `#2D2D32` | 像素样本 `[C]`；语义 `[I]` | panel divider / control border |
| `border/subtle` | `#34353B` | 近似采样 `[I]` | table / nested divider |
| `text/primary` | `#D1D3DB` | 像素样本近似 `[C]`；语义 `[I]` | heading / primary UI text |
| `text/secondary` | `#9599A6` | 像素样本近似 `[C]`；语义 `[I]` | metadata / secondary label |
| `text/muted` | `#6F7480` | `[I]` | disabled-looking metadata / placeholder |
| `accent/default` | `#80BBFF` | 像素样本近似 `[C]`；语义 `[I]` | file link / active code reference |
| `status/success` | `#32C192` | 像素样本近似 `[C]`；语义 `[I]` | completed task / completion status |
| `status/warning` | `#D8A74E` | `[I]` | pending review / warning count |
| `status/error` | `#E05B64` | `[I]` | error state candidate；当前无完整 error surface |
| `interaction/selected-bg` | `#35363D` | `[I]` | active task / active row |
| `interaction/hover-bg` | `[U]` | `[U]` | 需要 pointer screenshot |
| `interaction/focus` | `[U]` | `[U]` | 需要 keyboard focus screenshot |

### 2.1 颜色关系假设

- Dark surface 主要通过小幅明度差和 1px divider 分层，而不是明显 shadow `[I]`。
- Active / selected 同时依赖背景、边框或文字强调，不应只依赖色相 `[I]`。
- Success green 同时出现在 icon 与状态文字附近 `[C]`，但具体 success palette 数量 `[U]`。
- Accent blue 更像链接/代码引用色，不等于产品 brand primary `[I]`。

## 3. Typography

| Text style candidate | Family | Size / line-height | Weight | Evidence |
|---|---|---|---|---|
| `UI / Small` | system sans + Chinese system fallback `[I]` | 11–12 / 16 `[I]` | 400–500 `[I]` | metadata、status |
| `UI / Body` | system sans + Chinese system fallback `[I]` | 13–14 / 20 `[I]` | 400 `[I]` | panel / task body |
| `UI / Label` | system sans + Chinese system fallback `[I]` | 12–13 / 18 `[I]` | 500–600 `[I]` | tabs、controls |
| `UI / Heading` | system sans + Chinese system fallback `[I]` | 18–24 / 26–34 `[I]` | 600–700 `[I]` | Markdown Preview headings |
| `Code / Small` | monospaced family `[C]`; exact family `[U]` | 11–12 / 17 `[I]` | 400 `[I]` | status/log/inline code |
| `Code / Body` | monospaced family `[C]`; exact family `[U]` | 12–13 / 19 `[I]` | 400 `[I]` | code block / output |

候选字体不应命名为 SF Pro、Inter、Menlo 或 JetBrains Mono，除非从应用 CSS、Figma source 或 font inspection 得到证据。

## 4. Spacing

| Token candidate | Value | Evidence | 典型场景 |
|---|---:|---|---|
| `space/2` | 2 | `[I]` | optical alignment |
| `space/4` | 4 | `[I]` | icon-label micro gap |
| `space/6` | 6 | `[I]` | dense control padding |
| `space/8` | 8 | `[I]` | compact row gap / task card gap |
| `space/12` | 12 | `[I]` | panel inset / card padding |
| `space/16` | 16 | `[I]` | content block inset |
| `space/24` | 24 | `[I]` | section gap |
| `space/32` | 32 | `[I]` | major document separation |

`space/6` 不能因为不符合纯 4px scale 就删除；应先验证它是实际 token、字体 line-box 结果，还是测量误差。

## 5. Radius / Border / Elevation

| Token candidate | Value | Evidence | 说明 |
|---|---:|---|---|
| `radius/s` | 4 | `[I]` | dense control / tag |
| `radius/m` | 6 | `[I]` | task item / button / code block |
| `radius/l` | 8 | `[I]` | composer / larger surface |
| `border/default-width` | 1 image px | `[C]` | logical px `[U]` |
| `border/focus-width` | `[U]` | `[U]` | focus screenshot required |
| `elevation/panel` | border-first, shadow minimal | `[I]` | docked panel |
| `elevation/overlay` | `[U]` | `[U]` | no overlay visible |

## 6. Iconography

| Candidate | Value | Evidence |
|---|---|---|
| Standard icon canvas | 16 × 16 | `[I]` |
| Compact icon canvas | 14 × 14 | `[I]` |
| Control hit target | 28–32 | `[I]` |
| Stroke weight | 1.5–2 | `[I]` |
| Filled status mark | 用于 success / active exceptions | `[C]` visible；rule `[I]` |

具体 icon family、license 与 source `[U]`。不得从视觉相似度直接声称使用 Lucide、Codicon 或自有图标集。

## 7. CSS 映射草案

以下只展示命名映射，不是生产值冻结稿：

```css
:root[data-theme="traecode-re-working"] {
  --bg-app: #1a1a1d;
  --bg-panel: #222327;
  --bg-control: #27272b;
  --bg-elevated: #292b2f;
  --border-default: #2d2d32;
  --text-primary: #d1d3db;
  --text-secondary: #9599a6;
  --accent-default: #80bbff;
  --status-success: #32c192;

  --space-4: 4px;
  --space-8: 8px;
  --space-12: 12px;
  --space-16: 16px;
  --radius-sm: 4px;
  --radius-md: 6px;
}
```

## 8. 后续验证顺序

1. 只在新组件确有需要时扩展 official core subset，不为追求“全量”无差别导入所有 token。
2. 对新增截图区域继续保持 raw value、official token 与 semantic role 三层分离。
3. 用代表性 Screens 与 Resize Experiments 验证现有 spacing / radius / surface token 的覆盖率。
4. Tooltip / Popover surface 与 elevation 已由官方 contract 晋级；Hover、Focus、Disabled、Error 与 overlay runtime behavior 仍必须获得交互证据或更具体合同。
5. 只有在至少两类组件稳定复用同一 screenshot candidate 时，才考虑把 candidate 晋级为 shared token。
6. 与 Askora Foundations 保持命名空间和 authority 隔离。

## 9. Figma 集成审计

- `05 Application Shell` 当前有 171 个 variable-bound nodes `[C]`；Shell 组合未新增第二套 portable alias。
- Shell text segment audit 只出现 Inter Regular / Medium 与 JetBrains Mono Regular `[C]`。Inter 仍是当前 Figma runtime 对官方 system UI font contract 的展示 fallback，不改变官方 SF Pro / SF Pro Text 来源记录。
- Status Bar 使用官方 24px component geometry `[C official]`，与截图约 21 image px `[C screenshot]` 的差异已记录为 system-consistency exception。
- Hover、Focus、Disabled、Error、Overlay elevation 仍未因 Shell 组合而晋级为 Confirmed token `[U]`。
- Table / Table Panel 已验证 `spacer-8 / 12 / 16`、`radius-4 / 8`、`bg-base-secondary / bg-layout-1`、`border-neutral-l1 / border-1`、`bg-overlay-l1`、`text-default / tertiary` 的复用关系 `[C source + implementation]`；这不确认 selection、sort、resize 或 sticky-header token `[U]`。
- Button 已验证 8 个 Text intents 与 3 个 Icon intents 对 31 个既有 official variables 的复用；96 + 36 个静态 variants 不证明 Focus、Loading、Tooltip 或 keyboard token 已存在 `[C source + implementation / U runtime]`。
- Atoms 已验证 `bg-tooltip`、Tooltip / Popover effect styles、Heading / Eyebrow styles 与 18 个 official variable bindings；静态 surface contract 不证明 trigger、placement、dismissal、focus、keyboard、transition 或 scroll affordance `[C source + implementation / U runtime]`。
