# EXEC-064 — Local Web BYOK Secure Configuration and Activation

> Status: **FROZEN / BLOCKED_BY_EXEC_060**  
> Linear: XIK-173  
> Priority: P0 Core AI Configuration  
> Frozen: 2026-08-10  
> Governing gap: GAP-V1-004

## 1. Objective

Implement Local Web BYOK end to end using ADR-0017 + `LSS-*` + `MODEL-CONFIG-*`: browser Settings → loopback API → SYS08 ModelRouteProfile → approved OS-backed LocalSecretStore → real provider runtime.

## 2. Dependency

```text
EXEC-060 DONE
→ EXEC-064
```

The runtime baseline must be stable before adding production credential activation/recovery semantics.

## 3. Required Sources

- `PRODUCT-POSITIONING.md`
- ADR-0017
- `docs/specs/platform/local-secret-store.md`
- `docs/specs/systems/08-model-configuration.md`
- `docs/specs/quality/security-standard.md`
- Persistence/Error/API contracts
- current provider/router/settings code

## 4. Frozen Security Shape

Production persistent backends only:

```text
macOS   → exact keyring.backends.macOS.Keyring
Windows → exact keyring.backends.Windows.WinVaultKeyring
```

Windows uses local-machine credential persistence. Production rejects automatic/unapproved/Null/file/third-party backend selection and has no plaintext fallback.

Profile routing truth remains SYS08; secret presence never activates a route.

## 5. Implementation Tasks

1. Add pinned/locked `keyring` production dependency and required platform bindings.
2. Implement `LocalSecretStore` port + exact production backend adapters/allowlist.
3. Implement Windows local-machine persistence setting.
4. Add non-sensitive ModelRouteProfile persistence for provider/model/embedding/task routes.
5. Add durable non-secret model-config operation journal with ADR-0017/LSS phases.
6. Implement apply/clear idempotency and optimistic revision checks.
7. Implement fixed synthetic real-provider probe before activation.
8. Implement secret write → profile commit → runtime refresh/verify → old-secret retirement ordering.
9. Implement clear as disabled routing first, cleanup second.
10. Reconcile incomplete operations before model config reports ready.
11. Implement missing-secret/degraded/re-enter behavior on restore/machine move.
12. Add loopback model-settings API with no saved-key readback.
13. Implement Settings UI for Provider, Model, Embedding and permitted task routes.
14. Ensure candidate keys never enter browser persistence/durable frontend cache/URL/logs.
15. Ensure runtime provider instances invalidate stale credentials on revision change.
16. Add real-provider E2E path without exposing secret in evidence artifacts.

## 6. Allowed Files

- model configuration contracts/models/application/repositories
- LocalSecretStore infrastructure
- provider/router runtime integration
- loopback API routes
- Settings frontend/API module
- dependency/lock files
- migration for non-secret profile/journal only
- security/contract/E2E tests

## 7. Forbidden Changes

Do NOT:

- use Electron/safeStorage/preload IPC;
- persist API key/plaintext/ciphertext in ordinary SQLite;
- expose saved key, fragment, fingerprint or secret_ref to browser;
- allow automatic/unverified keyring backend selection in production;
- fall back to `.env` after explicit clear/user config failure;
- send user documents/learner state in connection probe;
- activate config after failed probe;
- delete prior credential before new runtime verification;
- introduce Askora cloud proxy/vault;
- claim OS keyring protects against arbitrary same-user machine compromise.

## 8. Acceptance Criteria

- `EXEC064-AC-001`: browser Settings can configure provider/model/embedding/task routes without Desktop/Electron.
- `EXEC064-AC-002`: production macOS/Windows accept only exact approved OS-backed keyring backend.
- `EXEC064-AC-003`: Windows credential uses local-machine persistence.
- `EXEC064-AC-004`: no secret material appears in browser persistence, public API, ordinary SQLite, logs, export, default backup or diagnostics.
- `EXEC064-AC-005`: failed probe writes no persistent candidate secret and does not switch active profile.
- `EXEC064-AC-006`: successful activation binds exact profile/runtime revision and real provider.
- `EXEC064-AC-007`: crash after every journal phase reconciles to exact prior/new verified config or explicit degraded state; no silent split-brain.
- `EXEC064-AC-008`: clear remains disabled across restart even if old-secret cleanup fails.
- `EXEC064-AC-009`: restored profile with missing secret requires re-entry and never silently uses environment key.
- `EXEC064-AC-010`: changing task route is deterministic/auditable; no silent cross-provider failover.
- `EXEC064-AC-011`: real-model-required Local Web flow uses the configured exact provider/model after restart.
- `EXEC064-AC-012`: storage/provider failures never become learner failure evidence.

## 9. Required Tests

- exact backend allowlist and override rejection;
- Windows persistence property;
- LocalSecretStore unavailable/locked/no plaintext fallback;
- browser/API/SQLite/log/export/backup leakage scans;
- probe failure matrix;
- apply/clear concurrency + idempotency;
- crash injection for every activation/clear phase;
- orphan-secret recovery;
- missing-secret restore;
- runtime revision refresh;
- real provider browser E2E when credentials are available;
- Required CI relevant jobs.

## 10. Completion Report

Report exact dependency versions, OS adapters, schema/journal migration, secret-leakage scan results, crash matrix results, real provider evidence, CI state and any environment-only compatibility retained.

Archive only after all ACs pass.