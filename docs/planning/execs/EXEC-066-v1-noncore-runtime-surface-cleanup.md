# EXEC-066 — v1 Non-core Runtime Surface and Dependency Cleanup

> Status: **FROZEN / BLOCKED_BY_EXEC_062_063_064_065**  
> Linear: XIK-175  
> Priority: P1 Scope Hygiene / Maintenance  
> Frozen: 2026-08-10  
> Governing gaps: GAP-V1-006..008

## 1. Objective

After all P0 product-boundary paths are working, remove or isolate non-v1 runtime surfaces that can resurrect obsolete product assumptions: full OCR/DOCX as core, Account/Auth runtime, and service-era infrastructure dependencies.

This is a proof-driven cleanup task, not a broad rewrite.

## 2. Dependencies

```text
EXEC-060 DONE
EXEC-062 DONE
EXEC-063 DONE
EXEC-064 DONE
EXEC-065 DONE
→ EXEC-066
```

EXEC-061 is transitively required through 062/063/065.

## 3. Required Sources

- `PRODUCT-POSITIONING.md`
- v1 conformance audit
- ADR-0008/0013 supersession notes
- ADR-0015/0016/0017
- `LIB-*`, `WSP-*`, `LSS-*`, `MATLIFE-*`
- Dependency Rules / CI Infrastructure Standard
- current dependency manifests and production route registrations

## 4. Classification Rule

Every cleanup candidate MUST be classified before deletion:

```text
KEEP_CORE
KEEP_OPTIONAL
MOVE_DEV_TEST
QUARANTINE_HISTORICAL
REMOVE
```

Presence alone is not proof that code/dependency is wrong. Determine production reachability, migration need, recovery value and Quality evidence first.

## 5. Implementation Tasks

### 5.1 OCR / DOCX

- remove DOCX/full OCR from the default v1 supported-capability surface;
- isolate historical/optional OCR routes/workers/dependencies or remove them when unreferenced;
- ensure scanner-text failure can return unsupported/partial without requiring OCR engine;
- remove OCR/DOCX from Required release readiness unless a v1 core path genuinely needs them.

### 5.2 Account / Auth residue

- prove registered production-local routes no longer use auth/account/dev-auth;
- classify migration-only persistence/code separately from dead runtime code;
- delete or quarantine unused backend auth/account routes/services and frontend Account/auth/session heartbeat surfaces;
- retire JWT/password dependencies/config when no current migration/runtime path requires them;
- preserve only historical migration evidence needed to read/transform legacy data.

### 5.3 Service-era dependencies

Classify Redis/PostgreSQL/Kafka and related packages:

- keep PostgreSQL only where Optional compatibility/CI evidence has explicit value;
- move non-runtime clients to dev/optional groups when practical;
- remove Redis/Kafka runtime paths that no v1 core feature needs;
- ensure normal install/startup does not provision or probe them;
- add architecture/packaging regression guards.

### 5.4 Documentation

Align README/capability docs so historical implemented features are not presented as current v1 core requirements.

## 6. Allowed Files

- dead/legacy backend/frontend auth/account/OCR/DOCX code
- dependency manifests/lock files
- optional compatibility adapters/workflow config
- runtime route registration
- package/startup architecture tests
- docs describing supported product surface

Do not alter UI Design System/Teaching Policy algorithms.

## 7. Forbidden Changes

Do NOT:

- delete migration/recovery code before proving it is no longer needed;
- delete Optional PostgreSQL evidence solely because SQLite is production baseline;
- expand OCR/DOCX to justify keeping them;
- reintroduce Account/Login for compatibility;
- move a Required product-core test to Optional;
- remove dependencies by breaking current accepted migration/recovery paths;
- mix unrelated refactors.

## 8. Acceptance Criteria

- `EXEC066-AC-001`: default v1 UI/API no longer presents full OCR or DOCX as core capability.
- `EXEC066-AC-002`: OCR engine is not a Required runtime/startup/release dependency.
- `EXEC066-AC-003`: no Account/Login/JWT/AuthSession route is reachable in production-local product flow.
- `EXEC066-AC-004`: unused auth/account frontend/backend surface is removed or explicitly quarantined with retirement reason.
- `EXEC066-AC-005`: JWT/password dependencies/config are absent from core runtime when no migration need remains.
- `EXEC066-AC-006`: Redis/Kafka are not core runtime dependencies; PostgreSQL remains only explicit Optional compatibility where justified.
- `EXEC066-AC-007`: dependency grouping/install path reflects the actual v1 Local Web product.
- `EXEC066-AC-008`: architecture/packaging tests prevent service-era prerequisites from returning.
- `EXEC066-AC-009`: all retained legacy components have an explicit reason and no current product-authority role.
- `EXEC066-AC-010`: Required CI is not weakened.

## 9. Required Verification

- production route reachability tests;
- dependency/import scans;
- clean core install/startup;
- Optional compatibility jobs where retained;
- Local Web upload core-format tests;
- scanned-PDF unsupported/partial behavior;
- no-auth regression;
- Required CI.

Coordinate with Quality XIK-152/XIK-157/XIK-162 rather than duplicating CI governance.

## 10. Completion Report

Provide a candidate-by-candidate classification table, removed/retained dependency list, production reachability evidence, tests/CI and any historical migration code intentionally kept.

Archive only after all ACs pass.