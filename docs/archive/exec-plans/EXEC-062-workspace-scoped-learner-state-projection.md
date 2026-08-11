# EXEC-062 — Workspace-scoped Learner Evidence / Mastery / Review Projection

> Status: **FROZEN / BLOCKED_BY_EXEC_061**  
> Linear: XIK-177  
> Priority: P0 Learning Data Isolation  
> Frozen: 2026-08-10

## 1. Objective

Implement ADR-0016 / `WSP-030..035` so LearnerEvidence, MasteryEstimate, LearnerState and ReviewSchedule are Workspace-specific and cannot mix evidence between independent learning spaces.

Do this without changing mastery algorithms, v0.3 Teaching Policy or SYS03/SYS04/SYS07 ownership.

## 2. Dependency

```text
EXEC-061 DONE
→ EXEC-062
```

EXEC-061 must provide real durable Workspace and migration foundation first.

## 3. Required Sources

- `PRODUCT-POSITIONING.md`
- ADR-0016
- `WSP-*`
- Domain Model
- State Ownership / Dependency Rules
- SYS03 Learner Model
- SYS04 Assessment
- SYS05 Teaching Policy
- SYS07 Review Scheduler
- Event/Decision contracts
- current learner/assessment/review persistence and projectors

## 4. Frozen Invariant

```text
same LocalOwner
+ same KnowledgeUnit
+ different Workspace
≠ same learner evidence/mastery/review stream
```

Cross-workspace evidence fusion is forbidden.

## 5. Implementation Tasks

1. Add exact Workspace attribution to LearnerEvidence acceptance/persistence.
2. Make MasteryEstimate identity/version stream Workspace-specific.
3. Make LearnerState projection/version stream Workspace-specific.
4. Make ReviewSchedule workspace-specific where derived from that learner state.
5. Backfill existing records to the deterministic default Workspace without changing stable evidence/estimate/state IDs when avoidable.
6. Update uniqueness/index/query keys to include Workspace where required.
7. Update SYS03 projector/recompute/replay to consume one Workspace only.
8. Ensure invalidation/correction reprojects only the affected Workspace.
9. For Attempt/Assessment/TeachingAction/Decision/Outcome records, use direct Workspace field or exact immutable parent resolution only under `WSP-031`; add direct scope where lossless resolution cannot be proven.
10. Make application entry fail closed before creating learning evidence/TeachingAction if Workspace cannot be resolved.
11. Preserve validation-obligation, assistance and anti-oscillation semantics unchanged.

## 6. Allowed Files

- learner evidence/mastery/state models/repositories/projectors
- review-scheduler persistence/application paths
- assessment/decision schema only where Workspace attribution is required and non-duplicative
- Alembic migrations
- relevant application composition
- architecture/integration/replay tests

## 7. Forbidden Changes

Do NOT:

- change mastery thresholds/algorithm as part of scoping;
- create one LearnerState per Project unless a future design says so;
- infer Workspace from browser local state;
- copy evidence across Workspace because KU IDs match;
- change TeachingStage/TeachingAction ownership;
- replace stable evidence/provenance refs unnecessarily;
- perform SYS02 retrieval cutover here.

## 8. Acceptance Criteria

- `EXEC062-AC-001`: evidence from Workspace A cannot update Mastery/LearnerState in Workspace B.
- `EXEC062-AC-002`: same KU in A/B has independent estimate/version histories.
- `EXEC062-AC-003`: ReviewSchedule uses Workspace-matched learner state/evidence only.
- `EXEC062-AC-004`: legacy records migrate to default Workspace with provenance/source refs preserved.
- `EXEC062-AC-005`: duplicate event/evidence idempotency remains correct inside Workspace scope.
- `EXEC062-AC-006`: evidence correction/invalidation reprojects only one Workspace stream.
- `EXEC062-AC-007`: deterministic replay remains deterministic/offline.
- `EXEC062-AC-008`: answer-exposure/assistance evidence eligibility and validation obligations are unchanged.
- `EXEC062-AC-009`: no application path can create unscoped new learner evidence/state.
- `EXEC062-AC-010`: no cross-owner repository write is introduced.

## 9. Required Tests

Use explicit Workspace A/B fixtures with overlapping KU identity/topic and verify:

- evidence isolation;
- mastery isolation;
- learner-state isolation;
- review isolation;
- invalidation/replay isolation;
- assessment→evidence handoff scope;
- v0.3 sequential Teaching Policy regression;
- migration from legacy owner-global state;
- architecture ownership tests.

## 10. Completion Report

Report exact schema changes, migration semantics, Workspace-keyed uniqueness changes, replay results, v0.3 regression evidence and unresolved attribution records if any.

Archive only when all ACs are satisfied.