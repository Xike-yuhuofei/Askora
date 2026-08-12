# Implementation Handoff — 第一轮与 Official Core 更新

> 状态：Research / Supporting，非生产实现合同  
> 面向：下一阶段 Figma Prototype / Resize Experiments、前端架构评估  
> Authority：任何进入 Askora 的行为必须先由 Askora current Product / Design / ADR / Specs 接受

## 1. Handoff Snapshot

| 项目 | 当前结果 |
|---|---|
| Source screenshots | 1 |
| Confirmed reference size | 1717 × 1299 image px |
| FigJam | [TraeCode UI Reverse Engineering](https://www.figma.com/board/mPKPm5h5j1WJxsv74Td3wK) |
| Figma Design | [TraeCode Reverse Engineering UI](https://www.figma.com/design/fWWjzmyWfZojb0P0vcwyD3) |
| FigJam sections | 8 |
| Figma pages | 10 |
| Candidate component types | 52 / 7 categories `[I]` |
| Official source | `TraeCode Copy/`：tokens / 24 component contracts / 115 SVG icons / 2 showcase UI kits `[C]` |
| Figma foundations | 3 official collections / 54 variables / 16 official text styles / 2 official effect styles；另保留 screenshot candidates `[C]` |
| Figma components | 32 Component Sets / 258 Component nodes / 38 standalone components `[C]` |
| Official Buttons | 8 Text Button sets / 96 variants；3 Icon Button sets / 36 variants；Board `160:1320` `[C implementation]` |
| Official Atoms | Tooltip `171:1416`、Popover `172:1416`、Empty `175:1416`、Code Block `176:1421`；Board `177:1421` `[C implementation]` |
| Figma patterns | 3 pattern components / 58 instances；Board `50:2` `[C]` |
| Figma Application Shell | Component `57:6`；1717 × 1299；212 nodes / 61 linked instances / 0 placeholder `[C]` |
| Figma Screens | `TC-UI-001` Component `71:2`；Reference Reconstruction Board `73:458`；29 authored Phase 5 nodes / 0 placeholder `[C]` |
| Prototype | Editor Tab A/B selection；2 reactions；起点 `79:1227`；9 authored nodes / 0 placeholder `[C]` |
| Resize Experiments | 13 linked Screen samples；Board `86:3214`；169 authored Phase 7 nodes / 0 placeholder `[C implementation]` |
| Primary unresolved area | real resize/collapse contract、dynamic state、overlay、accessibility |

## 2. Reference Layout Handoff

| Component | Width | Height | Min | Max | Padding / Gap | Behavior |
|---|---:|---:|---:|---:|---|---|
| Window | 1717 `[C]` | 1299 `[C]` | `[U]` | `[U]` | 0 | reference only |
| Top Region | fill `[C]` | ≈41 `[C]` | `[U]` | `[U]` | segmented by dock `[C]` | likely fixed height `[I]` |
| Task Rail | 255 `[C]` | body fill `[C]` | `[U]` | `[U]` | outer ≈12 `[C]`; item gap ≈8 `[C]` | scroll `[I]`; resize/collapse `[U]` |
| Agent Main | 520 `[C]` | body fill `[C]` | `[U]` | `[U]` | content ≈16 `[I]` | vertical stream `[I]`; resize `[I]` |
| Workbench | 942 `[C]` | body fill `[C]` | `[U]` | `[U]` | 0 | primary fill container `[I]` |
| Editor Column | 642 `[C]` | to status `[C]` | `[U]` | fill `[I]` | content-specific | primary flex candidate `[I]` |
| Resource Sidebar | 300 `[C]` | to status `[C]` | `[U]` | `[U]` | dense rows 8–12 `[I]` | docked `[C]`; resize/collapse `[I]` |
| Bottom Panel | editor width `[C]` | 330 `[C]` | `[U]` | `[U]` | tab strip ≈36–38 `[C]` | internal scroll `[I]`; vertical resize `[I]` |
| Status Bar | workbench width `[C]` | 21 screenshot `[C]` / 24 Figma official component `[C]` | `[U]` | `[U]` | compact inline `[I]` | not under Agent Dock `[C]`; 24px is documented system-consistency exception |

所有尺寸均是 screenshot reference，不得命名为 `defaultWidth`，直到多尺寸证据完成。

### 2.1 Current Figma Stress-test Constraints

| Item | Current implementation | Interpretation |
|---|---|---|
| Agent Dock | fixed 775 | `[C implementation]`，不是 TraeCode official default |
| Task Rail | fixed 255 | `[C implementation]` |
| Editor Column | fixed 642 | `[C implementation]` |
| Resource Sidebar | absorbs Workbench compression | `[C implementation]` |
| Horizontal no-overflow threshold | 1564 | scenegraph threshold，不是 usable UX min |
| Vertical no-overflow threshold | 618 | scenegraph threshold，不是 official min height |
| Structural hard failure | total width < 1417 | Workbench 小于 fixed Editor 642 |
| Collapse order | none implemented | TraeCode behavior `[U]` |

这些读数用于暴露当前 Auto Layout 约束；前端不得映射为 `min-width: 1564px` 或 production breakpoint。完整证据见 [Resize Stress Test](15-resize-stress-test.md)。

## 3. Token Handoff

以下 JSON 是第一轮 screenshot candidate，已被官方来源降级，不再作为默认 component token：

```json
{
  "$status": "working-hypothesis",
  "$authority": "research-supporting",
  "color": {
    "bg.app": "#1A1A1D",
    "bg.panel": "#222327",
    "bg.control": "#27272B",
    "bg.elevated": "#292B2F",
    "border.default": "#2D2D32",
    "text.primary": "#D1D3DB",
    "text.secondary": "#9599A6",
    "accent.default": "#80BBFF",
    "status.success": "#32C192"
  },
  "space": [2, 4, 6, 8, 12, 16, 24, 32],
  "radius": {
    "s": 4,
    "m": 6,
    "l": 8
  }
}
```

Raw sampled values 与 semantic alias 应分层；`hover`、`focus`、`error`、`overlay elevation` 暂不设正式值。

当前 Figma component 优先消费 `TraeCode Official / Color Core`、`Spacing`、`Radius`。变量名称保持官方 CSS 名称，例如 `bg-base-default`、`text-default`、`border-neutral-l1`、`spacer-12`、`radius-4`；不创建第二套 portable alias。

## 4. Component Build Queue

### Batch 1 — Official core primitives（已完成）

- Icon Button
- Text Button
- Badge
- Status Icon
- Dropdown Trigger
- Divider / seam reference
- File Link
- Inline Code

### Batch 2 — Navigation / Panels

- Product Mode Tab
- Task List Item
- Editor Tab
- Panel Tab
- Tree Item / Tree Expander
- Panel Header / Docked Panel
- Status Bar

### Batch 3 — Agent

- Agent Result Block
- Completion Indicator
- Change Summary / Diff Stat
- File Change Table
- Change Review Bar
- Agent Identity Row
- Composer Context Row
- Prompt Composer

### Batch 4 — Official data display（已完成）

- Tag / Avatar / Avatar Group
- Table Cell / Table Row
- Table Bare / Wrapper
- Table Panel Cell / Row / Panel
- External Header pairing pattern

### Batch 5 — Official Buttons（已完成）

- Primary / Secondary / Tertiary
- Danger Strong / Danger Subtle / Warning
- Brand / Link
- Text Button：8 intents × SM/MD/LG × Default/Hover/Active/Disabled
- Icon Button：Primary/Secondary/Tertiary × SM/MD/LG × Default/Hover/Active/Disabled
- Button Group 与每页最多一个 Brand CTA 的 composition rule

### Deferred until evidence

- Tooltip / Popover / Context Menu / Toast
- Empty / Error states
- full Agent running / tool / approval variants
- formal Resize Divider behavior
- command palette / multi-editor split patterns

## 5. Frontend Architecture Mapping — Candidate

```text
AppWindow
├── TopRegion
└── AppBody
    ├── AgentDock
    │   ├── TaskRail
    │   └── AgentWorkspace
    │       ├── AgentStream
    │       ├── ChangeReview
    │       └── PromptComposer
    └── Workbench
        ├── WorkbenchBody
        │   ├── EditorColumn
        │   │   ├── EditorChrome
        │   │   ├── EditorContent
        │   │   └── BottomPanel
        │   └── ResourceSidebar
        └── StatusBar
```

这是布局组件边界候选 `[I]`，不定义数据 owner、API、store 或 persistence。前端实现前仍需冻结：panel state ownership、agent run/review state、resource/editor selection sync、resize persistence 与 error contracts。

## 6. Figma Execution Plan

1. `01 References`：放置原图与测量 overlay，记录 scale。
2. `02 Foundations`：official source 为主；screenshot candidates 独立命名并仅用于视觉对照。
3. `03 Components`：Batch 1、Official Chat Composer、Batch 4 data display 与 Batch 5 official Buttons 已完成；其余 Batch 2→3 继续使用 Auto Layout、Variants、Properties、Instance Swap 与 official bundled icons。
4. `04 Patterns`：已完成 File Tree、Editor Tab Row、Activity Rail 与 Docked Panel combinations；继续补 Agent reusable patterns。
5. `05 Application Shell`：已完成 reference Shell、Agent/Workbench 两级 dock、完成态 Review 与 Composer 组合。
6. `06 Screens`：已完成 `TC-UI-001`；Screen Component `71:2` 仅包含 linked Shell instance，并建立 50% Reference / Reconstruction 并排与 overlay 校验。
7. `07 Prototype`：已完成 Editor Tab selection A/B 往返；待补证后再做 resize、Agent lifecycle、overlay 与 keyboard focus。
8. `08 Experiments`：已完成 13 个 Resize stress samples 与 Hypothesis Board；Candidate A/B 只记录为 `[U]`，待真实证据后再制作交互原型。
9. `99 Archive`：保留被否定假设，不让它们混入 current working set。

## 7. Visual Validation Gate

下一阶段每批组件至少通过：

- 1717 × 1299 reference overlay；
- 一级边界偏差不超过 1 image px；
- shared chrome / row / padding 系统性偏差有记录；
- instances 未 detached；
- Auto Layout resize 不发生意外重叠；
- `[C]` / `[I]` / `[U]` annotation 保留；
- pixel accuracy 与 system consistency 冲突时，优先 system consistency 并记录 exception；
- Figma prototype 结论与真实应用交互证据分开。

## 8. Askora Adoption Gate

TraeCode pattern 进入 Askora 前，必须逐项回答：

1. 它服务 Askora Product Strategy 中的 primary user / problem / outcome 吗？
2. 它是否保持 Local Web、single-user、local-first、BYOK 等 Product Positioning 边界？
3. 它对应哪个 Askora Product Capability / Rule / Requirement / Acceptance？
4. 它是否遵守 `Left = Where / Center = Learn / Right = Reference & Notes` 的 current experience model？
5. 它是否只是视觉借鉴，还是会改变公共交互语义、state owner、API 或 schema？
6. 若改变共享语义，是否先完成 Canonical Design / ADR / Spec / EXEC 闭环？

未经过以上 gate，本目录不得作为开发者“照图实现 Askora Desktop IDE”的依据。

## 9. 当前完成条件

- Screenshot inventory、IA、Shell、Panel、Layout、Tokens、Components、Interaction、State、Resize、Questions 与 Handoff 均已形成文档；
- FigJam 8 Sections 与 Figma Design 10 Pages 已实际创建；
- 原截图已纳入仓库并以 SHA-256 校验；
- Foundations、32 个 Component Sets、254 个 Component nodes、34 个 standalone components、3 个 Patterns、reference Application Shell、`TC-UI-001` Screen 与基础 Editor Tab Prototype 已完成并通过 live metadata / screenshot 验收；
- Shell audit 为 212 nodes、61 linked instances、0 placeholder、0 detached-like instance、171 variable-bound nodes；
- Screen audit 为 1717 × 1299、唯一 Shell child instance、29 authored Phase 5 nodes、0 placeholder；两个 Reference 图层与 `14:289` 使用同一 imageHash；
- Prototype audit 为两个 1717 × 1299 linked Screen states、2 个双向 ON_CLICK NAVIGATE reactions、9 authored Phase 6 nodes、0 placeholder；真实应用 resize contract 与完整 Agent lifecycle 仍未伪完成；
- Resize audit 为 13 个 linked Screen samples、169 authored Phase 7 nodes、0 placeholder、0 missing/duplicate key；1564 × 618 仅记录为 Figma no-overflow threshold，真实 TraeCode resize/collapse 仍未伪完成；
- Chat Composer audit 为 8 个主 variants、44 / 44 linked nested instances、177 authored Phase 8 nodes、145 variable-bound nodes、0 placeholder、0 missing/duplicate key；disabled / attachment / keyboard / running 语义仍保持 `[U]`；
- Table / Table Panel audit 为 141 authored Phase 9 nodes、115 variable-bound nodes、61 / 61 linked instances、0 placeholder、0 missing/duplicate key、0 broken alias；selection / sort / column resize / sticky header / vertical scroll / pagination behavior 仍保持 `[U]`；
- Button audit 为 8 / 96 Text Button sets / variants、3 / 36 Icon Button sets / variants、632 个真实 authored nodes、400 个 variable-bound nodes、27 个 linked documentation samples、1 个 Brand sample、0 placeholder、0 missing/duplicate key、0 broken alias；Focus / Loading / Tooltip / keyboard / runtime transitions 仍保持 `[U]`；
- 所有跨截图动态规则保持 `[I]` / `[U]`；
- Askora canonical authority boundary 已显式声明。
