# SPEC-D02 — Multi-Granularity Content Model Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D02`  
> 冻结日期：2026-08-08  
> Owner：SYS01 Content & Knowledge  
> 上游：`SPEC-D01`、`systems/01-content-knowledge.md`、`architecture/state-ownership.md`  
> 目的：冻结解析、知识抽取、引用、检索四类不同粒度，禁止继续用一个 chunk 同时承担全部职责。

## 1. Canonical Rule

Askora MUST 明确区分：

```text
DocumentNode      → 结构事实
EvidenceSpan      → 引用/证据角色
SemanticUnit      → 知识抽取工作单元
RetrievalChunk    → 检索投影
HierarchyNode     → 范围路由投影
```

这些对象/角色不得因为“文本内容相似”而被实现为同一长期 identity。

## 2. Ownership Classification

### D02-010

- `DocumentNode`：SYS01 internal structured truth；
- `EvidenceSpan`：不是新的 canonical object；它是一个或多个 canonical `SourceSpan` 在证据语境下的 typed reference；
- `SemanticUnit`：SYS01 extraction working record，绑定 exact MaterialRevision + segmentation version；
- `RetrievalChunk`：现有 canonical `SourceChunk` 的 SYS02-ready projection role；
- `HierarchyNode`：从 DocumentNode 派生的可重建范围路由 projection。

不得新增第二 KnowledgeUnit、第二 SourceSpan 或第二文档事实源。

## 3. EvidenceSpan

### D02-020

EvidenceSpan MUST 通过 SourceSpan refs 表达：

```yaml
evidence_span:
  source_span_ids: [uuid]
  evidence_role: source_fact|definition|example|counterexample|procedure|relation_evidence|assessment_support
  evidence_hash: string
```

`evidence_hash` 只用于完整性/去重，不是业务 identity。

### D02-021

任何影响 KnowledgeUnit/Relation publish 的 evidence MUST 最终回到当前 MaterialRevision 的可 replay SourceSpan。

## 4. SemanticUnit

### D02-030

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

### D02-031

SemanticUnit segmentation MUST 优先使用 DocumentNode boundary，再按语义/长度规则受控切分；MUST NOT 直接复用 RetrievalChunk 作为唯一 extraction unit。

### D02-032

相同 revision + segmentation version MUST deterministic 产生稳定 SemanticUnit 内容与 stable ordering。升级 segmentation version MAY 产生新 unit identity，但不得因此自动改变已发布 KnowledgeUnit identity。

## 5. RetrievalChunk / SourceChunk

### D02-040

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

### D02-041

重新分块、embedding 模型变化、reranker 变化、index 重建 MUST NOT 修改 KnowledgeUnit/Concept/Relation truth。

## 6. HierarchyNode

### D02-050

HierarchyNode 是 DocumentNode 的可重建路由 projection，用于：

- book/part/chapter/section scope routing；
- long-document retrieval narrowing；
- goal-to-knowledge candidate scope；
- UI knowledge map grouping。

不得把章节 parent/child 顺序解释为 prerequisite。

## 7. Processing Order

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

## 8. Boundary with SYS02

SYS01：

- 定义/生成 SourceChunk projection records；
- 维护 projection freshness/version metadata。

SYS02：

- 最终召回、过滤、排序、压缩并创建 EvidenceBundle；
- 不得反向修改 SemanticUnit/KnowledgeUnit/DocumentNode。

## 9. Boundary with SYS08 / LLM

SYS08 MAY 执行 SemanticUnit 上的 schema-constrained model inference，但：

```text
ModelInference
→ candidate only
→ SYS01 validation/publish path
```

LLM output MUST NOT 直接变成 KnowledgeUnit/Relation published truth。

## 10. Tests

MUST 覆盖：

1. 同一 EPUB 产生不同的 SemanticUnit 与 RetrievalChunk boundaries；
2. chunk rebuild 不改变 KnowledgeUnit stable ids；
3. SemanticUnit 可回到 SourceSpan；
4. HierarchyNode 不制造 prerequisite；
5. grader-only boundary 不与 learner-visible chunk 混合；
6. extraction segmentation version 可审计；
7. projection 删除后可重建。

## 11. Acceptance Criteria

- `D02-AC-001`：Knowledge candidate 不再以 SourceChunk identity 作为长期知识 identity。
- `D02-AC-002`：每个 SemanticUnit 可追溯至少一个 SourceSpan。
- `D02-AC-003`：SemanticUnit / RetrievalChunk / HierarchyNode 可独立重建和版本化。
- `D02-AC-004`：SourceChunk 重建不会修改 canonical KnowledgeUnit/Relation。
- `D02-AC-005`：章节 hierarchy 不自动形成 prerequisite edge。
- `D02-AC-006`：不存在 EvidenceSpan 第二 truth；引用仍落回 SourceSpan。

## 12. Forbidden Implementations

禁止：

- `chunk == KnowledgeUnit`；
- `chunk == SourceSpan`；
- 一个固定 chunk size 服务解析、抽取、检索、引用全部阶段；
- 重分块时重置全部知识 identity；
- HierarchyNode 作为 graph truth owner；
- SYS02 修改 SYS01 canonical state。

## 13. Freeze Decision

`SPEC-D02`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。如实现需要把 SemanticUnit 或 HierarchyNode 提升为跨系统 canonical public object，必须先报告 `SPEC GAP`。