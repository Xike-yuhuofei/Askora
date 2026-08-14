# Official Component Coverage Matrix

> 状态：Research / Supporting，Phase 10 coverage baseline  
> Source：`TraeCode Copy/components/index.json` 的 24 个官方合同  
> Audit：Figma `03 Components` live Plugin API snapshot，2026-08-12

## 1. 判定规则

| Status | 含义 |
|---|---|
| Covered | 已有对应 Figma component / component set，并有截图或官方 contract 支持的 pattern composition |
| Partial | 只覆盖子组件、核心 anatomy 或截图组合；尚未覆盖完整官方 contract / variant matrix |
| Missing | 当前 Figma Library 没有该官方合同的可复用 component |

“Covered”不自动表示所有 hover、focus、disabled、accessibility 或真实应用交互已验证；它只说明 Figma Library 已有可复用核心资产。

## 2. 24-contract Matrix

| Official slug | Current Figma asset | Status | Gap / Next action |
|---|---|---|---|
| `activity-rail` | Activity Item set `45:81` + Activity Rail pattern `55:69` | Partial | 完整 rail action/divider matrix 待补 |
| `alert` | — | Missing | Agent error/warning 组件候选；只按官方 tone/layout 构建 |
| `atoms` | Badge、Status Icon、Divider、Dropdown Trigger、File Link、Inline Code | Partial | Tooltip、Popover、Empty、Code atom 等未覆盖 |
| `avatar` | Avatar Set `109:502` + Avatar Group `110:478` | Covered | image fallback chain 与 status dot 仍 `[U]` |
| `buttons` | 8 Text Button sets `137:5207`～`151:1260` + 3 Icon Button sets `156:1272` / `157:5464` / `158:5488` | Covered | 96 + 36 source-backed static variants；runtime focus/loading/accessibility 仍 `[U]` |
| `cards` | — | Missing | Dashboard / elevated surface，当前截图非优先 |
| `chat-composer` | Main Set `99:508` + Tool/Model/Send subcomponent sets | Covered | 8 source-backed variants；runtime semantics 仍 `[U]` |
| `dialog` | — | Missing | 无 modal 截图；仅可按官方 contract 建库 |
| `editor-tabs` | Editor Tab set `38:42` + Row `54:38` | Covered | 真实 keyboard/close persistence 仍 `[U]` |
| `file-tree` | Tree Item set `39:92` + File Tree `51:5` | Covered | 真实 context menu / preview behavior 仍 `[U]` |
| `forms` | — | Missing | Search/Input/Select 基础资产候选 |
| `kbd` | — | Missing | Keyboard hint / command surface 候选 |
| `menu` | — | Missing | Context Menu / Dropdown 视觉基础；真实触发行为 `[U]` |
| `nav-list` | — | Missing | 当前截图 Task Rail 不等同官方 Nav List |
| `page-header` | Reverse Panel Header `46:60` | Missing | Panel Header 不冒充官方 Page Header |
| `pagination` | — | Missing | 当前截图非优先 |
| `setting-row` | — | Missing | Settings screen 到达后优先 |
| `stat-card` | — | Missing | Dashboard，当前截图非优先 |
| `status-bar` | Status Bar set `48:139` | Covered | 真实 overflow / item priority 仍 `[U]` |
| `table` | Table Cell `116:4599` + Row `118:4618` + Table `124:687` | Covered | selection / sort / resize / pagination behavior 仍 `[U]` |
| `table-panel` | Panel Cell `125:4794` + Row `125:4813` + Panel `126:695` | Covered | sticky header / vertical scroll 仍 `[U]` |
| `tabs` | Tabs set `34:36` | Covered | 完整 interaction / accessibility 仍 `[U]` |
| `tag` | Tag Set `107:499` | Covered | 7 source-backed variants；dismiss / leading icon 仍 `[U]` |
| `workbench-titlebar` | Workbench Titlebar `49:88` | Covered | macOS native/custom chrome ownership 仍 `[U]` |

## 3. Coverage Summary

| Status | Count | Share |
|---|---:|---:|
| Covered | 11 | 45.8% |
| Partial | 2 | 8.3% |
| Missing | 11 | 45.8% |
| Total | 24 | 100% |

当前 Figma 中的 “32 Component Sets / 254 Component nodes / 34 standalone components” 不等于 24 个官方合同已覆盖。Supporting icons、reverse components 和一个官方 contract 的多个 primitive 会使节点数量高于合同覆盖数。

## 4. Build Priority

### P0 — 当前截图可见 + 官方合同明确

1. `atoms` gap：Empty / Tooltip / Popover / Code 等 source-backed primitives；
2. `buttons` 已完成，不再占用 P0 build gap；真实 interaction / accessibility verification 进入证据补充队列。

### P1 — 关键状态与 overlay 基础

1. `alert`：error / warning / success / info；
2. `menu`：Context Menu / Dropdown 的视觉 component；
3. `forms`：Input / Textarea / Select / Checkbox / Radio / Switch；
4. `kbd`。

### P2 — 需要新 Screen 证据后再优先

`cards`、`dialog`、`nav-list`、`page-header`、`pagination`、`setting-row`、`stat-card`。

优先级只决定 Figma 建库顺序，不把缺失组件解释为 TraeCode 当前截图一定使用，也不为 Askora 创造新产品能力。

## 5. Phase 8 Acceptance

Chat Composer 只有同时满足以下条件才从 Partial 提升为 Covered：

- root、input、toolbar、tools、model chip、actions、send anatomy 与官方 contract 一致；
- Empty / Filled × Claude / GPT-4o × Default / Focused 有 source-backed variants；
- Focused 只使用官方 `border-brand`；send Default / Hover 只使用官方 `bg-brand` / `bg-brand-hover`；
- bundled SVG 作为 supporting icon components，不手绘、不 detach；
- repeated controls 使用 linked subcomponent instances；
- official color / spacing / radius / typography bindings 完整；
- 0 placeholder、0 missing/duplicate authored tracking key；
- 视觉截图无裁切、重叠或默认白色 Auto Layout fill。

## 6. Phase 9 Acceptance

Table / Table Panel / Tag / Avatar 只有同时满足以下条件才提升为 Covered：

- contract 与 preview 中的 anatomy、padding、surface、radius、numeric alignment 均有对应 Figma 表达；
- Table Cell / Row 与 Table Panel Cell / Row 使用 linked component composition；
- status 只通过 inline Tag 表达，不新增整行状态底色；
- Table 提供 Bare 与 self-contained Wrapper，Table Panel 保持 squared top + external Header pairing；
- bundled SVG 用于分页箭头 supporting components，不手绘、不 detach；
- 61 / 61 Phase 9 real instances linked；
- 0 placeholder、0 missing/duplicate authored key、0 broken alias；
- selection、sort、column resize、sticky header、vertical scroll 与 pagination behavior 继续标记 `[U]`；
- visual screenshots 无裁切、重叠或透明上下文导致的错误背景。

## 7. Phase 10 Acceptance

Buttons 只有同时满足以下条件才从 Partial 提升为 Covered：

- DOM / CSS / preview 的 8 intents source conflict 已显式记录，不以较窄 JSON 列表静默删除 Secondary、Tertiary、Danger Subtle、Warning 或 Link；
- Text Button 为 8 sets / 96 variants，Icon Button 为 3 sets / 36 variants；Size 与 State 笛卡尔积无缺失或额外值；
- Icon Button 每组只包含一个 `INSTANCE_SWAP` icon property 和 Size / State variants，不为 icon 建 variant；
- Link Hover 在三个 sizes 均为 underline，并绑定官方 text token；
- Documentation Board 的 27 个 Button samples 全部 linked，Brand 恰好 1，Board 内无 Component copy；
- 632 个真实 authored nodes、400 个 bound nodes、0 placeholder、0 missing/duplicate authored key、0 broken alias；
- linked instance 虚拟内部节点不写 metadata，也不计入 authored duplicate-key audit；
- Focus、Loading、Spinner、Tooltip、keyboard activation、accessible name implementation 与 runtime transitions 继续标记 `[U]`。
