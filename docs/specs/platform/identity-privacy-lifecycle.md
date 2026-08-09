# Askora Platform Identity and Privacy Lifecycle Specification

> Spec ID：`IDP-*`
> 状态：FROZEN
> 版本：v1.0
> Governing decision：ADR-0009

## 1. Scope and Ownership

### IDP-001 — Platform Boundary

Identity & Privacy 是平台横切边界，不是第九学习系统。它 MUST NOT 写入 KnowledgeUnit、EvidenceBundle、LearnerState、AssessmentResult、TeachingAction、LearningPlan/Activity、ReviewSchedule 或 Workflow/ModelExecution 的普通业务 truth。

### IDP-002 — Identity-owned State

Identity 是以下状态的唯一 writer：

```text
User credential_version / password_changed_at / account lifecycle
AuthSession / token family / refresh generation
RecoveryCredential / recovery throttling
```

### IDP-003 — Privacy-owned State

Privacy Coordinator 是以下治理记录的唯一 writer：

```text
DeletionPreview
AccountDeletionRequest
PrivacySubjectManifest / blocking issue
OwnerErasureStepReceipt
PrivacyTombstone / RestoreBarrier
```

它 MUST 通过 owner erasure port 清除学习数据，MUST NOT 通过普通 shared ORM session 任意 patch 八系统状态。

## 2. Password Policy

### IDP-010

`password-policy-v2` 对新注册、修改和恢复后的密码要求：15～128 Unicode code points；接受空格和 Unicode；不要求字符种类组合；不得截断。密码与当前密码相同 MUST 拒绝。

### IDP-011

新 hash MUST 使用 Argon2id 并记录 scheme/parameters。历史 bcrypt hash MAY 读取；成功认证时若 `needs_rehash` MUST 在同一 identity transaction 更新为 Argon2id。任何日志/事件 MUST NOT 保存密码或 hash。

### IDP-012 — Change Password

`ChangePasswordV1` 输入至少包含 current password、new password、idempotency key、current session version。成功 MUST：

1. 验证 current password 与 account ACTIVE；
2. 写新 hash、`credential_version + 1`、`password_changed_at`；
3. 撤销其他 sessions；
4. 轮换当前 token family 并返回新 tokens/session version；
5. 重复幂等键返回原/等价结果，不重复递增 version。

## 3. Durable Auth Session

### IDP-020 — AuthSessionV1

```yaml
auth_session:
  session_id: uuid
  user_id: uuid
  version: integer
  token_family_id: uuid
  current_refresh_jti_digest: string
  client_instance_digest: string|null
  client_label: string
  credential_version: integer
  created_at: datetime
  last_seen_at: datetime
  refresh_expires_at: datetime
  revoked_at: datetime|null
  revoke_reason: string|null
```

客户端 label 是展示信息，不是认证因子；MUST 限长和转义。原始 fingerprint、IP 或完整 user-agent MUST NOT 作为默认持久化数据。

### IDP-021 — Token Binding

access/refresh token MUST 包含 `sid`、`fam`、`cv`、`jti`、`type`、`iat`、`exp`、`iss`。受保护请求 MUST 验证 exact active session、family 与 credential version。Redis MAY cache，但数据库是唯一 truth。

### IDP-022 — Refresh Rotation and Replay

refresh 必须在一个 database transaction 内 compare current JTI digest → consume → write next digest/version。旧/并发 refresh 再次出现 MUST 将 session 标记 revoked/replay，且不得发新 token。

### IDP-023 — Session Commands

必须提供 current-user scoped：list sessions、revoke one、revoke others、logout current。未授权/不存在不可枚举。撤销当前 session 后 access/refresh 立即不可用。

### IDP-024 — Session Limit

session limit 只统计 durable active、未过期 sessions。达到上限返回稳定 conflict，并提供 session-management recovery action；Redis 不可用不得跳过限制或放行 revoked session。

## 4. Recovery Credential

### IDP-030 — Recovery Kit

Recovery secret MUST 由 CSPRNG 生成，至少 128 bits entropy；只在 issuance/rotation/successful recovery response 展示一次。数据库只保存 keyed digest、created/used/revoked timestamps 和 throttling metadata。

### IDP-031 — Registration and Existing Accounts

新注册 MUST 原子创建首份 recovery credential，并返回一次性 recovery kit。既有账号在设置中通过 current password 创建/轮换；创建新 credential MUST 撤销旧 credential。

### IDP-032 — Recover Password

`RecoverPasswordV1` 输入 phone、recovery secret、new password、client instance 与 idempotency key。无论 phone 是否存在，都 MUST 执行近似同成本验证并使用不枚举文案。成功 MUST：

- consume 当前 recovery credential；
- 设置符合 `password-policy-v2` 的新 hash并递增 credential version；
- revoke all sessions；
- 生成并只返回一次新 recovery kit；
- 要求用户重新登录。

### IDP-033 — Throttling

登录、current-password、recovery 与 deletion confirmation 的失败尝试 MUST server-side bounded throttling。首版策略固定到 `identity-security-policy-v1`：每账号/动作连续 5 次失败后 15 分钟冷却；成功验证清零。未知账号使用不可反查的 identifier digest 和相同 throttle path。

## 5. Deletion Commands and Lifecycle

### IDP-040 — Product Semantics

UI/API MUST 分开：

```text
LogoutCurrentSession
RevokeAuthSession
DeleteAllLearningDataV1
DeleteAccountV1
```

退出/撤销 session MUST NOT 删除学习数据。`DeleteAllLearningDataV1` MUST NOT 删除账号 credential。`DeleteAccountV1` MUST 包含全量用户数据清除和最终 identity 去标识化。

### IDP-041 — Preview

Deletion preview MUST strict/versioned/current-user/no-store，至少返回：

```yaml
preview_id: uuid
schema_version: "1.0"
policy_version: "account-deletion-v1"
generated_at: datetime
expires_at: datetime
counts_by_owner: object
file_count: integer
pending_task_count: integer
projection_count: integer
blocking_issues: [object]
explicit_exclusions: [string]
recovery_boundary: string
preview_digest: string
```

preview 有 blocking issue 时 MUST NOT 接受删除请求。

### IDP-042 — Request

`DeleteAccountV1` MUST 要求 current password、精确确认短语 `永久删除我的 Askora 账号`、preview id/digest、policy version 和 idempotency key。preview stale/expired 或数据版本变化返回 conflict，不得静默扩大/缩小范围。

### IDP-043 — Lifecycle

允许转换仅：

```text
ACTIVE → DELETION_PENDING
DELETION_PENDING → ACTIVE (cancel)
DELETION_PENDING → PURGING (due)
PURGING → DELETED
PURGING → DELETION_BLOCKED
DELETION_BLOCKED → PURGING (explicit retry)
```

默认 grace 为 `account-deletion-v1/grace=24h`，服务端时钟决定。进入 pending 必须 revoke all ordinary sessions，issue 单用途 deletion-control token；token 只能 query/cancel deletion。

### IDP-044 — Cancel

只有 pending 且未到 purging 的 request 可取消。取消后账号回 ACTIVE，但所有旧 session 保持 revoked，用户必须重新登录。重复 cancel 幂等。

## 6. Subject Manifest and Erasure

### IDP-050 — Manifest

manifest MUST 由 explicit registry 基于 direct `user_id`、`pseudonym_id`、owner reference 与结构化 JSON reference 构造。每个 entry 包含 owner、record type/id、storage class 与 deletion order。单用户部署事实不是 ownership 证据。

### IDP-051 — Ambiguity

记录同时关联其他 user、无法解析 subject 或超出 registry 时必须创建 blocking issue。MUST NOT 猜测、跳过后仍报告完成或删除其他用户数据。

### IDP-052 — Owner Erasure

每个 owner handler MUST：只接受 frozen manifest；幂等删除自己的 rows/files/projections；取消能重建数据的 pending task；返回 requested/deleted/missing/error counts 与 digest。普通业务 repository 不获得跨 owner delete 权限。

### IDP-053 — Immutable Records

`EVENT-071` 隐私删除 MAY 物理删除受保护 immutable ledger。实现必须使用 privacy-only repository/Core path并要求 manifest + deletion request；普通 update/delete listener 继续 fail closed。

### IDP-054 — Reconciliation

所有 owner steps 完成后 MUST 重新 inventory。数据库 records、文件、pending task、cache/projection 对目标 subject 均为零才可完成。bounded retry 耗尽进入 `DELETION_BLOCKED`，账号保持不可用。

### IDP-055 — Tombstone

tombstone MAY 保存 request id、policy/schema version、时间、scope/receipt digests、最终状态与不可逆边界；MUST NOT 保存 phone/email/nickname/password/hash/recovery secret、原始 user content、Prompt/model output 或可逆身份。

### IDP-056 — Restore Barrier

完成删除 MUST 原子/可恢复写数据库外 restore barrier。认证与 startup recovery 在普通业务启动前检查；App 管理的旧 snapshot 命中 barrier 时 MUST fail closed 并重新执行清除，MUST NOT 恢复 ACTIVE 登录。

## 7. API / Error / Observability

### IDP-060

公共 request/response 使用 `extra=forbid`、strict v1、unknown major reject。写命令必须 current-user 或 single-purpose deletion-control scoped，并传播 correlation/idempotency。

### IDP-061 — Stable Errors

至少冻结：

```text
AUTH_CURRENT_PASSWORD_INVALID
AUTH_PASSWORD_POLICY_REJECTED
AUTH_SESSION_REQUIRED
AUTH_SESSION_NOT_FOUND
AUTH_SESSION_REVOKED
AUTH_REFRESH_REPLAY_DETECTED
AUTH_RECOVERY_INVALID
AUTH_RECOVERY_RATE_LIMITED
ACCOUNT_DELETION_PREVIEW_STALE
ACCOUNT_DELETION_CONFIRMATION_INVALID
ACCOUNT_DELETION_IN_PROGRESS
ACCOUNT_DELETION_NOT_CANCELLABLE
ACCOUNT_DELETION_BLOCKED
PRIVACY_SUBJECT_AMBIGUOUS
PRIVACY_RECONCILIATION_FAILED
PRIVACY_RESTORE_BLOCKED
```

### IDP-062

日志只保存 stable code、request/session/deletion id 的最小必要片段和 count/digest；MUST NOT 保存 password、recovery/deletion token、phone、原始文件名/content 或删除数据正文。

## 8. UI Contract

### IDP-070

`/settings` 必须提供账号安全、恢复套件状态、设备/会话和危险操作四个明确区域。当前 session 有明确标记；撤销动作有 loading/result/error；不得把 app-instance label 宣称为可信硬件身份。

### IDP-071

Login 必须支持登录、注册和“使用恢复套件重设密码”。注册/恢复产生的新 recovery kit 必须要求用户确认已保存后才离开结果视图；不得自动写入普通 localStorage/user cache。

### IDP-072

删除账号至少两阶段：preview → re-auth/typed confirmation。pending 页面显示执行时间、可取消边界和“关闭本地 App 会延迟本地清除，重启后继续”；purging 后不得显示取消。

### IDP-073

360px、200% zoom、keyboard、focus、live status/error、reduced motion 与 destructive confirmation 都必须可访问。

## 9. Acceptance Criteria

- `IDP-AC-001`：password change 后旧 session/refresh 不可用，当前 session 使用新 family。
- `IDP-AC-002`：Redis 丢失/重启不恢复 revoked session，session limit 仍正确。
- `IDP-AC-003`：refresh replay revoke family，concurrent refresh 最多一个成功。
- `IDP-AC-004`：recovery secret 明文不持久化、单次使用、限流且不枚举账号。
- `IDP-AC-005`：四类用户动作的数据/身份/会话语义无混淆。
- `IDP-AC-006`：cross-user session/deletion request 不可枚举。
- `IDP-AC-007`：duplicate/stale deletion command 不产生重复删除或范围漂移。
- `IDP-AC-008`：restart 后 pending/purging 从 durable step 恢复。
- `IDP-AC-009`：representative all-owner fixture 删除后 DB/files/tasks/projections 零残留，其他用户/全局 policy 不受影响。
- `IDP-AC-010`：tombstone/log 无 PII/content/secret。
- `IDP-AC-011`：旧 snapshot 命中 restore barrier 时不能登录或继续处理旧数据。
- `IDP-AC-012`：真实 UI 完成 change password、session revoke、recovery 和 delete lifecycle，且错误可恢复。

## 10. Forbidden Implementations

禁止：Redis/renderer state 作为 session truth；logout 只删前端 token；recovery 明文落库；安全问题；按单用户假设删除 unscoped ledger；直接 cascade User 并声称全部删除；删除失败后恢复 ACTIVE；pending outbox 重建已删数据；普通 immutable delete 开洞；tombstone 保存 PII/content；旧备份静默复活；用 UI/test pass 声称学习效果。
