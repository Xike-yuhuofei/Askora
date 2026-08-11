# Askora UI Specification Set

> 状态：`FROZEN — ADR-0014 + ADR-0018 UI Contract Set`  
> 权威性：Canonical UI Implementation Contract  
> 上游产品定义：`docs/product/PRODUCT-DEFINITION.md`  
> Governing Design：`docs/design/Interactive-Element-System-Canonical-Design-Delta.md`、`docs/design/UX-Architecture-Canonical-Design-Delta.md`  
> Governing ADR：`docs/adr/ADR-0014-user-job-driven-interaction-architecture.md`、`docs/adr/ADR-0018-ux-workspace-context-architecture.md`

## 1. Purpose

本目录定义 Askora 的 Information Architecture、Interactive Element semantics、screen behavior、UI read models、visual system 与 UI migration / quality gates。

UI Specs 回答的是：

> **用户如何看到、理解和操作已经由 Product Definition 冻结的产品能力。**

它们不拥有 Product Capability、v1 Feature inclusion、Product Rule 或 Product Acceptance。任何“某能力是否属于 v1”的判断必须回到 `PRODUCT-DEFINITION.md` 或明确的 Product Feature Spec。

Askora UI 的学习主链仍然围绕：

```text
Today next action
→ LearningActivity
→ Tutor / Task / Assessment
→ Evidence / Review / Plan update
→ Next action
```

UI 不得改变 SYS01～SYS08 状态所有权、TeachingAction、AssessmentResult、MasteryEstimate、LearningPlan 或 ReviewSchedule 语义。

## 2. Product Definition Traceability

UI Spec Set 的主要上游 Product Definition 映射：

| UI Area | Product Definition Trace | UI Ownership |
|---|---|---|
| Workspace / Library | `CAP-01`、`CAP-07`、`PD-REQ-0101..0104`、`PD-RULE-006/009/011` | 导航、呈现、contextual commands、source disclosure |
| Goal / Plan / Next Activity | `CAP-02`、`CAP-03`、`CAP-07`、`PD-REQ-0201..0203`、`PD-REQ-0301..0303` | task flow、信息层级、状态解释、入口 |
| Tutor / Learning Canvas | `CAP-04`、`CAP-05`、`PD-REQ-0401..0403`、`PD-REQ-0501..0503` | 同一 canonical activity 的交互与呈现 |
| Review / validation disclosure | `CAP-06`、`CAP-07`、`PD-REQ-0601..0603`、`PD-REQ-0701..0703` | obligation / history / next-step 的可理解呈现 |
| Local data / Settings | `CAP-08`、`PD-REQ-0801..0804`、`PD-RULE-008/010/011` | utility IA、配置呈现、恢复/删除确认 |
| Accessibility / usability | `PD-NFR-005` | UI-specific responsive / accessibility contract |

规则：

- 新建或实质重构 UI Spec 时 MUST 引用适用的 `CAP-*` / `PD-REQ-*` / `PD-RULE-*`；
- 不得为了“完整”把所有 CAP 机械挂到每份 UI 文档；
- Product Definition 缺失时报告 `PRODUCT DEFINITION GAP`，不得由 UI 自行补成永久产品范围；
- UI Acceptance 只证明用户交互合同成立，不自动等同 Product Acceptance 或 Learning Evidence。

## 3. ADR-0014 Frozen UX Decisions

ADR-0014 冻结以下 UX / Interaction Architecture 语义：

1. UI 推导顺序固定为：

```text
User Job
→ Product / Domain Meaning
→ Information Architecture
→ Interaction Semantics
→ Interaction Pattern
→ Visual Component
```

2. L0 Product Domain 固定为：

```text
今天 / 学习 / 资料库
```

3. Settings / Recovery / Search 属于 App Utility，不与 Product Domain 等权。
4. Chat/Tutor 是 LearningActivity interaction mode，不是 Product Domain。
5. Today 在 canonical activity 可用时只允许一个 Primary Learning Task；Quick Start 降为 fallback/secondary。
6. Interactive Element 顶层 semantic primitives 固定为 7 类：Navigation、Action、Control、Selection、Disclosure、InteractiveContent、StatusFeedback。
7. Card/Button/Toolbar/Menu/Modal 是 pattern/component，不是 semantic role。
8. Settings landing 使用 hierarchical category navigation，不再是 giant control grid。

历史 ADR-0014 中关于 Learning 常驻 facets、OCR progressive disclosure 等条款，若与 ADR-0018 / current `UXA-*` 条款冲突，以明确 supersession matrix 为准。

## 4. ADR-0018 Frozen UX Decisions

ADR-0018 在 ADR-0014 之上冻结：

1. 三栏职责：Left = Where（导航 + Workspace），Center = Learn（唯一 Primary Canvas），Right = Reference / Notes（可隐藏）。
2. Workspace 是三栏共享的 canonical `current_workspace_id` 上下文；切换处理 draft / stream / note / session / material-tab。
3. Learning Context Drawer 固定在中栏 composer 正上方，默认收起，只显示 stage / stage goal / next 1..3。
4. Learning 不再暴露 Goal / Plan / Progress / History 常驻管理 facet（domain truth 保留）。
5. Library v1 正常 UI 不暴露 OCR；扫描 PDF 诚实显示 unsupported / partial。
6. 大纲 / Evidence 管理中心 / 知识图谱管理 UI / Progress Dashboard / AI Summary / Flashcards / 错题本等当前 deferred candidates 不建 placeholder。

其中第 5、6 项是对当前 Product Definition v1 Scope 的**呈现层落实**，不是 UI 自己拥有 Feature inclusion / exclusion。若 Product Definition 未来改变，必须先完成上游 Product Delta，再更新 UX / UI Specs。

`UserNote` 已是 `PRODUCT-DEFINITION.md` 的 Core Product Object，并属于 `CAP-01` 的辅助沉淀能力。历史 UI-03 “persistent notes 非目标”语义已被 ADR-0018 / current Product Definition supersede；当前 UI 只能在 owner / persistence contract 明确后呈现 UserNote，不得用 frontend-only state 冒充持久化笔记。

## 5. Spec Index

- [Interactive Element System](interactive-element-system.md)：7 类 semantic primitives、L0～L5 hierarchy、pattern qualification、cross-platform mapping 与 anti-patterns。
- [Information Architecture](information-architecture.md)：当前三栏学习架构、Workspace context、routes、legacy migration 与 responsive IA；旧 facet 条款按其 supersession matrix 解释。
- [Screen Contracts](screen-contracts.md)：Today / Learning Canvas / Workspace / Library / Settings 等 task/state/action contracts。
- [UI Data Contracts](data-contracts.md)：领域来源、UI Read Model、Query/API 与兼容边界。
- [Visual System](visual-system.md)：semantic-before-component、tokens、hierarchy、rows/cards、contextual actions 与 accessibility。
- [Quality and Migration](quality-and-migration.md)：UI migration、tests、responsive/security/claim gates。
- [Component State Contracts](component-state-contracts.md)：组件状态与交互状态合同。

## 6. Authority

UI 工作遵守：

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ Canonical UX / Interaction Design
→ Accepted ADR
→ Domain / System / Interface / UI Specs
→ Frozen Vertical Slice（需要时）
→ Linear Issue / EXEC
→ Code / Test
```

发生冲突时：

- Product Definition 与 UI Design/Spec 冲突：报告 `DESIGN–DEFINITION GAP`，下游不得自行改变 Product Scope；
- UI Spec 与更高权威 domain/system/security contract 冲突：报告 `SPEC GAP`；
- UI 与 current code 冲突：默认视为 implementation drift，除非上游已明确 supersede。

不得用视觉、route 或 frontend-only state 绕过 owner truth。

## 7. System / Domain Traceability

| UI Area | Primary Technical Upstream | UI 只允许决定 |
|---|---|---|
| Interactive Elements / IA | ADR-0014、ADR-0018、System Architecture | semantic role、navigation、hierarchy、pattern |
| Today / Goal / Plan | SYS06、SYS07、Goal/Activity lifecycle | owner state 的组合、解释、入口 |
| Tutor / Focus | SYS04、SYS05、SYS08 | 同 activity execution 的呈现与 user request |
| Library | SYS01、SYS02、Library Management | Material / source 呈现与 contextual commands |
| Progress / Evidence disclosure | SYS03、State Ownership | canonical evidence projection、uncertainty、source |
| Settings / Data Control | LID / LSS / Data Control / Recovery / Security | category/navigation/presentation，不改变 security semantics |
| Rich Response | RENDER、Security | typed payload layout 与 safe fallback |
| Quality | TEST、DOD、Security | UI-specific gates、migration、claims |

SYS01～SYS08 是 technical / teaching ownership，不是 Product Capability taxonomy。

## 8. Current Implementation Boundary

当前代码、历史 Release 与旧 Vertical Slice 只作为 migration starting point，不拥有 Product Definition，也不构成实时工作状态。

判断“当前是否已实现/是否正在做”时：

1. 读取 current `main` 与 tests；
2. 读取对应 current ADR / Spec；
3. 读取 Linear 当前 Issue / Milestone；
4. 不从本 README 的历史清单推断实时进度。

因此本文件不再维护 `EXEC-*` 的实时执行队列、等待关系或“当前仍由某 EXEC 管理”的静态状态。该信息属于 Linear 与 `docs/exec-plans/` 的当前索引。

## 9. Explicit Non-goals

UI / Interaction Design 不授权：

- 改变 Teaching Strategy / TeachingAction；
- frontend mastery threshold；
- Plan manual reorder/replan；
- LearnerState direct edit；
- 新的 global search backend；
- 新生产依赖或 telemetry；
- 重写已冻结 security / data flows；
- 把 UI 改善称为学习效果改善；
- 用 frontend mock / local state 冒充 Workspace、UserNote、LearningPlan、Evidence 等 canonical truth；
- 删除 Goal / Plan / Evidence / History domain truth 只是因为不再常驻展示；
- 扩展 OCR 或为 Product Definition 当前 deferred candidates 建 placeholder / disabled tab。

## 10. Working Rule

> **Product Definition 决定 Askora 必须具备什么产品能力；UI Design / Specs 决定这些能力如何被用户看见和使用。UI 不能通过导航、页面、placeholder 或历史实现反向创造 Product Scope。**
