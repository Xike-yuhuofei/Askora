# EXEC-053 — Production Local Runtime Cutover

> Status：**DONE**（2026-08-10）  
> Governing：PRODUCT-POSITIONING、CI-*、QUAL-V1-*、ADR-0015 / LID-*  
> Dependency：EXEC-052 DONE + EXEC-051 DONE  
> Next：EXEC-054

## Objective

把 Askora v1 的 production runtime truth 收敛到 Local Server + SQLite + Local Files + local jobs，并消除 Redis、PostgreSQL、JWT/Auth、Kafka、Docker 对最终用户运行路径的隐式依赖。

## Dependencies

- EXEC-052 DONE；
- EXEC-051 DONE，确保 no-auth / LocalOwner migration 已收口；
- 当前 branch 不混入 UI-03 页面重构。

## Required Product Positioning

必须读取 PRODUCT-POSITIONING 中 Local Web、基础设施边界、Local-first、后台任务、Schema Migration、Observability、Non-goals。

## Required Specs

- `CI-100..103`
- `CI-200..204`
- `QUAL-V1-001..003`
- `QUAL-V1-101/105/202`
- ADR-0015 / LID-*
- Persistence / Schema Versioning / Recovery contracts

## Current Reality

- backend dependencies 仍含 `asyncpg`、`redis`、`PyJWT`、`passlib`、`bcrypt`、`aiokafka`；
- `docker-compose.yml` 仍将 PostgreSQL + Redis + JWT secret 描述为 production environment；
- 现有 CI 仍注入 Redis/JWT 配置并维护 PostgreSQL Required contract；
- `aiosqlite` 已存在，可作为 v1 production persistence path。

## Allowed Files

```text
apps/backend/app/**
apps/backend/alembic/**
apps/backend/pyproject.toml
apps/backend/uv.lock
apps/backend/tests/**
docker-compose.yml
.env.example
.gitignore
README.md
apps/backend/README.md
.github/**
docs/specs/quality/**
docs/planning/**
```

## Forbidden Changes

- 不改变 Teaching Policy / Assessment / Learner State 领域语义；
- 不恢复 auth/account runtime；
- 不以“保留 compatibility”为理由让 Redis/Postgres/Kafka 继续参与 production startup；
- 不删除 legacy schema/data 而绕过 migration；
- 不要求 Docker 才能执行 production-local smoke；
- 不把 observability libraries 误删为“分布式依赖”，除非证明其无价值且有对应测试。

## Implementation Tasks

1. 建立明确 `Production Local` profile：SQLite、Local Files、loopback、LocalOwner、local jobs；
2. 确保 Redis/PostgreSQL/Kafka 不可用时 Production Local startup 与核心业务仍成立；
3. 将 Redis/JWT/Auth/PostgreSQL/Kafka 相关 production config 分为 delete / optional / historical migration；
4. 删除确定无 runtime/migration价值的依赖和 imports；仍需历史迁移/兼容的依赖必须隔离，不进入默认 startup；
5. 确保 background jobs 有本地 durable state，不依赖 Redis broker；
6. 将 `docker-compose.yml` 明确降级为 developer/compatibility tool，或在无持续价值时删除；不得标为 v1 production deployment；
7. `.env.example` / README / health readiness 不再要求 JWT/Redis/Postgres secrets；
8. production startup 强制 loopback；
9. 保证 external AI provider unavailable 不破坏 durable local data；
10. 增加 production-local runtime smoke tests。

## Acceptance Criteria

- `E053-AC-001`：无 Redis 服务时 Production Local startup PASS；
- `E053-AC-002`：无 PostgreSQL 服务时 Production Local startup PASS；
- `E053-AC-003`：无 JWT/Auth secret 时 Production Local startup PASS；
- `E053-AC-004`：无 Kafka 服务时核心 runtime PASS；
- `E053-AC-005`：默认 structured persistence 为 SQLite；
- `E053-AC-006`：Local Files 原始资料路径可写读并受 AskoraData 隔离；
- `E053-AC-007`：Docker 不参与 v1 startup acceptance；
- `E053-AC-008`：removed dependencies 无 production import residue；
- `E053-AC-009`：教学核心 deterministic regression 不变；
- `E053-AC-010`：文档不再把 compose/Postgres/Redis 描述为 v1 production requirement。

## Required Tests

- Production Local bootstrap smoke；
- SQLite integration；
- LocalOwner/no-auth regression；
- background-job local persistence targeted tests；
- backend unit/contract/integration applicable suites；
- ruff / formatter / mypy applicable；
- docs gate。

## Completion Report Format

报告：retired/optional dependencies、production startup config、remaining compatibility paths、SQLite evidence、tests、commit SHA、`E053 DONE` 或 blocker。