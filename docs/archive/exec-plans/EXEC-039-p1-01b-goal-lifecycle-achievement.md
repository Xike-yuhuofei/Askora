# EXEC-039 — P1-01B Goal Lifecycle and Evidence-gated Achievement

> Status: DONE
> Governing: ADR-0011, SYS06 Goal Management, P1-01B

## Objective

Implement lifecycle commands, criterion measurement, fail-closed scoring, accepted-evidence evaluation and
user-confirmed achievement without crossing SYS03/SYS04/SYS06 ownership.

## Allowed files

Same P1-01 goal-management modules and specs plus SYS04 assessment contracts/services/tests required by
ADR-0011. Existing cross-owner modules may only be changed through their public owner service.

## Gate

Four criterion types, deterministic/open-response dual grading, provider/prompt-injection failure, migration,
replay, browser/accessibility, one real configured-model E2E, full gates, independent local commit, no push.

## Completion evidence

- append-only pause/resume/archive/achieve plan and goal state, focus clearing, exact-plan resume and
  archive-to-new-draft copy are implemented through SYS06 commands;
- criterion-specific objectives and assessment activities cover recall, understand, apply and transfer;
- SYS04 deterministic/open-response scoring fails closed on injection, provider failure, low confidence and
  grader disagreement; SYS03 receives only accepted canonical results;
- evidence evaluation cites exact result/evidence refs and only enables a user-confirmed terminal transition;
- migration, replay, owner isolation, real configured-model and real-browser gates are recorded in the P1-01B
  completion report.
