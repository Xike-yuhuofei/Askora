# EXEC-055 — Local Data Migration, Recovery & Rebuild Gate

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-054 DONE  
> Next：EXEC-056 / EXEC-057

## Objective

把 Askora v1 最重要的数据正确性要求转化为 Required automation：SQLite migration、升级失败保护、Derived Data 重建、后台任务中断恢复、Learning Evidence 删除后的 Learner State 重算。

## Dependencies

- EXEC-053 Production Local runtime DONE；
- EXEC-054 Required core suite 已稳定；
- SQLite 是当前 production persistence truth。

## Required Product Positioning

必须读取 Durable/Derived Data、后台任务、Schema Migration、Backup/Restore、Evidence recompute、工程优先级章节。

## Required Specs

- `CI-300..403`
- `QUAL-V1-105`
- Persistence / Schema Versioning / Recovery contracts
- Learner Model / Assessment / Review Scheduler contracts
- Testing Standard L5 retained clauses

## Current Reality

当前 CI 主要执行 Alembic `upgrade → check → downgrade → upgrade`，但这不足以证明真实用户数据升级安全、Derived Data 可重建或进程中断后任务可恢复。

## Allowed Files

```text
apps/backend/app/**
apps/backend/alembic/**
apps/backend/tests/migrations/**
apps/backend/tests/recovery/**
apps/backend/tests/integration/**
apps/backend/tests/fixtures/**
apps/backend/tests/unit/**
.github/**
docs/specs/quality/**
docs/exec-plans/**
```

只允许与 migration/recovery/rebuild/idempotency/evidence recompute 直接相关的 production 改动。

## Forbidden Changes

- 不把 Derived Data 提升为不可替代 canonical truth；
- 不通过删除旧数据库 fixture 逃避 migration；
- 不以 downgrade-to-base 作为唯一 migration safety 证据；
- 不在 replay/rebuild 中调用在线 LLM；
- 不在失败时静默覆盖/删除旧 durable data；
- 不将 learner/system failure 误记为 learner incorrect。

## Implementation Tasks

1. fresh SQLite → head → startup validation；
2. representative legacy SQLite fixtures → backup/preflight → migration → validation；
3. migration failure 路径证明旧 durable data preserved / rollback or forward-fix boundary明确；
4. data directory `schema_version` / reader/writer compatibility 检查；
5. 删除/recreate Chunks、Indexes、cached retrieval 等 Derived Data 并验证可重建；
6. 对可重建 Learner State/projection 验证 deterministic recompute；
7. 删除/invalidate Learning Evidence 后验证相关 Learner State 不保留旧值；
8. background job `running → process interruption → restart → interrupted/retry/resume`；
9. 同 Material 同类 rebuild 去重/互斥；
10. retry/idempotency 验证不重复破坏 durable state。

## Acceptance Criteria

- `E055-AC-001`：fresh SQLite migration PASS；
- `E055-AC-002`：至少一个 representative legacy SQLite fixture migration PASS；
- `E055-AC-003`：migration failure 不破坏旧 durable data；
- `E055-AC-004`：不兼容 data dir fail closed；
- `E055-AC-005`：至少一类 retrieval/index derived data 删除后可重建；
- `E055-AC-006`：Learner State/projection 可从 evidence 重建；
- `E055-AC-007`：Evidence 删除触发正确 recompute；
- `E055-AC-008`：interrupted job restart recovery PASS；
- `E055-AC-009`：duplicate/retry 不产生重复 canonical side effect；
- `E055-AC-010`：rebuild/replay 不调用在线 LLM。

## Required Tests

- migration fixtures；
- recovery/rebuild integration；
- restart tests；
- idempotency/concurrency tests；
- learner-state recompute；
- Required backend regression；
- ruff / formatter / mypy applicable。

## Completion Report Format

报告：migration fixtures、failure-preservation evidence、rebuild targets、job recovery evidence、tests、commit SHA、`E055 DONE` 或 blocker。