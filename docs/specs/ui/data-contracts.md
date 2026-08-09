# Askora UI Data and Query Specification

> Spec ID：`UI-DATA-*`
> 状态：`FROZEN`
> 依赖：`DOMAIN-*`、`STATE-*`、`DEP-*`、`API-*`、`SCHEMA-*`

## 1. 原则

### UI-DATA-001 — UI Is Not an Owner

UI、frontend store、API handler 与 UI read-model assembler 均不是新的业务状态 owner。它们只可读取、组合和呈现 owner 已发布的 exact-version state 或明确标记的 compatibility projection。

### UI-DATA-002 — Query Composition Does Not Change Ownership

面向页面的聚合 Query MAY 组合 SYS01、SYS03、SYS05、SYS06、SYS07、SYS08 的只读投影，但每个字段必须保留 `source_system`、version/ref、availability/freshness。聚合 response 不得成为第二 LearningPlan、LearnerState、TeachingAction 或 ReviewSchedule truth。

### UI-DATA-003 — No Frontend Domain Inference

前端 MUST NOT：

- 从 score/session/message 推导 mastery；
- 从 `next_due_at` 推导已进入今日计划；
- 从章节顺序推导 prerequisite；
- 从 RichMessage card 推导 TeachingAction/assistance；
- 从聊天轮数或持续时间推导进度/学习效果；
- 用固定 threshold 生成 canonical product label。

### UI-DATA-004 — Missing and Source Semantics

跨系统 UI 字段 SHOULD 使用：

```yaml
value: any|null
availability: AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE
source_system: SYS01|SYS02|SYS03|SYS04|SYS05|SYS06|SYS07|SYS08|LEGACY_COMPATIBILITY
source_ref: versioned_ref|null
observed_at: datetime|null
```

`MISSING` MUST NOT 转换为 0、空字符串、false 或空进度条。

## 2. 当前接口分类

### UI-DATA-010 — Existing and Reusable

| 能力 | 当前接口 | UI 用途 | 限制 |
|---|---|---|---|
| 会话与消息 | `/api/v1/dialog/**` | 导师工作台、历史记录 | session 中部分字段仍为 legacy compatibility |
| 富文本回答 | `message.render_payload` | Markdown/math/cards/citations | 必须继续保留 `content` fallback |
| 学习画像 | `/api/v1/users/profile` | 学习证据迁移入口 | 仅 `profile.mastery` 为 canonical SYS03；其余多为 legacy |
| 文档 | `/api/v1/documents/**` | 资料库列表、上传、状态 | 当前不等于 canonical KnowledgeUnit map query |
| 本地运行状态 | `/health/config` | 设置 | 只返回 mode/ready 类非敏感事实 |

### UI-DATA-011 — Frozen Additive Query Plan

以下 read-only endpoints 已冻结，并按 Vertical Slice 串行实现：

| Endpoint | Slice | 当前实施状态 |
|---|---|---|
| `GET /api/v1/workspace/today` | UI-01 | REQUIRED |
| `GET /api/v1/workspace/activities/{activity_id}` | future activity-link slice | DEFERRED_BY_ACTIVITY_LINK_CONTRACT |
| `GET /api/v1/workspace/library` | UI-02A | REQUIRED |
| `GET /api/v1/workspace/knowledge-map` | UI-02A | REQUIRED |
| `GET /api/v1/workspace/goals` | UI-02B / EXEC-029 | IMPLEMENTED |
| `GET /api/v1/workspace/path` | UI-02B / EXEC-029 | IMPLEMENTED |
| `GET /api/v1/workspace/evidence` | UI-02B / EXEC-029 | IMPLEMENTED |

这些 endpoint MUST 由 application/query layer 调用 owner query ports；API handler 只做 auth、validation、serialization 与 error mapping。

### UI-DATA-012 — Commands Remain Out of Scope Except Frozen Additive Slices

本基础 Spec Set 不新增：

```text
Create/Confirm/Pause/Resume LearningGoal
Reorder/Edit/Replan LearningPlan
SetNextReviewAt
SetMastery / EditEvidence
SetTeachingAction / SetHintLevel
StartLearningActivity canonical command
```

现有 dialog/document/auth commands 可继续使用。UI-02B1 通过独立冻结 Slice 复用 SPEC-D06 已实现的单资料 Goal/diagnostic/plan/activity/teaching commands，并冻结 learner-visible diagnostic payload；这不授权完整 Goal/Plan 编辑或 durable activity/session link。未来其他 goal/activity command 仍必须单独冻结公共 schema、idempotency、version conflict 与 ownership contract。

UI-02C 通过 ADR-0007、`SYS06 Activity Lifecycle and Completion` 与独立 Vertical Slice 单独
冻结 `StartLearningActivityV1`、`CompleteLearningActivityV1` 和 activity query。该授权仅在
EXEC-030 dependency gate 满足后生效，不扩大 Goal/Plan/mastery 编辑范围。

## 3. Common Response Envelope

### UI-DATA-020

所有新 workspace query 使用 additive v1 envelope：

```yaml
schema_version: "1.0"
generated_at: datetime
data: object|null
source_status:
  - source_system: string
    availability: AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE
    source_ref: versioned_ref|null
    reason_codes: [string]
correlation_id: string
```

未知 major version MUST 明确拒绝或进入安全页面级 fallback；不得猜测字段语义。

### UI-DATA-021 — Partial Success

若一个聚合 Query 的非关键 owner source 失败，response MAY 返回 `data` 的可用部分及 `source_status`。若主实体（例如 requested activity）不存在或无权限，必须返回 stable error，而不是 `200 + empty`。

### UI-DATA-022 — Stable Ordering

Activity、goal、evidence 和 node 列表必须有服务端定义的稳定排序与 tie-break。前端 MAY 做 presentation-only filter/sort，但不得把本地顺序保存为 canonical plan/map truth。

## 4. TodayWorkspaceViewV1

### UI-DATA-030 — Contract

```yaml
today_workspace:
  local_date: YYYY-MM-DD
  timezone: string
  active_goal:
    goal_ref: versioned_ref
    title: string
    status: string
    target_capabilities: [string]
  current_activity:
    activity_ref: versioned_ref
    objective_ref: versioned_ref
    type: string
    title: string
    estimated_duration_minutes: integer|null
    reason_codes: [string]
    status: string
    launch_state: ACTIVE|RESUMABLE|REQUIRES_START_COMMAND|UNAVAILABLE
  planned_activities:
    - activity_ref: versioned_ref
      objective_ref: versioned_ref
      type: string
      title: string
      estimated_duration_minutes: integer|null
      reason_codes: [string]
      status: string
  review_due_candidates:
    - knowledge_unit_ref: versioned_ref
      schedule_ref: versioned_ref
      next_due_at: datetime|null
      review_priority: float|null
      evidence_quality: float|null
      included_activity_ref: versioned_ref|null
  current_evidence_summary:
    knowledge_unit_ref: versioned_ref|null
    confidence: float|null
    independent_success_count: integer|null
    delayed_recall_evidence_count: integer|null
    transfer_evidence_count: integer|null
    validation_obligation: NONE|INDEPENDENT_VALIDATION_REQUIRED|UNKNOWN
  compatibility_quick_start:
    source_label: LEGACY_COMPATIBILITY
    recent_sessions:
      - session_id: uuid
        title: string|null
        subject: string
        knowledge_point_id: string|null
        status: active|ended|archived
        updated_at: datetime
```

### UI-DATA-031 — Ownership

- goal/objective/activity/plan inclusion → SYS06；
- review candidate / next_due_at → SYS07；
- evidence counts/confidence → SYS03；
- validation obligation → SYS05。

Query assembler MUST NOT locally decide activity priority, review inclusion or validation completion.

### UI-DATA-032 — Local Date

今日视图 MAY 使用用户时区分组展示，但 canonical timestamps 保持 timezone-aware。客户端日期变化不得自动创建新 plan/version。

## 5. Goal and Path Views

### UI-DATA-040 — GoalListViewV1

```yaml
goals:
  - goal_ref: versioned_ref
    title: string
    topic: string
    target_capabilities: [string]
    success_criteria: [string]
    deadline_at: datetime|null
    weekly_time_budget_minutes: integer|null
    status: string
    confirmed_by_user: boolean
```

只返回当前授权用户的数据。历史 version MAY 通过独立 detail query 后续补充，不在首个 query 强制范围。

### UI-DATA-041 — LearningPathViewV1

```yaml
learning_path:
  plan_ref: versioned_ref
  goal_ref: versioned_ref
  status: active|superseded|completed|paused
  created_from_learner_state_version: integer
  knowledge_graph_version: string
  review_schedule_version: string|null
  assumptions: object
  reason_codes: [string]
  objectives:
    - objective_ref: versioned_ref
      capability: string|null
      cognitive_process: string|null
      status: string|null
      activity_refs: [versioned_ref]
      reason_codes: [string]
  activities:
    - activity_ref: versioned_ref
      objective_ref: versioned_ref
      type: string
      title: string
      estimated_duration_minutes: integer
      priority: float
      reason_codes: [string]
      status: string
```

前端不得根据 priority 重新排序并称为 canonical plan；服务端 response order 是展示基线。

### UI-DATA-042 — Path Scope and Missing Objective Metadata

`GET /workspace/path` MAY 接受 `goal_id` scope。未提供 scope 时：零个 current plan 返回 EMPTY；
恰好一个可返回该 plan；多个 current plan MUST 返回
`MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE`，不得以创建时间、priority 或前端选择
隐式定义业务上的唯一 current plan。

当前 SYS06 未发布 durable LearningObjective metadata stream。Query MUST 保留 exact objective ref，
并将 capability/cognitive_process/status 返回为 null，附
`OBJECTIVE_METADATA_UNAVAILABLE`。不得从 Goal title、Activity type、KnowledgeUnit 或 legacy
字段推断。未来 SYS06 发布 versioned Objective 时 MAY additive 填充这些 nullable 字段。

## 6. ActivityWorkspaceViewV1

### UI-DATA-050 — Contract

```yaml
activity_workspace:
  activity_ref: versioned_ref
  objective_ref: versioned_ref
  plan_ref: versioned_ref
  title: string
  activity_type: string
  status: string
  session_ref: versioned_ref|null
  teaching_action:
    action_ref: versioned_ref|null
    strategy_family: string|null
    teaching_stage: string|null
    scaffold_control: NONE|LOW|MEDIUM|HIGH|null
    hint_specificity: NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT|null
    answer_exposure: NONE|PARTIAL|COMPLETE|null
    validation_obligation: NONE|INDEPENDENT_VALIDATION_REQUIRED|UNKNOWN
    reason_codes: [string]
  actual_assistance:
    assistance_state: INDEPENDENT|ASSISTED|ANSWER_EXPOSED|null
    scaffold_control: string|null
    hint_specificity: string|null
    answer_exposure: string|null
    source_ref: versioned_ref|null
  evidence_sources:
    - label: string
      source_span_id: uuid
      document_id: uuid|null
      locator: object|null
```

### UI-DATA-051 — Planned vs Actual

`teaching_action` 表示 allowed/planned envelope；`actual_assistance` 表示已经发生的实际体验。UI 必须明确区分，缺 actual data 时不得复制 planned envelope 作为事实。

### UI-DATA-052 — Session Link

在 canonical activity launch command 未冻结前，`session_ref` MAY 为 null：

- `ACTIVE` / `RESUMABLE` MUST 携带可打开的 canonical `session_ref`；
- `REQUIRES_START_COMMAND` 表示 activity 已存在，但当前 Spec Set 不授权启动；
- `UNAVAILABLE` 必须带稳定 reason code；
- UI 不得通过创建 legacy session 自动写回虚构 activity/session link；
- 兼容入口产生的 session 必须标记来源，且不得改变该 activity 的 `launch_state`。

## 7. LibraryViewV1 / KnowledgeMapViewV1

### UI-DATA-059 — Library Contract

```yaml
library:
  view_state: READY|PARTIAL|STALE|EMPTY
  total: integer
  page: integer
  page_size: integer
  documents:
    - document_ref: versioned_ref
      document_id: uuid
      title: string
      media_type: string
      file_size_bytes: integer
      subject: string|null
      processing_status: pending|processing|completed|failed|rejected|quarantined
      moderation_status: pending|approved|requires_review|rejected
      current_revision_ref: versioned_ref|null
      knowledge_status: NOT_MODELED|CANDIDATES|PUBLISHED|LEGACY_COMPATIBILITY
      knowledge_unit_count: integer
      relation_count: integer
      reason_codes: [string]
      created_at: datetime
      updated_at: datetime
```

Library response MUST NOT 返回 storage path、raw parser/security details 或完整本地文件内容。

### UI-DATA-060 — Contract

```yaml
knowledge_map:
  scope:
    document_refs: [versioned_ref]
    subject: string|null
    graph_version: string
  nodes:
    - knowledge_unit_ref: versioned_ref
      kind: string
      canonical_name: string
      description: string
      provenance_type: string
      confidence: float|null
      status: candidate|verified|published|rejected|superseded
      evidence_span_refs: [versioned_ref]
      learner_evidence_summary: object|null
  edges:
    - relation_ref: versioned_ref
      prerequisite_ref: versioned_ref
      target_ref: versioned_ref
      strength: hard|soft|contextual
      confidence: float|null
      status: candidate|published|rejected|superseded
      evidence_span_refs: [versioned_ref]
  source_spans:
    - source_span_ref: versioned_ref
      source_span_id: uuid
      document_id: uuid
      page: integer|null
      chapter: string|null
      start_offset: integer|null
      end_offset: integer|null
      excerpt: string
```

### UI-DATA-061 — Query Source

Node/relation truth 来自 SYS01；learner evidence summary 来自 SYS03，只读拼接。Map response MUST NOT 把 learner evidence 写回 node，或把 node status 当 learner mastery。

### UI-DATA-062 — Pagination / Scope

Knowledge map query MUST 要求明确 scope，并对 node/edge 数量设置上限或分页。前端不得默认加载所有文档和全部图谱到一个 canvas。

UI-02A 首个实现 MUST 使用单一 `document_id` scope，默认上限 nodes 100、edges 200、source spans 300。`minimal-binding-v1` 必须标为 compatibility/pending rebuild；不得以文件名节点伪装 mature published map。无可靠 relation 时返回空 edges 与 reason code，不得从章节顺序推断 prerequisite。

## 8. EvidenceProfileViewV1

### UI-DATA-070 — Contract

```yaml
evidence_profile:
  knowledge_units_assessed: integer
  entries:
    - knowledge_unit_ref: versioned_ref
      label: string|null
      competence_probability: float|null
      confidence: float|null
      independent_success_count: integer|null
      delayed_recall_evidence_count: integer|null
      transfer_evidence_count: integer|null
      evidence_count: integer|null
      effective_evidence_weight: float|null
      active_misconception_ids: [uuid]|null
      algorithm_id: string|null
      algorithm_version: string|null
      product_label: string|null
      product_label_rule_version: string|null
  legacy_compatibility:
    visible_by_default: false
    fields: object
    source_label: LEGACY_COMPATIBILITY
```

### UI-DATA-071 — Product Label Gate

`product_label` 只有在 SYS03 canonical query 返回稳定 label 与 rule version 时才可非 null。UI/API assembler MUST NOT 从 `competence_probability` 自行派生。

### UI-DATA-072 — Current `/users/profile` Migration

首个实现 MAY 直接消费当前 `profile.mastery.entries` 作为 canonical source，并忽略 legacy fields。新增 `/workspace/evidence` SHOULD 提供 KnowledgeUnit label/ref 与统一 availability/source semantics；切换完成后旧 profile learning aggregates 有明确 retirement condition。

## 9. Security, Privacy and Caching

### UI-DATA-080

所有 workspace query 必须绑定当前授权用户。Knowledge/document query 也必须执行 resource ownership；仅凭 object id 不得跨用户读取。

### UI-DATA-081

响应不得包含密码、token、API key、内部 Prompt、grader-only answer、未经授权的全文文档或本地绝对路径。

### UI-DATA-082

Frontend cache 只能是可失效 read cache。切换用户、退出登录、resource deletion 或 schema major change 时必须清除相关缓存。Local storage 不得成为 LearningPlan/LearnerState/ReviewSchedule truth。

### UI-DATA-083

含个人学习数据的 Query 默认不得被共享代理缓存；transport cache policy 与 Electron 本地 cache 必须遵循当前 auth/privacy mode。

## 10. Errors

### UI-DATA-090

除既有 stable error code 外，workspace query 如需新增 code，正式 API Spec 至少应覆盖：

```text
WORKSPACE_SOURCE_PARTIAL
WORKSPACE_ACTIVITY_NOT_FOUND
WORKSPACE_PLAN_NOT_AVAILABLE
WORKSPACE_KNOWLEDGE_SCOPE_REQUIRED
WORKSPACE_SCHEMA_UNSUPPORTED
```

对应 endpoint 进入实现前必须复核这些 code 是否应复用现有 `PLAN_NO_FEASIBLE_ACTIVITY`、`SCHEMA_VERSION_UNSUPPORTED` 等稳定语义，避免重复错误协议。

## 11. Acceptance Criteria

- `UI-DATA-AC-001`：每个聚合字段可追踪 owner/system 与 exact ref/version 或明确 compatibility source。
- `UI-DATA-AC-002`：MISSING/STALE/LOW_CONFIDENCE 不被前端转成 0 或 READY。
- `UI-DATA-AC-003`：today query 不把 ReviewDue candidate 自动变成计划活动。
- `UI-DATA-AC-004`：activity query 分离 planned envelope 与 actual assistance。
- `UI-DATA-AC-005`：knowledge map 不合并 KnowledgeUnit truth 与 learner evidence truth。
- `UI-DATA-AC-006`：evidence query 不从 probability 派生无版本 mastery label。
- `UI-DATA-AC-007`：API handler 不含 planner、review、mastery、policy 或 knowledge algorithm。
- `UI-DATA-AC-008`：退出/换用户后 frontend cache 不泄漏上一用户学习数据。
- `UI-DATA-AC-009`：未冻结的新 commands 不会以假按钮或 frontend-only state 出现。
- `UI-DATA-AC-010`：只有 ACTIVE/RESUMABLE activity 才携带可进入工作台的 canonical session link。

## 12. Forbidden Implementations

禁止：

- 新建 `workspace_state` JSON 作为多个 owner 的第二事实源；
- API 为页面方便直接 join ORM 后重新判断业务语义；
- 在前端复制 planner/review/policy thresholds；
- 把 `/users/profile` legacy 字段改名后伪装成 canonical；
- 为知识地图读取 vector index/graph projection 后当作唯一 truth；
- 用 current mutable state 补齐历史 plan/action/evidence refs；
- 为了 UI 完整直接开放未定义的 SetMastery/SetNextReviewAt/SetTeachingAction。

## 13. OnboardingJourneyViewV1

### UI-DATA-100

`GET /api/v1/onboarding/journey` MUST 复用 `ONBOARD-*` strict view。前端只呈现四个 steps 与一个
`next_action`，不得依据 owner arrays、localStorage、message、duration 或 model result 重算完成、排序
业务对象或生成恢复动作。

### UI-DATA-101

Preference 与 journey cache 必须 current-user scoped 且可失效；logout/switch/dismiss/reopen/owner
mutation 后重查。MISSING/STALE/PARTIAL 不得转换为 false/READY；dismissed 不得转换为 completed。
