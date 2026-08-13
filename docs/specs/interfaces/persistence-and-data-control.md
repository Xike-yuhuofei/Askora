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

---

## Material Trash, Restore and Permanent Delete Contract

> Spec ID：`MATLIFE-*`  
> 状态：**Canonical Implementation Contract / FROZEN**  
> 版本：v1.0  
> 冻结日期：2026-08-10  
> Governing：`docs/product/PRODUCT-POSITIONING.md`、`LIB-045/046`、`PERSIST-080..083`、`DATA-070..077`、ADR-0016  
> Linear：XIK-170

### 1. Purpose

本合同只补齐 v1 已冻结的：

```text
active
→ trash
→ permanent delete
```

的 command、migration、SourceFile、Project reference、derived-data、job、restore 与 no-resurrection 实现语义。

它不建立新的产品级删除模型，不替代 P1-03 Data Control，也不改变 Material/SYS01/Workspace 的 ownership。

### 2. Ownership and Boundary

#### MATLIFE-001 — Material Lifecycle Writer

Material current lifecycle (`active|trash`) 由 SYS01 Material owner 写入。

Permanent Delete 的跨 owner 物理清理由 canonical Data Control `DOCUMENT` erasure workflow 协调；SYS01 只执行其 owner step，不得直接越权删除 SYS03/SYS06/SYS08 等其他 owner 状态。

#### MATLIFE-002 — Relationship Removal Is Not Material Delete

```text
RemoveFromProject(project_id, material_id)
→ delete ProjectMaterial relationship only

TrashMaterial(material_id)
→ Material lifecycle active → trash

PermanentDeleteMaterial(material_id)
→ confirmed DATA DOCUMENT workflow
```

三者 MUST 是不同 command/receipt/telemetry 语义。

#### MATLIFE-003 — Processing Status Is Orthogonal

Material lifecycle MUST NOT 复用：

- `processing_status=FAILED`；
- parser/index status；
- quarantine status；
- Project membership；
- UI hidden flag。

Trash does not mean processing failed. New Trash/Restore commands MUST NOT mutate processing status merely to express lifecycle.

### 3. Canonical Lifecycle

#### MATLIFE-010 — Active

`active` Material MAY participate in ordinary Library search, retrieval, Project learning, new LearningSession and background processing subject to normal safety/readiness rules.

#### MATLIFE-011 — Trash

Trash is durable and recoverable.

When `lifecycle=trash`:

- Material metadata remains durable；
- managed SourceFile remains durable；
- MaterialRevision/SourceSpan provenance remains durable；
- ProjectMaterial memberships remain durable；
- historical Goal/LearningSession/LearningEvidence refs remain durable；
- ordinary Library default view/search excludes it；
- SYS02 ordinary retrieval excludes it；
- it cannot be used to start new learning or new knowledge publication；
- active/retryable background jobs for that Material MUST be canceled/interrupted or their late result rejected from publish；
- backup MUST include the Trash state and retained SourceFile like other durable data。

#### MATLIFE-012 — Restore

Restore is allowed only from `trash` and returns Material to `active`.

Restore MUST NOT fabricate processing readiness. Existing valid durable content/revision facts remain, but any removed/stale derived projection is rebuilt/validated under current versioned pipeline before being advertised READY.

ProjectMaterial memberships retained through Trash automatically become effective again when Material is active; Restore does not recreate guessed relationships.

#### MATLIFE-013 — Permanent Deleted

Permanent deletion is terminal for the recoverable Material.

`deleted` is a logical terminal state represented only by the minimum tombstone/erasure receipt/checkpoint needed for idempotency, audit and no-resurrection. It MUST NOT retain user content merely to keep a Material row looking populated.

A permanently deleted Material cannot be restored through Trash. Recovery from an older backup MUST obey the erasure checkpoint and MUST NOT resurrect it.

### 4. Lifecycle Record

#### MATLIFE-020

Canonical current Material persistence MUST be able to represent at least:

```yaml
material_lifecycle:
  material_id: uuid
  workspace_id: uuid
  lifecycle: active|trash
  lifecycle_version: integer
  trashed_at: datetime|null
  trash_reason: USER_DELETE|BATCH_DELETE|OTHER|null
  updated_at: datetime
```

A terminal permanent-delete tombstone/receipt MAY be stored outside the current Material row according to Data Control so long as `material_id`, scope, deletion time/workflow/checkpoint and idempotency can be proven without retained content.

#### MATLIFE-021 — Optimistic Concurrency

Trash/Restore commands MUST include expected lifecycle/material version and idempotency key. Stale expected version returns explicit conflict; no last-write-wins.

#### MATLIFE-022 — Idempotent Repeats

- Trash already trashed + same idempotency/payload → return original result；
- Restore already restored + same idempotency/payload → return original result；
- same idempotency key + different target/payload → conflict；
- permanent delete repeat uses canonical Data Control workflow idempotency and returns same safe report/result。

### 5. Trash Command

#### MATLIFE-030 — Preflight

Before Trash, validate exact LocalOwner + Workspace + Material scope.

If Material is already permanently deleted/not found, return stable not-found/deleted semantics without exposing cross-workspace metadata.

#### MATLIFE-031 — Reference Preview

Trash UI/application SHOULD have a read-only preview containing at least same-Workspace organization impact:

```yaml
material_id: uuid
workspace_id: uuid
current_lifecycle: active|trash
project_references:
  - project_id: uuid
    title: string
active_learning_reference_count: integer
warning_codes: [string]
```

Project references are informational: Trash does not remove them.

Permanent Delete uses the stronger Data Control preview defined below.

#### MATLIFE-032 — Atomic Material Transition

SYS01 Trash transaction MUST atomically persist:

- lifecycle `trash`；
- lifecycle version/timestamp/reason；
- idempotency receipt；
- outbox/job-control signal needed to hide/invalidate downstream projections。

It MUST NOT delete SourceFile in this transaction or afterward as part of ordinary Trash.

#### MATLIFE-033 — Late Job Guard

Every content/index/modeling job publish step MUST re-check current Material lifecycle or an exact generation token pinned to active lifecycle version.

A job started before Trash MAY finish computation, but MUST NOT publish learner-visible/search/retrieval current output if Material is no longer active.

### 6. Restore Command

#### MATLIFE-040 — Restore Preconditions

Restore requires:

- exact owner/workspace/material；
- current lifecycle `trash`；
- retained managed SourceFile or an explicit recoverable source state；
- no terminal Data Control permanent-delete workflow/checkpoint for this Material。

#### MATLIFE-041 — Source Verification

Before reporting restored Material ready for normal use, Askora MUST verify the retained managed SourceFile exists and its expected checksum/integrity is consistent where available.

If source is missing/corrupt:

- do not pretend restore succeeded to READY；
- return/record stable recovery state；
- preserve Trash until a safe recovery action succeeds, or explicitly restore metadata as non-ready only if the product contract can represent that state without hiding the loss。

#### MATLIFE-042 — Derived Rebuild

Restore MAY reuse exact valid immutable facts/projections only when current version/freshness/lifecycle dependency proves they remain valid. Otherwise mark derived artifacts stale/missing and schedule bounded local rebuild.

No online LLM is required merely to restore the Material identity/lifecycle; LLM-dependent derived stages can recover asynchronously under normal job semantics.

### 7. Search / Retrieval / Learning Visibility

#### MATLIFE-050 — Default Exclusion

Every default production query that can feed learning MUST exclude Trash:

- Library active list/search；
- RAG/SYS02 candidate generation；
- Knowledge publication/current source projection；
- Goal/Project material picker for new attachment/learning where inactive material is invalid；
- new LearningSession material attachment。

#### MATLIFE-051 — Explicit Trash Query

Trash is accessed only through explicit Trash/list/recovery query. Such query MAY expose safe metadata and project reference information but MUST NOT accidentally pass content into ordinary retrieval/LLM context.

#### MATLIFE-052 — Existing History

Trash does not delete historical learning facts. Existing LearningSession/Attempt/Evidence/Decision/History refs may continue to point to the trashed Material identity for audit/history, while current source rendering MAY show `source unavailable while in Trash` rather than reactivating content for retrieval.

### 8. Permanent Delete

#### MATLIFE-060 — Data Control Handoff

Permanent Delete MUST call/instantiate the canonical `DATA DOCUMENT` erasure workflow for the exact `workspace_id + material_id` target.

Library/SYS01 MUST NOT implement a parallel physical-delete cascade.

#### MATLIFE-061 — Strong Preview and Confirmation

Before permanent delete, use `ErasurePreviewV1` or a v1 LocalOwner-equivalent superseding contract to show at least:

- Material target；
- same-Workspace Project references；
- SourceFile/raw asset impact；
- knowledge/retrieval projection impact；
- Goal/Plan/Session/evidence/history categories affected or retained according to owner rules；
- backup/no-resurrection impact；
- irreversible warning；
- expiring confirmation token/digest。

Execution requires explicit confirmation + idempotency.

#### MATLIFE-062 — Fail-closed During Erasure

Once permanent-delete workflow is accepted, target Material must remain non-visible/non-retrievable while the workflow is running, partial or retryable failed.

UI MUST NOT restore it from Trash while a terminal erasure workflow controls the target.

#### MATLIFE-063 — SYS01 Owner Step

SYS01 permanent-delete owner step must remove/retire as applicable:

- managed SourceFile bytes；
- Material/current metadata content；
- MaterialRevision/DocumentIR/DocumentNode/SourceSpan/source-content facts that are exclusive to the Material；
- Material-owned library organization refs；
- ProjectMaterial memberships through the proper Project organization owner command；
- Material-owned duplicate/search/fingerprint projections or source facts；
- derived chunk/index/cache artifacts。

Shared KnowledgeUnit/relation provenance follows current Data Control rules: alternate valid provenance MAY preserve shared knowledge only after deleted provenance is removed and validity is re-established.

#### MATLIFE-064 — Other Owner Steps

Goal/Plan/Session/LearningEvidence/Decision/Outcome references are handled by their canonical owners according to Data Control. SYS01 MUST NOT directly delete their repository rows.

No implementation may leave a dangling current ref that causes a deleted Material to become retrievable or be reconstructed as source truth.

#### MATLIFE-065 — Physical Source Deletion Ordering

Physical managed SourceFile deletion occurs only inside the accepted permanent-delete/Data Control workflow after target scope has been durably fail-closed.

A file-delete failure keeps the workflow incomplete/partial and retriable; UI MUST NOT report permanent delete complete.

#### MATLIFE-066 — Completion

Permanent delete is complete only when:

- required owner steps/receipts are complete；
- managed SourceFile cleanup status is successful or explicitly covered by terminal safe policy；
- derived projections cannot recreate the source；
- erasure/no-resurrection checkpoint is advanced；
- final minimal receipt/tombstone exists；
- target cannot be restored through Trash。

### 9. Automatic Cleanup Policy

#### MATLIFE-070

v1 does **not** require automatic Trash purge. Default product-safe behavior is manual permanent delete unless a versioned local cleanup policy is explicitly enabled.

If automatic cleanup is enabled later/currently:

- retention duration MUST be versioned/configurable；
- due calculation MUST be local/deterministic；
- cleanup MUST execute the same Permanent Delete/Data Control workflow, not `rm` files directly；
- active/partial recovery/migration locks MAY postpone cleanup；
- cleanup result MUST be auditable without storing deleted content。

### 10. Legacy Migration

#### MATLIFE-080 — Legacy Fields

Current legacy fields include:

```text
is_deleted: bool
deleted_at: datetime|null
processing_status
storage_path
```

Migration MUST NOT assume `processing_status=FAILED` means deleted, because genuine processing failures also use FAILED.

#### MATLIFE-081 — Active Legacy Rows

`is_deleted=false` → `lifecycle=active`.

If managed source is unexpectedly missing/corrupt, record an independent source-integrity/recovery issue; do not classify it Trash/Deleted merely because storage is missing.

#### MATLIFE-082 — Legacy Deleted + Source Present

For `is_deleted=true` where the managed source still exists and matches known identity/checksum sufficiently:

```text
lifecycle → trash
trashed_at → legacy deleted_at when available
reason → LEGACY_DELETE_SOURCE_PRESENT migration reason
```

This row is restorable after normal SourceFile/current-revision reconciliation.

#### MATLIFE-083 — Legacy Deleted + Source Missing

For `is_deleted=true` where old behavior already removed the managed source:

- MUST NOT recreate content from stale derived chunks/index or older backup；
- classify as terminal legacy-deleted/tombstone state with reason `LEGACY_SOURCE_ALREADY_REMOVED` or stable equivalent；
- hide/invalidate source-derived current projections；
- preserve only historical learning facts that the legacy delete did not unambiguously authorize erasing；
- do not run a new broad destructive Data Control workflow by assumption；
- future restore is not offered because the durable SourceFile is gone and the user had already invoked delete under the old contract。

This migration classification records historical loss without inventing consent for additional deletion.

#### MATLIFE-084 — Legacy ProcessingStatus FAILED

If a legacy deleted row was forced to `processing_status=FAILED`, migration/restore MUST NOT simply set READY.

- new lifecycle is independent；
- restore validates SourceFile/current revision and reconstructible stage evidence；
- if prior processing state cannot be proven, use explicit non-ready/stale/partial/pending recovery semantics and schedule validation/rebuild；
- no guessed historical ready state。

#### MATLIFE-085 — Compatibility Retirement

After lifecycle cutover:

- `is_deleted/deleted_at` MAY be compatibility reads only for a bounded window；
- active writers MUST write canonical lifecycle/version；
- no permanent dual-write；
- old `DELETE /documents/{id}` compatibility endpoint MAY remain only if its semantics are changed to Trash and tests prove it never deletes SourceFile；
- compatibility fields/endpoints retire after current frontend/application consumers migrate。

### 11. API/Application Contract

#### MATLIFE-090 — Compatibility Trash Endpoint

For minimum breaking change, existing:

```text
DELETE /api/v1/documents/{material_id}
```

MAY be retained as the v1 compatibility command for **Trash only**.

Its implementation MUST NOT call physical file deletion. Response SHOULD expose safe lifecycle/version/result semantics rather than claiming permanent deletion.

#### MATLIFE-091 — Explicit Commands

Canonical application/API surface MUST provide equivalents of:

```text
PreviewMaterialDelete
TrashMaterial
ListTrash
RestoreMaterial
PreviewPermanentDelete
PermanentDeleteMaterial
GetPermanentDeleteStatus
```

Exact HTTP verbs/paths MAY follow repository conventions, but Trash and Permanent Delete MUST never share an ambiguous destructive command.

#### MATLIFE-092 — Stable Errors

At minimum distinguish:

```text
MATERIAL_NOT_FOUND
MATERIAL_WORKSPACE_SCOPE_VIOLATION
MATERIAL_ALREADY_TRASHED
MATERIAL_NOT_IN_TRASH
MATERIAL_SOURCE_MISSING
MATERIAL_DELETE_VERSION_CONFLICT
MATERIAL_PERMANENT_DELETE_CONFIRMATION_INVALID
MATERIAL_PERMANENT_DELETE_IN_PROGRESS
MATERIAL_PERMANENT_DELETE_PARTIAL
```

Raw path/DB/storage exceptions do not cross public API.

### 12. Backup / Recovery / No-resurrection

#### MATLIFE-100

Trash Material + SourceFile MUST be included in normal Askora recovery backup as durable recoverable state.

#### MATLIFE-101

After Permanent Delete completion, older managed backups/recovery points MUST obey Data Control erasure checkpoint. An unsafe old backup cannot silently restore the Material as active/trash.

#### MATLIFE-102

Projection rebuild MUST consume current lifecycle/erasure checkpoint and MUST NOT recreate permanently deleted SourceSpan/Knowledge provenance from stale cache/index/outbox artifacts.

### 13. Required Tests

#### MATLIFE-110 — Trash/Restore

- active → trash retains SourceFile bytes/checksum；
- ProjectMaterial memberships retained；
- default Library/RAG/new learning excludes Trash；
- explicit Trash list includes it；
- running job late publish rejected；
- restart preserves Trash；
- restore re-enables relationships only after source validation；
- restore rebuilds stale/missing derived artifacts；
- repeated commands idempotent；
- cross-workspace command rejected。

#### MATLIFE-111 — Permanent Delete

- preview is read-only and reference-aware；
- invalid/expired confirmation rejected；
- workflow target fail-closed while running/partial；
- SourceFile deletion only inside accepted permanent-delete workflow；
- file/owner-step failure does not report complete；
- derived projections cannot resurrect source；
- old backup no-resurrection；
- repeat command returns same workflow/report；
- SYS01 does not directly delete other-owner learning state。

#### MATLIFE-112 — Legacy Migration

Fixtures MUST cover:

```text
is_deleted=false + source present
is_deleted=false + source missing
is_deleted=true + source present
is_deleted=true + source missing
is_deleted=true + FAILED processing status
```

Migration must be idempotent and preserve stable Material IDs/provenance.

### 14. Acceptance Criteria

- `MATLIFE-AC-001`：ordinary delete changes active→trash and never physically deletes SourceFile.
- `MATLIFE-AC-002`：Trash survives restart/backup and Restore returns the exact same Material identity.
- `MATLIFE-AC-003`：ProjectMaterial membership survives Trash; removing Project relation never deletes Material.
- `MATLIFE-AC-004`：Trash cannot enter ordinary search/retrieval/new learning or late job publication.
- `MATLIFE-AC-005`：processing status is independent from lifecycle and Restore never guesses READY.
- `MATLIFE-AC-006`：Permanent Delete uses canonical Data Control `DOCUMENT` workflow with explicit preview/confirmation/idempotency.
- `MATLIFE-AC-007`：physical SourceFile deletion happens only during accepted Permanent Delete and incomplete cleanup is not reported successful.
- `MATLIFE-AC-008`：Permanent Delete advances no-resurrection evidence and cannot be undone by old backup/projection rebuild.
- `MATLIFE-AC-009`：legacy deleted rows with retained source become Trash; rows whose source was already removed become terminal legacy-deleted without reconstructing content or inventing broader erasure consent.
- `MATLIFE-AC-010`：existing compatibility DELETE endpoint, if retained, means Trash only and has an explicit retirement path.

### 15. Forbidden Implementations

禁止：

- ordinary Delete 调用 `storage.delete_file`；
- Trash 写 `processing_status=FAILED` 表示删除；
- Trash 删除 ProjectMaterial/Goal/history 以致 Restore 无法恢复组织上下文；
- Trash Material 进入 RAG/LLM context；
- running job 在 Trash 后继续 publish current knowledge/index；
- Restore 从 stale derived data 伪造丢失 SourceFile；
- SYS01 自行 cascade delete SYS03/SYS06/SYS08 state；
- Permanent Delete 绕过 Data Control/no-resurrection；
- legacy source-missing row 从旧 backup/cache 静默复活；
- automatic cleanup 直接删文件而不走 permanent-delete workflow；
- 使用 Project relation delete 冒充 Material delete。

### 16. Freeze Result

`MATLIFE-*`：**FROZEN / READY_FOR_IMPLEMENTATION**。

XIK-174 MAY 在本合同 + `LIB-*` + `PERSIST-*` + current Data Control 下实施。若实现要求改变 Product Positioning 两阶段删除、重新定义 DOCUMENT erasure ownership 或把普通 Trash 变成不可恢复删除，必须停止并返回上游，不得由 Codex自行决定。

---

## Askora Data Control and Recovery Contract

> Spec ID：`DATA-*`
> 状态：FROZEN
> 版本：1.0
> Owner boundary：Infrastructure control artifacts + owner-coordinated commands；不建立第九个业务 owner
> Governing decision：ADR-0103

### 1. Scope

#### DATA-001 — Supported Product Mode

P1-03 v1 MUST 支持 macOS 私人桌面 SQLite。服务模式/PostgreSQL MUST 明确返回 unsupported adapter，MUST NOT 使用 SQLite 文件逻辑或在 UI 显示已受保护。

#### DATA-002 — Capability Separation

以下是四个独立合同：

```text
Recovery Package  = encrypted lossless Askora restore input
User Data Export  = readable current-user portability artifact
Erasure Workflow  = owner-coordinated destructive command
Recovery Report   = non-sensitive verification/control evidence
```

User Data Export MUST NOT 被直接导入为 canonical state；Recovery Package MUST NOT 被描述为人类可读导出。

### 2. Recovery Key

#### DATA-010

首次启用数据保护时 MUST 创建至少 256-bit 独立随机 Recovery Key。设备保存副本 MUST 通过 platform secure storage 封装；明文 key MUST NOT 写入恢复包、catalog、日志、命令行参数、localStorage 或普通导出。

#### DATA-011

用户 MUST 能显式查看/保存 recovery key，并被告知丢失 key 时跨设备恢复不可行。同设备自动备份 MAY 使用 platform-unwrapped key；跨设备恢复 MUST 要求用户提供 key。

### 3. Recovery Package V1

#### DATA-020 — Container

`askora-recovery/1.0` MUST 使用分块 authenticated encryption。每个 chunk 使用唯一 nonce；header/version 作为 authenticated data。任何 chunk tamper、truncation、reorder、unknown major 或错误 key MUST 在解压/激活前失败。

#### DATA-021 — Manifest

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

#### DATA-022 — Included Data

MUST 包含 consistent SQLite snapshot、受管 raw document assets、当前 erasure checkpoint 与恢复数据库加密字段所需 KEK material。MUST NOT 包含 provider API key、logs、Redis/cache、临时文件或未受管宿主路径。

KEK 必须原样恢复，否则受保护数据不可读。

#### DATA-023 — Limits

文件数量、单文件大小、总明文大小、chunk size 与解压比例 MUST 使用 versioned configurable limits；超限在写入目标路径前 fail closed。默认预算至少覆盖产品允许的 2 GiB document quota，但不得无上限。

### 4. Backup Lifecycle

#### DATA-030

状态固定为：

```text
CREATING → VERIFYING → VERIFIED
CREATING/VERIFYING → FAILED
VERIFIED → INVALIDATED|PURGED
```

只有重新打开容器、校验 AEAD/manifest/file hashes/SQLite integrity 成功后可进入 VERIFIED。临时文件 MUST 原子 rename 后才进入 catalog。

#### DATA-031 — Maintenance Boundary

桌面 backup MUST 在普通 backend 与 worker 停止写入后执行。maintenance process 以独占锁保护同一 userData root；无法取得锁返回 `DATA_MAINTENANCE_BUSY`，不得并发复制。

#### DATA-032 — Retention

默认保留 7 daily、4 weekly、6 monthly。最后一个 VERIFIED、最新 PRE_MIGRATION、PRE_RESTORE 与 POST_ERASURE MUST protected。Retention 只删除 catalog 已验证且不受保护的明确路径；不得使用未解析 glob 或删除 userData root。

#### DATA-033 — Schedule

桌面 SHOULD 在距最近 VERIFIED 超过 24 小时后的安全启动/退出窗口创建 SCHEDULED recovery point。失败记录稳定原因并在设置页告警；不得阻止普通启动。PRE_MIGRATION 失败 MUST 阻止 migration。

### 5. Verification and Restore

#### DATA-040 — Verify

Verify MUST 覆盖：container auth、manifest schema、path/size limits、每个文件 hash/size、SQLite `quick_check`/`foreign_key_check`、数据库 schema revision presence/compatibility、required raw asset presence。

#### DATA-041 — Staging Restore

Restore MUST 解密到新建的 private staging directory；MUST NOT 直接解压或写入 active database/documents。staging 通过 verification 后才 MAY forward migrate。

#### DATA-042 — Schema Compatibility

- same/current supported revision → continue；
- older supported revision → deterministic Alembic forward migration in staging；
- future/unknown/multiple heads/missing required migration → `DATA_RESTORE_SCHEMA_UNSUPPORTED`；
- migration failure → current active data unchanged。

Restore MUST NOT 使用 downgrade 破坏新数据，也不得用 `create_all` 猜迁移后的历史 schema。

#### DATA-043 — Reconciliation

激活前至少验证：SQLite integrity/FK；每个 non-deleted UserDocument 的受管文件存在且 checksum 匹配；deleted/quarantined visibility；outbox running task recovery；current erasure checkpoint；registered user-data binding coverage；projection source revision/version 可用。

可重建 projection MAY 标 stale 并在激活后 rebuild；canonical facts MUST NOT 通过在线 LLM 重新生成或用 current state 猜历史。

#### DATA-044 — Atomic Activation and Rollback

激活前 MUST 创建 VERIFIED PRE_RESTORE rescue point。active DB/documents/secrets 通过同一 maintenance transaction journal 切换；crash recovery 根据 journal 完成或回滚，MUST NOT 留半套数据。激活后 readiness 失败 MUST 自动恢复 rescue point并报告 `DATA_RESTORE_FAILED_ROLLED_BACK`。

#### DATA-045 — Report

`RecoveryReportV1` MUST 包含 report/backup id、阶段状态、schema before/after、校验计数、projection actions、erasure checkpoint、started/completed_at、稳定 reason codes；MUST NOT 包含原文、secret、Prompt、完整本地路径。

### 6. Migration Guard

#### DATA-050

任何可能改变或删除用户数据的 desktop migration MUST 在 active data 上执行前：

1. 识别 current DB revision；
2. 创建 VERIFIED PRE_MIGRATION point；
3. 在 staging copy 执行 migration 与 validation；
4. 成功后 atomic activate；
5. 失败保持 current data 并显示报告。

### 7. User Data Export V1

#### DATA-060 — Envelope

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

#### DATA-061 — Current-user and Allowlist

Export MUST 由 LocalOwner-scoped command 创建（Askora 无登录认证）。字段/实体采用显式 allowlist，MUST NOT 使用 `SELECT *` 或 ORM automatic serialization。每项保留 owner/source/version 或 `LEGACY_COMPATIBILITY`。

#### DATA-062 — Exclusions

MUST 排除 KEK/Recovery Key/provider key、内部 Prompt/system instructions、grader-only answer/rubric、未经选择的完整文档、其他 owner 数据、本地绝对路径、stack trace。

#### DATA-063 — Delivery

导出临时文件使用 private permissions、短期 expiry、一次性短期本地交付凭证；下载完成或 expiry 后安全清理。导出失败不得生成 partial artifact 并声称完成。

### 8. Erasure Workflow V1

#### DATA-070 — Scope

```text
DOCUMENT
LEARNING_RECORDS
MODEL_EXECUTION
ALL_PERSONAL_DATA
```

Scope 语义不得由客户端自由组合。未来新增 scope 必须升合同版本或 additive enum 并冻结影响矩阵。

#### DATA-071 — Preview

执行前 MUST 返回 `ErasurePreviewV1`：current-user、scope/target ref、每 owner 预计影响计数、共享 provenance 处理、backup impact、不可逆说明、expiring confirmation token。Preview MUST read-only，token 与 preview digest/user/scope/expiry 绑定。

#### DATA-072 — Confirmation and Idempotency

执行必须使用 preview token + idempotency key + explicit confirmation phrase。过期、digest/owner/scope 不匹配、重复但 payload 不同必须拒绝。重复相同 command 返回同一 workflow/report。

#### DATA-073 — Ownership

Erasure coordinator MUST 通过 owner command/adapter 执行；不得直接 patch 其他 owner canonical state。每个 owner step durable、idempotent、可重试并记录最小 result。执行期间 target scope MUST fail closed/invisible。

#### DATA-074 — Document Erasure

DOCUMENT 必须处理 raw asset、UserDocument/SourceSpan/DocumentIR、exclusive KnowledgeUnit/relation provenance、retrieval projection、goal mapping/plan refs、evidence/event/inference refs。存在 alternate valid provenance 的 shared knowledge MAY 保留，但必须移除被删 provenance 并重新验证；无法安全分类时 fail closed，不得继续发布。

#### DATA-075 — Learning and Execution Erasure

LEARNING_RECORDS 必须处理 dialog/transcript、Attempt/AssessmentResult、LearnerEvidence/Mastery/LearnerState、Goal/Plan/Activity、ReviewSchedule、related events/decisions/outcomes，并重建空/剩余 projection。MODEL_EXECUTION 只处理可归属当前用户的 inference/transcript/execution metadata；不能证明归属的全局 policy/config 不得删除。

ALL_PERSONAL_DATA 还必须处理 profile/document storage 等本地数据；Askora 无账号认证撤销（见 `identity-privacy-lifecycle.md` LID-061）。

#### DATA-076 — Tombstone and No Resurrection

成功后写不含内容的 `ErasureReceiptV1` 与单调 `ErasureCheckpointV1`。Restore/rebuild MUST 应用 checkpoint，MUST NOT 引用或重新生成被删事实。早于 checkpoint 且无法安全过滤的 managed recovery points 必须 INVALIDATED/PURGED；随后创建 VERIFIED POST_ERASURE baseline。

#### DATA-077 — Partial Failure

任一 step 失败时 workflow 为 `FAILED_RETRYABLE|FAILED_TERMINAL|PARTIAL`；target scope 保持不可见。UI 不得显示“删除完成”。Retry 只执行未完成的幂等 step；最终报告列出 owner/status/reason，不含被删内容。

#### DATA-078 — Destructive Confirmation (no account)

Askora 无账号删除（见 `identity-privacy-lifecycle.md` LID-061）。全量本地清除（Reset Local Workspace）与 scoped erasure 统一使用本工作流（DATA-070..077）。确认 MUST 使用 preview + expiring confirmation + typed phrase + idempotency key，不得要求 password 或引入 account-deletion 状态机（LID-062）。`data_erasure_workflows`、`data_erasure_steps`、`data_erasure_receipts` 与 `data_erasure_checkpoints` 是唯一执行 truth。

### 9. API / IPC

#### DATA-080

Backend current-user API 负责 status/query、export、erasure preview/confirm/report。Desktop IPC 负责 recovery key、native file chooser、backend stop/start、maintenance backup/verify/restore 与 progress。IPC 使用固定 allowlist typed payload；renderer 不获得 filesystem、shell 或 arbitrary argv 权限。

#### DATA-081

恢复/备份进行中普通 UI 进入 maintenance 状态；不得继续提交学习写入。Restore success 后清除本地前端缓存；Askora 无登录流程。

### 10. Stable Errors

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

### 11. Tests

必须覆盖 L0～L5：contracts/version/errors；crypto/tamper/limits/path；SQLite snapshot/integrity/FK；migration staging/rollback；file reconciliation；export allowlist/secret leakage；four erasure scopes/owner/idempotency/partial recovery/no resurrection；Electron IPC/packaged maintenance；frontend states/accessibility；真实桌面 backup→mutate→restore→verify。

### 12. Acceptance Criteria

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

### 13. Forbidden Implementations

禁止：普通 `copytree` 冒充一致备份；明文或自包含 key 备份；恢复直接覆盖 active path；unknown schema `create_all`；在线 LLM replay；export `SELECT *`；跨 owner ORM hard delete；删除后保留可激活旧 managed backup；renderer 任意 filesystem/shell；仅 Mock/单元测试宣称 P1-03 DONE。
