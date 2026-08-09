# SYS01 Library Management, Deduplication and OCR Specification

> Spec ID: `LIB-*`
> Status: FROZEN
> Governing ADR: ADR-0008
> Owner: SYS01

## 1. Invariants

- `LIB-001`：SourceDocument metadata、tag、collection、duplicate suggestion/decision、OCR run/candidate/review 只有 SYS01 可写。
- `LIB-002`：`original_filename`、raw bytes/checksum 与历史 MaterialRevision 不得因重命名、分类、去重或 OCR 静默覆盖。
- `LIB-003`：search index、fingerprint 和 OCR preview 是可重建 projection/candidate，不是第二 content truth。
- `LIB-004`：任何正文命中、OCR 接纳或重复建议必须 current-user scoped 且可追踪 exact document/revision/evidence/version。

## 2. Metadata and organization

```yaml
source_document_profile_v1:
  document_id: uuid
  metadata_version: integer
  display_title: string
  subject: string|null
  author: string|null
  language: string|null
  original_filename: string
  raw_asset_checksum: string
  archived_at: datetime|null
```

- `LIB-010`：metadata command MUST 带 expected version 与 idempotency key；冲突返回 `CONCURRENT_VERSION_CONFLICT`。
- `LIB-011`：metadata-only 更新不得创建 MaterialRevision 或改变 KnowledgeUnit identity。
- `LIB-012`：tag/collection 名称在 owner scope 内按 versioned normalization 唯一；archive 后 assignment 不再作为默认筛选结果。
- `LIB-013`：一个文档 MAY 属于多个 flat collection/tag；删除 tag/collection 不删除文档。

## 3. Search

```yaml
library_search_projection_v1:
  document_id: uuid
  revision_id: uuid|null
  index_version: string
  normalized_title: string
  normalized_body: string
  source_span_refs: [uuid]
  freshness: AVAILABLE|STALE|MISSING
```

- `LIB-020`：search projection 从 canonical SourceDocument/current MaterialRevision 重建。
- `LIB-021`：标题可搜索所有 owner-visible 文档；正文只搜索 approved/current、learner-visible SourceSpan。
- `LIB-022`：结果按 explicit sort + stable tie-break；正文命中返回 ≤500 字 excerpt 和 SourceSpan ref。
- `LIB-023`：projection failure 标 STALE/PARTIAL；不得返回旧正文却声明 READY。

## 4. Batch commands

- `LIB-030`：batch scope 只能是显式、去重后的 document IDs，1～100 项。
- `LIB-031`：同 owner + command type + idempotency key 返回原 receipt；payload 不同则 conflict。
- `LIB-032`：metadata/tag/collection 操作单事务原子；archive/restore 写 state + outbox/receipt 原子。
- `LIB-033`：response 返回每项 status/version/reason；未授权与不存在保持不可枚举。

## 5. Duplicate suggestions

- `LIB-040`：fingerprint policy/version 必须持久化；阈值是产品参数，不宣称普适常数。
- `LIB-041`：exact checksum MAY 高置信建议，但仍不得自动 archive/merge。
- `LIB-042`：near/revision candidate 必须保存差异摘要和 evidence；model/heuristic confidence 不等于事实概率。
- `LIB-043`：resolution command 幂等；`KEEP_SEPARATE|DISMISS|ARCHIVE_CANDIDATE|ATTACH_AS_REVISION` 语义显式。
- `LIB-044`：archive 可恢复且不删除 raw bytes；attach-as-revision 重新走安全/parse/publish pipeline。

## 6. OCR

```yaml
ocr_run_v1:
  run_id: uuid
  document_id: uuid
  input_revision_id: uuid|null
  raw_checksum: string
  engine: tesseract-local
  engine_version: string
  languages: [string]
  policy_version: string
  status: pending|processing|review_required|accepted|rejected|failed

ocr_candidate_v1:
  candidate_id: uuid
  run_id: uuid
  page: integer
  block_index: integer
  bbox: [float, float, float, float]
  text: string
  confidence: float|null
  image_hash: string
  status: candidate|accepted|rejected
  corrected_text: string|null
  version: integer
```

- `LIB-050`：OCR request 仅接受 owner-visible PDF，durable、idempotent、bounded retry。
- `LIB-051`：adapter 不使用 shell，不开放网络，限制页数、像素、超时、输出大小和进程。
- `LIB-052`：candidate 在人工接受前不得进入普通 search/retrieval/knowledge publication。
- `LIB-053`：review command 带 candidate version；低置信、空文本、bbox 越界不得自动接受。
- `LIB-054`：接受一个 run 创建新 MaterialRevision；SourceSpan locator 至少包含 page+bbox+image/text hash+OCR provenance/version。
- `LIB-055`：partial/failed run 保留旧 current revision；不得把 OCR 失败写成 learner evidence。

## 7. Errors

至少新增：

```text
LIBRARY_METADATA_VERSION_CONFLICT
LIBRARY_BATCH_SCOPE_INVALID
LIBRARY_IDEMPOTENCY_CONFLICT
DUPLICATE_SUGGESTION_NOT_ACTIONABLE
OCR_NOT_APPLICABLE
OCR_ENGINE_UNAVAILABLE
OCR_TIMEOUT
OCR_OUTPUT_INVALID
OCR_REVIEW_VERSION_CONFLICT
OCR_RUN_NOT_READY
```

## 8. Acceptance criteria

- `LIB-AC-001`：标题/正文/标签/集合组合搜索 owner-safe，正文命中可追踪 current SourceSpan。
- `LIB-AC-002`：重命名/分类不创建 MaterialRevision，历史 metadata version 可审计。
- `LIB-AC-003`：batch 重试不重复副作用，version conflict 不 last-write-wins。
- `LIB-AC-004`：exact/near/revision duplicate 都只形成候选；无自动 canonical merge。
- `LIB-AC-005`：archive/restore 保留 raw asset，projection 与默认列表收敛。
- `LIB-AC-006`：OCR candidate 有 page/bbox/hash/confidence/engine version，未接受不可用于学习。
- `LIB-AC-007`：接受 OCR 后新 revision/SourceSpan 可重放，旧 revision/raw asset 不变。
- `LIB-AC-008`：SQLite/PostgreSQL migration、projection rebuild、worker restart 和 owner isolation 通过。

## 9. Forbidden implementations

禁止 frontend-only tags；用 SourceChunk 当搜索/知识 truth；自动重复合并；归档时物理删除；OCR 文本覆盖 raw/current revision；未审核 OCR 进入学习；外部 OCR 默认上传；日志保存整页图像/全文；跨 owner 批量操作。
