# Askora Error Contract

> Spec ID：`ERROR-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

ADR-0012 / P1-07 adds the recovery presentation fields below without changing
the meaning of existing stable codes.

## 1. 原则

### ERROR-001

错误必须区分：业务拒绝、输入无效、并发冲突、暂时基础设施失败、永久外部依赖失败、安全拒绝和内部不变量破坏。不得全部变成 HTTP 500 或自由文本异常。

### ERROR-002

错误对象必须可机器处理，至少包含：

```yaml
error:
  code: string
  category: validation|business|conflict|not_found|authorization|security|dependency|transient|internal
  message: string
  retryable: boolean
  correlation_id: string|null
  details: object|null
  recovery:
    issue_ref: string|null
    retry_after_seconds: integer|null
    actions: [RecoveryActionV1]
```

`request_id` MAY remain as an additive compatibility alias, but
`correlation_id` is canonical. API adapters MUST emit `category`, `retryable`
and `correlation_id` for every `AppError` and unhandled error.

## 2. 稳定错误码

错误码语义发布后不得改变。建议命名：

```text
CONTENT_UNSUPPORTED_TYPE
CONTENT_QUARANTINED
CONTENT_REINSPECTION_NOT_ALLOWED
CONTENT_REINSPECTION_POLICY_UNCHANGED
CONTENT_REINSPECTION_CHECKSUM_MISMATCH
CONTENT_REINSPECTION_UNAVAILABLE
RETRIEVAL_MISSING_EVIDENCE
RETRIEVAL_ACCESS_DENIED
ASSESS_ITEM_VERSION_MISMATCH
ASSESS_SCORING_UNAVAILABLE
LEARNER_EVIDENCE_INELIGIBLE
TEACH_NO_ELIGIBLE_ACTION
PLAN_NO_FEASIBLE_ACTIVITY
REVIEW_INVALID_OBSERVATION
AI_MODEL_UNAVAILABLE
AI_PROVIDER_TIMEOUT
AI_PROVIDER_RATE_LIMITED
AI_PROVIDER_KEY_INVALID
AI_PROVIDER_KEY_MISSING
AI_OUTPUT_VALIDATION_FAILED
MODEL_CONFIG_STORAGE_UNAVAILABLE
MODEL_CONFIG_SCHEMA_UNSUPPORTED
MODEL_CONFIG_REVISION_CONFLICT
MODEL_CREDENTIAL_REJECTED
MODEL_NOT_AVAILABLE
MODEL_RATE_LIMITED
MODEL_PROVIDER_TIMEOUT
MODEL_PROVIDER_UNAVAILABLE
MODEL_CONFIG_APPLY_FAILED
MODEL_CONFIG_ROLLBACK_FAILED
TOOL_NOT_AUTHORIZED
CONCURRENT_VERSION_CONFLICT
SCHEMA_VERSION_UNSUPPORTED
CONTENT_PROCESSING_FAILED
CONTENT_FILE_MISSING
CONTENT_OCR_REVIEW_REQUIRED
DATABASE_UNAVAILABLE
DATABASE_MIGRATION_REQUIRED
DATABASE_INTEGRITY_FAILED
OUTBOX_RETRY_WAITING
OUTBOX_RETRY_EXHAUSTED
OUTBOX_HANDLER_UNAVAILABLE
DATA_MODE_UNSUPPORTED
DATA_MAINTENANCE_BUSY
DATA_RECOVERY_KEY_REQUIRED
DATA_RECOVERY_KEY_INVALID
DATA_BACKUP_NOT_VERIFIED
DATA_BACKUP_INTEGRITY_FAILED
DATA_BACKUP_LIMIT_EXCEEDED
DATA_RESTORE_SCHEMA_UNSUPPORTED
DATA_RESTORE_RECONCILIATION_FAILED
DATA_RESTORE_FAILED_ROLLED_BACK
DATA_EXPORT_SCOPE_INVALID
DATA_EXPORT_EXPIRED
DATA_ERASURE_PREVIEW_EXPIRED
DATA_ERASURE_CONFIRMATION_INVALID
DATA_ERASURE_PARTIAL
MESSAGE_NOT_FOUND
MESSAGE_REVISION_CONFLICT
MESSAGE_BLOCK_NOT_FOUND
MESSAGE_CAPABILITY_NOT_FOUND
MESSAGE_CAPABILITY_UNAVAILABLE
MESSAGE_CAPABILITY_STALE
MESSAGE_CONTEXT_SCOPE_VIOLATION
MESSAGE_SCHEMA_UNSUPPORTED
MESSAGE_INTERACTION_INVALID
```

上述 recovery 错误的 category、retryability、data safety、retry budget 与允许动作由
`recovery-contract.md` 的单一目录冻结。Provider adapter MUST 根据 typed exception/HTTP status
分类，不得把 provider message 文本作为主分支。

`MESSAGE_*` 是 ADR-0020 / `LCMS-*` façade boundary errors。Target owner 的 assessment/activity/policy/source error code MUST 原样保留；Message adapter 不得把它们改写成自由文本或 learner failure。重复 idempotency key 返回原 receipt/result，不产生第二 side effect。

P1-03 data-control errors 的 category/retryability 由 `data-control-contract.md` 冻结：wrong key、unsafe package、future schema 与 invalid confirmation non-retryable；maintenance busy、temporary storage 与未完成 owner step MAY retryable。任何 error details 不得包含 key、内容原文或完整本地路径。

## 3. Retry

### ERROR-010

只有 `retryable=true` 的 transient/dependency error MAY 自动重试。业务校验、安全拒绝、版本冲突不得盲重试同一输入。

### ERROR-011

自动 retry 必须有上限、退避、trace，并对副作用操作保证幂等。

### ERROR-012

`retryable=true` 只表示该错误类别允许重试，不表示现在立即重试。若存在 rate limit、lease、
backoff 或预算，响应 MUST 同时给出 `next_eligible_at/retry_after` 与剩余预算。预算耗尽后同一
run/task 不得继续自动重试。

### ERROR-013

Manual recovery MUST append audit and create an owner-approved replacement task/run when replay is
safe. It MUST NOT erase or reset the original dead-letter/exhausted history.

## 4. Domain vs Transport

### ERROR-020

领域错误不能依赖 HTTP status。API adapter 负责映射：

- validation → 400/422；
- auth → 401/403；
- not found → 404；
- conflict/version → 409；
- dependency unavailable → 502/503；
- rate/temporary → 429/503；
- invariant/internal → 500。

具体 transport status 可调整，但领域 code 必须稳定。

## 5. 学习语义错误

### ERROR-030

基础设施/模型/工具故障不得记录成“学习者答错”“学习者忘记”或其他负向学习 evidence。

### ERROR-031

检索证据不足应返回 `RETRIEVAL_MISSING_EVIDENCE` 或等价结构化结果，不得伪造资料答案。

### ERROR-032

评分器不可用时 Attempt 可进入 `scoring_failed/needs_review`，不得自动记 0 分。

## 6. Security

安全拒绝默认 `retryable=false`；对用户返回的信息不得泄露敏感规则、密钥、内部路径或可被利用的检测细节。

`CONTENT_REINSPECTION_POLICY_UNCHANGED` 与 `CONTENT_REINSPECTION_NOT_ALLOWED` 是 non-retryable
business/conflict；`CONTENT_REINSPECTION_CHECKSUM_MISMATCH` 是 non-retryable integrity conflict。
它们不得进入普通 processing 自动 retry。复检任务内部仅允许 transient storage/database failure
按固定预算重试，耗尽后返回 `CONTENT_REINSPECTION_UNAVAILABLE` 并保持隔离。

## 7. Logging

错误日志必须带 correlation/trace id、error code 和必要上下文；不得把原始密钥、密码、完整敏感 Prompt 写入日志。

### ERROR-040 — Model Configuration Retry Semantics

`MODEL_CREDENTIAL_REJECTED`、`MODEL_NOT_AVAILABLE`、`MODEL_CONFIG_SCHEMA_UNSUPPORTED` 与
`MODEL_CONFIG_REVISION_CONFLICT` 默认 non-retryable；必须修改输入或刷新 revision。
`MODEL_RATE_LIMITED`、`MODEL_PROVIDER_TIMEOUT`、`MODEL_PROVIDER_UNAVAILABLE` MAY retry，UI 必须保留候选输入且不得声称已保存。
`MODEL_CONFIG_APPLY_FAILED` 表示新配置未激活且已恢复旧 revision；只有实际无法恢复旧 revision 时使用
`MODEL_CONFIG_ROLLBACK_FAILED`，该错误 non-retryable 且必须明确当前状态未知/不可用。

## 8. Acceptance Criteria

- `ERROR-AC-001`：模型超时与用户答错在数据层完全不同。
- `ERROR-AC-002`：同一稳定领域错误在 HTTP/WS/streaming 都保留同一 error code。
- `ERROR-AC-003`：非 retryable 业务错误不会进入自动重试循环。
- `ERROR-AC-004`：副作用 retry 不产生重复操作。
- `ERROR-AC-005`：全部 HTTP application/unhandled errors 实现完整 `ERROR-002` envelope。
- `ERROR-AC-006`：provider timeout/rate/key/model/output errors 使用稳定 code 且不依赖自由文本。
- `ERROR-AC-007`：credential/model/rate-limit/timeout/provider/apply/rollback 错误可机器区分。
- `ERROR-AC-008`：任何 model configuration 错误 payload 与日志不含 credential/ciphertext/token/provider raw body。

## 9. Forbidden Implementations

禁止：

- `except Exception: return None` 吞掉关键失败；
- 所有异常统一 retry；
- 模型超时给 AssessmentResult 记失败；
- 依赖自由文本判断错误类型；
- 把 stack trace/密钥直接返回前端。

## 10. P1-06 Onboarding Errors

### ERROR-100

Onboarding stable codes 至少包括：

```text
ONBOARDING_SCHEMA_UNSUPPORTED
ONBOARDING_PREFERENCE_VERSION_CONFLICT
ONBOARDING_PREFERENCE_NOT_FOUND
ONBOARDING_COMPLETION_PRECONDITION_FAILED
ONBOARDING_DEPENDENCY_UNAVAILABLE
```

依赖 owner error MUST 保留原 stable code 和服务端允许的 P1-07 recovery action。partial/stale source 可
返回 read view，但不得映射为 READY；provider/document/activity failure 不得写 learner negative evidence。

## 11. P1-01 Goal Errors

Stable codes：`GOAL_VERSION_CONFLICT`、`GOAL_PREVIEW_STALE`、`GOAL_SOURCE_NOT_EXECUTABLE`、
`GOAL_TARGET_CONFIRMATION_REQUIRED`、`GOAL_CRITERION_UNMEASURABLE`、
`GOAL_WAITING_ACTIVITY_BOUNDARY`、`GOAL_REPLAN_REQUIRED`、`GOAL_EVIDENCE_INSUFFICIENT`、
`GOAL_MEASUREMENT_UNAVAILABLE`。冲突/门禁失败不得终止当前活动或写 learner failure。
