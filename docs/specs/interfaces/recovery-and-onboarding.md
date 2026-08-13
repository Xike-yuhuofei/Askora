# Askora Recovery Contract

> Spec ID: `RECOVERY-*`
> Status: FROZEN
> Version: v1.0
> Governing decision: ADR-0012

## 1. Boundary

### RECOVERY-001 — Query/control plane only

Recovery Center MUST 组合 owner-published state 和 SYS08 operational incidents，不得拥有或直接
改写八类系统的业务 truth。恢复动作 MUST 路由到原 owner command。

### RECOVERY-002 — Two entry points, one vocabulary

App 内运行期使用 `RecoveryIssueViewV1/RecoveryActionV1/RecoveryResultV1`；后端不可用时 Electron
使用 `BootstrapDiagnosticV1`。两者共享稳定 code、数据安全状态和动作语义，不共享运行依赖。

## 2. Strict public contracts

所有对象 MUST strict、unknown field forbidden、timezone-aware，未知 major version拒绝。

```yaml
RecoveryIssueViewV1:
  schema_version: "1.0"
  issue_ref: string
  issue_version: integer
  code: string
  category: dependency|transient|conflict|security|data_integrity|internal
  severity: info|warning|blocking
  status: active|waiting|action_running|resolved
  title: string
  summary: string
  data_safety: preserved|preserved_but_unavailable|at_risk|unknown
  duplicate_risk: none|prevented_by_idempotency|requires_confirmation|not_applicable
  source_system: SYS01|SYS08|BOOTSTRAP|DATA_CONTROL
  resource_ref: string|null
  correlation_id: string|null
  attempt_count: integer
  retry_budget: integer|null
  next_eligible_at: datetime|null
  actions: [RecoveryActionV1]
  opened_at: datetime
  updated_at: datetime
```

```yaml
RecoveryActionV1:
  action_code: retry_owner_command|reinspect_document|open_model_settings|open_data_recovery|open_activity|open_ocr_review|reselect_file|wait_until|copy_diagnostics|acknowledge
  label: string
  kind: command|navigate|wait|client
  enabled: boolean
  disabled_reason_code: string|null
  endpoint: string|null
  method: POST|null
  route: string|null
  requires_idempotency_key: boolean
  requires_confirmation: boolean
```

```yaml
RecoveryCommandV1:
  schema_version: "1.0"
  issue_ref: string
  expected_issue_version: integer
  action_code: string
  idempotency_key: string
```

```yaml
RecoveryResultV1:
  schema_version: "1.0"
  result_ref: string
  issue_ref: string
  status: accepted|already_applied|waiting|succeeded|failed
  issue_version: integer
  owner_command_ref: string|null
  replacement_task_ref: string|null
  message: string
  correlation_id: string
  completed_at: datetime
```

```yaml
BootstrapDiagnosticV1:
  schema_version: "1.0"
  status: starting|ready|failed
  code: string|null
  data_safety: preserved|unknown
  retryable: boolean
  attempt: integer
  started_at: datetime|null
  updated_at: datetime
  exit_code: integer|null
  actions: [retry_backend, copy_diagnostics]
```

## 3. Stable catalog

第一版 MUST 覆盖：

- `AI_PROVIDER_TIMEOUT`、`AI_PROVIDER_RATE_LIMITED`、`AI_PROVIDER_KEY_INVALID`、
  `AI_PROVIDER_KEY_MISSING`、`AI_MODEL_UNAVAILABLE`、`AI_OUTPUT_VALIDATION_FAILED`；
- `CONTENT_PROCESSING_FAILED`、`CONTENT_QUARANTINED`、`CONTENT_FILE_MISSING`、
  `CONTENT_OCR_REVIEW_REQUIRED`；
- `DATABASE_UNAVAILABLE`、`DATABASE_MIGRATION_REQUIRED`、`DATABASE_INTEGRITY_FAILED`；
- `OUTBOX_RETRY_WAITING`、`OUTBOX_RETRY_EXHAUSTED`、`OUTBOX_HANDLER_UNAVAILABLE`；
- ADR-0012 定义的 bootstrap codes。

code → category/retry policy/data safety/action list MUST 在服务端单一 versioned catalog 中定义。
UI 只呈现服务端动作，不用自由文本或 HTTP status 猜测。

provider issue 若携带 current-user scoped `activity:{id}`，MUST 提供 `open_activity` 导航回 canonical
`/learn/:id`；该动作不重放模型调用。`CONTENT_FILE_MISSING` 只有在 SYS01 已冻结并实现原文件替换
command 时才能启用 `reselect_file`，否则只导航已验证的数据恢复 owner 页面。

`CONTENT_OCR_REVIEW_REQUIRED` MUST 由 current-user scoped `DocumentOcrRun.status=review_required`
投影，并提供 `open_ocr_review` 导航到同一 document/run 的 SYS01 人工复核界面。导航不得自动接受、
拒绝或发布候选；已 accepted/rejected 的 run 不再作为 active recovery issue。

## 4. Query and command

- `GET /api/v1/recovery/issues` current-user scoped，返回 active/waiting；MAY 通过显式 filter 查询历史；
- `POST /api/v1/recovery/actions` 是 transport-only command endpoint；
- command 必须验证 issue version、action allowlist、owner scope、budget 与 idempotency；
- unauthorized 与 missing 保持不可枚举；
- command 成功后 MUST 重新投影 issue；UI 不乐观伪造 resolved。

## 5. Retry and audit

- automatic/manual attempt 分开计数；`retry_budget` 和 `next_eligible_at` 由服务端返回；
- dead-letter history immutable；允许恢复时创建 replacement task/run 并记录 `recovery_of`；
- 每次 action request/result 追加安全审计，重复 idempotency key 返回相同 `RecoveryResultV1`；
- unknown/non-idempotent/unscoped task MUST NOT replay；
- `acknowledge` 只隐藏提示，不改变 owner failure 或 active issue truth。

## 6. Data and learning safety

- 响应/日志不得含绝对路径、密钥、Prompt、provider 原始 body、SQL/traceback、grader-only 数据；
- `data_safety=preserved` 需由 owner transaction/file checksum 等证据支持；不能证明时使用 `unknown`；
- provider/tool/storage/database/outbox/bootstrap failure MUST NOT 生成 learner incorrect/forgotten、
  score=0、mastery decrease、review failure、goal/activity completion。

## 7. Acceptance criteria

- `RECOVERY-AC-001`：每个 issue 明确 what/safety/action/duplicate risk；
- `RECOVERY-AC-002`：稳定目录覆盖 P1-07 全部类别且 UI 无自由文本分支；
- `RECOVERY-AC-003`：owner command、scope、version、budget、idempotency 和 audit 可证明；
- `RECOVERY-AC-004`：restart 后 issue/action result 可恢复，dead-letter history 不被覆盖；
- `RECOVERY-AC-005`：后端不可达时 bootstrap shell 仍可解释并重试；
- `RECOVERY-AC-006`：系统失败与 learner evidence 数据层完全分离；
- `RECOVERY-AC-007`：secret/path/prompt/grader-only leakage tests 通过。

---

## Askora First-use Onboarding Contract

> Spec ID：`ONBOARD-*`
> 状态：FROZEN
> 版本：v1.0
> Governing decision：ADR-0106

### 1. Boundary and Ownership

#### ONBOARD-001 — Read projection, not workflow owner

Onboarding MUST 只组合 Platform Experience Preference、P1-02、SYS01、SYS06、SYS08、P1-03 与
P1-07 已发布的 query/action。它不得创建第二 model/document/goal/plan/activity/transcript/recovery
truth，也不得直接调用领域 repository 修改业务状态。

#### ONBOARD-002 — Presentation preference owner

Platform Experience Preference MUST 是 `OnboardingPreferenceV1` 唯一 writer。该对象只控制展示，
不得包含 step completion、document/goal/plan/activity/transcript ref 或 secret。

### 2. Strict Public Contracts

全部对象 MUST strict、unknown field forbidden、timezone-aware；未知 major version MUST 拒绝。

```yaml
OnboardingPreferenceV1:
  schema_version: "1.0"
  journey_id: first-learning-v1
  preference_version: integer
  visibility: ACTIVE|DISMISSED
  boundary_notice_version_acknowledged: string|null
  dismissed_reason: USER_DEFERRED|COMPLETED_JOURNEY|LEGACY_EXISTING_USER_BACKFILL|null
  created_at: datetime
  updated_at: datetime
```

```yaml
OnboardingStepViewV1:
  step: MODEL|MATERIAL|GOAL|FIRST_ACTIVITY
  state: NOT_STARTED|IN_PROGRESS|COMPLETE|BLOCKED|STALE
  title: string
  summary: string
  source_status:
    - source_system: string
      availability: AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE
      source_ref: string|null
      observed_at: datetime|null
      reason_codes: [string]
```

```yaml
OnboardingNextActionV1:
  action_code: ACKNOWLEDGE_BOUNDARIES|OPEN_MODEL_SETTINGS|OPEN_LIBRARY|SELECT_MATERIAL|OPEN_MATERIAL_LEARNING|CONTINUE_GOAL_SETUP|CONTINUE_DIAGNOSTIC|START_ACTIVITY|RESUME_ACTIVITY|COMPLETE_ACTIVITY|OPEN_TODAY|WAIT|RECOVER|NONE
  kind: command|navigate|wait|recover|none
  label: string
  enabled: boolean
  route: string|null
  resource_ref: string|null
  recovery_action: RecoveryActionV1|null
  reason_codes: [string]
```

```yaml
OnboardingJourneyViewV1:
  schema_version: "1.0"
  journey_id: first-learning-v1
  generated_at: datetime
  journey_state: ACTIVE|COMPLETE|BLOCKED|PARTIAL|STALE
  should_enter_welcome: boolean
  preference: OnboardingPreferenceV1
  boundary_notice:
    notice_version: string
    acknowledged: boolean
    data_control_route: string|null
    model_settings_route: string
  steps: [OnboardingStepViewV1]
  next_action: OnboardingNextActionV1
  correlation_id: string
```

```yaml
OnboardingPreferenceCommandV1:
  schema_version: "1.0"
  journey_id: first-learning-v1
  expected_preference_version: integer
  action: ACKNOWLEDGE_BOUNDARIES|DISMISS|REOPEN|FINISH_AND_DISMISS
  notice_version: string|null
  idempotency_key: string
```

#### ONBOARD-010 — API

- `GET /api/v1/onboarding/journey` 返回 current-user `OnboardingJourneyViewV1`；
- `POST /api/v1/onboarding/preferences` 执行 presentation command，并返回重新投影后的 journey；
- 两者 MUST `Cache-Control: private, no-store`；
- handler 只做 auth、strict validation、query/command、serialization 与 stable error mapping。

### 3. Preference Semantics

#### ONBOARD-020

`DISMISS`/`REOPEN`/`ACKNOWLEDGE_BOUNDARIES` 必须 optimistic-versioned、幂等；并发不同 payload 不能
last-write-wins。`FINISH_AND_DISMISS` MUST 在 command transaction/application boundary 重新读取
current completion；未 COMPLETE 返回 `ONBOARDING_COMPLETION_PRECONDITION_FAILED`。

#### ONBOARD-021

`visibility=DISMISSED` 只表示不自动进入 welcome，不表示 journey 或任一步完成。REOPEN 后所有步骤
必须按 current owner facts 重算。

### 4. Derived Step Semantics

#### ONBOARD-030 — Model

MODEL 只有在 P1-02 public summary 同时满足 `state=ACTIVE`、`runtime_ready=true`、非空
`verified_at`、`runtime_revision=revision` 时 COMPLETE。不得主动发 provider probe，也不得读取 Key。

#### ONBOARD-031 — Material

MATERIAL 只使用 SYS01 current-user current revision 与 Book Learning eligibility。pending/processing 为
IN_PROGRESS；failed/quarantined 为 BLOCKED；deleted/missing 为 NOT_STARTED 或 STALE。多个 eligible
资料且无 owner link 可唯一延续时，next action 必须为 SELECT_MATERIAL。

#### ONBOARD-032 — Goal

GOAL 只使用 SYS06 current confirmed/current Goal 与 canonical material mapping。draft、archived、
superseded、unconfirmed 或 source mapping unavailable 不算 COMPLETE。Onboarding 不创建或修改 Goal，
只导航既有 Book Learning command flow。

#### ONBOARD-033 — First activity completion

SYS06 MUST 提供只读 `FirstActivityCompletionProjectionV1`：

```yaml
user_ref: string
activity_ref: versioned_ref
state_ref: versioned_ref
status: completed
completed_at: datetime
completion_source_type: accepted_model_transcript
completion_source_ref: versioned_ref
```

只纳入符合 `ACTIVITY-*` completion transition 的 exact state；按 `completed_at ASC,
activity_id ASC` 稳定选择首个。不存在时为 MISSING。模型 inference、message、duration、plan readiness、
Attempt 或前端 click 不得替代该投影。

#### ONBOARD-034 — Single next action

服务端 MUST 返回恰好一个 `next_action`。选择优先级：boundary acknowledgment → first incomplete/
blocked step → completed journey OPEN_TODAY。跨多个候选对象没有唯一 owner link 时 MUST 返回选择页，
不得隐式挑选。UI MUST NOT 重排或覆盖该决定。

### 5. Entry Route and Deep Links

#### ONBOARD-040

`/welcome` MUST protected。只有用户 intended route 为 `/` 或 `/today`，且当前 response
`should_enter_welcome=true` 时 MAY replace 到 `/welcome`。任何其他 explicit route/deep link MUST
原样继续；onboarding query failure MUST NOT 把用户困在 welcome，也不得伪造 COMPLETE。

#### ONBOARD-041

`should_enter_welcome=true` 当且仅当 preference ACTIVE、boundary/四步尚未形成 COMPLETE journey，
且 query 没有阻止可信判断的关键 unauthorized/schema failure。Settings MUST 固定提供 REOPEN。

### 6. Backfill and Lifecycle

#### ONBOARD-050

additive migration MUST 在同一 transaction 将当时所有 existing users backfill 为 DISMISSED +
LEGACY_EXISTING_USER_BACKFILL。不得读取 legacy messages/events/localStorage 推断完成。迁移后首次查询
无 row 的用户创建 ACTIVE v1；并发创建使用 unique `(user_id, journey_id)` 返回同一记录。

#### ONBOARD-051

Preference 必须随 `ALL_PERSONAL_DATA` 删除；不得在恢复、projection rebuild 或换用户后泄漏。普通
PROFILE export MAY 输出非敏感 presentation preference，但不得包含领域 ref 或内部路径。

### 7. Errors and Recovery

至少冻结：

```text
ONBOARDING_SCHEMA_UNSUPPORTED
ONBOARDING_PREFERENCE_VERSION_CONFLICT
ONBOARDING_PREFERENCE_NOT_FOUND
ONBOARDING_COMPLETION_PRECONDITION_FAILED
ONBOARDING_DEPENDENCY_UNAVAILABLE
```

依赖错误 MUST 保留 owner stable code 与 P1-07 server-allowed `RecoveryActionV1`。UI 不根据自由文本或
HTTP status 生成恢复动作。partial/stale MAY 返回 200 view，但不得显示完整 READY。

### 8. Security and Privacy

- current-user scope；unauthorized 与 missing 不可枚举；
- response/log 不得含 Key/fragment、Prompt、grader-only、raw provider body、absolute path 或其他用户 ref；
- frontend/localStorage 不得持久化 journey/step truth；
- boundary 文案不得承诺“完全离线”或“绝对隐私”；
- v1 MUST NOT 创建、导入或自动选择样例资料。

### 9. Tests

必须覆盖 strict schema、source/version、single action、所有 step/partial/stale/error、completion 负面
推断、backfill/new user、SQLite/PostgreSQL migration、concurrent/idempotent preference、restart、
cross-user/cache/leakage、default route/deep links、dismiss/reopen、P1-07 recovery mapping、360px/200%
zoom/keyboard/live region、deterministic E2E、real-provider main path 与 App restart。

### 10. Acceptance Criteria

- `ONBOARD-AC-001`：四步 completion 全部来自 exact owner refs/versions，无 frontend inference。
- `ONBOARD-AC-002`：preference 只保存展示状态；dismissed 与 completed 可独立变化。
- `ONBOARD-AC-003`：first activity 只由 SYS06 accepted-transcript completion projection 证明。
- `ONBOARD-AC-004`：每个 response 只有一个确定性 next action；ambiguity 导航选择而非猜选。
- `ONBOARD-AC-005`：existing-user 不被强制 backfill，新用户 active，并发/重启无重复副作用。
- `ONBOARD-AC-006`：默认入口可进入 welcome，所有 explicit deep links 保留。
- `ONBOARD-AC-007`：错误恢复只使用 stable owner code/P1-07 action，无 secret/path/learner side effect。
- `ONBOARD-AC-008`：数据/模型说明准确链接真实 P1-02/P1-03 能力，v1 无假样例。
- `ONBOARD-AC-009`：自动、真实桌面/浏览器和无内部知识首次用户门禁有当前证据。

### 11. Forbidden Implementations

禁止 localStorage wizard truth；持久化 step completion；复制领域 ref 作为 onboarding truth；read handler
写 Goal/Activity；看到模型回复即完成；隐式挑选多个业务对象；全局 deep-link redirect；自由文本恢复；
自动样例/假目标/假进度；mock-only 宣称 P1-06 DONE；把产品路径可用宣称为真人学习效果。
