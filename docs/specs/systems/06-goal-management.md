# SYS06 Goal Management Specification

> Spec IDs: `GOAL-*`
> Status: FROZEN
> Governing ADRs: ADR-0010, ADR-0011
> Owner: SYS06

## 1. Public contracts

- `LearningGoalDefinitionV2`: immutable semantic version; no current status.
- `LearningGoalStateV1`: append-only `confirmed → active ↔ paused`, `active → achieved`,
  `confirmed|active|paused → archived`; achieved/archived terminal.
- `LearningPlanStateV1`: append-only current plan truth.
- `LearningGoalDraftV1`: `draft|preview_ready|approved_pending_boundary|applying|applied|blocked|cancelled`.
- `GoalChangePreviewV1`: exact input refs, diff, target decision, plan impact and effective boundary.
- `FocusedLearningGoalStateV1`: zero-or-one explicit focus per user.
- `LearningObjectiveV1`, `GoalAchievementEvaluationV1`, versioned `GoalAchievementPolicyV1`.

## 2. Commands and concurrency

`GOAL-010`: every write command MUST carry all relevant `expected_*_version`, `idempotency_key` and
correlation id. Duplicate same payload replays receipt; different payload conflicts. Last-write-wins forbidden.

`GOAL-011`: preview is valid only while all pinned definition/mapping/plan/activity/source/learner refs remain
exact. Stale preview returns `GOAL_PREVIEW_STALE` and leaves current execution unchanged.

## 3. Draft and source gate

`GOAL-020`: pending/processing/no-published-knowledge sources MAY remain in draft but block approval.
failed/rejected/quarantined/archived sources cannot be newly selected; existing refs remain visible with reason.
Executable scope is the SYS01 owner query result.

`GOAL-021`: success criteria require a stable id, cognitive process and measurable statement. Unmeasurable text
blocks preview/apply. Suggested criteria are candidates editable by the user.

`GOAL-022`: target cards expose name/source/evidence/reason, never raw internal ids as the primary label.
Multiple candidates require explicit selected target confirmation.

## 4. Preview and apply

`GOAL-030`: intent/capability/criterion/source/target changes create new definition, mapping, subgraph and plan
versions. Budget/deadline-only changes reuse pinned target evidence and create new mapping+plan versions without
target inference.

`GOAL-031`: no active activity applies immediately. Active activity produces `approved_pending_boundary`.
Normal completion applies pending change before exposing a next old-plan activity. Explicit switch supersedes the
old activity, preserves transcript and creates no mastery/negative evidence.

`GOAL-032`: new plan must be complete before effective refs switch. All old current plans become superseded;
two current plans are forbidden.

`GOAL-033`: first active goal MAY be explicitly focused by default. Today uses only explicit focus when multiple
active goals exist. Pause/archive/achieve clears focus without guessing a replacement.

## 5. Lifecycle

`GOAL-040`: pause also pauses plan, retains activity/transcript and prevents scheduling. Resume restores exact
plan/activity only when pinned inputs remain valid; otherwise remains paused and requires replan.

`GOAL-041`: archive is terminal, supersedes active activity/plan and permits copy-to-new-draft with new goal id.

## 6. Measurement and achievement

`GOAL-050`: default policy differentiates recall delayed independent retrieval; understand/explain independent
explanation plus delayed evidence; apply independent application plus novel context; transfer sufficiently novel
independent transfer. Delay/novelty/score thresholds are versioned parameters.

`GOAL-051`: deterministic scoring is preferred for exact/numeric/structured items. Open response must be
rubric/source/schema-bound and independently reviewed. Low confidence, disagreement, provider failure or prompt
injection cannot create learner failure.

`GOAL-052`: evaluation cites exact accepted evidence per criterion. Achievement eligibility requires every
criterion satisfied, no open independent-validation obligation and no relevant active misconception. Only the user
may confirm achieved.

## 7. Stable errors

At least: `GOAL_VERSION_CONFLICT`, `GOAL_PREVIEW_STALE`, `GOAL_SOURCE_NOT_EXECUTABLE`,
`GOAL_TARGET_CONFIRMATION_REQUIRED`, `GOAL_CRITERION_UNMEASURABLE`, `GOAL_WAITING_ACTIVITY_BOUNDARY`,
`GOAL_REPLAN_REQUIRED`, `GOAL_EVIDENCE_INSUFFICIENT`, `GOAL_MEASUREMENT_UNAVAILABLE`.

## 8. Acceptance criteria

- `GOAL-AC-001`: multi-source draft, explicit target and measurable criterion gates are owner-safe.
- `GOAL-AC-002`: immediate/boundary/supersede apply preserves one effective definition/mapping/plan.
- `GOAL-AC-003`: idempotency/version/stale-preview failure never damages the old plan.
- `GOAL-AC-004`: focus, pause/resume, archive/copy obey append-only lifecycle.
- `GOAL-AC-005`: four criterion types and fail-closed scoring/evaluation are evidence-traceable.
- `GOAL-AC-006`: migration preserves legacy history and retires new legacy writes.
