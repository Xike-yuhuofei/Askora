# Component System 与 Component Map

> 状态：Research / Supporting，候选 taxonomy  
> 当前总数：52 个候选组件类型、7 类 `[I]`  
> 注意：这是审计与构建清单，不代表 Figma 已创建 52 个 Components

## 0. 官方组件来源与当前 Figma 状态

`TraeCode Copy/components/` 现为已确认的官方 component contract 来源 `[C]`。截图 taxonomy 仍用于判断当前画面出现了哪些结构；当官方 contract 已覆盖同一 primitive 时，以官方 anatomy、variant dimensions、tokens consumed 与 bundled icons 为准。

`03 Components` 已建立首批 official core primitives `[C]`：

| 用户组件 | Figma 结构 | 官方来源 |
|---|---|---|
| Icon Button | Phase 10 前的 screenshot primitive；已由 source-backed 3 intent × 3 size × 4 state sets supersede | `buttons.json` + `component-buttons.html` |
| Text Button | Phase 10 前的 screenshot primitive；已由 source-backed 8 intent × 3 size × 4 state sets supersede | 同上 |
| Badge | 2 variants：Default/Success | `tag.json` + `component-tag.html` |
| Status Icon | 2 variants：Success/Running | official status tokens |
| Dropdown Trigger | 1 component | `forms.json` + `.ds-select` |
| Divider | 2 variants：Horizontal/Vertical | `menu.json` + `.ds-menu__divider` |
| File Link | 1 component | official `code-link` + bundled `file.svg` |
| Inline Code | 1 component | `atoms.json` + `.ds-code` subset |

Phase 9 进一步完成以下 source-backed data-display 资产 `[C implementation]`：

| 资产 | Figma ID | 结构 |
|---|---|---|
| Tag | `107:499` | 7 tone variants |
| Avatar | `109:502` | Size × Shape × Tone = 12 variants |
| Avatar Group | `110:478` | 3 linked avatars + overflow chip |
| Table Cell | `116:4599` | Header / Text / Numeric / Avatar+Text / Tag / Action |
| Table Row | `118:4618` | Header / Body |
| Table | `124:687` | Bare / Wrapper |
| Table Panel Cell | `125:4794` | Header / Header Numeric / Text / Numeric |
| Table Panel Row | `125:4813` | Header / Body |
| Table Panel | `126:695` | panel body + separate footer；external Header 由 pattern 组合 |

Phase 10 完成 source-backed Button Library `[C implementation]`：

| 资产 | Figma ID | 结构 |
|---|---|---|
| Text Button | `137:5207`～`151:1260` | 8 个 intent sets；每组 Size × State = 12 variants，共 96 |
| Icon Button | `156:1272`、`157:5464`、`158:5488` | Primary / Secondary / Tertiary；每组 12 variants，共 36 |
| Button Documentation | `160:1320` | 27 个 linked Button samples；Brand 恰好 1 |

Phase 11 完成 source-backed Atoms `[C implementation]`：

| 资产 | Figma ID | 结构 |
|---|---|---|
| Tooltip | `171:1416` | `Text` property + official Tooltip effect |
| Popover Surface | `172:1416` | transparent `Content SLOT` + official Popover effect |
| Empty State | `175:1416` | `Title`、`Description`、`Icon INSTANCE_SWAP`；无 CTA |
| Code Block | `176:1421` | `Code` property + Code / Editor style |
| Atoms Documentation | `177:1421` | 5 linked samples、Typography / Utility specimens、Evidence / Scope |

Heading、Eyebrow 与 mono/num 使用 Text Styles；row/col/grid/stack 保持 Auto Layout recipes，不创建 pseudo-components。当前 `03 Components` live audit 总计 32 个 Component Sets、258 个 Component nodes 与 38 个 standalone components。Supporting icons 与可发布组件都计入 Figma 节点总数，但不等同于 24 个官方合同全部覆盖。

## 1. Taxonomy Summary

| 分类 | 数量 | 作用 |
|---|---:|---|
| Shell & Panels | 8 | 窗口、一级 dock、panel chrome 与 status |
| Navigation & Organization | 9 | workspace、mode、task、tab、breadcrumb、tree |
| Workspace & Content | 7 | resource、preview、toolbar、code/data presentation |
| Agent Workflow | 10 | run stream、结果、变更审阅与 composer context |
| Inputs & Actions | 8 | buttons、selectors、search/filter、composer、submit |
| Feedback & Overlay | 6 | badge、status 与 overlay candidates |
| State & Utility | 4 | loading、progress、empty、error |
| **Total** | **52** | 作为下一阶段去重与变体审计基线 |

## 2. 候选组件清单

### 2.1 Shell & Panels — 8

| # | Component | Evidence | 说明 |
|---:|---|---|---|
| 1 | App Window | `[C]` | 完整 window frame |
| 2 | Top Region | `[C]` | workspace / mode / window actions 的共享高度区 |
| 3 | Agent Dock | `[C]` | Task Rail + Agent Main |
| 4 | Workbench | `[C]` | Editor + Resource + Bottom + Status |
| 5 | Docked Panel | `[C]` | 多个占位型 panel surface 可抽象 |
| 6 | Panel Header | `[C]` | Resource、Bottom、Agent 子区存在不同 header |
| 7 | Resize Divider | seam `[C]`；drag semantics `[I]` | 不能把可见 border 自动当作可拖拽组件 |
| 8 | Status Bar | `[C]` | Workbench 底部状态汇总 |

### 2.2 Navigation & Organization — 9

| # | Component | Evidence | 说明 |
|---:|---|---|---|
| 9 | Workspace Switcher | `[C]` | Askora + dropdown |
| 10 | Product Mode Tab | `[C]` | Editor / Browser / Settings / Code Changes |
| 11 | New Task Action | `[C]` | 带 icon、label、shortcut |
| 12 | Task List Item | `[C]` | title、status、time、selected/completed |
| 13 | Editor Tab | `[C]` | file type、title、close、active |
| 14 | Breadcrumb | `[C]` | path / document context |
| 15 | Panel Tab | `[C]` | Problems / Output / Terminal / Ports / Debug Console |
| 16 | Tree Item | `[C]` | folder/file、level、selected |
| 17 | Tree Expander | `[C]` | expanded/collapsed chevron state visible |

### 2.3 Workspace & Content — 7

| # | Component | Evidence | 说明 |
|---:|---|---|---|
| 18 | Resource Tree | `[C]` | hierarchical file content |
| 19 | Markdown Preview | `[C]` | heading、body、quote、code/table |
| 20 | Editor Toolbar | `[C]` | Edit / Preview / Markdown / secondary actions |
| 21 | Code Block | `[C]` | 截图内容区可见 code presentation；official atom 只确认 pre-like surface，language / line numbers / copy behavior 仍需独立证据 |
| 22 | Data Table | `[C]` | Agent result tables |
| 23 | File Link | `[C]` | blue monospaced file references |
| 24 | Inline Code | `[C]` | muted chip-like inline code surface |

### 2.4 Agent Workflow — 10

| # | Component | Evidence | 说明 |
|---:|---|---|---|
| 25 | Conversation Stream | `[C]` | 纵向滚动运行/结果内容 |
| 26 | Conversation Message | visible content `[C]`；message boundary `[I]` | 当前无典型 bubble 边界 |
| 27 | Agent Result Block | `[C]` | 结果 section / summary |
| 28 | Completion Indicator | `[C]` | success icon + completion text |
| 29 | Change Summary | `[C]` | changed files + insertions/deletions |
| 30 | File Change Table | `[C]` | changed/new/test file group |
| 31 | Diff Stat | `[C]` | `+256 -216` 统计 |
| 32 | Change Review Bar | `[C]` | pending count + discard/keep decisions |
| 33 | Agent Identity Row | `[C]` | `@Agent` + status/actions |
| 34 | Composer Context Row | `[C]` | mention / attach / mode / model / voice controls |

### 2.5 Inputs & Actions — 8

| # | Component | Evidence | 说明 |
|---:|---|---|---|
| 35 | Icon Button | `[C]` | 多区域高频 primitive |
| 36 | Text Button | `[C]` | 查看变更、全部撤销、全部保留 |
| 37 | Segmented Control | `[C]` | Edit / Preview 等紧凑模式切换 |
| 38 | Dropdown Trigger | `[C]` | workspace、language、server、model |
| 39 | Search Field | search affordance `[C]`；field state `[I]` | 当前多处仅显示 icon |
| 40 | Filter Field | `[C]` | Bottom Panel filter input |
| 41 | Prompt Composer | `[C]` | multiline input container |
| 42 | Primary Submit Button | `[C]` | composer green send control |

### 2.6 Feedback & Overlay — 6

| # | Component | Evidence | 说明 |
|---:|---|---|---|
| 43 | Badge | `[C]` | task count、status counters |
| 44 | Status Icon | `[C]` | completed/running/warning-like states |
| 45 | Tooltip | screenshot `[U]`；official atom `[C]` | 静态 surface 已建；trigger / delay / placement / focus `[U]` |
| 46 | Popover | screenshot `[U]`；official atom `[C]` | 静态 slot surface 已建；anchor / placement / dismissal `[U]` |
| 47 | Context Menu | `[U]` | task/tree/editor menu 未显示 |
| 48 | Toast | `[U]` | transient feedback 未显示 |

### 2.7 State & Utility — 4

| # | Component | Evidence | 说明 |
|---:|---|---|---|
| 49 | Loading Indicator | `[C]` | Cue-Pro `分析中...` |
| 50 | Progress Indicator | `[C]` | Agent footer `64%` / file analysis status |
| 51 | Empty State | screenshot `[U]`；official atom `[C]` | 静态 icon/title/description 已建；业务选择与 CTA policy `[U]` |
| 52 | Error State | `[U]` | 有 error/warning counters，但无完整 error surface |

## 3. Evidence Distribution

| Evidence | 数量 | 含义 |
|---|---:|---|
| 可见 component type `[C]` | 43 | 截图中存在对应视觉结构；variants 未必确认 |
| 结构推断 `[I]` | 3 | seam / message / search 需要语义拆分 |
| 缺失但应审计 `[U]` | 6 | overlay、empty、error 等必须补图后再建完整组件 |

整个 taxonomy 仍标记为 `[I]`，因为“如何拆成可维护 Figma component”的选择不是截图事实。

## 4. Variant / Property 候选

| Component | Candidate variants / properties | 当前证据 |
|---|---|---|
| Icon Button | Size=SM/MD/LG；State=Default/Hover/Active/Disabled；Icon swap | 四种静态 source-backed states `[C]`；focus/tooltip/keyboard/runtime behavior `[U]` |
| Text Button | 8 intents；Size=SM/MD/LG；State=Default/Hover/Active/Disabled；label / leading / trailing icon properties | 96 个静态 source-backed variants `[C]`；focus/loading/runtime behavior `[U]` |
| Task List Item | selected, completion status, title, timestamp | default + selected + completed `[C]`；running/error `[U]` |
| Product Mode Tab | active, label, icon, badge | active/inactive `[C]`；hover/focus `[U]` |
| Editor Tab | active, dirty, pinned, closeable, file icon | active/closeable `[C]`；dirty/pinned `[U]` |
| Tree Item | level, expanded, selected, kind, status | level/expanded/selected/kind `[C]`；hover/focus `[U]` |
| Panel Tab | active, badge, label | active/inactive `[C]`；closeable `[U]` |
| Agent Result Block | kind, status, expandable | result groups `[C]`；expand/collapse `[U]` |
| Change Review Bar | pending count, decision state | pending `[C]`；accepted/reverted/partial `[U]` |
| Prompt Composer | empty, has-context, running, disabled, error | filled chrome `[C]`；lifecycle variants `[U]` |
| Status Bar | item kind, status, icon, progress | multiple item kinds `[C]`；overflow behavior `[U]` |

## 5. 构建顺序

1. **Foundations experiment**：raw colors、semantic aliases、spacing、radius、type samples。
2. **Primitives**：Icon Button、Text Button 已完成 source-backed library；继续 Badge、Status Icon、Divider、Dropdown Trigger 的官方合同收敛。
3. **Navigation**：Product Mode Tab、Editor Tab、Panel Tab、Tree Item、Task List Item。
4. **Panels**：Panel Header、Docked Panel、Status Bar、reference Resize Divider。
5. **Content**：Code Block、Data Table、File Link、Inline Code、Markdown Preview wrappers；Table / Table Panel 已完成 source-backed library。
6. **Agent**：Result Block、Change Summary、Review Bar、Composer Context Row、Prompt Composer。
7. **Patterns**：Task→Result→Review→Composer、Editor→Resource→Diagnostics。
8. **Shell**：只用 instances 组合 reference Application Shell。

## 5.1 Figma 当前实现状态

| 资产层 | 当前结果 | 说明 |
|---|---:|---|
| Component Sets | 32 | Phase 9 的 21 sets + Phase 10 的 8 个 Text Button sets 与 3 个 Icon Button sets `[C]` |
| Component nodes | 258 | 原 254 个节点 + Phase 11 的 4 个 standalone Atoms `[C]` |
| Standalone components | 38 | 原 34 个 + Tooltip / Popover Surface / Empty State / Code Block `[C]` |
| Pattern components | 3 | File Tree `51:5`、Editor Tab Row `54:38`、Activity Rail `55:69` `[C]` |
| Pattern instances | 58 | `04 Patterns` Board `50:2` live audit `[C]` |
| Application Shell | 1 | Component `57:6`；61 个 linked instances、0 placeholder `[C]` |

上述数量是已建 Figma 资产，不替代 52 个候选 component type taxonomy；候选类型可能合并、延后或在更多截图后重新拆分。Official Chat Composer、Table、Table Panel、Tag、Avatar、Button 与 Atoms 已提升为可复用资产；Agent Result Block 与 Change Review Bar 仍只是 Shell 组合，尚未成为独立可发布组件 `[C current state]`。

## 6. Figma 组件规则

- 使用 Auto Layout 表达内容驱动尺寸；只有截图 overlay 对齐、icon optical alignment 等场景允许局部 absolute positioning。
- icon 使用 Instance Swap；label、badge、shortcut、description 用 component properties。
- 先建立可证实的 states；Hover、Focus、Disabled、Error 可以预留 property schema，但视觉值保持未冻结。
- 不为每个 panel 复制一套 Button / Tab；共享 primitive 通过 semantic role 或 context property 组合。
- 不 detached instances 追求局部像素；差异进入 `08 Experiments` 并判断是 token exception 还是错误拆分。
- Resize shell 使用 reference variants / experiments，不声称 Figma prototype 等同真实布局引擎。

## 7. 去重风险

- `Data Table` 与 `File Change Table` 可能共享 table primitive，但 Agent 语义和密度不同 `[I]`。
- `Product Mode Tab`、`Editor Tab`、`Panel Tab` 不应立即合并成万能 Tab；它们的层级、close/badge 与 hit area 不同 `[C]`。
- `Task List Item` 不是普通 Sidebar Item；它承载两行任务状态和时间 `[C]`。
- `Completion Indicator`、`Status Icon`、`Loading Indicator` 可以共享 icon primitive，但状态语义不可被单一颜色属性吞掉 `[I]`。
- `Conversation Message` 的边界当前不清晰，需更多 user/assistant/tool screenshots 才能决定是否为独立 bubble component `[U]`。
