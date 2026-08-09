# ADR-0107 — Account Deletion Uses the Canonical Data Erasure Workflow

Status: accepted
Date: 2026-08-09
Decision owner: Codex under the user's explicit authorization to close P1-05 and publish the resulting PR
Decision authority: user-delegated Codex
Affected specs: `identity-privacy-lifecycle.md`, `data-control-contract.md`, P1-05 Vertical Slice, EXEC-037

## Context

P1-05 was implemented before P1-03 landed on `main`. Both slices independently created durable owner-erasure execution records: P1-05 stored owner step receipts, while P1-03 froze `DataErasureWorkflowV1` with workflow, step, receipt and checkpoint records as the single owner-coordinated erasure workflow. Keeping both implementations would create permanent dual truth and would violate `ARCH-031`, `STATE-001/041` and `DATA-075`.

The account product journey still needs behavior that the generic P1-03 command does not own: password re-authentication, the exact account-deletion phrase, a 24-hour grace period, cancellation, revocation of ordinary sessions and a deletion-control token.

## Decision

1. Platform Identity/Privacy continues to own account-deletion preview, re-authentication, grace/cancel lifecycle, ordinary-session revocation, deletion-control authorization and the final minimal account tombstone.
2. Once an account request becomes due, P1-05 MUST invoke P1-03 with the fixed `ALL_PERSONAL_DATA` scope. P1-03 `DataErasureWorkflowV1` is the only durable execution truth for owner steps, retry results, receipt and monotonic erasure checkpoint.
3. P1-05 MUST NOT write a second owner-erasure receipt stream. The unmerged P1-05 `owner_erasure_step_receipts` schema and model are retired before release. `AccountDeletionRequest` stores only the canonical P1-03 workflow/receipt/checkpoint references required for orchestration and status projection.
4. The P1-05 durable preview and exact phrase are an accepted authorization envelope for the later internal `ALL_PERSONAL_DATA` invocation. At purge time, P1-03 builds a current plan under that fixed scope; a change in record count does not change the accepted business scope. Ambiguous ownership still fails closed.
5. Account state remains `PURGING` while the canonical workflow is retryable, partial or awaiting required post-erasure maintenance. It becomes `DELETED` only after the canonical receipt/checkpoint exists and the applicable no-resurrection adapter is complete.
6. macOS private SQLite uses P1-03 managed recovery-point invalidation and VERIFIED `POST_ERASURE` baseline. PostgreSQL/service verification uses an explicit operational no-resurrection adapter and MUST NOT claim P1-03 desktop backup support.
7. P1-05 `PrivacyTombstone` and external subject restore barrier are projections/adapters derived from the canonical P1-03 receipt/checkpoint. They do not own owner-step status and cannot mark deletion complete without the canonical receipt.
8. The exhaustive P1-05 subject registry becomes the `ALL_PERSONAL_DATA` coverage adapter for tables that landed after P1-03. P1-03 workflow records, P1-05 deletion-control records and privacy tombstones are governance records and are excluded from the erased subject payload.

## Alternatives Considered

- **Keep both workflows and reconcile their receipts**: rejected because it preserves two durable execution truths and doubles retry/failure semantics.
- **Remove P1-05 grace/cancel and expose the generic immediate P1-03 command**: rejected because it breaks the accepted P1-05 product and security contract.
- **Make P1-05 the erasure owner and treat P1-03 as UI only**: rejected because `DATA-073..076` and `DATA-075` already freeze P1-03 as the canonical workflow.

## Invariants

- One account request maps to at most one canonical idempotency identity and one current P1-03 workflow chain.
- No account request reaches `DELETED` from a partial or missing P1-03 receipt/checkpoint.
- Other users and global policy/config remain untouched; ambiguous bindings block before deletion.
- Retry reuses P1-03 durable step/workflow state and never recreates a P1-05 owner receipt.
- Logs, tombstones and status projections contain no reversible identity, content, secrets or raw manifest.

## Migration and Rollback

P1-05 migrations are not yet on `main`, so the duplicate receipt table is removed from the release migration rather than shipped as a legacy table. The account request receives nullable canonical workflow/receipt/checkpoint references. Existing branch-local databases created from the pre-integration migration are forward-adopted by compatibility checks; a future released database would require a new additive migration instead of rewriting history.

Rollback before merge is branch rollback. After release, forward-fix preserves P1-03 receipts/checkpoints and P1-05 account request/tombstone records; it MUST NOT restore the retired receipt writer.

## Validation

- migration graph and pre-created schema compatibility on SQLite/PostgreSQL;
- architecture test proving only P1-03 writes erasure step/receipt/checkpoint truth;
- account due/cancel/retry/restart tests linked to canonical workflow ids;
- all-model/current-user/cross-user zero-residual coverage, including P1-04/P1-06/activity/auth/recovery tables;
- partial and post-erasure-baseline states cannot report account deletion complete;
- full backend/frontend/docs/security gates and real account-deletion browser path.
