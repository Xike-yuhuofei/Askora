# Askora Persistence Contract

> Spec ID：`PERSIST-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1 + P1-03 additive recovery contract

## 1. 基线

### PERSIST-001

v0.2 MUST 支持：桌面/本地 SQLite；服务模式 SHOULD 保持 PostgreSQL 兼容。领域语义不得依赖某数据库专有行为，除非通过 adapter 隔离。

### PERSIST-002

共用一个物理数据库不等于共享状态写权限。repository 按 `state-ownership.md` 分界。

## 2. Repository Boundary

目标逻辑 repository：

```text
ContentKnowledgeRepository   SYS01
RetrievalProjectionStore     SYS02
LearnerStateRepository       SYS03
AssessmentRepository         SYS04
TeachingPolicyRepository     SYS05
LearningPlanRepository       SYS06
ReviewScheduleRepository     SYS07
ExecutionLedgerRepository    SYS08
```

### PERSIST-010

一个领域不得通过其他领域 ORM model 绕过其 repository/application contract。

## 3. 事务与 Outbox

### PERSIST-020

领域状态更新与对应 durable outbox/event record MUST 同事务提交。

### PERSIST-021

v0.2 使用 local transaction + outbox + idempotent consumer，不引入 2PC。

### PERSIST-022

Outbox task 必须具有：id、type、payload/schema version、status、attempt count、next_attempt_at、last_error、created/updated timestamps、idempotency key。

## 4. 幂等与并发

### PERSIST-030

关键 command 使用幂等键；aggregate version 使用唯一约束/optimistic concurrency。

### PERSIST-031

重复请求不得创建重复 Attempt、Evidence、Mastery update、Tool side effect。

### PERSIST-032

并发冲突必须显式返回 conflict/retryable outcome，不得 last-write-wins 静默覆盖版本化状态。

## 5. Versioning

### PERSIST-040

Published/decision/inference objects 按 Spec 使用 immutable row + new version/supersedes semantics。

### PERSIST-041

Schema migration 与业务 object version 是不同概念，不得混用。

## 6. SQLite/PostgreSQL

### PERSIST-050

SQLite 模式必须启用适当 foreign keys/transaction discipline；不得假设 Redis/Kafka 存在。

### PERSIST-051

PostgreSQL 可以增强并发/索引，但应用结果语义必须与 SQLite 保持一致。

## 7. Cache / Redis

### PERSIST-060

Redis 只能用于可重建 cache、短期协调或性能优化，MUST NOT 成为 LearnerState、Event Ledger、LearningPlan 等唯一事实源。

Redis 不可用时核心教学闭环 SHOULD 能降级运行，除非明确功能本身依赖实时协调。

## 8. 文件与向量/图索引

### PERSIST-070

原始文件存储、向量 index、lexical index、graph projection 与 canonical relational data 必须区分。

### PERSIST-071

任何可重建 projection 都必须保存 source revision/index version，支持 invalidate/rebuild。

## 9. 数据完整性

至少建立以下约束：

- event_id unique；
- aggregate id/version unique；
- idempotency scope unique；
- item id/version consistent；
- estimate user/knowledge/version unique；
- plan id/version unique；
- review schedule user/knowledge/version unique；
- foreign key/reference integrity where practical。

## 10. 数据删除

### PERSIST-080

用户删除长期数据时，必须能定位相关 content、learning events、inferences、states 和 projections；删除后重建不应重新生成已删除事实。

### PERSIST-081 — Durable Identity and Privacy State

`AuthSession`、`RecoveryCredential`、`AccountDeletionRequest`、subject manifest 与 privacy tombstone projection MUST 持久化于 SQLite/PostgreSQL compatible store。owner step/workflow/receipt/checkpoint 唯一持久化 truth 是 P1-03 `DataErasureWorkflowV1` records；P1-05 request 只保存其 refs。Redis、renderer local state 或只存在内存的 token blacklist MUST NOT 成为唯一 truth。

### PERSIST-082 — Privacy Erasure

隐私删除 MUST 使用固定 scope、registered subject manifest、P1-03 per-owner idempotent step/receipt/checkpoint 与 reconciliation。普通 immutable repository 继续拒绝 delete；只有携带 canonical erasure workflow 与 accepted account authorization/manifest 的 privacy-only adapter MAY 按 `EVENT-071` 删除受保护 ledger。

### PERSIST-083 — Restore Barrier

账号删除完成后的 restore barrier MUST 位于普通数据库快照之外并使用原子文件替换或等价 durable adapter；启动/认证必须在接受旧 snapshot 数据前检查 barrier。

## 11. Migration

### PERSIST-090

每个破坏性 migration 必须：

- 明确 source/target schema；
- 数据 backfill strategy；
- rollback 或 forward-fix strategy；
- old/new code compatibility window；
- 数据校验 query/test；
- 不丢历史 provenance。

### PERSIST-091

双写仅允许短期迁移，必须在 EXEC Plan 指定 canonical truth、reconciliation 和停止条件。

## 11A. P1-03 Backup / Restore

### PERSIST-100 — Physical Snapshot Boundary

私人桌面 SQLite recovery point MUST 在 maintenance write-stop boundary 创建，并同时覆盖数据库、受管 raw assets、恢复 PII 所需 KEK material、manifest/checksum 与 erasure checkpoint。普通目录复制或只备份数据库不满足本要求。

### PERSIST-101 — Staging Restore

Restore MUST 先在 private staging 完成 authenticated decrypt、schema/SQLite/file/reference/checkpoint validation 与必要 forward migration，再 atomic activate；失败不得改变 active data。详细合同见 `data-control-contract.md`。

### PERSIST-102 — Migration Protection

破坏性 desktop migration MUST 有当前 VERIFIED PRE_MIGRATION recovery point，并在 staging 验证后激活。恢复优先使用 rescue/forward-fix，不把 blind Alembic downgrade 当数据安全保证。

### PERSIST-103 — Erasure Checkpoint

明确删除后，managed recovery catalog 与 projection rebuild MUST 消费单调 erasure checkpoint；无法证明不会复活被删事实的旧恢复点不得激活。

## 12. Failure Semantics

- transient DB lock/network → bounded retry；
- unique/idempotency conflict → fetch existing or explicit conflict；
- migration mismatch → fail startup/health gate；
- outbox delivery failure → durable retry；
- projection failure → mark stale, canonical truth preserved。

### PERSIST-092 — Operational recovery ledger

Recovery incident/action audit MAY 由 SYS08 以 append-only ledger 持久化，但它不是文档、计划、
learner state 或原 outbox task 的 current truth。至少保存 stable code、safe resource ref、status
event、attempt/budget、correlation、idempotency 与 timestamps；MUST NOT 保存 secret、完整 Prompt、
绝对路径、SQL/traceback 或 provider 原始 body。

同一 issue 的 current projection必须 deterministic fold append-only events。Manual replay 必须创建
带 `recovery_of` 的 replacement task/run，原 dead-letter row/history 不得重置或删除。重复 action
idempotency key 返回同一 result。

### PERSIST-093 — Startup compatibility gate

Local desktop startup MUST verify database connectivity and migration compatibility before `/ready`。
Mismatch/failure must fail readiness and publish a sanitized bootstrap diagnostic. Migration recovery
MUST route to P1-03 verified snapshot/restore/forward-fix capability; startup code MUST NOT silently run
destructive repair or continue against an unknown schema.

## 13. Tests

必须覆盖：

- SQLite integration；
- transactional outbox atomicity；
- duplicate idempotency；
- optimistic concurrency；
- restart task recovery；
- projection rebuild；
- migration upgrade on representative fixture；
- rollback/forward-fix path；
- Redis unavailable degradation（相关功能）。
- recovery event fold、action idempotency、replacement lineage 与 restart；
- startup migration mismatch/forward-fix and sanitized diagnostic。
- encrypted recovery round trip、tamper/wrong-key/path/limit；
- staging restore、rescue rollback、erasure no-resurrection。

## 14. Forbidden Implementations

禁止：

- Redis 作为唯一 learner state；
- 一个 JSON column 由八类系统任意 patch；
- last-write-wins 覆盖 immutable decisions；
- 业务状态更新成功但 outbox 靠另一个非原子事务写；
- SQLite 本地版依赖 Kafka 才能启动；
- migration 丢弃历史版本/证据而无显式设计批准。
- 恢复直接覆盖 active path、明文/自包含 key recovery package、删除后继续激活不安全旧恢复点。

## 15. P1-06 Presentation Preference Persistence

### PERSIST-300

`onboarding_preferences` MUST 使用 SQLite/PostgreSQL compatible schema，唯一键
`(user_id, journey_id)`、optimistic `preference_version`、timezone-aware timestamps 与幂等 command
receipt。表中 MUST NOT 出现 step completion 或 document/goal/plan/activity/transcript refs。

### PERSIST-301

Migration MUST 在同一事务把当时 existing users backfill 为 dismissed/legacy-existing-user；迁移后无
row 的新用户首次查询创建 active v1，并发创建通过唯一约束 fetch existing。Rollback/forward-fix 不得
改写任何 SYS01～SYS08 state。

### PERSIST-302

Preference 必须随 ALL_PERSONAL_DATA 删除，并在 logout/user switch/schema major change 清除 frontend
read cache。localStorage/sessionStorage 不得成为 preference、journey 或 step truth。
