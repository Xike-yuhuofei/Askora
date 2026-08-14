# TraeCode UI Reverse Engineering — 阶段性概览

> 状态：Research / Supporting，阶段性设计资产基线  
> 证据日期：2026-08-12  
> 证据范围：1 张静态截图 + 用户提供的 TraeCode 官方 Design System 本地包 + 13 个 Figma implementation stress samples + source-backed Chat Composer、Table / Table Panel、Button 与 Atoms Figma Library；不包含可交互应用或真实多窗口截图  
> Authority：本目录是外部 UI 研究输入，不是 Askora Canonical Experience、UI Spec 或 Design System 的替代来源

## 1. 目标与边界

本轮从 TraeCode 截图恢复可继续验证的 UI 架构假设，先完成素材盘点、Information Architecture、Application Shell、Panel Architecture、Component Map、Token 假设与 Open Questions，再进入 Figma Foundations 和 Components。

本轮明确不做：

- 不把单张截图复刻成不可维护的单一高保真 Frame；
- 不把 TraeCode 的 Desktop IDE Shell 直接移植为 Askora 产品 Shell；
- 不从静态截图声称已确认 Hover、Focus、Resize、Collapse、Split 或键盘交互；
- 不把截图推断 token 冒充官方 token；官方包到达后，优先消费其 token、component contract 与 bundled icons；
- 不以工程或 Figma 资产存在性声称 Askora Product / UX Acceptance 已满足。

## 2. 证据等级

| 标记 | 含义 | 使用规则 |
|---|---|---|
| `[C] Confirmed` | 截图像素或截图中可见状态直接支持 | 只确认当前截图，不外推到其他窗口或状态 |
| `[I] Inferred` | 由重复视觉规律、容器边界或 IDE 模式推导 | 必须保留验证条件，不能作为冻结实现合同 |
| `[U] Unknown` | 当前证据不足 | 不用静默脑补填补 |

证据等级绑定到具体结论，而不是绑定到整份文档。同一组件的当前宽度可以是 `[C]`，其默认宽度、最小宽度和拖拽行为仍可能是 `[U]`。

## 3. 第一轮交付物

| 交付物 | 状态 | 说明 |
|---|---|---|
| [Screenshot Inventory](01-screenshot-inventory.md) | 已完成 | 1 张截图、文件哈希、场景与可见状态 |
| [Information Architecture](02-information-architecture.md) | 已完成 | 全局模式、任务/Agent、编辑器、资源与诊断域 |
| [Application Shell](03-application-shell.md) | 已完成 | 当前 Shell 容器树与 Panel Architecture |
| [Layout System](04-layout-system.md) | 已完成 | 截图坐标测量、重复间距与尺寸假设 |
| [Design Tokens](05-design-tokens.md) | 已完成初稿 | Semantic Token 候选，不是正式 Askora Token |
| [Component System](06-component-system.md) | 已完成初稿 | 52 个候选组件类型，分为 7 类 |
| [Interaction Model](07-interaction-model.md) | 已完成初稿 | 静态状态与交互假设分离 |
| [State Model](08-state-model.md) | 已完成初稿 | 可见 Agent / Editor / Panel 状态与缺口 |
| [Responsive / Resize Rules](09-responsive-resize-rules.md) | 已完成 implementation stress test | 当前 Figma 约束已测量；真实跨尺寸规则仍待验证 |
| [Open Questions](10-open-questions.md) | 已完成 | 按阻塞级别列出补证计划 |
| [Implementation Handoff](11-implementation-handoff.md) | 已完成第一轮 | 可供下一阶段 Figma/前端映射的非规范性输入 |
| [Official Design System Consumption](12-official-design-system-consumption.md) | 已完成 | 官方包读取顺序、Figma 导入范围、复用与 showcase 边界 |
| [Screen Reconstruction](13-screen-reconstruction.md) | 已完成 `TC-UI-001` | linked Screen component、Reference 对照、50% overlay 与偏差台账 |
| [Prototype Validation](14-prototype-validation.md) | 已完成基础交互 | Editor Tab selection A/B、往返 click navigation 与证据边界 |
| [Resize Stress Test](15-resize-stress-test.md) | 已完成 Phase 7 | 13 个 linked Screen samples、Resize Board、阈值与失效模型 |
| [Official Component Coverage](16-official-component-coverage.md) | 已完成 Phase 10 coverage baseline | 24 个官方合同：11 Covered / 2 Partial / 11 Missing |
| [Official Chat Composer](17-chat-composer-component.md) | 已完成 Phase 8 | 8 个主变体、3 个 linked subcomponent sets、8 个 bundled SVG components |
| [Official Table / Table Panel](18-table-table-panel-components.md) | 已完成 Phase 9 | Table / Table Panel / Tag / Avatar source-backed library、展示板与 live audit |
| [Official Buttons](19-button-components.md) | 已完成 Phase 10 | 8 个 Text Button sets / 96 variants、3 个 Icon Button sets / 36 variants、linked documentation board 与 live audit |
| [Official Atoms](20-official-atoms.md) | 已完成 Phase 11 | Tooltip、Popover Surface、Empty State、Code Block、Typography / Utility specimens 与 live audit |

## 4. 实际 Figma 资产

- [TraeCode UI Reverse Engineering — FigJam](https://www.figma.com/board/mPKPm5h5j1WJxsv74Td3wK)：已创建 8 个分析 Section，并已上传原始截图 `[C]`。
- [TraeCode Reverse Engineering UI — Figma Design](https://www.figma.com/design/fWWjzmyWfZojb0P0vcwyD3)：已创建 10 个 Pages 与 Cover；`01 References` 至 `08 Experiments` 已有实际资产 `[C]`。

FigJam 当前 Sections：

1. Screenshot Inventory
2. Information Architecture
3. Application Shell
4. Panel Architecture
5. Component Map
6. Interaction Model
7. State Model
8. Open Questions

Figma Design 当前 Pages：

```text
00 Cover
01 References
02 Foundations
03 Components
04 Patterns
05 Application Shell
06 Screens
07 Prototype
08 Experiments
99 Archive
```

### 4.1 Figma live audit snapshot

| 区域 | 当前结果 | 证据 |
|---|---|---|
| `03 Components` | 32 个 Component Sets、254 个 Component nodes、34 个 standalone components；Phase 10 Button 为 632 个真实 authored nodes、400 个 bound nodes、27 个 linked documentation samples、0 placeholder、0 missing/duplicate key、0 broken alias | Figma Plugin API live audit `[C]` |
| Phase 11 Atoms | 4 个 standalone components；Board `177:1421` 为 1200 × 2186；92 authored nodes、90 bound nodes、5 linked documentation samples、0 placeholder、0 missing/duplicate key、0 unbound solid paint、0 clipped text | Figma Plugin API + screenshot live audit `[C]` |
| `04 Patterns` | 3 个 pattern components、58 个 instances；Board `50:2` 为 1440 × 1724 | Figma Plugin API live audit `[C]` |
| `05 Application Shell` | Shell Component `57:6` 为 1717 × 1299；212 个节点、61 个 linked instances、0 placeholder | Figma Plugin API live audit `[C]` |
| Shell 字体 | Inter fallback + JetBrains Mono；没有其他字体 family | Figma text segment audit `[C]` |
| `06 Screens` | Screen Component `71:2` 为 1717 × 1299，内部唯一子节点为 linked Shell instance `71:3`；Reference Board `73:458` 为 1880 × 1935 | Figma Plugin API live audit `[C]` |
| `07 Prototype` | State A `79:1227` / State B `79:1441`；2 个 ON_CLICK NAVIGATE reactions；9 个 authored nodes、0 placeholder | Figma Plugin API live audit `[C]` |
| `08 Experiments` | 13 个 linked Screen resize samples；Board `86:3214` 为 1880 × 1140；169 个 authored nodes、0 placeholder、0 missing/duplicate key | Figma Plugin API live audit `[C implementation]` |

## 5. 关键发现

1. 当前窗口由左侧 Agent Dock 与右侧 Workbench 两个一级区域组成 `[C]`；不是传统单 Activity Bar + 单 Sidebar 的 VS Code 结构。
2. Agent Dock 内再次分为 Task Rail 与 Agent Main `[C]`；任务历史、运行结果、变更审阅与 Composer 形成连续 Agent 工作流 `[C]`。
3. Workbench 由 Editor、Resource Sidebar、Bottom Panel 和底部 Status Bar 构成 `[C]`；Bottom Panel 只位于 Editor 下方，而 Status Bar 跨越整个 Workbench `[C]`。
4. 顶部不是单一无差别标题栏：Workspace selector、产品模式切换和窗口级动作按区域分布 `[C]`。
5. 单图可稳定恢复“当前快照几何”，但不能确认 Panel min/default/max、Resize 优先级、Collapse 顺序或动态交互 `[U]`。
6. 当前 Component Map 有 52 个候选类型、7 类 `[I]`；这是下一阶段审计清单，不是 52 个已建成的 Figma Components。
7. `TraeCode Copy/` 是用户确认的官方 Design System `[C]`：dark-only tokens、24 个组件合同、115 个 SVG icons 与 2 个 showcase UI kits。它将颜色、字体、radius、spacing 和已定义组件状态从截图假设提升为 source-confirmed；截图到具体 token/component 的映射仍需逐项判断。
8. 当前 Figma Shell 已恢复两级 Dock ownership，并用已有组件实例组合 Agent 完成态、变更审阅与 Composer `[C implementation]`；其中代表性总结文案与验证块仍是 `[I]`，不是官方完整 Agent data/state contract。
9. `TC-UI-001` 已通过 Screen component → Shell instance 的两级实例链建立；Reference 与 Reconstruction 的 50% 并排/叠加视图明确显示几何可比，但内容密度和代表文案不是像素级复刻 `[C implementation]`。
10. 基础 Prototype 已验证官方 Editor Tab 的 active/default composition 与双向 navigation `[C implementation]`；它不证明真实应用的 persistence、keyboard order、close behavior 或 motion `[U]`。
11. 当前 Figma Shell 的 no-overflow threshold 为 1564 × 618 `[C implementation]`；这是 scenegraph 几何阈值，不是 TraeCode 官方 window minimum `[U]`。
12. 水平压缩首先落在 Resource Sidebar；1564px 时其宽度已降为 147px，因此 no-overflow 不等于 usable UX minimum `[C implementation]`。
13. 总宽度低于 1417px 时，Workbench 小于固定 Editor 642，当前结构进入硬失效；真实产品应先 collapse 哪个区域仍为 `[U]`。
14. 官方 Chat Composer 已完成 8 个主变体与 Tool / Model / Send 子组件；44 / 44 nested instances 保持 linked，disabled / attachment / keyboard / running 语义继续为 `[U]`。
15. 官方 Table / Table Panel Library 已完成：Table Cell / Row / Bare / Wrapper、Table Panel Cell / Row / Panel、Tag、Avatar 与 Avatar Group 均为可复用资产 `[C implementation]`；selection、sort、column resize、sticky header、vertical scrolling 与 pagination behavior 没有被静态组件伪造 `[U]`。
16. 官方 Button Library 已完成：8 个 Text Button intents × 3 sizes × 4 states = 96 variants，3 个 Icon Button intents × 3 sizes × 4 states = 36 variants `[C implementation]`；Focus、Loading、Tooltip、keyboard activation 与真实 runtime transitions 仍为 `[U]`。
17. 官方 Atoms 已完成 source-type-aware 消费：Tooltip、Popover Surface、Empty State、Code Block 组件化；heading / mono 进入 Text Styles；layout helpers 保持 Auto Layout recipes。Phase 11 audit 为 92 authored nodes、5 个 linked samples、0 placeholder、0 unbound solid paint `[C implementation]`；runtime trigger、placement、dismissal、focus、keyboard、transition 与真实 scroll affordance 仍为 `[U]`。

## 6. 与 Askora 的治理边界

Askora current product shape 仍是 Local Web、single-user、local-first、BYOK；current experience shell 仍由 Askora Canonical Experience 与 UI Specs 决定。本研究只能提供以下类型的候选输入：

- 高密度信息层级处理；
- Docked Panel、Resizable Divider 与状态反馈模式；
- Agent 任务、运行、变更审阅与输入编排的组件拆分；
- Semantic Token、Auto Layout 与组件维护方法。

任何进入 Askora 的设计规则仍必须经 Product → Experience Design → ADR/Spec 的治理链接受，不能由本目录直接成为 implementation contract。

## 7. 下一阶段重点与进入条件

Foundations、首批 Components、Patterns、reference Application Shell、`TC-UI-001` 代表性 Screen、基础 Editor Tab Prototype、Figma Resize Stress Test、Official Chat Composer、Table / Table Panel、Button 与 Atoms Library 已完成。下一阶段应进入更多有证据支持的 interaction states，并继续官方 `alert` / `menu` / `forms` / `kbd` component contracts；真实 resize、overlay、Button 与 data-table interaction contract 仍需以下补证：

- 至少 3 个窗口宽度与 2 个窗口高度样本；
- Panel collapse / expand / resize 的前后截图或录屏；
- Agent start / running / approval / completed / error 状态链；
- Hover、Focus、Keyboard、Context Menu 与 Command Palette；
- Editor split、Bottom Panel tabs、Resource Sidebar 展开与滚动；
- Display scale / screenshot scale factor，避免把设备像素误当作逻辑像素。
