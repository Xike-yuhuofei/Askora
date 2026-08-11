# EXEC-016 — UI-02A Canonical Library and Scoped Knowledge Map

> Priority：P1 Product Experience / Content Infrastructure  
> Status：READY（历史执行入口）；Final Status：DONE
> Depends on：EXEC-015 DONE  
> Baseline：backend 255 passed / 1 skipped；frontend 31 passed；lint/type/migration/build/audit PASS

## Objective

实现冻结的 UI-02A Vertical Slice：交付真实资料列表与上传处理、durable/recoverable document worker、deterministic source-bound KnowledgeUnit candidates、范围化 Knowledge Map/SourceSpan Inspector，并保持 SYS01/SYS02 ownership、安全与诚实状态语义。

## Dependencies

- EXEC-015 DONE；
- UI Redesign Spec Set FROZEN；
- 用户于 2026-08-08 明确采纳“方案 B + 拆分 UI-02A”；
- `ui-02a-library-knowledge-map.md` FROZEN；
- existing transactional outbox/recovery infrastructure available；
- baseline commands real PASS。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与：

- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/lifecycle-state-machines.md`
- `docs/specs/systems/01-content-knowledge.md`
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/ui/README.md`
- `docs/archive/specs/ui/information-architecture.md`
- `docs/archive/specs/ui/screen-contracts.md`
- `docs/specs/frontend/ui-read-model-contracts.md`
- `docs/archive/specs/ui/visual-system.md`
- `docs/archive/specs/ui/quality-and-migration.md`
- `docs/archive/specs/vertical-slices/ui-02a-library-knowledge-map.md`

## Current Reality

- `/library` is an honest UI-01 placeholder。
- document upload/list/status/delete/RAG exist and enforce current-user ownership, but page-safe version/source read models do not。
- content revisions/spans/chunks exist in SYS01-owned structured payload；`minimal-binding-v1` is file-level compatibility, not a mature map。
- document processing dispatch is non-durable process memory task；outbox infrastructure already supports retry/recovery。
- no knowledge map/source inspector endpoint or UI。

## Allowed Files

```text
docs/specs/README.md
docs/specs/ui/**
docs/archive/specs/vertical-slices/ui-02a-library-knowledge-map.md
docs/planning/**
docs/governance/document-inventory.md
docs/archive/releases/**
apps/backend/app/contracts/__init__.py
apps/backend/app/contracts/workspace.py
apps/backend/app/domains/content_knowledge/**
apps/backend/app/queries/__init__.py
apps/backend/app/queries/library.py
apps/backend/app/api/v1/documents.py
apps/backend/app/api/v1/workspace.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/documents/processing_worker.py
apps/backend/app/models/document.py
apps/backend/app/main.py
apps/backend/tests/contracts/test_library_workspace_contract.py
apps/backend/tests/architecture/test_library_query_boundary.py
apps/backend/tests/integration/test_library_workspace_query.py
apps/backend/tests/recovery/test_document_processing_recovery.py
apps/backend/tests/test_content_retrieval_v02.py
apps/backend/tests/test_document_safety.py
apps/frontend/README.md
apps/frontend/src/App.jsx
apps/frontend/src/api/documents.js
apps/frontend/src/api/workspace.js
apps/frontend/src/pages/Library.*
apps/frontend/src/pages/Unavailable.*
apps/frontend/src/test/**
.github/workflows/check_black_baseline.py
```

## Forbidden Changes

- 不实现 Goals/Path/Evidence profile/Focus 或未冻结 command；
- 不新增 KnowledgeUnit/Relation review/publish、tag/collection/note command；
- 不把 DocumentChunk、legacy KnowledgePoint、filename 或章节顺序当 published knowledge/relation；
- 不调用 LLM 自动发布知识事实，不引入 GraphRAG/图数据库/外部任务队列；
- 不改变 TeachingAction、LearnerState、Assessment、Plan、Review 写语义；
- 不返回 storage/internal absolute path、grader-only text、quarantined content；
- 不新增 production dependency、第二 content truth 或永久 dual-write；
- 不覆盖或提交本 EXEC 之外的用户修改。

## Implementation Tasks

1. 冻结 UI-02A Vertical Slice、Query contract 与本 EXEC；记录 baseline；独立 docs commit。
2. 定义 strict immutable Library/KnowledgeMap/SourceSpan workspace v1.0 contracts。
3. 升级 deterministic content extraction identity/version，生成 source-bound candidates，并提供 minimal-binding compatibility migration/rebuild path。
4. 将 document processing dispatch 迁移到 existing durable outbox worker；实现 startup reconciliation、stale recovery、bounded retry/idempotency tests。
5. 实现 current-user `WorkspaceLibraryQueryService`、`/workspace/library`、`/workspace/knowledge-map`、caps/stable ordering/private cache/error mapping。
6. 增加 contract、architecture、SQLite integration/auth/source/scope/security/recovery tests。
7. 实现 `/library` 三栏 desktop 与单列 narrow layout、upload/list/filter/status、node/relation text view、SourceSpan Inspector。
8. 增加 loading/empty/partial/stale/error/unauthorized、keyboard/focus/live-status/reduced-motion tests。
9. 运行 targeted/full gates；执行真实本地 API/upload/process/map/page 验证。
10. 更新 release evidence/index、归档 EXEC；独立本地 implementation commit。

## Acceptance Criteria

- `EXEC016-AC-001`：`UI02A-VSLICE-AC-001..012` 全部满足。
- `EXEC016-AC-002`：Library/KnowledgeMap strict schema 1.0、current-user scoped、source/version/availability/caps/stable ordering/private no-store。
- `EXEC016-AC-003`：document/outbox 同事务；restart/retry/repeated worker execution 不重复 canonical revision/projection。
- `EXEC016-AC-004`：v2 candidates 有 stable identity + SourceSpan；legacy binding 不冒充成熟 map；无证据 relation 不生成。
- `EXEC016-AC-005`：quarantined/unauthorized/grader-only/internal path 在 API/UI 不泄漏。
- `EXEC016-AC-006`：资料库真实 upload→processing→map→Inspector path 可运行，不依赖 mock 页面数据。
- `EXEC016-AC-007`：Document/SourceChunk/KnowledgeUnit/Relation 状态和文案不混淆。
- `EXEC016-AC-008`：关键页面状态、keyboard/focus、360px/desktop 自动/人工验证通过。
- `EXEC016-AC-009`：frontend/backend/docs gates 全部有真实结果。
- `EXEC016-AC-010`：无 blocking SPEC GAP、无新依赖/第二 truth/ownership regression；Learning Evidence 仍 insufficient。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts/test_library_workspace_contract.py tests/architecture/test_library_query_boundary.py tests/integration/test_library_workspace_query.py tests/recovery/test_document_processing_recovery.py tests/test_content_retrieval_v02.py tests/test_document_safety.py
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Spec / Query:
- frozen paths
- schema/source/auth/scope/caps behavior

Content / Recovery:
- revision/extraction compatibility
- outbox/restart/idempotency evidence

UI:
- library/map/inspector
- responsive/accessibility evidence

AC Matrix:
- EXEC016-AC-001 ... EXEC016-AC-010

Tests:
- command -> result

Learning Evidence Gate:
- LEARNING_EVIDENCE_INSUFFICIENT

SPEC GAP:
- none / details
```

## Resolved SPEC GAP

`check_black_baseline.py` 是 CI 静态检查的强制门禁。EXEC-016 授权修改的
`app/services/documents/document_service.py` 与 `tests/test_content_retrieval_v02.py`
同时是该门禁的 hash-locked legacy entries；本 Slice 按 Spec 修改并 Black 格式化后，
门禁要求从 `.github/workflows/check_black_baseline.py` 删除这两条 baseline 记录，但该
CI 文件不在 EXEC-016 Allowed Files。

用户于 2026-08-08 明确授权 EXEC-016 追加
`.github/workflows/check_black_baseline.py`，仅删除上述两条已格式化文件的 baseline entry。
该授权不改变业务语义、CI 策略或其他 legacy baseline。
