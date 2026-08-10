# EXEC-054 — Required Core Test Realignment

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-053 DONE  
> Next：EXEC-055

## Objective

将 Required backend/test suite 从历史 auth/PostgreSQL/service-mode truth 重排为当前 Product Boundary + Learning Core + SQLite Production Local truth，并把 Optional/Historical tests 与 Required tests 物理或逻辑隔离。

## Dependencies

- EXEC-052 test oracle classification DONE；
- EXEC-053 Production Local runtime DONE；
- stale runtime dependency 已不再参与默认 startup。

## Required Product Positioning

必须读取 PRODUCT-POSITIONING 的单用户、Local Web、SQLite、Workspace isolation、Learning Evidence、Learner State、RAG/KnowledgeUnit boundary、LLM write boundary、Testing/Replay sections。

## Required Specs

- `CI-100..204`
- `QUAL-V1-100..106`
- current Testing Standard 中未被 supersede 的 L0～L6 / OPVE / G0 / G1 contracts
- ADR-0015 / LID-*
- SYS01～SYS08 canonical specs

## Current Reality

现有 `pytest tests` 将仍有效核心测试与大量历史 auth/account/PostgreSQL oracle 混为一个 release-like suite；这会导致正确的 v1 migration 被 stale tests 阻挡，也无法清晰证明 Product Boundary。

## Allowed Files

```text
apps/backend/tests/**
apps/backend/pyproject.toml
apps/backend/test_document_service.py
apps/backend/test_optimizations.py
.github/**
docs/specs/quality/**
docs/exec-plans/**
```

除修复测试暴露出的当前 contract bug 外，不得修改 production code；若发现 production bug，必须报告并仅在本 EXEC 明确允许的最小范围内修复，否则返回 SPEC/EXEC GAP。

## Forbidden Changes

- 不用 skip/xfail 隐藏失败；
- 不降低 G0 / hard-rule / security assertions；
- 不把 Mock 当真实 Provider current availability；
- 不继续让 password/JWT/AuthSession/cross-user service-mode 成为 Required oracle；
- 不把 PostgreSQL compatibility 作为 SQLite v1 release blocker；
- 不删除有 migration/security价值的 historical fixtures。

## Implementation Tasks

1. 建立 `product-boundary` 自动测试：no-auth、loopback、no external infra requirement、Workspace != Tenant、LLM no canonical direct write 等；
2. 建立明确 Required suite composition：architecture + unit + contract + SQLite integration + deterministic OPVE core；
3. 将 `REWRITE_REQUIRED` 的 cross-user/auth tests 改写为 LocalOwner / Workspace / RetrievalScope / destructive-operation boundary；
4. 将 PostgreSQL/legacy auth/native desktop compatibility tests 移到 Optional/Historical test category；
5. 删除经 EXEC-052 认定无 migration/security/audit value 的 `DELETE_CANDIDATE`；
6. 保留并强化 Teaching Policy / Assessment / Learner State / Review / Retrieval / Content / Replay tests；
7. 统一 pytest markers/commands，使 Required、Optional、real-provider、historical migration 可独立执行；
8. 清理 `test_document_service.py` / `test_optimizations.py` 等游离脚本：纳入正常 suite 或明确 historical/dev purpose；
9. Required suite 不读取用户真实 AskoraData，不需要用户 API Key。

## Acceptance Criteria

- `E054-AC-001`：存在稳定 Required backend test command；
- `E054-AC-002`：Product Boundary tests 自动验证 no-auth / loopback / no Redis/Postgres/Docker requirement；
- `E054-AC-003`：Required suite 无 stale Account/JWT/password expected behavior；
- `E054-AC-004`：cross-user Required tests 已改写为 current LocalOwner/Workspace scope；
- `E054-AC-005`：PostgreSQL/native desktop/real-provider tests 可独立运行且默认不属于 Required；
- `E054-AC-006`：G0/OPVE/assessment/replay core未弱化；
- `E054-AC-007`：Required suite 不依赖真实 AI key/network；
- `E054-AC-008`：无批量 skip/xfail 伪造通过。

## Required Tests

- Required backend suite itself；
- optional marker dry-run/listing；
- ruff / formatter / mypy；
- test collection sanity；
- docs gate。

## Completion Report Format

报告：Required test count/categories、rewritten/deleted/historical paths、remaining known failures、test commands、commit SHA、`E054 DONE` 或 blocker。