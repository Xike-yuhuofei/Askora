# SYS01 Workspace Material Management, Deduplication and OCR Boundary Specification

> Spec ID: `LIB-*`  
> Status: FROZEN / v1 PRODUCT-POSITIONING-ALIGNED  
> Historical Governing ADR: ADR-0008  
> Current lifecycle contract: `docs/specs/interfaces/material-lifecycle-contract.md` (`MATLIFE-*`)  
> Current upper constraint: `docs/product/PRODUCT-POSITIONING.md`  
> Owner: SYS01 for Material/content metadata; Platform Workspace boundary for Project membership

## 1. Invariants

- `LIB-001`：Material content metadata、SourceFile refs、duplicate suggestion/decision 只有 SYS01 可写；Workspace/LearningProject/ProjectMaterial membership 由 Platform Workspace/Product Organization owner 写。
- `LIB-002`：managed SourceFile、raw checksum 与历史 MaterialRevision 不得因重命名、分类、去重、Trash 或 derived rebuild 静默覆盖。
- `LIB-003`：search index、fingerprint 与其他检索 projection 是可重建数据，不是第二 Material/content truth。
- `LIB-004`：任何正文命中、重复建议、批量操作必须 `LocalOwner + workspace_id` scoped，并可追踪 exact Material/SourceFile/revision/evidence/version。
- `LIB-005`：v1 不存在跨 Workspace Global Material Library；同一 LocalOwner 的多个 Workspace 默认仍互相隔离。
- `LIB-006`：Material 与 LearningProject 是多对多关系；从 Project 移除 Material 只解除关系，不删除 Material 本体。

## 2. Material, SourceFile and Workspace Scope

```yaml
material_v1:
  material_id: uuid
  workspace_id: uuid
  metadata_version: integer
  display_title: string
  subject: string|null
  author: string|null
  language: string|null
  current_revision_id: uuid|null
  lifecycle: active|trash

source_file_ref_v1:
  asset_id: uuid
  material_id: uuid
  checksum: string
  original_filename: string
  managed_storage_ref: string
```

`deleted` 是 Permanent Delete 完成后的 logical terminal/tombstone semantics，不要求在 current Material row 中保留用户内容；具体由 `MATLIFE-*` + Data Control receipt/checkpoint 表达。

### LIB-010

Material metadata command MUST 带 expected version 与 idempotency key；冲突返回 `CONCURRENT_VERSION_CONFLICT`。

### LIB-011

metadata-only 更新不得创建 MaterialRevision 或改变 KnowledgeUnit identity。

### LIB-012

Tag/collection 若保留，必须是**Workspace 内**的可选个人组织 state；名称按 workspace-scoped normalization 唯一。它们不是 LearningProject，也不得形成 Global Library。

### LIB-013

一个 Material MAY 属于同一 Workspace 内多个 flat tag/collection 和多个 LearningProject。删除 tag/collection 或 ProjectMaterial relationship 不删除 Material/SourceFile。

### LIB-014 — Managed Copy

新 Material import MUST 拥有 Askora managed SourceFile；不得仅依赖用户原始文件绝对路径。

## 3. Search

```yaml
library_search_projection_v1:
  workspace_id: uuid
  material_id: uuid
  revision_id: uuid|null
  index_version: string
  normalized_title: string
  normalized_body: string
  source_span_refs: [uuid]
  freshness: AVAILABLE|STALE|MISSING|PARTIAL
```

- `LIB-020`：search projection 从 canonical Workspace-scoped Material/current MaterialRevision 重建。
- `LIB-021`：标题/正文搜索默认仅作用于明确 workspace；正文只搜索 approved/current、learner-visible SourceSpan。
- `LIB-022`：结果按 explicit sort + stable tie-break；正文命中返回 bounded excerpt 和 SourceSpan ref。
- `LIB-023`：projection failure 标 STALE/PARTIAL；不得返回旧正文却声明 READY。
- `LIB-024`：跨 Workspace search 在 v1 默认禁止。未来若开放必须由新的 Product Positioning/Spec 明确授权。

## 4. Project Membership

### LIB-025 — Relationship Only

ProjectMaterial 是 `LearningProject ↔ Material` relationship。SYS01 MAY 校验 Material ref 存在并属于同一 Workspace，但 MUST NOT 成为 LearningProject owner。

### LIB-026 — Remove vs Delete

必须区分：

```text
Remove from Project
→ delete relationship only

Delete Material
→ Material → Trash
→ optional Permanent Delete later
```

如果 Material 仍被其他 Project 引用，delete preview MUST 返回这些引用影响；不得静默级联删除其他 Project relationship/learning history。

## 5. Batch Commands

- `LIB-030`：batch scope 只能是同一 Workspace 内显式、去重后的 Material IDs；MAY 设本地资源保护上限。
- `LIB-031`：同 owner/workspace + command type + idempotency key 返回原 receipt；payload 不同则 conflict。
- `LIB-032`：metadata/tag/collection/relationship 操作按 owner contract 原子；Trash/Restore 写 lifecycle + outbox/receipt 原子。
- `LIB-033`：response 返回每项 status/version/reason；不得通过错误差异泄露其他 Workspace 的 Material existence。

## 6. Duplicate Suggestions

### LIB-040

fingerprint policy/version 必须持久化；阈值是产品参数，不宣称普适常数。

### LIB-041

exact checksum MAY 产生高置信重复建议，但 Detect Duplicate 不等于强制 Deduplicate。

用户 MAY：

- 使用已有 Material；
- 明确创建新副本；
- 取消导入；
- 在明确设计允许时将新文件作为已有 Material 的 revision candidate。

系统 MUST NOT 自动 merge/delete。

### LIB-042

near/revision candidate 必须保存差异摘要和 evidence；model/heuristic confidence 不等于事实概率。

### LIB-043

resolution command 幂等。跨 Workspace duplicate detection 默认 MUST NOT 暴露另一个 Workspace 的 Material metadata 或自动建议跨 Workspace reuse。

### LIB-044

attach-as-revision 若当前产品流程允许，MUST 重新走 managed copy、安全扫描、parse、SourceSpan 和 projection pipeline；旧 revision 与 SourceFile 不覆盖。

## 7. Trash, Restore and Permanent Delete

### LIB-045 — Two-stage Delete

普通删除进入本地 Trash，而不是立即永久删除：

```text
active
→ trash
→ permanent delete
```

Trash 中 Material 默认不参与普通 search/retrieval/new learning，但其 Material metadata、managed SourceFile、revision/provenance、ProjectMaterial memberships 与 historical learning refs 仍是 durable、可恢复状态。

Trash MUST NOT：

- 删除 managed SourceFile；
- 写 `processing_status=FAILED` 代表删除；
- 删除 ProjectMaterial membership；
- 让旧 background job late result 发布为 current learner-visible output。

完整 command/migration/job/restore rules 服从 `MATLIFE-001..052`。

### LIB-046 — Permanent Delete

Permanent Delete 必须由用户明确触发或 versioned local cleanup policy 执行，并服从 canonical Data Control `DOCUMENT` erasure + no-resurrection contract。

SYS01 MUST NOT 实现平行的 cross-owner physical-delete cascade。物理 SourceFile 删除只发生在已接受的 Permanent Delete/Data Control workflow 内；owner step 未完成时不得报告永久删除成功。

删除 durable Material 后，关联 derived chunks/index/cache MUST invalidated/removed；不得保留能重新生成已删 source facts 的孤立 projection。

完整 preview/confirmation/idempotency/legacy migration/backup semantics 服从 `MATLIFE-060..112`。

### LIB-047 — Restore

Restore 仅允许 `trash → active`，保留 exact Material identity。恢复前必须验证 retained SourceFile/revision integrity；不得从 stale derived chunk/index 猜测重建丢失 source，也不得无证据把旧 `processing_status=FAILED` 直接改成 READY。

### LIB-048 — Legacy Delete Migration

Legacy `is_deleted` 迁移按 `MATLIFE-080..085`：

- `is_deleted=false` → active；
- `is_deleted=true + managed source present/valid` → trash；
- `is_deleted=true + source already removed` → terminal legacy-deleted/tombstone，不从旧 cache/backup 复活，也不自行推断授权更广泛 erasure；
- `processing_status` 与 lifecycle 分离。

## 8. OCR Boundary — Deferred from v1 Core

`PRODUCT-POSITIONING.md` 明确冻结：v1 不建设完整 OCR Pipeline。

因此原 ADR-0008 / P1-04C 的 OCR 实现状态调整为：

- MAY 作为 legacy/experimental/local optional capability 保留；
- MUST NOT 是 v1 core capability 或 release prerequisite；
- MUST NOT 让扫描 PDF 的 OCR failure 阻塞文本型 PDF/EPUB/Markdown/TXT 主链；
- 产品默认只需识别扫描 PDF 无法可靠提取文本，并给出明确 unsupported/partial 提示；
- 不得因历史实现存在而在 v1 架构中继续扩大 OCR、layout/table/formula/vision pipeline。

### LIB-050 — Legacy OCR Isolation

若现有 OCR path 继续运行：

- candidate 在显式接受前不得进入普通 search/retrieval/knowledge publication；
- failure 不得记 learner error；
- raw PDF 不覆盖；
- OCR engine 不得成为 v1 runtime required dependency；
- 外部云 OCR 不得无新的隐私/产品决策自动启用。

## 9. Errors

至少支持或迁移到等价稳定错误：

```text
LIBRARY_METADATA_VERSION_CONFLICT
LIBRARY_BATCH_SCOPE_INVALID
LIBRARY_IDEMPOTENCY_CONFLICT
LIBRARY_WORKSPACE_SCOPE_VIOLATION
DUPLICATE_SUGGESTION_NOT_ACTIONABLE
MATERIAL_STILL_REFERENCED
MATERIAL_TRASHED
MATERIAL_NOT_IN_TRASH
MATERIAL_SOURCE_MISSING
MATERIAL_PERMANENT_DELETE_IN_PROGRESS
SCANNED_PDF_TEXT_EXTRACTION_UNAVAILABLE
```

历史 OCR error MAY 保留给 legacy/optional adapter，但不得作为 v1 core error gate。

## 10. Acceptance Criteria

- `LIB-AC-001`：标题/正文/标签/集合搜索严格 workspace-safe，正文命中可追踪 current SourceSpan。
- `LIB-AC-002`：重命名/分类不创建 MaterialRevision，历史 metadata version 可审计。
- `LIB-AC-003`：batch 重试不重复副作用，version conflict 不 last-write-wins。
- `LIB-AC-004`：exact/near/revision duplicate 都只形成候选；无自动 canonical merge。
- `LIB-AC-005`：Material Trash/Restore 保留 managed SourceFile、Project relationships 与 exact identity；Permanent Delete 服从 Data Control/no-resurrection。
- `LIB-AC-006`：从 Project 移除只删除 relationship，不删除 Material。
- `LIB-AC-007`：同一 Material 可属于同 Workspace 多个 LearningProject；跨 Workspace membership 被拒绝。
- `LIB-AC-008`：SQLite projection rebuild、worker restart 和 workspace isolation 通过；PostgreSQL 不属于 production requirement。
- `LIB-AC-009`：v1 没有完整 OCR 依赖；扫描 PDF 可被安全识别为 unsupported/partial 而不破坏 durable source。
- `LIB-AC-010`：existing compatibility document DELETE 若保留，只执行 Trash，不调用 physical file delete。

## 11. Forbidden Implementations

禁止：

- frontend-only Material/tag/project membership truth；
- 用 SourceChunk 当 Material/Knowledge truth；
- 自动重复合并/删除；
- Trash 时物理删除 managed SourceFile；
- Trash 用 processing failure 表示 lifecycle；
- Project relation removal 级联删除 Material；
- SYS01 Permanent Delete 越权 cascade 其他 owner state；
- Restore 从 stale derived data 伪造丢失 SourceFile；
- 跨 Workspace 默认搜索、dedup reuse 或 metadata 泄露；
- 未审核 OCR 进入学习；
- 把完整 OCR Pipeline 宣称为 v1 core requirement；
- 外部 OCR 默认上传私人资料；
- 日志保存整本原文/整页图像；
- PostgreSQL/Redis 作为 Library production-local correctness dependency。
