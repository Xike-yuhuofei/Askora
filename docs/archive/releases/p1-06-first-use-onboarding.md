# P1-06 First-use Onboarding Release Evidence

> Status：DONE  
> Date：2026-08-10  
> Governing：ADR-0106、ADR-0014、ADR-0015 transition boundary、`ONBOARD-*`

## Scope

P1-06B closes the fact-driven first-use journey without turning onboarding into a second product domain or a new identity system.

Canonical user journey:

```text
Open Askora
→ /welcome supporting route when first-use facts are incomplete
→ MODEL
→ MATERIAL
→ GOAL
→ FIRST_ACTIVITY
→ /today
```

Explicit deep links remain preserved. Settings provides a reopen path. Reload/restart must not manufacture completion or duplicate business writes.

## Implementation Evidence

- PR #13 merged onboarding frontend/backend implementation into `main` at `6068cf39ad492bcc1028950f9ea58058100c6d41`.
- PR #14 completed the merged branch cleanup at `05273d61b655d547939addd4110f097f903f807f`.
- Frontend evidence recorded build success and onboarding/security tests.
- Backend evidence recorded pytest/ruff execution for the candidate; unrelated EXEC-042 integration debt was kept separate from P1-06B claims.
- User confirmed the remaining real-product/manual acceptance as complete on 2026-08-10.

## Product / Architecture Result

```text
/welcome = supporting route, not L0 domain
L0 domains = Today / Learning / Library
Settings = App Utility
welcome completion → /today
explicit deep links preserved
onboarding truth != auth session truth
```

ADR-0015 now governs the next identity transition. P1-06B MUST remain functional when Login/AuthProvider/JWT/session infrastructure is removed by EXEC-047～051.

## Release Gates

```text
Engineering Gate: PASS
Security / Privacy Gate: PASS
Product Usability Gate: PASS
Real Product / Manual Acceptance Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT / unchanged
```

No claim is made that onboarding improves learning outcomes.

## Next Dependency

`EXEC-1062 DONE` unlocks `EXEC-047 — LocalOwner Foundation & Migration`.
