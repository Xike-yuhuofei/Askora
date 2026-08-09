# EXEC-034 — Identity Credential and Durable Session Foundation

> Priority：P1-05
> Status：FROZEN / ACTIVE
> Depends on：ADR-0009 + IDP Spec frozen
> Governing decision：ADR-0009

## Objective

实现 `IDP-010..024`：Argon2id/bcrypt migration、修改密码、durable AuthSession、token-family rotation/replay detection、session list/revoke/logout，并交付 Settings UI。

## Required Specs

`AGENTS.md`、ADR-0009、`IDP-*`、API/Error/Persistence/Schema/Security/Testing/DoD、UI Screen/Visual/Quality、P1-05 Vertical Slice。

## Current Reality

- access/refresh JWT 无 `sid/fam/cv`；
- Redis/进程内集合承担撤销与 session count；
- logout 只撤销 access JTI；
- password 是 bcrypt，公共 request 最低 8 位；
- Settings 只有账号事实与退出。

## Allowed Files

```text
docs/** (ADR-0009/IDP/P1-05/EXEC registries and release evidence only)
apps/backend/pyproject.toml
apps/backend/uv.lock
apps/backend/alembic/versions/<exec034_identity_session>.py
apps/backend/app/contracts/identity.py
apps/backend/app/models/identity.py
apps/backend/app/models/user.py
apps/backend/app/models/__init__.py
apps/backend/app/infrastructure/identity.py
apps/backend/app/services/auth/**
apps/backend/app/api/v1/auth.py
apps/backend/app/core/exceptions.py
apps/backend/tests/contracts/test_identity_contract.py
apps/backend/tests/integration/test_identity_sessions.py
apps/backend/tests/integration/test_identity_session_migration.py
apps/backend/tests/security/test_identity_security.py
apps/backend/tests/test_auth_security.py
apps/frontend/src/api/auth.js
apps/frontend/src/hooks/useAuth.jsx
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/test/Settings.test.jsx
apps/frontend/src/test/AuthBoundary.test.jsx
```

## Forbidden Changes

- 不修改 SYS01～SYS08 业务状态；
- 不实现 recovery/delete 产品行为；
- Redis 不得继续是 session truth；
- 不把 client label/fingerprint 当可信硬件身份；
- 不提交 Allowed Files 外的现有未提交改动。

## Implementation Tasks

1. 新增 strict identity contracts、migration、durable repository/model。
2. Argon2id new-write、bcrypt read/rehash、v2 password validation。
3. login/refresh/validation/logout 切到 `sid/fam/cv` 与 DB rotation。
4. 实现 change-password、list/revoke/revoke-others endpoints 和稳定错误。
5. 实现 Settings password/session UI 与 token replacement。
6. 覆盖 contract/security/SQLite/PostgreSQL migration/concurrency/Redis outage/frontend tests。
7. full gates、release evidence、归档并独立 commit。

## Acceptance Criteria

- `EXEC034-AC-001`：`IDP-AC-001..003/006` 适用部分通过。
- `EXEC034-AC-002`：旧 refresh cutover 明确要求重新登录，不存在 silent legacy session。
- `EXEC034-AC-003`：Redis 故障/重启、concurrent refresh、session limit、cross-user revoke 通过。
- `EXEC034-AC-004`：password change/UI/session list/revoke 真实可用并可恢复失败。
- `EXEC034-AC-005`：migration/forward-fix、full gates、独立 commit 通过。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts/test_identity_contract.py tests/integration/test_identity_sessions.py tests/integration/test_identity_session_migration.py tests/security/test_identity_security.py tests/test_auth_security.py
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check

cd ../frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report Format

分别报告 Engineering、Policy/Ownership、Learning Evidence；列出 migration、测试、真实 UI、commit、SPEC GAP 与未提交用户改动保护。
