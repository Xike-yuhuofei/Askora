# EXEC-074 — PostgreSQL Membership Constraint Reconciliation

> Status: **DONE / ARCHIVED**
> Priority: P1 Engineering Maintenance
> Frozen: 2026-08-11
> Completed: 2026-08-11
> Governing: PRODUCT-POSITIONING, ADR-0016, WSP-012, WSP-013, DB schema versioning and CI quality contracts

## 1. Objective

Reconcile the PostgreSQL-reflected schema for Workspace membership tables with
the SQLAlchemy canonical metadata without changing Workspace, Project, Material
or LearningSession semantics.

The composite primary keys already enforce the frozen membership uniqueness:

```text
project_materials(project_id, material_id)
learning_session_materials(session_id, material_id)
```

The same-column named `UNIQUE` constraints are redundant physical constraints.
They cause PostgreSQL `alembic check` to report drift after a fresh upgrade even
though the logical contract is already enforced by the primary keys.

## 2. Dependencies and Current Reality

- ADR-0016 and WSP-012/WSP-013 are frozen and sufficient.
- SQLite remains the production-local datastore truth.
- PostgreSQL remains Optional compatibility evidence, not a v1 runtime dependency.
- Revision `w171d0e0a001` created both composite primary keys and redundant named
  unique constraints.
- Current ORM metadata repeats the same redundant unique constraints.
- Optional PostgreSQL CI reports `uq_project_material` and
  `uq_learning_session_material` as autogenerate drift.

This EXEC is a forward reconciliation. Historical migrations MUST remain immutable.

## 3. Allowed Files

```text
docs/exec-plans/active/EXEC-074-postgresql-membership-constraint-reconciliation.md
docs/exec-plans/completed/EXEC-074-postgresql-membership-constraint-reconciliation.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
docs/document-inventory.md
apps/backend/app/models/workspace.py
apps/backend/alembic/versions/*reconcile_workspace_membership_constraints.py
apps/backend/tests/migrations/**
```

## 4. Implementation Contract

1. Remove only the two redundant same-column `UniqueConstraint` declarations
   from canonical ORM metadata.
2. Add one forward Alembic migration after the current head.
3. Upgrade MUST conditionally drop the named redundant constraints when present.
4. Downgrade MUST conditionally restore the named constraints when absent.
5. PostgreSQL MUST use named constraint operations; SQLite MUST use Alembic batch
   table recreation compatible with its DDL limits.
6. Preserve both composite primary keys and all foreign keys/indexes.
7. Preserve existing rows through upgrade, downgrade and re-upgrade.

## 5. Forbidden Changes

- Do not edit `w171d0e0a001` or any other historical migration.
- Do not change Workspace/Project/Material/LearningSession ownership or APIs.
- Do not change same-Workspace validation, membership idempotency or deletion semantics.
- Do not introduce another schema truth, production dependency or backend schema.
- Do not reclassify PostgreSQL as Required or as production-local truth.
- Do not modify unrelated EXEC-061 lifecycle state or broaden into EXEC-062/063/065.

## 6. Acceptance Criteria

- `E074-AC-001`: fresh SQLite upgrade reaches the new single Alembic head.
- `E074-AC-002`: SQLite `alembic check` reports no new upgrade operations.
- `E074-AC-003`: previous-head SQLite data survives upgrade, downgrade and re-upgrade.
- `E074-AC-004`: both composite primary keys remain present after upgrade.
- `E074-AC-005`: duplicate ProjectMaterial and LearningSessionMaterial membership
  remains rejected by the database.
- `E074-AC-006`: the redundant named unique constraints are absent after upgrade
  and restored by downgrade.
- `E074-AC-007`: fresh PostgreSQL upgrade plus `alembic check` passes in Optional CI.
- `E074-AC-008`: no Product Positioning, public schema, owner or WSP semantic delta.

## 7. Required Tests

```bash
cd apps/backend
pytest tests/migrations
ruff check app tests
mypy app

DATABASE_URL=<fresh-sqlite-url> alembic upgrade head
DATABASE_URL=<fresh-sqlite-url> alembic check

# Optional CI / local PostgreSQL when available
DATABASE_URL=<fresh-postgresql-url> alembic upgrade head
DATABASE_URL=<fresh-postgresql-url> alembic check

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## 8. Completion Report

Report base/final commit, revision, exact constraints changed, SQLite and
PostgreSQL evidence, data-preservation/duplicate-membership evidence, changed
files, and any SPEC GAP. Archive only after all applicable ACs pass.

## 9. Completion Evidence

- Base: `db963d7`; implementation commit: `ea78ada`.
- Revision: `w171r0e0a002`, single head over `x174e0e0a002`.
- ORM and migrated schema remove only `uq_project_material` and
  `uq_learning_session_material`; both composite primary keys remain canonical.
- SQLite migration + Workspace regression: `38 passed, 2 skipped`.
- Full backend suite: `566 passed, 6 skipped`.
- Ruff: PASS; Mypy: PASS.
- PostgreSQL 16 fresh upgrade: PASS; `alembic check`: no new operations;
  PostgreSQL DecisionTrace regression: `1 passed`.
- Documentation check and `git diff --check`: PASS.
- Product/owner/public-schema delta: none. SPEC GAP: none.
