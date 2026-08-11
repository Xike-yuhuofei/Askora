# ADR-0019 — UI Workspace Context and Learning Context Read Projections

Status: accepted; experience assumption amended by ADR-0022
Date: 2026-08-11
Decision owners: user-authorized Askora product governance
Decision authority: user-delegated Codex；用户于 2026-08-11 明确采纳 EXEC-068/069 SPEC GAP 收敛建议并授权执行
Upper authority: `docs/product/PRODUCT-POSITIONING.md`
Affected specs: `docs/specs/architecture/state-ownership.md`, `docs/specs/interfaces/api-contract.md`, `docs/specs/frontend/ui-read-model-contracts.md`, UI-04 Vertical Slice, EXEC-068, EXEC-069
Task scope: close the canonical query gaps required by EXEC-068 and EXEC-069 without changing Product Positioning, SYS01～SYS08 ownership, Teaching Policy, database schema, or migration semantics

## Context

ADR-0018 froze a shared canonical Workspace context and a Learning Context Drawer, but intentionally did not invent their read-query contracts. Current `main` contains two invalid presentation shortcuts:

- frontend constants (`default` / `默认工作区`) stand in for the durable Workspace;
- the component named `LearningContextDrawer` manages mock resources and derives presentation text from React state instead of consuming a canonical query.

The durable default Workspace, SYS05 TeachingAction and SYS06 LearningActivity already exist. The missing decision is how UI may compose those exact owner records without creating a new writer or second truth.

## Decision

### 1. Read-projection boundary

Add two strict, versioned, current-owner-scoped read projections:

```text
GET /api/v1/workspace/context
GET /api/v1/workspace/learning-context?activity_id=<optional UUID>
```

Both endpoints are query-only transport adapters, return `Cache-Control: private, no-store`, and perform no command, write, inference call, or migration.

### 2. Workspace Context projection

`WorkspaceContextResponseV1` reads the exact active default Workspace resolved by Platform Workspace Registry and returns its stable id, version, display name, lifecycle and `is_default` value.

- Platform Workspace Registry remains the only Workspace owner/writer.
- V1 currently exposes one canonical default Workspace and therefore returns `switch_capability=SINGLE_WORKSPACE`; the UI MUST NOT render a fake selector.
- Route ids, subject, session, localStorage and React state MUST NOT supply or override `current_workspace_id`.
- A future multi-Workspace switch command requires a separate accepted command contract; this query does not authorize switching.

### 3. Learning Context projection

`LearningContextResponseV1` is a read-only composition over exact owner records:

- `stage_name` / `stage_ref` come only from the latest canonical SYS05 `TeachingActionV03` for the exact current/requested `LearningActivity` version;
- `next_directions` contains 1..3 ordered SYS06-owned current/next `LearningActivity` refs and deterministic owner-published labels;
- `stage_goal` is learner-facing presentation copy selected from a fixed, versioned server-side catalog keyed by canonical `TeachingStage`. It does not modify or reinterpret the stage mapper, TeachingAction, LearningGoal, LearningObjective or LearningPlan;
- every stage, stage-goal and direction field carries `source_system`, exact `source_ref`, and presentation/query version where applicable;
- no online LLM is called and no LLM text is accepted as canonical direction.

The query returns `READY | MISSING | PARTIAL | STALE`. Transport/dependency failure remains a structured API `ERROR` in the frontend state. `MISSING`, `PARTIAL` and `STALE` MUST NOT be promoted to `READY`.

### 4. Freshness

- no current SYS06 activity/direction → `MISSING`;
- direction exists but no exact SYS05 action yet → `PARTIAL`;
- the latest action references a non-current activity version or the requested activity is completed/superseded → `STALE`;
- exact SYS05 stage plus at least one exact SYS06 direction → `READY`.

### 5. No owner or schema change

The application query assembler owns only serialization/composition. It does not own or persist Workspace, TeachingStage, TeachingAction, LearningGoal, LearningPlan or LearningActivity. No database schema or migration is introduced.

## Alternatives Considered

### A. Compose Drawer fields in React from Today/chat data

Rejected. This would make frontend code infer stage/goal/next and violates ADR-0018 / UXA-DATA-220..222.

### B. Persist a new `learning_context_drawer` table

Rejected. It would create a duplicate truth and require reconciliation with SYS05/SYS06.

### C. Add presentation fields to the LLM response

Rejected. LLM output cannot become canonical next direction or state owner.

### D. Read exact owner records through a versioned query projection

Accepted. It preserves single-writer ownership, exposes honest missing/stale states and requires no data migration.

## Consequences

- EXEC-068 may replace the fake frontend Workspace with a canonical owner query.
- EXEC-069 may consume a strict Drawer query without changing Teaching Policy or planner behavior.
- Before the first TeachingAction for an activity, the Drawer honestly renders `PARTIAL` rather than inventing a stage.
- Query performance uses existing immutable records; a future storage index is a forward optimization and MUST NOT change response semantics.

## Security / Privacy / Replay / Idempotency

- both queries are current LocalOwner + current Workspace scoped and fail closed for foreign activity refs;
- responses contain no Prompt, transcript body, grader-only content, secret or local path;
- queries are side-effect free and stable for the same exact owner versions;
- refresh/retry cannot create state or duplicate facts;
- cross-Workspace existence is not disclosed.

## Migration / Rollback

Additive API and presentation-only forward migration. Rollback removes the new frontend consumer/endpoints and returns to honest unavailable UI; it MUST NOT restore frontend mock truth. No database rollback is required.

## Validation

At least verify:

- canonical Workspace id/name/version are returned from the durable owner record;
- a single Workspace produces no selector or switch command;
- Drawer READY/MISSING/PARTIAL/STALE and transport ERROR states are distinct;
- stage/source refs are exact SYS05 records and directions are ordered exact SYS06 refs;
- frontend performs no stage/goal/next inference and toggle performs no network/owner command;
- foreign Workspace/activity refs fail closed;
- frontend/backend tests, build, audit, docs and diff gates pass.

Engineering / Policy-Ownership / Learning Evidence conclusions remain separate. These projections provide no learning-efficacy evidence.

## Supersedes / Superseded By

This ADR closes the read-query gaps explicitly left open by ADR-0018. It does not supersede ADR-0016, ADR-0018, SYS05, SYS06 or Product Positioning.

ADR-0022 amends the target Experience beyond this ADR's `SINGLE_WORKSPACE` presentation assumption. The current query remains a valid compatibility projection, but Course list/create/current/switch and conflict recovery require a separate accepted technical ADR/Spec before frontend implementation.
