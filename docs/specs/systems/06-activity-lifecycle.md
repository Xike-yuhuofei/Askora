# SYS06 Activity Lifecycle and Completion

> Spec ID：`SYS06-ACT-*`
> 状态：Canonical Implementation Contract / Frozen
> 版本：v1.0
> 冻结日期：2026-08-09
> Governing decision：ADR-0007

## 1. Ownership and Meaning

`LearningActivityStateV1` 是 SYS06-owned current lifecycle truth。它只回答计划任务的可用、执行和完成状态，不回答 learner mastery、assessment correctness、objective satisfaction 或 goal achievement。

`LearningActivity` definition immutable；payload status 是 initial/legacy snapshot。cutover 后所有 current-state query、Today、Path 与 execution guard MUST 读取 latest lifecycle state。

## 2. State Contract

```yaml
learning_activity_state_v1:
  schema_version: "1.0"
  activity_id: uuid
  version: integer >= 1
  plan_id: uuid
  plan_version: integer >= 1
  status: planned|available|active|completed|skipped|superseded
  previous_status: planned|available|active|completed|skipped|superseded|null
  transition_reason: string
  source_refs: [versioned_ref]
  actor_type: system|learner
  started_at: datetime|null
  completed_at: datetime|null
  correlation_id: uuid
  created_at: datetime
```

唯一约束为 `(activity_id, version)`；version 单调递增。state row、SYS06 event 与 outbox MUST 同事务提交。

## 3. Transitions

允许：

```text
planned → available        SelectNextLearningActivity
available → active         StartLearningActivityV1
active → completed         CompleteLearningActivityV1
planned/available → skipped
planned/available/active → superseded
```

禁止 completed 回退；需要再次学习时由 replan 创建新 activity。superseded plan 下的 activity 不得 start/complete。

### SYS06-ACT-010 — Availability

只有 SYS06 可根据 immutable plan order、前置约束与当前状态把 activity 置为 available。选择不得重排 `LearningPlan.activity_ids`。

### SYS06-ACT-011 — Start

`StartLearningActivityV1` 仅接受 current `available`，必须校验 owner chain、current plan、expected state version、idempotency 与 execution capability。成功产生 `ActivityStarted`，重复相同 command 返回原结果。

### SYS06-ACT-012 — Completion

`CompleteLearningActivityV1` 仅接受 current `active`。UI-02C v1 的 `learner_finished` 只适用于 transcript-backed `learn_new|prerequisite_remediation|practice|metacognitive_review`，且必须引用至少一个 current-user accepted transcript turn。

`diagnostic|delayed_review|transfer_check` 返回 `ACTIVITY_COMPLETION_EVIDENCE_REQUIRED`，直到对应 evaluator/review contract 冻结。completion 不写 SYS03/SYS04/SYS05/SYS07 state。

### SYS06-ACT-013 — Progression

completion 与 next eligible activity `planned → available` 必须原子提交。不存在下一非终态 activity 时，SYS06 MAY 将 plan 置为 completed；goal 保持原状态，除非独立 goal-achievement command 已冻结。

## 4. Commands

```yaml
start_learning_activity_v1:
  schema_version: "1.0"
  activity_id: uuid
  expected_state_version: integer >= 1
  idempotency_key: string

complete_learning_activity_v1:
  schema_version: "1.0"
  activity_id: uuid
  expected_state_version: integer >= 1
  completion_intent: learner_finished
  transcript_turn_refs: [versioned_ref]
  idempotency_key: string
```

客户端不得提交 target status、next activity、mastery、objective/goal status、plan order 或 evidence score。

## 5. Events

`ActivityAvailable`、`ActivityStarted`、`ActivityCompleted` 使用现有 `LearningEventEnvelope`，payload 至少包含 activity/plan/goal refs、previous/new status、lifecycle version、reason、source refs；event provenance owner 为 SYS06。aggregate version 使用 lifecycle version，不复用 plan version。

## 6. API and Query

- `POST /api/v1/workspace/activities/{activity_id}/start`
- `POST /api/v1/workspace/activities/{activity_id}/complete`
- `GET /api/v1/workspace/activities/{activity_id}`

写响应返回 strict v1 state、next activity ref/plan status 与 correlation id；query 返回 execution capability 与 stable `/learn/{activity_id}` product route，但不得把 route/session 当作 lifecycle truth。所有资源 current-user scoped，未授权与不存在不可枚举，read response `private, no-store`。

## 7. Stable Errors

```text
ACTIVITY_NOT_AVAILABLE
ACTIVITY_NOT_ACTIVE
ACTIVITY_STALE_OR_SUPERSEDED
ACTIVITY_COMPLETION_EVIDENCE_REQUIRED
ACTIVITY_EXECUTION_UNAVAILABLE
ACTIVITY_STATE_VERSION_CONFLICT
ACTIVITY_IDEMPOTENCY_CONFLICT
LEGACY_ACTIVITY_STATE_UNMIGRATED
```

provider/transcript persistence failure不得映射成 learner failure 或 completion。version/idempotency/business errors non-retryable；transient DB/outbox failure可 bounded retry。

## 8. Migration and Compatibility

按 ADR-0007 backfill。所有新 plan 创建时原子创建 lifecycle v1。迁移完成后 active readers 不再以 payload status、event recency 或 transcript presence 推断 current state；legacy fallback 必须显式 reason 且有删除 gate。

## 9. Security and Privacy

completion source refs 必须属于同一 current user/activity；不复制 transcript正文、Prompt、grader answer 或 secret。外部模型无 lifecycle command 权限。

## 10. Acceptance Criteria

- `SYS06-ACT-AC-001`：latest version 是唯一 current truth，payload/transcript/UI 不形成第二 writer。
- `SYS06-ACT-AC-002`：允许转换、禁止转换、expected version 与 duplicate idempotency 可机器验证。
- `SYS06-ACT-AC-003`：start/complete/next availability/outbox 原子、可重启恢复。
- `SYS06-ACT-AC-004`：completion 不写 mastery/assessment/policy/review，不自动 achieved/satisfied。
- `SYS06-ACT-AC-005`：evaluator-required activity fail closed；provider failure不形成 completion/evidence。
- `SYS06-ACT-AC-006`：SQLite/PostgreSQL migration、backfill、reconciliation 与 forward-fix 有测试。
- `SYS06-ACT-AC-007`：cross-user、stale plan、superseded activity 与 source-ref ownership 不泄漏。

## 11. First Activity Completion Projection

### SYS06-ACT-080

SYS06 MUST 提供 current-user scoped `FirstActivityCompletionProjectionV1` 只读 query：只纳入 canonical
latest `status=completed` 且 completion transition 已验证 accepted transcript source 的 activity；按
`completed_at ASC, activity_id ASC` 稳定选择首个。

该 projection MUST 返回 exact activity/state/completion source refs，不复制 transcript 正文；不存在时
返回 MISSING。它不新增 lifecycle writer，也不得以 inference/message/duration/plan ready/Attempt/UI click
补齐。

### SYS06-ACT-AC-008

相同 owner state 重查必须返回相同 first completion；删除/supersede/unauthorized/stale source 时不得保留
onboarding 缓存完成状态。
