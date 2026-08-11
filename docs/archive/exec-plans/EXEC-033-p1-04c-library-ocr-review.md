# EXEC-033 — P1-04C Scanned PDF OCR Review

> Status: DONE
> Governing: ADR-0008, SYS01 Library Management Spec, P1-04C Slice

## Objective

实现 local OCR durable candidate/review/publish 闭环，确保未审核文本不进入 canonical learning path。

## Allowed files

```text
docs/archive/specs/vertical-slices/p1-04c-library-ocr-review.md
docs/planning/**
docs/archive/audits/product-gap-register-p1-p2.md
docs/archive/releases/**
apps/backend/alembic/versions/<p104_ocr>.py
apps/backend/app/contracts/library_management.py
apps/backend/app/models/document.py
apps/backend/app/models/__init__.py
apps/backend/app/services/documents/ocr.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/documents/processing_worker.py
apps/backend/app/domains/content_knowledge/**
apps/backend/app/queries/library.py
apps/backend/app/api/v1/documents.py
apps/backend/app/contracts/workspace.py
apps/backend/app/core/exceptions.py
apps/backend/tests/**/test_library_ocr*.py
apps/frontend/src/api/documents.js
apps/frontend/src/pages/Library.*
apps/frontend/src/test/Library*.test.jsx
```

DONE requires all `P104C-AC-*`, real scanned-PDF flow, restart/failure/security/full gates and independent commit. P1-04 closes only after EXEC-031～033 all DONE.
