# EXEC-061 — Workspace / Project / Session Persistence and Migration

> Status: **FROZEN / BLOCKED_BY_EXEC_060**  
> Linear: XIK-171  
> Priority: P0 Product Architecture  
> Frozen: 2026-08-10  
> Governing gap: GAP-V1-001

## 1. Objective

Implement ADR-0016 + `WSP-*` durable Workspace, LearningProject, ProjectMaterial, LearningSession and normalized SourceFile foundation, preserving existing Material identity and migrating LocalOwner-global data into one deterministic default Workspace.

## 2. Dependencies

Hard dependency:

```text
EXEC-060 DONE
→ EXEC-061
```

Design dependency already satisfied by:

- ADR-0016
- `docs/specs/platform/workspace-project-session-scope.md`

If those contracts prove ambiguous during implementation, stop as `BLOCKED_BY_SPEC_GAP`; do not invent ownership/schema semantics.

## 3. Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0015 / ADR-0016
- `LID-*`
- `WSP-*`
- Domain Model / State Ownership / Dependency Rules
- Persistence / Data Control contracts
- current Material/document, Goal, dialog/session, library, job models/migrations

## 4. Current Reality to Verify

At audit baseline:

- no durable Workspace model;
- no LearningProject/ProjectMaterial durable model;
- `/workspace/*` is UI aggregation, not the product aggregate;
- Material/Goal/Dialog/learner records are owner-global;
- `user_documents.id` is the existing stable Material-compatible identity;
- managed file metadata is embedded in the legacy Material/document row.

Re-audit current main before coding and preserve any already-correct work.

## 5. Allowed Files

Primarily:

- platform/workspace/session application/domain modules
- SQLAlchemy models and repositories
- Alembic migrations
- Material/document persistence only as required for Workspace + SourceFile cutover
- Goal records only for Workspace attribution required by WSP
- dialog compatibility only for Workspace/session refs
- API/application contracts for Workspace/Project/Session
- focused migration/repository/application tests

Do not perform SYS03 learner-state scope propagation here; that is EXEC-062.
Do not perform SYS02 retrieval cutover here; that is EXEC-063.
Do not implement Material Trash here; that is EXEC-065.

## 6. Frozen Implementation Shape

### 6.1 Workspace

Create one Platform Workspace Registry truth with stable Workspace IDs and exactly one active default Workspace for the LocalOwner after bootstrap.

### 6.2 Material identity

Preserve existing `user_documents.id` as stable `material_id` compatibility identity. Do not create a second writable Material truth merely to rename the table.

### 6.3 SourceFile

Normalize managed SourceFile records per `WSP-022`, backfilling from existing managed storage metadata without re-copying bytes solely for migration.

### 6.4 LearningProject / ProjectMaterial

Implement durable same-Workspace Project organization. N:M membership is current organizational state and removing membership does not delete Material.

### 6.5 LearningSession

Implement narrow Platform Learning Session Registry. It MUST NOT own transcript, TeachingAction, AssessmentResult, LearnerState or LearningPlan semantics. Do not rename legacy DialogSession into LearningSession.

## 7. Migration Tasks

Execute WSP phases in order:

```text
preflight LocalOwner/recovery/schema
→ additive structures
→ nullable workspace refs
→ create/resolve default Workspace
→ backfill Workspace refs + SourceFile
→ validate identity/FK/same-workspace integrity
→ cut writers
→ cut readers needed by this foundation
→ make required refs strict where safe
→ retire bounded owner-global/embedded-file writers
```

At minimum migrate Workspace attribution for Material/Library/Goal/Dialog and the platform structures required for subsequent EXECs.

LearnerEvidence/Mastery/LearnerState/Review backfill is intentionally finalized in EXEC-062 after this foundation exists.

## 8. Forbidden Changes

Do NOT:

- create Tenant/Organization/RBAC semantics;
- create a parallel writable `materials` table while `user_documents` stays canonical writable truth;
- rewrite stable Material/Revision/SourceSpan IDs;
- guess LearningSession from legacy DialogSession when exact refs are absent;
- make LearningProject own copies of Material/Goal content;
- allow cross-workspace Project/Goal/Session refs;
- implement Workspace destructive cascade delete;
- combine retrieval/learner-state/Trash full closures into this EXEC;
- weaken migration/recovery tests.

## 9. Acceptance Criteria

- `EXEC061-AC-001`: fresh datastore bootstraps exactly one LocalOwner and one active default Workspace.
- `EXEC061-AC-002`: rerun bootstrap/migration is idempotent and does not create duplicate default Workspace.
- `EXEC061-AC-003`: existing Material IDs remain stable.
- `EXEC061-AC-004`: every migrated valid Material has exact Workspace attribution and normalized managed SourceFile identity.
- `EXEC061-AC-005`: SourceFile backfill does not duplicate bytes solely for migration and validates known checksum/path state.
- `EXEC061-AC-006`: one Material can belong to multiple Projects within the same Workspace.
- `EXEC061-AC-007`: cross-workspace ProjectMaterial/Goal/Session refs are rejected.
- `EXEC061-AC-008`: removing ProjectMaterial never deletes Material or SourceFile.
- `EXEC061-AC-009`: LearningSession exists without requiring Project/Goal and owns no teaching/mastery/transcript truth.
- `EXEC061-AC-010`: legacy DialogSession may remain unbound when a real LearningSession cannot be reconstructed; no guessed bindings.
- `EXEC061-AC-011`: active new Material/Goal/Session writers cannot create owner-global records after cutover.
- `EXEC061-AC-012`: representative legacy SQLite migration and forward-fix/recovery verification pass.
- `EXEC061-AC-013`: no Workspace cascade delete is introduced.

## 10. Required Tests

- migration fresh + legacy fixture + rerun;
- default Workspace uniqueness;
- SourceFile backfill/integrity;
- ProjectMaterial same-workspace property;
- Goal/Session cross-workspace negative tests;
- owner-global compatibility resolves default Workspace only;
- architecture tests for one writer/no second Material truth;
- SQLite migration/recovery gates;
- relevant API/application tests.

Coordinate, do not duplicate, Quality migration evidence in XIK-155/EXEC-055.

## 11. Completion Report

Report exact commits, schema/migration revisions, row/backfill counts on fixtures, stable-ID evidence, tests, any compatibility writers retained + retirement condition, and blockers for EXEC-062/063/065.

Archive only after all ACs pass.