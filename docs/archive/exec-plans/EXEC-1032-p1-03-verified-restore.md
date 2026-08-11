# EXEC-1032 — P1-03 Verified Offline Restore

> Priority：P1 Private Product Reliability
> Status：FROZEN / BLOCKED_BY_EXEC-1031
> Governing：ADR-0103、DATA-040..050

## Objective

交付 verify、private staging、schema compatibility/forward migration、file/owner/checkpoint reconciliation、atomic activation、rescue rollback 与非敏感 RecoveryReportV1。

## Allowed Files

```text
docs/**P1-03/EXEC-1032/release index files
apps/backend/app/contracts/data_control.py
apps/backend/app/data_control/**
apps/backend/app/main.py
apps/backend/backend.spec
apps/backend/tests/contracts/test_data_control_contract.py
apps/backend/tests/integration/test_recovery_restore.py
apps/backend/tests/integration/test_recovery_migration.py
apps/backend/tests/recovery/test_recovery_crash_consistency.py
apps/backend/tests/security/test_recovery_package_security.py
apps/frontend/electron/main.cjs
apps/frontend/electron/preload.cjs
apps/frontend/src/api/dataControl.js
```

## Forbidden Changes

不得直接覆盖 active path；不得 `create_all` 猜历史 schema；不得 online LLM replay；不得恢复 JWT/provider key。

## Tasks

1. full verify；2. staging extraction/limits；3. schema head/forward migration；4. reconciliation；5. rescue journal/atomic activation/crash recovery；6. report；7. Electron restore/restart/re-login；8. tests。

## Acceptance Criteria

- `E1032-AC-001`：DATA-AC-002..004 满足；
- `E1032-AC-002`：older supported schema forward-migrates，future schema rejects；
- `E1032-AC-003`：任一 failure active dataset byte/content unchanged or rescued；
- `E1032-AC-004`：restore 后 DB/files/KEK/checkpoint/refs/readiness 一致；
- `E1032-AC-005`：L5 recovery/migration/crash tests pass。
