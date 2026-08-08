# EXEC-019 — Canonical Knowledge Verification & Publication Pipeline

> Priority：P0 Book-to-Learning / SYS01 Knowledge Truth  
> Status：READY  
> Depends on：EXEC-018 DONE  
> Primary Spec：SPEC-D03  
> Execution rule：完成并归档本 EXEC 后，方可进入 EXEC-020 / EXEC-021。

## Objective

把 UI-02A 的 source-bound structural candidates 扩展为真正的 SYS01 canonical knowledge pipeline：

```text
SemanticUnit
→ candidate extraction
→ evidence binding
→ entity resolution
→ normalization
→ relation validation
→ reverse verification
→ duplicate/conflict/cycle checks
→ versioned publication policy
→ published | review_required | rejected
```

本 EXEC 的目标是**知识事实发布正确性**，不是让图看起来更丰富。

## Dependencies

- EXEC-018 DONE；
- replayable SourceSpan / SemanticUnit 可用；
- UI-02A `deterministic-structure-v2` candidate 作为兼容基线；
- 不要求完整人工 review UI。

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
- `docs/specs/systems/01-knowledge-publish-pipeline.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Current Reality

- current `deterministic-structure-v2` 主要从显式 heading 生成 source-bound `KnowledgeUnit(status=candidate)`；
- relation 当前保持为空；
- 尚无 ConceptCandidate / RelationCandidate / PedagogicalAssetCandidate / ExtractionRun / publication policy 主路径；
- 当前代码已正确避免把章节顺序直接伪装成 prerequisite，本 EXEC 必须保持该保守边界。

## Allowed Files

```text
docs/exec-plans/**
docs/releases/**
docs/document-inventory.md
apps/backend/app/contracts/content.py
apps/backend/app/contracts/**
apps/backend/app/domains/content_knowledge/**
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/knowledge_graph/**
apps/backend/app/models/document.py
apps/backend/app/models/knowledge.py
apps/backend/app/infrastructure/**
apps/backend/tests/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/replay/**
apps/backend/tests/fixtures/**
apps/backend/tests/test_content_retrieval_v02.py
```

`apps/backend/app/infrastructure/**` 仅允许复用现有 ledger/outbox/persistence adapter；不得引入新的基础设施产品。

## Forbidden Changes

- 不允许一次 LLM 调用完成 extraction + validation + publish；
- 不将 model confidence 当 calibrated truth；
- 不以章节顺序、embedding 相似、LLM 单次判断发布 hard prerequisite；
- 不修改 SYS03 mastery / SYS04 assessment / SYS06 plan；
- 不新增 canonical relation ontology；
- 不实现完整人工审核产品/UI；
- 不使用 SourceChunk 直接升级 KnowledgeUnit；
- 不为“图完整”制造无证据 edge。

## Implementation Tasks

1. 定义/实现 SYS01 internal candidate families：ConceptCandidate、KnowledgeUnitCandidate、RelationCandidate、PedagogicalAssetCandidate。
2. 实现 `ExtractionRun`，固定 parser/semantic-segmentation/extractor/model/prompt/schema/publication-policy/input revision versions。
3. 将 deterministic structural candidates 接入统一 candidate pipeline。
4. 如使用 LLM extraction，只能经 SYS08 bounded structured inference，结果持久化为 candidate；model unavailable 必须有可解释降级。
5. 实现 current-revision evidence binding 与 invalid/replay-failed anchor gate。
6. 实现 conservative entity resolution；blocking ambiguity 保持多个 candidate 或 `review_required`。
7. 实现 relation validation/reverse verification；hard prerequisite 只允许 SPEC-D03 指定的 evidence/rule/review 来源。
8. 实现 duplicate/self-loop/hard-cycle/orphan/conflict/superseded-ref checks。
9. 实现 immutable/versioned `KnowledgePublicationPolicy` 与 publish/reject/review_required reason codes。
10. 发布事件引用 exact revision/candidate/ExtractionRun/policy refs；replay 使用持久化 candidate/result，不在线重跑 LLM。
11. PedagogicalAsset candidate 明确 source-derived / generated provenance；不得越权激活 AssessmentItem。
12. 增加完整 knowledge-publish contract/replay/security tests，归档 EXEC-019。

## Acceptance Criteria

- `EXEC019-AC-001`：`D03-AC-001..007` 全部满足。
- `EXEC019-AC-002`：任一 published KU/Relation 可追踪 MaterialRevision + SourceSpan + ExtractionRun + publication policy。
- `EXEC019-AC-003`：LLM JSON / model-only hard prerequisite 不可直接 publish。
- `EXEC019-AC-004`：explicit/rule-backed prerequisite fixture 可合法发布；章节顺序 fixture 不可发布。
- `EXEC019-AC-005`：hard prerequisite cycle、自环、invalid anchor、blocking entity ambiguity 均被阻止或 review_required。
- `EXEC019-AC-006`：fixed persisted extraction replay 不调用在线 LLM。
- `EXEC019-AC-007`：`minimal-binding-v1` 保持 legacy compatibility，不重新成为成熟 truth。
- `EXEC019-AC-008`：SYS01 仍是 knowledge publication 唯一 writer。

## Required Tests

```bash
cd apps/backend
uv run pytest tests -k "knowledge or content or relation or replay or source_span"
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

Candidate / Extraction:
- candidate families
- ExtractionRun versions
- model boundary

Publication:
- policy version
- verification
- hard prerequisite gate
- graph quality checks

Replay:
- no-online-LLM evidence

AC Matrix:
- EXEC019-AC-001 ... EXEC019-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

Commit:
- <sha>
```
