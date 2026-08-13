# SYS01 — Content & Knowledge

> Spec ID：`SYS01-*`  
> 对应设计：4.1 内容解析与知识建模  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS01-001

4.1 的唯一职责是把不可信原始材料转换为**可版本化、可定位原文、可审核、可教学/评估**的规范知识模型。

### SYS01-002

4.1 是以下状态的唯一写入者：`SourceDocument`、`MaterialRevision`、`SourceSpan`、`SourceChunk`、`KnowledgeUnit`、`Concept`、`PrerequisiteRelation`、规范 `Misconception`、索引投影元数据。

## 2. Non-responsibility

4.1 MUST NOT：

- 判断用户 mastery；
- 选择 TeachingAction；
- 生成 LearningPlan；
- 计算 ReviewSchedule；
- 选择本轮最终 EvidenceBundle；
- 直接把材料中的练习当正式 AssessmentItem 发布；
- 执行最终用户交互。

## 3. Owned State

必须遵守 `state-ownership.md`。核心持久状态：

```text
RawAsset metadata
MaterialRevision
DocumentIR / DocumentNode
SourceSpan
KnowledgeUnit revision
Concept revision
KnowledgeRelation revision
PedagogicalAsset candidate
ExtractionRun
ReviewDecision
IndexProjection metadata
```

### SYS01-010

已发布知识对象必须采用 stable id + immutable revision。

## 4. Inputs

允许输入：

- 用户上传的 PDF/EPUB/DOCX/Markdown/TXT；
- 网页/音视频转录等未来受控来源；
- parser/extractor 配置；
- 人工 ReviewDecision；
- 4.6 提交的 prerequisite/path conflict evidence；
- 安全扫描结果。

所有外部内容 MUST 默认视为不可信数据，而不是系统指令。

## 5. Outputs

必须能够输出：

- SourceDocument/MaterialRevision；
- 可回放 SourceSpan；
- SourceChunk；
- KnowledgeUnit/Concept；
- PrerequisiteRelation；
- 规范 Misconception；
- PedagogicalAsset candidate；
- content/index version events；
- 可供 4.2/4.4/4.6 查询的只读接口。

## 6. Domain Objects

公共对象引用 `domain-model.md`。

内部对象至少允许：

```text
RawAsset
DocumentIR
DocumentNode
KnowledgeMention
PedagogicalAsset
ExtractionRun
ReviewDecision
IndexProjection
```

### SYS01-020

`KnowledgeMention` MUST NOT 与 canonical `Concept` 等价。

### SYS01-021

`SourceChunk` MUST NOT 与 `KnowledgeUnit` 等价。

## 7. Commands

建议公共命令：

```text
ImportContent
ReinspectQuarantinedContent
ParseMaterialRevision
ExtractKnowledgeCandidates
ReviewKnowledgeCandidate
PublishKnowledgeRevision
RebuildIndexProjection
ReportKnowledgeConflict
```

每个 command MUST 支持幂等语义或明确不可重复范围。

### SYS01-025 — Quarantine Reinspection Command

`ReinspectQuarantinedContent` 由 SYS01 独占执行，必须验证 owner、当前 `quarantined` 状态、
原始资产 checksum 与更新的 scanner/policy version。幂等键至少包含 `document_id + target_scanner_version`。
同一版本重复提交返回已有任务，不创建第二个 SafetyScanRun。

复检任务必须 durable；但安全拒绝本身 `retryable=false`，不得把同一策略下的业务拒绝包装为
自动 retry。只有存储/数据库等 transient failure 可 bounded retry。

## 8. Events

至少产生/消费：

- `ContentImported`
- `ContentPublished`
- `KnowledgeRelationPublished`
- processing failed/review-required 类事件

关键发布决策 MUST 关联 DecisionTrace。

## 9. Algorithms

### SYS01-030：默认流水线

```text
validate file
→ compute checksum / revision
→ deterministic parse
→ recover structure
→ semantic segmentation
→ schema-constrained candidate extraction
→ bind SourceSpan
→ conservative entity resolution
→ relation inference
→ reverse evidence validation
→ graph quality checks
→ human review if required
→ publish revision
→ build replaceable projections
```

### SYS01-031：Baseline

MVP MUST 优先：

- deterministic parser；
- 结构规则；
- schema constrained LLM extraction；
- evidence binding；
- conservative merge；
- graph cycle/duplicate checks。

### SYS01-032：Hard prerequisite

hard prerequisite 自动发布要求高 precision。章节顺序、LLM 单次推断或低置信关系 MUST NOT 直接成为 hard prerequisite。

### SYS01-033：高级算法

不得自行引入 RL。监督模型可用于 entity resolution/candidate validation，但进入主路径前必须优于 baseline 并可回退。

## 10. Persistence

### SYS01-040

原始文件、规范内容、知识对象和索引投影必须逻辑分层：

```text
source of truth
→ canonical knowledge records
→ rebuildable lexical/vector/graph projections
```

图数据库/向量库若未来引入，默认只是 projection，不是第二事实源。

### SYS01-041

文档更新 MUST 形成新 MaterialRevision；受影响范围支持局部重算，stable KnowledgeUnit id SHOULD 尽量保留。

### SYS01-042

Published KnowledgeUnit/Relation 不能原地静默覆盖。

## 11. Failure Semantics

失败必须分类：

- unsupported/corrupted file → reject；
- security risk → quarantine；
- explicit newer-policy reinspection allow/review → imported + normal processing；
- same-policy reinspection → business reject，状态保持 quarantined；
- reinspection transient/internal failure → 状态保持 quarantined；
- partial parser failure → partial + review_required；
- anchor failure → 不得发布受影响事实；
- low-confidence relation → candidate/review；
- projection build failure → canonical content 可保留，projection 标 stale/failed 并重建。

### SYS01-050

索引构建失败不得回滚已成功提交的 canonical content revision，除非该 revision 无任何可用访问路径且产品定义要求原子发布。

## 12. Idempotency

- 相同 checksum + import scope 重复导入 SHOULD 返回已有 revision；
- extraction run 必须绑定 parser/extractor/prompt/model version；
- projection rebuild 必须可重复执行；
- ReviewDecision 重放不得重复创建同一 published revision。

## 13. Observability

必须记录：

- parse/extract/review/index trace；
- parser/extractor/model versions；
- object/edge publish/reject reason codes；
- anchor replay failures；
- processing latency；
- quarantine count；
- SafetyScanRun/scanner version/reinspection outcome；
- relation cycle/duplicate count；
- index freshness。

关键指标：object/relationship P/R/F1、hard prerequisite precision、anchor replay rate、hallucinated unsupported object rate。

## 14. Security

### SYS01-060

上传内容中的 Prompt Injection 只能作为内容数据，不得覆盖 system/developer/policy 指令。

### SYS01-061

解析器必须限制文件类型、大小、压缩炸弹/路径穿越/外部引用等风险；具体阈值由 security spec 配置。

### SYS01-062

模型抽取不得拥有任意 shell、文件写入或网络副作用权限。

## 15. Tests

必须至少覆盖：

- PDF/Markdown 基础解析；
- SourceSpan anchor replay；
- revision 更新；
- duplicate import idempotency；
- KnowledgeUnit stable identity；
- hard prerequisite cycle/rejection；
- unsupported relation 无证据不得发布；
- prompt injection 文档不会控制系统；
- quarantined 内容不入检索；
- projection 重建不会改变 canonical facts。

## 16. Acceptance Criteria

- `SYS01-AC-001`：导入文档后任一 published KnowledgeUnit 可追溯到 SourceSpan。
- `SYS01-AC-002`：修改源文档产生新 MaterialRevision，旧 revision 仍可审计。
- `SYS01-AC-003`：低置信 hard prerequisite 不自动发布。
- `SYS01-AC-004`：重新分块不无条件改变 canonical KnowledgeUnit identity。
- `SYS01-AC-005`：图/向量索引可从 canonical records 重建。
- `SYS01-AC-006`：恶意文档指令不会触发未授权工具或改变系统策略。
- `SYS01-AC-007`：4.6 报告路径冲突只能形成 evidence/review，不直接改知识图。

## 17. Forbidden Implementations

禁止：

- 直接把 LLM 抽取 JSON 当已发布知识库；
- 没有 SourceSpan 的关键知识对象自动发布；
- 把章节顺序直接当 prerequisite；
- 用 vector index / graph database 作为唯一事实源；
- 重建 chunk 时重置全部 KnowledgeUnit id；
- 4.1 修改 mastery/plan/action/review；
- 让文档 Prompt Injection 进入系统指令层。

## Legacy Mapping

当前主要相关路径：

```text
apps/backend/app/services/documents/parsers.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/knowledge_graph/kg_service.py
apps/backend/app/models/document.py
apps/backend/app/models/knowledge.py
```

`rag_service.py` 的检索/排序职责应逐步迁入 SYS02，而不是继续扩展在 SYS01。

---

## SYS01 Workspace Material Management, Deduplication and OCR Boundary Specification

> Spec ID: `LIB-*`  
> Status: FROZEN / v1 PRODUCT-POSITIONING-ALIGNED  
> Historical Governing ADR: ADR-0008  
> Current lifecycle contract: `docs/specs/interfaces/material-lifecycle-contract.md` (`MATLIFE-*`)  
> Current upper constraint: `docs/product/PRODUCT-POSITIONING.md`  
> Owner: SYS01 for Material/content metadata; Platform Workspace boundary for Project membership

### 1. Invariants

- `LIB-001`：Material content metadata、SourceFile refs、duplicate suggestion/decision 只有 SYS01 可写；Workspace/LearningProject/ProjectMaterial membership 由 Platform Workspace/Product Organization owner 写。
- `LIB-002`：managed SourceFile、raw checksum 与历史 MaterialRevision 不得因重命名、分类、去重、Trash 或 derived rebuild 静默覆盖。
- `LIB-003`：search index、fingerprint 与其他检索 projection 是可重建数据，不是第二 Material/content truth。
- `LIB-004`：任何正文命中、重复建议、批量操作必须 `LocalOwner + workspace_id` scoped，并可追踪 exact Material/SourceFile/revision/evidence/version。
- `LIB-005`：v1 不存在跨 Workspace Global Material Library；同一 LocalOwner 的多个 Workspace 默认仍互相隔离。
- `LIB-006`：Material 与 LearningProject 是多对多关系；从 Project 移除 Material 只解除关系，不删除 Material 本体。

### 2. Material, SourceFile and Workspace Scope

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

#### LIB-010

Material metadata command MUST 带 expected version 与 idempotency key；冲突返回 `CONCURRENT_VERSION_CONFLICT`。

#### LIB-011

metadata-only 更新不得创建 MaterialRevision 或改变 KnowledgeUnit identity。

#### LIB-012

Tag/collection 若保留，必须是**Workspace 内**的可选个人组织 state；名称按 workspace-scoped normalization 唯一。它们不是 LearningProject，也不得形成 Global Library。

#### LIB-013

一个 Material MAY 属于同一 Workspace 内多个 flat tag/collection 和多个 LearningProject。删除 tag/collection 或 ProjectMaterial relationship 不删除 Material/SourceFile。

#### LIB-014 — Managed Copy

新 Material import MUST 拥有 Askora managed SourceFile；不得仅依赖用户原始文件绝对路径。

### 3. Search

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

### 4. Project Membership

#### LIB-025 — Relationship Only

ProjectMaterial 是 `LearningProject ↔ Material` relationship。SYS01 MAY 校验 Material ref 存在并属于同一 Workspace，但 MUST NOT 成为 LearningProject owner。

#### LIB-026 — Remove vs Delete

必须区分：

```text
Remove from Project
→ delete relationship only

Delete Material
→ Material → Trash
→ optional Permanent Delete later
```

如果 Material 仍被其他 Project 引用，delete preview MUST 返回这些引用影响；不得静默级联删除其他 Project relationship/learning history。

### 5. Batch Commands

- `LIB-030`：batch scope 只能是同一 Workspace 内显式、去重后的 Material IDs；MAY 设本地资源保护上限。
- `LIB-031`：同 owner/workspace + command type + idempotency key 返回原 receipt；payload 不同则 conflict。
- `LIB-032`：metadata/tag/collection/relationship 操作按 owner contract 原子；Trash/Restore 写 lifecycle + outbox/receipt 原子。
- `LIB-033`：response 返回每项 status/version/reason；不得通过错误差异泄露其他 Workspace 的 Material existence。

### 6. Duplicate Suggestions

#### LIB-040

fingerprint policy/version 必须持久化；阈值是产品参数，不宣称普适常数。

#### LIB-041

exact checksum MAY 产生高置信重复建议，但 Detect Duplicate 不等于强制 Deduplicate。

用户 MAY：

- 使用已有 Material；
- 明确创建新副本；
- 取消导入；
- 在明确设计允许时将新文件作为已有 Material 的 revision candidate。

系统 MUST NOT 自动 merge/delete。

#### LIB-042

near/revision candidate 必须保存差异摘要和 evidence；model/heuristic confidence 不等于事实概率。

#### LIB-043

resolution command 幂等。跨 Workspace duplicate detection 默认 MUST NOT 暴露另一个 Workspace 的 Material metadata 或自动建议跨 Workspace reuse。

#### LIB-044

attach-as-revision 若当前产品流程允许，MUST 重新走 managed copy、安全扫描、parse、SourceSpan 和 projection pipeline；旧 revision 与 SourceFile 不覆盖。

### 7. Trash, Restore and Permanent Delete

#### LIB-045 — Two-stage Delete

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

#### LIB-046 — Permanent Delete

Permanent Delete 必须由用户明确触发或 versioned local cleanup policy 执行，并服从 canonical Data Control `DOCUMENT` erasure + no-resurrection contract。

SYS01 MUST NOT 实现平行的 cross-owner physical-delete cascade。物理 SourceFile 删除只发生在已接受的 Permanent Delete/Data Control workflow 内；owner step 未完成时不得报告永久删除成功。

删除 durable Material 后，关联 derived chunks/index/cache MUST invalidated/removed；不得保留能重新生成已删 source facts 的孤立 projection。

完整 preview/confirmation/idempotency/legacy migration/backup semantics 服从 `MATLIFE-060..112`。

#### LIB-047 — Restore

Restore 仅允许 `trash → active`，保留 exact Material identity。恢复前必须验证 retained SourceFile/revision integrity；不得从 stale derived chunk/index 猜测重建丢失 source，也不得无证据把旧 `processing_status=FAILED` 直接改成 READY。

#### LIB-048 — Legacy Delete Migration

Legacy `is_deleted` 迁移按 `MATLIFE-080..085`：

- `is_deleted=false` → active；
- `is_deleted=true + managed source present/valid` → trash；
- `is_deleted=true + source already removed` → terminal legacy-deleted/tombstone，不从旧 cache/backup 复活，也不自行推断授权更广泛 erasure；
- `processing_status` 与 lifecycle 分离。

### 8. OCR Boundary — Deferred from v1 Core

`PRODUCT-POSITIONING.md` 明确冻结：v1 不建设完整 OCR Pipeline。

因此原 ADR-0008 / P1-04C 的 OCR 实现状态调整为：

- MAY 作为 legacy/experimental/local optional capability 保留；
- MUST NOT 是 v1 core capability 或 release prerequisite；
- MUST NOT 让扫描 PDF 的 OCR failure 阻塞文本型 PDF/EPUB/Markdown/TXT 主链；
- 产品默认只需识别扫描 PDF 无法可靠提取文本，并给出明确 unsupported/partial 提示；
- 不得因历史实现存在而在 v1 架构中继续扩大 OCR、layout/table/formula/vision pipeline。

#### LIB-050 — Legacy OCR Isolation

若现有 OCR path 继续运行：

- candidate 在显式接受前不得进入普通 search/retrieval/knowledge publication；
- failure 不得记 learner error；
- raw PDF 不覆盖；
- OCR engine 不得成为 v1 runtime required dependency；
- 外部云 OCR 不得无新的隐私/产品决策自动启用。

### 9. Errors

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

### 10. Acceptance Criteria

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

### 11. Forbidden Implementations

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

---

## SPEC-D02 — Multi-Granularity Content Model Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D02`  
> 冻结日期：2026-08-08  
> Owner：SYS01 Content & Knowledge  
> 上游：`SPEC-D01`、`systems/01-content-knowledge.md`、`architecture/state-ownership.md`  
> 目的：冻结解析、知识抽取、引用、检索四类不同粒度，禁止继续用一个 chunk 同时承担全部职责。

### 1. Canonical Rule

Askora MUST 明确区分：

```text
DocumentNode      → 结构事实
EvidenceSpan      → 引用/证据角色
SemanticUnit      → 知识抽取工作单元
RetrievalChunk    → 检索投影
HierarchyNode     → 范围路由投影
```

这些对象/角色不得因为“文本内容相似”而被实现为同一长期 identity。

### 2. Ownership Classification

#### D02-010

- `DocumentNode`：SYS01 internal structured truth；
- `EvidenceSpan`：不是新的 canonical object；它是一个或多个 canonical `SourceSpan` 在证据语境下的 typed reference；
- `SemanticUnit`：SYS01 extraction working record，绑定 exact MaterialRevision + segmentation version；
- `RetrievalChunk`：现有 canonical `SourceChunk` 的 SYS02-ready projection role；
- `HierarchyNode`：从 DocumentNode 派生的可重建范围路由 projection。

不得新增第二 KnowledgeUnit、第二 SourceSpan 或第二文档事实源。

### 3. EvidenceSpan

#### D02-020

EvidenceSpan MUST 通过 SourceSpan refs 表达：

```yaml
evidence_span:
  source_span_ids: [uuid]
  evidence_role: source_fact|definition|example|counterexample|procedure|relation_evidence|assessment_support
  evidence_hash: string
```

`evidence_hash` 只用于完整性/去重，不是业务 identity。

#### D02-021

任何影响 KnowledgeUnit/Relation publish 的 evidence MUST 最终回到当前 MaterialRevision 的可 replay SourceSpan。

### 4. SemanticUnit

#### D02-030

SemanticUnit 的目的只是为 extraction 提供语义完整上下文。至少包含：

```yaml
semantic_unit_id: uuid
revision_id: uuid
segmentation_version: string
source_span_ids: [uuid]
parent_node_ids: [uuid]
text: string
semantic_role: definition|argument|procedure|example|exercise|narrative|other
context_refs: [uuid]
```

#### D02-031

SemanticUnit segmentation MUST 优先使用 DocumentNode boundary，再按语义/长度规则受控切分；MUST NOT 直接复用 RetrievalChunk 作为唯一 extraction unit。

#### D02-032

相同 revision + segmentation version MUST deterministic 产生稳定 SemanticUnit 内容与 stable ordering。升级 segmentation version MAY 产生新 unit identity，但不得因此自动改变已发布 KnowledgeUnit identity。

### 5. RetrievalChunk / SourceChunk

#### D02-040

现有 `SourceChunk` 继续是 canonical retrieval projection contract。其生成 MAY 使用与 SemanticUnit 不同的粒度、overlap 和 budget。

每个新 SourceChunk MUST 保存：

```text
revision_id
segmentation/index version
source_span_ids
knowledge_unit_ids（如已知）
pedagogical_role
answer exposure classification / allowed_use
hierarchy scope refs
```

#### D02-041

重新分块、embedding 模型变化、reranker 变化、index 重建 MUST NOT 修改 KnowledgeUnit/Concept/Relation truth。

### 6. HierarchyNode

#### D02-050

HierarchyNode 是 DocumentNode 的可重建路由 projection，用于：

- book/part/chapter/section scope routing；
- long-document retrieval narrowing；
- goal-to-knowledge candidate scope；
- UI knowledge map grouping。

不得把章节 parent/child 顺序解释为 prerequisite。

### 7. Processing Order

```text
DocumentIR / DocumentNode
↓
SourceSpan
↓
SemanticUnit segmentation
↓
Knowledge candidate extraction
↓
Knowledge publish
↓
RetrievalChunk / Hierarchy projection
```

允许为低延迟先生成临时 SourceChunk，但在 canonical learning path 中 MUST 能被后续 exact revision/version projection 替换，不得成为知识发布依据的唯一事实。

### 8. Boundary with SYS02

SYS01：

- 定义/生成 SourceChunk projection records；
- 维护 projection freshness/version metadata。

SYS02：

- 最终召回、过滤、排序、压缩并创建 EvidenceBundle；
- 不得反向修改 SemanticUnit/KnowledgeUnit/DocumentNode。

### 9. Boundary with SYS08 / LLM

SYS08 MAY 执行 SemanticUnit 上的 schema-constrained model inference，但：

```text
ModelInference
→ candidate only
→ SYS01 validation/publish path
```

LLM output MUST NOT 直接变成 KnowledgeUnit/Relation published truth。

### 10. Tests

MUST 覆盖：

1. 同一 EPUB 产生不同的 SemanticUnit 与 RetrievalChunk boundaries；
2. chunk rebuild 不改变 KnowledgeUnit stable ids；
3. SemanticUnit 可回到 SourceSpan；
4. HierarchyNode 不制造 prerequisite；
5. grader-only boundary 不与 learner-visible chunk 混合；
6. extraction segmentation version 可审计；
7. projection 删除后可重建。

### 11. Acceptance Criteria

- `D02-AC-001`：Knowledge candidate 不再以 SourceChunk identity 作为长期知识 identity。
- `D02-AC-002`：每个 SemanticUnit 可追溯至少一个 SourceSpan。
- `D02-AC-003`：SemanticUnit / RetrievalChunk / HierarchyNode 可独立重建和版本化。
- `D02-AC-004`：SourceChunk 重建不会修改 canonical KnowledgeUnit/Relation。
- `D02-AC-005`：章节 hierarchy 不自动形成 prerequisite edge。
- `D02-AC-006`：不存在 EvidenceSpan 第二 truth；引用仍落回 SourceSpan。

### 12. Forbidden Implementations

禁止：

- `chunk == KnowledgeUnit`；
- `chunk == SourceSpan`；
- 一个固定 chunk size 服务解析、抽取、检索、引用全部阶段；
- 重分块时重置全部知识 identity；
- HierarchyNode 作为 graph truth owner；
- SYS02 修改 SYS01 canonical state。

### 13. Freeze Decision

`SPEC-D02`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。如实现需要把 SemanticUnit 或 HierarchyNode 提升为跨系统 canonical public object，必须先报告 `SPEC GAP`。

---

## SPEC-D03 — Knowledge Candidate Verification & Publish Pipeline

> 状态：**FROZEN**  
> Spec ID：`SPEC-D03`  
> 冻结日期：2026-08-08  
> Owner：SYS01 Content & Knowledge  
> 上游：`SPEC-D01`、`SPEC-D02`、`systems/01-content-knowledge.md`、UI-02A Frozen Baseline  
> 目的：把 UI-02A 的 source-bound structural candidates 扩展为可验证、可发布、可审计的真实 Knowledge Model，而不允许 LLM 输出直接成为 canonical truth。

### 1. Baseline

UI-02A 已冻结：

```text
deterministic-structure-v2
→ SourceSpan-bound KnowledgeUnit candidate
```

并明确：无可靠 relation 时 edges 保持为空；`minimal-binding-v1` 只能兼容读取。

本合同 MUST 在该基线上扩展，不得回退为“一文档一个高置信 published KnowledgeUnit”。

### 2. Candidate Families

SYS01 内部至少支持：

```text
ConceptCandidate
KnowledgeUnitCandidate
RelationCandidate
PedagogicalAssetCandidate
```

每个 candidate MUST 保存：

```yaml
candidate_id: uuid
revision_id: uuid
candidate_type: string
source_span_ids: [uuid]
semantic_unit_ids: [uuid]
extraction_run_id: uuid
proposed_payload: object
provenance_type: deterministic|source_explicit|model_inferred|human_curated
confidence: float|null
status: candidate|verified|published|rejected|review_required|superseded
reason_codes: [string]
```

Model confidence MUST NOT 被解释为已校准事实概率。

### 3. ExtractionRun

#### D03-010

每次 extraction run MUST 固定并保存：

```text
parser version
semantic segmentation version
extractor version
model/provider/snapshot（如有）
prompt/schema version（如有）
publication policy version
input revision
```

Replay MUST 使用持久化 candidate/result；不得调用当前在线 LLM 重构历史 extraction。

### 4. Pipeline

```text
SemanticUnit
→ schema-constrained extraction
→ evidence binding
→ entity resolution
→ candidate normalization
→ relation validation
→ reverse evidence check
→ duplicate/conflict/cycle checks
→ publication policy
→ published | review_required | rejected
```

任何步骤失败都必须显式保留状态/reason code；不得静默丢弃后把剩余结果宣称完整。

### 5. KnowledgeUnit Publication

#### D03-020

KnowledgeUnit MAY 自动 publish，仅当 versioned `KnowledgePublicationPolicy` 明确允许且同时满足：

- 至少一个 current-revision replayable SourceSpan；
- schema/business validation pass；
- identity/entity resolution 无 blocking ambiguity；
- 无未解决 source conflict；
- provenance 和 extraction versions 完整；
- confidence/quality rule 达到 policy 要求。

阈值 MUST versioned/configured，MUST NOT 写成普适学习科学常数。

#### D03-021

source-explicit / deterministic structural evidence 可以与 model inference 组合，但 model inference 单独不足以绕过证据要求。

### 6. Concept Resolution

#### D03-030

Concept merge MUST conservative。别名、同义词或相似 embedding 不足以静默合并 canonical Concept。

实体消歧至少考虑：

```text
source scope
local definition/context
hierarchy
existing aliases
relation neighborhood
```

Blocking ambiguity → `review_required` 或保持多个 candidate。

### 7. Relation Publication

#### D03-040

Relation 至少支持既有 canonical relation semantics；`PrerequisiteRelation` 的约束最严格。

#### D03-041 — Hard Prerequisite

`hard prerequisite` 自动发布必须满足以下之一：

1. 原文明确陈述且证据可回放；
2. versioned deterministic domain rule 且规则适用条件可审计；
3. 人工 ReviewDecision 接纳。

以下信息单独存在 MUST NOT 发布 hard prerequisite：

- 章节先后顺序；
- embedding 相似度；
- LLM 单次判断；
- “一般常识”；
- learner 当前错误表现。

#### D03-042

soft/contextual relation MAY 使用 model-assisted candidate，但仍需 evidence binding + reverse validation + versioned publication policy。

### 8. Reverse Verification

每个 model-inferred KnowledgeUnit/Relation 在 publish 前 MUST 执行独立于初始自由生成文本的验证步骤。实现 MAY 使用：

- deterministic evidence entailment rules；
- schema/rule validator；
- separate constrained model inference；
- human review。

若使用第二模型步骤，必须保存独立 inference/version，不得把“同一回答自我声称正确”当验证。

### 9. Graph Quality Checks

至少：

```text
duplicate identity
self-loop
hard prerequisite cycle
orphan evidence
invalid SourceSpan
conflicting relation
superseded revision reference
```

Hard prerequisite cycle MUST block affected edge publication；SYS06 发现的规划冲突只能回报 evidence，不得直接修改 graph。

### 10. PedagogicalAsset

来源材料中的 definition/example/exercise/solution 等 MAY 形成 source-derived asset candidate。

LLM 生成的 explanation/example/hint/exercise MUST 明确 `generated` provenance；未经对应验证规则不得伪装为 source fact。AssessmentItem 是否 active 仍由 SYS04 决定。

### 11. Publication / Review Semantics

`ReviewDecision` 是 SYS01-owned 领域决定，但本 Spec 不要求本轮实现完整人工审核 UI。

若无审核 UI：

- 可安全机器发布的对象按 policy publish；
- 其余保持 `review_required/candidate`；
- downstream executable LearningPlan MUST 只消费允许的 published/verified KnowledgeUnit；
- UI 可展示 candidate，但不得当成熟 truth。

### 12. Events

继续使用现有事件家族：

```text
ContentImported
ContentPublished
KnowledgeRelationPublished
processing failed / review-required events
```

事件 payload MUST 引用 exact revision、candidate/published refs、ExtractionRun、reason codes；不得复制整本材料。

### 13. Tests

MUST 覆盖：

1. deterministic structural candidate 兼容；
2. source-bound KU publish；
3. unsupported candidate rejection；
4. ambiguous entity 保持未合并；
5. model-only hard prerequisite 不发布；
6. explicit hard prerequisite 可验证发布；
7. cycle rejection；
8. reverse verification failure；
9. invalid SourceSpan blocks publish；
10. fixed extraction result replay 不调用 LLM；
11. projection rebuild 不改变 published knowledge。

### 14. Acceptance Criteria

- `D03-AC-001`：任一 published KnowledgeUnit/Relation 可追溯 exact MaterialRevision + SourceSpan + ExtractionRun/policy version。
- `D03-AC-002`：LLM JSON 不能直接成为 published truth。
- `D03-AC-003`：章节顺序不能自动产生 hard prerequisite。
- `D03-AC-004`：blocking entity ambiguity 不会被静默 merge。
- `D03-AC-005`：hard prerequisite cycle 不可进入 published graph。
- `D03-AC-006`：`minimal-binding-v1` 不重新成为成熟知识 truth。
- `D03-AC-007`：SYS04/SYS06/SYS08 不获得知识发布写权限。

### 15. Forbidden Implementations

禁止：

- 一次 LLM 调用同时抽取、验证、发布；
- model self-confidence 直接控制 truth；
- 用 user mastery/error 反向修改 canonical prerequisite；
- SourceChunk 直接升级成 KnowledgeUnit；
- 没有 evidence anchor 的自动知识发布；
- 为“图看起来完整”生成无证据 edges。

### 16. Freeze Decision

`SPEC-D03`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。若实现需要改变 relation ontology、引入新的 canonical relation type 或外部人工审核服务，必须先报告 `SPEC GAP`。
