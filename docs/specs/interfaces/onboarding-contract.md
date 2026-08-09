# Askora First-use Onboarding Contract

> Spec ID：`ONBOARD-*`
> 状态：FROZEN
> 版本：v1.0
> Governing decision：ADR-0106

## 1. Boundary and Ownership

### ONBOARD-001 — Read projection, not workflow owner

Onboarding MUST 只组合 Platform Experience Preference、P1-02、SYS01、SYS06、SYS08、P1-03 与
P1-07 已发布的 query/action。它不得创建第二 model/document/goal/plan/activity/transcript/recovery
truth，也不得直接调用领域 repository 修改业务状态。

### ONBOARD-002 — Presentation preference owner

Platform Experience Preference MUST 是 `OnboardingPreferenceV1` 唯一 writer。该对象只控制展示，
不得包含 step completion、document/goal/plan/activity/transcript ref 或 secret。

## 2. Strict Public Contracts

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

### ONBOARD-010 — API

- `GET /api/v1/onboarding/journey` 返回 current-user `OnboardingJourneyViewV1`；
- `POST /api/v1/onboarding/preferences` 执行 presentation command，并返回重新投影后的 journey；
- 两者 MUST `Cache-Control: private, no-store`；
- handler 只做 auth、strict validation、query/command、serialization 与 stable error mapping。

## 3. Preference Semantics

### ONBOARD-020

`DISMISS`/`REOPEN`/`ACKNOWLEDGE_BOUNDARIES` 必须 optimistic-versioned、幂等；并发不同 payload 不能
last-write-wins。`FINISH_AND_DISMISS` MUST 在 command transaction/application boundary 重新读取
current completion；未 COMPLETE 返回 `ONBOARDING_COMPLETION_PRECONDITION_FAILED`。

### ONBOARD-021

`visibility=DISMISSED` 只表示不自动进入 welcome，不表示 journey 或任一步完成。REOPEN 后所有步骤
必须按 current owner facts 重算。

## 4. Derived Step Semantics

### ONBOARD-030 — Model

MODEL 只有在 P1-02 public summary 同时满足 `state=ACTIVE`、`runtime_ready=true`、非空
`verified_at`、`runtime_revision=revision` 时 COMPLETE。不得主动发 provider probe，也不得读取 Key。

### ONBOARD-031 — Material

MATERIAL 只使用 SYS01 current-user current revision 与 Book Learning eligibility。pending/processing 为
IN_PROGRESS；failed/quarantined 为 BLOCKED；deleted/missing 为 NOT_STARTED 或 STALE。多个 eligible
资料且无 owner link 可唯一延续时，next action 必须为 SELECT_MATERIAL。

### ONBOARD-032 — Goal

GOAL 只使用 SYS06 current confirmed/current Goal 与 canonical material mapping。draft、archived、
superseded、unconfirmed 或 source mapping unavailable 不算 COMPLETE。Onboarding 不创建或修改 Goal，
只导航既有 Book Learning command flow。

### ONBOARD-033 — First activity completion

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

### ONBOARD-034 — Single next action

服务端 MUST 返回恰好一个 `next_action`。选择优先级：boundary acknowledgment → first incomplete/
blocked step → completed journey OPEN_TODAY。跨多个候选对象没有唯一 owner link 时 MUST 返回选择页，
不得隐式挑选。UI MUST NOT 重排或覆盖该决定。

## 5. Entry Route and Deep Links

### ONBOARD-040

`/welcome` MUST protected。只有用户 intended route 为 `/` 或 `/today`，且当前 response
`should_enter_welcome=true` 时 MAY replace 到 `/welcome`。任何其他 explicit route/deep link MUST
原样继续；onboarding query failure MUST NOT 把用户困在 welcome，也不得伪造 COMPLETE。

### ONBOARD-041

`should_enter_welcome=true` 当且仅当 preference ACTIVE、boundary/四步尚未形成 COMPLETE journey，
且 query 没有阻止可信判断的关键 unauthorized/schema failure。Settings MUST 固定提供 REOPEN。

## 6. Backfill and Lifecycle

### ONBOARD-050

additive migration MUST 在同一 transaction 将当时所有 existing users backfill 为 DISMISSED +
LEGACY_EXISTING_USER_BACKFILL。不得读取 legacy messages/events/localStorage 推断完成。迁移后首次查询
无 row 的用户创建 ACTIVE v1；并发创建使用 unique `(user_id, journey_id)` 返回同一记录。

### ONBOARD-051

Preference 必须随 `ALL_PERSONAL_DATA` 删除；不得在恢复、projection rebuild 或换用户后泄漏。普通
PROFILE export MAY 输出非敏感 presentation preference，但不得包含领域 ref 或内部路径。

## 7. Errors and Recovery

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

## 8. Security and Privacy

- current-user scope；unauthorized 与 missing 不可枚举；
- response/log 不得含 Key/fragment、Prompt、grader-only、raw provider body、absolute path 或其他用户 ref；
- frontend/localStorage 不得持久化 journey/step truth；
- boundary 文案不得承诺“完全离线”或“绝对隐私”；
- v1 MUST NOT 创建、导入或自动选择样例资料。

## 9. Tests

必须覆盖 strict schema、source/version、single action、所有 step/partial/stale/error、completion 负面
推断、backfill/new user、SQLite/PostgreSQL migration、concurrent/idempotent preference、restart、
cross-user/cache/leakage、default route/deep links、dismiss/reopen、P1-07 recovery mapping、360px/200%
zoom/keyboard/live region、deterministic E2E、real-provider main path 与 App restart。

## 10. Acceptance Criteria

- `ONBOARD-AC-001`：四步 completion 全部来自 exact owner refs/versions，无 frontend inference。
- `ONBOARD-AC-002`：preference 只保存展示状态；dismissed 与 completed 可独立变化。
- `ONBOARD-AC-003`：first activity 只由 SYS06 accepted-transcript completion projection 证明。
- `ONBOARD-AC-004`：每个 response 只有一个确定性 next action；ambiguity 导航选择而非猜选。
- `ONBOARD-AC-005`：existing-user 不被强制 backfill，新用户 active，并发/重启无重复副作用。
- `ONBOARD-AC-006`：默认入口可进入 welcome，所有 explicit deep links 保留。
- `ONBOARD-AC-007`：错误恢复只使用 stable owner code/P1-07 action，无 secret/path/learner side effect。
- `ONBOARD-AC-008`：数据/模型说明准确链接真实 P1-02/P1-03 能力，v1 无假样例。
- `ONBOARD-AC-009`：自动、真实桌面/浏览器和无内部知识首次用户门禁有当前证据。

## 11. Forbidden Implementations

禁止 localStorage wizard truth；持久化 step completion；复制领域 ref 作为 onboarding truth；read handler
写 Goal/Activity；看到模型回复即完成；隐式挑选多个业务对象；全局 deep-link redirect；自由文本恢复；
自动样例/假目标/假进度；mock-only 宣称 P1-06 DONE；把产品路径可用宣称为真人学习效果。
