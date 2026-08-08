# EXEC-017 — Structure-Preserving EPUB Ingestion & Source Replay

> Priority：P0 Book-to-Learning / SYS01 Foundation  
> Status：READY  
> Depends on：EXEC-016 DONE；SPEC-D01～D06 FROZEN  
> Primary Spec：SPEC-D01  
> Execution rule：完成并归档本 EXEC 后，方可进入 EXEC-018。

## Objective

把当前 EPUB 的 `strip HTML → flat text → PlainText chunk` 路径升级为 **structure-preserving canonical ingestion**：

```text
RawAsset
→ existing security gate
→ MaterialRevision
→ EPUB parser
→ DocumentIR
→ DocumentNode hierarchy
→ canonical linearized text
→ SourceSpan(node_id)
→ replay to original EPUB location
```

必须复用 UI-02A 已完成的 durable upload / outbox / quarantine / reinspection；不得创建第二条 document processing truth。

## Dependencies

- EXEC-016 / UI-02A DONE；
- 当前 `main` 上 `deterministic-structure-v2`、MaterialRevision、SourceSpan 与 durable processing 可用；
- SPEC-D01～D06 已冻结；
- 不新增生产依赖；`ebooklib` 等现有依赖范围内实现。

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
- `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

## Current Reality

- 当前 EPUB parser 读取 document items 后去除 script/style/HTML，压平成 `full_text`，再进入 PlainText chunking；
- `ParsedContent` 主要只有 `full_text/chunks/metadata`，没有 DocumentIR / DocumentNode；
- current SourceSpan 主要基于 material-linearized offsets，`node_id` 尚未成为真实结构 replay path；
- UI-02A 的 durable processing、安全扫描、revision、candidate 与 SourceChunk projection 必须保持兼容。

## Allowed Files

```text
docs/exec-plans/**
docs/releases/**
docs/document-inventory.md
apps/backend/app/contracts/content.py
apps/backend/app/domains/content_knowledge/**
apps/backend/app/services/documents/parsers.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/documents/processing_worker.py
apps/backend/app/models/document.py
apps/backend/tests/contracts/**
apps/backend/tests/integration/**
apps/backend/tests/recovery/**
apps/backend/tests/fixtures/**
apps/backend/tests/test_content_retrieval_v02.py
apps/backend/tests/test_document_safety.py
```

如完成本 EXEC 必须修改未列出的公共 schema、生产依赖、跨系统模块或 CI 策略，MUST `BLOCKED_BY_SPEC_GAP`；不得自行扩大范围。

## Forbidden Changes

- 不实现知识 LLM extraction / publish pipeline；
- 不实现 Goal mapping / diagnostics / planner bootstrap；
- 不改变 SYS02～SYS08 ownership；
- 不改变现有 SourceSpan 公共字段含义；只可按 SPEC-D01 让 `node_id` 指向 SYS01 DocumentNode；
- 不伪造 EPUB CFI；可靠生成不了时使用 `spine + href + dom_path + content hash`；
- 不新增外部解析服务或未冻结生产依赖；
- 不回退 durable processing、quarantine/reinspection、current-user security；
- 不允许 canonical EPUB parse 继续只有 flat text/chunk truth。

## Implementation Tasks

1. 在 SYS01 内定义/实现 versioned `DocumentIR`、`DocumentNode` 与 typed `source_locator` working/persisted records。
2. 重构 EPUB parser：保持 spine reading order、TOC/nav hierarchy、XHTML heading、paragraph/list、footnote/endnote、image/figure、internal anchor/link metadata。
3. 生成 deterministic canonical linearized text，并建立 node → text range 的稳定映射。
4. 让新 SourceSpan 设置 `node_id`，同时保持现有 start/end offset 兼容。
5. 实现 `EXACT | RECOVERED | FAILED` source replay；hash/context 验证失败不得标 EXACT。
6. parser semantic version 进入 revision identity；升级不得原地覆盖旧 MaterialRevision。
7. 将 DocumentIR/DocumentNode persistence/rebuild 接入现有 durable processing，不建立第二处理队列。
8. 补充合法最小 EPUB fixture，覆盖 spine/nav/footnote/internal link/replay；不得提交受版权保护的完整商业电子书。
9. 增加 malformed/archive/path traversal/quarantine regression。
10. 运行 targeted + full backend/doc gates；完成后归档 EXEC-017，并记录实现 commit / release evidence。

## Acceptance Criteria

- `EXEC017-AC-001`：`D01-AC-001..007` 全部满足。
- `EXEC017-AC-002`：固定 EPUB + parser version deterministic 生成相同 semantic DocumentIR / structure hash。
- `EXEC017-AC-003`：任一测试 SourceSpan 可经 `node_id → source_locator` 重放至原 XHTML 位置。
- `EXEC017-AC-004`：spine/TOC/heading/footnote/internal-link 结构未在 canonical parse 阶段丢失。
- `EXEC017-AC-005`：replay FAILED 的 span 可被 downstream 明确识别，不能伪装可发布证据。
- `EXEC017-AC-006`：parser semantic version 变化形成可追踪新 revision，不静默覆盖。
- `EXEC017-AC-007`：UI-02A durable processing/quarantine/reinspection/idempotency regression 全部通过。
- `EXEC017-AC-008`：无新生产依赖、第二 SourceSpan/document truth 或 ownership regression。

## Required Tests

```bash
cd apps/backend
uv run pytest tests -k "epub or source_span or document_processing or document_safety"
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

Parser / IR:
- parser version
- DocumentIR / DocumentNode implementation
- structure retained

Source Replay:
- EXACT / RECOVERED / FAILED evidence
- SourceSpan compatibility

Recovery / Security:
- durable processing
- quarantine/reinspection
- malformed/archive safety

AC Matrix:
- EXEC017-AC-001 ... EXEC017-AC-008

Tests:
- command -> result

SPEC GAP:
- none / details

Commit:
- <sha>
```
