# Askora Experience Architecture

> 状态：**Canonical Experience Design Baseline**  
> 冻结日期：2026-08-11  
> 适用范围：Askora v1 Experience / IA / Navigation / Workspace / Journey 设计  
> 上游：[`../../product/PRODUCT-STRATEGY.md`](../../product/PRODUCT-STRATEGY.md)、[`../../product/PRODUCT-POSITIONING.md`](../../product/PRODUCT-POSITIONING.md)、[`../../product/PRODUCT-DEFINITION.md`](../../product/PRODUCT-DEFINITION.md)  
> 关键已接受决策：[`../../adr/ADR-0014-user-job-driven-interaction-architecture.md`](../../adr/ADR-0014-user-job-driven-interaction-architecture.md)、[`../../adr/ADR-0018-ux-workspace-context-architecture.md`](../../adr/ADR-0018-ux-workspace-context-architecture.md)  
> 下游实现合同：[`../../specs/ui/`](../../specs/ui/)

---

## 1. Purpose

本文件定义 Askora 当前稳定的**用户体验架构**：用户如何理解产品、如何找到当前位置、如何进入学习、如何保持长期学习上下文，以及不同界面区域分别承担什么职责。

它回答：

> **用户如何使用 Askora，而不是 Askora 有哪些 capability，也不是软件内部如何实现。**

正式边界：

```text
Product Definition = WHAT the product must provide
Experience Design  = HOW the learner understands and uses it
System Design      = HOW the software owns and implements it
```

如果本文件与 Product Definition 冲突，应报告 `DESIGN–DEFINITION GAP`；如果实现与本文件冲突，应报告 `DESIGN–IMPLEMENTATION GAP`。

---

## 2. Authority and Change Control

本文件是当前 Experience Architecture 的 consolidated current truth。

历史增量设计：

- `../UX-Architecture-Canonical-Design-Delta.md`
- `../Interactive-Element-System-Canonical-Design-Delta.md`

其已被本 Experience 文档体系吸收。历史 Delta 继续作为设计演进记录保留，但新的实现和 Spec 不应要求执行代理通过 Supersession Matrix 自行推断当前体验模型。

重大 Experience 变更仍应遵循：

```text
Product Definition
→ Design / Design Delta
→ ADR（需要稳定决策记录时）
→ 更新本 Canonical Experience Design
→ UI / UX Specs
→ Linear / EXEC
→ Implementation
```

---

## 3. Experience Principles

### EXP-001 — Learning Outcome First

Askora 的界面必须优先帮助用户形成、验证并保持真实能力，而不是最大化对话轮次、内容消费量、停留时间或操作数量。

### EXP-002 — Learning, Not System Management

用户的主要任务是学习，不是管理 `LearningGoal`、`LearningPlan`、`LearnerState`、`Evidence` 等内部/领域对象。

领域对象只有在明确 user job 下才进入页面、Disclosure 或 task flow；对象存在不自动意味着存在常驻导航或管理页。

### EXP-003 — One Primary Learning Context

一次学习过程中必须存在清晰的主要上下文：当前 Workspace、当前 LearningActivity、当前学习任务以及完成该任务所需的资料/反馈。

界面不得同时让多个同等级 Dashboard、Card 或导航中心争夺主任务。

### EXP-004 — Data Honesty

未知、缺失、低置信度、部分、过期、受助、答案暴露、失败等状态必须诚实呈现，不得为了界面完整而伪造计划、掌握度、推荐原因、来源或保存成功。

### EXP-005 — Progressive Complexity

用户完成主要学习任务不应被迫理解系统全部内部结构。复杂信息应按照：

```text
需要完成任务的核心信息
→ 当前上下文
→ 可选解释 / provenance
→ 高级 / 审计信息
```

逐层暴露。

### EXP-006 — Continuity Over Page Count

Askora 是长期学习工具。跨天、跨 session、跨资料时，体验必须优先保持：当前位置、当前任务、未完成工作、来源位置和下一步方向，而不是依赖用户重新建立上下文。

---

## 4. Product Structure vs User-facing IA

### 4.1 Product / Domain Structure

Product Definition 拥有：

```text
Workspace
LearningProject
Material
UserNote
LearningGoal
LearningObjective
LearningPlan
LearningActivity
LearningSession
Attempt
LearningEvidence
LearnerState
Review / Validation Obligation
LearningHistory
```

这些对象回答“产品中什么是真实存在的对象与能力”。

### 4.2 User-facing Information Architecture

Experience Design 拥有：

- 用户看到哪些稳定信息空间；
- 什么是一级入口；
- 哪些对象只在上下文中出现；
- 用户如何从一个任务转入另一个任务；
- 哪些信息属于主任务、辅助信息或高级 Disclosure。

### 4.3 Route Structure

具体 URL、redirect、deep-link compatibility、route parameter 属于 UI Spec，不属于本文件的稳定 IA 概念。

---

## 5. Canonical User-facing IA

### EXP-IA-001 — Stable Product Domains

Askora v1 的稳定 Product Domain 为：

```text
今天
学习
资料库
```

它们分别回答：

| Domain | 用户问题 |
|---|---|
| 今天 | 我现在最值得做什么？为什么？ |
| 学习 | 我现在在哪里学习，并如何继续？ |
| 资料库 | 我的学习资料与来源在哪里？ |

### EXP-IA-002 — Utilities Are Not Product Domains

Settings、Recovery 等是 App Utility，不与三个 Product Domain 等权。

Search / Command 只有在正式 capability 与 contract 存在时才作为 Utility 暴露，不得为了“功能完整”预留空入口。

### EXP-IA-003 — Learning Is Not a Four-facet Management Center

`Goal / Plan / Progress / History` 继续作为 canonical product truth 与必要的 contextual task flow 存在，但**不再作为 Learning 的常驻管理 Facets**。

用户只有在明确任务需要时进入：创建/纠正目标、查看计划原因、理解证据、恢复历史或审计状态。

### EXP-IA-004 — Chat Is Not a Product Domain

Conversation / Tutor 是 LearningActivity 的交互形式之一，不是 L0 Product Domain，也不是 Askora 的产品心智模型。

---

## 6. Workspace Experience Model

### EXP-WSP-001 — Workspace Is the Long-term Context

Workspace 是用户可理解的长期学习上下文，同时服从 Product / ADR 已冻结的 durable scope。

界面不得用 route、subject、session title 或 frontend local state 冒充 Workspace truth。

### EXP-WSP-002 — Shared Context

进入学习时，导航、中央学习画布、资料、笔记与方向信息必须解析同一当前 Workspace。

切换 Workspace 意味着学习上下文切换，而不是仅改变 Sidebar 的 selected 样式。

### EXP-WSP-003 — Switching Must Preserve Work

Workspace 切换不得静默丢弃：

- 未提交回答；
- streaming 中的运行；
- 未持久化笔记；
- 当前打开资料及位置；
- 可恢复的学习 session。

exact persistence / command / version mechanics 由下游 Spec 定义。

---

## 7. Primary Learning Workspace

桌面/宽屏的 Experience responsibility 固定为：

```text
Left / Where        Center / Learn             Right / Reference & Notes

Product navigation  Teaching content           Learning Notes
Workspace context   Questions / tasks           Current Material
Workspace switch    Learner answers             Citation / source context
                    Feedback
                    Learning Context Drawer
                    Composer
```

### EXP-LAYOUT-001 — Left = Where

左侧只承担：

- 稳定产品导航；
- 当前 Workspace 可见性；
- Workspace 切换。

不得承担 Goal/Plan/Progress/Evidence 的常驻管理 Dashboard。

### EXP-LAYOUT-002 — Center = Learn

中央区域是唯一 Primary Learning Canvas，优先呈现：

- 当前教学内容；
- 当前问题/任务；
- 学习者作答；
- 反馈与修正；
- 必要的 assistance / validation / citation 状态；
- 当前可执行动作。

中央区域不得退化成综合 Dashboard。

### EXP-LAYOUT-003 — Learning Context Drawer = Orientation

Learning Context Drawer 位于输入/Composer 上方，默认收起，只提供轻量方向：

- 当前阶段；
- 阶段目标；
- 接下来 1–3 个动态学习方向。

它不是 Goal/Plan/Progress 管理器，也不是 Teaching Policy 控制台。

### EXP-LAYOUT-004 — Right = Reference / Notes

右栏服务“边学边写、边学边对照”，v1 只承担：

- 用户学习笔记；
- 当前资料 / citation source context。

右栏可隐藏，但隐藏不能移除完成当前任务所需的唯一信息。

不得为大纲、Evidence、知识图谱、Progress、AI Summary、Flashcards、错题本建立 placeholder/disabled tab。

---

## 8. Core Journeys

### EXP-JOURNEY-001 — First Meaningful Learning

```text
准备必要条件
→ 导入/确认学习材料
→ 明确 Learning Goal
→ 建立可开始的 LearningActivity
→ 进入真实学习
```

首次使用流程只解释用户必须理解的步骤，不暴露内部系统阶段。

### EXP-JOURNEY-002 — Daily Continuation

```text
Today
→ 当前最值得进行的 LearningActivity
→ 理解为什么现在做
→ 开始/继续
→ Learning Workspace
```

当存在 canonical activity 时，Today 只有一个最高层级 Primary Learning Task。

### EXP-JOURNEY-003 — Material to Active Learning

```text
Library / Current Material
→ 阅读或定位来源
→ 进入解释 / 问题 / retrieval / practice
→ Attempt
→ Feedback
```

资料消费不是学习闭环终点；Experience 应支持从“看材料”自然进入主动学习。

### EXP-JOURNEY-004 — Interrupted Learning Recovery

```text
重新进入 Askora
→ 恢复 Workspace
→ 恢复 current activity/session/context
→ 识别未完成状态
→ 继续学习
```

恢复必须基于 durable truth；浏览器内存不等于已保存。

### EXP-JOURNEY-005 — Review / Validation Return

用户因延迟复习、迁移验证或受助后的独立验证重新进入学习时，应被引导回真实 LearningActivity，而不是只看到提醒数字或掌握度 Dashboard。

---

## 9. Responsive Experience

Askora v1 是 Local Web，当前主要目标是桌面浏览器，同时必须在窄屏保持任务可完成。

概念优先级：

```text
Primary learning task
→ Current state / error
→ Required action
→ Context / source
→ Local controls
→ Global navigation / utilities
```

窄屏可改变 presentation pattern，例如 rail → drawer、right rail → sheet，但不得改变语义职责，也不得永久隐藏引用、错误、帮助状态或 validation obligation。

具体 breakpoint 属 UI Spec。

---

## 10. Content and Language Principles

用户界面语言必须：

- 使用简体中文作为 v1 正式语言；
- 优先使用学习者可理解词汇，而不是 `SYSxx`、DTO、version id；
- 清楚区分“建议”“估计”“已验证”“受助”“答案已暴露”；
- 错误说明回答：发生了什么、数据是否安全、现在能做什么；
- 不把系统/模型故障表达成学习者失败；
- 不使用游戏化奖励替代真实学习证据。

---

## 11. Explicit Non-goals

本文件不定义：

- Product Capability inclusion；
- LearningGoal / Plan / Evidence schema；
- Teaching Policy / Assessment / Mastery algorithm；
- API / persistence / state management；
- React component tree；
- route exact path；
- design token；
- CSS breakpoint；
- telemetry / analytics implementation；
- 当前 Linear backlog。

---

## 12. Downstream Contract Split

本 Canonical Experience Design 的下游应保持：

```text
EXPERIENCE-ARCHITECTURE
LEARNING-EXPERIENCE
INTERACTION-MODEL
        ↓
Screen & Navigation Contracts
Learning Interaction Contracts
Design System
Quality & Regression
        ↓
Frontend technical read-model / interface specs
        ↓
EXEC / Code / Tests
```

UI Spec 必须只保存**当前有效规则**。历史 superseded 条款由 ADR / Git history 保存，不应继续与 current normative clauses 共存在同一执行合同中。
