# EXEC-032 — P1-04B Library Deduplication

> Status: DONE
> Governing: ADR-0008, SYS01 Library Management Spec, P1-04B Slice

## Objective

实现 versioned duplicate fingerprints、候选、证据、显式 resolution 与可恢复归档，禁止自动 canonical merge。

## Allowed files

```text
docs/specs/vertical-slices/p1-04b-library-deduplication.md
docs/exec-plans/**
docs/product-gap-register-p1-p2.md
docs/releases/**
apps/backend/alembic/versions/<p104_dedup>.py
apps/backend/app/contracts/library_management.py
apps/backend/app/models/document.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/documents/library_management.py
apps/backend/app/queries/library.py
apps/backend/app/api/v1/documents.py
apps/backend/app/contracts/workspace.py
apps/backend/tests/**/test_library_deduplication*.py
apps/frontend/src/api/documents.js
apps/frontend/src/pages/Library.*
apps/frontend/src/test/Library*.test.jsx
```

DONE requires all `P104B-AC-*`, migration/recovery/security/full gates, real browser and independent commit.
