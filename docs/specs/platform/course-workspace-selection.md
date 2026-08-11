# Course / Workspace Selection and Activity Projection Contract

> Spec ID：`CWSP-*`
> 状态：Canonical Implementation Contract / Frozen
> 版本：v1.0
> Governing：ADR-0016、ADR-0019、ADR-0022、ADR-0023

## 1. Scope and Ownership

### CWSP-001 — Single Writer

Platform Workspace Registry 是以下事实的唯一 writer：

- Workspace list/get/create metadata；
- owner-scoped `WorkspaceSelection.current_workspace_id`；
- selection version；
- create/switch idempotency receipts。

UI、route、localStorage、React state、Workspace read assembler、LearningSession、SYS06、LLM 均不得成为第二 writer。

### CWSP-002 — Owner Boundaries Remain

- Workspace / WorkspaceSelection → Platform Workspace Registry；
- LearningActivity / Plan → SYS06；
- LearningSession interval/scope → Platform Learning Session Registry；
- Material、UserNote、Transcript、Attempt、LearnerState、TeachingAction、ReviewSchedule owner 不变。

Course 是 user-facing vocabulary，不新增 Course table、`course_id` 或第二 DTO identity。

### CWSP-003 — Non-goals

本合同不授权 Workspace delete/cascade、跨 Workspace move/copy、LearningProject=Course、Goal/Plan editing、Teaching Policy/Mastery/Review 变化或前端实现。

## 2. Durable State

### CWSP-010 — WorkspaceSelectionV1

```yaml
workspace_selection_v1:
  owner_id: uuid
  version: integer >= 1
  current_workspace_id: uuid
  reason: FIRST_CREATE|LEGACY_MIGRATION|EXPLICIT_SWITCH|RECOVERY_RECONCILIATION
  previous_workspace_id: uuid|null
  correlation_id: uuid
  updated_at: datetime
```

`owner_id` 唯一；version 单调递增。current target MUST 属于同一 owner 且 `lifecycle=active`。selection 是 application preference，不改变 Workspace ownership/default/lifecycle。

### CWSP-011 — Empty / Default / Current Cardinality

| Owner state | Active Workspace | Active default | Selection |
|---|---:|---:|---:|
| fresh、无 legacy data | 0 | 0 | 0 |
| first Course create 后 | ≥1 | exactly 1 | exactly 1 |
| legacy migration 后 | ≥1 | exactly 1 | exactly 1 |

active Workspace 存在时最多一个 active default。current MAY 与 default 不同。不得用 `is_default` 更新冒充 switch。

### CWSP-012 — Command Receipt

```yaml
workspace_command_receipt_v1:
  receipt_id: uuid
  owner_id: uuid
  command_type: CREATE_WORKSPACE|SWITCH_WORKSPACE
  idempotency_key: string
  command_digest: string
  response_payload: object
  created_at: datetime
```

唯一性至少为 `(owner_id, command_type, idempotency_key)`。相同 key + 相同 digest 返回原结果；相同 key + 不同 digest 返回 `WORKSPACE_IDEMPOTENCY_CONFLICT`。

## 3. Public Schemas

所有 schema strict、`schema_version="1.0"`，拒绝 unknown major。

### CWSP-020 — WorkspaceItemV1

```yaml
workspace_item_v1:
  workspace_id: uuid
  workspace_ref: versioned_ref
  display_name: string
  version: integer >= 1
  lifecycle: active|trash
  is_default: boolean
  is_current: boolean
  created_at: datetime
  updated_at: datetime
```

### CWSP-021 — WorkspaceListResponseV1

```yaml
workspace_list_response_v1:
  schema_version: "1.0"
  generated_at: datetime
  data:
    view_state: EMPTY|READY|STALE
    selection_version: integer|null
    current_workspace_id: uuid|null
    workspaces: [WorkspaceItemV1]
  correlation_id: uuid
```

排序固定为：current first；其余 `updated_at DESC, created_at ASC, workspace_id ASC`。`EMPTY` 必须是真实 0 Workspace/0 selection；不得 query 时 bootstrap。

Default list includes active Workspaces only。Trash lifecycle is returned only by an explicit lifecycle-management/recovery query authorized by its owner contract；the Course sidebar MUST NOT expose trash as a normal Course candidate。

### CWSP-022 — WorkspaceGetResponseV1

显式 get 必须返回 owner 内 exact WorkspaceItemV1。foreign/inaccessible 与不存在使用同一不可枚举错误；get 不写 selection。

### CWSP-023 — WorkspaceTransitionGuardV1

```yaml
workspace_transition_guard_v1:
  schema_version: "1.0"
  composer_draft: CLEAR|PRESERVED|DISCARD_CONFIRMED|UNRESOLVED
  stream: CLEAR|BACKGROUND_SAFE|CANCEL_CONFIRMED|UNRESOLVED
  user_note: CLEAR|SAVED|PRESERVED|DISCARD_CONFIRMED|UNRESOLVED
  material_position: PRESERVED|DISCARD_CONFIRMED|UNRESOLVED
  source_refs: [versioned_ref]
```

任何 `UNRESOLVED` 必须在写入前返回 recovery required。`DISCARD_CONFIRMED` 只确认 presentation/transient work；不得删除 durable owner data。frontend 必须从真实页面 state 构造 guard，测试证明不能固定伪报 `CLEAR`。

### CWSP-024 — CreateWorkspaceV1

```yaml
create_workspace_v1:
  schema_version: "1.0"
  display_name: string
  expected_selection_version: integer|null
  transition_guard: WorkspaceTransitionGuardV1
  idempotency_key: string
```

名称 trim 后 1..120 字符，不允许 control character。fresh create 要求 `expected_selection_version=null`；已有 selection 要求 exact version。

### CWSP-025 — SwitchWorkspaceV1

```yaml
switch_workspace_v1:
  schema_version: "1.0"
  target_workspace_id: uuid
  expected_selection_version: integer
  transition_guard: WorkspaceTransitionGuardV1
  idempotency_key: string
```

客户端不得提交 owner_id、source_workspace_id、target lifecycle、selection target status 或任何 learning state mutation。

### CWSP-026 — WorkspaceMutationResultV1

```yaml
workspace_mutation_result_v1:
  schema_version: "1.0"
  outcome: CREATED_AND_SELECTED|SWITCHED|ALREADY_CURRENT|RECOVERY_REQUIRED
  workspace: WorkspaceItemV1|null
  selection_ref: versioned_ref|null
  selection_version: integer|null
  preserved:
    activity_refs: [versioned_ref]
    learning_session_refs: [versioned_ref]
    workflow_run_refs: [versioned_ref]
    note_refs: [versioned_ref]
  blockers: [WorkspaceSwitchBlockerV1]
  correlation_id: uuid
```

`RECOVERY_REQUIRED` 不得伴随 Workspace/selection write。`ALREADY_CURRENT` 为成功幂等结果，不增加 selection version。

### CWSP-027 — WorkspaceSwitchBlockerV1

```yaml
workspace_switch_blocker_v1:
  kind: COMPOSER_DRAFT|STREAM|USER_NOTE|LEARNING_SESSION|MATERIAL_POSITION
  source_ref: versioned_ref|null
  owner: FRONTEND_PRESENTATION|PLATFORM_SESSION|SYS08|USER_NOTE_OWNER
  allowed_actions: [PRESERVE|SAVE|BACKGROUND|CANCEL|DISCARD|RETURN]
  reason_code: string
```

不返回内容正文、Prompt、other-Workspace metadata 或内部路径。

## 4. Commands and Transactions

### CWSP-030 — Create-and-select Atomicity

Create 成功必须在一个事务内创建 Workspace、必要的 first-default marker、new selection version、receipt/outbox。任一步失败全部回滚。不得创建 Workspace 后靠 frontend 第二次 switch 补齐。

Create 只证明 Workspace 已创建并选中；Material/Goal/Plan/Activity readiness 保持独立 owner result。

### CWSP-031 — Switch Atomicity

Switch 顺序：

```text
resolve LocalOwner
→ load current selection FOR UPDATE / equivalent CAS
→ validate expected version
→ resolve target in same owner without existence leakage
→ validate active lifecycle
→ evaluate transition guard + server-known durable/in-flight refs
→ append new selection version + receipt
→ commit
```

不得在 selection commit 前后隐式写其他 owner state。

### CWSP-032 — Preservation Semantics

| Work | Required behavior |
|---|---|
| composer draft | per-Workspace preserve or explicit discard confirmation |
| streaming run | background/reconnect or explicit cancel；switch does not duplicate completion |
| UserNote | accepted ADR-0021 / `UNSI-*` save/version receipt or preserve/explicit discard；conflict remains owner error |
| active LearningSession | remains source-Workspace scoped；never auto-end；return resumable ref |
| Material tabs/position | preserve keyed by workspace+material or explicit discard |

Server-known source Session/Activity/run refs必须从 owner query读取，不能从 client title/free text 推断。前端 transient safety 与后端 canonical mutation是双层 gate；任何一层 unresolved 都不得显示 switched success。

### CWSP-033 — Concurrency

stale expected selection version 返回 `WORKSPACE_SELECTION_VERSION_CONFLICT`，包含 current selection version/ref（不含 foreign metadata）。客户端 re-query 后由用户重新确认；不得 blind overwrite/auto retry stale command。

### CWSP-034 — No Hidden Writes

GET/list/current/activity projection、route resolution、redirect、reload、browser back/forward、deep link validation 全部 side-effect free。不得创建 Workspace/selection/Activity/Session/receipt。

## 5. API Surface

### CWSP-040 — Canonical Routes

```text
GET  /api/v1/workspaces
POST /api/v1/workspaces
GET  /api/v1/workspaces/current
GET  /api/v1/workspaces/{workspace_id}
POST /api/v1/workspaces/{workspace_id}/switch
GET  /api/v1/workspaces/{workspace_id}/activities
```

`GET /api/v1/workspace/context` 在迁移期适配 current selection；不得继续硬编码 default，也不得聚合全部 Workspace。写 response 使用 `private, no-store`；create/switch 必须携带 idempotency key 与 expected version。

### CWSP-041 — Explicit Scope

所有 Workspace 子资源请求以 route scope 为 hard filter。`/workspace/**` legacy routes只可解析 current selection；selection missing 时返回 typed missing，不得自动创建 default。

### CWSP-042 — Deep-link Resolution

Course deep link先 owner-safe get，再加载目标 Course view；与 current selection 不同也可只读展示目标，但 UI 必须标明尚未显式切换，任何写 command 继续携带 exact route Workspace。产品主路径中的 Course item Action 应先 switch success，再 navigation。

## 6. Course-scoped Activity Projection

### CWSP-050 — WorkspaceActivityIndexResponseV1

```yaml
workspace_activity_index_response_v1:
  schema_version: "1.0"
  generated_at: datetime
  data:
    view_state: EMPTY|READY|PARTIAL|STALE
    workspace_ref: versioned_ref
    resumable_activity_ref: versioned_ref|null
    activities:
      - activity_ref: versioned_ref
        lifecycle_state_ref: versioned_ref
        plan_ref: versioned_ref
        goal_ref: versioned_ref
        display_title: string
        title_source_ref: versioned_ref
        activity_type: string
        status: planned|available|active|completed|skipped|superseded
        launch_state: RESUMABLE|REQUIRES_START_COMMAND|UNAVAILABLE
        latest_transition_at: datetime
        learning_session_refs: [versioned_ref]
    reason_codes: [string]
  source_status: [source_status]
  correlation_id: uuid
```

### CWSP-051 — Exact SYS06 Source

每项必须通过：

```text
Workspace
← exact LearningGoal.workspace_id
← exact current LearningPlan.learning_goal_id
← immutable LearningActivity.plan_id+plan_version
← latest LearningActivityStateV1
```

任一链不完整、ambiguous、foreign、superseded plan mismatch 时 fail closed或诚实 PARTIAL/STALE；不得用 dialog session、transcript recency、route、title 或 frontend cache补齐。

### CWSP-052 — Ordering and Resume

- `active` first，按 `started_at DESC, activity_id ASC`；
- `available` next，保持 plan order，activity id tie-break；
- 其余 recent items按 `latest_transition_at DESC, activity_id ASC`；
- `resumable_activity_ref` 只可指向同 Workspace current-plan latest `active`；
- 多个 active 若违反 current invariant，返回 `PARTIAL + MULTIPLE_ACTIVE_ACTIVITIES`，不得任意选择；
- `available` 必须调用 SYS06 start command，不得 GET/navigation 自动 start。

### CWSP-053 — Title Boundary

`display_title` 使用 LearningActivity typed semantics 与 versioned presentation catalog。Conversation/Dialog title 不得成为 Activity name；LLM 不得在 query 时生成 title。未来 durable user-edited Activity title 需 SYS06 新合同。

### CWSP-054 — LearningSession Link

new Activity-scoped LearningSession MUST pin `learning_activity_id` and validate activity/goal/project/material are same Workspace。Session link不改变 lifecycle；resume projection只返回 exact valid active/ended session refs，不复制 transcript。

## 7. Stable Errors and Retry

### CWSP-060 — Codes

```text
WORKSPACE_NOT_FOUND_OR_INACCESSIBLE
WORKSPACE_SELECTION_MISSING
WORKSPACE_SELECTION_VERSION_CONFLICT
WORKSPACE_IDEMPOTENCY_CONFLICT
WORKSPACE_SWITCH_RECOVERY_REQUIRED
WORKSPACE_NAME_INVALID
WORKSPACE_SCHEMA_UNSUPPORTED
WORKSPACE_INTEGRITY_FAILED
WORKSPACE_ACTIVITY_SCOPE_VIOLATION
WORKSPACE_ACTIVITY_PROJECTION_UNAVAILABLE
```

- validation/business/conflict/not-found/security errors non-retryable without changed input/re-query；
- transient DB/projection dependency MAY retry bounded；
- retry必须复用 idempotency key；
- provider/session failure不得写 learner failure或 selection success。

## 8. Migration / Rollback / Forward-fix

### CWSP-070 — Additive Migration

1. add WorkspaceSelection + Workspace command receipt structures；
2. add nullable `learning_sessions.learning_activity_id`；
3. classify owner：fresh-empty vs legacy-data/existing Workspace；
4. fresh-empty 保持 0 Workspace/selection；
5. legacy-data 幂等 create/resolve default + backfill + selection；
6. existing Workspace missing selection → select active default deterministically；
7. validate owner/target/cardinality/FK；
8. cut over current readers；
9. enable create/switch writers；
10. enforce strict new Session activity link at application boundary。

不得从 filename/title/most-recent timestamp猜测 Workspace/Activity。旧 Session 无 exact activity proof 时保持 nullable compatibility并给 reason code。

### CWSP-071 — Rollback

writer cutover 前且无新 selection/create writes时可回滚 additive schema。writer cutover、多个 Workspace 或 selection version > 1 后禁止 destructive downgrade；使用 forward-fix、reconciliation 与 verified recovery point。

## 9. Security / Privacy / Observability

### CWSP-080

Workspace 是 LocalOwner 内隔离边界，不是 auth role。所有 query/write必须同时验证 owner + Workspace；foreign ref与不存在不可枚举。response/log不暴露 other-Workspace name、Activity title、note/transcript/content、secret或local path。

### CWSP-081

sanitized telemetry至少：`workspace_id`、source/target selection version、command/result/error code、correlation/idempotency/receipt ref、activity/session ref（适用时）。不得记录 transition guard正文或用户内容。

## 10. Required Tests

### CWSP-090 — Contract / Architecture

- strict v1 / unknown major；
- one Platform writer；no UI/localStorage/default-marker truth；
- API transport-only；Activity assembler read-only；
- command digest/idempotency/version；
- no hidden write on GET/route/refresh/retry。

### CWSP-091 — Persistence / Migration

- fresh SQLite owner remains 0 Workspace；
- legacy fixture gets exactly one default + selection；
- rerun migration；
- existing single/multiple Workspace missing selection；
- create-and-select atomic rollback；
- upgraded fixture与 fresh `alembic upgrade head`；
- `alembic check` single head；
- PostgreSQL constraints where CI available；
- post-cutover forward-fix。

### CWSP-092 — Isolation / Recovery

- owner A/B and Workspace A/B list/get/switch isolation；
- foreign ids return same non-enumerable error；
- stale version/no write；
- same/different idempotency digest；
- every transition guard blocker；
- active Session/run/note/material position preserved；
- cross-Workspace Activity/Session chain rejected；
- no negative LearningEvidence on infrastructure failure。

### CWSP-093 — Activity Projection

- exact goal/plan/activity/lifecycle refs；
- stable grouping/order/tie-break；
- multiple active → PARTIAL；
- available is not auto-started；
- superseded/foreign/ambiguous chains fail closed；
- title catalog versioned、no chat/LLM inference；
- refresh deterministic/no write。

## 11. Acceptance Criteria

- `CWSP-AC-001`：fresh owner真实返回 Course Empty State基础事实，不隐式创建 Workspace。
- `CWSP-AC-002`：legacy data幂等归属 exactly one default Workspace + selection。
- `CWSP-AC-003`：current selection只有 Platform Registry writer，与 default marker分离。
- `CWSP-AC-004`：create-and-select原子、versioned、idempotent，无半成品 Course。
- `CWSP-AC-005`：switch unresolved work不写 selection、不静默丢 draft/stream/note/session/material position。
- `CWSP-AC-006`：deep link/route/read/refresh无 business side effect。
- `CWSP-AC-007`：foreign Workspace/Activity ref fail closed且不可枚举。
- `CWSP-AC-008`：Activity projection只组合 exact SYS06 refs，不形成第二 Activity truth。
- `CWSP-AC-009`：active Activity可恢复、available Activity只经 SYS06 start command启动。
- `CWSP-AC-010`：new Activity-scoped Session pin exact activity；legacy不猜测 backfill。
- `CWSP-AC-011`：migration/rollback/forward-fix与 SQLite/PostgreSQL verification完整。
- `CWSP-AC-012`：Product/UX/Engineering/Quality/Learning Evidence分别报告；工程 PASS 不声称真人学习有效。

## 12. Forbidden Implementations

禁止：browser/route/default marker作为 current truth；GET/redirect自动 switch/create/start；create 与 select非原子；switch静默取消/丢弃 work；foreign existence leakage；owner-global list；Activity title来自 chat/LLM；Activity projection写 SYS06；Session 自动完成 Activity；跨 Workspace refs；destructive downgrade；用 mock Course 声称真实能力可用。
