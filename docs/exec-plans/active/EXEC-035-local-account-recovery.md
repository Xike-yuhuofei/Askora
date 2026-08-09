# EXEC-035 — Local Account Recovery Kit

> Priority：P1-05
> Status：FROZEN / BLOCKED_BY_DEPENDENCY
> Depends on：EXEC-034 DONE
> Governing decision：ADR-0009

## Objective

实现 `IDP-030..033`：注册自动恢复套件、既有账号创建/轮换、离线恢复密码、单次使用、durable throttling、全部 session 撤销和 Login/Settings UI。

## Required Specs

`AGENTS.md`、ADR-0009、`IDP-*`、API/Error/Persistence/Schema/Security/Testing/DoD、UI Screen/Visual/Quality、P1-05 Vertical Slice、EXEC-034 completion evidence。

## Current Reality

无 recovery credential、恢复 API/UI 或账号级认证限流；注册成功只返回用户信息。

## Allowed Files

```text
docs/** (P1-05/EXEC/release registries only)
apps/backend/alembic/versions/<exec035_recovery>.py
apps/backend/app/contracts/identity.py
apps/backend/app/models/identity.py
apps/backend/app/infrastructure/identity.py
apps/backend/app/services/auth/**
apps/backend/app/api/v1/auth.py
apps/backend/app/core/exceptions.py
apps/backend/tests/contracts/test_identity_contract.py
apps/backend/tests/integration/test_account_recovery.py
apps/backend/tests/integration/test_account_recovery_migration.py
apps/backend/tests/security/test_identity_security.py
apps/frontend/src/api/auth.js
apps/frontend/src/hooks/useAuth.jsx
apps/frontend/src/pages/Login.jsx
apps/frontend/src/pages/Login.css
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/test/Login.test.jsx
apps/frontend/src/test/Settings.test.jsx
```

## Forbidden Changes

- 不引入短信/邮件/第三方身份服务；
- 不持久化/日志记录 recovery secret；
- 不使用安全问题；
- 不实现 account deletion；
- 不提交 Allowed Files 外的现有修改。

## Implementation Tasks

1. recovery/throttle contracts、model、migration、repository。
2. 注册原子 issuance；Settings setup/rotate；Login recover flow。
3. generic response、dummy verify、5-attempt/15-minute throttling。
4. success consume/rotate credential、increment credential version、revoke all sessions。
5. contract/security/migration/restart/frontend/real-browser tests。
6. full gates、release evidence、归档并独立 commit。

## Acceptance Criteria

- `EXEC035-AC-001`：`IDP-AC-004/006` 与恢复相关 UI AC 全部满足。
- `EXEC035-AC-002`：明文只出现一次且不进入 DB/log/local user cache。
- `EXEC035-AC-003`：unknown/existing account timing/path 不枚举，throttle durable。
- `EXEC035-AC-004`：recovery 后旧 credential/session 失效，新 kit 可用且只一次。
- `EXEC035-AC-005`：full gates、真实 UI、独立 commit 通过。

## Required Tests

沿用 EXEC-034 full gates，并增加 `test_account_recovery*`、Login/Settings recovery 与真实浏览器恢复流程。

## Completion Report Format

分别报告 Engineering、Policy/Ownership、Learning Evidence；列出 secret leakage scan、throttle、migration、UI、commit 与未提交改动保护。
