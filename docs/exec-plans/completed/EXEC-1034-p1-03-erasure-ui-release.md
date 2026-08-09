# EXEC-1034 — P1-03 Erasure, Settings UX and Release Gate

> Priority：P1 Private Product Reliability
> Status：FROZEN / BLOCKED_BY_EXEC-1033
> Governing：ADR-0103、DATA-070..081、P1-03 Vertical Slice

## Objective

交付 four-scope preview/confirm/idempotent owner erasure、checkpoint/no-resurrection、完整 Settings/Electron 体验与 P1-03 release gate，并只在全部证据通过后把缺口标 DONE。

## Allowed Files

```text
docs/**P1-03/EXEC-1034/product-gap/release/index files
apps/backend/alembic/versions/<p103_data_control>.py
apps/backend/app/contracts/data_control.py
apps/backend/app/models/data_control.py
apps/backend/app/models/__init__.py
apps/backend/app/data_control/**
apps/backend/app/api/v1/data_control.py
apps/backend/app/api/v1/__init__.py
apps/backend/app/main.py
apps/backend/tests/architecture/test_data_control_boundary.py
apps/backend/tests/contracts/test_data_control_contract.py
apps/backend/tests/integration/test_data_erasure.py
apps/backend/tests/integration/test_data_erasure_migration.py
apps/backend/tests/recovery/test_data_erasure_recovery.py
apps/backend/tests/security/test_data_erasure_security.py
apps/frontend/electron/main.cjs
apps/frontend/electron/preload.cjs
apps/frontend/src/api/dataControl.js
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/test/Settings.test.jsx
```

## Forbidden Changes

不得 data-control direct cross-owner canonical patch；不得 partial 显示完成；不得保留可激活的 unsafe managed old backup；不得把 P1-05 账号 UX 或 P1-02 provider key scope 偷渡进来。

## Tasks

1. erasure schema/migration（含 frozen manifest 中 `consent_records` 的 Alembic additive coverage 与旧版预建表兼容校验）；2. subject-binding registry/coverage gate；3. preview/token/confirm/workflow；4. four scope steps/receipts/checkpoint；5. old backup invalidation + POST_ERASURE；6. complete Settings states/a11y；7. full L0～L5/Electron E2E；8. release report/index/product gap DONE。

## Acceptance Criteria

- `E1034-AC-001`：DATA-AC-006..010、P103-AC-001..006 全部满足；
- `E1034-AC-002`：所有注册 user-data tables/payload bindings 被 export/erasure coverage test 覆盖；
- `E1034-AC-003`：partial retry/restart converges，target pending 时 fail closed；
- `E1034-AC-004`：managed old backup + replay + projection rebuild 均不复活被删事实；
- `E1034-AC-005`：真实桌面 backup→mutate→restore 和 four-scope UI E2E；
- `E1034-AC-006`：Engineering、Policy/Ownership PASS；Learning Evidence 仍 `LEARNING_EVIDENCE_INSUFFICIENT`。
