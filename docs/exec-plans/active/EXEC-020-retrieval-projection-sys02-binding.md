# EXEC-020 — Published Knowledge → Retrieval Projection & SYS02 Binding

> Priority：P0 Book-to-Learning / SYS01→SYS02 Handoff  
> Status：READY  
> Depends on：EXEC-019 DONE  
> Primary Specs：SPEC-D02、SPEC-D03、SYS02  
> Execution rule：可与 EXEC-021 在 EXEC-019 DONE 后独立实现；EXEC-023 需要本 EXEC DONE。

## Objective

把已发布/可用 canonical knowledge 与 multi-granularity content 安全投影到现有 SYS02：

```text
Published KnowledgeUnit / Relation
+ SourceSpan
+ Hierarchy
→ rebuildable SourceChunk / retrieval projections
→ current HybridEvidenceRetriever
→ EvidenceBundle
```

目标是让后续 TeachingAction 能检索到有 exact source evidence、正确 role/exposure/scope 的资料；不重写 SYS02 owner 语义。

## Dependencies

- EXEC-019 DONE；
- existing HybridEvidenceRetriever / EvidenceBundle 已由 v0.3 baseline 实现；
- SourceChunk 仍为 projection，不是 knowledge truth。

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
- `docs/specs/systems/01-content-granularity.md`
- `docs/specs/systems/01-knowledge-publish-pipeline.md`
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Current Reality

- SYS02 已有 hybrid lexical+dense/RRF baseline、scope/exposure/citation filtering；
- current projection 可携带 `knowledge_unit_ids/source_span_ids/pedagogical_role/exposure`，但此前 knowledge model 主要是 structural candidates；
- 本 EXEC 要把 EXEC-019 的 published knowledge/version/freshness 正确接入，而不是另写 retrieval engine。

## Allowed Files

```text
docs/exec-plans/**
docs/releases/**
docs/document-inventory.md
apps/backend/app/contracts/content.py
apps/backend/app/contracts/learning.py
apps/backend/app/domains/content_knowledge/**
apps/backend/app/domains/retrieval/**
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/rag_service.py
apps/backend/app/models/document.py
apps/backend/tests/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/replay/**
apps/backend/tests/test_content_retrieval_v02.py
```

## Forbidden Changes

- 不重新定义 EvidenceBundle owner；
- 不改变 TeachingAction / answer-exposure canonical vocabulary；
- 不把 candidate-only/stale/invalid-anchor knowledge 放入 executable learner-visible bundle；
- 不使 vector/graph index 成为第二 truth；
- 不默认引入 GraphRAG；
- 不允许 cache 忽略 source scope / exposure / revision / index versions；
- 不实现 Goal mapping/diagnostic。

## Implementation Tasks

1. 从 EXEC-019 published/eligible knowledge rebuild retrieval projection，附 exact KU/relation/span/hierarchy/version refs。
2. projection freshness/index version 必须与 MaterialRevision / knowledge publication version 对齐。
3. 根据 source-derived PedagogicalAsset / SemanticUnit role 生成 conservative pedagogical role/exposure/allowed_use metadata。
4. 确保 candidate-only、review_required、rejected、superseded、invalid-anchor、quarantined data 不进入 canonical learner-visible retrieval path。
5. 接入现有 HybridEvidenceRetriever，不建立第二 retriever；保留 lexical+dense/RRF、hard scope/exposure filter、citation validation、degrade path。
6. 实现 projection rebuild/idempotency/cache invalidation tests。
7. 验证 grader-only isolation 与 SYS05 envelope tightening-only。
8. 用 published knowledge fixture 生成真实 EvidenceBundle，并可回到 SourceSpan。
9. full gates + 归档 EXEC-020。

## Acceptance Criteria

- `EXEC020-AC-001`：任一 selected EvidenceBundle item 可追踪 published/eligible KU + replayable SourceSpan。
- `EXEC020-AC-002`：candidate/review_required/rejected/stale/invalid-anchor content 不静默进入 executable learner-visible bundle。
- `EXEC020-AC-003`：projection 删除后可从 canonical records 重建，knowledge truth 不变。
- `EXEC020-AC-004`：scope/exposure/revision/index version 参与安全过滤/cache identity。
- `EXEC020-AC-005`：SYS02 只能收紧 TeachingAction envelope，不能扩大。
- `EXEC020-AC-006`：grader-only solution 不泄漏。
- `EXEC020-AC-007`：existing HybridEvidenceRetriever 为唯一默认 EvidenceBundle path，无第二 retriever。
- `EXEC020-AC-008`：无 vector/graph second truth 或 GraphRAG mandatory dependency。

## Required Tests

```bash
cd apps/backend
uv run pytest tests -k "retrieval or evidence_bundle or content or exposure or citation"
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

Projection:
- source/knowledge/index versions
- rebuild evidence

SYS02:
- hybrid retrieval path
- scope/exposure/citation behavior
- degraded behavior

AC Matrix:
- EXEC020-AC-001 ... EXEC020-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

Commit:
- <sha>
```
