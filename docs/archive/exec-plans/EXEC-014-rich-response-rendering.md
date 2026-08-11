# EXEC-014 — Rich Response Rendering

> Priority：P1 Product Capability
> Status：READY
> Depends on：EXEC-013

## Objective

实现冻结的 v0.3.1 Rich Response Rendering Vertical Slice：canonical reply 生成并持久化 `RenderPayloadV1`，前端安全渲染 Markdown/GFM/KaTeX/typed cards/citations，旧消息、普通响应、历史 query、SSE final/replay 保持兼容。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与：

- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/render-content-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/vertical-slices/v0.3.1-rich-response-rendering.md`

## Current Reality

- `CanonicalTurnResult.reply_text`、LLM response、SSE chunk 与 `DialogMessage.content` 都是 string/text；
- Chat 页面使用 `<p>{msg.content}</p>`，只保留换行；
- frontend 无 Markdown/math renderer 与 automated component test command；
- API-030 预留 citation event，但当前 SSE 主要发送 content/delta/final compatibility events；
- `dialog_messages` 没有 structured render payload。

## Allowed Files

```text
docs/specs/**                         # 仅本 EXEC 前已冻结的引用，不再改语义
docs/planning/**
apps/backend/app/contracts/**
apps/backend/app/orchestration/learning_facade.py
apps/backend/app/services/dialog/dialog_service.py
apps/backend/app/api/v1/dialog.py
apps/backend/app/models/dialog.py
apps/backend/alembic/versions/**
apps/backend/tests/**
apps/frontend/package.json
apps/frontend/package-lock.json
apps/frontend/src/components/messages/**
apps/frontend/src/pages/Chat.jsx
apps/frontend/src/pages/Chat.css
apps/frontend/src/test/**
apps/frontend/vite.config.js
.github/workflows/ci.yml
.github/workflows/check_black_baseline.py
```

## Forbidden Changes

- 不改变 TeachingAction、StrategyFamily、assessment/mastery/plan/review 语义；
- 不启用 raw HTML、MDX、`dangerouslySetInnerHTML`；
- 不执行模型指定组件、脚本、代码块或 arbitrary card command；
- 不用在线 LLM 回填历史消息；
- 不删除/弱化既有测试；
- 不覆盖工作区内与本 EXEC 无关的用户修改。

## Implementation Tasks

1. 定义 strict/frozen `RenderPayloadV1` discriminated union 与 deterministic Markdown baseline。
2. 扩展 canonical result、dialog persistence、normal/history/SSE final/replay serialization。
3. 新增 nullable JSON Alembic migration 与 migration/round-trip tests。
4. 新增 RichMessage/Markdown/Card/Citation typed components。
5. 接入 CommonMark/GFM/remark-math/KaTeX，禁用 raw HTML、unsafe URLs、remote images 与 executable code。
6. 增加 frontend component tests 与 production build gate。
7. 把 frontend component tests 纳入 CI，并运行 backend targeted/full applicable tests、Ruff、mypy；归档 EXEC 与 completion evidence。

## Acceptance Criteria

- `EXEC014-AC-001`：`RENDER-AC-001..008` 全部满足。
- `EXEC014-AC-002`：new assistant completion 持久化 schema 1.0 payload；user/legacy message 为 null。
- `EXEC014-AC-003`：idempotent replay 返回相同 payload。
- `EXEC014-AC-004`：normal/history/SSE final payload equivalent。
- `EXEC014-AC-005`：Markdown/GFM/math/five card variants/citations render tests pass。
- `EXEC014-AC-006`：XSS/raw HTML/unsafe URL/remote image/invalid math security tests pass。
- `EXEC014-AC-007`：migration upgrade/downgrade/compatibility verified。
- `EXEC014-AC-008`：frontend build、backend tests/lint/type gates pass。
- `EXEC014-AC-009`：无 blocking SPEC GAP、无 TeachingAction envelope regression。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts tests/migrations tests/test_dialog_canonical_entry.py tests/security
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary

cd apps/frontend
npm test -- --run
npm run build
```

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Contract / migration:
- RenderPayload version
- fallback
- DB migration

Transport:
- normal
- history
- SSE final/replay

Renderer / security:
- Markdown/GFM/math/cards/citations
- raw HTML/unsafe URL/remote image/code behavior

AC Matrix:
- EXEC014-AC-001 ... EXEC014-AC-009

Tests:
- command -> result

SPEC GAP:
- none / details
```
