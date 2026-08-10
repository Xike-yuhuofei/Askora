# Askora Interactive Element System — Canonical Design Delta

> 状态：**FROZEN — Canonical Design Delta Record**  
> 冻结日期：2026-08-10  
> 适用范围：Askora Product Information Architecture / Interaction Architecture / Interactive Element System  
> 用户授权：2026-08-10 明确采纳 Zero-Based Interactive Elements 重构建议并授权开始执行  
> 上位产品定义：[`个人AI辅助学习平台设计方案.md`](个人AI辅助学习平台设计方案.md)  
> 当前实现合同：[`../specs/ui/`](../specs/ui/)  
> 当前实现：`apps/frontend/src/`

---

## 0. Freeze Declaration

本文件冻结 Askora Interactive Element System 的产品级增量设计。

本次冻结的目标不是视觉改版，也不是把既有按钮换名字，而是纠正当前 UI 信息架构中存在的结构性问题：

```text
Domain Object
→ 独立 Page
→ Global Navigation Item
→ Visual Component
```

不得继续作为默认设计推导方式。

新的正式推导顺序冻结为：

```text
User Job
→ Domain Meaning
→ Information Architecture
→ Interaction Semantics
→ Interaction Pattern
→ Visual Component
```

### 0.1 权威边界

本文件是 Canonical Design Delta，不是当前可直接执行的 Implementation Spec。

当前仓库权威顺序仍为：

```text
docs/specs/**
→ Accepted ADR
→ Canonical Design
→ Implementation
```

因此，在本 Delta 被新的 ADR 和更新后的 `docs/specs/ui/**` 吸收之前：

- 当前 UI Spec 仍是代码实现的直接合同；
- 本文件与旧 UI Spec 的冲突必须登记为 upstream/spec gap；
- 禁止先修改 React，再用文档追认；
- 下一阶段必须完成 ADR → Spec → EXEC 治理闭环后再修改产品代码。

### 0.2 本次冻结不改变的产品核心

Askora 仍是：

> 一个私人自用、本地单机、面向个人长期学习的 AI 学习 App。

Askora 仍然不是普通问答、聊天、摘要或知识管理工具。对话仍只是 LearningActivity 的一种交互手段，而不是产品顶层信息架构。

---

# 1. Executive Diagnosis

当前 UI 已经完成从 chat-first 向 learning-loop-first 的重要迁移，但仍存在第二层结构性问题：**过多 canonical domain object 被直接暴露成一级信息架构。**

当前 Sidebar：

```text
今天
学习目标
学习路径
资料库
学习证据
历史记录
设置
```

该结构的问题不是入口数量本身，而是七项不属于同一语义层级：

- `今天` 是 daily learning orchestration destination；
- `学习目标` 是 LearningGoal domain collection；
- `学习路径` 是 LearningPlan projection；
- `学习证据` 是 learner-state/evidence projection；
- `历史记录` 是 past activity projection；
- `资料库` 是 stable product domain；
- `设置` 是 application configuration destination。

把这些对象全部作为同级 Navigation Item，会让用户先理解 Askora 的内部领域模型，再决定去哪里学习。

本 Delta 冻结以下核心判断：

> Askora 的一级信息架构必须围绕稳定用户任务空间，而不是围绕 canonical object 数量组织。

---

# 2. First-Principles User Jobs

## 2.1 P0 — Daily Learning Jobs

用户打开 Askora 时，系统首先必须帮助用户回答：

1. 我现在最应该学什么？
2. 为什么现在应该学这个？
3. 我要继续上一次学习，还是开始下一项？
4. 当前需要理解、作答、复习还是迁移验证什么？
5. 遇到困难时如何获得适当的 Tutor 帮助？

## 2.2 P1 — Long-term Learning Management

6. 我的长期学习目标是什么？
7. 当前计划准备如何带我达到目标？
8. 我的真实能力和证据发生了什么变化？
9. 我的学习资料在哪里，如何补充和组织？

## 2.3 P2 — Reflection and Application Management

10. 我以前完成过什么学习活动？
11. 系统为什么做出当前安排或判断？
12. 如何配置模型、数据、隐私、外观和 App 行为？

## 2.4 Primary Product Loop

首页和全局 IA 必须优先支持：

```text
打开 Askora
→ 看见下一件最值得做的事
→ 理解原因
→ 开始 / 继续
→ 学习与作答
→ 得到反馈
→ canonical state 更新
→ 得到下一步
```

禁止要求用户先选择：

```text
Goal / Plan / Evidence / History
```

才能找到当前学习任务。

---

# 3. Interactive Element Taxonomy

Askora 长期冻结 **7 类 Semantic Interaction Primitives**。

| Primitive | Semantic Role | 典型行为 |
|---|---|---|
| `Navigation` | 改变用户所处的信息空间 | push、select destination、back |
| `Action` | 执行明确命令或产生副作用 | start、create、upload、delete |
| `Control` | 修改当前对象或应用状态 | toggle、slider、editable preference |
| `Selection` | 从有限候选中选择一个或多个值 | picker、segmented selection、multi-select |
| `Disclosure` | 暴露附加信息，不改变核心任务空间 | expand、collapse、inspector、details |
| `Interactive Content` | 用户直接选择或操作 domain content | document row、goal row、activity row |
| `Status / Feedback` | 表达状态、结果、错误、加载或进度 | badge、progress、error、success |

## 3.1 非 Primitive 术语

以下不得与 Semantic Primitive 混为一谈：

- Entry
- Button
- Card
- Toolbar
- Menu Item
- Context Menu
- Shortcut
- Popover
- Sheet
- Modal
- Row

它们是 composition、presentation 或 interaction pattern。

## 3.2 Entry

`Entry` 只作为产品分析术语使用：

> 让用户进入某个任务、对象或信息空间的可发现交互组合。

Entry 本身不是新的 semantic primitive。

一个 Entry 必须最终归类为：

- Navigation；或
- Action；或
- Interactive Content。

## 3.3 Contextual Action

`Contextual Action` 不建立为第八类 primitive。

定义为：

```text
Action + Contextual Visibility / Availability Rule
```

例如资料行的归档、重命名、重新 OCR、删除。

## 3.4 Domain Object 与 Interaction 必须分离

例如：

```text
LearningGoal = Domain Object
```

而：

```text
查看目标 = Navigation / Interactive Content
创建目标 = Action
编辑目标 = Action
切换关注目标 = Selection
```

禁止再把 `LearningGoal` 自身称为 Button、Entry 或 Navigation Item。

---

# 4. Canonical Information Architecture

## 4.1 L0 Product Domains

Askora 一级产品信息架构冻结为 **3 个核心域**：

```text
今天
学习
资料库
```

### 今天

每日学习决策与执行入口。

回答：

> 现在做什么？为什么？

### 学习

长期学习状态与计划空间。

包含：

```text
目标
路径
进展
历史
```

### 资料库

用户拥有的学习输入、来源与知识结构空间。

## 4.2 Settings 不属于 Product Domain Navigation

`设置` 保留为 App-level destination，但不再与三个产品域保持同等导航权重。

macOS 目标交互：

```text
Askora → Settings…
⌘,
```

Web 验证形态可以暂时保留可发现入口，但正式目标 IA 中它属于 Application Commands / Utility，而不是 Product Domain。

## 4.3 Chat 不属于 L0

`Chat`、`Tutor`、`Conversation` 均不得成为默认一级产品域。

Canonical 语义：

```text
LearningActivity
→ Workspace
→ Conversation / Task / Assessment / Tutor Interaction
```

对话是 LearningActivity 的 presentation/interaction mode。

---

# 5. Zero-Based Home Architecture

## 5.1 Primary Purpose

`Today` 只回答：

> 下一件最值得做的学习活动是什么？

## 5.2 Primary Information

READY 状态首屏必须优先展示：

- 当前 LearningGoal 的简短上下文；
- 当前 / next available LearningActivity；
- activity type；
- estimated duration；
- 用户可理解的推荐原因；
- 必要 validation obligation；
- canonical launchability。

## 5.3 Primary Action

首要动作：

```text
继续学习
```

或：

```text
开始学习
```

每个主任务区域最多一个 Primary Action。

## 5.4 Secondary Information

Today 只保留与当前决策直接相关的：

- 到期复习候选；
- 后续 1～3 项已规划活动；
- 当前目标；
- 必要的证据不足/待独立验证说明。

## 5.5 Compatibility Quick Start

兼容快速学习不得与 canonical next activity 同等视觉权重。

它只允许：

1. 无 canonical Goal / Plan 时作为 empty-state fallback；或
2. 进入 overflow / secondary utility。

只要 canonical next activity 可启动，兼容快速学习不得成为 Today 主内容区的并列 Primary Task。

---

# 6. Learning Domain Architecture

新的 `学习` 信息空间聚合以下对象：

```text
学习
├─ 目标
├─ 路径
├─ 进展
└─ 历史
```

这四者不是四个 L0 product domains，而是同一长期学习空间中的不同 Facet。

## 6.1 目标

语义：LearningIntent / LearningGoal collection。

支持：

- 查看；
- 创建；
- 编辑；
- 生命周期管理；
- 选择 focused goal。

## 6.2 路径

语义：LearningPlan Projection。

它是 Goal 的计划视图，而不是独立产品域。

不得暗示用户需要频繁“管理路径”。只在 owner command 已定义时允许改变计划约束。

## 6.3 进展

原 `学习证据` 重命名为面向用户的 `进展` 信息空间。

内部仍必须保持：

- evidence-first；
- uncertainty-visible；
- no arbitrary mastery label；
- independent/delayed/transfer evidence distinction。

`进展` 是 UI vocabulary，不改变 SYS03 / Evidence canonical semantics。

## 6.4 历史

历史是 Past Activity / Session / Outcome projection。

默认用于：

- 回顾；
- 恢复；
- 审计。

历史不得与当前 active state 混淆，也不需要占据 L0 Navigation。

---

# 7. Library Interaction Architecture

资料库继续作为 L0 Product Domain，但必须减少 always-visible controls。

## 7.1 Primary Tasks

资料库默认优先支持：

1. 查找资料；
2. 打开资料；
3. 导入资料；
4. 查看处理状态；
5. 查看相关知识结构。

## 7.2 Progressive Disclosure

以下能力应按上下文出现，而不是永久占据主页面：

- 批量标签；
- 批量集合；
- 批量归档；
- 重复资料处理；
- OCR 复核；
- 元数据高级编辑；
- 重新安全检查；
- destructive actions。

推荐模式：

```text
Selection
→ Contextual Toolbar / Inspector / More Menu
→ Action
```

禁止长期保留“大型资料管理控制面板”作为资料库默认主视觉。

---

# 8. Settings Architecture

## 8.1 Qualification Rule

只有满足以下条件之一的能力才进入 Settings：

- 跨任务持续生效的 App Preference；
- 账号 / 安全配置；
- 模型 / 外部能力配置；
- 数据与隐私管理；
- 外观与无障碍；
- 高级系统配置。

局部对象操作必须留在对应功能上下文，不得因为“难以分类”而进入 Settings。

## 8.2 Target Structure

```text
Settings
├─ 通用
├─ AI 与模型
├─ 学习偏好
├─ 外观
├─ 数据与隐私
├─ 账号与恢复
└─ 高级
```

## 8.3 Settings Landing Page

Settings 首页只显示 category navigation 和少量需要立即处理的状态。

以下不得在 Settings 首页一次性展开完整操作流：

- 永久删除数据；
- 全量数据导出；
- 修改密码；
- 会话管理；
- 恢复套件轮换；
- 账号删除。

这些应进入二级 destination 或 task flow。

## 8.4 Runtime Status

正常运行状态不需要长期占据 Settings 信息层级。

只有 degraded / unavailable / action-required 状态才 Contextually Reveal。

## 8.5 Recovery

错误恢复中心保留，但优先由 global recovery indicator 在存在真实 issue 时触发。

Settings 可以保留备用入口，不应让恢复能力成为正常状态下的首要设置内容。

---

# 9. Interaction Hierarchy

冻结以下层级：

## L0 — Product Domain Navigation

```text
今天 / 学习 / 资料库
```

## L1 — Domain Facet / Local Navigation

例如：

```text
目标 / 路径 / 进展 / 历史
```

## L2 — Primary Task / Primary Action

当前页面最重要的用户任务。

规则：一个局部任务区域最多一个 Primary Action。

## L3 — Secondary Action

支持主任务但不应抢占主视觉。

例如：

- 查看完整路径；
- 切换目标；
- 查看相关资料。

## L4 — Object-level Contextual Action

例如：

- 归档资料；
- 重命名；
- 重新 OCR；
- 删除。

## L5 — Advanced / Overflow

低频、审计、开发或高风险能力，例如：

- source refs；
- correlation details；
- 导出；
- advanced model configuration；
- destructive data commands。

规则：

> 层级越低，越不应该长期常驻。

---

# 10. Semantic → Interaction Mapping

| Domain Meaning | User Intent | Semantic Primitive | Typical Pattern |
|---|---|---|---|
| LearningGoal | 查看 | Navigation / Interactive Content | row → detail |
| LearningGoal | 创建 | Action | primary/secondary button → flow |
| LearningGoal | 编辑 | Action | toolbar/context action |
| Focused Goal | 切换 | Selection | picker |
| LearningPlan | 查看 | Navigation / Disclosure | facet/detail |
| LearningActivity | 开始 | Action | primary action |
| LearningActivity | 继续 | Action | primary action |
| ReviewDue | 开始复习 | Action | contextual primary/secondary action |
| Material | 打开 | Interactive Content | row/list |
| Material | 导入 | Action | toolbar action |
| Material | 归档 | Contextual Action | context menu / contextual toolbar |
| Evidence | 理解当前状态 | Content / Disclosure | summary + inspector |
| Tutor Help | 请求帮助 | Action | contextual action |
| Preference | 修改 | Control | toggle/picker/field |
| Search | 查找对象 | Control / Action | search field / command |
| System state | 理解状态 | Status / Feedback | status, notice, recovery entry |

---

# 11. Presentation Pattern Rules

## 11.1 Card

Card 只在内容确实需要独立边界时使用。

适合：

- 当前主任务；
- typed rich response；
- evidence summary；
- recovery issue；
- 少量可选对象。

不适合：

- 普通 collection 中的每一行；
- 仅因为元素可点击；
- 为制造 Dashboard 视觉而包装内容。

## 11.2 Row / List

重复 domain objects 默认使用 row/list。

例如：

- goals；
- documents；
- activities；
- history；
- sessions。

## 11.3 Button

Button 只表达 Action / Control，不表达普通 destination identity。

## 11.4 Toolbar

Toolbar 只承载：

- 当前页面高频动作；
- contextual selection actions；
- search / view controls。

禁止把所有低频能力都永久放入 Toolbar。

## 11.5 Modal / Sheet

只用于：

- 短暂决策；
- destructive confirmation；
- compact selection；
- narrow-screen inspector。

长流程、复杂配置和可导航内容应使用 destination page，而不是大型 modal。

---

# 12. Platform Adaptation

Semantic Role 在 macOS / iOS / Web 验证形态之间不得改变。

## 12.1 macOS

优先模式：

```text
Sidebar / NavigationSplitView
Toolbar
Context Menu
Inspector
Keyboard Commands
Settings command
```

建议长期支持：

- `⌘,` Settings；
- `⌘K` Search / Command；
- Escape 关闭 transient surface；
- keyboard focus traversal；
- context menu for object actions。

## 12.2 iOS

优先模式：

```text
Tab Bar: 今天 / 学习 / 资料库
Navigation Stack
Toolbar
Sheet
Swipe / Context Actions
```

## 12.3 Web-first Development

当前 Web UI 可以继续作为实现与验证载体，但不得因为 Web Sidebar 方便实现，就反向决定最终 App 的 canonical IA。

---

# 13. Canonical Decision Register

| ID | Frozen Decision | Status |
|---|---|---|
| `IES-CD-001` | UI 推导顺序固定为 User Job → Domain Meaning → IA → Interaction → Pattern → Component | **FROZEN** |
| `IES-CD-002` | Domain Object 不自动成为 Page、Entry 或 Global Navigation Item | **FROZEN** |
| `IES-CD-003` | Askora Semantic Interaction Primitive 固定为 7 类 | **FROZEN** |
| `IES-CD-004` | Entry 不是 primitive；必须落到 Navigation / Action / Interactive Content | **FROZEN** |
| `IES-CD-005` | Contextual Action = Action + contextual rule，不创建独立 primitive | **FROZEN** |
| `IES-CD-006` | L0 Product Domain 收敛为 今天 / 学习 / 资料库 | **FROZEN** |
| `IES-CD-007` | Settings 从 Product Domain Navigation 中移出，成为 App-level destination | **FROZEN** |
| `IES-CD-008` | Goal / Path / Progress / History 聚合到 Learning domain 的 L1 facets | **FROZEN** |
| `IES-CD-009` | LearningGoal 是 domain object；LearningPath 是 LearningPlan projection | **FROZEN** |
| `IES-CD-010` | Chat/Tutor 不成为 L0；Conversation 是 LearningActivity 的 interaction mode | **FROZEN** |
| `IES-CD-011` | Today 只围绕 canonical next activity 建立单一 Primary Task | **FROZEN** |
| `IES-CD-012` | Compatibility Quick Start 在 canonical activity 可用时必须降级 | **FROZEN** |
| `IES-CD-013` | Library 保持 L0，但批处理/OCR/去重等采用 progressive disclosure | **FROZEN** |
| `IES-CD-014` | Settings landing page 从 control panel 重构为 category navigation | **FROZEN** |
| `IES-CD-015` | Interaction Hierarchy 固定 L0～L5，越低层越不应常驻 | **FROZEN** |
| `IES-CD-016` | Card/Button/Toolbar/Menu/Modal 是 presentation pattern，不是 semantic role | **FROZEN** |
| `IES-CD-017` | 同一 semantic role 跨 macOS/iOS/Web 保持不变，仅 pattern 适配平台 | **FROZEN** |
| `IES-CD-018` | Quiet UI 通过语义删减和 progressive disclosure 实现，不通过隐藏关键状态实现 | **FROZEN** |

---

# 14. Existing Spec Conflict / Supersession Register

本表是下一阶段 ADR + Spec Update 的输入，不在本文件中直接修改当前实现合同。

| Current Spec Area | Current Semantics | Target Delta | Required Action |
|---|---|---|---|
| `UI-IA-001` | Learning-loop first | 保留原则，但 IA 进一步从 domain-object navigation 收敛为 user-job domains | AMEND |
| `UI-IA` Global Navigation | Today/Goals/Path/Library/Evidence/History/Settings 7 项 L0 | Today/Learning/Library 3 个 product domains；Settings app-level | SUPERSEDE |
| `UI-IA-020` Canonical Routes | `/goals` `/path` `/evidence` `/history` 为独立 canonical L0 routes | 新 canonical `/learning/*`；旧 routes redirect | SUPERSEDE |
| `UI-IA-030` Standard Shell | Global Nav + Primary Content + Inspector | 基本保留，Global Nav vocabulary 更新 | AMEND |
| `UI-SCREEN-010..015` Today | canonical next activity + compatibility quick start | canonical activity 成为唯一 primary；quick start 仅 fallback/overflow | AMEND |
| `UI-SCREEN-020..022` Goals | 独立 Goals page semantics | 语义保留，迁入 Learning facet；并吸收后续 Goal command baseline | AMEND |
| `UI-SCREEN-030..032` Path | 独立 Path page semantics | Plan projection 保留，迁入 Learning facet | AMEND |
| `UI-SCREEN-070..074` Evidence | 独立 Evidence destination | 语义保留，用户 vocabulary → Progress / 进展 | AMEND |
| `UI-SCREEN-080..` History | 独立 History destination | 语义保留，迁入 Learning facet | AMEND |
| Settings screen contract | 大量控制同屏 | category navigation + secondary task destinations | SUPERSEDE |
| `UI-VIS-052` Cards | 已禁止 card ocean | 保留并增加 semantic qualification rule | AMEND |
| `UI-VIS-050/051` Button/Nav | component intent | 增加 semantic primitive → component mapping | AMEND |

---

# 15. Route Target and Compatibility

下一版 UI Spec 应冻结目标路由：

```text
/today

/learning
/learning/goals
/learning/goals/:goalId
/learning/goals/new
/learning/plan
/learning/progress
/learning/history

/library
/library/:documentId

/learn/:activityId
/quick/:sessionId   # compatibility only

/settings
/settings/ai
/settings/learning
/settings/appearance
/settings/data
/settings/account
/settings/advanced
```

旧路由不得直接失效：

```text
/goals    → /learning/goals
/path     → /learning/plan
/evidence → /learning/progress
/history  → /learning/history
```

Redirect 必须无业务副作用。

---

# 16. Current → Target Migration Decisions

| Current Element | Problem | Target | Action | Priority |
|---|---|---|---|---|
| Today | canonical task 与 compatibility flow 同屏竞争 | Daily Learning Orchestrator | REDESIGN | P0 |
| Goals L0 | Domain Collection 被提升为 Product Domain | Learning → Goals | DEMOTE | P0 |
| Path L0 | Plan Projection 被提升为 Product Domain | Learning → Plan | DEMOTE | P0 |
| Evidence L0 | State Projection 与 daily task 同级 | Learning → Progress | DEMOTE | P0 |
| History L0 | Past state 与 active task 同级 | Learning → History | DEMOTE | P1 |
| Library L0 | Stable user-owned content domain | Library | KEEP | P0 |
| Settings L0 | App configuration 与 product domains 混合 | App-level Settings | MOVE | P1 |
| Today Quick Start | Compatibility entry 抢占 primary hierarchy | Empty-state / Overflow fallback | DEMOTE | P0 |
| Legacy `Chat.jsx` | 第二套 chat-first mental model | canonical TutorWorkspace only | REMOVE | P1 |
| Library permanent management panel | Advanced actions always visible | Contextual selection actions | REDESIGN | P1 |
| Settings giant grid | Control Panel Syndrome | Hierarchical Settings | REDESIGN | P0 |

---

# 17. Minimal Long-term Interaction Model

Askora 长期最小模型：

```text
Askora
│
├─ 今天
│   └─ 下一件最值得做的学习活动
│
├─ 学习
│   ├─ 目标
│   ├─ 路径
│   ├─ 进展
│   └─ 历史
│
├─ 资料库
│
└─ LearningActivity Workspace
    ├─ Task
    ├─ Tutor
    ├─ Assessment
    └─ Context / Evidence
```

Application utility：

```text
Settings
Search / Command
Recovery
```

不得再把这些 utility 与 Product Domain 强行放在同一产品层级。

---

# 18. Design System Contract Requirements

下一阶段 UI Spec 必须为每个长期 primitive 定义：

1. Semantic Role；
2. 使用条件；
3. 禁止使用条件；
4. interaction behavior；
5. state vocabulary；
6. hierarchy constraints；
7. pointer/touch behavior；
8. keyboard behavior；
9. accessibility；
10. macOS/iOS pattern mapping；
11. examples；
12. anti-patterns。

至少覆盖：

```text
Navigation Item
Primary Action
Secondary Action
Contextual Action
State Control
Selection
Interactive Row / Content
Disclosure
Status / Feedback
```

---

# 19. Explicit Anti-patterns

正式禁止：

- Domain Object → automatic L0 navigation；
- 所有功能都变成独立页面；
- 所有可点击内容都称为 Entry；
- 所有区域都变成 Card；
- 所有 Card 都可点击；
- 用视觉权重代替 semantic hierarchy；
- 让 Goal、Plan、Evidence、History 永久并列；
- 让兼容功能与 canonical learning task 同级；
- 把内部 SYS/algorithm vocabulary 暴露成用户导航；
- Settings 作为无法分类功能的垃圾桶；
- Library 默认展示所有管理能力；
- 正常状态下持续展示 system/runtime diagnostics；
- 为追求 Quiet UI 隐藏 evidence uncertainty、error、citation 或 validation obligation。

---

# 20. Next Governance Step

本 Delta 冻结后，下一阶段必须严格执行：

```text
Interactive Element System Canonical Design Delta（本文件）
→ 新 Accepted ADR：UI Information / Interaction Architecture
→ 更新 docs/specs/ui/information-architecture.md
→ 更新 docs/specs/ui/screen-contracts.md
→ 更新 docs/specs/ui/visual-system.md
→ 必要时更新 docs/specs/ui/quality-and-migration.md
→ 新 Vertical Slice / EXEC
→ Codex 修改 frontend
→ build / responsive / keyboard / E2E 验收
```

在 ADR + Spec 更新完成前，不允许把本 Delta 当作理由直接重构 production frontend。

---

# 21. Final Freeze Answers

## Q1 — Askora 真正需要几类 Interactive Elements？

**7 类 Semantic Interaction Primitives：**

```text
Navigation
Action
Control
Selection
Disclosure
Interactive Content
Status / Feedback
```

## Q2 — 长期基础 Interaction Primitives 是什么？

长期冻结 semantic primitives；同时仅保留少量稳定 presentation patterns：

```text
Row / List
Toolbar
Menu / Context Menu
Popover / Sheet / Modal
```

## Q3 — 如果只能保留当前 L0 Interactive Elements 的 50%？

保留：

```text
今天
资料库
```

将 `学习目标` 转化为新的聚合域 `学习`；把：

```text
学习路径
学习证据
历史记录
```

降为 Learning domain 的 L1 facets；把 Settings 移至 App-level utility。

最终 L0 不是机械保留旧元素的一半，而是收敛为：

```text
今天 / 学习 / 资料库
```

---

## 22. Canonical Summary

本 Delta 最重要的冻结原则是：

> **Domain Model ≠ Information Architecture ≠ Interactive Element。**

Askora 的 UI 不再以“系统拥有哪些对象”为起点，而以“用户此刻需要完成什么学习任务”为起点。

最终目标不是建立更完整的 Dashboard，而是建立：

> 语义正确、层级清晰、行为可预测、数量最少，并能长期适配 macOS / iOS / Web 验证形态的 Interactive Element System。
