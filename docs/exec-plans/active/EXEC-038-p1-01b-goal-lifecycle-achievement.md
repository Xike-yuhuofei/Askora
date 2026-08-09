# EXEC-038 — P1-01B Goal Lifecycle and Evidence-gated Achievement

> Status: FROZEN / WAITING_FOR_EXEC-037
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
