# EXEC-054 — Required Core Test Realignment

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-053 DONE  
> Next：EXEC-055

## Objective

将 Required backend/test suite 从历史 auth/PostgreSQL/service-mode truth 重排为当前 Product Boundary + Learning Core + SQLite Production Local truth，并把 Optional/Historical tests 与 Required tests 物理或逻辑隔离。

本 EXEC 的 Product Boundary 不只验证“no-auth / no Redis / no Postgres”。Required oracle 必须覆盖最新 PRODUCT-POSITIONING 中对数据模型和产品边界最关键、可自动化验证的约束：Workspace isolation、Workspace ≠ Tenant、无 Global Material Library、Material↔LearningProject 多对多、Project 非学习启动门禁、两阶段删除语义、LLM 不直接写 Canonical State。

## Dependencies

- EXEC-052 test oracle classification DONE；
- EXEC-053 Production Local runtime DONE；
- stale runtime dependency 已不再参与默认 startup。

## Required Product Positioning

必须读取 PRODUCT-POSITIONING 的单用户、Local Web、SQLite、Workspace isolation、Workspace/Project/Material、Trash/Permanent Delete、Learning Evidence、Learner State、RAG/KnowledgeUnit boundary、LLM write boundary、Testing/Replay sections。

至少冻结以下 Required product-boundary assertions：

```text
single user / no auth
loopback Local Web
no Redis/Postgres/Docker runtime requirement
Workspace != Tenant / Organization
no default cross-Workspace retrieval or Global Material Library
Material belongs to Workspace
Material <-> LearningProject = many-to-many
LearningProject is not required to start learning from Material
remove Material from Project != delete Material
Normal Delete -> Trash -> Permanent Delete
LLM cannot directly mutate canonical persistence
```

## Required Specs

- `CI-100..204`
- `QUAL-V1-100..106`
- current Testing Standard 中未被 supersede 的 L0～L6 / OPVE / G0 / G1 contracts
- ADR-0015 / LID-*
- SYS01～SYS08 canonical specs
- current Workspace / Material / Project / Data Control contracts

## Current Reality

现有 `pytest tests` 将仍有效核心测试与大量历史 auth/account/PostgreSQL oracle 混为一个 release-like suite；这会导致正确的 v1 migration 被 stale tests 阻挡，也无法清晰证明 Product Boundary。

此外，若 Required tests 只覆盖基础设施切换，而不覆盖 Workspace/Material/Project/Delete/LLM ownership 等上位边界，就仍可能出现“CI 全绿但产品模型重新漂移”的问题。

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
- 不删除有 migration/security价值的 historical fixtures；
- 不把 Workspace isolation 改写成多租户/Tenant 测试；
- 不引入 Global Material Library / default cross-Workspace search 作为 Required truth；
- 不让“必须先创建 Project 才能学习 Material”成为 Required oracle；
- 不把从 Project 移除 Material 等同于删除 Material；
- 不用 frontend/UI 行为代替核心 domain/application boundary test；
- 不允许 LLM/mock provider 直接写 SQLite/canonical repositories 来简化测试。

## Implementation Tasks

1. 建立 `product-boundary` 自动测试：no-auth、loopback、no external infra requirement、Workspace != Tenant、LLM no canonical direct write 等。
2. 扩展 `product-boundary`：验证 Workspace scope 默认隔离，默认 retrieval/material query 不跨 Workspace；不存在 v1 Global Material Library current truth。
3. 增加 Material / LearningProject 关系测试：Material 必属 Workspace；同一 Material 可关联同 Workspace 内多个 Project；解除 ProjectMaterial 关系不删除 Material。
4. 增加 direct-Material learning boundary：在无 Learning Project 前提下，合法 Material 仍可创建/启动当前 canonical Learning Session / launch path；Project 不得成为 domain/application gate。
5. 增加删除边界测试：普通删除进入 Trash；Permanent Delete 必须显式/按已冻结策略触发；不得把普通删除直接等同不可逆删除。
6. 建立明确 Required suite composition：architecture + unit + contract + SQLite integration + deterministic OPVE core + product-boundary。
7. 将 `REWRITE_REQUIRED` 的 cross-user/auth tests 改写为 LocalOwner / Workspace / RetrievalScope / destructive-operation boundary。
8. 将 PostgreSQL/legacy auth/native desktop compatibility tests 移到 Optional/Historical test category。
9. 删除经 EXEC-052 认定无 migration/security/audit value 的 `DELETE_CANDIDATE`。
10. 保留并强化 Teaching Policy / Assessment / Learner State / Review / Retrieval / Content / Replay tests。
11. 统一 pytest markers/commands，使 Required、Optional、real-provider、historical migration 可独立执行。
12. 清理 `test_document_service.py` / `test_optimizations.py` 等游离脚本：纳入正常 suite 或明确 historical/dev purpose。
13. Required suite 不读取用户真实 AskoraData，不需要用户 API Key。

## Acceptance Criteria

- `E054-AC-001`：存在稳定 Required backend test command。
- `E054-AC-002`：Product Boundary tests 自动验证 no-auth / loopback / no Redis/Postgres/Docker requirement。
- `E054-AC-003`：Required suite 无 stale Account/JWT/password expected behavior。
- `E054-AC-004`：cross-user Required tests 已改写为 current LocalOwner/Workspace scope。
- `E054-AC-005`：PostgreSQL/native desktop/real-provider tests 可独立运行且默认不属于 Required。
- `E054-AC-006`：G0/OPVE/assessment/replay core 未弱化。
- `E054-AC-007`：Required suite 不依赖真实 AI key/network。
- `E054-AC-008`：无批量 skip/xfail 伪造通过。
- `E054-AC-009`：Required Product Boundary 自动证明 Workspace isolation、Workspace ≠ Tenant/Organization、无默认跨 Workspace Global Material Library。
- `E054-AC-010`：Required tests 证明 Material 属于 Workspace、Material↔LearningProject 为多对多，并且解除 ProjectMaterial 关系不删除 Material。
- `E054-AC-011`：无 Project 的 Material 可以沿 canonical application/domain path 开始学习；Project 不是 Required gate。
- `E054-AC-012`：普通删除与 Permanent Delete 两阶段语义有 Required 自动化证据。
- `E054-AC-013`：LLM/provider output 只能形成 structured proposal/validated input，不能直接拥有 canonical persistence write path。

## Required Tests

- Required backend suite itself；
- product-boundary marker/suite；
- Workspace isolation / RetrievalScope；
- Material-Project relationship / direct-Material learning；
- Trash / Permanent Delete boundary；
- LLM canonical-write ownership；
- optional marker dry-run/listing；
- ruff / formatter / mypy；
- test collection sanity；
- docs gate。

## Completion Report Format

报告：Required test count/categories、Product Boundary matrix、Workspace/Material/Project/Delete/LLM ownership evidence、rewritten/deleted/historical paths、remaining known failures、test commands、commit SHA、`E054 DONE` 或 blocker。
