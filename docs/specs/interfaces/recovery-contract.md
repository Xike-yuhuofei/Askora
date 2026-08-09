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
  action_code: retry_owner_command|reinspect_document|open_model_settings|open_data_recovery|open_activity|reselect_file|wait_until|copy_diagnostics|acknowledge
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
