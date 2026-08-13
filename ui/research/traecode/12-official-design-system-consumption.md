# TraeCode Official Design System Consumption

> 状态：Research / Supporting  
> 来源：`TraeCode Copy/`，用户于 2026-08-11 确认为 TraeCode 官方设计系统  
> Authority：TraeCode 外部设计资产来源；不是 Askora Canonical Design 或生产实现合同

## 1. 包结构与读取顺序

| 层 | 主要文件 | 当前用途 |
|---|---|---|
| Tokens | `colors_and_type.css`、`css.json` | dark-only 颜色、字体、spacing、radius 的 source truth |
| Components | `components/*.json`、`preview/component-*.html`、`components.css` | anatomy、variants、tokens consumed 与可复制 markup |
| Icons | `assets/icons/*.svg`、`icons.js` | 115 个 bundled SVG；不得自行生成替代 icon |
| UI Kits | `ui_kits/dashboard/`、`ui_kits/dev-explorer/` | 结构展示，不复制 1184px showcase 根容器 |

消费顺序遵循包内 `library-consumption.json`：README → tokens → component index → component contract → preview；UI kit 最后只读结构。

## 2. 官方与截图证据的分工

- token 的名称与值来自官方 CSS / JSON `[C]`；
- component 的 variant dimension、anatomy、tokens consumed 来自官方 contract `[C]`；
- bundled SVG 的形状与默认 tint 来自官方 icon asset `[C]`；
- `TC-UI-001` 中某个像素区域究竟消费哪个 token，若无对应 markup/CSS 定位，仍为 `[I]`；
- window/panel 几何、当前 dock 组合与内容状态仍以 screenshot measurement 为准 `[C]`；跨尺寸行为仍为 `[U]`。

## 3. Figma 当前导入

### 3.1 Official foundations

| Collection / Style | 数量 | 说明 |
|---|---:|---|
| `TraeCode Official / Color Core` | 38 | 基础 surface、overlay、text、icon、border、status、code；含 Table / Table Panel source-backed dependencies |
| `TraeCode Official / Spacing` | 9 | `0 / 4 / 6 / 8 / 12 / 16 / 24 / 32 / 40` |
| `TraeCode Official / Radius` | 6 | `2 / 4 / 6 / 8 / 10 / full` |
| Official text styles | 12 | 原 7 个 styles + Table Header、Numeric Header、Numeric SM、Avatar XS、Avatar SM |

官方字体合同是 SF Pro Text / SF Pro 与 JetBrains Mono。当前 Figma runtime 的 SF Pro Text 不可用，且 SF Pro TextNode 出现 0px glyph width；因此 Figma 展示层使用 Inter 作为 `system-ui` fallback，JetBrains Mono 保持原样。该 fallback 不改变源 token 文档。

### 3.2 Components 与 supporting assets

Figma `03 Components` 当前包含：

- 32 个 Component Sets；
- 254 个 Component nodes；
- 34 个 standalone components；
- official bundled SVG 转换的 supporting icon components；
- Auto Layout、Variant、TEXT / INSTANCE_SWAP properties 与 Variable bindings。

旧的 screenshot-only primitive 实验没有删除，已移到 `99 Archive` 并标记 `superseded-by-official-traecode-copy`。

### 3.3 Patterns 与 Application Shell

- `04 Patterns` Board `50:2`：1440 × 1724，包含 3 个 pattern components 与 58 个 instances `[C]`；
- File Tree `51:5`、Editor Tab Row `54:38`、Activity Rail `55:69` 已完成 `[C]`；
- Docked Panel combinations 使用本地 Panel Header / Docked Panel 与官方 primitives 组合 `[C]`；
- `05 Application Shell` Board `57:2` 与 Shell Component `57:6` 已完成 `[C]`；
- Shell 为 1717 × 1299、212 nodes、61 linked instances、0 placeholder、171 variable-bound nodes `[C]`；
- Agent Main 使用截图完成态 + 官方 Chat Composer anatomy + 既有 primitives 组合；代表文案与验证块仍为 `[I]`，不是官方完整 Agent contract。

### 3.4 Screen Reconstruction

- `06 Screens` 已创建 `TraeCode RE / Screen / TC-UI-001 / Completed Review` Component `71:2` `[C]`；
- Screen 为 1717 × 1299，唯一直接子节点是指向 Shell `57:6` 的 instance `71:3`；没有复制或 detach Shell `[C]`；
- Reference Reconstruction Board `73:458` 使用原图节点 `14:289` 的 imageHash，包含 50% 并排与 50% opacity overlay `[C]`；
- Board 与 Screen 共 29 个 authored Phase 5 nodes、0 placeholder；字体保持 Inter fallback + JetBrains Mono `[C]`；
- Agent 代表文案和代码/终端内容仍为 `[I]`；Resize、Hover、Focus、Error 与完整 lifecycle 仍为 `[U]`。

### 3.5 Evidence-backed Prototype

- `07 Prototype` 已创建 State A `79:1227` 与 State B `79:1441`，两者均只包含 linked Screen `71:2` instance `[C]`；
- State A 为 `App.tsx Active / styles.css Default`，State B 为相反组合，直接使用官方 Editor Tab variants `[C]`；
- 非活动 tab 使用 `ON_CLICK → NAVIGATE` 在两个 frame 间往返；没有添加未证实的 motion transition `[C]`；
- prototype 起点为 `79:1227`；9 个 authored nodes、0 placeholder、0 duplicate idempotency key `[C]`；
- 该原型只验证 selection state composition，不证明真实应用的 persistence、keyboard order、close behavior 或 hover timing `[U]`。

### 3.6 Resize Stress Test

- `08 Experiments` 已创建 13 个 Resize sample Frames，全部只包含指向 Screen Component `71:2` 的 linked instance `[C implementation]`；
- Resize Hypothesis Board `86:3214` 为 1880 × 1140 Vertical Auto Layout，绑定官方 background / border / spacing / radius variables `[C implementation]`；
- Phase 7 live audit 为 169 个 authored nodes、0 placeholder、0 missing key、0 duplicate key `[C implementation]`；
- 当前 Figma no-overflow threshold 为 1564 × 618；1564px 时 Resource Sidebar 仅 147px，因此几何无溢出不等于 usable UX minimum `[C implementation]`；
- Candidate A（Resource Sidebar collapse）与 Candidate B（Agent Dock / Task Rail collapse）均保持 `[U]`，没有伪造成官方 behavior；
- Board 只使用 Inter fallback 文本；Shell instances 继续保留 Inter fallback + JetBrains Mono。

### 3.7 Official Chat Composer

- Color Core 新增官方 `bg-brand-hover` `VariableID:95:2` 与 `border-brand` `VariableID:95:3` `[C]`；
- 8 个 bundled SVG 已转换为 supporting icon components `96:100`～`96:131`，并绑定 official foreground tokens `[C]`；
- Tool Button `97:110`、Send Button `97:119`、Model Chip `98:140` 均为 linked subcomponent sets `[C]`；
- 主 Chat Composer Set `99:508` 包含 Empty/Filled × Claude/GPT-4o × Default/Focused 共 8 个 variants 与 Prompt TEXT property `[C]`；
- 44 / 44 nested instances linked；Phase 8 为 177 authored nodes、145 variable-bound nodes、0 placeholder、0 missing/duplicate key `[C]`；
- Documentation Board `100:332` 为 1600 × 606，4 个代表实例均指向 `99:508`，视觉验收通过 `[C]`；
- disabled send、attachment preview、keyboard submit、focus order 与 running/queued semantics 继续为 `[U]`。

### 3.8 Official Table / Table Panel

- Color Core 新增 6 个 source-backed variables；`bg-layout-1` 与 `border-1` 分别 alias 到 `bg-base-secondary` 与 `border-neutral-l1` `[C]`；
- Tag `107:499` 为 7 variants；Avatar `109:502` 为 12 variants，另有 linked Avatar Group `110:478` `[C]`；
- Table Cell `116:4599`、Table Row `118:4618` 与 Table `124:687` 建立 Bare / Wrapper composition `[C]`；
- Table Panel Cell `125:4794`、Row `125:4813` 与 standalone Panel `126:695` 保留 external Header pairing、squared top、rounded bottom 与 numeric mono 规则 `[C]`；
- Documentation Board `126:4859` 为 1200 × 1722，包含 Tag / Avatar matrices、Bare / Wrapped Table 与 Table Panel external Header example `[C]`；
- Phase 9 live audit 为 141 authored nodes、115 bound nodes、61 / 61 linked instances、0 placeholder、0 missing/duplicate key、0 broken alias `[C]`；
- Shell 中 Change Summary / Change Review 没有被误替换为 Table；selection、sort、resize、sticky header、vertical scroll 与 pagination behavior 继续为 `[U]`。

### 3.9 Official Buttons

- `buttons.json` 的 intent 列表只列 4 类，但其 DOM anatomy、官方 CSS 与 preview 明确渲染 8 类并写明 `Eight variants × three sizes × four states`；Figma 采用真实渲染证据并保留该 source conflict `[C]`；
- Text Button 建立 Primary `137:5207`、Secondary `143:1056`、Tertiary `144:1068`、Danger Strong `145:1080`、Danger Subtle `147:1140`、Warning `148:1200`、Brand `149:1236`、Link `151:1260`，共 96 variants `[C]`；
- Icon Button 建立 Primary `156:1272`、Secondary `157:5464`、Tertiary `158:5488`，共 36 variants；每组只暴露 `Icon INSTANCE_SWAP + Size + State` `[C]`；
- Link 的 3 个 Hover labels 已设置官方要求的 underline，并继续绑定 `text-default-hover` `[C]`；
- Documentation Board `160:1320` 为 1200 × 1248，27 个 Button samples 全部 linked，Brand sample 恰好 1，Board 内没有 Component copy `[C]`；
- Phase 10 live audit 为 632 个真实 authored nodes、400 个 bound nodes、31 个被消费变量、0 missing binding、0 placeholder、0 missing/duplicate authored key、0 broken alias `[C]`；
- Focus、Loading、Spinner、Tooltip、keyboard activation、accessible name implementation 与 runtime transition 继续为 `[U]`。

## 4. 复用规则

1. 保持官方 token 名称，不创建第二套长期 alias。
2. 组件先读 contract 和 preview，再组合 Figma variant；不要从 screenshot 反推已定义组件。
3. icon 优先使用 bundled SVG；brand surface 必须遵守包内 tinted variant 规则。
4. `components.css` 是生成物，不在本研究中直接编辑。
5. UI kit 的 `.uikit-shell` 和其 1184px grid 不复制到真实 Shell；只借鉴区域组合。
6. screenshot candidate collections 只用于视觉差异与未覆盖问题，不作为 official component 默认依赖。
7. TraeCode 资产进入 Askora 前仍须通过 Askora Product / Design / ADR / Spec adoption gate。

## 5. 剩余未完整导入 / 验证范围

- 完整 color token 全量，而非当前 core subset；
- 24 个官方 component contract 的完整 Figma library；当前 coverage 为 11 Covered / 2 Partial / 11 Missing；
- 非 Button 组件的 Hover / Active / Disabled 全矩阵，以及全局 Focus / Loading / keyboard state；
- 独立可发布的 Agent Result Block、Change Review Bar 与完整 Agent lifecycle variants；Chat Composer 已完成；
- 真实应用的 Resize / Collapse / Split 行为与可验证 prototype；Figma implementation stress test 已完成；
- 真实应用交互、resize persistence 与 accessibility 行为验证。

这些是后续阶段范围，不因官方包存在而自动宣称已完成。
