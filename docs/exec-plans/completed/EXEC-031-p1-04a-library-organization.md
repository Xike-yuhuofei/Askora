# EXEC-031 — P1-04A Library Search and Organization

> Status: DONE
> Governing: ADR-0008, SYS01 Library Management Spec, P1-04A Slice

## Objective

实现 P1-04A 的 current-user 搜索、元数据、标签、集合、非破坏性批量整理和可恢复 archive/restore。

## Allowed files

```text
docs/adr/ADR-0008-library-management-deduplication-and-ocr.md
docs/specs/systems/01-library-management.md
docs/specs/vertical-slices/p1-04a-library-organization.md
docs/exec-plans/**
docs/product-gap-register-p1-p2.md
docs/releases/**
apps/backend/alembic/versions/<p104_library_management>.py
apps/backend/app/contracts/library_management.py
apps/backend/app/contracts/workspace.py
apps/backend/app/models/document.py
apps/backend/app/models/__init__.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/documents/library_management.py
apps/backend/app/queries/library.py
apps/backend/app/api/v1/documents.py
apps/backend/app/api/v1/workspace.py
apps/backend/app/core/exceptions.py
apps/backend/tests/**/test_library_management*.py
apps/backend/tests/**/test_library_workspace*.py
apps/frontend/src/api/documents.js
apps/frontend/src/api/workspace.js
apps/frontend/src/pages/Library.*
apps/frontend/src/test/Library*.test.jsx
```

## Tasks / gate

1. additive migration/models/backfill；2. contracts/service/query/API；3. UI；4. contract/owner/idempotency/recovery/security tests；5. full gates and real browser；6. archive/report/independent commit。

DONE requires all `P104A-AC-*` and no blocking SPEC GAP. Learning Evidence remains insufficient.
