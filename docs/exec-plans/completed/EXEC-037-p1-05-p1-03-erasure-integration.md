# EXEC-037 — P1-05 / P1-03 Canonical Erasure Integration

> Priority：P1-05 merge readiness
> Status：DONE
> Governing：ADR-0107、`IDP-*`、`DATA-070..078`

## Objective

Rebase the completed P1-05 account journey onto the newly authoritative P1-03 `ALL_PERSONAL_DATA` workflow, retire the duplicate P1-05 owner receipt writer, preserve grace/cancel/deletion-control behavior and restore a conflict-free, fully verified PR.

## Allowed Files

```text
docs/** (ADR-0107, IDP/DATA/P1-05/EXEC/release/index/gap reconciliation only)
apps/backend/alembic/versions/f36c91b807d3_add_account_deletion_lifecycle.py
apps/backend/app/contracts/privacy.py
apps/backend/app/data_control/erasure.py
apps/backend/app/infrastructure/privacy.py
apps/backend/app/models/data_control.py
apps/backend/app/models/privacy.py
apps/backend/app/models/__init__.py
apps/backend/app/services/privacy/**
apps/backend/app/api/v1/account.py
apps/backend/app/main.py
apps/backend/tests/architecture/test_privacy_owner_boundary.py
apps/backend/tests/contracts/test_privacy_contract.py
apps/backend/tests/integration/test_account_deletion.py
apps/backend/tests/integration/test_account_deletion_all_models.py
apps/backend/tests/integration/test_account_deletion_migration.py
apps/backend/tests/integration/test_data_erasure.py
apps/backend/tests/recovery/test_account_deletion_recovery.py
apps/backend/tests/security/test_account_deletion_security.py
apps/frontend/electron/main.cjs
apps/frontend/electron/preload.cjs
apps/frontend/src/api/dataControl.js
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/AccountDeletion.jsx
apps/frontend/src/test/Settings.test.jsx
apps/frontend/src/test/AccountDeletion.test.jsx
```

Merge-conflict-only index/import composition outside this list is allowed when it preserves both already accepted slices and does not change their semantics.

## Forbidden Changes

- no second owner-erasure step/receipt/checkpoint writer;
- no weakening of account password re-authentication, exact phrase, grace or cancel boundary;
- no account `DELETED` result while P1-03 is partial, retryable or missing receipt/checkpoint;
- no claim that PostgreSQL provides the P1-03 desktop backup product;
- no deletion of other-user or global policy/config rows;
- no unrelated refactor or expansion of P1-03 recovery/export scope.

## Tasks

1. Reconcile ADR/Spec/Vertical Slice and freeze this EXEC before product code.
2. Merge current `main`, compose Settings and documentation conflicts, and linearize Alembic heads.
3. Make the exhaustive subject registry cover P1-03 governance plus all landed P1-04/P1-06/activity/auth tables.
4. Add the internal account authorization bridge to canonical `ALL_PERSONAL_DATA` planning/execution.
5. Link `AccountDeletionRequest` to P1-03 workflow/receipt/checkpoint and remove the P1-05 receipt writer/table.
6. Map partial/retry/post-erasure maintenance to honest account status; finalize only from canonical evidence.
7. Update architecture/migration/recovery/security/frontend tests and release evidence.
8. Run full gates, commit, push, and verify PR CI.

## Acceptance Criteria

- `E037-AC-001`：one account request produces P1-03 workflow/step/receipt/checkpoint records and zero P1-05 owner receipt records.
- `E037-AC-002`：pending/cancel/retry/restart and deletion-control behavior remain compatible.
- `E037-AC-003`：representative all-table fixture erases target data while retaining other-user/global/governance records.
- `E037-AC-004`：partial or incomplete post-erasure maintenance never reports `DELETED`.
- `E037-AC-005`：SQLite/PostgreSQL migration, backend/frontend/security/docs and PR CI pass.

## Completion Evidence

- Primary integration commit：`aea603e0e77afcbbd855330e4c1e715fb25c9aab`；
- local backend：474 passed / 5 skipped；ruff、Black baseline、mypy PASS；
- local frontend：78 passed；build 与 high-severity dependency audit PASS；
- Alembic：single head `f36c91b807d3`；SQLite 与真实 PostgreSQL upgrade/check PASS；
- real PostgreSQL representative account-deletion fixture：PASS；
- documentation：174 files / 0 broken local links；
- PR #5 Askora CI run `31302663091`：10/10 jobs PASS，含双 Python coverage、container build 与 dependency audits。
