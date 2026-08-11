# EXEC-055 — Local Data Migration, Recovery & Rebuild Gate

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*  
> Dependency：EXEC-054 DONE  
> Next：EXEC-056 / EXEC-057

## Objective

把 Askora v1 最重要的数据正确性要求转化为 Required automation：SQLite migration、升级失败保护、Askora Backup/Restore、Derived Data 重建、后台任务中断恢复、Learning Evidence 删除后的 Learner State 重算。

本 EXEC 必须同时证明两个不同的数据出口语义不会混淆：

```text
Backup = 恢复 Askora 本身
Export = 让用户数据离开 Askora 后仍可使用
```

Backup/Restore 必须围绕 Durable Data 建立可验证 roundtrip；API Key、可重建 Cache/Embedding/Index 等默认不得成为恢复 Askora 所必需的备份内容。

## Dependencies

- EXEC-053 Production Local runtime DONE；
- EXEC-054 Required core suite 已稳定；
- SQLite 是当前 production persistence truth。

## Required Product Positioning

必须读取 Durable/Derived Data、后台任务、Schema Migration、Backup/Restore、Export、API Key/Secret、Evidence recompute、工程优先级章节。

至少冻结：

- Durable Data 不因 cache/index/AI failure 丢失；
- Derived Data 删除后可重建；
- Backup 与 Export 是不同能力；
- Backup 至少包含 versioned manifest + durable database + source files + backup metadata；
- 默认 Backup 不包含 API Key 与非必要 Derived Data；
- Restore 后 API Key 可重新配置；
- migration failure 必须 preserve old durable data；
- Evidence 删除后相关 Learner State 必须重算。

若当前 Spec 尚未冻结 Backup format/version/restore owner 等实现所必需的细节，本 EXEC 必须返回 `BLOCKED_BY_SPEC_GAP`，不得自行发明不可迁移的长期备份协议。

## Required Specs

- `CI-300..403`
- `QUAL-V1-105`
- Persistence / Schema Versioning / Recovery / Backup / Export contracts
- Secret / credential storage contracts
- Learner Model / Assessment / Review Scheduler contracts
- Testing Standard L5 retained clauses

## Current Reality

当前 CI 主要执行 Alembic `upgrade → check → downgrade → upgrade`，但这不足以证明真实用户数据升级安全、Backup/Restore roundtrip、Derived Data 可重建或进程中断后任务可恢复。

如果现有 Backup/Export 实现仍混用一个流程，或 Backup 默认携带 API Key / Embedding / Cache，本 EXEC 必须将其作为当前 Product Positioning conformance gap 处理；若修复需要未冻结 public format/schema，则返回 SPEC GAP。

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
docs/planning/**
```

只允许与 migration/backup/restore/recovery/rebuild/idempotency/evidence recompute 直接相关的 production 改动。

## Forbidden Changes

- 不把 Derived Data 提升为不可替代 canonical truth；
- 不通过删除旧数据库 fixture 逃避 migration；
- 不以 downgrade-to-base 作为唯一 migration safety 证据；
- 不在 replay/rebuild 中调用在线 LLM；
- 不在失败时静默覆盖/删除旧 durable data；
- 不将 learner/system failure 误记为 learner incorrect；
- 不把 Backup 与 Export 实现/命名/验收混成同一个语义；
- 不把 API Key、完整 secret、默认 diagnostics 或非必要 Derived Data 写入默认 Backup；
- 不要求恢复 Embedding/Vector Index/Cache 后才能视为 Restore 成功；这些应允许重建；
- 不直接用用户真实 AskoraData 做测试。

## Implementation Tasks

1. fresh SQLite → head → startup validation。
2. representative legacy SQLite fixtures → backup/preflight → migration → validation。
3. migration failure 路径证明旧 durable data preserved / rollback or forward-fix boundary 明确。
4. data directory `schema_version` / reader/writer compatibility 检查。
5. 基于当前 frozen Backup contract 建立 versioned Askora Backup fixture/roundtrip：manifest + durable DB + source files + metadata；如 contract 不足，返回 `BLOCKED_BY_SPEC_GAP`。
6. Restore 到全新隔离 AskoraData，验证 Workspace / Material source files / Learning Project / Goal / Evidence / History / user config 等适用 Durable Data 恢复且引用完整。
7. 验证默认 Backup 明确排除 API Key、credential secret、cache、Embedding/Vector/Search Index 等非必要 Derived Data；Restore 后 secret 处于需重新配置状态。
8. 对 Export 使用独立测试/contract 证明其目标与 Backup 不同；不得以“Backup 能解包”代替可互操作 Export。如果当前 Export 未进入本 EXEC 实现范围，至少验证两者 API/command/format owner 不混用。
9. 删除/recreate Chunks、Indexes、cached retrieval 等 Derived Data 并验证可重建。
10. 对可重建 Learner State/projection 验证 deterministic recompute。
11. 删除/invalidate Learning Evidence 后验证相关 Learner State 不保留旧值。
12. background job `running → process interruption → restart → interrupted/retry/resume`。
13. 同 Material 同类 rebuild 去重/互斥。
14. retry/idempotency 验证不重复破坏 durable state。
15. 验证 Backup/Restore/migration/rebuild/replay 全流程不需要在线 LLM；需要重新生成的 AI-derived data 应标 stale/rebuildable，而不是阻断 durable restore。

## Acceptance Criteria

- `E055-AC-001`：fresh SQLite migration PASS。
- `E055-AC-002`：至少一个 representative legacy SQLite fixture migration PASS。
- `E055-AC-003`：migration failure 不破坏旧 durable data。
- `E055-AC-004`：不兼容 data dir fail closed。
- `E055-AC-005`：至少一类 retrieval/index derived data 删除后可重建。
- `E055-AC-006`：Learner State/projection 可从 evidence 重建。
- `E055-AC-007`：Evidence 删除触发正确 recompute。
- `E055-AC-008`：interrupted job restart recovery PASS。
- `E055-AC-009`：duplicate/retry 不产生重复 canonical side effect。
- `E055-AC-010`：rebuild/replay 不调用在线 LLM。
- `E055-AC-011`：Askora Backup 使用明确 versioned manifest，并可 Restore 到新的隔离 AskoraData；核心 Durable Data 与 source files roundtrip PASS。
- `E055-AC-012`：默认 Backup 不包含 API Key/credential secrets，也不依赖 Cache/Embedding/Vector/Search Index 才能恢复。
- `E055-AC-013`：Restore 后 API Key 需要重新配置；Derived Data 可标 stale 并随后重建，不得伪装为 canonical loss。
- `E055-AC-014`：Backup 与 Export 在 command/API/format/acceptance 语义上明确区分；没有用单一“导出”流程同时承担两种职责。

## Required Tests

- migration fixtures；
- Backup → Restore roundtrip；
- Backup manifest/version compatibility；
- secret/API-key exclusion negative tests；
- Backup vs Export contract separation；
- recovery/rebuild integration；
- restart tests；
- idempotency/concurrency tests；
- learner-state recompute；
- Required backend regression；
- ruff / formatter / mypy applicable。

## Completion Report Format

报告：migration fixtures、failure-preservation evidence、Backup manifest/roundtrip、secret exclusion、Backup vs Export disposition、rebuild targets、job recovery evidence、tests、commit SHA、`E055 DONE` 或 blocker。
