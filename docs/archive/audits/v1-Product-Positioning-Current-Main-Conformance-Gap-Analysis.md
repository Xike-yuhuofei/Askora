# Askora v1 Product Positioning — Current Main Conformance Gap Analysis

> Status: **FROZEN CURRENT-MAIN CONFORMANCE SNAPSHOT**  
> Audit date: 2026-08-10  
> Audited `main`: `da2942e1be69c817d4e2ba36663ef802a61762b1`  
> Governing source: `docs/product/PRODUCT-POSITIONING.md`  
> Supporting contracts: current `docs/specs/**`  
> Purpose: identify implementation drift against the frozen v1 product boundary. This document is **not** a new Canonical Design, ADR, Spec, or implementation contract.

---

## 1. Executive Verdict

Current `main` has made material progress toward the frozen product positioning, especially around Local Web, LocalOwner/no-auth, loopback-only access, durable local document jobs, managed source copies, and the v0.3 Teaching Policy closure.

However, **Askora v1 Product Positioning Conformance is NOT PASS**.

The remaining blocking gaps are structural rather than cosmetic:

```text
Product Positioning Conformance: FAIL

Local Web / no-auth boundary:          PASS / substantial implementation present
LocalOwner foundation:                 PASS / compatibility residue remains
Workspace / LearningProject boundary:  FAIL
Workspace-scoped Retrieval:            FAIL
Standalone local runtime defaults:     FAIL
Local Web BYOK configuration:          FAIL
Trash / Restore lifecycle:             FAIL
v1 import/OCR surface:                  PARTIAL / scope leakage remains
Required CI:                            FAIL at audited HEAD
Learning Evidence Gate:                LEARNING_EVIDENCE_INSUFFICIENT
```

No evidence in this audit requires redesigning the frozen v0.3 Teaching Policy ontology or SYS01～SYS08 learning-core ownership.

---

## 2. Source-of-Truth Boundary

This audit applies the current governance order:

```text
PRODUCT-POSITIONING
→ Canonical Design
→ Accepted / non-superseded ADR
→ Canonical Specs
→ EXEC
→ Code / Tests
```

When current code conflicts with Product Positioning or current Specs, the code is treated as implementation drift. Historical release reports, completed EXEC files, PR descriptions, or already-implemented legacy features do not override the frozen product boundary.

---

## 3. Confirmed Conformant Areas

### 3.1 Local Web / loopback-only product shape

Current backend runtime enforces a loopback host boundary in non-development mode and rejects non-loopback browser origins/referers. Auth/account routers are not registered in the current production application entry.

Current frontend is a browser/Vite application and the active product routing is browser-based. Historical Account pages may remain as dead code, but they do not define the registered product route.

**Verdict: CONFORMANT BASELINE.**

### 3.2 LocalOwner foundation

`LocalOwnerRecord` exists and current API adapters resolve an `OwnerProjection` rather than requiring a login flow. Legacy `User`/auth persistence remains as migration/compatibility residue, but registered product flow is no-auth.

**Verdict: CONFORMANT FOUNDATION / CLEANUP REMAINS.**

### 3.3 Managed source copy

Document import receives file bytes and writes them through `LocalFileStorage.save_file(...)`, then stores the resulting managed storage reference. The product therefore does not depend solely on the original user-selected file path remaining available.

**Verdict: CONFORMANT.**

### 3.4 Durable local document jobs

Document ingestion creates durable outbox tasks with typed task/schema/idempotency metadata, and the application starts a document-processing runtime that reconciles persisted work.

**Verdict: CONFORMANT DIRECTION.**

### 3.5 SQLite capability exists

The database adapter supports SQLite, enables foreign keys, applies local file permissions, and can create local tables in local/development/test modes.

The gap is not “SQLite unsupported”; the gap is that **the default/production-local configuration is still PostgreSQL/Redis-oriented**.

### 3.6 v0.3 Teaching Policy is not the v1 positioning blocker

The production sequential policy closure was merged before this snapshot. Nothing in the Product Positioning audit requires replacing the six Strategy Families, deterministic B3 policy, anti-oscillation semantics, DecisionTrace, Assessment/Learner Evidence ownership, or SYS01～SYS08 boundaries.

---

## 4. Blocking Product-Positioning Gaps

## GAP-V1-001 — Workspace / LearningProject durable aggregates are not implemented

**Severity:** P0 / Product Architecture Blocker  
**Classification:** DESIGN–IMPLEMENTATION GAP

### Required product semantics

The frozen product model requires:

```text
LocalOwner
└── Workspace
    ├── Material
    ├── LearningProject
    │   └── ProjectMaterial N:M Material
    ├── LearningGoal
    └── LearningSession
```

Workspace is the high-level isolation boundary; it is not a Tenant/Organization alias. Material, LearningProject, LearningGoal and LearningSession must be attributable to Workspace according to the current Product/Spec contracts.

### Current implementation evidence

- no current `Workspace` durable model is registered in `apps/backend/app/models/__init__.py`;
- no `LearningProject` / `ProjectMaterial` durable model is present in the current model registry;
- repository code search at the audited snapshot contains no `workspace_id` implementation field;
- `UserDocument` is scoped only by `pseudonym_id`;
- `LearningGoalRecord` is scoped by `user_id`, not Workspace;
- `/api/v1/workspace/*` is a UI/read-model aggregation route, not a Product Positioning Workspace aggregate.

### Impact

Without a real Workspace boundary, Askora cannot correctly implement:

- multiple independent learning spaces;
- Project N:M Material semantics;
- Workspace-local tags/collections;
- Workspace-scoped goals/sessions/configuration;
- safe cross-workspace isolation;
- correct delete/move/reference impact analysis.

### Required closure

Before broad implementation, freeze an implementation-ready Workspace/Project contract covering at least:

- Workspace lifecycle and default bootstrap;
- LearningProject lifecycle;
- ProjectMaterial membership;
- workspace ownership refs on Material/Goal/Session and required projections;
- migration of existing LocalOwner-global records into a deterministic default Workspace;
- same-workspace invariants and cross-workspace rejection;
- API/query boundary and idempotency;
- deletion/reference behavior;
- migration/recovery/rebuild verification.

**Implementation readiness:** `SPEC DELTA REQUIRED` before mechanical Codex implementation.

---

## GAP-V1-002 — Retrieval is still owner-global instead of Workspace-scoped

**Severity:** P0 / Data Isolation & Knowledge Supply Blocker  
**Depends on:** GAP-V1-001

### Required semantics

Every production retrieval must carry an explicit scope, with at least:

```yaml
workspace_id: required
project_ids: optional
material_ids: optional
knowledge_unit_ids: optional
session_context: optional
```

Default unbounded retrieval over all Askora data is forbidden.

### Current implementation evidence

The registered `/api/v1/documents/rag/query` request accepts only:

- query;
- max_chunks;
- subject.

It then calls retrieval using `pseudonym_id` as the ownership scope. No `workspace_id`, Project scope, Material scope, or typed RetrievalScope is supplied.

Current `UserDocument`/Library projections are also LocalOwner-global because Workspace persistence is absent.

### Impact

A future multi-Workspace user can receive evidence from the wrong learning space. The current behavior also contradicts the explicit “no Global Material Library” boundary.

### Required closure

After Workspace persistence exists:

1. introduce the canonical typed RetrievalScope at production application/SYS02 boundaries;
2. require `workspace_id` for ordinary retrieval;
3. constrain optional Project/Material/KU scopes to the same Workspace;
4. include Workspace and subordinate scope in cache/index keys;
5. reject cross-workspace refs without existence leakage;
6. migrate legacy owner-global RAG endpoints to bounded compatibility or retire them;
7. add isolation, cache, citation and E2E tests.

**Implementation readiness:** Workspace contract first; then existing SYS02 Spec is sufficiently directional, but an API/application contract delta may be needed for exact public payloads.

---

## GAP-V1-003 — Standalone local runtime is not the actual default runtime

**Severity:** P0 / Product Runtime Blocker  
**Classification:** IMPLEMENTATION GAP

### Required semantics

Final-user v1 startup must not require manual Docker, PostgreSQL, Redis, Kafka, or other independently operated infrastructure. SQLite/local files/in-process or local durable jobs are the production-local baseline.

### Current implementation evidence

`apps/backend/app/core/config.py` currently defaults to:

```text
APP_ENV = development
DATABASE_URL = postgresql+asyncpg://...
REDIS_URL = redis://localhost:6379/0
```

`apps/backend/app/main.py` always attempts Redis initialization. Redis failure is tolerated only when `auto_create_tables` is true; in non-auto-create environments the startup raises.

Production configuration validation still requires a JWT secret even though the current product explicitly has no authentication.

`.env.example` is Docker/PostgreSQL/JWT-oriented and does not establish a standalone `APP_ENV=local + SQLite` default path.

The root README therefore describes a Local SQLite path that is technically supported but is not the actual default configuration produced by the documented setup.

### Impact

A user following the repository default path still encounters service-era infrastructure assumptions, violating the “open/use Askora without operating infrastructure” product contract.

### Required closure

- make production-local/normal local execution default to a managed SQLite path;
- separate dev/compatibility PostgreSQL configuration from final-user defaults;
- remove Redis from correctness/readiness/startup requirements for production-local;
- replace Redis-only coordination/cache dependencies with in-process or SQLite-backed behavior where correctness requires durability;
- remove JWT requirements from production-local configuration;
- align `.env.example`, startup command, readiness, migration and README;
- classify PostgreSQL/Redis/Docker compatibility as Optional/Scheduled evidence rather than Required release runtime.

**Implementation readiness:** current Product/Architecture/Persistence/CI contracts are sufficient. This should be implemented as a focused EXEC, not a new product decision.

---

## GAP-V1-004 — Local Web BYOK configuration path is missing

**Severity:** P0 / Core Product Capability Blocker  
**Classification:** IMPLEMENTATION GAP with security-sensitive adapter decision

### Required semantics

The user must be able to configure Provider, Model, Embedding Model and permitted task routes from the Local Web Settings UI. Secret material must remain local and must not be stored in browser persistence, ordinary SQLite payloads, logs, default backup/export, or an Askora cloud service.

### Current implementation evidence

- current Settings UI only reads a model-ready status;
- no active Provider/Model/API-Key configuration form exists in `Settings.jsx`;
- no frontend model-configuration API module is present;
- no registered backend model-settings router exists in `app.main`;
- `/health/config` reads provider/model readiness directly from environment-backed settings;
- the former Electron/safeStorage implementation has been removed from the active Local Web product path.

### Impact

The principal AI-dependent product path still requires developer/environment configuration rather than the frozen BYOK user experience.

### Required closure

Use the current `MODEL-CONFIG-*` contract:

```text
Browser Settings
→ loopback model-config API
→ Model Configuration Application Service
├── SYS08 ModelRouteProfileV1
└── LocalSecretStore
```

Implementation must provide:

- non-sensitive versioned profile persistence;
- LocalSecretStore port;
- production secure-storage adapter;
- probe-before-activation;
- atomic/recoverable profile-secret activation;
- clear/disable semantics;
- runtime refresh without Electron;
- no Key readback;
- secret leakage tests;
- browser E2E.

The exact cross-platform production `LocalSecretStore` adapter is security-sensitive. If the current Spec does not uniquely select an acceptable implementation, freeze a narrow ADR/Spec delta before Codex chooses a library or OS mechanism.

---

## GAP-V1-005 — Normal document delete physically removes the managed source file

**Severity:** P0 / Data Safety Blocker  
**Classification:** SPEC–IMPLEMENTATION GAP

### Required semantics

```text
active
→ trash
→ permanent delete
```

Trash retains durable Material/SourceFile and supports restore. Physical removal belongs only to Permanent Delete / governed cleanup.

### Current implementation evidence

`DocumentService.delete_document(...)` currently:

1. sets `is_deleted = True`;
2. sets `deleted_at`;
3. changes `processing_status = FAILED`;
4. commits;
5. immediately calls `self.storage.delete_file(document.storage_path)`.

The API exposes this as ordinary `DELETE /documents/{document_id}`.

### Impact

This is not a recoverable Trash lifecycle: the durable managed source is destroyed immediately. It also overloads `FAILED` processing status with deletion semantics.

### Required closure

- introduce explicit Material lifecycle `active|trash|deleted` or equivalent current Spec representation;
- ordinary delete moves to Trash without deleting SourceFile;
- add restore command;
- exclude Trash from ordinary search/retrieval/new learning;
- Permanent Delete requires explicit confirmation or configured cleanup policy;
- permanent deletion invalidates derived projections and obeys no-resurrection/recovery rules;
- reference preview must expose Project memberships before material deletion;
- migrate legacy `is_deleted` records safely.

**Implementation readiness:** lifecycle semantics are already frozen in Product Positioning and `LIB-045/046`; exact migration/API details may be frozen in a focused Spec/EXEC without a new product decision.

---

## 5. Non-blocking but Required Scope/Technical-Debt Closure

## GAP-V1-006 — OCR and DOCX remain exposed as active product capabilities

**Severity:** P1 / Scope Hygiene

Current registered upload API documents `.docx` as supported and exposes full OCR request/read/review endpoints. `python-docx` remains a normal backend dependency and OCR service/models remain active.

The frozen product boundary says:

- v1 core formats: EPUB, text PDF, Markdown, TXT;
- DOCX is not v1 core;
- full OCR pipeline is not v1 core.

Historical implementation MAY remain only if isolated as optional/legacy and does not become a Required runtime/release dependency.

Required closure: remove these capabilities from the default v1 product surface or explicitly isolate them behind optional/experimental capability boundaries. Do not spend v1 scope expanding OCR/DOCX.

---

## GAP-V1-007 — Auth/Account implementation residue remains in the source tree

**Severity:** P1 / Architecture Cleanup

The active runtime no longer registers Auth/Account routes, which is correct. However current source still contains:

- backend `api/v1/auth.py`, `account.py`, `dev_auth.py`;
- auth/account persistence models and services;
- frontend `Account*` pages;
- frontend `api/auth.js`, `api/account.js`, `sessionHeartbeat.js`;
- JWT/password dependencies and configuration.

These do not currently redefine the product boundary, but they increase the probability of accidental resurrection and keep dependency/configuration complexity alive.

Required closure: determine migration-only code that must remain temporarily, then delete or quarantine all unused account/auth runtime surface once data migration compatibility no longer needs it. No new account feature work is authorized.

---

## GAP-V1-008 — Primary dependency set still carries service-era infrastructure

**Severity:** P1 / Packaging & Maintenance

Normal backend dependencies still include PostgreSQL driver, Redis client, Kafka client, JWT/password packages and DOCX parser. Presence alone is not a product violation, but primary dependency classification should converge to the actual Local Web runtime.

Required closure:

- keep only dependencies required by normal v1 runtime in the core dependency set;
- move genuine CI/compatibility/historical dependencies to optional/dev groups where practical;
- do not remove a dependency merely because its name appears legacy—first prove production reachability and migration requirements;
- add architecture/packaging tests that prevent service-era dependencies from becoming final-user startup prerequisites.

---

## 6. Required CI State at Audit Snapshot

At audited HEAD `da2942e1...`:

```text
Askora CI / Required: FAIL
Askora CI / Optional: FAIL
```

Required jobs observed:

- Frontend test & build: PASS
- Migration validation: PASS
- Dependency audit: PASS
- Code quality: FAIL
- Backend tests: FAIL
- Documentation links: FAIL

Documentation failure is primarily stale EXEC links/inventory after EXEC-048～053 were archived plus newly added governance/UI docs not registered in the inventory.

This audit does **not** treat Optional PostgreSQL/desktop/provider failures as v1 product blockers by themselves. Required CI must return green before a Product Positioning implementation closure can be accepted.

---

## 7. Closure Sequence

Do not fix the gaps as one giant implementation task.

Recommended dependency order:

```text
A. Governance / audit freeze
   ↓
B. Standalone Local Runtime Closure          [GAP-V1-003]
   ↓
C. Workspace + LearningProject Contract Freeze
   ↓
D. Workspace / Project Persistence & Migration [GAP-V1-001]
   ↓
E. Workspace-scoped Material + Retrieval       [GAP-V1-002]

In parallel after governance:
F. Local Web BYOK / LocalSecretStore          [GAP-V1-004]
G. Trash / Restore / Permanent Delete         [GAP-V1-005]

After P0 closures:
H. Scope / Legacy / Dependency Cleanup        [GAP-V1-006..008]
   ↓
I. Required CI + Product Boundary E2E Release Gate
```

### Why Workspace must precede Retrieval cutover

A `workspace_id` parameter added to an API without a durable Workspace aggregate would be cosmetic scoping. The scope must be backed by actual durable ownership/membership and migration invariants.

### Why BYOK can proceed separately

BYOK is Application/SYS08/LocalSecretStore work and does not require Workspace persistence unless Workspace-level model overrides are included in the first implementation. v1 may first close Application-level configuration and add explicitly allowed Workspace/Project override semantics later under the already-frozen configuration hierarchy.

---

## 8. Linear Project Placement

These gaps MUST NOT be mixed into `Askora — UI Redesign`.

- CI/test-only fixes belong to `Askora — Quality`.
- Product runtime/data/domain closure should live in a separate Askora Initiative project, recommended name: **Askora — v1 Product Architecture**.
- UI changes needed only to expose already-frozen Workspace/BYOK/Trash semantics may have linked implementation issues in UI Redesign, but the domain truth and product acceptance remain owned by the v1 Product Architecture project.

---

## 9. Acceptance Gate for v1 Product Positioning Closure

A future closure may claim `PRODUCT_POSITIONING_CONFORMANCE = PASS` only when all of the following are true:

1. Local Web production-local startup works with managed SQLite/local files and no Redis/PostgreSQL/Docker manual prerequisite.
2. no Account/Login/JWT authentication is required by production-local runtime.
3. a durable default Workspace exists and existing data migrates into it deterministically.
4. LearningProject and ProjectMaterial N:M semantics exist and preserve Material ownership.
5. Material, Goal and LearningSession are Workspace-attributable according to frozen contracts.
6. ordinary retrieval is explicit Workspace-scoped and cross-workspace isolation tests pass.
7. Local Web Settings can configure BYOK provider/model/embedding routes without Electron or secret leakage.
8. normal Material delete enters recoverable Trash; physical SourceFile deletion only occurs through Permanent Delete/cleanup governance.
9. OCR/DOCX/auth/service-era capabilities are outside the default v1 product surface unless explicitly optional and non-blocking.
10. Required CI is green on the exact accepted commit.
11. no closure changes the frozen v0.3 Teaching Policy semantics without a separately authorized Design/ADR/Spec change.
12. Learning Evidence remains reported separately; engineering/product conformance must not be described as proven learning efficacy.

---

## 10. Freeze Result

**Current Main Product Positioning Conformance: FAIL.**

This is an implementation/governance gap set, not evidence that `PRODUCT-POSITIONING.md` should be weakened to match the existing code.

The next correct phase is:

```text
freeze this audit
→ establish non-UI Linear project control plane
→ close P0 gaps in dependency order
→ Codex executes frozen Specs/EXECs
→ ChatGPT independently verifies current main + Required CI
→ only then mark Product Positioning Conformance PASS
```
