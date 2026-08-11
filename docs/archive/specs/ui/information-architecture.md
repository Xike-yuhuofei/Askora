# Askora UI Information Architecture Specification

> Spec ID：`UI-IA-*`、`UXA-IA-*`
> 状态：`FROZEN`
> Governing：`ADR-0014`、`ADR-0018`、`UI-IES-*`、`ARCH-001`、`ARCH-020`、`STATE-012`、`WSP-*`
> Canonical Design：`docs/archive/design/Interactive-Element-System-Canonical-Design-Delta.md`、`docs/archive/design/UX-Architecture-Canonical-Design-Delta.md`

## 0. UX Architecture Absorption (ADR-0018)

本节冻结 `UX-Architecture-Canonical-Design-Delta.md` 经 `ADR-0018` 吸收后的三栏学习架构与 Workspace 上下文。凡与本节冲突的旧 `UI-IA-*` 条款，按 [Supersession Matrix](#12-uxa-supersession-matrix-for-ui-ia) 处置。

### UXA-IA-001 — Three-Column Responsibilities

冻结三栏职责：

```text
Left (Where)      Center (Learn)                    Right (Reference / Notes)
Global Nav        Teaching content                  User-authored notes
Current Workspace Questions                          Current source material
Workspace switch  Learner answers                   Citation / source context
                  Feedback
                  Learning Context Drawer
                  Composer
```

- 左栏只承担稳定产品导航、当前 Workspace 可见性与 Workspace 切换；不得承担 Goal/Plan/Progress/Evidence/图谱详情。
- 中栏是唯一 Primary Learning Canvas，MUST NOT 变成 Dashboard。
- 右栏整体可隐藏，V1 仅学习笔记与当前资料。

### UXA-IA-002 — Shared Canonical Workspace Context

- 三栏 MUST 解析同一个 canonical `current_workspace_id`（`ADR-0016` / `WSP-*` durable Workspace）。
- 不得用 route、subject、session 或 frontend local state 冒充 Workspace truth。
- 切换 Workspace 改变中栏、右栏与 Context Drawer 的全部查询范围，不仅是左栏选中态。
- 单一 Workspace 不得显示虚假 dropdown/switch affordance。
- 无默认跨 Workspace 聚合或全局搜索。

### UXA-IA-003 — Workspace Switching Safety

切换 Workspace 前 MUST 处理并明确呈现 saved / saving / failed / recoverable：

- 未提交回答；
- 正在 streaming 的 run；
- 未持久化的笔记；
- 打开的 Material tabs 与引用位置；
- 可恢复的 active LearningSession。

不得通过清空 React state 假装切换成功。

### UXA-IA-004 — Learning Context Drawer Placement and Default

- Drawer 固定在中栏 composer/输入区正上方，默认收起；它不是第四栏，也不占右栏。
- 收起时只显示一行方向信息，例如 `监督学习基础 · 接下来：残差诊断`。
- 展开只允许：当前阶段、阶段目标、接下来 1..3 个动态知识点/教学方向。
- 禁止 V1 Drawer 加入完整 Goal editor、完整 Plan、Progress Dashboard、Evidence 管理、mastery 编辑、ReviewSchedule 编辑或 TeachingAction/Policy 控制。
- expand/collapse 只改变 presentation state，不触发 owner command。

### UXA-IA-005 — Learning Is Not a Management Console

Learning 主界面不再暴露以下常驻管理 Facets：

```text
Goals
Plan / Path
Progress
History-as-management-facet
```

这不删除 canonical truth：LearningGoal、LearningPlan、LearnerState、Evidence、ReviewSchedule、History 继续存在并驱动教学，但不决定用户必须管理多少页面。必要创建/纠正/确认/恢复/审计可在明确 user job 下进入 contextual task flow，不得恢复长期常驻管理中心。

### UXA-IA-006 — Library v1 No-OCR Exposure

- Library v1 正常 UI 不得暴露：识别扫描 PDF、OCR 状态、OCR candidate、OCR review/publish、OCR confidence/bbox/image hash、把 OCR 描述为 v1 核心能力的文案。
- 扫描 PDF 无可靠文本时诚实显示 `unsupported / partial extraction` 并建议受支持文本型资料。
- 历史/optional OCR runtime 是否保留由 v1 Product Architecture cleanup 决定；即使存在，正常 v1 UI 也不可达。

### UXA-IA-007 — Deferred Candidates

以下不得进入 V1，不得建立 placeholder、disabled tab 或空页面：

```text
大纲
Evidence
知识图谱
Progress
AI Summary
Flashcards
错题本
```

未来加入任何候选都需独立 user-job evidence、owner/query contract、隐私与恢复边界，并形成新 Design Delta / Spec。

### UXA-IA-030 — Route / Deep-link Migration Matrix

旧 `/learning/**` 管理 route 在去管理化后不再承载常驻管理 facet。迁移遵守 NGS（no global side effect）：redirect / compatibility / task-flow 不得触发 owner command、创建 session/activity、或写业务状态。

| Current route | Target route | Redirect / compatibility / task-flow | Deep-link preservation | Business side effect | Retirement condition |
|---|---|---:|---:|---:|---|
| `/learning` | Learning Canvas default stage | Compatibility：Learning 不再管理四 facet | 保留跳转至 central Learning Canvas | None | 无（central Learning 是常驻目标） |
| `/learning/goals` | Contextual task flow（明确 user job 下） | Compatibility→task-flow：仅在创建/纠正/审计 job 下可达 | `/goals/**` 与 goal deep link 保留迁移 | None；不自动创建/修改 goal | 新 Learning 主链稳定后视证据收口 |
| `/learning/goals/new` | Goal task-flow | Task-flow（明确 user job） | 保留 | 仅用户显式提交时创建 | 同上 |
| `/learning/goals/:goalId` | Goal detail context / task-flow | Compatibility→task-flow | 保留 | 只读；编辑需显式提交 | 同上 |
| `/learning/plan` | Contextual plan disclosure | Compatibility→task-flow / Disclosure | 保留 | None；不得 client replan | 同上 |
| `/learning/progress` | Contextual evidence disclosure | Compatibility→Disclosure | Deep link 保留，进入 only when user job | None | 同上 |
| `/learning/history` | History-as-history（非管理 facet） | Compatibility：历史只读，不作为常驻管理入口 | 保留 | None | 同上 |
| `/learn/:activityId` | Learning Canvas（Primary） | 常驻目标 | 保留 | 仅在 activity lifecycle command 下 | 无 |
| `/quick/:sessionId` | 兼容快速学习 | Compatibility（标记来源） | 保留 | 仅 canonical dialog facade | canonical activity link 覆盖后 |
| `/goals` `/path` `/evidence` `/history` `/profile` `/knowledge` `/account` | 见 `UI-IA-031` | 无副作用 redirect | 保留 | None | 迁移周期结束 |

所有旧 route 保持 no-business-side-effect；删除旧 route 前必须满足对应 retirement condition 并完成历史 deep-link 验证。

## 1. 产品模式

### UI-IA-001 — User-job-driven Learning-loop First

全局导航与首页 MUST 从用户任务推导，而不是从 canonical domain object 数量推导。

正式顺序：

```text
User Job
→ Domain Meaning
→ Information Architecture
→ Interaction Semantics
→ Interaction Pattern
→ Visual Component
```

Chat/session MAY 作为 LearningActivity 执行和历史记录存在，但 MUST NOT 成为默认顶层信息架构。

### UI-IA-002 — Three Stable Product Domains

L0 Product Domain 只允许：

```text
今天
学习
资料库
```

`学习目标`、`学习路径`、`进展/学习证据`、`历史记录` 不再分别作为 L0 Product Domain。

### UI-IA-003 — One Activity, Multiple Presentation Modes

“导师工作台”和“沉浸学习” MUST 是同一 `LearningActivity` / canonical execution 的不同呈现模式。切换模式不得创建第二 TeachingAction、第二 Attempt 或第二消息事实源。

### UI-IA-004 — Evidence, Not Gamification

导航和首页 SHOULD 优先显示需要采取的学习行动及其原因。连续天数、聊天轮数、时长、点赞、token 等 MAY 作为次级过程信息，但 MUST NOT 成为主导航、主成就或学习效果证明。

### UI-IA-005 — Private Local App

Askora 是私人本地应用。UI MUST 准确呈现本地运行/外部模型配置事实，但 MUST NOT 使用“绝对隐私”“完全离线”等未经事实支持的宣称。

## 2. L0 Product Domain Navigation

### UI-IA-010 — Canonical L0

| 顺序 | 标签 | 用户问题 | 默认路由 |
|---:|---|---|---|
| 1 | 今天 | 我现在最应该做什么？为什么？ | `/today` |
| 2 | 学习 | 我的目标、路径、进展和历史是什么？ | `/learning` |
| 3 | 资料库 | 我的学习资料和知识来源在哪里？ | `/library` |

一级导航标签使用简洁中文，禁止内部系统编号、算法名或 `SYS03/SYS05` 等工程术语。

### UI-IA-011 — App Utilities Are Not Product Domains

以下属于 App Utility，不与 L0 Product Domain 等权：

- Settings；
- Search / Command；
- Recovery；
- Account utility。

macOS/native host SHOULD 通过 App command / `⌘,` 提供 Settings。Web 开发形态 MAY 保留 utility entry，但视觉层级 MUST 低于三个 Product Domain。

`错误恢复中心` 不新增常驻 Product Domain。仅在存在 active/waiting issue 时显示紧凑全局指示器；指示器只导航，不直接执行恢复动作。

### UI-IA-012 — Dialog Demotion

旧“对话学习” MUST 从 L0 移除。对话入口只允许出现于：

- 当前 LearningActivity；
- 历史 activity/session；
- 明确标记的兼容快速学习入口。

### UI-IA-013 — Compatibility Quick Start

兼容 subject / knowledge-point session creation MAY 暂时保留，但必须：

- 与 goal-driven canonical activity 明确区分；
- 内部继续进入同一 canonical facade；
- 不伪造 LearningPlan、ReviewSchedule 或 mastery；
- 在 canonical next activity 可启动时降为 secondary/overflow；
- retirement condition 明确。

## 3. Learning Domain

### UI-IA-020 — Canonical Learning Facets

`/learning` 是长期学习信息空间，L1 facets 固定为：

```text
目标
路径
进展
历史
```

| Facet | Canonical Meaning | Route |
|---|---|---|
| 目标 | LearningGoal collection / lifecycle | `/learning/goals` |
| 路径 | LearningPlan projection | `/learning/plan` |
| 进展 | SYS03/evidence projection 的用户视图 | `/learning/progress` |
| 历史 | past activity/session/outcome projection | `/learning/history` |

### UI-IA-021 — Domain Semantics Are Preserved

IA 聚合不得改变状态所有权：

- Goal 仍由现有 Goal/SYS06 合同拥有；
- Path 仍是 SYS06 LearningPlan；
- Progress 仍只读取 SYS03 canonical projection；
- History 仍是现有 activity/session/read-model 历史。

`进展` 只是用户 vocabulary，不产生第二份 mastery/evidence truth。

### UI-IA-022 — Facet Navigation

L1 facet navigation MAY 使用 segmented/tab/sidebar local pattern，具体 pattern 由平台适配；semantic role 必须是 Navigation。

切换 facet 本身不得触发 command 或修改 canonical learning state。

## 4. 路由合同

### UI-IA-030 — Canonical Routes

| 路由 | 页面 | Shell |
|---|---|---|
| `/today` | 今日学习 | Standard |
| `/learning` | 学习总览 / default facet | Standard |
| `/learning/goals` | 学习目标 | Standard |
| `/learning/goals/new` | 创建目标 | Standard / Task Flow |
| `/learning/goals/drafts/:draftId` | 目标草稿 | Standard / Task Flow |
| `/learning/goals/:goalId` | 目标详情 | Standard |
| `/learning/goals/:goalId/edit` | 编辑目标 | Standard / Task Flow |
| `/learning/plan` | 学习路径 | Standard |
| `/learning/progress` | 学习进展 | Standard + Optional Inspector |
| `/learning/history` | 学习历史 | Standard |
| `/library` | 资料库 / 知识地图 | Standard + Optional Inspector |
| `/settings` | 设置分类 | Standard / Utility |
| `/settings/recovery` | 错误恢复中心 | Standard / Utility |
| `/learn/:activityId` | 导师工作台 | Workspace |
| `/quick/:sessionId` | 兼容快速学习工作台 | Workspace + Compatibility Label |
| `/focus/:activityId` | 沉浸学习 | Focus |
| `/welcome` | 首次引导 | Supporting |

Settings 二级 route SHOULD 按已实现 capability 逐步拆分，例如：

```text
/settings/ai
/settings/learning
/settings/appearance
/settings/data
/settings/advanced
```

不得为了满足路由表创建没有真实能力的空页面。

### UI-IA-031 — Legacy Route Migration

旧路由 MUST 采用无副作用兼容 redirect：

```text
/          → /today（受 onboarding contract 约束）
/goals     → /learning/goals
/path      → /learning/plan
/evidence  → /learning/progress
/history   → /learning/history
/profile   → /learning/progress
/knowledge → /library
/account   → /settings
```

旧 goal detail/editor routes 同样 MUST 转发到 `/learning/goals/**` 对应 canonical route。

Redirect 不得修改业务状态、创建 session/activity 或触发 command。至少保留一个已发布迁移周期，或直到历史 deep link 已验证迁移。

### UI-IA-032 — Unknown Route

未知路由 MUST 进入可理解的 Not Found / recovery 页面或 canonical default route。MUST NOT 因错误路由触发新会话、新活动或 LocalOwner 切换。

### UI-IA-033 — Compatibility Workspace Route

现有 dialog session 通过 `/quick/:sessionId` 进入兼容工作台。必须执行当前用户 ownership check、继续调用 canonical dialog facade，且不得将 `sessionId` 伪装为 `activityId`。

Retirement condition：canonical activity launch/link 覆盖受支持 quick-learning use case，且兼容历史完成迁移。

## 5. Shell 合同

### UI-IA-040 — Standard Shell

桌面 Standard Shell 使用：

```text
Global Product Navigation | Primary Content | Optional Context Inspector
```

- Global Product Navigation：只承载 Today/Learning/Library；
- App Utility：Settings/Recovery/Search 与 Product Navigation 视觉分组；
- Primary Content：页面主任务；
- Context Inspector：推荐原因、证据来源、状态解释、引用等上下文；
- Inspector MAY collapse；隐藏不得丢失完成主任务所需的唯一信息。

### UI-IA-041 — Workspace Shell

导师工作台使用：

```text
Activity / History Rail | Conversation & Task Canvas | Learning Context Inspector
```

中央画布是唯一主交互区域；两侧只提供 Navigation / Disclosure / Status。当前目标、帮助上限与待独立验证状态必须可见，但不得允许用户直接改写 canonical policy state。

### UI-IA-042 — Focus Shell

沉浸学习模式 MUST：

- 一次只呈现一个 activity/task；
- 保留退出和必要帮助；
- 复用同一消息、Attempt、TeachingAction 与 actual assistance 记录；
- 不以视觉隐藏绕过 citation、security、assessment integrity 或 exposure guard。

### UI-IA-043 — No Auth Shell

Askora 无登录/注册 shell。首次引导（Welcome/Onboarding）与错误恢复中心承载本地初始化与恢复说明；不提供登录、注册、账号设置或自动登录页面。

## 6. Today Hierarchy

### UI-IA-050 — Single Primary Task

当 canonical current/next LearningActivity 可执行时，Today MUST 只有一个最高层级的 learning task 和对应 Primary Action。

Compatibility Quick Start、历史会话、完整 Plan、完整 Evidence 不得与该主任务并列为同等视觉模块。

### UI-IA-051 — Secondary Context

Today MAY 展示：

- 当前 Goal 摘要；
- 1～3 个 upcoming planned activities；
- ReviewDue candidates；
- validation obligation / evidence sufficiency 摘要；
- 推荐原因。

完整详情通过 Learning facets 或 Disclosure 进入。

## 7. Responsive Contract

### UI-IA-060 — Desktop-first Breakpoints

实现至少验证：

- 1440×900：完整 shell；
- 1024×768：Inspector 可收起，主任务不压缩到不可读；
- 768×1024：Global Navigation 进入 drawer/compact rail；
- 360×800：单列布局，无页面横向滚动。

具体 CSS breakpoint MAY 调整，但行为不可改变。

### UI-IA-061 — Narrow-screen Priority

窄屏优先级：

```text
Primary Task
→ Current State / Error
→ Required Action
→ Context / Evidence
→ Local Navigation
→ Global Navigation / Utility
```

Context Inspector 在窄屏 MUST 变为可访问 sheet/section，不得永久消失。Focus 模式帮助入口不得因为窄屏被移除。

### UI-IA-062 — No Nested Critical Scroll

主要操作区域 SHOULD 避免同时出现页面滚动、消息滚动和 Inspector 滚动三层关键滚动。任何必须内部滚动的区域都必须有明确边界与键盘可达性。

## 8. Navigation and State Preservation

### UI-IA-070

页面/Facet 切换 MAY 保留 presentation-only 状态，例如筛选、展开节点、Inspector 可见性。它 MUST NOT 静默丢弃未提交草稿、未确认答案或正在 streaming 的 run。

### UI-IA-071

离开有未提交内容或正在执行的 activity 时，UI MUST 给出明确状态：已保存、仍在执行、可恢复或需要确认。不得仅依赖浏览器内存假装 durable recovery。

### UI-IA-072

返回历史消息、活动或计划版本时，UI MUST 清晰区分只读历史与当前 active state，避免旧 DecisionTrace、旧 plan 或旧 evidence 被误认为当前状态。

## 9. Settings / Utility Placement

### UI-IA-080

Settings MUST NOT 作为第四个或更多 Product Domain 与 Today/Learning/Library 等权。

Web-first 当前实现可以在 Sidebar footer / utility group 提供 Settings Navigation，但必须与 Product Domain group 分离。

### UI-IA-081

Search/Command 与 Recovery indicator 属于全局 utility。只有存在对应 user job / issue 时才出现，不得为了“功能完整”建立常驻 product card。

## 10. Acceptance Criteria

- `UI-IA-AC-001`：L0 Product Domain 只有 Today/Learning/Library；
- `UI-IA-AC-002`：Goal/Path/Progress/History 为 Learning L1 facets；
- `UI-IA-AC-003`：Settings/Recovery 与 Product Domain Navigation 明确分组；
- `UI-IA-AC-004`：对话不作为 L0；导师工作台与 Focus 复用同一 activity identity；
- `UI-IA-AC-005`：旧 `/goals` `/path` `/evidence` `/history` 等有无副作用兼容跳转；
- `UI-IA-AC-006`：Today 在 canonical activity 可用时只有一个 Primary Task；
- `UI-IA-AC-007`：1440、1024、768、360 宽度下主任务可完成且无页面横向滚动；
- `UI-IA-AC-008`：Inspector 收起/窄屏重排不会隐藏完成任务所需唯一信息；
- `UI-IA-AC-009`：兼容 quick flow 与 goal-driven canonical activity 有明确标识和 retirement condition；
- `UI-IA-AC-010`：历史状态与当前 active state 不会在视觉或交互上混淆；
- `UI-IA-AC-011`：route/facet navigation 不产生业务副作用。

## 11. Forbidden Implementations

禁止：

- 把 canonical domain object 数量直接映射为 L0 navigation 数量；
- 恢复 Goals/Path/Evidence/History 七项平级 Sidebar；
- 把新 Sidebar 当作完成 Today redesign；
- `/` 直接进入 subject picker/chat-first 主链；
- Focus 模式另写一套消息或评估逻辑；
- Inspector 内直接修改 mastery、TeachingAction 或 next_due_at；
- 为适应小屏把引用、帮助状态、错误或独立验证义务完全隐藏；
- 用前端 route/session state 充当 LearningActivity、LearningPlan 或 ReviewSchedule truth；
- 把 Settings 作为无法分类功能的默认收纳区。

## 12. UXA Supersession Matrix (UI-IA)

本节是 `ADR-0018` / `UX-Architecture-Canonical-Design-Delta.md` 与旧 UI 合同之间的条款处置对照。`KEEP` 表示继续生效；`AMEND` 表示在保留语义下修订；`SUPERSEDE` 表示被新条款取代，旧条款不得再被机械执行；`HISTORICAL` 表示仅存档，不再作为实现合同。

| Clause | Old disposition | New authority | Disposition |
|---|---|---:|---|
| `IES-CD-008`（Goal/Path/Progress/History 为 Learning L1 facets） | Learning 常驻管理 facet | `UXA-IA-005` 去管理化 | **SUPERSEDE**（默认暴露；domain truth 保留） |
| `UI-IA-020..022`（Learning L1 facets 目标/路径/进展/历史） | 常驻 facets 导航 | `UXA-IA-005`、`UXA-IA-030`（contextual task-flow） | **SUPERSEDE**（默认常驻暴露） |
| `UI-IA-030`（canonical routes 表） | `/learning/goals|plan|progress|history` 为常驻页面 | `UXA-IA-030`（route/deep-link migration matrix） | **AMEND**（路由保留迁移，语义改 contextual） |
| `UI-IA-041`（Workspace Shell：Activity/History Rail | Conversation & Task Canvas | Learning Context Inspector） | 旧三栏布局 Inspector 语义 | `ADR-0018` §1、`UXA-IA-001..004`（Where/Learn/Reference + Drawer） | **SUPERSEDE**（布局） |
| `UI-SCREEN-020..062`（Learning 各 facet 页面契约） | 常驻管理页面 | `UXA-SCREEN-*`（screen-contracts 新条款） | **SUPERSEDE**（作为常驻页面） |
| `UI-SCREEN-070`（Tutor Workspace 核心构成） | 兼容导师工作台 | `UXA-SCREEN-*`（Learning Canvas / Drawer） | **AMEND**（并入 central Learning Canvas） |
| `UI-SCREEN-091`（OCR 高级能力 contextual reveal） | Library 可 contextually 暴露 OCR | `UXA-IA-006`、`UXA-SCREEN-190..195` | **SUPERSEDE**（v1 UI 不暴露 OCR） |
| `UI-03`（UI-03 Interactive Element System Refactor Vertical Slice） | 交互元素重构 | `UI-IES-*` 保留 + `UXA-*` 增补 | **KEEP**（IES 语义保留；UXA 增补） |
| `EXEC-043`（UI-03A Shell/Routes/Learning Domain） | 已归档实现合同 | 新 UI-04 Vertical Slice / EXEC | **SUPERSEDE**（作为新实现合同） |
| `EXEC-045`（UI-03C Library Progressive Disclosure） | active 实现合同 | 新 UI-04 Vertical Slice / EXEC | **SUPERSEDE**（Library no-OCR 条款优先） |

处置规则：`SUPERSEDE` 的条款不再作为机械实现依据；对应实现行为以新 `UXA-*` 条款为准。`AMEND` 保留原语义目的，仅按本 Matrix 修订。`KEEP` 语义不变。

## 13. P1-06 Welcome Entry

### UI-IA-090

`/welcome` 是 protected supporting route，不新增 L0 navigation。只有 intended `/` 或 `/today` 在服务端 `should_enter_welcome=true` 时可 replace；`/library`、`/learn/:activityId` 及其他 explicit deep link MUST 保留。

### UI-IA-091

Settings 固定提供“重新打开首次引导”。Dismiss 后返回 `/today`；query failure 保留 intended route 并提供非阻断恢复提示，不得造成 redirect loop。
