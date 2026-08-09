# EXEC-1031 — P1-03 Recovery Foundation

> Priority：P1 Private Product Reliability
> Status：FROZEN / READY
> Governing：ADR-0103、DATA-001..033
> Depends on：P1-03 governance commit

## Objective

交付 Recovery Key boundary、versioned encrypted container、manifest、catalog、offline SQLite/documents/KEK backup、reopen verification、retention 与 pre-migration guard；不得把普通目录复制称为备份。

## Required Specs

`AGENTS.md`、ADR-0103、`data-control-contract.md`、Persistence/Schema/Error/Security/Testing/DoD、P1-03 Vertical Slice。

## Current Reality

Electron 使用 `askora.db`、`documents/`、`local-secrets.json`，无 backup/catalog/recovery key。桌面启动直接拉起 backend；local `create_all` 不等于 migration guard。

## Allowed Files

```text
docs/**P1-03/ADR-0103/EXEC-1031/release index files
apps/backend/app/contracts/data_control.py
apps/backend/app/core/config.py
apps/backend/app/data_control/**
apps/backend/app/main.py
apps/backend/backend.spec
apps/backend/tests/contracts/test_data_control_contract.py
apps/backend/tests/unit/test_recovery_crypto.py
apps/backend/tests/integration/test_recovery_backup.py
apps/backend/tests/security/test_recovery_package_security.py
apps/frontend/electron/main.cjs
apps/frontend/electron/preload.cjs
apps/frontend/src/api/dataControl.js
apps/frontend/src/test/DataControlBridge.test.jsx
```

## Forbidden Changes

- 不实现 restore activation、user export 或 erasure；
- 不备份 provider key/JWT/browser cache/log；
- 不写明文 Recovery Key；
- 不修改 SYS01～SYS08 canonical payload。

## Tasks

1. strict contracts/errors；2. chunked AEAD + safe archive；3. catalog/lock/retention；4. offline SQLite/documents/KEK backup；5. reopen verify；6. maintenance CLI/Electron typed bridge；7. tests/docs。

## Acceptance Criteria

- `E1031-AC-001`：DATA-AC-001、DATA-020..033 满足；
- `E1031-AC-002`：wrong key/tamper/truncate/path/limit fail closed；
- `E1031-AC-003`：恢复包不含 forbidden secrets/cache/log；
- `E1031-AC-004`：pre-migration backup failure blocks migration；
- `E1031-AC-005`：targeted + Ruff/mypy/build/diff/docs gates pass。

## Completion Report

列出 container/version/key boundary、included/excluded data、retention、tests、SPEC GAP、未提交用户改动保护；独立本地 commit，不 push。
