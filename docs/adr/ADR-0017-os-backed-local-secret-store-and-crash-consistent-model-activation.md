# ADR-0017 — OS-backed LocalSecretStore and Crash-consistent Model Activation

Status: accepted  
Date: 2026-08-10  
Decision authority: user-directed ChatGPT architecture closure  
Authorized objective: XIK-169 / close the security-sensitive design gap in `GAP-V1-004`  
Affected specs: `MODEL-CONFIG-*`, `PERSIST-*`, `SEC-*`, `ERROR-*`, LocalSecretStore platform contract

## Context

Askora v1 is a Local Web application. The browser must be able to submit a BYOK API key to the loopback Local Server, but the key must not be persisted in browser storage, ordinary SQLite payloads, logs, default backup/export, or an Askora cloud service.

The historical Electron `safeStorage` implementation is not available in the v1 product shape. The current `MODEL-CONFIG-*` contract intentionally leaves the concrete `LocalSecretStore` adapter open. This is security-sensitive and must not be chosen ad hoc by an implementation agent.

A second problem is transactional: the canonical non-secret `ModelRouteProfileV1` is persisted in SQLite while the credential is stored in an OS credential service. Those two stores cannot participate in one atomic database transaction. A crash between secret storage, profile activation and runtime refresh can otherwise create an orphan secret or profile/runtime split-brain.

## Decision

### 1. Production LocalSecretStore uses OS credential services through `keyring`

Askora v1 uses a pinned Python `keyring` dependency as the narrow cross-platform adapter to the operating-system credential service.

Only these production backends are allowed:

```text
macOS   → keyring.backends.macOS.Keyring
Windows → keyring.backends.Windows.WinVaultKeyring
```

Askora MUST instantiate/select the expected backend explicitly and verify its exact backend type before any persistent secret write/read/delete.

Automatic backend discovery is not trusted as a production security decision.

### 2. Production backend allowlist is fail-closed

Production Local MUST reject:

- Null keyring;
- third-party keyring backends;
- plaintext/file keyrings;
- environment/config overrides that resolve to an unapproved backend;
- unsupported operating systems for this v1 contract;
- backend initialization or secure-store access failures.

There is no plaintext persistent fallback.

Development/tests MAY inject a dedicated in-memory fake `LocalSecretStore` through the application port, but that adapter MUST be marked non-production and MUST NOT satisfy production secure-storage readiness.

### 3. Windows credentials are machine-local, not enterprise-roaming

The Windows adapter MUST set `WinVaultKeyring.persist` to `CRED_PERSIST_LOCAL_MACHINE` (or the exact library-equivalent property) rather than rely on the backend's default enterprise persistence.

This keeps Askora's credential within subsequent logon sessions for the same user on the same computer and avoids Askora intentionally selecting a roaming credential persistence mode.

### 4. Secret identity is opaque and independent of provider/model metadata

Use a stable Askora service namespace and a random opaque secret reference:

```text
service_name = "askora.local-model-secret.v1"
account/username = <secret_ref UUID>
value = <API key secret>
```

`secret_ref` is non-secret but MUST remain an internal backend reference. It MUST NOT be returned in ordinary browser profile summaries, logs, diagnostics or exports.

Provider/model names are stored in `ModelRouteProfileV1`, not encoded as the credential identity. This avoids secret-store naming becoming a second routing truth.

### 5. LocalSecretStore port is deliberately small

Production application code may depend only on an abstraction equivalent to:

```text
capability() -> AVAILABLE | LOCKED | UNAVAILABLE | UNSUPPORTED
put(secret_ref, secret)
get(secret_ref) -> secret | missing/error
delete(secret_ref)
```

The browser/public API never gets `get()` and cannot enumerate stored secrets.

No domain/SYS01～SYS07 code may access this port directly. SYS08 model-configuration/runtime application code is the only business consumer.

### 6. Profile supports opaque credential bindings without exposing secrets

`ModelRouteProfileV1` remains the SYS08 routing truth and MAY internally bind one or more provider credential slots to opaque `secret_ref` values.

Public summaries expose only configured/verified status, provider/model/task routes and stable reason codes. They do not expose `secret_ref`, a key fragment or key fingerprint.

For a route edit that keeps the same provider, the application MAY reuse the current stored credential internally without exposing it to the browser. Changing to a provider for which no approved credential binding exists requires a replacement credential.

### 7. Activation uses a durable non-secret operation journal

Because SQLite and the OS credential store cannot commit atomically, every apply/clear operation MUST have a durable SQLite activation journal containing only non-sensitive references and state.

Minimum operation state:

```yaml
model_config_operation:
  operation_id: uuid
  operation_type: APPLY|CLEAR
  expected_profile_revision: integer|null
  prior_profile_ref: versioned_ref|null
  candidate_profile_fingerprint: string|null
  candidate_secret_refs: [uuid]
  phase: PREPARED|PROBE_VERIFIED|SECRET_STORED|PROFILE_COMMITTED|RUNTIME_VERIFIED|COMPLETED|ROLLING_BACK|FAILED
  idempotency_key: string
  error_code: string|null
  created_at: datetime
  updated_at: datetime
```

The journal MUST NOT store API keys, Authorization headers or provider raw bodies.

### 8. Canonical apply sequence

Apply is:

```text
validate schema / expected revision / idempotency
→ write PREPARED non-secret operation journal
→ probe candidate with key held only in process memory
→ mark PROBE_VERIFIED
→ write new/replacement secret(s) to approved LocalSecretStore
→ mark SECRET_STORED
→ atomically publish/switch exact ModelRouteProfile revision in SQLite
→ mark PROFILE_COMMITTED in the same SQLite commit boundary where practical
→ refresh runtime from exact active profile + secret binding
→ verify runtime revision/readiness
→ mark RUNTIME_VERIFIED / COMPLETED
→ retire superseded secret(s) only after successful completion
```

Probe failure MUST NOT persist a new secret or switch the active profile.

### 9. Crash recovery is phase-driven

On Local Server startup, incomplete model-config operations MUST be reconciled before the configuration is reported ready.

Required behavior:

- `PREPARED` / `PROBE_VERIFIED`: no active change; mark/reconcile failed/interrupted safely.
- `SECRET_STORED` with no profile commit: delete orphan candidate secrets when ownership is provable; preserve prior profile/secret.
- `PROFILE_COMMITTED` but runtime not verified: reload exact active profile and secret; verify runtime. If verification fails, restore the exact prior active profile when reconstructible and retire candidate secrets only after rollback is durable.
- if neither candidate nor prior state can be safely established, enter `DEGRADED`/recovery state; never guess or silently fall back to environment secrets.
- cleanup failure for an unreferenced secret is a recovery issue, not permission to activate it.

### 10. Clear commits disabled routing before secret deletion

Clear/disable sequence is:

```text
validate expected revision / confirmation / idempotency
→ PREPARED journal
→ atomically publish DISABLED/UNCONFIGURED profile revision
→ stop/refresh runtime so the old credential is no longer routable
→ delete retired secret refs
→ verify disabled runtime state
→ COMPLETED
```

If credential deletion fails after the disabled profile is committed, the secret is an orphaned local secret requiring cleanup, but it MUST NOT become active again. Secret existence never determines routing state.

### 11. Environment configuration is development compatibility only

Production Local MUST ignore `PYTHON_KEYRING_BACKEND`, keyring user configuration, and equivalent backend-selection overrides as authority for choosing an insecure production backend. Askora explicitly selects and verifies its approved OS backend.

Development/testing environment provider keys MAY remain compatibility input only under the existing `MODEL-CONFIG-*` source rules. A persisted ACTIVE/DISABLED user profile has precedence; `.env` MUST NOT resurrect a cleared production configuration.

### 12. Backup / restore does not copy credentials

Default Askora backup/export MUST NOT include the API key or a recoverable secret blob.

A restored profile whose referenced OS credential is unavailable becomes `DEGRADED` / `SECRET_MISSING` (or equivalent stable reason) and requires the user to re-enter the credential. It MUST NOT fall back to a development environment key.

### 13. Threat boundary is explicit

This design protects API keys from ordinary Askora database/files, browser persistence, logs, diagnostics, exports/backups and accidental application disclosure by delegating at-rest secret storage to the OS credential service.

It does **not** claim to protect a secret against arbitrary code execution under the same signed-in OS user or a fully compromised machine. In particular, the Python keyring project documents a macOS consideration that applications using the same Python executable may access keyring-created items without a fresh OS prompt. Askora therefore MUST NOT describe this architecture as an application sandbox or hardware-backed isolation guarantee.

A future packaged/signed native helper MAY strengthen per-application ACLs, but that is outside v1 and MUST NOT become a Desktop-shell prerequisite.

## Alternatives Considered

### A. Plaintext `.env` or app configuration file

Rejected. It directly violates the frozen local secret boundary and leaks into common backup/editor/log workflows.

### B. Encrypt the API key and store ciphertext in SQLite with an app-managed local key

Rejected for v1. It simply moves the root-secret problem to another local file/key and creates custom cryptographic key-management, backup and portability coupling without a clear benefit over OS credential stores.

### C. Implement macOS Security.framework and Windows WinCred directly with custom Python/ctypes code

Rejected as the default v1 path. It duplicates platform bindings/error handling and increases security-sensitive code. The chosen keyring package already provides thin built-in OS backends; Askora adds an explicit allowlist and its own application-level recovery semantics.

### D. Let keyring auto-select any recommended/installed backend

Rejected. Keyring explicitly supports runtime/config/environment backend selection and third-party backends. Product security cannot depend on whichever backend wins discovery on a user's machine.

### E. Askora-hosted secret proxy/cloud vault

Rejected. It adds remote infrastructure, account/security scope and operating cost contrary to the local single-user v1 product boundary.

## Consequences

- one small cross-platform secret dependency replaces Electron-specific storage;
- no secret needs to live in SQLite/browser/default backup;
- Windows persistence must be explicitly configured to local-machine scope;
- Local Server startup gains a small recovery/reconciliation step for incomplete model-config operations;
- model configuration becomes crash-consistent rather than pretending cross-store atomicity exists;
- restore on another machine requires re-entering BYOK credentials, which is intentional;
- macOS local-user threat limits are documented instead of overstating isolation.

## Migration / Rollback

- Existing environment-only configuration is not automatically copied into LocalSecretStore.
- First explicit user save creates a new secret ref and `LOCAL_USER_CONFIG` profile revision.
- No Electron vault migration is required for v1 unless a later explicit migration task proves such artifacts still exist and should be imported; silent import is forbidden.
- Before `PROFILE_COMMITTED`, rollback removes any provable candidate orphan secret and leaves the prior profile unchanged.
- After profile commit, rollback uses the operation journal and exact prior profile ref; if exact recovery cannot be proven, fail closed into recovery/degraded state.
- Never downgrade to plaintext storage.

## Validation

Required tests include:

- production backend exact allowlist on macOS/Windows;
- reject Null/third-party/configured alternate backend;
- Windows local-machine persistence property;
- fake store allowed only in test/dev and never production-ready;
- no browser/API/log/SQLite/export/backup secret leakage;
- probe failure creates no persistent secret/profile switch;
- crash/restart after each activation phase;
- orphan-secret reconciliation;
- profile-commit/runtime-failure rollback;
- clear where secret deletion fails but disabled routing remains authoritative;
- restore with missing credential becomes degraded/reconfigure, not env fallback;
- idempotent repeated apply/clear;
- real provider Local Web E2E for release evidence.

## Supersedes / Superseded By

This ADR specializes the Local Web `LocalSecretStore` left open by current `MODEL-CONFIG-*` and supersedes any remaining assumption that Electron `safeStorage` or desktop IPC is required for model credentials.

It does not change SYS08 routing ownership, BYOK provider choice, Teaching Policy, Workspace ownership or the product's no-cloud-secret-service boundary.
