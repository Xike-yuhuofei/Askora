# EXEC-018 — Multi-Granularity Content Model & Rebuildable Projections

> Priority：P0 Book-to-Learning / SYS01-SYS02 Boundary  
> Status：READY  
> Depends on：EXEC-017 DONE  
> Primary Spec：SPEC-D02  
> Execution rule：完成并归档本 EXEC 后，方可进入 EXEC-019。

## Objective

在 DocumentIR / DocumentNode / SourceSpan 基础上实现：

```text
SourceSpan
→ SemanticUnit
→ knowledge-extraction input

DocumentNode
→ HierarchyNode projection

SourceSpan / canonical content
→ RetrievalChunk(SourceChunk) projection
```

明确分离引用、知识抽取、检索和层级路由粒度；禁止继续让一个 chunk 承担所有职责。

## Dependencies

- EXEC-017 DONE；
- SPEC-D02 Frozen；
- current SourceChunk / DocumentChunk projection 与 UI-02A Knowledge Map 可兼容迁移/重建。

## Required Specs

Codex MUST 读取：

- `AGENTS.md`
- `docs/specs/README.md`
- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/interfaces/content-ingestion-contract.md`
- `docs/specs/systems/01-content-knowledge.md`
- `docs/specs/systems/01-content-granularity.md`
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Current Reality

- 当前 content processing 主要从 parser chunks 同时建立 SourceSpan 与 SourceChunk；
- `deterministic-structure-v2` 从 SourceSpan heading 形成 candidate，但没有独立 SemanticUnit；
- Hierarchy routing 尚未形成明确可重建 projection；
- 当前 DocumentChunk 可作为迁移起点，但不得继续隐含 `chunk == extraction unit == citation unit`。

## Allowed Files

```text
docs/exec-plans/**
docs/releases/**
docs/document-inventory.md
apps/backend/app/contracts/content.py
apps/backend/app/domains/content_knowledge/**
apps/backend/app/domains/retrieval/**
apps/backend/app/services/documents/document_service.py
apps/backend/app/models/document.py
apps/backend/app/queries/library.py
apps/backend/tests/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/recovery/**
apps/backend/tests/test_content_retrieval_v02.py
```

## Forbidden Changes

- 不实现最终 KnowledgeUnit/Relation publication policy（EXEC-019）；
- 不改 SYS02 的 TeachingAction ownership/envelope 语义；
- 不把 SemanticUnit / HierarchyNode 提升为新的跨系统 canonical truth；
- 不将章节 parent/child 自动转成 prerequisite；
- 不因重新分块修改 canonical KnowledgeUnit stable identity；
- 不把 EvidenceSpan 建成第二 SourceSpan 表；
- 不引入向量数据库/图数据库作为必需基础设施。

## Implementation Tasks

1. 实现 versioned deterministic `SemanticUnit` segmentation：优先 DocumentNode boundary，再做受控语义/长度切分。
2. EvidenceSpan 仅实现为 SourceSpan refs + typed evidence role/value object，不建立第二 evidence truth。
3. 将 current SourceChunk/DocumentChunk 明确为 RetrievalChunk projection；补齐 exact revision/span/version/hierarchy/visibility metadata。
4. 建立可重建 HierarchyNode projection，支持 book/part/chapter/section scope。
5. 将 extraction segmentation version 与 retrieval segmentation/index version 分离。
6. 实现 projection rebuild：删除/rebuild SemanticUnit working set、RetrievalChunk、Hierarchy projection 不改变 canonical KnowledgeUnit/Relation。
7. 保持 grader-only / learner-visible boundary，不允许 protected material 被混入 learner-visible chunk。
8. 更新 UI-02A knowledge-map query 的 grouping/availability，仅消费 projection，不取得 truth ownership。
9. 增加 deterministic ordering、rebuild/idempotency、no-prerequisite-from-hierarchy architecture tests。
10. 完成 full gates，归档 EXEC-018。

## Acceptance Criteria

- `EXEC018-AC-001`：`D02-AC-001..006` 全部满足。
- `EXEC018-AC-002`：同一 EPUB 至少存在可证明不同边界的 SemanticUnit 与 RetrievalChunk fixture。
- `EXEC018-AC-003`：所有 SemanticUnit 可回到 SourceSpan。
- `EXEC018-AC-004`：HierarchyNode 可重建且不生成 prerequisite truth。
- `EXEC018-AC-005`：SourceChunk projection 删除/重建不改变 canonical KU/Relation。
- `EXEC018-AC-006`：grader-only boundary 与 exposure metadata 回归通过。
- `EXEC018-AC-007`：不存在 EvidenceSpan / HierarchyNode 第二 truth。
- `EXEC018-AC-008`：SYS01/SYS02 single-writer boundary architecture tests PASS。

## Required Tests

```bash
cd apps/backend
uv run pytest tests -k "content or retrieval or library or source_span"
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Granularity:
- SemanticUnit
- EvidenceSpan refs
- RetrievalChunk
- HierarchyNode

Rebuild:
- versions
- projection rebuild evidence
- KU identity preservation

AC Matrix:
- EXEC018-AC-001 ... EXEC018-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

Commit:
- <sha>
```
