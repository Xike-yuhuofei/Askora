# Askora Data Control and Recovery Contract

> Spec ID：`DATA-*`
> 状态：FROZEN
> 版本：1.0
> Owner boundary：Infrastructure control artifacts + owner-coordinated commands；不建立第九个业务 owner
> Governing decision：ADR-0103

## 1. Scope

### DATA-001 — Supported Product Mode

P1-03 v1 MUST 支持 macOS 私人桌面 SQLite。服务模式/PostgreSQL MUST 明确返回 unsupported adapter，MUST NOT 使用 SQLite 文件逻辑或在 UI 显示已受保护。

### DATA-002 — Capability Separation

以下是四个独立合同：

```text
Recovery Package  = encrypted lossless Askora restore input
User Data Export  = readable current-user portability artifact
Erasure Workflow  = owner-coordinated destructive command
Recovery Report   = non-sensitive verification/control evidence
```

User Data Export MUST NOT 被直接导入为 canonical state；Recovery Package MUST NOT 被描述为人类可读导出。

## 2. Recovery Key

### DATA-010

首次启用数据保护时 MUST 创建至少 256-bit 独立随机 Recovery Key。设备保存副本 MUST 通过 platform secure storage 封装；明文 key MUST NOT 写入恢复包、catalog、日志、命令行参数、localStorage 或普通导出。

### DATA-011

用户 MUST 能显式查看/保存 recovery key，并被告知丢失 key 时跨设备恢复不可行。同设备自动备份 MAY 使用 platform-unwrapped key；跨设备恢复 MUST 要求用户提供 key。

## 3. Recovery Package V1

### DATA-020 — Container

`askora-recovery/1.0` MUST 使用分块 authenticated encryption。每个 chunk 使用唯一 nonce；header/version 作为 authenticated data。任何 chunk tamper、truncation、reorder、unknown major 或错误 key MUST 在解压/激活前失败。

### DATA-021 — Manifest

解密后的 package MUST 包含 `manifest.json`：

```yaml
format: askora-recovery
schema_version: "1.0"
backup_id: uuid
backup_set_id: uuid
reason: MANUAL|SCHEDULED|PRE_MIGRATION|PRE_RESTORE|POST_ERASURE
created_at: datetime
app_version: string
database_kind: sqlite
database_schema_revision: string|null
database_sha256: string
erasure_checkpoint: integer
files:
  - relative_path: string
    size_bytes: integer
    sha256: string
secrets_schema_version: "1.0"
totals:
  file_count: integer
  size_bytes: integer
```

Manifest path MUST normalized relative path；absolute、`..`、empty segment、duplicate、symlink 与 special file MUST reject。

### DATA-022 — Included Data

MUST 包含 consistent SQLite snapshot、受管 raw document assets、当前 erasure checkpoint 与恢复数据库加密字段所需 KEK material。MUST NOT 包含 provider API key、password plaintext、JWT secret、browser Session/cache、logs、Redis/cache、临时文件或未受管宿主路径。

恢复 secrets payload 中 JWT MUST absent；restore activation 生成新 JWT secret。KEK 必须原样恢复，否则受保护 PII 不可读。

### DATA-023 — Limits

文件数量、单文件大小、总明文大小、chunk size 与解压比例 MUST 使用 versioned configurable limits；超限在写入目标路径前 fail closed。默认预算至少覆盖产品允许的 2 GiB document quota，但不得无上限。

## 4. Backup Lifecycle

### DATA-030

状态固定为：

```text
CREATING → VERIFYING → VERIFIED
CREATING/VERIFYING → FAILED
VERIFIED → INVALIDATED|PURGED
```

只有重新打开容器、校验 AEAD/manifest/file hashes/SQLite integrity 成功后可进入 VERIFIED。临时文件 MUST 原子 rename 后才进入 catalog。

### DATA-031 — Maintenance Boundary

桌面 backup MUST 在普通 backend 与 worker 停止写入后执行。maintenance process 以独占锁保护同一 userData root；无法取得锁返回 `DATA_MAINTENANCE_BUSY`，不得并发复制。

### DATA-032 — Retention

默认保留 7 daily、4 weekly、6 monthly。最后一个 VERIFIED、最新 PRE_MIGRATION、PRE_RESTORE 与 POST_ERASURE MUST protected。Retention 只删除 catalog 已验证且不受保护的明确路径；不得使用未解析 glob 或删除 userData root。

### DATA-033 — Schedule

桌面 SHOULD 在距最近 VERIFIED 超过 24 小时后的安全启动/退出窗口创建 SCHEDULED recovery point。失败记录稳定原因并在设置页告警；不得阻止普通启动。PRE_MIGRATION 失败 MUST 阻止 migration。

## 5. Verification and Restore

### DATA-040 — Verify

Verify MUST 覆盖：container auth、manifest schema、path/size limits、每个文件 hash/size、SQLite `quick_check`/`foreign_key_check`、数据库 schema revision presence/compatibility、required raw asset presence。

### DATA-041 — Staging Restore

Restore MUST 解密到新建的 private staging directory；MUST NOT 直接解压或写入 active database/documents。staging 通过 verification 后才 MAY forward migrate。

### DATA-042 — Schema Compatibility

- same/current supported revision → continue；
- older supported revision → deterministic Alembic forward migration in staging；
- future/unknown/multiple heads/missing required migration → `DATA_RESTORE_SCHEMA_UNSUPPORTED`；
- migration failure → current active data unchanged。

Restore MUST NOT 使用 downgrade 破坏新数据，也不得用 `create_all` 猜迁移后的历史 schema。

### DATA-043 — Reconciliation

激活前至少验证：SQLite integrity/FK；每个 non-deleted UserDocument 的受管文件存在且 checksum 匹配；deleted/quarantined visibility；outbox running task recovery；current erasure checkpoint；registered user-data binding coverage；projection source revision/version 可用。

可重建 projection MAY 标 stale 并在激活后 rebuild；canonical facts MUST NOT 通过在线 LLM 重新生成或用 current state 猜历史。

### DATA-044 — Atomic Activation and Rollback

激活前 MUST 创建 VERIFIED PRE_RESTORE rescue point。active DB/documents/secrets 通过同一 maintenance transaction journal 切换；crash recovery 根据 journal 完成或回滚，MUST NOT 留半套数据。激活后 readiness 失败 MUST 自动恢复 rescue point并报告 `DATA_RESTORE_FAILED_ROLLED_BACK`。

### DATA-045 — Report

`RecoveryReportV1` MUST 包含 report/backup id、阶段状态、schema before/after、校验计数、projection actions、erasure checkpoint、started/completed_at、稳定 reason codes；MUST NOT 包含原文、secret、密码、Prompt、完整本地路径。

## 6. Migration Guard

### DATA-050

任何可能改变或删除用户数据的 desktop migration MUST 在 active data 上执行前：

1. 识别 current DB revision；
2. 创建 VERIFIED PRE_MIGRATION point；
3. 在 staging copy 执行 migration 与 validation；
4. 成功后 atomic activate；
5. 失败保持 current data 并显示报告。

## 7. User Data Export V1

### DATA-060 — Envelope

```yaml
format: askora-user-export
schema_version: "1.0"
export_id: uuid
created_at: datetime
user_ref: opaque string
scopes: [PROFILE|DOCUMENTS|LEARNING_RECORDS|MODEL_EXECUTION]
files:
  - path: string
    media_type: string
    sha256: string
```

### DATA-061 — Current-user and Allowlist

Export MUST 由 authenticated current-user command 创建。字段/实体采用显式 allowlist，MUST NOT 使用 `SELECT *` 或 ORM automatic serialization。每项保留 owner/source/version 或 `LEGACY_COMPATIBILITY`。

### DATA-062 — Exclusions

MUST 排除 password/hash、JWT/refresh token、KEK/Recovery Key/provider key、内部 Prompt/system instructions、grader-only answer/rubric、未经选择的完整文档、其他用户数据、本地绝对路径、stack trace。

### DATA-063 — Delivery

导出临时文件使用 private permissions、短期 expiry、一次性 current-user token；下载完成或 expiry 后安全清理。导出失败不得生成 partial artifact 并声称完成。

## 8. Erasure Workflow V1

### DATA-070 — Scope

```text
DOCUMENT
LEARNING_RECORDS
MODEL_EXECUTION
ALL_PERSONAL_DATA
```

Scope 语义不得由客户端自由组合。未来新增 scope 必须升合同版本或 additive enum 并冻结影响矩阵。

### DATA-071 — Preview

执行前 MUST 返回 `ErasurePreviewV1`：current-user、scope/target ref、每 owner 预计影响计数、共享 provenance 处理、backup impact、不可逆说明、expiring confirmation token。Preview MUST read-only，token 与 preview digest/user/scope/expiry 绑定。

### DATA-072 — Confirmation and Idempotency

执行必须使用 preview token + idempotency key + explicit confirmation phrase。过期、digest/owner/scope 不匹配、重复但 payload 不同必须拒绝。重复相同 command 返回同一 workflow/report。

### DATA-073 — Ownership

Erasure coordinator MUST 通过 owner command/adapter 执行；不得直接 patch 其他 owner canonical state。每个 owner step durable、idempotent、可重试并记录最小 result。执行期间 target scope MUST fail closed/invisible。

### DATA-074 — Document Erasure

DOCUMENT 必须处理 raw asset、UserDocument/SourceSpan/DocumentIR、exclusive KnowledgeUnit/relation provenance、retrieval projection、goal mapping/plan refs、evidence/event/inference refs。存在 alternate valid provenance 的 shared knowledge MAY 保留，但必须移除被删 provenance 并重新验证；无法安全分类时 fail closed，不得继续发布。

### DATA-075 — Learning and Execution Erasure

LEARNING_RECORDS 必须处理 dialog/transcript、Attempt/AssessmentResult、LearnerEvidence/Mastery/LearnerState、Goal/Plan/Activity、ReviewSchedule、related events/decisions/outcomes，并重建空/剩余 projection。MODEL_EXECUTION 只处理可归属当前用户的 inference/transcript/execution metadata；不能证明归属的全局 policy/config 不得删除。

ALL_PERSONAL_DATA 还必须处理 profile/auth/session/document storage；P1-05 负责账号入口与认证撤销，但必须调用同一 workflow。

`consent_records` 等已进入 frozen subject-binding manifest 的 legacy privacy 表 MUST 具有正式
Alembic schema coverage，不得只依赖本地 `create_all` 偶然建表。P1-03 migration 对已由旧版应用
预建的同结构表 MUST 校验兼容并 forward-adopt；结构不兼容时 fail closed。该兼容只补齐持久化与
删除覆盖，不改变 Identity/Privacy owner，也不授权 Data Control 成为该表的普通业务写入者。

### DATA-076 — Tombstone and No Resurrection

成功后写不含内容的 `ErasureReceiptV1` 与单调 `ErasureCheckpointV1`。Restore/rebuild MUST 应用 checkpoint，MUST NOT 引用或重新生成被删事实。早于 checkpoint 且无法安全过滤的 managed recovery points 必须 INVALIDATED/PURGED；随后创建 VERIFIED POST_ERASURE baseline。

### DATA-077 — Partial Failure

任一 step 失败时 workflow 为 `FAILED_RETRYABLE|FAILED_TERMINAL|PARTIAL`；target scope 保持不可见。UI 不得显示“删除完成”。Retry 只执行未完成的幂等 step；最终报告列出 owner/status/reason，不含被删内容。

### DATA-078 — P1-05 Account Authorization Bridge

P1-05 继续拥有账号删除的 password re-auth、精确确认短语、24h grace/cancel、session revoke 与 deletion-control token；这些记录是调用 `ALL_PERSONAL_DATA` 的 authorization/orchestration envelope，不是第二 erasure workflow。

账号请求到期后 MUST 以稳定 request idempotency identity 调用本工作流。`data_erasure_workflows`、`data_erasure_steps`、`data_erasure_receipts` 与 `data_erasure_checkpoints` 是唯一执行 truth；P1-05 只能保存其 refs/digest 和最小 tombstone。P1-05 MUST NOT 写独立 owner-step receipt。

当前 `ALL_PERSONAL_DATA` plan MUST 使用已登记的 exhaustive subject-binding coverage，包含后续落地的 activity、library、onboarding、auth/recovery 数据；P1-03/P1-05 governance rows 不作为用户正文删除。账号状态在 canonical partial/retry 或必需的 POST_ERASURE/no-resurrection maintenance 完成前 MUST 保持 `PURGING|DELETION_BLOCKED`，不得显示 `DELETED`。

## 9. API / IPC

### DATA-080

Backend current-user API 负责 status/query、export、erasure preview/confirm/report。Desktop IPC 负责 recovery key、native file chooser、backend stop/start、maintenance backup/verify/restore 与 progress。IPC 使用固定 allowlist typed payload；renderer 不获得 filesystem、shell 或 arbitrary argv 权限。

### DATA-081

恢复/备份进行中普通 UI 进入 maintenance 状态；不得继续提交学习写入。Restore success 后清除 auth/frontend caches 并要求重新登录。

## 10. Stable Errors

至少冻结：

```text
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
```

错误遵循 `error-contract.md`；secret/internals 不进入 details。

## 11. Tests

必须覆盖 L0～L5：contracts/version/errors；crypto/tamper/limits/path；SQLite snapshot/integrity/FK；migration staging/rollback；file reconciliation；export allowlist/secret leakage；four erasure scopes/owner/idempotency/partial recovery/no resurrection；Electron IPC/packaged maintenance；frontend states/accessibility；真实桌面 backup→mutate→restore→verify。

## 12. Acceptance Criteria

- `DATA-AC-001`：桌面用户可创建 VERIFIED 加密恢复点并看见时间、原因、范围和位置边界。
- `DATA-AC-002`：wrong key/tampered/truncated/unsafe package 在 active data 变化前被拒绝。
- `DATA-AC-003`：restore 在 staging 完成 schema/file/owner/checkpoint reconciliation，失败自动保留/恢复原数据。
- `DATA-AC-004`：destructive migration 无 VERIFIED PRE_MIGRATION point 时不能执行。
- `DATA-AC-005`：export current-user allowlist，无 secret/internal/grader/other-user leakage。
- `DATA-AC-006`：四类 erasure preview/confirm/idempotency/report 完整，partial 不谎报成功。
- `DATA-AC-007`：被删除事实不能由 managed old backup、event replay 或 projection rebuild 恢复。
- `DATA-AC-008`：data-control artifacts 不形成第九业务 truth，owner boundary architecture tests 通过。
- `DATA-AC-009`：Settings 覆盖 loading/ready/not-protected/in-progress/error/partial/success 与 360px/keyboard/live status。
- `DATA-AC-010`：真实打包/等价 Electron maintenance smoke 和本地桌面 E2E 通过。

## 13. Forbidden Implementations

禁止：普通 `copytree` 冒充一致备份；明文或自包含 key 备份；恢复直接覆盖 active path；unknown schema `create_all`；在线 LLM replay；export `SELECT *`；跨 owner ORM hard delete；删除后保留可激活旧 managed backup；renderer 任意 filesystem/shell；仅 Mock/单元测试宣称 P1-03 DONE。
