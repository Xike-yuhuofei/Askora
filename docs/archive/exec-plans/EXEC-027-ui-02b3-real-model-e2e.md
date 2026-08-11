# EXEC-027 — UI-02B3 Real-model Guided Learning E2E

> Status：DONE / FROZEN
>
> Priority：P0 Real Product Acceptance
>
> Decision authority：user-delegated Codex
>
> Frozen Slice：`docs/archive/specs/vertical-slices/ui-02b3-real-model-guided-learning.md`

## Objective

把测试专用真实模型 renderer 收敛为 production SYS08 execution adapter，并用真实 EPUB、浏览器点击、
configured provider、PostgreSQL transcript/event 与刷新恢复完成真实端到端验收。

## Allowed Files

```text
docs/architecture/decisions/**
docs/specs/**
docs/planning/**
docs/archive/releases/**
docs/governance/document-inventory.md
apps/backend/app/contracts/book_learning.py
apps/backend/app/contracts/model_execution.py
apps/backend/app/orchestration/adaptive_execution.py
apps/backend/app/orchestration/learning_facade.py
apps/backend/app/orchestration/model_rendering.py
apps/backend/app/application/book_learning.py
apps/backend/app/api/v1/book_learning.py
apps/backend/app/services/rag_service.py
apps/backend/tests/contracts/test_book_learning_contract.py
apps/backend/tests/architecture/test_published_retrieval_boundary.py
apps/backend/tests/integration/test_book_learning_orchestration.py
apps/backend/tests/integration/test_published_knowledge_retrieval.py
apps/backend/tests/integration/test_v03_adaptive_execution_loop.py
apps/backend/tests/security/test_v03_adaptive_envelope_security.py
apps/backend/tests/evals/test_real_model_e2e.py
apps/frontend/src/pages/BookLearningLaunch.jsx
apps/frontend/src/test/BookLearningLaunch.test.jsx
apps/frontend/src/api/client.js
```

## Tasks

1. 实现 production policy-bound real-model renderer 与 fixed prompt version。
2. additive model_execution contract，保存 exact transcript metadata。
3. 追加最小化 ModelInferenceCompleted event，并保持 transaction/idempotency。
4. 定义 provider/empty/validation/persistence stable failure，不写 accepted/learner failure。
5. 补 unit/contract/integration/security/real-model tests。
6. 修复真实点击暴露的运行时阻塞，完成 browser/API/DB/reload/duplicate audit。
7. 运行 full gates，形成 release evidence 并归档 EXEC。

真实点击发现 canonical retrieval 把大型 `UserDocument.moderation_details` 与每个
`DocumentChunk` 重复联表返回；本 EXEC 明确授权改为 owner-scoped documents 单次读取、
chunks 独立读取，保持相同 publication/revision/visibility 校验语义并消除 O(chunks × metadata)
传输放大。

## Acceptance Criteria

- `EXEC027-AC-001`：UI02B3-AC-001～009 全部有当前证据。
- `EXEC027-AC-002`：无第二 TeachingAction owner、第二 tutor 或 legacy default path。
- `EXEC027-AC-003`：真实 provider/model/prompt/inference id 可追踪且不泄漏 secret/raw prompt。
- `EXEC027-AC-004`：Mock/template 不被报告为真实 E2E PASS。

## Required Gates

```bash
cd apps/backend
uv run pytest tests/contracts/test_book_learning_contract.py \
  tests/integration/test_book_learning_orchestration.py \
  tests/integration/test_v03_adaptive_execution_loop.py \
  tests/security/test_v03_adaptive_envelope_security.py
ASKORA_RUN_REAL_MODEL=1 uv run pytest tests/evals/test_real_model_e2e.py -s
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd apps/frontend
npm test -- --run
npm run build

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```
