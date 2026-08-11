# EXEC-067 — v1 Product Positioning Conformance Release Gate

> Status: **FROZEN / BLOCKED_BY_PRODUCT_AND_QUALITY_GATES**  
> Linear: XIK-176  
> Priority: P0 Final Acceptance  
> Frozen: 2026-08-10

## 1. Objective

Independently verify exact current `main` against `docs/product/PRODUCT-POSITIONING.md` and current Canonical Specs. Only if all product/runtime/data/security boundaries and Required Quality evidence pass may the project change:

```text
PRODUCT_POSITIONING_CONFORMANCE = FAIL
→ PASS
```

This EXEC is acceptance, not implementation scope expansion.

## 2. Dependencies

Product dependencies:

```text
EXEC-060 DONE
EXEC-062 DONE
EXEC-063 DONE
EXEC-064 DONE
EXEC-065 DONE
EXEC-066 DONE
```

EXEC-061 is transitively required.

Quality dependencies must have current evidence for the accepted commit, including relevant outcomes from XIK-154, XIK-155, XIK-156, XIK-157, XIK-160, XIK-161 and XIK-162 / corresponding current EXECs.

Do not trust prior historical PASS or Codex completion reports as substitutes for current verification.

## 3. Required Sources

- exact current `main`
- `PRODUCT-POSITIONING.md`
- current Canonical Design/ADR/Specs
- v1 conformance gap analysis
- completed EXEC-060..066 completion reports
- Required/Optional GitHub Actions for exact candidate commit
- current Linear project/issue state

## 4. Verification Matrix

### 4.1 Runtime

Verify clean normal Local Web startup:

```text
Browser → loopback Local Server
SQLite + managed local files + local jobs
```

No manual Docker/Redis/PostgreSQL/JWT prerequisite.

### 4.2 Identity / Workspace

Verify:

- one LocalOwner, no account/login authentication;
- multiple durable Workspaces supported;
- deterministic default Workspace migration;
- LearningProject N:M Material;
- LearningSession narrow scope aggregate;
- no cross-workspace state mixing.

### 4.3 Material / Retrieval

Verify:

- managed SourceFile copy;
- explicit Workspace retrieval;
- Project/Material/KU/session narrowing;
- no Global Material Library;
- citations remain SourceSpan-grounded;
- Trash/Restore/Permanent Delete/no-resurrection.

### 4.4 Learner state

Verify LearnerEvidence/MasteryEstimate/LearnerState/Review are Workspace-specific without changing mastery/Teaching Policy semantics.

### 4.5 BYOK

Verify Local Web Settings can securely configure provider/model/embedding/task routes through approved OS-backed LocalSecretStore; no Electron prerequisite or secret leakage.

### 4.6 Scope hygiene

Verify OCR/DOCX/Auth/service-era components are removed or explicitly optional/historical and cannot become normal runtime prerequisites.

### 4.7 Quality

Verify exact accepted commit has all Required jobs green. Optional compatibility failures, if any, must be accurately classified and must not hide a Required product defect.

## 5. Forbidden Acceptance Shortcuts

Do NOT mark PASS because:

- a prior release was green;
- a PR description says DONE;
- targeted tests pass while Required CI is red;
- UI hides a still-global backend path;
- SQLite support exists but default still requires service infrastructure;
- key storage works only through Electron/dev env;
- ordinary delete merely sets a flag while source deletion is still immediate;
- Workspace exists but retrieval/mastery remain owner-global;
- OCR/Auth legacy code merely exists—judge reachability and runtime role, not filenames alone;
- learning interaction feels better.

## 6. Acceptance Criteria

All are mandatory:

- `EXEC067-AC-001`: normal v1 startup requires no Docker/Redis/PostgreSQL/JWT auth secret.
- `EXEC067-AC-002`: durable Workspace/Project/ProjectMaterial/Session implementation matches WSP contracts.
- `EXEC067-AC-003`: legacy data migration to default Workspace is deterministic/idempotent and verified.
- `EXEC067-AC-004`: learner evidence/mastery/state/review cannot cross Workspace.
- `EXEC067-AC-005`: production retrieval is explicit Workspace-scoped with isolation/cache tests.
- `EXEC067-AC-006`: Local Web BYOK works through LSS/MODEL-CONFIG without secret leakage or Electron dependency.
- `EXEC067-AC-007`: ordinary Material delete is recoverable Trash; physical source deletion only via governed Permanent Delete.
- `EXEC067-AC-008`: old backups/projections cannot resurrect permanently deleted Material.
- `EXEC067-AC-009`: core import/support surface matches v1 positioning; OCR/DOCX are not core prerequisites.
- `EXEC067-AC-010`: Account/Login/AuthSession and service-era infra cannot re-enter normal production-local flow.
- `EXEC067-AC-011`: v0.3 Teaching Policy/SYS01～SYS08 ownership remains conformant.
- `EXEC067-AC-012`: all Required CI jobs green on exact accepted commit.
- `EXEC067-AC-013`: release smoke/regression evidence covers browser, SQLite, migration, Workspace isolation, BYOK and Material lifecycle.
- `EXEC067-AC-014`: no unresolved P0 Product Positioning gap remains.
- `EXEC067-AC-015`: Learning Evidence is still reported separately; absent real-user evidence, retain `LEARNING_EVIDENCE_INSUFFICIENT`.

## 7. Required Deliverable

Update/supersede the frozen current-main conformance audit with an exact commit-bound acceptance report that includes:

- accepted commit SHA;
- product constraint → implementation/test evidence matrix;
- Required CI run/job evidence;
- Optional compatibility status separately;
- remaining P1/non-blocking debt if any;
- explicit final values for Product Positioning Conformance, Engineering Gate, Policy/Contract Correctness and Learning Evidence Gate.

GitHub is the durable acceptance record; Linear status follows that evidence, not vice versa.

## 8. Completion Rule

Only archive EXEC-067 and close XIK-176 when every AC is evidenced on the same accepted current-main commit. Otherwise keep conformance FAIL and create/return only the specific proven gap; do not broaden the task.