# Material Trash, Restore and Permanent Delete Contract

> Spec ID：`MATLIFE-*`  
> 状态：**Canonical Implementation Contract / FROZEN**  
> 版本：v1.0  
> 冻结日期：2026-08-10  
> Governing：`docs/product/PRODUCT-POSITIONING.md`、`LIB-045/046`、`PERSIST-080..083`、`DATA-070..077`、ADR-0016  
> Linear：XIK-170

## 1. Purpose

本合同只补齐 v1 已冻结的：

```text
active
→ trash
→ permanent delete
```

的 command、migration、SourceFile、Project reference、derived-data、job、restore 与 no-resurrection 实现语义。

它不建立新的产品级删除模型，不替代 P1-03 Data Control，也不改变 Material/SYS01/Workspace 的 ownership。

## 2. Ownership and Boundary

### MATLIFE-001 — Material Lifecycle Writer

Material current lifecycle (`active|trash`) 由 SYS01 Material owner 写入。

Permanent Delete 的跨 owner 物理清理由 canonical Data Control `DOCUMENT` erasure workflow 协调；SYS01 只执行其 owner step，不得直接越权删除 SYS03/SYS06/SYS08 等其他 owner 状态。

### MATLIFE-002 — Relationship Removal Is Not Material Delete

```text
RemoveFromProject(project_id, material_id)
→ delete ProjectMaterial relationship only

TrashMaterial(material_id)
→ Material lifecycle active → trash

PermanentDeleteMaterial(material_id)
→ confirmed DATA DOCUMENT workflow
```

三者 MUST 是不同 command/receipt/telemetry 语义。

### MATLIFE-003 — Processing Status Is Orthogonal

Material lifecycle MUST NOT 复用：

- `processing_status=FAILED`；
- parser/index status；
- quarantine status；
- Project membership；
- UI hidden flag。

Trash does not mean processing failed. New Trash/Restore commands MUST NOT mutate processing status merely to express lifecycle.

## 3. Canonical Lifecycle

### MATLIFE-010 — Active

`active` Material MAY participate in ordinary Library search, retrieval, Project learning, new LearningSession and background processing subject to normal safety/readiness rules.

### MATLIFE-011 — Trash

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

### MATLIFE-012 — Restore

Restore is allowed only from `trash` and returns Material to `active`.

Restore MUST NOT fabricate processing readiness. Existing valid durable content/revision facts remain, but any removed/stale derived projection is rebuilt/validated under current versioned pipeline before being advertised READY.

ProjectMaterial memberships retained through Trash automatically become effective again when Material is active; Restore does not recreate guessed relationships.

### MATLIFE-013 — Permanent Deleted

Permanent deletion is terminal for the recoverable Material.

`deleted` is a logical terminal state represented only by the minimum tombstone/erasure receipt/checkpoint needed for idempotency, audit and no-resurrection. It MUST NOT retain user content merely to keep a Material row looking populated.

A permanently deleted Material cannot be restored through Trash. Recovery from an older backup MUST obey the erasure checkpoint and MUST NOT resurrect it.

## 4. Lifecycle Record

### MATLIFE-020

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

### MATLIFE-021 — Optimistic Concurrency

Trash/Restore commands MUST include expected lifecycle/material version and idempotency key. Stale expected version returns explicit conflict; no last-write-wins.

### MATLIFE-022 — Idempotent Repeats

- Trash already trashed + same idempotency/payload → return original result；
- Restore already restored + same idempotency/payload → return original result；
- same idempotency key + different target/payload → conflict；
- permanent delete repeat uses canonical Data Control workflow idempotency and returns same safe report/result。

## 5. Trash Command

### MATLIFE-030 — Preflight

Before Trash, validate exact LocalOwner + Workspace + Material scope.

If Material is already permanently deleted/not found, return stable not-found/deleted semantics without exposing cross-workspace metadata.

### MATLIFE-031 — Reference Preview

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

### MATLIFE-032 — Atomic Material Transition

SYS01 Trash transaction MUST atomically persist:

- lifecycle `trash`；
- lifecycle version/timestamp/reason；
- idempotency receipt；
- outbox/job-control signal needed to hide/invalidate downstream projections。

It MUST NOT delete SourceFile in this transaction or afterward as part of ordinary Trash.

### MATLIFE-033 — Late Job Guard

Every content/index/modeling job publish step MUST re-check current Material lifecycle or an exact generation token pinned to active lifecycle version.

A job started before Trash MAY finish computation, but MUST NOT publish learner-visible/search/retrieval current output if Material is no longer active.

## 6. Restore Command

### MATLIFE-040 — Restore Preconditions

Restore requires:

- exact owner/workspace/material；
- current lifecycle `trash`；
- retained managed SourceFile or an explicit recoverable source state；
- no terminal Data Control permanent-delete workflow/checkpoint for this Material。

### MATLIFE-041 — Source Verification

Before reporting restored Material ready for normal use, Askora MUST verify the retained managed SourceFile exists and its expected checksum/integrity is consistent where available.

If source is missing/corrupt:

- do not pretend restore succeeded to READY；
- return/record stable recovery state；
- preserve Trash until a safe recovery action succeeds, or explicitly restore metadata as non-ready only if the product contract can represent that state without hiding the loss。

### MATLIFE-042 — Derived Rebuild

Restore MAY reuse exact valid immutable facts/projections only when current version/freshness/lifecycle dependency proves they remain valid. Otherwise mark derived artifacts stale/missing and schedule bounded local rebuild.

No online LLM is required merely to restore the Material identity/lifecycle; LLM-dependent derived stages can recover asynchronously under normal job semantics.

## 7. Search / Retrieval / Learning Visibility

### MATLIFE-050 — Default Exclusion

Every default production query that can feed learning MUST exclude Trash:

- Library active list/search；
- RAG/SYS02 candidate generation；
- Knowledge publication/current source projection；
- Goal/Project material picker for new attachment/learning where inactive material is invalid；
- new LearningSession material attachment。

### MATLIFE-051 — Explicit Trash Query

Trash is accessed only through explicit Trash/list/recovery query. Such query MAY expose safe metadata and project reference information but MUST NOT accidentally pass content into ordinary retrieval/LLM context.

### MATLIFE-052 — Existing History

Trash does not delete historical learning facts. Existing LearningSession/Attempt/Evidence/Decision/History refs may continue to point to the trashed Material identity for audit/history, while current source rendering MAY show `source unavailable while in Trash` rather than reactivating content for retrieval.

## 8. Permanent Delete

### MATLIFE-060 — Data Control Handoff

Permanent Delete MUST call/instantiate the canonical `DATA DOCUMENT` erasure workflow for the exact `workspace_id + material_id` target.

Library/SYS01 MUST NOT implement a parallel physical-delete cascade.

### MATLIFE-061 — Strong Preview and Confirmation

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

### MATLIFE-062 — Fail-closed During Erasure

Once permanent-delete workflow is accepted, target Material must remain non-visible/non-retrievable while the workflow is running, partial or retryable failed.

UI MUST NOT restore it from Trash while a terminal erasure workflow controls the target.

### MATLIFE-063 — SYS01 Owner Step

SYS01 permanent-delete owner step must remove/retire as applicable:

- managed SourceFile bytes；
- Material/current metadata content；
- MaterialRevision/DocumentIR/DocumentNode/SourceSpan/source-content facts that are exclusive to the Material；
- Material-owned library organization refs；
- ProjectMaterial memberships through the proper Project organization owner command；
- Material-owned duplicate/search/fingerprint projections or source facts；
- derived chunk/index/cache artifacts。

Shared KnowledgeUnit/relation provenance follows current Data Control rules: alternate valid provenance MAY preserve shared knowledge only after deleted provenance is removed and validity is re-established.

### MATLIFE-064 — Other Owner Steps

Goal/Plan/Session/LearningEvidence/Decision/Outcome references are handled by their canonical owners according to Data Control. SYS01 MUST NOT directly delete their repository rows.

No implementation may leave a dangling current ref that causes a deleted Material to become retrievable or be reconstructed as source truth.

### MATLIFE-065 — Physical Source Deletion Ordering

Physical managed SourceFile deletion occurs only inside the accepted permanent-delete/Data Control workflow after target scope has been durably fail-closed.

A file-delete failure keeps the workflow incomplete/partial and retriable; UI MUST NOT report permanent delete complete.

### MATLIFE-066 — Completion

Permanent delete is complete only when:

- required owner steps/receipts are complete；
- managed SourceFile cleanup status is successful or explicitly covered by terminal safe policy；
- derived projections cannot recreate the source；
- erasure/no-resurrection checkpoint is advanced；
- final minimal receipt/tombstone exists；
- target cannot be restored through Trash。

## 9. Automatic Cleanup Policy

### MATLIFE-070

v1 does **not** require automatic Trash purge. Default product-safe behavior is manual permanent delete unless a versioned local cleanup policy is explicitly enabled.

If automatic cleanup is enabled later/currently:

- retention duration MUST be versioned/configurable；
- due calculation MUST be local/deterministic；
- cleanup MUST execute the same Permanent Delete/Data Control workflow, not `rm` files directly；
- active/partial recovery/migration locks MAY postpone cleanup；
- cleanup result MUST be auditable without storing deleted content。

## 10. Legacy Migration

### MATLIFE-080 — Legacy Fields

Current legacy fields include:

```text
is_deleted: bool
deleted_at: datetime|null
processing_status
storage_path
```

Migration MUST NOT assume `processing_status=FAILED` means deleted, because genuine processing failures also use FAILED.

### MATLIFE-081 — Active Legacy Rows

`is_deleted=false` → `lifecycle=active`.

If managed source is unexpectedly missing/corrupt, record an independent source-integrity/recovery issue; do not classify it Trash/Deleted merely because storage is missing.

### MATLIFE-082 — Legacy Deleted + Source Present

For `is_deleted=true` where the managed source still exists and matches known identity/checksum sufficiently:

```text
lifecycle → trash
trashed_at → legacy deleted_at when available
reason → LEGACY_DELETE_SOURCE_PRESENT migration reason
```

This row is restorable after normal SourceFile/current-revision reconciliation.

### MATLIFE-083 — Legacy Deleted + Source Missing

For `is_deleted=true` where old behavior already removed the managed source:

- MUST NOT recreate content from stale derived chunks/index or older backup；
- classify as terminal legacy-deleted/tombstone state with reason `LEGACY_SOURCE_ALREADY_REMOVED` or stable equivalent；
- hide/invalidate source-derived current projections；
- preserve only historical learning facts that the legacy delete did not unambiguously authorize erasing；
- do not run a new broad destructive Data Control workflow by assumption；
- future restore is not offered because the durable SourceFile is gone and the user had already invoked delete under the old contract。

This migration classification records historical loss without inventing consent for additional deletion.

### MATLIFE-084 — Legacy ProcessingStatus FAILED

If a legacy deleted row was forced to `processing_status=FAILED`, migration/restore MUST NOT simply set READY.

- new lifecycle is independent；
- restore validates SourceFile/current revision and reconstructible stage evidence；
- if prior processing state cannot be proven, use explicit non-ready/stale/partial/pending recovery semantics and schedule validation/rebuild；
- no guessed historical ready state。

### MATLIFE-085 — Compatibility Retirement

After lifecycle cutover:

- `is_deleted/deleted_at` MAY be compatibility reads only for a bounded window；
- active writers MUST write canonical lifecycle/version；
- no permanent dual-write；
- old `DELETE /documents/{id}` compatibility endpoint MAY remain only if its semantics are changed to Trash and tests prove it never deletes SourceFile；
- compatibility fields/endpoints retire after current frontend/application consumers migrate。

## 11. API/Application Contract

### MATLIFE-090 — Compatibility Trash Endpoint

For minimum breaking change, existing:

```text
DELETE /api/v1/documents/{material_id}
```

MAY be retained as the v1 compatibility command for **Trash only**.

Its implementation MUST NOT call physical file deletion. Response SHOULD expose safe lifecycle/version/result semantics rather than claiming permanent deletion.

### MATLIFE-091 — Explicit Commands

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

### MATLIFE-092 — Stable Errors

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

## 12. Backup / Recovery / No-resurrection

### MATLIFE-100

Trash Material + SourceFile MUST be included in normal Askora recovery backup as durable recoverable state.

### MATLIFE-101

After Permanent Delete completion, older managed backups/recovery points MUST obey Data Control erasure checkpoint. An unsafe old backup cannot silently restore the Material as active/trash.

### MATLIFE-102

Projection rebuild MUST consume current lifecycle/erasure checkpoint and MUST NOT recreate permanently deleted SourceSpan/Knowledge provenance from stale cache/index/outbox artifacts.

## 13. Required Tests

### MATLIFE-110 — Trash/Restore

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

### MATLIFE-111 — Permanent Delete

- preview is read-only and reference-aware；
- invalid/expired confirmation rejected；
- workflow target fail-closed while running/partial；
- SourceFile deletion only inside accepted permanent-delete workflow；
- file/owner-step failure does not report complete；
- derived projections cannot resurrect source；
- old backup no-resurrection；
- repeat command returns same workflow/report；
- SYS01 does not directly delete other-owner learning state。

### MATLIFE-112 — Legacy Migration

Fixtures MUST cover:

```text
is_deleted=false + source present
is_deleted=false + source missing
is_deleted=true + source present
is_deleted=true + source missing
is_deleted=true + FAILED processing status
```

Migration must be idempotent and preserve stable Material IDs/provenance.

## 14. Acceptance Criteria

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

## 15. Forbidden Implementations

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

## 16. Freeze Result

`MATLIFE-*`：**FROZEN / READY_FOR_IMPLEMENTATION**。

XIK-174 MAY 在本合同 + `LIB-*` + `PERSIST-*` + current Data Control 下实施。若实现要求改变 Product Positioning 两阶段删除、重新定义 DOCUMENT erasure ownership 或把普通 Trash 变成不可恢复删除，必须停止并返回上游，不得由 Codex自行决定。
