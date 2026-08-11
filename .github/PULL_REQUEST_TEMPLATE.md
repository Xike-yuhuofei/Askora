## Problem / User Outcome

<!--
What problem, defect, or user outcome does this PR address?
Do not describe implementation only. Link the originating Opportunity/Bug when available.
-->

Closes / Relates to: #

## Governing References

<!-- Delete rows that are genuinely not applicable. Do not invent references. -->

- Product Positioning: `docs/product/PRODUCT-POSITIONING.md`
- ADR / Canonical Design:
- Spec / Vertical Slice:
- EXEC:
- Product Gap / Opportunity / Bug:

## Scope

<!-- What is intentionally changed by this PR? Prefer one problem / vertical slice / EXEC. -->

-

## Non-goals

<!-- Explicitly state what this PR must not change. -->

-

## Risk Assessment

<!-- State `None identified` only after considering each relevant boundary. -->

- Product / learning semantics:
- Privacy / security / secrets:
- Data ownership / persistence / migration:
- Runtime / compatibility / recovery:
- Rollback or fail-closed behavior:

## Acceptance Criteria

- [ ] Governing acceptance criteria are satisfied on the candidate SHA.
- [ ] No Product Positioning / ADR / Spec semantic change is hidden inside implementation.
- [ ] Any discovered `POSITIONING GAP` / `SPEC GAP` is explicitly reported rather than silently resolved in code.

## Verification

<!-- Record the candidate SHA and actual evidence. Never write “tests pass” without naming the relevant gate. -->

Candidate SHA: `TBD`

- [ ] `Askora CI / Required` is green on the candidate SHA.
- [ ] Required backend tests are green.
- [ ] Frontend test/build is green when frontend is affected.
- [ ] Migration/recovery checks are green when data/schema/runtime state is affected.
- [ ] Security/privacy checks are green when ownership, secrets, network, deletion, or external providers are affected.
- [ ] Manual / real-browser / real-provider evidence is recorded when the frozen contract requires it.

## Review Findings

<!-- Summarize P0/P1 findings and how they were resolved. Do not merge with unresolved known correctness/security findings. -->

- None / TBD

## Documentation / Release Evidence

- [ ] Current documentation and lifecycle indexes are reconciled.
- [ ] Release Evidence is created or updated when this PR closes an EXEC / product baseline.
- [ ] Historical evidence is not rewritten as current evidence.

## Evidence Classification

<!-- Engineering completion is not proof of product value or learning effectiveness. -->

- Engineering Evidence: `PASS / FAIL / NOT YET VERIFIED`
- Product / Usability Evidence: `PASS / INSUFFICIENT / NOT APPLICABLE`
- Learning Evidence: `PASS / LEARNING_EVIDENCE_INSUFFICIENT / NOT APPLICABLE`

## PR Integrity Checklist

- [ ] I did not delete, weaken, skip, or reclassify a failing Required test merely to make the PR green.
- [ ] I did not expose API keys, credentials, private learning content, or sensitive local paths in code, tests, logs, screenshots, or review evidence.
- [ ] This PR is independently reviewable. If it is a multi-EXEC integration/release PR, the constituent changes already have independently reviewable evidence and the integration role is explicit.
- [ ] Merge is intended only after Required CI is green and P0/P1 review findings are resolved.
