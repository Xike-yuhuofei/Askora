# EXEC-077 — Course Workspace Selection Platform

> Status: **FROZEN / READY_AFTER_XIK-188_MERGE**
> Linear: XIK-189
> Priority: P1 Course-centric Platform
> Product Traceability: `CAP-01`、`CAP-07`、`PD-RULE-009`、`PD-REQ-0701..0703`
> Governing: ADR-0016、ADR-0019、ADR-0022、ADR-0023、`WSP-*`、`CWSP-*`
> Depends on: XIK-188 / ADR-0023 + `CWSP-*` merged to current `main`

## Objective

实现 Platform Workspace Registry 的真实 list/get/create/current/switch、durable versioned WorkspaceSelection、create/switch receipts、fresh-empty/legacy migration 与 Course-scoped exact-SYS06 Activity projection，使 Course-centric frontend 可以在不建立第二 Workspace/Activity truth 的前提下使用真实后端能力。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-STRATEGY.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`
- ADR-0016、ADR-0019、ADR-0022、ADR-0023
- `docs/specs/platform/workspace-project-session-scope.md`
- `docs/specs/platform/course-workspace-selection.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/systems/06-activity-lifecycle.md`
- applicable security/testing/DOD contracts
- Linear XIK-189 current state and current `main`

## Current Reality

At freeze time, current code has durable Workspace/Project/Session foundation and one-default read projection, but no WorkspaceSelection table、create/switch public command、multi-Workspace current resolver or Course Activity index。`get_default_workspace` and bootstrap currently create/resolve default and therefore conflict with fresh Course Empty State；this EXEC must change only the paths authorized by ADR-0023 while preserving legacy-data migration safety。

Runtime reality must be rechecked at execution start；this snapshot is not completion evidence。

## Allowed Files

```text
apps/backend/app/models/workspace.py
apps/backend/app/contracts/workspace.py
apps/backend/app/services/workspace/**
apps/backend/app/queries/workspace.py
apps/backend/app/api/v1/workspace.py
apps/backend/app/api/v1/**                 # router registration only if needed
apps/backend/app/models/planning.py        # only additive query/index support if required
apps/backend/alembic/versions/**           # one additive migration / current head convergence
apps/backend/tests/contracts/**
apps/backend/tests/architecture/**
apps/backend/tests/integration/**
apps/backend/tests/migrations/**
apps/backend/tests/product_boundary/**
apps/backend/tests/recovery/**
docs/planning/execs/EXEC-077-course-workspace-selection-platform.md
docs/archive/exec-plans/EXEC-077-course-workspace-selection-platform.md
docs/planning/README.md
docs/governance/document-inventory.md
```

Any additional file requires direct trace to an acceptance criterion and must be reported；frontend files are forbidden in this EXEC。

## Forbidden Changes

- rename Workspace/Course domain/API/persistence identity；
- create Course table or frontend/localStorage truth；
- change Product Strategy/Positioning/Definition；
- write SYS06 Activity state from Platform query/service；
- auto-create/start Activity/Session/Goal/Plan on GET/route；
- silent draft/stream/note/session/material loss；
- Workspace cascade delete or cross-Workspace move/copy；
- weaken tests/constraints/ignore to manufacture PASS；
- claim Product/Learning effectiveness from engineering tests。

## Implementation Tasks

1. Write RED strict-contract tests for `CWSP-020..027/050` and stable errors。
2. Add `WorkspaceSelection`、command receipt persistence and nullable `LearningSession.learning_activity_id` with one additive Alembic migration。
3. Split fresh-empty resolution from legacy-data default migration；fresh query stays zero-write，legacy backfill remains idempotent。
4. Implement Platform repository/application commands with transaction、CAS、digest/idempotency、recovery guard and sanitized observability。
5. Implement owner-safe list/current/get/create/switch API adapters and `workspace/context` compatibility over selection。
6. Implement read-only exact Goal→Plan→Activity→latest lifecycle Course Activity index with stable title catalog/order and session refs。
7. Add cross-owner/cross-Workspace non-enumerability、atomic rollback、restart/retry、migration/reconciliation/forward-fix tests。
8. Run full backend、migration、docs and diff gates；capture real API requests proving no hidden writes。
9. Independent commit/PR/CI/merge；after merge update XIK-189 with evidence and only then unblock XIK-190。

## Acceptance Criteria

- `EXEC077-AC-001`：all `CWSP-AC-001..012` pass with traceable tests；
- `EXEC077-AC-002`：fresh LocalOwner list/current returns EMPTY/MISSING without creating Workspace；
- `EXEC077-AC-003`：legacy fixture gets exactly one default + selection；rerun no duplicate；
- `EXEC077-AC-004`：first/subsequent create-and-select atomic、CAS-safe、idempotent；rollback leaves no orphan Workspace；
- `EXEC077-AC-005`：switch stale/different-digest/unresolved guard produces stable no-write result；same retry returns original receipt；
- `EXEC077-AC-006`：active source Activity/Session/run/note/material position preserved，no auto end/cancel/complete；
- `EXEC077-AC-007`：foreign Workspace/Activity refs non-enumerable and no metadata leak；
- `EXEC077-AC-008`：GET/list/current/deep-link/refresh/retry side-effect free；
- `EXEC077-AC-009`：Activity index exact SYS06-derived、stable ordered；active resume/available start semantics correct；
- `EXEC077-AC-010`：new Activity-scoped Session pins exact Activity；legacy null refs not guessed；
- `EXEC077-AC-011`：fresh/upgraded SQLite `upgrade head` + `alembic check` + representative migration/forward-fix PASS；optional PostgreSQL lane PASS；
- `EXEC077-AC-012`：no unreported public schema/API change、no second truth、no unrelated workspace changes。

## Required Tests

```bash
cd apps/backend
uv run pytest
uv run ruff check app tests
uv run mypy app

tmp_db="$(mktemp -d)/askora-course-workspace.sqlite3"
DATABASE_URL="sqlite+aiosqlite:///$tmp_db" uv run alembic upgrade head
DATABASE_URL="sqlite+aiosqlite:///$tmp_db" uv run alembic check

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

另外必须运行 targeted contract/architecture/isolation/recovery/migration tests、representative upgraded fixture与真实 local API smoke。若项目当前真实命令不同，先按 `pyproject.toml`/CI确认并报告，不得虚构 PASS。

## Completion Report

报告：modified files；owner/schema/API/error/migration matrix；fresh/legacy/upgraded evidence；isolation/recovery/idempotency/concurrency evidence；real API smoke；full gates；commit/PR/CI/merge SHA；XIK-189 update；remaining risks；Product/UX/Engineering/Quality/Learning Evidence separate status。
