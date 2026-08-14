# Askora Experience Architecture

> 状态：**Canonical Experience Design Baseline**  
> 冻结日期：2026-08-13  
> 适用范围：Askora v1 Experience / IA / Navigation / Workspace / Journey 设计  
> 上游：[`../../product/PRODUCT-STRATEGY.md`](../../product/PRODUCT-STRATEGY.md)、[`../../product/PRODUCT-POSITIONING.md`](../../product/PRODUCT-POSITIONING.md)、[`../../product/PRODUCT-DEFINITION.md`](../../product/PRODUCT-DEFINITION.md)  
> 关键已接受决策：[`../../archive/adr/ADR-0014-user-job-driven-interaction-architecture.md`](../../archive/adr/ADR-0014-user-job-driven-interaction-architecture.md)、[`../../archive/adr/ADR-0018-ux-workspace-context-architecture.md`](../../archive/adr/ADR-0018-ux-workspace-context-architecture.md)、[`../../archive/adr/ADR-0022-course-centric-information-architecture.md`](../../archive/adr/ADR-0022-course-centric-information-architecture.md)、[`../../archive/adr/ADR-0025-space-conversation-core-journeys.md`](../../archive/adr/ADR-0025-space-conversation-core-journeys.md)、[`../../archive/adr/ADR-0026-close-journey-goal-and-unassigned-material-gaps.md`](../../archive/adr/ADR-0026-close-journey-goal-and-unassigned-material-gaps.md)、[`../../archive/adr/ADR-0027-welcome-home-not-first-use-wizard.md`](../../archive/adr/ADR-0027-welcome-home-not-first-use-wizard.md)、[`../../archive/adr/ADR-0029-local-and-hybrid-material-parse.md`](../../archive/adr/ADR-0029-local-and-hybrid-material-parse.md)
> 下游实现合同：[`../../specs/ui.md`](../../specs/ui.md)

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

历史增量设计已吸收进本文件；原文不在 current。溯源见 [`ADR-0018`](../../archive/adr/ADR-0018-ux-workspace-context-architecture.md) 与 [`ADR-0014`](../../archive/adr/ADR-0014-user-job-driven-interaction-architecture.md)。新的实现和 Spec 不应要求通过 Supersession Matrix 自行推断当前体验模型。

重大 Experience 变更：

```text
Product Definition
→ 更新本 Experience Design
→ 更新 specs/ui.md
→ 需要稳定决策记录时追加 ADR
→ Linear / implementation
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

### EXP-IA-001 — Space-centric Product IA

Askora v1 的稳定用户侧 IA 为：

```text
Welcome                      Default Destination
已有对话                      Resumable Learning Process Navigation
＋ 新建空间                   Explicit Action
资料库                        Stable Product Domain Navigation
Settings / Recovery           Utilities
```

`今天` 与 `学习` 不再是 stable Product Domain 或 L0 Navigation。`课程` / `＋ 新课程` 不再是用户侧词汇。

- Welcome 回答“我打开 Askora 后先到哪里”；
- 空间回答“长期学习上下文与进度记在哪里”；
- 对话回答“哪一段可恢复的学习过程”；
- 资料库回答“学习资料与来源在哪里”。

不得以 Goal、Plan、Progress、Knowledge Graph、Agent、Chat History 或新的 Dashboard 替代 Welcome / 空间 / 对话。

### EXP-IA-002 — Utilities Are Not Product Domains

Settings、Recovery 等是 App Utility，不与空间上下文或资料库等权。

Search / Command 只有在正式 capability 与 contract 存在时才作为 Utility 暴露，不得为了“功能完整”预留空入口。

### EXP-IA-003 — Space Is Not a Management Center

`Goal / Plan / Progress / History` 继续作为 canonical product truth 存在，但不作为空间的常驻管理 Facets，也不出现在主路径 Journey 上。

主路径不要求用户创建、确认或管理目标。查看计划原因、证据或历史只在明确任务需要时进入。Goal 由系统按 `PD-RULE-004` 维护。

### EXP-IA-004 — Chat Is Not a Product Domain

Conversation / Message / Tutor 是学习过程的交互形式，不是 L0 Product Domain，也不是 Askora 的产品心智模型。

用户界面的「对话」是某空间内一次可恢复学习过程的称呼，对应 canonical `LearningActivity`，不是 Chat thread，不新增 Product Object，不得用 Chat 1/2/3 或轮次计数组织。

### EXP-IA-005 — Create Space and Start Learning Are Actions

以下才是会写入的 `Action`：

- `＋ 新建空间`：提交后创建真实 Workspace；
- 上传资料：只创建 `Material`，不创建空间或对话；
- 加入学习空间：把已处理资料归属到选定或当场新建的空间；
- 马上开始学习：系统自动创建空间、放入刚上传的资料、开第一段对话；
- 对某空间「继续学习」：在该空间新开一段对话；
- 开始尚未 active 的对话 / 学习活动：正式 lifecycle Action。

进入创建流程的 Navigation 不得产生业务写入。没有真实 command/readiness 时不得显示 placeholder、disabled future entry 或 frontend-only success。

### EXP-IA-006 — User-facing Object Model

```text
空间  1 ── n  资料
空间  1 ── n  对话
```

| 用户文案 | Canonical | 创建时机 |
|---|---|---|
| 资料 | `Material` | 用户上传成功 |
| 空间 | `Workspace` | 用户显式新建；加入空间时当场新建；「马上开始学习」自动创建 |
| 对话 | `LearningActivity`（用户侧称呼） | 开始学习或对空间「继续学习」 |

`LearningProject` 仍是 Workspace 内可选组织对象，不与「空间」互换。不得创建第二套 `space_id` / `conversation_id` 身份。

---

## 6. Workspace Experience Model

### EXP-WSP-001 — Space Is the User-facing Long-term Context

用户界面统一使用“空间”表达长期学习上下文；canonical `Workspace` identity、scope 与 owner 保持不变。

`LearningProject` 继续是 Workspace 内可选组织对象，不与“空间”互换。「对话」不与空间互换。

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

### EXP-WSP-004 — Space Switching Changes Real Scope

切换空间必须切换同一 canonical Workspace scope 下的 Activity、Session、Materials、Retrieval、Notes、Current Material、Goal/Plan/LearnerState/Review projections 与 History/resumable state。Selection 与 switch Action 分离；route、Sidebar selected state、React state 或 localStorage 不构成切换成功。

### EXP-WSP-005 — One Space, Many Conversations

一个空间可以包含多段对话。对话标题使用学习目的，不使用 Chat 1/2/3。

- 打开已有可恢复对话是 Navigation / InteractiveContent，不得创建第二 Activity / Session / transcript；
- 对某空间「继续学习」是 Action，必须调用 SYS06 owner 创建/启动新的 LearningActivity，并继承该空间的学习进度；
- 启动尚未 active 的对话必须使用正式 Action。

---

## 7. Primary Learning Workspace

桌面/宽屏的 Experience responsibility 固定为：

```text
Left / Where        Center / Learn             Right / Reference & Notes

Welcome              Teaching content           Learning Notes
已有对话              Questions / tasks           Current Material
＋ 新建空间           Learner answers             Citation / source context
当前空间（学习中）
Library / Utilities
                    Feedback
                    Learning Context Drawer
                    Composer
```

### EXP-LAYOUT-001 — Left = Where

左侧只承担：

- Welcome destination；
- 已有对话列表（恢复入口）；
- `＋ 新建空间` Action；
- 学习中的当前空间上下文；
- 资料库与 Utility navigation。

不得承担 Goal/Plan/Progress/Evidence 的常驻管理 Dashboard。不得把左侧做成 Chat thread manager。

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

现行 Core Journey 四条，覆盖用户侧主工作，不覆盖 Settings / Recovery / 备份等 Utility。Product / Positioning / SYS06 / Platform 已按 ADR-0026 与这四条对齐：开始学习不确认目标；上传允许未归属空间的资料。

```text
001 用资料开始学习
002 回来继续
003 在对话里学习
004 建立或扩充空间
```

`001` / `002` / `004` 的终点是进入或回到 `003`。`003` 的细部语义（Attempt、帮助、证据、引用、笔记）由 [`LEARNING-EXPERIENCE.md`](LEARNING-EXPERIENCE.md) 拥有；本文件只冻结用户可走的主路径。

每一步区分：用户做 / 系统做 / 用户看到。系统内部阶段（解析、诊断、规划、生成目标）不得要求用户当作步骤来完成。

### EXP-JOURNEY-001 — Materials to First Learning

**情境：** 用户有自己的材料，想开始用 Askora 学。  
**期望：** 放下资料后进入学习；不必先理解目标、计划或内部对象。

```text
上传资料
→ 系统处理
→ 选择「加入学习空间」或「马上开始学习」
→ 进入对话，或回到 Welcome
```

| 阶段 | 用户做 | 系统做 | 用户看到 |
|---|---|---|---|
| 放入资料 | 上传 | 只创建 `Material` | 处理中；不得假装已有空间或对话 |
| 处理 | 等待 | 先完成本地解析；模型可用且开关开启时再做 AI 增强 | 不出现目标管理；写清「仅本机解析」或「已用模型增强」；无 key 不得假装已用模型 |
| 决定去向 | 选「加入学习空间」或「马上开始学习」 | 按选择执行 | 二选一 |
| 加入空间 | 选已有空间；没有则可当场新建 | 资料归属该空间 | 再问：要不要现在开始学习 |
| 现在学（加入之后） | 要 / 不要 | 要：在该空间开一段对话；不要：结束本次 | 对话，或回到 Welcome |
| 马上开始学习 | 选这条 | 自动建空间、放入刚上传的资料、开第一段对话 | 进入对话 |

首次使用只解释用户必须理解的步骤。处理中 / 失败必须可理解；系统故障不得显示成学习者失败。

### EXP-JOURNEY-002 — Return and Continue

**情境：** 用户再次打开 Askora。  
**期望：** 能接着某段对话，或按某个空间的进度往下学。

```text
打开 Askora
→ Welcome（侧栏挂着已有对话）
→ 点某段对话恢复
  或 在 Welcome 选空间并点「继续学习」
```

| 阶段 | 用户做 | 系统做 | 用户看到 |
|---|---|---|---|
| 打开 | 打开 Askora | 不自动新建空间 / 对话 / Session | **每次先 Welcome**；侧栏是已有对话 |
| 续聊 | 点侧栏某段对话 | 恢复同一段对话 | 该对话的现场；不新开 |
| 按空间续学 | 选空间，点「继续学习」 | 分析该空间进度，**新开一段对话**接续 | 新对话；旧对话仍在侧栏 |

启动解析与 redirect 不得创建空间、对话或 Session，也不得修改 Workspace truth。打开某段已有对话不得复制 Activity / transcript。对空间「继续学习」必须走正式 owner Action。

复习 / 迁移 / 受助后的独立验证通过「继续学习」或打开相关对话回到真实学习过程，而不是提醒数字或掌握度 Dashboard。

恢复已有对话必须基于 durable truth；浏览器内存不等于已保存。

### EXP-JOURNEY-003 — Learn in a Conversation

**情境：** 用户已经在某段对话里。  
**期望：** 能真正想、答、看反馈；需要时要帮助或看原文；停下来之后还能接上。

```text
知道我现在在学什么
→ 思考并作答
→ 看到诚实反馈
→ 需要时请求帮助或查看原文
→ 再试，或做一次独立验证
→ 停下来可恢复，或进入真实的下一步
```

| 阶段 | 用户做 | 系统做 | 用户看到 |
|---|---|---|---|
| 定向 | 进入或回到这段对话 | 呈现当前任务与必要上下文 | 在哪个空间、这段对话要做什么；不出现 Goal/Plan 管理 |
| 作答 | 思考并提交 Attempt | 记录真实 Attempt；评估 | 自己的回答被保留 |
| 反馈 | 阅读反馈 | 说明哪部分成立、哪部分要改、下一步是什么 | 学习反馈，不是「你答错了」式的系统故障 |
| 请求帮助 | 要解释 / 提示 / 例子 / 直接答案 | 按 request 与 Teaching Policy 响应；保留暴露语义 | 帮助状态可读（独立 / 已用帮助 / 已暴露答案 / 待验证） |
| 对照来源 | 点引用或查看原文 | 打开真实来源，不把用户带离当前对话 | 可读出处；无来源时说不可用 |
| 写笔记 | 写下自己的文字 | 保存为 `UserNote`；不无确认覆盖原文 | 保存中 / 已保存 / 失败 诚实 |
| 再试 | 再次作答 | 作为新的 Attempt，不覆盖旧回答 | 两次作答都可追溯 |
| 这一段结束 | 停下，或接受系统给出的下一步 | 给真实下一步，或诚实说没有 | 继续当前对话 / 新对话 / 可恢复暂停 / 仍需独立验证 |

阅读完成、点「懂了」、AI 代答不得被包装成独立掌握。补救必须留在当前空间 / 对话 / 资料上下文，并回到新的 Attempt。

本 Journey 的教学、评估与证据规则听 [`LEARNING-EXPERIENCE.md`](LEARNING-EXPERIENCE.md) 与 `docs/specs/systems/`。

### EXP-JOURNEY-004 — Create or Extend a Space

**情境：** 用户要先有一个长期容器，或给已有空间补充资料。  
**期望：** 不必先开聊也能建空间；后补的资料能进同一个空间。

```text
＋ 新建空间
→ 得到空空间
→ 放入资料，或先不学

或

已有空间
→ 再上传 / 加入资料
→ 系统处理
→ 问要不要现在开始学习
```

| 阶段 | 用户做 | 系统做 | 用户看到 |
|---|---|---|---|
| 显式新建 | 提交「新建空间」 | 创建真实 Workspace | 一个空空间；不是对话 |
| 空空间 | 可先离开 | 不自动开对话，不编造资料或目标 | 诚实的空态：可以加资料，还不能开始有依据的学习 |
| 往已有空间加资料 | 上传或从资料库加入 | 只创建或归属 `Material`，再处理 | 处理中；完成后问要不要现在开始学习 |
| 现在学 | 要 / 不要 | 要：在该空间开一段对话（走 `003`）；不要：留在空间 / Welcome | 对话，或资料已在空间里 |

没有资料时，「开始学习 / 继续学习」必须说明还缺依据，不得进入伪装成有来源的对话。后补资料的处理完成弹窗与 `001` 相同：加入哪个空间（默认当前空间）以及要不要现在学。

`001` 是「手上有资料，第一次决定去哪」；`004` 是「先有空间，或以后再往里加东西」。不要把两条合成一个必须先建空间才能上传的向导。

上传未归属空间的 Material 服从 `PD-REQ-0101` 与 `WSP-021`：允许 `workspace_id=null`；归属前不得开始有依据的学习。目标不出现在主路径，服从 `PD-RULE-004` / `PD-REQ-0203`。

### EXP-PARSE-001 — Local Parse Always; AI Parse Is Optional

资料处理只有两种模式，不是两种产品：

```text
仅本机解析     始终发生，不依赖模型 key
本机 + AI 增强  叠在本机结果上，由设置开关与模型就绪共同决定
```

本地解析成功后就可以问「加入学习空间 / 马上开始学习」。用户可以打开原文、写笔记、把资料加入空间。不得把「仅本机解析」说成「模型已经读懂全书」。

### EXP-PARSE-002 — Parse Toggle Lives in Settings

设置里、紧挨模型配置，提供一个 Control：**用 AI 增强资料解析**。

- 不要放在 Welcome 主按钮上，也不要每次上传再问一次；
- 没有 key / 模型未就绪：开关不可用，强制仅本机解析，并说明原因；
- 有可用模型：默认打开，用户可关掉；
- 打开开关不得自动把已经解析过的资料发给模型。

这个开关只约束**解析上传资料**。对话里的讲解、出题、反馈仍可能使用模型；界面不得暗示关掉它等于 Askora 完全离线。

### EXP-PARSE-003 — Re-parse Is an Explicit Action

模型就绪后，对仅本机解析过的资料提供「用模型再解析」。这是同一份资料的增强，不是重传，也不是新资料。AI 增强失败时，本机结果仍可用；状态写成「本机已就绪，模型增强失败」，可重试增强。

「马上开始学习 / 继续学习 / 进入对话」若当前需要模型生成教学，而模型不可用：资料可以已就绪，但必须说明还缺模型、数据是否安全、现在能去设置。不得用假教师或 mock 对话冒充学习。

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
- 正常用户界面使用“空间”“对话”，不用 `Workspace` / `LearningActivity` 作为主文案；工程/诊断层仍保持 canonical naming；
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
