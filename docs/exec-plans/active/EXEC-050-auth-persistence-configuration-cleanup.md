# EXEC-050 — Auth Persistence & Configuration Cleanup

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE  
> Governing：ADR-0015、`LID-*`、Authentication Removal Vertical Slice  
> Dependency：EXEC-049 DONE  
> Next：EXEC-051

## Objective

在 frontend/backend 已完全切换 LocalOwnerContext 后，物理清理 authentication-only persistence、配置、后台 runtime 与依赖，同时保留 learner ownership、P1-03 data governance 和 historical replay integrity。

## Dependencies

- EXEC-047～049 DONE；
- production request path 已无 AuthService/TokenService/current-user dependency；
- frontend 已无 token/login semantics；
- migration backup/fixture 可验证。

## Required Specs

- `LID-050..063`
- persistence/schema-versioning/data-control contracts
- ADR-0015 Migration / Rollback

## Current Reality

旧 schema/runtime 至少包含：

- `users` credential/account columns；
- `auth_sessions`；
- recovery credentials/throttles；
- identity command receipts；
- account deletion lifecycle state/runtime；
- JWT/session/account-deletion config；
- auth-only dependencies/tests。

`users.id` / `pseudonym_id` 等仍可能被大量 learner-owned foreign key / compatibility code 引用，禁止为“干净命名”一次性制造大规模 FK churn。

## Allowed Files

```text
apps/backend/app/models/user.py
apps/backend/app/models/identity.py
apps/backend/app/models/privacy.py
apps/backend/app/infrastructure/identity.py
apps/backend/app/infrastructure/privacy.py
apps/backend/app/services/auth/**
apps/backend/app/services/recovery.py
apps/backend/app/services/privacy/**
apps/backend/app/api/v1/auth.py
apps/backend/app/api/v1/dev_auth.py
apps/backend/app/api/v1/account.py
apps/backend/app/api/v1/recovery.py
apps/backend/app/core/config.py
apps/backend/app/core/exceptions.py
apps/backend/app/models/__init__.py
apps/backend/app/contracts/**identity*
apps/backend/app/contracts/**recovery*
apps/backend/alembic/versions/**
apps/backend/tests/**
apps/backend/pyproject.toml
apps/backend/requirements.txt
docs/exec-plans/**
```

只允许 auth/account persistence cleanup、LocalOwner compatibility 和必要 data-control 适配。

## Forbidden Changes

- 不重写八系统 canonical schema；
- 不强制 rename 全部 `user_id`；
- 不删除 LocalOwner/learner ownership keys；
- 不删除 P1-03 export/erasure receipts/checkpoints；
- 不删除 Recovery Center 仅因为文件名含 recovery；
- 不恢复 password/token compatibility；
- 不把 PostgreSQL→SQLite 混入本 EXEC。

## Implementation Tasks

1. 生成 forward migration，删除 auth-only tables/indexes/constraints；
2. 删除 `users` 中 password/phone/email/wechat/login/account-lifecycle 等仅认证字段；
3. 保留最小 compatibility owner row/key，直到未来独立 learner-schema ADR 决定是否重命名；
4. 删除 auth session/recovery/account-deletion runtime 与 dead routes/files；
5. 删除 JWT/session/dev-auto-login/account-deletion grace/polling config；
6. 删除 auth-only secret validation；
7. 清理 auth-only Python/package dependencies（仅确认无其他用途后）；
8. 删除/重写旧 auth/security tests，使其转为 LocalOwner/network/data-safety tests；
9. P1-03 owner-safe erasure 若引用 account lifecycle，改为 LocalOwner/local data semantics；
10. migration report 证明旧 auth secret material 不再存在；
11. 若 downgrade 是仓库门禁，最多恢复空结构，不得伪造被删除 secrets。

## Acceptance Criteria

- `E050-AC-001`：auth_sessions/recovery_credentials/recovery_throttles/auth-only receipts 不再存在；
- `E050-AC-002`：users compatibility row 无 credential/contact/login/account lifecycle secret fields；
- `E050-AC-003`：JWT/session/account-deletion runtime config 已删除或无 production reference；
- `E050-AC-004`：AuthService/TokenService/password/recovery runtime production references 为零；
- `E050-AC-005`：existing single-learner DB upgrade 后关键 learner-owned records/refs 保持；
- `E050-AC-006`：DecisionTrace/replay owner references 仍可解析；
- `E050-AC-007`：P1-03 export/scoped erasure/no-resurrection regression PASS；
- `E050-AC-008`：migration 日志无 secret 泄漏；
- `E050-AC-009`：无大规模无必要 FK rename/churn。

## Required Tests

- migration upgrade current-head→new-head；
- legacy single learner fixture；
- ambiguous owner fixture；
- PostgreSQL integration if current CI provides；
- data erasure/export/recovery tests；
- DecisionTrace/replay regression；
- full backend pytest relevant suites；
- ruff + mypy。

## Completion Report Format

必须报告：dropped schema、retained compatibility owner fields、removed dependencies/config、migration evidence、data-control/replay evidence、tests、commit SHA、`E050 DONE` 或 blocker。
