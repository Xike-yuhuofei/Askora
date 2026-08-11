# EXEC-038 — P1-01A Goal Definition, Draft and Safe Replan

> Status: DONE
> Governing: ADR-0010, SYS06 Goal Management, P1-01A

## Objective

Implement versioned Definition/State/Draft/Preview/Focus and safe multi-source replan through one SYS06 service.

## Allowed files

```text
docs/architecture/decisions/ADR-0010-*.md
docs/specs/**
docs/planning/**
docs/archive/audits/product-gap-register-p1-p2.md
docs/governance/document-inventory.md
docs/archive/releases/**
apps/backend/alembic/versions/<p101a>.py
apps/backend/app/contracts/goal_management.py
apps/backend/app/models/goal_management.py
apps/backend/app/infrastructure/goal_management.py
apps/backend/app/services/goal_management.py
apps/backend/app/services/activity_lifecycle.py
apps/backend/app/api/v1/goals.py
apps/backend/app/api/v1/__init__.py
apps/backend/app/main.py
apps/backend/app/models/__init__.py
apps/backend/tests/**/test_goal_management*.py
apps/frontend/src/App.jsx
apps/frontend/src/api/goals.js
apps/frontend/src/pages/Goals.*
apps/frontend/src/pages/Goal*.jsx
apps/frontend/src/test/Goal*.test.jsx
apps/frontend/src/pages/BookLearningLaunch.jsx
apps/frontend/src/test/BookLearningLaunch.test.jsx
apps/frontend/src/test/AppRoutes.test.jsx
```

## Gate

Contracts/migration/service/API/UI/tests; full backend/frontend/docs gates; real browser; local commit; no push.

## Completion evidence

- Release evidence: `docs/archive/releases/p1-01a-goal-definition-draft-replan.md`
- Engineering / Contract / Ownership / Browser Gate: PASS
- Learning Evidence Gate: `LEARNING_EVIDENCE_INSUFFICIENT`
