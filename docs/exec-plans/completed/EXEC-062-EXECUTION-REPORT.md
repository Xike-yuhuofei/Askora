# XIK-177 / EXEC-062 EXECUTION REPORT

## STATUS
**XIK-177 READY_FOR_ACCEPTANCE**

## COMMITS
- **BASE_COMMIT**: `dd6be65b80639b4d44382469dafbd8a3c0f47dc8` (`origin/main`)
- **FINAL_COMMIT**: `26d4eda73eb998542ab59c139df4f224972e7785` (implementation; report doc committed on top)
- **BRANCH**: `codex/xik-177-exec-062` (dedicated worktree `../Askora-xik-177`, not shared with EXEC-063/065)
- **ALEMBIC_REVISION**: `x062d0e0a001` (single head; revises `w171d0e0a001`)

## SCHEMA / QUERY KEY CHANGES
Additive, non-destructive migration. Added a nullable `workspace_id` attribution column to all SYS03/SYS04/SYS07 records:

| Table | New column | Workspace-scoped key |
| --- | --- | --- |
| `learner_evidence` | `workspace_id` | `uq_learner_evidence_workspace_source_result (workspace_id, source_result_id)` |
| `canonical_mastery_estimate_versions` | `workspace_id` | `uq_canonical_mastery_version (workspace_id, user_id, knowledge_unit_id, version)` |
| `learner_state_versions` | `workspace_id` | `learner_state_id` already embeds workspace (`askora:learner-state:{user}:{workspace}`) |
| `review_schedule_versions` | `workspace_id` | `idx_review_latest` rebuilt to include `workspace_id`; schedule_id embeds workspace |
| `review_observations` | `workspace_id` | `ix_review_observations_workspace_id` |
| `canonical_assessment_attempts` | `workspace_id` | `uq_canonical_attempt_workspace_idempotency (workspace_id, idempotency_key)` |
| `canonical_assessment_result_versions` | `workspace_id` | `ix_canonical_assessment_result_versions_workspace_id` |

Legacy owner-global UNIQUE INDEXes (`ix_canonical_assessment_attempts_idempotency_key`, `ix_learner_evidence_source_result_id`) were rebased into the workspace-scoped compound constraints above, and a matching non-unique index reinstated so the migrated schema matches `Base.metadata.create_all` (`alembic check` clean). No stable evidence/estimate/state ID is regenerated.

## MIGRATION RESULT
- `alembic upgrade head` from a fresh DB succeeds across the full chain (`... -> g001d0e0a001 -> w171d0e0a001 -> x062d0e0a001`).
- `alembic heads` reports exactly one head: `x062d0e0a001 (head)`.
- `alembic check` passes (no model/migration drift) — verified by the migration suite (`test_local_owner_migration`, `test_sqlite_migration_gate`, `test_decision_trace_input_migration`).
- Downgrade is reversible and restores the legacy owner-global unique indexes.
- Legacy owner-global rows are backfilled deterministically into the default Workspace by `WorkspaceBootstrapService.migrate_legacy_to_default` (application-layer, matching XIK-171), covering `learner_evidence`, `canonical_mastery_estimate_versions`, `learner_state_versions`, `review_schedule_versions`, `review_observations`, `canonical_assessment_attempts`, `canonical_assessment_result_versions`.

## WORKSPACE A/B ISOLATION EVIDENCE
`tests/integration/test_exec062_workspace_isolation.py` (12 tests) builds a fresh SQLite datastore with default Workspace A and a second Workspace B, using the **same KnowledgeUnit** in both, and proves the invariant:

```text
same LocalOwner + same KnowledgeUnit + different Workspace
!= same learner evidence/mastery/review stream
```

Key assertions:
- Evidence written to A is only visible in A; evidence written to B is only visible in B (no cross-Workspace fusion).
- Mastery `estimate_id` / version stream differ between A and B; `LearnerState` projections reference only each Workspace's own estimate IDs.
- `ReviewSchedule` consumes only same-Workspace evidence/state.
- Same idempotency key in A and B produce independent attempt/result/evidence streams (no cross-Workspace dedup collision).
- Invalidation in A reprojects only A; B's estimate is untouched.
- After deleting all Workspaces, `resolve_workspace_id` deterministically recreates exactly one default Workspace; evidence/state writers still fail closed without an exact Workspace (`TypeError`).

## REPLAY EVIDENCE
`test_ac007_deterministic_replay_is_offline_and_reproducible` invokes the pure `WeightedBKTProjector` offline with a fixed evidence sequence, then re-feeds the same evidence in reversed order, and asserts the resulting `MasteryEstimate` is **equal** (order-insensitive, deterministic, offline — no model/network dependency).

## TEACHING POLICY REGRESSION
- `test_ac008_evidence_eligibility_weighting_unchanged` re-asserts the frozen SYS03 eligibility weights (independent=1.0, assisted=0.35, answer_exposed=0.0) and assessment independence classification.
- Teaching Policy algorithms untouched; full suite passes `tests/unit/test_teaching_policy_layers.py` and `tests/e2e/test_v03_adaptive_loop.py`.

## ACCEPTANCE CRITERIA

| AC | Verdict | Evidence |
| --- | --- | --- |
| EXEC062-AC-001 — evidence isolation | PASS | `test_ac001_ac002_evidence_and_mastery_are_workspace_isolated`: A/B evidence lists disjoint; `list_evidence(workspace_id=...)` filters by workspace |
| EXEC062-AC-002 — mastery/version + learner-state isolation | PASS | Same test: distinct `estimate_id`/version; `test_ac002_learner_state_is_workspace_isolated` asserts state references only its own workspace's estimates |
| EXEC062-AC-003 — review isolation | PASS | `test_ac003_review_schedule_is_workspace_isolated`: schedule created via `ReviewPlanningApplication` in A only; B has none; same-KU schedules distinct across workspaces |
| EXEC062-AC-004 — legacy migration | PASS | `test_ac004_legacy_records_migrate_to_default_workspace`: owner-global rows backfilled into default workspace; stable IDs + provenance/source refs preserved; no unattributed rows remain |
| EXEC062-AC-005 — duplicate/idempotency + assessment-to-evidence scope | PASS | `test_ac005_idempotency_is_workspace_scoped`: same key twice in A dedups to one attempt/estimate; same key in B creates an independent stream |
| EXEC062-AC-006 — correction/invalidation isolation | PASS | `test_ac006_invalidation_reprojects_only_affected_workspace`: invalidate A reprojects A only; B estimate unchanged |
| EXEC062-AC-007 — deterministic replay | PASS | `test_ac007_deterministic_replay_is_offline_and_reproducible`: order-insensitive, offline-equal replay |
| EXEC062-AC-008 — Teaching Policy / eligibility regression | PASS | `test_ac008_evidence_eligibility_weighting_unchanged` + full `test_teaching_policy_layers.py` green |
| EXEC062-AC-009 — fail closed without Workspace | PASS | `test_ac009_new_evidence_and_state_writes_are_fail_closed`: required keyword-only `workspace_id` raises `TypeError` for scoring, projecting, and repository writes |
| EXEC062-AC-010 — architecture / state ownership | PASS | `test_ac010_no_cross_owner_repository_write_introduced`: AST-verified every SYS03/SYS04 `save_/invalidate_` is owner/Workspace-scoped; no cross-owner write introduced |

## TESTS
- Workspace A/B isolation suite: **12 passed** (`test_exec062_workspace_isolation.py`).
- Full backend suite: **538 passed, 6 skipped, 3 warnings**.
- Gates: `ruff check app tests` clean; `black --check app tests` clean; `mypy app` success (198 files); `git diff --check` clean; single Alembic head confirmed.

## CONCURRENT-EXEC CONFLICTS
- `git fetch origin` at completion: `origin/main` = `dd6be65` (unchanged from base). `origin/main` is an ancestor of `HEAD`, so no rebase/conflict was required. Dedicated worktree + branch used; no overlap with EXEC-063/065 working directories.
- Migration graph checked after my revision: exactly one head `x062d0e0a001`; no merge migration introduced.

## SPEC GAP
- **None blocking.** The migration correctly handles the legacy owner-global UNIQUE INDEX (realized as a named unique index, not an inline constraint) by rebasing it into a workspace-scoped compound constraint; this was the only deviation from the initial migration sketch and is fully covered by migration tests.

## UNRESOLVED
- None. All EXEC-062 must-implement items are complete; forbidden items (mastery algorithm, Teaching Policy, assistance/answer-exposure, per-Project LearnerState, cross-workspace evidence copy, localStorage canonical inference, SYS02 Retrieval, Trash) were not touched.

## FINAL VERDICT
**XIK-177 READY_FOR_ACCEPTANCE**
