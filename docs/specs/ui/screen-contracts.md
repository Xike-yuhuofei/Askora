# Askora UI Screen and Interaction Specification

> Spec ID：`UI-SCREEN-*`  
> 状态：`FROZEN`  
> Governing：`ADR-0014`、`UI-IA-*`、`UI-IES-*`、`API-*`、`ERROR-*`、`RENDER-*`

## 1. 通用页面状态

### UI-SCREEN-001 — Required State Vocabulary

所有依赖后端数据的页面 MUST 能区分：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

`PARTIAL` 表示部分 owner/query 可用；`STALE` 表示仍可读取 last valid data 但来源已过期。两者不得显示为完整 READY。

### UI-SCREEN-002 — State Is Local to Data Region

局部数据失败 SHOULD 局部降级。一个 Inspector 请求失败不得让整个导师工作台白屏；关键 activity/session 请求失败则必须阻断提交并提供恢复操作。

### UI-SCREEN-003 — Structured Error

UI MUST 优先使用稳定 `error.code`、`category`、`retryable` 与 `correlation_id` 决定呈现和恢复动作。不得依赖自由文本匹配作为主要错误分支。

### UI-SCREEN-004 — Honest Empty State

Empty state 必须说明“目前没有什么”和“用户下一步能做什么”。不得用假数据、模拟掌握度或默认 activity 填充空白。

### UI-SCREEN-005 — Recovery Issue Anatomy

Recovery issue MUST 明确呈现：发生了什么、数据是否安全、现在能做什么、重试/重复副作用语义。UI MUST 使用服务端 `RecoveryActionV1`；可以格式化 label，但不得自行发明 enabled command。

技术详情默认 Disclosure，且只显示 stable code、correlation 与 safe resource ref。Command 必须有 accessible pending/succeeded/failed live region，提交期间禁用重复点击，完成后恢复 focus 并 re-query。

### UI-SCREEN-006 — Bootstrap Recovery Shell

本地 host/backend bootstrap status 为 `failed` 时 MUST 显示不依赖业务 API 的恢复壳，包含数据安全状态、stable diagnostic code、single-flight retry 和复制脱敏诊断。不得显示 raw stderr、traceback、绝对路径或环境变量值。

## 2. 今天 / Daily Learning Orchestrator

### UI-SCREEN-010 — Purpose

`/today` 首先回答：

1. 现在最值得完成的 LearningActivity 是什么；
2. 为什么现在安排它；
3. 完成后还有什么已计划活动或复习候选。

### UI-SCREEN-011 — Single Primary Task

当 canonical current/next LearningActivity 可执行时，首屏 MUST 只有一个最高层级学习任务和一个对应 Primary Action：

```text
继续学习 | 开始学习
```

不得让 Quick Start、完整 Path、完整 Evidence、历史会话或其他 Dashboard widget 与其形成同等 Primary hierarchy。

### UI-SCREEN-012 — Required Information

READY 状态主任务区域至少呈现：

- 当前 LearningGoal / Objective 的简短上下文（若存在）；
- current/next LearningActivity；
- activity type；
- estimated duration；
- reason codes 的用户可读映射；
- validation obligation / evidence sufficiency（适用时）；
- canonical launch state。

Secondary region MAY 呈现：

- 后续 1～3 项 planned activities；
- ReviewDue candidates；
- 当前 Goal 简要状态。

完整详情进入 `/learning/*` facets。

### UI-SCREEN-013 — Recommendation Explanation

“为什么现在学这个”只能来自可追踪的 planner/review/evidence reason/source refs。UI MAY 把 reason code 映射为简洁文案，MUST NOT 让 LLM 或前端自行编造个性化原因。

### UI-SCREEN-014 — No Goal / No Plan State

当前没有 confirmed/active LearningGoal 或没有可执行 canonical activity 时：

- 必须诚实显示缺失状态；
- P1-01 Goal command 已存在时 MAY 提供“创建学习目标”或进入现有 Goal flow；
- MAY 提供“快速学习（兼容入口）”；
- MUST NOT 伪造计划、目标完成率或今日任务。

### UI-SCREEN-015 — Compatibility Quick Start Demotion

当 canonical activity 可启动时，Quick Start MUST 进入 secondary/overflow，不得作为并列主区块。

只有无 canonical goal/plan/activity 时，Quick Start MAY 作为 empty-state fallback，但必须继续标记“兼容快速学习 / 非计划活动”。

### UI-SCREEN-016 — Review Semantics

`next_due_at` 或 ReviewDue 只能标记为“复习建议/到期候选”。只有 SYS06 已创建 `DELAYED_REVIEW` activity 时，UI 才能把它显示为“今日计划中的复习”。

### UI-SCREEN-017 — Activity Launch Gate

“开始/继续学习”只有在 canonical activity lifecycle/query 返回允许的 launch state 时可执行。不得用 legacy session 冒充 activity。Activity start/resume MUST 服从现有 SYS06 lifecycle command/idempotency/version contract。

## 3. 学习 / Learning Domain

### UI-SCREEN-020 — Learning Landing

`/learning` 是长期学习空间。它 MUST 提供对以下 L1 facets 的清晰导航：

```text
目标 / 路径 / 进展 / 历史
```

Landing MAY 直接打开一个默认 facet；不得通过四张等权 Dashboard Card 重新制造旧 IA。

### UI-SCREEN-021 — Local Facet Navigation

Facet switch 是 Navigation，不是业务 Action；切换不得改变 focused goal、plan、evidence 或 history state。

在窄屏可转换为 segmented control / menu / navigation stack，但 semantic role 不变。

## 4. 学习目标

### UI-SCREEN-030 — Routes and Scope

Canonical routes：

```text
/learning/goals
/learning/goals/new
/learning/goals/drafts/:draftId
/learning/goals/:goalId
/learning/goals/:goalId/edit
```

旧 `/goals/**` route 只做无副作用 redirect。

### UI-SCREEN-031 — Goal Collection

目标列表展示 owner 发布的 LearningGoal：title、target capabilities、success criteria、deadline/time budget、status 与 version。

普通 goal collection SHOULD 使用 Interactive Row/List，不得默认每个 Goal 一个大型 Card。

### UI-SCREEN-032 — Goal Commands

Goal 创建、编辑、确认、pause/resume/archive/copy/replan 等能力只有在对应 `GOAL-*` / P1-01A/P1-01B command contract 已存在时可显示。

UI 不得直接 PATCH canonical fields 或绕过 preview/version/idempotency/apply-boundary contract。

### UI-SCREEN-033 — Version Awareness

Goal detail MUST 显示当前 version；查看 superseded version 时必须显示历史状态。用户可读目标信息优先，内部 target id 不作为主要文案。

### UI-SCREEN-034 — Focused Goal Selection

存在多个可查看/当前目标时，选择 focused goal 使用 Selection pattern。Selection 是否立即产生 owner command 必须服从 Goal contract；不得通过本地 route state 假装 focused state 已持久化。

## 5. 学习路径

### UI-SCREEN-040 — Plan Read Model

`/learning/plan` 至少展示：

- active LearningPlan version；
- objective/activity 顺序；
- current/available/completed/skipped/superseded 状态；
- activity type、estimated duration 与 reason codes；
- plan 输入版本摘要：LearnerState、knowledge graph、ReviewSchedule；
- stale/assumption 状态。

### UI-SCREEN-041 — Plan Is Projection

LearningPath 是 LearningPlan projection，不是用户可自由编辑的路线画布。

计划页 MUST 区分：

- SYS06 决定的 activity order；
- SYS07 提供的 ReviewDue / recommended next_due_at。

不得把 ReviewSchedule timeline 直接渲染为已确定 LearningPlan。

### UI-SCREEN-042 — No Client Replanning

拖拽、前端排序或编辑预计时间 MUST NOT 修改 canonical plan。只有存在明确 owner command、version/conflict/idempotency contract 时才能出现对应 Control/Action。

## 6. 学习进展

### UI-SCREEN-050 — Canonical First

`/learning/progress` 默认只使用 SYS03 canonical projection。`进展` 是用户 vocabulary，不改变 Evidence/LearnerState ownership。

每个 KnowledgeUnit 至少可展示（存在时）：

- competence estimate，并标记“估计”；
- confidence；
- independent success count；
- delayed recall evidence count；
- transfer evidence count；
- evidence count / effective evidence weight；
- active misconception hypotheses 的可用解释；
- algorithm/version 或来源说明。

### UI-SCREEN-051 — No Arbitrary Mastery Label

UI MUST NOT 使用单一 probability threshold 自行生成“已掌握/未掌握”、红黄绿状态或技能数。只有后端返回 versioned canonical product label 时才可显示该 label 与规则版本。

### UI-SCREEN-052 — Uncertainty

`competence_probability=null`、confidence 缺失或证据不足时应显示“不足/未知”，不得显示 0%、空进度条或默认低能力。

### UI-SCREEN-053 — Legacy Compatibility

`total_sessions`、`total_learning_minutes`、`streak_days`、`skills_mastered`、`mastery_summary`、`metacognition` 等 legacy fields 默认不进入 Progress 主视图。若临时保留，必须置于“兼容统计”Disclosure 并显示来源与 retirement condition。

### UI-SCREEN-054 — Dispute

用户对学习状态提出异议时，只有在对应 command contract 冻结后才可提供“申请复测/反馈判断”Action。不得提供直接编辑 probability、evidence count 或 mastery label 的 Control。

## 7. 学习历史

### UI-SCREEN-060 — History Projection

`/learning/history` 聚合现有 session/message history，并在可用时关联 activity、TeachingEpisode、结果与引用。列表必须区分 active、ended、failed/degraded 与只读历史。

### UI-SCREEN-061 — Durable Rendering

历史消息 MUST 使用持久化的同一 `RenderPayloadV1`；不得为旧消息调用在线 LLM 回填富文本。

### UI-SCREEN-062 — Historical State

历史 DecisionTrace、旧 plan/action/evidence MAY 提供审计详情，但默认使用人类可理解摘要，并保留原始 version/ref 可追踪性。历史状态不得视觉上冒充 current active state。

## 8. 导师工作台

### UI-SCREEN-070 — Core Composition

`/learn/:activityId` 必须统一呈现：

- 当前 activity/objective；
- 对话和任务内容；
- `RenderPayloadV1` 富文本、公式、typed cards 与 citations；
- 当前资料与可追踪引用；
- 当前允许/实际帮助摘要；
- validation obligation；
- streaming、完成、失败与可恢复状态。

### UI-SCREEN-071 — Chat Is Interaction Mode

Conversation/Tutor 是 LearningActivity 的 interaction mode，不是独立 Product Domain。

用户可表达“引导我、直接讲解、给例子、只给一点提示、让我独立试、测试我、挑战我、总结”等请求；它们 MUST 进入现有 request/feedback/constraint flow，由 SYS05/SYS08 按合同处理。UI 文案不得暗示按钮可直接改写 TeachingAction。

### UI-SCREEN-072 — Assistance Disclosure

UI SHOULD 以用户可理解语言显示：

```text
当前模式：独立 / 有帮助 / 已暴露答案
允许提示：方向 / 概念 / 子目标 / 部分步骤 / 最终提示
是否待独立验证
```

显示必须来自 canonical/actual query。前端不得根据消息长度、card variant 或点击次数自行推断 assistance state。

### UI-SCREEN-073 — Rich Response and Citations

Assistant message MUST 复用 `RichMessage` typed allowlist。未知/无效 payload 回退 `message.content`；不得新增 raw HTML、MDX、远程图片、模型指定组件或 executable card。

资料型回答引用 MUST 可追踪 SourceSpan。用户主视觉显示可读 label/locator；内部 UUID 可放 Disclosure/Inspector，不作为唯一信息。

### UI-SCREEN-074 — Streaming

Streaming UI 必须区分：

```text
run started
content delta
final payload accepted
run completed
run failed / violation
```

半截 structured payload 不得渲染。断线/重连不得重复 assistant message、Attempt 或 LearningEvent。

### UI-SCREEN-075 — Compatibility Tutor Workspace

`/quick/:sessionId` 读取现有 dialog session/message，并复用 canonical facade。页面必须显示“兼容快速学习”来源标签，不得展示虚构 objective、LearningPlan、TeachingAction envelope 或 validation obligation；缺少 canonical assistance data 时显示“当前记录不可用”。

## 9. 沉浸学习

### UI-SCREEN-080 — Same Activity

`/focus/:activityId` 必须携带与导师工作台相同的 activity/session/run identity。进入或退出 Focus 模式不得重新生成 TeachingAction 或清空 assistance history。

### UI-SCREEN-081 — Single Task

主视图一次只显示一个 task、必要资料、输入区域和提交动作。History、全局 progress 与详细 trace MAY 暂时隐藏，但当前帮助状态、必要引用、安全错误和 validation obligation 必须可访问。

### UI-SCREEN-082 — Progressive Help

帮助按钮只发出用户偏好/请求。按钮可用性和最大提示级别必须来自 canonical action/context；被 hard rule 禁止的帮助不得以 CSS 隐藏后仍可触发。

### UI-SCREEN-083 — Save / Pause Copy

“保存并暂停”只有后端存在 durable resume 语义时才能出现。否则使用“退出专注模式”等不宣称持久化的文案。

## 10. 资料库与知识地图

### UI-SCREEN-090 — Primary Library Tasks

`/library` 默认优先支持：

1. 查找资料；
2. 打开资料；
3. 导入资料；
4. 查看 processing state；
5. 查看知识结构/来源。

### UI-SCREEN-091 — Progressive Management

批量标签、集合、归档等批处理动作 MUST 在存在 selection 后才进入 Contextual Toolbar / Inspector / Menu。

以下高级能力 SHOULD 按当前 document/context 出现，不得全部长期占据默认主页面：

- duplicate review；
- OCR review/publish；
- metadata advanced edit；
- reinspection；
- destructive actions。

Touch/keyboard 必须有 hover action 的等价发现路径。

### UI-SCREEN-092 — Document vs Knowledge

Document、SourceChunk、KnowledgeUnit MUST 在视觉和文案上区分。文档处理完成不等于知识节点已发布；chunk 不得显示为 canonical KnowledgeUnit。

### UI-SCREEN-093 — Map Edges

关系图只能渲染后端返回的已发布或明确 candidate relation。章节顺序不得在前端转换为 hard prerequisite；低置信关系必须显示 confidence/status。

### UI-SCREEN-094 — Processing State

文档状态至少区分 pending、processing、completed、failed、rejected/quarantined。失败显示可恢复动作和结构化错误，不得把处理失败记为学习失败。

### UI-SCREEN-095 — Map Empty State

若文档存在但 canonical knowledge query 为空，必须说明“资料已导入，但尚无可展示的已发布知识节点”，不得展示由文件名或章节标题临时生成的假图谱。

## 11. Settings 与本地数据

### UI-SCREEN-100 — Settings Is App Utility

`/settings` 是 App-level Utility destination，不与 Today/Learning/Library 等权。

Settings landing page MUST 优先展示 category navigation，而不是把所有操作铺成大型 control grid。

目标 categories：

```text
通用
AI 与模型
学习偏好
外观
数据与隐私
错误恢复中心
高级
```

只为已有真实 capability 建立 route；不得创建占位设置页。

### UI-SCREEN-101 — Secondary Task Destinations

以下完整流程不应在 Settings landing page 同屏展开：

- 永久删除数据；
- 数据导出；
- 错误恢复中心；
- 高级模型配置。

它们进入对应二级 destination/task flow。

### UI-SCREEN-102 — Runtime Status Contextualization

正常运行状态 SHOULD 不占据 Settings 主层级。只有 degraded/unavailable/action-required 时才在 landing/global status 中显著出现。

### UI-SCREEN-104 — Data Deletion Copy

“删除学习数据”“删除本地文档”“清除全部本地数据”必须使用不同动作和文案。不存在 owner deletion contract 的控件不得声称已删除相应数据。

### UI-SCREEN-105 — Recovery Station

`/settings/recovery` 按 blocking、waiting、warning 排序 owner-scoped issues；rate limit 显示 next eligible time，Key invalid 导航模型设置，quarantine 仅在新策略存在时允许复检，OCR 候选只进入人工复核。File missing 不承诺自动找回。Resolved 不得写成学习成功或资料正确。

### UI-SCREEN-106 — Data Control and Recovery

数据与隐私/数据恢复相关 destination 必须继续服从 P1-03：protection state、VERIFIED recovery point、位置边界、backup/restore/export/erasure scope、owner impact preview、明确确认、PARTIAL/FAILED truthfulness、Recovery Key secret lifetime 等语义不得弱化。

### UI-SCREEN-107 — Model Settings State

AI 与模型 destination MUST 显示现有 model configuration contract 定义的状态，并展示脱敏 provider、model、source、revision 与最后验证时间。MUST NOT 展示、回填或复制完整 API Key；已保存 credential 只能用“已安全保存”状态表达。

### UI-SCREEN-108 — Configure and Verify

受支持 provider/model allowlist 与 credential flow 继续服从 `MODEL-CONFIG-*`。主动作“验证并应用”必须先说明测试数据/费用边界；提交完成（成功或失败）后清空 credential 字段，不得持久化或回填。

### UI-SCREEN-109 — Data and Cost Disclosure

必须准确区分测试与真实学习数据边界；不得声称 Askora 可读取 provider 余额、精确费用或预算能力，除非对应合同以后正式增加。

### UI-SCREEN-110 — Clear and Recovery

清除模型配置必须二次确认，并准确说明只影响 Askora 管理的配置边界。apply rollback 成功/失败状态不得混淆。

## 12. Accessibility

### UI-SCREEN-120

所有页面必须支持键盘导航、可见 focus、语义 heading、label、live status/error announcement 与 reduced motion。Icon-only control 必须有 accessible name。

### UI-SCREEN-121

颜色不得作为 evidence、error、status 或 mastery 的唯一编码。所有状态必须有文本、图形或图标的冗余表达。

### UI-SCREEN-122

消息、公式、表格、知识关系与长引用在 200% zoom 和 360px 宽度下不得截断关键文字。公式 MAY 局部横向滚动，但页面整体不得横向滚动。

### UI-SCREEN-123 — Contextual Discoverability

只在 hover 出现的 Contextual Action MUST 同时有 keyboard/touch 等价入口，例如 focus-visible action、More Menu 或 Context Menu。

## 13. Acceptance Criteria

- `UI-SCREEN-AC-001`：所有数据页覆盖必要 LOADING/EMPTY/READY/PARTIAL/STALE/ERROR/UNAUTHORIZED；
- `UI-SCREEN-AC-002`：Today 在 canonical activity 可用时只有一个 Primary Task；
- `UI-SCREEN-AC-003`：Quick Start 只作为 fallback/secondary，不冒充计划活动；
- `UI-SCREEN-AC-004`：Learning 下 Goal/Plan/Progress/History 四 facets 均可达且切换无业务副作用；
- `UI-SCREEN-AC-005`：Goal command UI 只调用已冻结 owner command，不直接 PATCH canonical truth；
- `UI-SCREEN-AC-006`：Plan 不允许 client-side canonical replan；
- `UI-SCREEN-AC-007`：Progress 不通过任意 threshold 生成 mastery label；
- `UI-SCREEN-AC-008`：导师工作台与 Focus 显示 canonical/actual assistance，不做前端推断；
- `UI-SCREEN-AC-009`：RichMessage 安全回退、历史持久化与 streaming final 语义保持；
- `UI-SCREEN-AC-010`：Library 批处理动作只在 selection/context 下显著出现；
- `UI-SCREEN-AC-011`：Settings landing 为 category navigation，不同高风险 flow 不在首屏全部展开；
- `UI-SCREEN-AC-012`：Recovery/Data/Model security contracts 不因 IA 重构弱化；
- `UI-SCREEN-AC-013`：360px 与 200% zoom 下关键任务、错误、引用和帮助状态可访问；
- `UI-SCREEN-AC-014`：兼容工作台保留 RichMessage、ownership 与 canonical dialog path，同时不伪造 activity/policy/evidence；
- `UI-SCREEN-AC-015`：Contextual Actions 有 keyboard/touch 等价路径。

## 14. Forbidden Implementations

禁止：

- skeleton 永久显示或 catch 后返回空数组伪装 EMPTY；
- UI 依据消息内容推断 mastery、assistance 或 error type；
- 把模型/工具/检索失败显示为“你答错了”；
- 用红黄绿进度条包装未经 versioned rule 授权的 mastery threshold；
- 未实现 persistence 却显示“已保存”；
- 隐藏 unknown/stale/low-confidence，只保留看起来完整的数字；
- 为知识地图或今日推荐编造后端不存在的理由与关系；
- 未经过 probe/runtime revision verification 就显示“已验证/已应用”；
- 回填、展示、复制或通过 DOM 属性保留已保存完整 API Key；
- 用四个等权 Card 重新包装 Goal/Path/Progress/History；
- 在 Library 无 selection 时长期显示批量管理主面板；
- 在 Settings landing 同屏展开所有 destructive/security flow。

## 15. P1-06 First-use Journey

### UI-SCREEN-130

`/welcome` 只显示 MODEL/MATERIAL/GOAL/FIRST_ACTIVITY 四步和一个主动作；boundary notice 在步骤前展示。Diagnostic/planner 等内部阶段可作为当前动作说明，不得增加用户必须理解的工程步骤。

### UI-SCREEN-131

页面必须覆盖 LOADING/READY/PARTIAL/STALE/ERROR/UNAUTHORIZED，以及 processing/quarantined/provider rate/key/version/activity unsupported。每个 blocked/error 显示 what/data safety/next action，且只呈现服务端 `RecoveryActionV1`。

### UI-SCREEN-132

“稍后再说”只 dismiss；“进入今天”只有 current journey COMPLETE 时可 finish+dismiss；Settings 可 reopen。配置/资料/Goal/activity 事实回退时页面必须撤销旧勾选，不得读取 localStorage 保留完成。

### UI-SCREEN-133

数据/模型说明必须准确引用 P1-02/P1-03 当前边界；不得展示 Key、路径或绝对隐私承诺。360px/200% zoom/keyboard/focus/live status 下主动作和信任信息均可访问。

## 16. P1-01 Goal Management Screens

`/learning/goals/new`、`/learning/goals/drafts/:draftId`、`/learning/goals/:goalId`、`/learning/goals/:goalId/edit` 必须展示资料状态、measurable criteria、target name/source/evidence/reason、definition/state/plan version 和 apply boundary。

旧 `/goals/**` route 仅 redirect。内部 target id 不作为主要文案。错误必须保留用户输入并提供刷新 preview/replan/retry；360/768/1024/1440、200% zoom、键盘与 focus 可操作。
