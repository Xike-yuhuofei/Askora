# ADR-0006 — Workspace Read-model Scope and Missing Objective Metadata

Status: accepted
Date: 2026-08-09
Decision owner: Codex under the user's explicit authorization to execute the accepted product-completion plan
Decision authority: user-delegated Codex
Affected specs: `docs/specs/frontend/ui-read-model-contracts.md`, `docs/archive/specs/ui/screen-contracts.md`, `docs/archive/specs/vertical-slices/ui-02b-goals-path-evidence.md`

## Context

UI-02B requires current-user read-only views for goals, learning path and canonical learning evidence. The owner records already exist, but two ambiguities cannot be resolved safely by presentation code:

1. more than one confirmed or active goal may have a current plan, while `/workspace/path` was specified as a singular view;
2. `LearningPlan` stores objective ids and `LearningActivity` stores an objective id, but no SYS06 owner record currently publishes objective capability, cognitive process or status.

Selecting one of several plans by timestamp would silently create a new "current plan" rule. Deriving objective metadata from goal titles, activity types or knowledge-unit labels would create facts that SYS06 did not publish.

## Decision

UI-02B is an additive, read-only composition layer:

- `/workspace/goals` returns the latest immutable version of every goal owned by the canonical current-user identity;
- `/workspace/path` accepts optional `goal_id` scope;
- without `goal_id`, exactly one eligible current plan may be returned automatically; zero produces an honest empty state and multiple eligible plans produce a scoped-selection state rather than an arbitrary winner;
- plan activities follow the canonical `LearningPlan.activity_ids` order; the frontend may filter for presentation but may not persist a reordered plan;
- objective refs remain exact and versioned, while unavailable owner-published metadata is returned as null with `OBJECTIVE_METADATA_UNAVAILABLE` and partial source status;
- `/workspace/evidence` reads only the latest SYS03 MasteryEstimate per knowledge unit and may attach a label only from current-user-owned SYS01 material revisions;
- product mastery labels remain null until SYS03 publishes a versioned label and rule version;
- legacy profile aggregates are excluded from the primary evidence view and are represented only by an explicitly hidden compatibility descriptor;
- all endpoints use schema `1.0`, current-user scoping, stable ordering and `Cache-Control: private, no-store`.

No command, owner, database schema, activity/session link or completion semantic changes in this decision.

## Alternatives

### Infer missing objective metadata in the query or frontend

Rejected. Goal titles, target capabilities and activity types are not a reliable one-to-one objective record. Inference would violate `UI-DATA-001..004` and create a second truth.

### Add a new durable LearningObjective stream and backfill it in UI-02B

Rejected for this slice. It is a valid future SYS06 change, but requires a domain contract, migration/reconciliation and writer changes. Bundling it into a read-only product slice increases risk and changes ownership semantics.

### Pick the newest active plan when several are eligible

Rejected. Recency is not a frozen business priority rule. Explicit goal scope is honest and deterministic.

## Invariants

- UI/query/API code performs no domain writes and owns no learning state.
- Missing metadata remains missing; it is never converted to an empty string, zero or fabricated label.
- Current-user ownership is established through the canonical LearningGoal owner stream before a plan or activity can be returned.
- Evidence labels never cross document ownership boundaries.
- UI-02B does not provide goal editing, replanning, mastery editing, activity start, session linking or activity completion.

## Migration and Rollback

This is an additive read API and frontend route activation. No database migration or backfill is required. Rollback removes the three route consumers and additive endpoints/contracts; owner records remain untouched. A future durable LearningObjective stream can populate the nullable fields additively while preserving schema `1.0`.

## Verification

- strict contract tests for unknown fields, schema version and timezone-aware timestamps;
- SQLite integration tests for latest-version selection, canonical identity, cross-user isolation, stable plan order, explicit multi-plan scope and null objective metadata;
- architecture tests proving transport-only handlers and read-only query assembly;
- frontend tests for loading, empty, ready, partial, error and unauthorized states, plus no threshold-derived mastery labels;
- full backend/frontend/lint/type/migration/build/audit gates and clean-commit verification.
