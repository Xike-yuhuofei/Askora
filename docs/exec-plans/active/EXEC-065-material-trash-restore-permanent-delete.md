# EXEC-065 — Material Trash, Restore and Permanent Delete Closure

> Status: **FROZEN / BLOCKED_BY_EXEC_061**  
> Linear: XIK-174  
> Priority: P0 Data Safety  
> Frozen: 2026-08-10  
> Governing gap: GAP-V1-005

## 1. Objective

Implement `MATLIFE-*` so normal Material delete is recoverable Trash, Restore preserves exact identity/source/project relationships, and irreversible deletion only occurs through the governed Data Control DOCUMENT erasure workflow.

## 2. Dependency

```text
EXEC-061 DONE
→ EXEC-065
```

Material must already have canonical Workspace attribution and normalized SourceFile foundation.

## 3. Required Sources

- `PRODUCT-POSITIONING.md`
- `MATLIFE-*`
- `LIB-*`
- `WSP-*`
- Persistence / Data Control / Recovery contracts
- current DocumentService/delete API/storage/jobs/index implementation

## 4. Current Reality to Verify

Audit baseline ordinary `DocumentService.delete_document(...)` marked the row deleted/failed and then immediately called physical `storage.delete_file(...)`.

Re-read current main. If any portion is already corrected, preserve it and only close remaining contract gaps.

## 5. Implementation Tasks

1. Add canonical Material lifecycle/version fields and migration.
2. Migrate legacy `is_deleted/deleted_at` per source-present/source-missing rules in MATLIFE.
3. Change ordinary existing DELETE compatibility endpoint, if retained, to Trash semantics only.
4. Implement explicit Trash/list/Restore application/API commands.
5. Trash transaction retains SourceFile and ProjectMaterial membership.
6. Stop/invalidate ordinary search/retrieval/new-learning visibility for Trash.
7. Add late-job publish guard keyed to Material lifecycle/version.
8. Restore verifies retained SourceFile and current revision before advertising readiness.
9. Restore rebuilds/validates stale derived projections rather than guessing READY.
10. Implement delete-impact preview with Project references and Data Control categories.
11. Permanent Delete delegates to canonical DOCUMENT erasure workflow; no parallel SYS01 cascade.
12. Ensure target is fail-closed while permanent erasure is running/partial.
13. Physical SourceFile deletion occurs only inside accepted SYS01 erasure owner step.
14. Advance/consume erasure checkpoint so old backup/projection cannot resurrect source.
15. Add explicit stable errors and idempotency/version-conflict behavior.
16. Add UI minimum flow required for Trash/Restore/Permanent Delete without redesigning Library IA.

## 6. Allowed Files

- Material/document lifecycle persistence/service/API
- SourceFile/storage adapter only for governed delete/restore
- Library search/RAG visibility checks
- document/background job publish checks
- Data Control DOCUMENT workflow integration
- minimal Library UI/API callers
- migrations/tests

## 7. Forbidden Changes

Do NOT:

- physically delete SourceFile during ordinary Trash;
- use `processing_status=FAILED` as lifecycle truth;
- delete ProjectMaterial on Trash;
- recreate missing source from stale chunks/index/old backup;
- let Trash content enter RAG/LLM context;
- let a pre-Trash job publish after Trash;
- implement SYS01 cross-owner cascade instead of Data Control;
- infer broad erasure consent from a legacy source-missing row;
- implement automatic cleanup by direct filesystem deletion;
- change Workspace/Project ownership.

## 8. Acceptance Criteria

- `EXEC065-AC-001`: ordinary delete is active→trash and never deletes SourceFile bytes.
- `EXEC065-AC-002`: Trash survives restart/backup and exact Material identity is restorable.
- `EXEC065-AC-003`: ProjectMaterial memberships survive Trash; relationship removal remains independent.
- `EXEC065-AC-004`: Trash is excluded from default Library/search/RAG/new learning.
- `EXEC065-AC-005`: late background job cannot republish trashed material as current.
- `EXEC065-AC-006`: Restore validates source and never guesses processing READY.
- `EXEC065-AC-007`: Permanent Delete requires preview/confirmation/idempotency and canonical DOCUMENT erasure workflow.
- `EXEC065-AC-008`: physical source deletion only occurs inside accepted erasure owner step; partial failure is not reported complete.
- `EXEC065-AC-009`: permanent deletion prevents old backup/projection resurrection.
- `EXEC065-AC-010`: legacy deleted + source-present migrates to Trash.
- `EXEC065-AC-011`: legacy deleted + source-missing migrates to terminal legacy tombstone without content reconstruction or inferred extra erasure.
- `EXEC065-AC-012`: no processing-state/lifecycle dual truth remains in new writers.

## 9. Required Tests

- Trash/Restore restart roundtrip;
- source checksum/managed-file retention;
- Project membership retention;
- Library/RAG exclusion;
- late worker race;
- restore source-missing/corrupt negative cases;
- permanent-delete preview/confirmation/idempotency;
- Data Control partial/retry/recovery;
- no-resurrection with old recovery fixture;
- legacy migration matrix in MATLIFE-112;
- cross-workspace negative delete/restore;
- Required CI relevant jobs.

Coordinate Quality lifecycle evidence with XIK-154 and migration evidence with XIK-155.

## 10. Completion Report

Report schema/migration mapping counts, old DELETE endpoint semantics, physical file deletion call sites before/after, Data Control integration, no-resurrection evidence, tests and Required CI state.

Archive only after all ACs pass.