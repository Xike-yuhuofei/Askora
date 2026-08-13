# ADR-0016 — Workspace, LearningProject and LearningSession Scope Ownership

Status: accepted  
Date: 2026-08-10  
Decision authority: user-directed ChatGPT architecture closure  
Authorized objective: XIK-168 / close `GAP-V1-001` design-spec gap  
Affected specs: `DOMAIN-*`, `STATE-*`, `PERSIST-*`, `API-*`, `LIB-*`, `SYS02-*`, `SYS03-*`, `SYS06-*`, platform Workspace/Project/Session contract

## Context

`docs/product/PRODUCT-POSITIONING.md` has already frozen the v1 product model:

```text
LocalOwner
└── Workspace
    ├── Material
    ├── LearningProject
    │   └── ProjectMaterial N:M Material
    ├── LearningGoal
    └── LearningSession
```

Current `main` at the XIK-168 audit baseline does not yet have durable Workspace, LearningProject or ProjectMaterial aggregates. `/api/v1/workspace/*` is a UI/read-model aggregation route, not the Product Positioning Workspace aggregate. Existing `UserDocument`, Goal, Dialog and learner-state records remain LocalOwner-global.

The existing `STATE-*` contract already assigns Workspace to Platform Workspace Registry and LearningProject/ProjectMaterial to Platform Workspace/Product Organization. The remaining architectural ambiguity is LearningSession ownership and how to migrate the existing document/dialog storage without creating duplicate truths.

## Decision

### 1. Workspace remains a Platform aggregate

Workspace is owned by **Platform Workspace Registry**. It is not SYS09, Tenant, Organization, Account or an authentication boundary.

Workspace owns only product-level scope/lifecycle metadata. It does not write Material content, Goal semantics, LearnerState, TeachingAction or any SYS01～SYS08 truth.

### 2. LearningProject is an organizational aggregate

LearningProject and current `ProjectMaterial` membership are owned by **Platform Workspace / Product Organization**.

A LearningProject:

- belongs to exactly one Workspace;
- may reference many Materials in the same Workspace;
- may organize many LearningGoals in the same Workspace;
- does not own or copy Material/Goal content;
- does not become a prerequisite for starting a LearningSession.

Removing a Material from a Project removes only the membership relation.

### 3. LearningSession uses a Platform Learning Session Registry

`LearningSession` is owned by **Platform Learning Session Registry**.

Its responsibility is intentionally narrow:

```text
continuous learning interval
+ exact workspace scope
+ optional project/goal/material context
+ lifecycle/time boundary
```

It MUST NOT own:

- transcript/message truth;
- TeachingAction or TeachingStage;
- AssessmentResult/Attempt scoring;
- LearnerState/MasteryEstimate;
- LearningPlan/Activity semantics;
- model/tool execution truth.

Those remain with their existing owners.

### 4. LearningSession is not DialogSession

Historical `DialogSession` is a compatibility conversation/transcript object and contains legacy fields such as Socratic strategy/hint/mastery summaries. It MUST NOT be renamed in place and declared canonical LearningSession truth.

A DialogSession MAY reference a LearningSession after migration when the relationship is known. Unstructured historical conversations MAY remain `learning_session_id = null`; they still receive Workspace scope for isolation.

### 5. Do not create a second Material truth

The existing `user_documents.id` identity is adopted as the persistence compatibility identity for canonical `material_id` during v1 migration. A second parallel `materials` table that duplicates the same current Material metadata/lifecycle truth MUST NOT be introduced merely for naming purity.

Implementation MAY rename the ORM class/table in a later cleanup migration, but identity must remain stable and there must be one canonical Material writer.

### 6. Normalize managed SourceFile separately

Material and SourceFile remain distinct domain concepts. Current `user_documents` embeds original filename/storage path/checksum fields. The v1 migration creates normalized managed SourceFile records linked to `material_id` and backfills one primary SourceFile from every valid existing imported Material.

After writer cutover:

- new source-file truth is written only through the SourceFile repository/application boundary;
- legacy embedded file columns become compatibility read/audit fields with an explicit retirement condition;
- no permanent dual-write is allowed.

This preserves current Material identity while establishing the Product Positioning `Material 1:N SourceFile` boundary.

### 7. Workspace scope must be explicit where state can otherwise mix

The implementation contract must require direct or unambiguous pinned Workspace attribution for all records that could otherwise be merged across Workspace boundaries.

At minimum direct `workspace_id` is required on:

- Material;
- LearningProject;
- LearningGoal aggregate records;
- LearningSession;
- library tags/collections/search projections/command receipts;
- LearnerEvidence;
- MasteryEstimate;
- LearnerState;
- ReviewSchedule or its workspace-scoped current projection;
- operational/background jobs when tied to a Workspace.

Assessment/decision/history records MAY resolve Workspace through immutable exact parent refs when that resolution is lossless and architecture tests prove no cross-workspace write/query path. Implementations must not duplicate workspace fields merely as unaudited denormalized guesses.

### 8. Default Workspace migration is deterministic and idempotent

For each valid local datastore:

1. resolve the single LocalOwner;
2. create exactly one active default Workspace when none exists;
3. rerunning bootstrap/migration MUST resolve the same row, never create a second default;
4. backfill all legacy LocalOwner-global records into that default Workspace according to the implementation contract;
5. validate all active canonical records are Workspace-attributable before making required scope non-null/fail-closed;
6. only then cut active writers/readers to Workspace-aware contracts.

The default Workspace display name is mutable presentation metadata and is not identity.

### 9. Cross-workspace references fail closed

ProjectMaterial, Goal→Project, Session→Project/Goal/Material, RetrievalScope and learner-state/evidence bindings MUST reject refs belonging to a different Workspace.

Failure must not disclose whether a foreign Workspace/object exists beyond what the LocalOwner is already allowed to know; ordinary application contracts return stable invalid-scope/not-found style errors.

### 10. Compatibility is bounded

Owner-global endpoints/fields MAY remain temporarily only as migration adapters. When used, they MUST resolve the canonical default Workspace and MUST NOT perform an unbounded all-workspace query.

Once active frontend/application writers use Workspace-aware contracts and representative legacy fixtures migrate correctly, the owner-global write path must be retired.

## Alternatives Considered

### A. Create a new `materials` table and keep `user_documents` in parallel

Rejected. It creates two current Material truths during the highest-risk migration and forces every existing foreign key to choose between them. Stable identity is more valuable than naming purity.

### B. Treat `/workspace/*` UI aggregation as the Workspace implementation

Rejected. A read-model route has no durable identity, membership, migration or isolation invariant and cannot safely scope retrieval or learner state.

### C. Reuse `DialogSession` as LearningSession

Rejected. `DialogSession` is conversation-centric and contains legacy strategy/mastery state that is explicitly non-canonical under v0.3. Renaming it would blur transcript, policy and learner-state ownership.

### D. Put LearningSession under SYS06

Rejected for v1. LearningSession may exist before or without a Goal/Plan/Activity and is fundamentally a temporal product-scope container. SYS06 remains owner of Goal/Objective/Activity/Plan semantics; the Platform Session Registry stores only scope/lifecycle refs.

### E. Use LocalOwner as the retrieval/state scope and add Workspace only in UI

Rejected. This recreates a global library/learner state beneath a cosmetic Workspace selector and violates Product Positioning.

## Consequences

- v1 gains a real data isolation unit without introducing multi-tenancy.
- existing Material IDs remain stable.
- SourceFile becomes independently governable and future 1:N material assets are possible.
- LearningSession can organize teaching/transcript/assessment refs without taking their ownership.
- learner evidence/mastery must become Workspace-specific, preventing accidental transfer of mastery between independent learning spaces.
- migration is larger than adding a single `workspace_id`, but it is still additive-first and avoids a permanent dual truth.

## Migration / Rollback

Migration is additive-first:

```text
LocalOwner resolved
→ create/default Workspace
→ add Workspace/Project/Session/SourceFile structures
→ add nullable workspace refs to affected legacy tables
→ backfill default Workspace
→ backfill normalized SourceFile
→ validate same-workspace invariants
→ cut writers
→ cut readers/retrieval
→ make required refs strict
→ retire owner-global/embedded-file compatibility writers
```

Rollback before writer cutover MAY remove additive structures after validation. After new canonical writes exist, prefer forward-fix; do not silently collapse multiple Workspaces back to LocalOwner-global data.

A downgrade that would lose Workspace membership, Project membership or SourceFile identity is forbidden.

## Validation

Required verification includes:

- fresh datastore default Workspace bootstrap;
- migration of representative LocalOwner-global fixtures;
- rerun/idempotency of bootstrap;
- one LocalOwner with multiple Workspaces;
- same-workspace ProjectMaterial constraints;
- Goal/Session/project reference validation;
- learner evidence/state isolation;
- legacy DialogSession remains non-canonical and may be unbound to LearningSession;
- SourceFile backfill without changing Material IDs;
- backup/restore/migration forward-fix;
- cross-workspace query/write/retrieval negative tests;
- Required CI on the exact implementation commit.

## Supersedes / Superseded By

This ADR specializes the Workspace/Project/Session implications already frozen by `PRODUCT-POSITIONING.md`, `DOMAIN-201..205` and `STATE-005..007`.

It does not supersede v0.3 Teaching Policy, SYS01～SYS08 ownership, ADR-0014 UI information architecture or ADR-0015 LocalOwner/no-auth semantics.
