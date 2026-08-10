# Askora Product Development Process

> Status: Current Governance Process  
> Scope: product discovery, prioritization, design, implementation, review, release, and evidence  
> Highest authority: [`product/PRODUCT-POSITIONING.md`](product/PRODUCT-POSITIONING.md)

Askora already has a strong downstream engineering authority chain. This process adds the missing upstream discovery and downstream validation loop without weakening the existing Product Positioning → Design/ADR → Spec → EXEC governance.

## 1. End-to-end flow

```text
User Problem / Research
→ Product Opportunity or Bug
→ Evidence & Hypothesis
→ Priority / Product Positioning Check
→ Canonical Design / ADR when needed
→ Spec / Vertical Slice
→ EXEC
→ Pull Request
→ Askora CI / Required
→ Review
→ Merge
→ Release Evidence
→ Product / User / Learning Evidence
→ Retrospective
→ next Opportunity
```

The flow is evidence-driven rather than document-driven: every document exists to make a decision, execution boundary, or result auditable. More documents are not a goal by themselves.

## 2. Authority and artifact roles

### 2.1 Product Opportunity / Bug — why work should exist

GitHub Issues are the intake and prioritization layer.

A **Product Opportunity** records:

- the concrete user problem and scenario;
- observed evidence versus assumptions;
- desired user outcome;
- success evidence;
- confidence and important constraints.

A **Bug / Regression** records:

- current and expected behavior;
- severity based on impact rather than effort;
- deterministic reproduction when available;
- governing contract;
- affected SHA/version and sanitized evidence;
- data, security, privacy, migration, or learning risk.

An Issue is **not** an EXEC. It may exist before the solution is known and may be rejected, deferred, researched, or split.

### 2.2 Product Positioning — what Askora is allowed to become

`docs/product/PRODUCT-POSITIONING.md` remains the highest frozen product baseline.

No Opportunity, ADR, Spec, EXEC, PR, test, or implementation may silently expand beyond Product Positioning. A conflict is a product decision and must be resolved at the Product Positioning layer before downstream implementation proceeds.

### 2.3 Canonical Design / ADR — decisions that change shared semantics

Use Canonical Design and/or an ADR when work introduces or changes a shared decision such as:

- domain ownership or single-writer semantics;
- user-visible information architecture;
- security/privacy boundaries;
- durable persistence/recovery behavior;
- cross-system contracts;
- production runtime architecture;
- a choice whose reversal would materially affect multiple EXECs.

Do not create an ADR merely to document an implementation detail already determined by a frozen Spec.

### 2.4 Spec / Vertical Slice — what must be true

Specs define stable contracts, invariants, state transitions, interfaces, quality constraints, and acceptance semantics.

A Vertical Slice binds those contracts into a deliverable user/system capability. It should be narrow enough that completion can be verified independently.

### 2.5 EXEC — how a frozen slice is executed

EXEC remains the engineering task contract. It must not become a general backlog or product discovery document.

Every new EXEC must retain the existing Askora contract fields:

- Objective;
- Dependencies;
- Required Product Positioning;
- Required Specs;
- Current Reality;
- Allowed Files;
- Forbidden Changes;
- Implementation Tasks;
- Acceptance Criteria;
- Required Tests;
- Completion Report Format.

If implementation exposes an unresolved product or shared semantic choice, report `POSITIONING GAP` or `SPEC GAP` instead of inventing the decision inside the EXEC.

### 2.6 Pull Request — reviewable delivery boundary

Prefer:

```text
one problem / vertical slice / EXEC
→ one independently reviewable PR
```

A PR is the first mandatory peer/automated review boundary, not merely a transport mechanism for code already considered done.

A multi-EXEC **integration/release PR** is acceptable only when:

- its integration role is explicit;
- constituent changes already have independently reviewable evidence;
- the PR does not become the first meaningful review of multiple unrelated task domains;
- cross-domain integration risks and rollback behavior are stated.

## 3. Definition of Ready

An implementation EXEC should not start until all applicable Ready conditions are satisfied.

### Required

- A concrete user problem, product opportunity, or reproducible defect exists.
- Evidence confidence is explicit; assumptions are not presented as validated facts.
- The work has been checked against current Product Positioning and Non-goals.
- The expected user/product outcome is clear enough to judge success.
- Acceptance criteria and important dependencies are known.
- Required shared product/architecture choices are frozen in Design/ADR/Spec.
- The proposed slice is small enough to review and verify independently.

### Not Ready

Work is not Ready when:

- the only rationale is “the implementation would be useful”;
- an EXEC needs to decide Product Positioning, domain ownership, or another unfrozen shared semantic;
- success is defined only as “code merged”;
- a dependency gate is unsatisfied;
- a known P0/P1 correctness or security contradiction is being deferred without an explicit governing decision.

## 4. Pull-request gate

Before merge, every applicable PR must answer four questions.

### Why

- What problem or outcome does this solve?
- Which Issue / Product Gap originated the work?

### What authority

- Which Product Positioning, Design/ADR, Spec, Vertical Slice, and EXEC govern the change?
- Is any authority intentionally being changed? If yes, that change must occur at the correct level first.

### What risk

At minimum consider:

- product and learning semantics;
- owner/data isolation;
- secrets/privacy/security;
- persistence/migrations/recovery/no-resurrection;
- Local Web runtime/network boundaries;
- external provider behavior and failure modes;
- rollback or fail-closed behavior.

### What evidence

Record the candidate SHA and the actual gates run. Do not write only “tests pass”.

## 5. Required CI and merge policy

`Askora CI / Required` is the engineering merge gate. Required checks must not be converted to Optional merely because they fail during a migration.

Target merge order:

```text
Candidate SHA
→ Askora CI / Required GREEN
→ review findings resolved
→ merge
→ main remains GREEN
```

A red Required gate means the candidate is not merge-ready.

Until repository branch protection is technically enforced, maintainers must follow the same policy manually. Once the GitHub ruleset is enabled, the repository configuration becomes the enforcement mechanism rather than relying on convention.

## 6. Review severity and closure

### P0

Release blocker: data loss/corruption, critical security/privacy violation, broken recovery/no-resurrection guarantee, or direct violation of a frozen critical product boundary.

A known P0 must be resolved before merge.

### P1

Major correctness, user-flow, architecture ownership, or security defect that materially invalidates the claimed capability.

A known P1 must be resolved before merge or the claimed capability must be explicitly reduced/reopened so that the PR no longer makes the invalid claim.

### P2 / P3

May be deferred when the remaining behavior still satisfies the frozen acceptance/release contract. Deferred work must have a traceable Issue when it materially affects product quality.

Review threads should be resolved only after the candidate code, scope, or product claim actually addresses the finding.

## 7. Definition of Done

A change is DONE only when all applicable completion conditions hold.

### Engineering

- implementation matches frozen contracts;
- Required tests pass on the candidate SHA;
- `Askora CI / Required` is green;
- review P0/P1 findings are resolved;
- migrations, recovery and security/privacy gates pass when applicable;
- no failing test was deleted, weakened, skipped, or reclassified merely to manufacture green status;
- current documentation is reconciled.

### Delivery evidence

When the work closes an EXEC or release baseline:

- the candidate SHA is recorded;
- Completion / Release Evidence records actual gate results;
- completed EXEC is archived according to the existing immutable-history rule;
- historical evidence is not silently rewritten into current evidence.

### Product evidence

Engineering completion does not prove that the user problem was solved.

Report separately, as applicable:

- Product / Usability Evidence;
- real Local Web / browser / provider evidence;
- task success or qualitative user evidence;
- product behavior metrics.

### Learning evidence

Learning effectiveness is an independent claim. Unless supported by the required real-user/learning experiment evidence, use the existing explicit status:

`LEARNING_EVIDENCE_INSUFFICIENT`

Do not infer learning effectiveness from:

- successful model calls;
- message count or session duration;
- Activity completion alone;
- Engineering PASS;
- policy-contract correctness alone.

## 8. Evidence taxonomy

Use distinct evidence classes so one cannot silently substitute for another.

| Evidence | Answers | Typical sources |
|---|---|---|
| Engineering Evidence | Did the implementation satisfy the technical contract? | Required CI, tests, build, migrations |
| Security / Privacy Evidence | Are ownership, secret, network and recovery boundaries preserved? | security tests, threat-specific checks, sanitized audit |
| Product / Usability Evidence | Can the target user complete the intended task and obtain the expected product outcome? | usability sessions, browser/product checks, task success |
| Learning Evidence | Does the product improve the intended learning outcome? | predefined real-user learning experiments and measures |

A PASS in one row must not automatically promote another row to PASS.

## 9. Product validation loop

After release, the originating Opportunity should be revisited when sufficient evidence exists.

Possible outcomes:

- **Validated** — evidence supports the expected user outcome;
- **Partially validated** — some outcomes improved but meaningful gaps remain;
- **Not validated** — the solution shipped but the expected outcome did not materialize;
- **Insufficient evidence** — more observation is required.

A shipped feature is therefore not the terminal state of product work. Evidence may create a new Opportunity, change priority, or justify removing/reworking a capability.

## 10. Governance exceptions

Exceptions must be explicit and narrow.

Examples:

- emergency recovery fix with a follow-up evidence task;
- solo-maintainer repository temporarily unable to require an independent human approval;
- optional compatibility evidence unavailable because the corresponding platform is outside the v1 Required baseline.

Exceptions must never be used to:

- bypass Product Positioning;
- merge known P0/P1 defects;
- weaken Required CI to hide a regression;
- fabricate product or learning evidence;
- expose private data or secrets for debugging convenience.

## 11. Working rule

The practical operating rule is:

> **Issues explain why work deserves to exist; Product/Design/ADR/Specs decide what must be true; EXEC controls how the frozen slice is implemented; PR/Required CI/review decide whether the candidate may merge; Release/Product/Learning Evidence decide what we are justified in claiming afterward.**
