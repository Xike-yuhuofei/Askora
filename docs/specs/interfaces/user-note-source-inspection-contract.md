# Askora UserNote and Source Inspection Contract

> Spec ID：`UNSI-*`
> 状态：**Canonical Implementation Contract / FROZEN**
> 版本：v1.0
> 冻结日期：2026-08-11
> Governing：Product Definition、ADR-0021
> Implementation sequence：EXEC-076 Backend Foundation → EXEC-070 Frontend Right Rail

## 1. Scope and Authority

本合同冻结 EXEC-070 所需的两个技术边界：

1. Workspace-scoped durable `UserNote` 的 owner、query、save/version/conflict/recovery/data-control；
2. citation/view-source 使用 exact Material/MaterialRevision/SourceSpan refs 打开 Current Material 的 read-only source-inspection handoff。

本合同不新增 Product Capability，不改变 SYS01～SYS08 Learning Core ownership，不实现 global notes library，不启用 `CAPTURE_NOTE`，不修改 Teaching Policy、Assessment、Mastery、Review 或 Learning Evidence semantics。

## 2. Ownership

### UNSI-001 — UserNote single writer

`UserNote`、`UserNoteVersion`、`UserNoteRecoveryDraft` 与 save/recovery receipt 的唯一 writer 是 **Platform Workspace Notes**。

API handler、query assembler、frontend store、LCMS/SYS08、SYS01/SYS02 与 local browser storage MUST NOT 写第二份 current UserNote truth。

### UNSI-002 — Source single writer

Material content semantics、MaterialRevision 与 SourceSpan 的唯一 writer仍为 SYS01。SYS02 只拥有 EvidenceBundle/RetrievalTrace。Source-inspection query 只读组合，不创建/修正/回填 source truth。

### UNSI-003 — Workspace scope

所有 UserNote 与 source inspection 必须解析 current LocalOwner + current `workspace_id`。`owner_id` 相同不得替代 workspace filter。foreign 与 missing resource 对 caller 保持不可枚举。

## 3. Common Public References

### UNSI-010 — Exact owner ref

本合同复用 LCMS `VersionedOwnerRefV1` 语义：

```yaml
versioned_owner_ref:
  source_system: SYS01|SYS02|SYS05|SYS06|PLATFORM
  entity_type: string
  entity_id: string
  version: string|integer
  workspace_id: uuid
  availability: READY|MISSING|STALE
```

`READY` 必须有 exact entity id/version/workspace。客户端不得把 nullable id、display label、filename、route 或 current mutable state转换为 READY ref。

### UNSI-011 — Source inspection ref

```yaml
SourceInspectionRefV1:
  schema_version: "1.0"
  material_ref: versioned_owner_ref       # entity_type=Material
  material_revision_ref: versioned_owner_ref # entity_type=MaterialRevision
  source_span_ref: versioned_owner_ref|null   # entity_type=SourceSpan
```

三个 ref 如同时存在，MUST 属于同一 Workspace、同一 Material lineage与 exact revision。`source_span_ref=null` 只能表示没有可定位 SourceSpan，不能由客户端猜一个 current span。

## 4. UserNote Domain Contract

### UNSI-020 — UserNoteV1

```yaml
UserNoteV1:
  schema_version: "1.0"
  note_ref: versioned_owner_ref           # PLATFORM/UserNote
  note_id: uuid
  workspace_id: uuid
  anchor: UserNoteAnchorV1
  content_markdown: string                # 0..65536 UTF-8 characters
  version: integer                        # >= 1
  created_at: datetime
  updated_at: datetime
  unresolved_recovery_ref: versioned_owner_ref|null
```

`content_markdown` 是 user-authored content；空内容 MAY durable 保存，但不得被解释为不存在或自动删除。Renderer 使用 safe Markdown/plain-text allowlist，禁止 raw HTML/MDX/script/dynamic component。

### UNSI-021 — UserNoteAnchorV1

```yaml
UserNoteAnchorV1:
  schema_version: "1.0"
  kind: LEARNING_ACTIVITY|STAGE|MATERIAL|SOURCE_SPAN|FREE
  anchor_ref: versioned_owner_ref|null
  source_ref: SourceInspectionRefV1|null
```

合法组合：

| kind | required | forbidden |
|---|---|---|
| `LEARNING_ACTIVITY` | exact SYS06 LearningActivity `anchor_ref` | `source_ref` |
| `STAGE` | exact SYS05 TeachingAction `anchor_ref` | `source_ref` |
| `MATERIAL` | `source_ref.material_ref`；revision/span MAY null only through a Material-only form | unrelated `anchor_ref` |
| `SOURCE_SPAN` | exact Material + MaterialRevision + SourceSpan `source_ref` | unrelated `anchor_ref` |
| `FREE` | no owner/source ref | any ref |

Material-only anchor的 wire representation使用 `SourceInspectionRefV1` 的 material ref，并以 explicit null revision/span compatibility shape由 strict validator约束；实现不得用 fake revision/version 填空。若实现选择独立 `MaterialAnchorV1` discriminated subtype，公共语义不变。

创建后 anchor identity immutable。未来 re-anchor 必须是独立 command/version，不得由普通 save/autosave 隐式改变。

### UNSI-022 — Query

```text
GET /api/v1/workspace/user-notes
  ?anchor_kind=<required>
  &anchor_id=<required except FREE>
  &anchor_version=<required for versioned anchor>
  &material_id=<required for MATERIAL/SOURCE_SPAN>
  &revision_id=<required for SOURCE_SPAN>
  &source_span_id=<required for SOURCE_SPAN>
  &cursor=<optional>
  &limit=<optional, 1..50>
```

返回 `UserNoteListResponseV1`：strict 1.0 envelope、current Workspace、exact normalized anchor、稳定 `(updated_at desc, note_id asc)` ordering、cursor 与 0..N `UserNoteV1`。Query MUST NOT 跨 anchor/global Workspace 聚合；`FREE` 只查询 current Workspace FREE notes。

```text
GET /api/v1/workspace/user-notes/{note_id}
```

返回 exact current note与 unresolved recovery ref；foreign/missing 使用同一 not-found外观。两类 query 均 `Cache-Control: private, no-store`、side-effect free、no LLM。

## 5. Save, Version and Idempotency

### UNSI-030 — SaveUserNoteV1

```text
PUT /api/v1/workspace/user-notes/{note_id}
```

```yaml
SaveUserNoteV1:
  schema_version: "1.0"
  workspace_id: uuid
  anchor: UserNoteAnchorV1
  content_markdown: string
  expected_version: integer               # create=0, update>=1
  idempotency_key: string
```

Rules：

- `note_id` 由 client 预先生成并保持稳定；
- create 仅允许不存在 note + `expected_version=0`；
- update 必须匹配 current exact version、Workspace 与 immutable anchor；
- accepted save 在一个 SQLite transaction 中 append `UserNoteVersion`、更新 current aggregate并保存 receipt；
- version 每次 semantic content change +1；相同 idempotency key/payload返回原 result，不增加 version；
- 相同 idempotency key但 payload不同返回 non-retryable conflict；
- 禁止 HTTP timestamp/updated_at/client clock/last-write-wins 决定胜者。

### UNSI-031 — UserNoteSaveResultV1

```yaml
UserNoteSaveResultV1:
  schema_version: "1.0"
  status: CREATED|UPDATED|ALREADY_APPLIED
  note: UserNoteV1
  receipt_ref: versioned_owner_ref        # PLATFORM/UserNoteSaveReceipt
  correlation_id: string
```

只有收到该 durable owner result（或随后 query 得到同一/更新 exact note ref）才能显示 `SAVED`。Transport 200/204、local debounce completion 或 browser state mutation都不是保存证据。

### UNSI-032 — Autosave ordering

同一 note autosave必须 single-flight：

```text
dirty(vN)
→ SAVING(expected=N)
→ owner result vN+1
→ SAVED(vN+1)
```

若请求期间产生较新 draft，frontend 保留 dirty generation，在前一请求完成后以返回 version 提交下一次；不得并发发送两个相同 expected version后让最后到达者获胜。Retry 必须复用原 idempotency key；内容变化创建新 key。

## 6. Conflict and Recovery

### UNSI-040 — Durable conflict result

expected version不匹配时 owner MUST：

1. 不修改 current UserNote；
2. 幂等持久化 submitted content 为 `UserNoteRecoveryDraftV1`；
3. 返回 HTTP 409 + `USER_NOTE_VERSION_CONFLICT`；
4. 在 typed `error.details` 返回 `UserNoteConflictV1`。

```yaml
UserNoteConflictV1:
  schema_version: "1.0"
  current_note: UserNoteV1
  submitted_expected_version: integer
  recovery_ref: versioned_owner_ref       # PLATFORM/UserNoteRecoveryDraft
  correlation_id: string
```

### UNSI-041 — Recovery draft

```yaml
UserNoteRecoveryDraftV1:
  schema_version: "1.0"
  recovery_ref: versioned_owner_ref
  note_id: uuid
  workspace_id: uuid
  anchor: UserNoteAnchorV1
  submitted_content_markdown: string
  submitted_expected_version: integer
  status: UNRESOLVED|RESOLVED_KEEP_CURRENT|RESOLVED_REPLACED|RESOLVED_MERGED|ERASED
  created_at: datetime
  resolved_at: datetime|null
```

Recovery draft 是 durable user content，但不是 current note。Restart/refresh 后 query 必须能恢复 unresolved draft；backup/export/erasure 与 note content使用同等保护。

### UNSI-042 — ResolveUserNoteRecoveryV1

```text
POST /api/v1/workspace/user-notes/{note_id}/recoveries/{recovery_id}/resolve
```

```yaml
ResolveUserNoteRecoveryV1:
  schema_version: "1.0"
  workspace_id: uuid
  action: KEEP_CURRENT|REPLACE_WITH_DRAFT|SAVE_MERGED
  expected_current_version: integer
  merged_content_markdown: string|null
  idempotency_key: string
```

- `KEEP_CURRENT` 要求 merged content null，只解决 recovery；
- `REPLACE_WITH_DRAFT` 使用 recovery content，merged content null；
- `SAVE_MERGED` 必须提供用户确认后的 merged content；
- replace/merge追加新 note version并返回 durable receipt；
- current version再次变化返回409，recovery仍 unresolved；
- owner不得自动选择、自动 merge 或静默丢弃任何一侧。

### UNSI-043 — UI state truth

| UI state | Required evidence |
|---|---|
| `SAVING` | one owner request in flight |
| `SAVED` | durable owner receipt/exact returned note ref |
| `FAILED` | no accepted owner receipt；dirty input retained in current UI process |
| `CONFLICT` | typed 409 + current note + durable recovery ref |
| `RECOVERABLE` | owner query reports unresolved durable recovery draft |

Local Server unavailable cannot create durable recovery and MUST remain `FAILED`。Before rail unmount、route/Workspace switch或已知 destructive navigation，dirty failed input必须显式 block/confirm并提供 copy；不得静默 discard，也不得把 browser persistence称为 durable recovery。

## 7. Source Inspection

### UNSI-050 — SourceInspectionQueryV1

```text
GET /api/v1/workspace/source-inspections
  ?material_id=<required UUID>
  &revision_id=<required UUID>
  &source_span_id=<optional UUID>
```

Server 从 current Workspace context解析 scope，再调用 SYS01 exact read port。API/query layer不得直接从 Message prose、filename、summary、vector index或 current revision猜测 source。

### UNSI-051 — SourceInspectionResponseV1

```yaml
SourceInspectionResponseV1:
  schema_version: "1.0"
  generated_at: datetime
  data:
    view_state: READY|MISSING|STALE
    workspace_ref: versioned_owner_ref
    source_ref: SourceInspectionRefV1
    document_ref: versioned_owner_ref|null # compatibility/audit only
    source_label: string
    locator:
      page: integer|null
      chapter: string|null
      node_id: uuid|null
      start_offset: integer|null
      end_offset: integer|null
      anchor_version: string|null
    excerpt: string|null                   # <= 8192, exact canonical source text only
    is_current_revision: boolean
    reason_codes: [string]
  source_status: [source_status_v1]
  correlation_id: string
```

Response `private, no-store`，不得含 managed/absolute path、完整非必要资料、Prompt、grader-only或secret。

### UNSI-052 — READY / MISSING / STALE

- `READY`：Material、exact revision、exact span关系一致，span可回放；`excerpt`与locator来自该 exact canonical span。历史 accepted revision只要仍可回放也可 READY，且 `is_current_revision=false`；
- `MISSING`：source_span_id 未提供，或 current-Workspace Material已验证但 requested span/source content缺失/已擦除；`excerpt=null`，不得 fallback；
- `STALE`：refs存在但 anchor invalidated、locator replay失败或一致性不能证明；不得显示为 READY，也不得改查 current revision。

Material/revision不属于 current Workspace、Material不存在、或 lineage不一致时，统一返回404 `SOURCE_INSPECTION_NOT_FOUND`。不得通过不同 code/message/timing/details枚举 foreign对象。

### UNSI-053 — Side effects and fallback

Source inspection：

- MUST side-effect free、no business write、no LLM、no online historical backfill；
- MUST NOT create Activity/TeachingAction/Attempt/Evidence/UserNote；
- MUST NOT use global Material fallback、similar-title fallback、first span、current revision或message excerpt冒充 exact source；
- refresh/retry可重复执行且不产生新事实。

## 8. LCMS Citation / View-source Handoff

### UNSI-060 — Capability issuance

AVAILABLE `INSPECT_SOURCE` 只可出现在 learner-visible block，且 `input_refs` 至少包含同一 Workspace的 exact：

```text
SYS02 EvidenceBundle
SYS01 Material
SYS01 MaterialRevision
SYS01 SourceSpan
```

缺任一 exact ref、legacy citation、stale ref或非 learner-visible evidence时，capability必须 `UNAVAILABLE|STALE`。`command_contract_ref` 继续使用 LearningMessage 1.0 已发布的 `SYS02.InspectSourceV1`；它是 read handoff contract，不是 SYS02 source ownership。

### UNSI-061 — Invocation result

LCMS invocation必须重验 message/block/capability/version/current Workspace与全部 source refs。成功返回：

```yaml
LearningInteractionResultV1:
  status: SUCCEEDED
  result_refs: [Material, MaterialRevision, SourceSpan]
  next_transition:
    kind: OPEN_SOURCE
    target_system: SYS01
    expected_ref_types: [Material, MaterialRevision, SourceSpan]
```

Frontend 只使用 result refs 调用 `SourceInspectionQueryV1` 并打开 Current Material。它不得从 capability label、block excerpt或旧 citation重建 refs。

### UNSI-062 — No CAPTURE_NOTE implication

本合同不向 LearningMessage V1 action enum增加 `CAPTURE_NOTE`，也不允许 source-to-note快捷动作绕过 `SaveUserNoteV1`。未来 capability需独立 schema/version/confirmation contract。

## 9. Persistence, Backup, Export and Erasure

### UNSI-070 — SQLite durable mapping

实现至少表达：

```text
user_notes                  # current aggregate/scope/anchor/current_version
user_note_versions          # immutable content versions
user_note_command_receipts  # idempotency/result
user_note_recovery_drafts   # unresolved/resolved durable user content
```

实际 table/class名 MAY 符合仓库命名，但语义必须分离。`workspace_id`直接持久化；`(note_id, version)`、command idempotency scope、一个 recovery id的resolution必须唯一。Foreign key/index/transaction在 SQLite production-local path生效。

### UNSI-071 — Backup and export

- Recovery Package的 consistent SQLite snapshot包含全部 UserNote/version/receipt/recovery records；
- User Data Export `LEARNING_RECORDS` 使用显式 allowlist导出 note id/workspace/anchor/content/version/timestamps与 unresolved recovery content；
- export不得含内部 path、receipt payload internals、Prompt、secret或其他 Workspace数据；
- restore后 unresolved recovery仍可查询，且不得绕过 erasure checkpoint复活已删 note。

### UNSI-072 — Erasure and Material deletion

- `LEARNING_RECORDS` 与 `ALL_PERSONAL_DATA` erasure处理 UserNote current/version/recovery content；
- Material/Document permanent delete默认保留用户笔记正文，MATERIAL/SOURCE_SPAN anchor变为 `MISSING`/invalidated；preview/report必须计数并说明；
- owner-safe erasure之外不得跨表 hard delete UserNote；
- deleted note/recovery content不得通过 backup、receipt、projection、message或online LLM恢复。

## 10. Stable Errors

### UNSI-080 — Error catalog

```text
USER_NOTE_NOT_FOUND
USER_NOTE_CONTENT_INVALID
USER_NOTE_ANCHOR_INVALID
USER_NOTE_VERSION_CONFLICT
USER_NOTE_IDEMPOTENCY_CONFLICT
USER_NOTE_RECOVERY_NOT_FOUND
USER_NOTE_RECOVERY_VERSION_CONFLICT
USER_NOTE_DEPENDENCY_UNAVAILABLE
SOURCE_INSPECTION_NOT_FOUND
SOURCE_INSPECTION_REF_INVALID
SOURCE_INSPECTION_UNAVAILABLE
```

Mapping：

- invalid content/anchor/ref → validation 400/422，non-retryable without new input；
- missing/foreign note/source → same not-found 404 appearance；
- version/idempotency/recovery current-version mismatch → conflict 409，non-retryable without requery/user choice；
- temporary database/local dependency failure → dependency/transient 503，MAY retry with same idempotency key；
- `MISSING/STALE` 是成功 read view state，不得机械映射成 transport error。

Error/details/log不得泄露 foreign ref、note/source content（typed conflict current/recovery payload除外且仅 current Workspace）、absolute path、Prompt、secret或grader-only。

## 11. Security and Caching

### UNSI-090

所有 endpoints `Cache-Control: private, no-store`。Frontend cache key必须至少包含 current owner/workspace、note/source exact ref与schema version；Workspace切换时清除/隔离旧 cache和dirty presentation state。

### UNSI-091

UserNote/recovery/source excerpt均视为 private local user content。Telemetry/log/audit只记录 opaque refs、version、size、reason/error/correlation，不记录正文。

### UNSI-092

Source/Note Markdown与locator是untrusted display input；必须使用 typed renderer/escaping。禁止 raw HTML/MDX/script、dynamic component、local file URL、remote tracking image与arbitrary command。

## 12. Tests

### UNSI-100 — Contract/unit

覆盖 strict schema、unknown fields/major、anchor discriminators、size limits、exact refs、stable errors、safe rendering、idempotency与version uniqueness。

### UNSI-101 — UserNote integration

覆盖 create/update/requery、single-flight ordering oracle、duplicate replay、409 no-overwrite、durable recovery after restart、keep/replace/merge、second conflict、server unavailable、Workspace switch isolation、foreign/missing indistinguishable。

### UNSI-102 — Source inspection integration

覆盖 citation/view-source handoff、exact historical revision、locator/excerpt、missing span、stale anchor、trashed/deleted source、foreign Workspace fail closed、no current/global/filename/summary fallback、no write/no LLM。

### UNSI-103 — Data lifecycle

覆盖 fresh/current Alembic upgrade + single head/check、Recovery Package restore、export allowlist、LEARNING_RECORDS/ALL_PERSONAL_DATA erasure、Material deletion anchor invalidation、no resurrection与privacy registry completeness。

## 13. Acceptance Criteria

- `UNSI-AC-001`：Platform Workspace Notes是 UserNote/recovery唯一 writer；SYS01仍是 MaterialRevision/SourceSpan唯一 writer。
- `UNSI-AC-002`：UserNote是 stable-id、Workspace-scoped、anchored、append-version durable object；frontend/browser storage无第二 truth。
- `UNSI-AC-003`：create/update/idempotency/single-flight owner receipt语义完整，未持久化不显示 SAVED。
- `UNSI-AC-004`：409不覆盖 current，recovery draft durable，keep/replace/merge显式且可重启恢复。
- `UNSI-AC-005`：SourceInspection exact refs返回 READY/MISSING/STALE；无 filename/summary/current/global fallback。
- `UNSI-AC-006`：citation/view-source只从 exact LCMS refs进入 `OPEN_SOURCE`，cross-Workspace fail closed。
- `UNSI-AC-007`：backup/export/erasure/material-delete/no-resurrection覆盖 UserNote与recovery content。
- `UNSI-AC-008`：public schema/error/cache/privacy/security contracts与SQLite production-local gates PASS。

## 14. Forbidden Implementations

禁止：

- frontend/localStorage/sessionStorage/IndexedDB持久化 canonical note；
- mock save/recovery显示成功；
- last-write-wins、timestamp winner、silent overwrite/merge；
- recovery draft只存在browser memory却显示 RECOVERABLE；
- global notes library或跨 Workspace note aggregation；
- Message/SYS08/SYS01写 UserNote；
- Message excerpt/citation payload成为 Material/SourceSpan truth；
- source missing/stale时回退 filename、summary、current revision、first span、相似 Material或其他 Workspace；
- source inspection调用LLM或产生业务写入；
- Material delete静默删除 UserNote正文；
- 新增 `CAPTURE_NOTE`、generic command router、backend schema或migration而不经过 EXEC-076 gates。
