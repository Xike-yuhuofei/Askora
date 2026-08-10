# EXEC-063 — Workspace-scoped Material and SYS02 Retrieval Cutover

> Status: **FROZEN / BLOCKED_BY_EXEC_061**  
> Linear: XIK-172  
> Priority: P0 Retrieval Isolation  
> Frozen: 2026-08-10  
> Governing gap: GAP-V1-002

## 1. Objective

Cut production Library/RAG/SYS02 paths from LocalOwner-global scope to explicit Workspace-scoped retrieval backed by the durable Workspace/Project membership created by EXEC-061.

Do not redesign retrieval ranking algorithms.

## 2. Dependency

```text
EXEC-061 DONE
→ EXEC-063
```

EXEC-062 may run independently after EXEC-061; retrieval cutover must preserve any concurrent learner-scope changes.

## 3. Required Sources

- `PRODUCT-POSITIONING.md`
- ADR-0016 / `WSP-*`
- `SYS02-*`
- `LIB-*`
- Domain Model / Dependency Rules
- Content ingestion/source locator contracts
- current Library/search/RAG/index/cache implementation

## 4. Frozen RetrievalScope

Ordinary production retrieval must resolve:

```yaml
workspace_id: required
project_ids: optional
material_ids: optional
knowledge_unit_ids: optional
session_context: optional
```

`LocalOwner` is ownership context, not RetrievalScope.

Optional refs can only narrow inside the required Workspace.

## 5. Implementation Tasks

1. Introduce/use one typed RetrievalScope at application/SYS02 boundaries.
2. Make `workspace_id` mandatory for ordinary Library/RAG/SYS02 queries after cutover.
3. Resolve Project scope through canonical ProjectMaterial membership.
4. Validate material/KU/session refs belong to the same Workspace.
5. Update Library list/search/knowledge-map/read projections to require exact Workspace where applicable.
6. Add Workspace and relevant subordinate scope to cache/index keys.
7. Ensure current source/revision/index versions remain pinned in EvidenceBundle/RetrievalTrace.
8. Prevent cross-workspace duplicate/search metadata leakage.
9. Bound legacy owner-global endpoints to the deterministic default Workspace only; add retirement tests.
10. Preserve SYS02 answer-exposure/grader-only/tightening-only behavior.
11. Preserve citation → SourceSpan replay.
12. Add two-Workspace E2E isolation fixtures.

## 6. Allowed Files

- SYS02 retrieval/application/query code
- Library/RAG API/application adapters
- search/index/cache projection code
- ProjectMaterial read/query integration
- source/knowledge scope validation helpers
- relevant frontend API callers only when required to supply Workspace scope; no UI redesign
- tests

## 7. Forbidden Changes

Do NOT:

- add a fake `workspace_id` parameter while underlying query remains owner-global;
- introduce Global Search/Global Library;
- search other Workspaces then filter results in UI;
- redesign BM25/dense/RRF/reranking strategy;
- weaken citation/exposure/ACL rules;
- use Project title/tag as access control;
- allow cache entries without Workspace identity;
- infer current Workspace solely from browser localStorage.

## 8. Acceptance Criteria

- `EXEC063-AC-001`: every normal retrieval request has exact Workspace before SYS02 execution.
- `EXEC063-AC-002`: Workspace A cannot list/search/retrieve Material/KU from Workspace B.
- `EXEC063-AC-003`: Project scope retrieves only Materials attached to that Project and Workspace.
- `EXEC063-AC-004`: Material/KU/session narrowing rejects cross-workspace refs without metadata leakage.
- `EXEC063-AC-005`: cache/index reuse cannot cross Workspace or exposure boundary.
- `EXEC063-AC-006`: EvidenceBundle items remain traceable to exact SourceSpan/current source revision.
- `EXEC063-AC-007`: SYS02 can only tighten TeachingAction exposure and does not become TeachingAction owner.
- `EXEC063-AC-008`: legacy owner-global compatibility, if retained, resolves default Workspace only and has explicit retirement tests.
- `EXEC063-AC-009`: no production Global Material Library query remains.
- `EXEC063-AC-010`: existing Book-to-Learning/adaptive retrieval regression passes under Workspace scope.

## 9. Required Tests

- Workspace A/B isolation for Library/search/RAG;
- ProjectMaterial scope;
- cache scope keys and invalidation;
- cross-workspace negative refs;
- source citation/replay;
- exposure/grader-only regression;
- legacy default-Workspace adapter regression;
- Book-to-Learning E2E with explicit Workspace.

## 10. Completion Report

Report exact routes/application contracts changed, legacy adapters retained/retired, cache/index migration semantics, isolation tests and Required CI state.

Archive only after all ACs pass.