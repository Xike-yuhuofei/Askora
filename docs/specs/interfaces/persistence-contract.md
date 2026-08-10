# Askora Persistence Contract

> Spec ID：`PERSIST-*`  
> 状态：Canonical Implementation Contract  
> 版本：v1 Product Positioning Alignment + existing recovery/learning contracts  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. v1 Production Baseline

### PERSIST-001 — SQLite Is the Production-local Baseline

Askora v1 最终用户运行时 MUST 使用本地 SQLite 作为结构化持久化 baseline。

PostgreSQL MAY 用于 CI、测试、兼容性验证或未来可选服务模式，但：

- MUST NOT 是 v1 最终用户运行依赖；
- MUST NOT 要求用户安装/维护 PostgreSQL；
- production-local correctness MUST NOT 依赖 PostgreSQL 专有语义。

### PERSIST-002 — Physical Store != Shared Write Ownership

共用一个物理 SQLite 数据库不等于共享状态写权限。repository/application boundary MUST 按 `state-ownership.md` 分界。

### PERSIST-003 — Managed Local Data Directory

Askora MUST 管理自己的本地数据目录，逻辑结构至少能够表达：

```text
AskoraData/
├── askora.db
├── files/       # durable managed source files/assets
├── indexes/     # rebuildable indexes
├── cache/       # disposable cache
├── jobs/        # optional file-backed job artifacts; job truth remains durable
└── logs/
```

实际目录名 MAY 实现调整，但 durable / derived 边界 MUST 保持。

用户选择数据目录位置不意味着内部文件成为公开稳定 API。

### PERSIST-004 — LocalOwner and Workspace Scope

每个 local datastore 最多存在一个 active LocalOwner。Workspace-scoped records MUST 能解析 `workspace_id`；owner_id 相同不得替代 workspace filter。

历史 `user_id` / `pseudonym_id` 列 MAY 作为迁移兼容字段保留，但 canonical semantics MUST 是 LocalOwner/Learner ownership，不是 Account/Auth principal。

## 2. Repository Boundary

目标逻辑 repository：

```text
PlatformIdentityRepository      LocalOwner
WorkspaceRepository             Workspace / LearningProject membership
ContentKnowledgeRepository      SYS01
RetrievalProjectionStore        SYS02
LearnerStateRepository          SYS03
AssessmentRepository            SYS04
TeachingPolicyRepository        SYS05
LearningPlanRepository          SYS06
ReviewScheduleRepository        SYS07
ExecutionLedgerRepository       SYS08
JobRepository                   Platform Job Runtime
DataLifecycleRepository         backup/migration/erasure metadata
```

### PERSIST-010

一个领域不得通过其他领域 ORM model 绕过其 repository/application contract。

## 3. Durable Data vs Derived Data

### PERSIST-011 — Durable Facts

至少以下数据 MUST 作为 durable/canonical data 保护：

- LocalOwner；
- Workspace / LearningProject / ProjectMaterial relationship；
- Material / managed SourceFile；
- LearningGoal；
- UserNote；
- Attempt / AssessmentResult / LearningEvidence；
- LearningHistory / canonical decision records；
- 用户配置（secret 除外，见 Secret Boundary）；
- deletion/trash/erasure facts；
- background job state needed for safe recovery。

### PERSIST-012 — Rebuildable Canonical Projection

MasteryEstimate / LearnerState 是 SYS03 的 canonical read projection，但 MUST 能从 durable LearningEvidence/Assessment-related facts + exact projector/version 重建。

删除或修正 evidence 后 MUST invalidate/supersede affected projection 并重建。

### PERSIST-013 — Infrastructure-derived Data

以下数据 SHOULD 可安全删除并重建：

- SourceChunk；
- Embedding；
- Vector Index；
- Lexical/Search Index；
- Graph retrieval projection；
- Cached Retrieval Results；
- 可重新生成的 AI Summary。

任何 derived artifact MUST 记录足够的 source/version dependency，以便 stale/invalidate/rebuild。

## 4. Transaction and Outbox

### PERSIST-020

领域状态更新与对应 durable outbox/event record MUST 在同一 SQLite transaction 或等价原子边界提交。

### PERSIST-021

v1 使用 local transaction + outbox + idempotent consumer/projection，不引入 2PC。

### PERSIST-022

Outbox/job task 必须具有：id、type、payload/schema version、status、attempt count、next_attempt_at、last_error code/summary、created/updated timestamps、idempotency key。

### PERSIST-023 — Local Delivery

Outbox/worker delivery MAY 由同一 Local Server 进程或受控本地 worker 执行。不得要求 Redis/Kafka/Celery 等独立服务才能保证 correctness。

## 5. Idempotency and Concurrency

### PERSIST-030

关键 command 使用幂等键；aggregate version 使用唯一约束/optimistic concurrency。

### PERSIST-031

重复请求不得创建重复 Attempt、Evidence、Mastery update、Tool side effect、Material ingest 或相同 rebuild job。

### PERSIST-032

并发冲突必须显式返回 conflict/retryable outcome，不得 last-write-wins 静默覆盖版本化状态。

### PERSIST-033 — Bounded Local Concurrency

Parsing、Embedding、AI API、Indexing 等 job category MUST 有本地并发上限。同一 Material 的同类 active rebuild MUST 支持 dedup/互斥。

## 6. Versioning

### PERSIST-040

Published/decision/inference objects 按 Spec 使用 immutable row + new version/supersedes semantics。

### PERSIST-041

Schema migration、business object version、parser/index/model version 是不同概念，不得混用。

### PERSIST-042 — Data-directory Compatibility

Local datastore MUST 记录或能确定：

```text
schema_version
minimum_reader_version
minimum_writer_version
```

程序打开数据目录前 MUST 检查兼容性。无法证明可安全读写时 MUST fail closed，而不是尝试未知 ALTER 或直接写入。

## 7. SQLite and Development Adapters

### PERSIST-050

SQLite production-local MUST 启用适当 foreign keys、transaction discipline、busy/lock handling 与 migration gate；不得假设 Redis/Kafka/PostgreSQL 存在。

### PERSIST-051

PostgreSQL adapter MAY 用于 CI 验证跨数据库领域语义，但 PostgreSQL compatibility 不得迫使 v1 引入服务化运维复杂度或牺牲 SQLite correctness。

### PERSIST-052

若 SQLite 与 PostgreSQL 某实现细节发生冲突，v1 product semantics 与 SQLite production-local correctness 优先；可通过 adapter/test 处理差异。

## 8. Cache / Redis

### PERSIST-060

Redis 不属于 v1 production runtime contract。

如开发/CI/未来实验仍存在 Redis adapter：

- 只能用于可重建 cache/短期协调；
- MUST NOT 成为 LearnerState、Event Ledger、LearningPlan、Job truth 或 idempotency correctness 的唯一来源；
- production-local path MUST 能在完全没有 Redis 的环境运行。

## 9. Files and Indexes

### PERSIST-070 — Import Copies Source into Managed Storage

Material Import MUST 是 `ingest + copy`。系统必须先把用户选择的原始资料复制到 Askora managed local storage，并以 checksum/managed asset identity 持久化。

后续 parse/replay MUST NOT 依赖用户最初选择的外部文件路径仍然存在。

### PERSIST-071

原始 managed SourceFile、vector index、lexical index、graph projection 与 canonical relational data 必须区分。

### PERSIST-072

任何可重建 projection 都必须保存 source revision/parser/chunker/embedding/index/model version，支持 invalidate/rebuild。

### PERSIST-073 — Original File Durability

缓存清理、index rebuild、AI provider failure、parser retry MUST NOT 删除或覆盖 durable SourceFile。新内容版本使用新 revision/supersede semantics。

## 10. Data Integrity

至少建立以下约束：

- LocalOwner cardinality ≤ 1 active per datastore；
- workspace id/reference integrity；
- material belongs to exactly one Workspace；
- ProjectMaterial relation unique in project/material scope；
- event_id unique；
- aggregate id/version unique；
- idempotency scope unique；
- item id/version consistent；
- estimate owner/workspace/knowledge/version unique where applicable；
- plan id/version unique；
- review schedule owner/workspace/knowledge/version unique where applicable；
- foreign key/reference integrity where practical。

## 11. Trash, Deletion and Erasure

### PERSIST-080

普通删除 MUST 服从：

```text
Normal
→ Trash
→ Permanent Delete
```

Trash state 是 durable lifecycle fact。永久删除只能由用户明确触发或由预定义本地清理策略执行。

### PERSIST-081 — Project Relation vs Material Deletion

从 LearningProject 移除 Material 只删除 `ProjectMaterial` relationship，不删除 Material/SourceFile。

删除 Material 本体前 MUST 检查其他 Project 引用并向上层返回影响信息；不得以 relationship delete 冒充 object delete。

### PERSIST-082 — Evidence/Data Erasure

删除 LearningEvidence/Assessment-related durable fact 后，受影响 LearnerState/MasteryEstimate MUST invalidated/reprojected。删除后 projection rebuild MUST NOT resurrect erased facts。

受保护 ledger 的物理删除只能由 owner-safe data-control/erasure adapter 按固定 scope、idempotent steps、receipt/checkpoint 执行；普通 repository 不开放任意 delete。

### PERSIST-083 — Restore Barrier / No Resurrection

明确永久删除后的 backup/restore 与 projection rebuild MUST 消费单调 erasure checkpoint 或等价 no-resurrection evidence。无法证明不会复活已删事实的旧恢复点不得直接激活。

AccountDeletion/AuthSession/RecoveryCredential 等旧 account-state persistence 已由 ADR-0015/LID-* supersede；不得重新进入 v1 runtime。

## 12. Schema Migration

### PERSIST-090

每个破坏性 migration 必须：

- 明确 source/target schema；
- 数据 backfill strategy；
- rollback 或 forward-fix strategy；
- old/new code compatibility window；
- 数据校验 query/test；
- 不丢 historical provenance；
- 不破坏 LocalOwner/Workspace ownership。

### PERSIST-091

双写仅允许短期迁移，必须在 EXEC Plan 指定 canonical truth、reconciliation 和停止条件。

### PERSIST-093 — Startup Compatibility Gate

Local Server startup MUST verify datastore/schema compatibility before readiness。Mismatch/failure MUST fail readiness and publish sanitized bootstrap diagnostic。

Startup code MUST NOT：

- 静默运行未知 destructive repair；
- “字段不存在就 ALTER”而无 migration version；
- 在未知 schema 上继续写入。

## 13. Backup / Restore / Export

### PERSIST-100 — Askora Backup Boundary

Backup 的目标是恢复 Askora。Versioned backup SHOULD 包含：

```text
Askora Backup
├── manifest
├── durable database snapshot
├── managed source files
└── backup metadata / erasure checkpoint
```

manifest 至少包含：backup_format_version、askora_version、schema_version、created_at、workspace scope。

默认 MUST NOT 包含：

- API Key / secret；
- cache；
- embeddings/indexes 等可重建 derived data；
- 非必要诊断内容。

### PERSIST-101 — Staging Restore

Restore MUST 先在 private staging 完成 schema/SQLite/file/reference/checkpoint validation 与必要 forward migration，再 atomic activate 或使用等价 crash-safe activation；失败不得破坏 active data。

### PERSIST-102 — Migration Protection

破坏性 migration 前 MUST 有符合当前数据风险的 safety backup/recovery point，并在 migration 后验证。恢复优先使用 forward-fix/staging restore，不把 blind downgrade 当唯一数据安全保证。

### PERSIST-103 — Erasure Checkpoint

明确永久删除后，managed recovery catalog 与 projection rebuild MUST 消费 no-resurrection checkpoint；不安全旧恢复点不得无提示激活。

### PERSIST-104 — Backup != Export

Export 的目标是让数据离开 Askora 后仍可使用；Backup 的目标是恢复 Askora。两者格式、兼容性与 secret policy MUST 分离。

## 14. Local Background Job Persistence

### PERSIST-110

Background job canonical runtime state至少支持：

```text
pending
running
succeeded
failed
interrupted
```

Local Server shutdown MUST 把无法安全完成的 running job 转入可恢复状态，或在下次启动通过 lease/heartbeat/versioned rule 判定 interrupted。

### PERSIST-111

Job retry MUST 基于 error taxonomy 和 bounded attempt/backoff；Authentication/API Key error、invalid request 等非 transient error 不得无限重试。

### PERSIST-112

Job artifacts 与 source facts 分离。下游失败不得默认重跑没有变化的上游阶段；stage completion/version fingerprints SHOULD 允许局部恢复。

## 15. Failure Semantics

- SQLite lock/busy → bounded retry；
- unique/idempotency conflict → fetch existing or explicit conflict；
- migration mismatch → fail startup/readiness；
- outbox/job execution failure → durable retry/interrupted；
- projection failure → mark stale/partial，canonical durable facts preserved；
- external AI failure → bounded retry or failed stage，MUST NOT corrupt durable data。

### PERSIST-092 — Operational Recovery Ledger

Recovery incident/action audit MAY 由 SYS08/Platform Recovery 以 append-only ledger 持久化，但它不是文档、计划、learner state 或原 job 的 current truth。至少保存 stable code、safe resource ref、status event、attempt/budget、correlation、idempotency 与 timestamps；MUST NOT 保存 secret、完整 Prompt、绝对路径、SQL/traceback 或 provider 原始 body。

同一 issue 的 current projection必须 deterministic fold append-only events。Manual replay 必须创建带 `recovery_of` 的 replacement task/run，原 dead-letter/history 不得重置或删除。重复 action idempotency key 返回同一 result。

## 16. Tests

必须覆盖：

- SQLite integration as production baseline；
- clean environment without Redis/PostgreSQL/Docker；
- LocalOwner cardinality / Workspace isolation；
- transactional outbox atomicity；
- duplicate idempotency；
- optimistic concurrency；
- managed source-file copy and original-path independence；
- job interruption/restart/dedup/retry；
- projection rebuild；
- delete LearningEvidence → LearnerState reprojection；
- migration upgrade on representative fixture；
- schema mismatch fail-closed；
- backup/restore round trip；
- erasure no-resurrection；
- derived indexes omitted from backup and rebuildable；
- secrets omitted from backup/export/log。

## 17. Forbidden Implementations

禁止：

- Redis 作为唯一 learner/job/idempotency truth；
- production-local 必须连接 PostgreSQL；
- 一个 JSON column 由八类系统任意 patch；
- last-write-wins 覆盖 immutable decisions；
- 业务状态更新成功但 outbox 靠另一个非原子事务写；
- SQLite 本地版依赖 Kafka/Redis/Docker 才能启动；
- migration 丢弃历史版本/证据而无明确治理；
- Import 只保存用户原文件路径、不复制 source；
- 删除 LearningEvidence 后保留旧 LearnerState；
- restore 直接覆盖 active path 而无验证；
- API Key 进入普通 SQLite profile、默认 backup/export/log；
- unknown schema 自动写入。

## 18. Onboarding Preference Persistence

### PERSIST-300

`onboarding_preferences` MUST 使用 production-local SQLite-compatible schema，唯一键语义为 `(owner_id, journey_id)`。历史实现若仍使用 `user_id` 列 MAY 迁移兼容，但不得解释为 Account identity。

Preference 只保存 presentation preference/version/timestamps/幂等 receipt；MUST NOT 出现 step completion 或 material/goal/plan/activity/transcript refs。

### PERSIST-301

LocalOwner bootstrap 后首次查询可创建 active onboarding preference；并发创建通过唯一约束 fetch existing。Migration/rollback/forward-fix 不得改写任何 SYS01～SYS08 state。

### PERSIST-302

Preference 可随 ALL_PERSONAL_DATA/reset scope 删除。localStorage/sessionStorage 不得成为 preference、journey 或 step truth。

## 19. Goal Persistence

Definition/Goal State/Plan State/Draft/Preview/Focus/Evaluation/Policy 与 command receipt 使用 SQLite-compatible tables。状态、预览和 receipt 只能按对应 contract version/supersede；effective refs 原子切换。

LearningGoal MUST 具有 Workspace scope；Project association MAY 为空。Legacy Goal/Plan payload status 降为 initial snapshot，新写不得长期双写。Migration 保留 legacy 历史并提供 semantic-fingerprint reconciliation、representative fixture 与 forward-fix/rollback strategy。
