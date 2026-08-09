# Askora UI Information Architecture Specification

> Spec ID：`UI-IA-*`
> 状态：`FROZEN`
> 依赖：`ARCH-001`、`ARCH-020`、`STATE-012`、Canonical Design 10.1～10.4

## 1. 产品模式

### UI-IA-001 — Learning-loop First

全局导航与首页 MUST 围绕“目标、计划、活动、证据、复习”组织。Chat/session MAY 作为活动执行和历史记录存在，但 MUST NOT 继续作为产品唯一或默认的顶层信息架构。

### UI-IA-002 — One Activity, Multiple Presentation Modes

“导师工作台”和“沉浸学习” MUST 是同一 `LearningActivity` / canonical execution 的两种呈现模式。切换模式不得创建第二 TeachingAction、第二 Attempt 或第二消息事实源。

### UI-IA-003 — Evidence, Not Gamification

导航和首页 SHOULD 优先显示需要采取的学习行动及其原因。连续天数、聊天轮数、时长、点赞、token 等 MAY 作为次级过程信息，但 MUST NOT 成为主导航、主成就或学习效果证明。

### UI-IA-004 — Private Local App

Askora 当前是私人本地应用。UI MUST 清晰呈现本地运行/外部模型配置状态，但 MUST NOT 使用“已认证”“绝对隐私”“完全离线”等未经事实支持的宣称。

## 2. 全局导航

冻结候选导航：

| 顺序 | 标签 | 目标 | 默认路由 |
|---:|---|---|---|
| 1 | 今天 | 今日计划、当前活动、到期复习与推荐原因 | `/today` |
| 2 | 学习目标 | 已存在目标及状态的只读视图 | `/goals` |
| 3 | 学习路径 | 当前 LearningPlan、活动顺序、约束与理由 | `/path` |
| 4 | 资料库 | 文档、处理状态、知识节点与关系图 | `/library` |
| 5 | 学习证据 | canonical mastery evidence、置信度与待验证项 | `/evidence` |
| 6 | 历史记录 | 会话、活动和结果的历史入口 | `/history` |
| 7 | 设置 | 账号、运行模式、模型配置事实、退出 | `/settings` |

`错误恢复中心` 是设置中的 station，不新增常驻一级导航。AppShell 只在存在 active/waiting issue
时显示紧凑全局指示器；指示器只导航，不直接执行恢复动作。

### UI-IA-010 — Navigation Vocabulary

一级导航标签使用 2～4 个中文字符，禁止使用内部系统编号、算法名或 `SYS03/SYS05` 等工程术语作为主导航。

### UI-IA-011 — Dialog Demotion

旧“对话学习” MUST 从一级导航移除。对话入口只允许出现于：

- 当前 LearningActivity；
- 历史会话；
- 明确标记的兼容快速学习入口。

### UI-IA-012 — Compatibility Quick Start

在 LearningGoal command 尚未形成正式 UI/API 合同前，旧 subject / knowledge-point session creation MAY 作为“快速学习（兼容入口）”保留，但必须：

- 与 goal-driven plan 明确区分；
- 内部继续进入同一 canonical facade；
- 不伪造 LearningPlan、ReviewSchedule 或 mastery；
- 标明 retirement condition：正式 goal/activity launch flow 可用且完成迁移。

## 3. 路由合同

### UI-IA-020 — Canonical Routes

| 路由 | 页面 | Shell |
|---|---|---|
| `/today` | 学习驾驶舱 | Standard |
| `/goals` | 学习目标 | Standard |
| `/path` | 学习路径 | Standard |
| `/library` | 资料库 / 知识地图 | Standard + Inspector |
| `/evidence` | 学习证据 | Standard + Inspector |
| `/history` | 历史记录 | Standard |
| `/settings` | 设置 | Standard |
| `/settings/recovery` | 错误恢复中心 | Standard |
| `/learn/:activityId` | 导师工作台 | Workspace |
| `/quick/:sessionId` | 兼容快速学习工作台 | Workspace + Compatibility Label |
| `/focus/:activityId` | 沉浸学习 | Focus |
| `/login` | 登录 / 注册 | Auth |

后端无法 ready 时，Electron MUST 在 protected router 之外显示 bootstrap recovery shell。登录页、
今天页或设置页都依赖后端，因此不能作为唯一启动恢复入口。

### UI-IA-021 — Legacy Route Migration

旧路由 MUST 采用 hash-router 兼容 redirect，不得静默失效：

```text
/          → /today
/profile   → /evidence
/knowledge → /library
/account   → /settings
```

Redirect 不得修改业务状态，且至少保留一个已发布版本周期或直到历史桌面 deep link 已验证迁移。

### UI-IA-022 — Unknown Route

未知路由 MUST 进入可理解的 Not Found / recovery 页面或 canonical default route。MUST NOT 因错误路由触发新会话、新活动或登录状态变化。

### UI-IA-023 — Compatibility Workspace Route

在 canonical activity/session link 与 StartLearningActivity command 冻结前，现有 dialog session MUST 通过 `/quick/:sessionId` 进入工作台，并显著标记“兼容快速学习”。该路由必须执行当前用户 ownership check、继续调用 canonical dialog facade，且不得将 `sessionId` 伪装为 `activityId`。Retirement condition：canonical activity launch/link query 完成并覆盖受支持 session。

## 4. Shell 合同

### UI-IA-030 — Standard Shell

桌面 Standard Shell 使用三段式布局：

```text
Global Navigation | Primary Content | Optional Context Inspector
```

- Global Navigation：固定产品区域，不承载当前页面局部筛选；
- Primary Content：页面主任务；
- Context Inspector：推荐原因、证据来源、状态解释、引用等只读上下文；
- Inspector MAY collapse；其隐藏不得丢失完成主任务所需的唯一信息。

### UI-IA-031 — Workspace Shell

导师工作台使用：

```text
Activity / History Rail | Conversation & Task Canvas | Learning Context Inspector
```

中央画布是唯一主交互区域；两侧只提供导航和上下文。当前目标、当前帮助上限与待独立验证状态必须可见，但不得允许用户直接改写 canonical policy state。

### UI-IA-032 — Focus Shell

沉浸学习模式 MUST：

- 一次只呈现一个 activity/task；
- 保留退出、保存/暂停和必要的帮助入口；
- 复用同一消息、Attempt、TeachingAction 与 actual assistance 记录；
- 不以视觉隐藏的方式绕过 citation、security、assessment integrity 或 exposure guard。

### UI-IA-033 — Auth Shell

Auth Shell 只承载登录、注册、开发态说明与错误恢复。账号设置不得混入登录主任务；开发自动登录不得通过前端 fallback 假装成功。

## 5. Responsive Contract

### UI-IA-040 — Desktop-first Breakpoints

实现必须至少验证：

- 1440×900：完整三段式；
- 1024×768：Inspector 可收起，主任务不压缩到不可读；
- 768×1024：Navigation 进入 drawer/compact rail；
- 360×800：单列布局，无横向页面滚动。

具体 CSS breakpoint MAY 调整，但上述行为不可改变。

### UI-IA-041 — Narrow-screen Priority

窄屏优先级：

```text
Primary Task
→ Current State / Error
→ Required Action
→ Context / Evidence
→ Global Navigation
```

Context Inspector 在窄屏 MUST 变为可访问的 sheet/section，不得永久消失。Focus 模式的帮助入口不得因为窄屏被移除。

### UI-IA-042 — No Nested Critical Scroll

主要操作区域 SHOULD 避免同时出现页面滚动、消息滚动和 Inspector 滚动三层关键滚动。任何必须内部滚动的区域都必须有明确边界与键盘可达性。

## 6. Navigation and State Preservation

### UI-IA-050

页面切换 MAY 保留 presentation-only 状态，例如当前筛选、展开节点、Inspector 可见性。它 MUST NOT 把未提交草稿、未确认答案或正在 streaming 的 run 静默丢弃。

### UI-IA-051

离开有未提交内容或正在执行的 activity 时，UI MUST 给出明确状态：已保存、仍在执行、可恢复或需要确认。不得仅依赖浏览器内存假装 durable recovery。

### UI-IA-052

返回历史消息、活动或计划版本时，UI MUST 清晰区分只读历史与当前 active state，避免用户把旧 DecisionTrace、旧 plan 或旧 evidence 误认为当前状态。

## 7. Acceptance Criteria

- `UI-IA-AC-001`：一级导航不含“对话学习”，默认入口为 `/today`。
- `UI-IA-AC-002`：导师工作台与沉浸模式复用同一 activity/execution identity。
- `UI-IA-AC-003`：旧 `/`、`/profile`、`/knowledge`、`/account` 有无副作用兼容跳转。
- `UI-IA-AC-004`：1440、1024、768、360 宽度下主任务均可完成且无页面横向滚动。
- `UI-IA-AC-005`：Inspector 收起或窄屏重排不会隐藏完成任务所需的唯一信息。
- `UI-IA-AC-006`：兼容快速学习入口与 goal-driven plan 有明确标识和 retirement condition。
- `UI-IA-AC-007`：历史状态与当前 active state 不会在视觉或交互上混淆。
- `UI-IA-AC-008`：兼容 session 使用独立 `/quick/:sessionId` 路由，不冒充 canonical LearningActivity。

## 8. Forbidden Implementations

禁止：

- 把新侧边栏当作完成学习驾驶舱；
- 继续让 `/` 直接进入 subject picker/chat-first 主链；
- Focus 模式另写一套消息或评估逻辑；
- 在 Inspector 内提供直接修改 mastery、TeachingAction 或 next_due_at 的控件；
- 为适应小屏把引用、帮助状态、错误或独立验证义务完全隐藏；
- 用前端 route/session state 充当 LearningActivity、LearningPlan 或 ReviewSchedule truth。

## 9. P1-06 Welcome Entry

### UI-IA-060

`/welcome` 是 protected supporting route，不新增一级导航。只有 intended `/` 或 `/today` 在服务端
`should_enter_welcome=true` 时可 replace；`/library`、`/book-learning/:documentId`、
`/learn/:activityId` 及其他 explicit deep link MUST 保留。

### UI-IA-061

Settings 固定提供“重新打开首次引导”。Dismiss 后返回 `/today`；query failure 保留 intended route 并
提供非阻断恢复提示，不得造成 redirect loop。
