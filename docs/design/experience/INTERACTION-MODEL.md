# Askora Interaction Model

> 状态：**Canonical Interaction Design Baseline**  
> 冻结日期：2026-08-11  
> 适用范围：Askora v1 semantic interaction model  
> 上游：[`EXPERIENCE-ARCHITECTURE.md`](EXPERIENCE-ARCHITECTURE.md)、[`../../product/PRODUCT-DEFINITION.md`](../../product/PRODUCT-DEFINITION.md)  
> 关键已接受决策：[`../../adr/ADR-0014-user-job-driven-interaction-architecture.md`](../../adr/ADR-0014-user-job-driven-interaction-architecture.md)、[`../../adr/ADR-0018-ux-workspace-context-architecture.md`](../../adr/ADR-0018-ux-workspace-context-architecture.md)  
> 下游：UI Screen / Learning Interaction / Design System Specs

---

## 1. Purpose

本文件定义 Askora 的稳定交互语义：用户的一个交互意图属于什么类型、不同类型有什么边界，以及界面组件如何承载这些语义。

它不定义 Button 长什么样，也不定义 route / API；它定义的是：

> **用户正在导航、执行动作、改变设置、选择对象、展开信息、操作内容，还是接收状态反馈。**

---

## 2. Derivation Rule

所有新增或重构交互必须遵循：

```text
User Job
→ Product / Domain Meaning
→ Information Architecture
→ Interaction Semantics
→ Interaction Pattern
→ Visual Component
```

禁止反向推导：

```text
已有 Button / Card / Modal
→ 为组件寻找用途
```

`LearningGoal`、`LearningPlan`、`Material`、`Evidence` 等 domain object 也不会自动生成页面、入口、按钮或卡片。

---

## 3. Canonical Semantic Primitives

Askora 只保留 7 类顶层 interaction primitive：

```text
Navigation
Action
Control
Selection
Disclosure
InteractiveContent
StatusFeedback
```

新需求必须首先映射到其中之一；如果无法映射，应重新检查 user job，而不是直接增加第八类 primitive。

### INT-001 — Navigation

改变用户当前所处的信息空间，不直接执行业务 command。

典型用途：

- 进入 Today / Learning / Library；
- 返回；
- 打开对象详情；
- 进入明确 task flow；
- 切换 presentation-only destination。

Navigation 本身不得创建 Goal、Activity、Session、Evidence 或改变 canonical business state。

### INT-002 — Action

执行明确命令并产生可观察副作用。

典型用途：

- 开始/继续 LearningActivity；
- 提交作答；
- 请求帮助；
- 导入资料；
- 创建/确认目标；
- 删除、恢复、导出、重试。

Action 必须具备可预测结果，并在适用时定义 pending / disabled / error / destructive / retry semantics。

### INT-003 — Control

改变当前对象的可编辑值、App preference 或 presentation preference。

例如：

- 显示/隐藏右栏；
- 主题偏好；
- 合法的 editable setting。

Control 不等于 Navigation，也不得在没有 owner contract 时冒充 canonical business-state editor。

### INT-004 — Selection

从明确候选集合中选择一个或多个对象/值。

例如：

- Workspace candidate；
- provider/model candidate；
- Material multi-selection。

Selection 与业务提交默认分离。只有上游合同明确 immediate apply 时，选择才可同时触发 Action。

### INT-005 — Disclosure

显示或隐藏附加信息，而不改变主要任务空间或 canonical business state。

例如：

- Learning Context Drawer；
- citation detail；
- technical detail；
- Inspector / sheet 中的辅助信息。

完成任务所需的唯一信息、安全错误、必要 citation、validation obligation 不得只存在于默认不可发现的 Disclosure 中。

### INT-006 — InteractiveContent

内容对象本身可被打开、聚焦或进入其上下文。

例如：

- Material row；
- Activity row；
- History item；
- contextual Goal entry。

重复对象默认优先 row/list，而不是 Card ocean。

### INT-007 — StatusFeedback

表达状态、进度、结果、置信度、保存状态、加载、错误或恢复信息。

StatusFeedback 默认不执行 command。若用户需要进一步操作，应提供独立 Action / Navigation / Disclosure，而不是让一个 status chip 同时承担多个语义。

---

## 4. Non-primitive Vocabulary

以下不是顶层 semantic primitive：

```text
Button
Card
Row
List
Toolbar
Menu
Context Menu
Shortcut
Popover
Sheet
Modal
Inspector
Tab
Sidebar Item
Badge
Chip
```

它们是 presentation pattern 或 reusable component。

`Entry` 也只允许作为分析术语，最终必须落到：

```text
Navigation | Action | InteractiveContent
```

`Contextual Action` 定义为：

```text
Action + Contextual Visibility / Availability Rule
```

不构成新的 primitive。

---

## 5. Interaction Hierarchy

### INT-H-001 — Primary Task

每个主任务区域原则上只有一个 primary intent。

如果界面出现两个同等级 Primary Action，应先重新检查是否存在两个不同任务，而不是仅通过视觉并列解决。

### INT-H-002 — Secondary Action

支持当前任务但不是完成任务唯一必要动作的行为使用 secondary hierarchy。

### INT-H-003 — Contextual Action

对象级、低频或选择后才有意义的动作应 contextually reveal，例如：

- selection toolbar；
- More Menu；
- Context Menu；
- focus-visible action；
- Inspector action。

### INT-H-004 — Advanced / Audit

开发诊断、correlation、内部 version/ref、高风险数据操作、低频导出等默认进入高级层级，不长期占据主任务首屏。

---

## 6. Progressive Disclosure Rule

新增常驻交互前，必须按以下顺序判断：

```text
Delete
→ Merge
→ Contextual Reveal
→ Secondary Action
→ Overflow
→ Stable Navigation
```

新增稳定 Navigation 是最后手段。

任何常驻元素必须回答：

> 删除它是否会阻断主要 User Job，或造成不可接受的 discoverability / safety 损失？

如果不会，默认应降级、合并或 contextualize。

---

## 7. Askora-specific Semantic Mapping

### INT-MAP-001 — Workspace

```text
查看当前 Workspace       → StatusFeedback / Context
选择候选 Workspace       → Selection
提交 Workspace 切换      → Action
进入某 Workspace 上下文   → Navigation
切换中的保存/恢复状态      → StatusFeedback
```

单一 Workspace 不展示虚假 selector。

### INT-MAP-002 — Learning Activity

```text
查看当前任务             → InteractiveContent / Content
开始 / 继续              → Action
提交 Attempt              → Action
请求帮助                 → Action
帮助 / 暴露状态           → StatusFeedback
查看来源                 → Disclosure / Navigation
```

Conversation 是 Activity 的交互形式，不是独立 Product Domain。

### INT-MAP-003 — Goal / Plan / Evidence / History

```text
必要上下文摘要           → Content / StatusFeedback
查看原因或详情           → Disclosure / contextual Navigation
创建 / 纠正 / 确认       → Action（仅 owner contract 存在时）
直接编辑 canonical state → FORBIDDEN unless explicitly authorized
```

它们不自动成为 Learning 常驻 navigation facet。

### INT-MAP-004 — Material

```text
Material row             → InteractiveContent
Import                   → Action
Search / Filter          → Control
Multi-select             → Selection
Selected-object operation→ Contextual Action
Processing / extraction  → StatusFeedback
查看原文                 → Navigation / Disclosure
```

### INT-MAP-005 — Notes / Current Material

```text
Right rail hide/show     → Control
Notes saving state       → StatusFeedback
Notes save/retry         → Action
Material tab switch      → Navigation / Disclosure
Citation detail          → Disclosure
```

---

## 8. State Semantics

交互状态必须表达真实语义，而不是纯视觉 variant。

概念上至少区分：

```text
available
focused
selected
pressed
pending
unavailable / disabled
succeeded
failed
recoverable
```

具体组件状态枚举和 DOM/ARIA 行为由 Design System Spec 定义。

### INT-STATE-001 — No Fake Success

`pressed`、local optimistic state 或 browser memory 不得被当作 command 成功或 durable save truth。

### INT-STATE-002 — Disabled Requires Reason

正式产品不得用 disabled control 代表“以后可能实现”。未实现能力应延期或不暴露。

当 action 因真实规则不可执行且原因对用户重要时，必须提供可理解原因。

### INT-STATE-003 — Failure Is Actionable

错误反馈应至少表达：

1. 发生了什么；
2. 数据是否安全；
3. 用户当前能做什么。

系统/模型失败不得伪装成学习者失败。

---

## 9. Input and Accessibility Principles

同一 interaction intent 在 pointer、keyboard、touch 下语义必须一致；只允许 presentation pattern 改变。

最低原则：

- 所有核心 Action 可通过键盘完成；
- focus 可见且顺序可预测；
- modal/sheet/disclosure 关闭后合理恢复 focus；
- Contextual Action 不能只依赖 hover；
- 状态不能只依赖颜色；
- icon-only control 必须有 accessible name；
- 窄屏 surface 不得永久移除完成任务所需能力。

exact key binding、ARIA pattern、target size 属 Design System / Screen Spec。

---

## 10. Interaction vs Design System

```text
Interaction Model
= 这个元素在用户任务中“是什么、做什么”

Design System
= 用哪个 component/pattern 承载，以及它的视觉和状态如何表现
```

例如：

```text
Action
→ Button / Menu Item / Context Menu Item

Navigation
→ Link / Sidebar Item / Row

Disclosure
→ Drawer / Inspector / Details / Sheet
```

Design System 不得反向创造 Product Capability 或新的 semantic primitive。

---

## 11. Explicit Non-goals

本文件不拥有：

- route path；
- component implementation；
- design token；
- API / command schema；
- persistence；
- canonical learner-state rules；
- Teaching Policy；
- exact screen layout；
- 当前 Linear issue 状态。

---

## 12. Downstream Requirements

UI / UX Specs 必须：

- 为每个核心 interactive element 指明 semantic primitive；
- 不把 Card/Button/Badge 当作业务语义；
- 不让 Navigation 产生隐藏业务写入；
- 不让 frontend-only state 形成第二 canonical truth；
- 对 loading / error / retry / disabled / focus 给出可自动验证行为；
- 对当前 Experience Architecture 的 Workspace、Learning Canvas、Notes/Material rail 提供一致映射。
