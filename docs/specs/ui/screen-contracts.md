# Askora UI Screen and Interaction Specification

> Spec ID：`UI-SCREEN-*`
> 状态：`FROZEN`
> 依赖：`UI-IA-*`、`API-*`、`ERROR-*`、`RENDER-*`

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

### UI-SCREEN-005 — Recovery Card Anatomy

每张 recovery issue card MUST 明确呈现：发生了什么、数据是否安全、现在能做什么、重试/重复
副作用语义。UI MUST 使用服务端 `RecoveryActionV1`；可以格式化 label，但不得自行发明 enabled
command。技术详情默认折叠，且只显示 stable code、correlation 与 safe resource ref。

Command 必须有 accessible pending/succeeded/failed live region，提交期间禁用重复点击，完成后
恢复 focus 并 re-query。`waiting` 显示服务端时间且不伪造进度。空态显示最近检查时间，但不得
声称系统绝对安全。

### UI-SCREEN-006 — Bootstrap Recovery Shell

Electron backend status 为 `failed` 时 MUST 显示不依赖业务 API 的恢复壳，包含数据安全状态、
stable diagnostic code、single-flight retry 和复制脱敏诊断。不得显示 raw stderr、traceback、
绝对路径或环境变量值。

## 2. 今天 / 学习驾驶舱

### UI-SCREEN-010 — Purpose

`/today` 回答三个问题：

1. 今天最值得完成的活动是什么；
2. 为什么现在安排它；
3. 完成后还有什么已计划活动或复习候选。

### UI-SCREEN-011 — Required Regions

READY 状态至少呈现：

- 当前 LearningGoal / Objective（若存在）；
- 当前或 next available LearningActivity；
- 活动类型、预计时间和 reason codes 的可读映射；
- 已纳入 LearningPlan 的后续活动；
- ReviewDue candidates，明确区分“建议复习”与“已纳入计划”；
- 与当前活动相关的 evidence sufficiency / validation obligation 摘要；
- “继续学习”主动作。

### UI-SCREEN-012 — Recommendation Explanation

“为什么现在学这个”只能来自可追踪的 planner/review/evidence reason/source refs。UI MAY 把 reason code 映射为简洁文案，MUST NOT 让 LLM 或前端自行编造个性化原因。

### UI-SCREEN-013 — No Goal State

当前没有 confirmed/active LearningGoal 时：

- 显示无目标空态；
- MAY 提供“快速学习（兼容入口）”；
- MUST NOT 伪造计划、目标完成率或今天任务；
- 创建/确认目标控件在本 Spec Set 的执行范围内 MUST 不出现，除非后续 command Spec 已冻结。

### UI-SCREEN-014 — Review Semantics

`next_due_at` 或 ReviewDue 只能标记为“复习建议/到期候选”。只有 SYS06 已创建 `DELAYED_REVIEW` activity 时，UI 才能把它显示为“今日计划中的复习”。

### UI-SCREEN-015 — Activity Launch Gate

“继续学习”只有在 Query 返回可恢复的 canonical activity/session link 时才可进入导师工作台。若 activity 尚需未冻结的 start command，UI 必须显示“活动已规划，暂不可启动”及原因，不得用 legacy session 冒充该 activity。兼容快速学习必须作为独立、明确标记的入口。

## 3. 学习目标

### UI-SCREEN-020 — Read-only Scope

`/goals` 在本 Spec Set 范围内只读展示已有 LearningGoal：title、target capabilities、success criteria、deadline/time budget、status 与 version。

### UI-SCREEN-021 — Version Awareness

Goal detail MUST 显示当前 version；查看 superseded version 时必须显示历史状态。UI 不得直接 PATCH Goal 字段。

### UI-SCREEN-022 — Unsupported Commands

“新建目标”“确认目标”“暂停/恢复目标”属于未来 command flow。本 Spec Set MAY 预留信息架构位置，但实施时不得提供无后端合同的假按钮。

## 4. 学习路径

### UI-SCREEN-030 — Plan Read Model

`/path` 至少展示：

- active LearningPlan version；
- objective/activity 顺序；
- current/available/completed/skipped/superseded 状态；
- activity type、estimated duration 与 reason codes；
- plan 输入版本摘要：LearnerState、knowledge graph、ReviewSchedule；
- stale/assumption 状态。

### UI-SCREEN-031 — Plan vs Review

计划页 MUST 区分：

- SYS06 决定的活动顺序；
- SYS07 提供的复习候选与 recommended next_due_at。

不得把 ReviewSchedule timeline 直接渲染为已确定的 LearningPlan。

### UI-SCREEN-032 — No Client Replanning

拖拽、前端排序或编辑预计时间 MUST NOT 在本 Spec Set 中修改 canonical plan。若未来支持用户偏好/锁定活动，必须先定义 command、冲突、version 与 idempotency 合同。

## 5. 导师工作台

### UI-SCREEN-040 — Core Composition

`/learn/:activityId` 必须统一呈现：

- 当前 activity/objective；
- 对话和任务内容；
- `RenderPayloadV1` 富文本、公式、typed cards 与 citations；
- 当前资料与可追踪引用；
- 当前允许/实际帮助摘要；
- validation obligation；
- streaming、完成、失败与可恢复状态。

### UI-SCREEN-041 — Action Semantics

用户可表达“引导我、直接讲解、给例子、只给一点提示、让我独立试、测试我、挑战我、总结”等偏好。这些输入 MUST 进入现有请求/feedback/constraint flow，由 SYS05/SYS08 按合同处理；UI 文案不得暗示按钮可以直接改写 TeachingAction。

### UI-SCREEN-042 — Assistance Disclosure

UI SHOULD 以用户可理解语言显示：

```text
当前模式：独立 / 有帮助 / 已暴露答案
允许提示：方向 / 概念 / 子目标 / 部分步骤 / 最终提示
是否待独立验证
```

显示内容必须来自 actual/canonical query。前端不得根据消息长度、card variant 或用户点击次数自行推断 assistance state。

### UI-SCREEN-043 — Rich Response

Assistant message MUST 复用 `RichMessage` typed allowlist。未知/无效 payload 回退 `message.content`；不得新增 raw HTML、MDX、远程图片、模型指定组件或 executable card。

### UI-SCREEN-044 — Citations

资料型回答的引用 MUST 可追踪 SourceSpan。引用侧栏 MAY 提供 label、文档名、章节/页码等已验证元数据；不得只显示内部 UUID 作为唯一用户信息，也不得把无 source ref 的生成内容伪装为资料引用。

### UI-SCREEN-045 — Streaming

Streaming UI 必须区分：

```text
run started
content delta
final payload accepted
run completed
run failed / violation
```

半截 structured payload 不得渲染。断线/重连不得重复 assistant message、Attempt 或 LearningEvent。

### UI-SCREEN-046 — Draft Notes

本轮 UI 改造不新增持久化学习笔记状态。若界面保留“草稿”区域，它必须是明确的本地临时输入并在离开前处理未保存状态，MUST NOT 被描述为已保存笔记或 canonical evidence。

### UI-SCREEN-047 — Compatibility Tutor Workspace

UI-01 的可执行工作台使用 `/quick/:sessionId` 读取当前用户现有 dialog session/message，并复用现有 normal/SSE/history canonical facade。页面必须显示“兼容快速学习”来源标签，不得展示虚构 objective、LearningPlan、TeachingAction envelope 或 validation obligation；缺少 canonical assistance data 时显示“当前记录不可用”，不得从 legacy `hint_level/current_strategy` 推断。

## 6. 沉浸学习

### UI-SCREEN-050 — Same Activity

`/focus/:activityId` 必须携带与导师工作台相同的 activity/session/run identity。进入或退出 Focus 模式不得重新生成 TeachingAction 或清空 assistance history。

### UI-SCREEN-051 — Single Task

主视图一次只显示一个 task、必要资料、输入区域和提交动作。History、全局 evidence 与详细 trace MAY 暂时隐藏，但当前帮助状态、必要引用、安全错误和 validation obligation 必须可访问。

### UI-SCREEN-052 — Progressive Help

帮助按钮只发出用户偏好/请求。按钮的可用性和最大提示级别必须来自 canonical action/context；被 hard rule 禁止的帮助不得以 CSS 隐藏后仍可触发。

### UI-SCREEN-053 — Save / Pause

“保存并暂停”只有在后端存在 durable resume 语义时才能出现。否则必须使用“退出专注模式”等不宣称持久化的文案。

## 7. 资料库与知识地图

### UI-SCREEN-060 — Library Modes

`/library` 提供：

- 文档列表；
- 文档处理状态；
- 上传入口（复用现有安全合同）；
- KnowledgeUnit / relation 结构视图；
- 选中节点的来源与学习证据摘要。

### UI-SCREEN-061 — Document vs Knowledge

Document、SourceChunk、KnowledgeUnit MUST 在视觉和文案上区分。文档处理完成不等于知识节点已发布；chunk 不得显示为 canonical KnowledgeUnit。

### UI-SCREEN-062 — Map Edges

关系图只能渲染后端返回的已发布或明确标记 candidate 的 relation。章节顺序不得在前端转换为 hard prerequisite；低置信关系必须显示 confidence/status。

### UI-SCREEN-063 — Processing State

文档状态至少区分 pending、processing、completed、failed、rejected/quarantined。失败必须显示可恢复动作和结构化错误，不得把处理失败记为学习失败。

### UI-SCREEN-064 — Map Empty State

若文档存在但 canonical knowledge query 为空，必须说明“资料已导入，但尚无可展示的已发布知识节点”，不得展示由文件名或章节标题临时生成的假图谱。

## 8. 学习证据

### UI-SCREEN-070 — Canonical First

`/evidence` 默认只使用 SYS03 canonical projection。每个 KnowledgeUnit 至少可展示：

- competence estimate（若存在，必须标记为估计）；
- confidence；
- independent success count；
- delayed recall evidence count；
- transfer evidence count；
- evidence count / effective evidence weight；
- active misconception hypotheses 的存在与可用解释；
- algorithm/version 或可查看的来源说明。

### UI-SCREEN-071 — No Arbitrary Mastery Label

UI MUST NOT 使用单一 probability threshold 生成“已掌握/未掌握”、红黄绿状态或技能数。只有后端返回由 versioned canonical rule 生成的 product label 时才可显示该 label 与规则版本。

### UI-SCREEN-072 — Uncertainty

`competence_probability=null`、confidence 缺失或证据不足时应显示“不足/未知”，不得显示 0%、空进度条或默认低能力。

### UI-SCREEN-073 — Legacy Compatibility

`total_sessions`、`total_learning_minutes`、`streak_days`、`skills_mastered`、`mastery_summary`、`metacognition` 等 `legacy_compatibility` 字段默认不进入主证据页面。若临时保留，必须置于“兼容统计”折叠区并显示来源标签与 retirement condition。

### UI-SCREEN-074 — Dispute

用户对学习状态提出异议时，UI MAY 展示“申请复测/反馈判断”的入口；在对应 command contract 未冻结前不得提供直接编辑概率、证据数或 mastery label 的控件。

## 9. 历史记录

### UI-SCREEN-080

`/history` 默认聚合现有 session/message history，并在可用时关联 activity、TeachingEpisode、结果与引用。列表必须区分 active、ended、failed/degraded 与只读历史。

### UI-SCREEN-081

历史消息 MUST 使用持久化的同一 `RenderPayloadV1`；不得为旧消息调用在线 LLM 回填富文本。

### UI-SCREEN-082

历史 DecisionTrace、旧 plan/action/evidence MAY 提供审计详情，但默认用户界面使用人类可理解摘要。任何摘要都必须保留原始 version/ref 可追踪性。

## 10. 设置、账号与认证

### UI-SCREEN-090 — Settings Consolidation

`/settings` 合并原账号管理与运行状态：账号信息、私人模式、模型是否配置、数据控制入口、退出登录。不得返回或展示密钥、完整 Prompt、内部路径或敏感连接信息。

### UI-SCREEN-091 — Authentication

正式模式保留手机号登录/注册。开发自动登录只有在后端和前端都由本地开发配置显式启用时才可发生；失败必须回到登录页并给出诊断，不得静默创建假用户。

### UI-SCREEN-092 — Login Precondition

当前 `Login.jsx` 使用未导入的 `User` icon，导致运行时白屏。正式 UI 实施前必须先修复并增加至少一个登录页 render test；该修复属于 UI-01 precondition，不是视觉重设计完成证据。

### UI-SCREEN-093 — Data Deletion Copy

“清除本地登录信息”“删除服务端学习数据”“删除本地文档”必须使用不同动作和文案。不存在服务端删除合同的控件不得声称删除了学习数据。

### UI-SCREEN-094 — Recovery Station

`/settings/recovery` 按 blocking、waiting、warning 排序 owner-scoped issues；rate limit 显示 next
eligible time，Key invalid 导航模型设置，quarantine 仅在新策略存在时允许复检，OCR 候选只
进入人工复核。File missing 不承诺自动找回。Resolved 不得写成学习成功或资料正确。

## 11. Accessibility

### UI-SCREEN-100

所有页面必须支持键盘导航、可见 focus、语义 heading、label、live status/error announcement 与 reduced motion。Icon-only control 必须有 accessible name。

### UI-SCREEN-101

颜色不得作为 evidence、error、status 或 mastery 的唯一编码。所有状态必须有文本、图形或图标的冗余表达。

### UI-SCREEN-102

消息、公式、表格、知识关系与长引用在 200% zoom 和 360px 宽度下不得截断关键文字。公式 MAY 局部横向滚动，但页面整体不得横向滚动。

## 12. Acceptance Criteria

- `UI-SCREEN-AC-001`：所有数据页覆盖 LOADING/EMPTY/READY/PARTIAL/STALE/ERROR/UNAUTHORIZED。
- `UI-SCREEN-AC-002`：今天页区分已计划活动与 ReviewDue candidate。
- `UI-SCREEN-AC-010`：无 canonical activity/session link 时不显示可执行的“继续学习”，兼容 quick start 不冒充计划活动。
- `UI-SCREEN-AC-003`：导师工作台与 Focus 模式显示 canonical/actual assistance，不做前端推断。
- `UI-SCREEN-AC-004`：RichMessage 安全回退、历史持久化与 streaming final 语义保持不变。
- `UI-SCREEN-AC-005`：知识地图不把 document/chunk/chapter order 伪装成 KnowledgeUnit/hard prerequisite。
- `UI-SCREEN-AC-006`：学习证据页不以单一 probability threshold 生成 mastery label。
- `UI-SCREEN-AC-007`：legacy profile 指标默认不进入主证据视图。
- `UI-SCREEN-AC-008`：正式登录、开发自动登录和本地退出语义清晰分离。
- `UI-SCREEN-AC-009`：360px 与 200% zoom 下关键任务、错误、引用和帮助状态可访问。
- `UI-SCREEN-AC-011`：兼容工作台保留 RichMessage、ownership 与 canonical dialog path，同时不伪造 activity/policy/evidence 数据。
- `UI-SCREEN-AC-012`：Recovery Center 和 bootstrap shell 满足 UI-SCREEN-005/006/094。

## 13. Forbidden Implementations

禁止：

- skeleton 永久显示或 catch 后返回空数组伪装 EMPTY；
- UI 依据消息内容推断 mastery、assistance 或 error type；
- 把模型/工具/检索失败显示为“你答错了”；
- 用红黄绿进度条包装未经 versioned rule 授权的 mastery threshold；
- 未实现 persistence 却显示“已保存”；
- 隐藏 unknown/stale/low-confidence，只保留看起来完整的数字；
- 为知识地图或今日推荐编造后端不存在的理由与关系。
