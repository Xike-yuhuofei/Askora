# EXEC-036 — Account Deletion, Owner Erasure and Restore Barrier

> Priority：P1-05
> Status：FROZEN / BLOCKED_BY_DEPENDENCY
> Depends on：EXEC-035 DONE
> Governing decision：ADR-0009

## Objective

实现 `IDP-040..056` 和 P1-05 完整删除闭环：preview、re-auth/confirmation、pending/cancel、durable owner erasure、restart recovery、reconciliation、identity sanitization、tombstone/restore barrier，并最终关闭 P1-05。

## Required Specs

`AGENTS.md`、ADR-0009、`IDP-*`、STATE/EVENT、SYS01～SYS08、API/Error/Persistence/Schema/Security/Testing/DoD、UI Screen/Visual/Quality、P1-05 Vertical Slice、EXEC-034/035 evidence。

## Current Reality

- User 只有 soft-delete enum；
- 文档删除只软删 DB row并删除原文件，chunks/ledger/其他 owner data 不完整；
- user scope 分布在直接 columns、owner refs、JSON payload、文件和 outbox；
- immutable ORM listener 会拒绝普通删除；
- 无 deletion request/manifest/receipt/tombstone/restore barrier/worker。

## Allowed Files

```text
docs/** (P1-05/EXEC/release/gap registries only)
apps/backend/alembic/versions/<exec036_privacy_deletion>.py
apps/backend/app/contracts/privacy.py
apps/backend/app/models/privacy.py
apps/backend/app/models/user.py
apps/backend/app/models/__init__.py
apps/backend/app/infrastructure/privacy.py
apps/backend/app/services/privacy/**
apps/backend/app/services/auth/**
apps/backend/app/api/v1/account.py
apps/backend/app/main.py
apps/backend/app/core/config.py
apps/backend/app/core/exceptions.py
apps/backend/tests/contracts/test_privacy_contract.py
apps/backend/tests/architecture/test_privacy_owner_boundary.py
apps/backend/tests/integration/test_account_deletion.py
apps/backend/tests/integration/test_account_deletion_all_models.py
apps/backend/tests/integration/test_account_deletion_migration.py
apps/backend/tests/recovery/test_account_deletion_recovery.py
apps/backend/tests/security/test_account_deletion_security.py
apps/frontend/electron/main.cjs
apps/frontend/src/App.jsx
apps/frontend/src/api/account.js
apps/frontend/src/hooks/useAuth.jsx
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/pages/AccountDeletion.jsx
apps/frontend/src/pages/AccountDeletion.css
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/Settings.test.jsx
apps/frontend/src/test/AccountDeletion.test.jsx
```

## Forbidden Changes

- coordinator 不得获得普通 cross-owner write API；
- 不按单用户假设猜测 ledger 归属；
- 不删除其他用户或 global policy/knowledge；
- 不在 reconciliation 非零时完成；
- 不把 soft-delete User 当完成；
- 不让 old outbox/restore 重建数据；
- 不提交 Allowed Files 外的现有修改。

## Implementation Tasks

1. strict privacy contracts、lifecycle、models、migration、stable errors。
2. frozen subject registry + iterative manifest + ambiguity blocking。
3. versioned preview/re-auth/typed confirmation/idempotent request/control token/cancel。
4. per-owner erasure handlers、step receipts、bounded retry、restart worker。
5. file/outbox/projection deletion、zero-residual reconciliation。
6. identity PII/credential clear、minimal tombstone、external restore barrier/startup enforcement。
7. Settings/Delete status UI 与 Login/route behavior。
8. all-model/cross-user/SQLite/PostgreSQL/recovery/security/frontend/real-browser tests。
9. full gates；release report；将 P1-05 标 DONE；归档 EXEC-036并独立 commit。

## Acceptance Criteria

- `EXEC036-AC-001`：`IDP-AC-005..012`、`P105-AC-001..008` 全部满足。
- `EXEC036-AC-002`：representative metadata all-table fixture 与真实文件/outbox/projection 零残留，其他 user/global rows 保留。
- `EXEC036-AC-003`：pending cancel、purging non-cancel、retry/block/restart deterministic。
- `EXEC036-AC-004`：old snapshot + retained barrier 不能恢复登录或后台处理。
- `EXEC036-AC-005`：真实浏览器 deletion journey、刷新和后端重启一致。
- `EXEC036-AC-006`：full backend/frontend/migration/security/docs/diff gates PASS；P1-05 register DONE；无 blocking SPEC GAP。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/contracts/test_privacy_contract.py tests/architecture/test_privacy_owner_boundary.py tests/integration/test_account_deletion.py tests/integration/test_account_deletion_all_models.py tests/integration/test_account_deletion_migration.py tests/recovery/test_account_deletion_recovery.py tests/security/test_account_deletion_security.py
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

真实验收必须包含浏览器、SQLite local file、PostgreSQL representative fixture 和 backend restart。

## Completion Report Format

分别报告 Engineering、Policy/Ownership、Learning Evidence；逐项列 P1-05 AC、owner receipts、zero-residual evidence、restore barrier、测试、commit、未完成项和 SPEC GAP。
