# EXEC-1033 — P1-03 User Data Export

> Priority：P1 Private Product Reliability
> Status：FROZEN / BLOCKED_BY_EXEC-1032
> Governing：ADR-0103、DATA-060..063

## Objective

交付 authenticated current-user、显式 allowlist、版本化、可读且不可作为 DB import 的个人数据导出。

## Allowed Files

```text
docs/**P1-03/EXEC-1033/release index files
apps/backend/app/contracts/data_control.py
apps/backend/app/data_control/export.py
apps/backend/app/api/v1/data_control.py
apps/backend/app/api/v1/__init__.py
apps/backend/app/main.py
apps/backend/tests/contracts/test_data_control_contract.py
apps/backend/tests/integration/test_user_data_export.py
apps/backend/tests/security/test_user_data_export_security.py
apps/frontend/src/api/dataControl.js
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/test/Settings.test.jsx
```

## Forbidden Changes

不得 `SELECT *`/ORM 自动序列化；不得导出 secret/hash/internal Prompt/grader-only/other-user/path；不得实现 import。

## Tasks

1. manifest/scopes；2. owner-aware allowlist assemblers；3. originals opt-in；4. private expiring artifact；5. API/download；6. Settings export flow；7. zero-leakage tests。

## Acceptance Criteria

- `E1033-AC-001`：DATA-AC-005 满足；
- `E1033-AC-002`：PROFILE/DOCUMENTS/LEARNING_RECORDS/MODEL_EXECUTION current-user coverage；
- `E1033-AC-003`：forbidden field/content scan 为 0；
- `E1033-AC-004`：partial/expired/cross-user fail closed；
- `E1033-AC-005`：backend/frontend applicable gates pass。
