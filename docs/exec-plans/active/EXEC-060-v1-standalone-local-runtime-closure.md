# EXEC-060 — v1 Standalone Local Runtime Closure

> Status: **FROZEN / READY_FOR_EXECUTION**  
> Linear: XIK-167  
> Priority: P0 Product Runtime  
> Frozen: 2026-08-10  
> Governing gap: GAP-V1-003

## 1. Objective

Make Askora's normal v1 Local Web runtime actually use a managed SQLite/local-files baseline with no manual Redis/PostgreSQL/Docker/JWT prerequisite.

This task closes implementation drift only. It MUST NOT weaken `PRODUCT-POSITIONING.md` to match service-era defaults.

## 2. Dependencies

- Product/design dependency: none; current contracts are sufficient.
- Quality tasks may be red while this task starts; do not claim release PASS until current Required CI is green.
- Before coding, fetch current `main` and re-check for concurrent changes from EXEC-054+ / UI work.

## 3. Required Sources

Read before implementation:

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/design/v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md`
- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/platform/identity-privacy-lifecycle.md`
- `docs/specs/quality/ci-infrastructure-standard.md`
- `docs/specs/quality/v1-local-web-quality-reconciliation.md`

## 4. Current Reality to Verify

Audit baseline found:

- default `DATABASE_URL` points to PostgreSQL;
- Redis is initialized during application startup;
- some startup paths treat Redis failure as fatal;
- production configuration still carries JWT-secret assumptions despite no-auth v1;
- `.env.example` / setup guidance remains service-era oriented;
- SQLite support exists but is not the unambiguous normal product path.

If current main already fixed any item, preserve the correct implementation and only close remaining gaps.

## 5. Allowed Files

Primarily:

- `apps/backend/app/core/config.py`
- `apps/backend/app/core/database.py`
- `apps/backend/app/main.py`
- local runtime/cache/job adapters directly required by this change
- `.env.example`
- root/backend README runtime instructions
- focused startup/config/SQLite tests
- migration/readiness tests

May modify lock/config files only when required by the frozen runtime contract.

## 6. Forbidden Changes

Do NOT:

- remove PostgreSQL optional CI compatibility merely to make tests pass;
- make Redis a required local service under a new name;
- reintroduce authentication/JWT as a runtime prerequisite;
- modify Teaching Policy/SYS01～SYS08 domain semantics;
- mix Workspace/BYOK/Trash implementation into this EXEC;
- weaken Required tests or move a product-core oracle to Optional;
- require Docker for normal end-user startup.

## 7. Implementation Tasks

1. Define a production-local/default configuration path whose database resolves to an Askora-managed SQLite file.
2. Ensure managed data directories are created safely with platform-appropriate permissions and deterministic paths.
3. Remove Redis from core startup/readiness/correctness requirements.
4. For any remaining cache/coordination use, provide in-process/local behavior consistent with current persistence contracts; Redis may remain dev/optional only.
5. Remove JWT/password secret validation from production-local startup.
6. Ensure no registered v1 route depends on AuthSession/JWT initialization.
7. Align `/ready`/health diagnostics with actual required vs optional dependencies.
8. Align `.env.example` and README so the documented default does not steer users to Postgres/Redis/Docker/JWT.
9. Keep PostgreSQL/Redis compatibility explicitly optional and non-authoritative.
10. Add regression tests that start the backend in a clean production-local-like environment with no external infra.
11. Preserve schema compatibility/recovery gates; do not auto-repair destructive migration mismatch.

## 8. Acceptance Criteria

- `EXEC060-AC-001`: clean normal local startup resolves to SQLite without external DB configuration.
- `EXEC060-AC-002`: no Redis listener/service is required for startup, `/ready`, document ingestion, learning loop correctness or local durable jobs.
- `EXEC060-AC-003`: no JWT/password secret is required in production-local mode.
- `EXEC060-AC-004`: browser → loopback backend works with only Askora-managed local data files plus configured external AI when needed.
- `EXEC060-AC-005`: Redis/PostgreSQL/Docker remain optional compatibility/dev evidence only.
- `EXEC060-AC-006`: migration mismatch still fails safely and does not silently destructively repair data.
- `EXEC060-AC-007`: `.env.example` and README match executable defaults.
- `EXEC060-AC-008`: existing Teaching Policy/ownership behavior is unchanged.
- `EXEC060-AC-009`: targeted local runtime/config/SQLite tests pass.
- `EXEC060-AC-010`: no Required oracle is weakened to manufacture a green result.

## 9. Required Verification

At minimum run:

- focused config unit tests;
- clean temporary SQLite startup/readiness integration;
- SQLite migration roundtrip/representative fixture;
- document durable-job restart path relevant to Redis removal;
- core adaptive/book-learning smoke affected by startup dependencies;
- Ruff/Black/Mypy for changed Python;
- Required CI if feasible on the exact candidate commit.

Record Optional PostgreSQL/Redis compatibility separately; its failure does not redefine production-local correctness but must be reported.

## 10. Completion Report

Report:

- exact baseline and final commit;
- files changed;
- old vs new default runtime resolution;
- any Redis/PostgreSQL compatibility retained and why;
- tests/CI exact results;
- unresolved issues;
- explicit statement: `PRODUCT_POSITIONING_CONFORMANCE` remains FAIL until EXEC-067 acceptance.

Only archive EXEC-060 after all ACs are evidenced.