# ADR-0018 — UX Workspace Context and Three-Column Learning Architecture

Status: accepted
Date: 2026-08-10
Decision owners: user-authorized Askora product governance
Decision authority: explicit user approval on 2026-08-10 to adopt the UX Architecture three-column model, Workspace context, hideable right rail, Learning Context Drawer, Learning de-management and Library no-OCR exposure
Upper authority: `docs/product/PRODUCT-POSITIONING.md`
Affected specs: `docs/specs/ui/information-architecture.md`, `screen-contracts.md`, `data-contracts.md`, `interactive-element-system.md`, `component-state-contracts.md`, `quality-and-migration.md`, `visual-system.md`, UI vertical slice / EXEC
Canonical design input: `docs/design/UX-Architecture-Canonical-Design-Delta.md`
Supersedes (partial): selected clauses of `ADR-0014` listed in Section 8

## Context

`ADR-0014` established the user-job-driven interaction architecture and the three L0 Product Domains (Today / Learning / Library) with Learning L1 facets Goal / Plan / Progress / History. It also froze a Workspace Shell of `Activity / History Rail | Conversation & Task Canvas | Learning Context Inspector` and allowed OCR to be contextually revealed in Library.

`main` now has the L0/L1 navigation, `/learning/**` routes, a Tutor Workspace with a session-history left rail and central conversation canvas, and a Library with explicit OCR request/review UI. At the same time `ADR-0016` / `WSP-*` froze Workspace as the real high-level data-isolation boundary, but durable Workspace implementation is not yet complete.

The UX Architecture Delta (`UX-Architecture-Canonical-Design-Delta.md`) freezes a further product-level direction that contradicts specific ADR-0014 clauses:

- Learning no longer exposes Goal / Plan / Progress / History as permanent L1 management facets;
- the left rail becomes `Where` (product navigation + canonical Workspace context), the center becomes `Learn` (sole Primary Learning Canvas), and the right rail becomes hideable `Reference / Notes`;
- a default-collapsed Learning Context Drawer sits directly above the composer;
- Workspace is a first-class, shared, canonical context across all three columns;
- Library v1 does not expose OCR in the normal UI.

This ADR absorbs that Delta into an accepted, auditable architecture decision. It does not rewrite the historical ADR-0014 record; it explicitly marks which ADR-0014 clauses are superseded or amended, and it keeps the non-conflicting ADR-0014 principles (user-job derivation, 3 product domains, chat not L0, 7 semantic primitives, L0..L5 hierarchy, progressive disclosure, single Today primary task) in force.

## Decision

### 1. Three-Column Learning Workspace

The Askora learning experience freezes the following column responsibilities, shared across all breakpoints:

```text
Where                          Learn                              Reference / Notes

Global Navigation              Teaching content                  User-authored notes
Current Workspace              Questions                         Current source material
Workspace switch               Learner answers                   Citation / source context
                               Feedback
                               Learning Context Drawer
                               Composer
```

- Left = Where: stable product navigation (Today / Learning / Library), current canonical Workspace visibility, and Workspace switching.
- Center = Learn: the sole Primary Learning Canvas. It presents teaching content, the current question/task, learner answers, feedback, next teaching round, streaming / complete / failed / recoverable state, and necessary citation / assistance / validation obligation. It MUST NOT become a Dashboard.
- Right = Reference / Notes: hideable. V1 supports only Learning Notes and Current Material tabs. Citation / "view source" opens in the right rail contextually; the center does not leave the current learning task.

### 2. Workspace Is Shared Canonical Context

- All three columns MUST resolve the same canonical `current_workspace_id` from the durable Workspace defined by `ADR-0016` / `WSP-*`. Workspace MUST NOT be modeled by route, subject, session, or frontend local state.
- Switching Workspace changes the query scope of the center learning canvas, the right rail notes/material, and the Context Drawer, not just the left-rail selection.
- A single Workspace MUST NOT render a fake dropdown/switch affordance.
- All Material, Note, Goal/Plan projection, Learner State, LearningSession and retrieval query MUST obey the current Workspace scope. No default cross-Workspace aggregation or global search.

### 3. Workspace Switching Safety

Switching Workspace MUST resolve the following before it is considered successful:

- unsaved draft answer;
- an in-flight streaming run;
- an unsaved note;
- open Material tabs and source position;
- a recoverable active LearningSession.

The UI MUST surface explicit `saved / saving / failed / recoverable` states. Clearing React state to fake a switch is forbidden.

### 4. Learning Context Drawer

- A default-collapsed Drawer is fixed directly above the center composer / input area. It is not a fourth column and does not occupy the right rail.
- Collapsed: shows a single orientation line, e.g. `监督学习基础 · 接下来：残差诊断`.
- Expanded: shows only the current stage, the stage goal, and 1..3 dynamic next knowledge points / teaching directions.
- V1 Drawer MUST NOT contain a full Goal editor, full Learning Plan, Progress Dashboard, Evidence management, mastery editing, ReviewSchedule editing, or TeachingAction/Policy control.
- All content MUST come from a canonical/versioned query or an explicit `MISSING / PARTIAL / STALE` state. The frontend MUST NOT infer stage/goal/next from chat text, heading order, or probability thresholds. LLM output MUST NOT be written as canonical next knowledge point.
- expand/collapse changes presentation state only and MUST NOT trigger an owner command.

### 5. Right Auxiliary Rail

- The right rail MUST be hideable; hiding it MUST NOT prevent the central learning task from completing, and reopening MUST restore context.
- V1 tabs: Learning Notes (user-authored durable, Workspace-scoped, anchored) and Current Material (opened contextually from citation / "view source").
- No generic "+" extension host. No deferred candidate tab may be created as a placeholder or disabled tab.
- Current Material and SourceSpan MUST come from canonical current-Workspace refs. Cross-Workspace refs MUST fail closed. Missing SourceSpan shows an honest unavailable state, never a fabricated summary or filename-as-original.

### 6. Learning Is Not a Management Console

- The Learning main surface no longer exposes Goal / Plan / Progress / History as permanent management facets.
- This does NOT delete LearningGoal, LearningPlan, LearnerState, Evidence, ReviewSchedule or History canonical truth, and does NOT change their owners. They continue to drive teaching.
- Necessary creation, correction, confirmation, recovery or audit MAY enter a contextual task flow under an explicit user job, but MUST NOT restore a permanent management center.

### 7. Library v1 Does Not Expose OCR

- Library v1 normal UI MUST NOT expose "recognize scanned PDF" entry, OCR engine/runtime status, OCR candidate, OCR review/publish flow, OCR confidence / bbox / image hash, or copy describing OCR as a v1 core capability.
- A scanned PDF without reliable text MAY honestly show `unsupported / partial extraction` and suggest a supported text-type material.
- Whether historical/optional OCR runtime is retained is decided by the v1 Product Architecture cleanup; even if it temporarily exists it MUST NOT be reachable from the normal v1 Library UI.

### 8. Clause-Level Supersession of ADR-0014

The following ADR-0014 clauses and their downstream UI Spec clauses are explicitly superseded or amended. Non-listed ADR-0014 clauses remain in force.

| ADR-0014 / IES decision | Disposition | Replaced by |
|---|---|---|
| ADR-0014 §3 (Learning aggregates Goal/Path/Progress/History as permanent L1 facets) | **SUPERSEDED** for default exposure | UXA-IA-020..022 / ADR-0018 §6 |
| ADR-0014 §10 route family exposing `/learning/goals|plan|progress|history` as canonical facets | **AMEND / MIGRATION REQUIRED** | UXA-IA-030 route/task-flow matrix |
| ADR-0014 §6..7 (Workspace Shell `Activity / History Rail + Context Inspector`) | **SUPERSEDED IN LAYOUT** | ADR-0018 §1 / UXA-IA-040..041 |
| `IES-CD-008` (Goal/Path/Progress/History as Learning L1 facets) | **SUPERSEDED** for default exposure | UXA-IA-020..022 |
| ADR-0014 §8 / `IES-CD-013` + `UI-SCREEN-091` (OCR contextually revealable) | **SUPERSEDED FOR V1 UI** | UXA-SCREEN-190..195 |
| ADR-0014 §9 Settings hierarchical categories | **KEEP** (unchanged) | UI-SCREEN-100..110 |
| ADR-0014 §5 Today single primary task | **KEEP** (unchanged) | UI-SCREEN-010..017 |
| ADR-0014 §6 7 semantic primitives | **KEEP** (unchanged) | UI-IES-* |
| ADR-0014 L0..L5 hierarchy | **KEEP** (unchanged) | UI-IES-030..035 |

## Alternatives Considered

### A. Keep ADR-0014 four-facet Learning and add Workspace as a cosmetic selector

Rejected. It recreates a global library/learner state beneath a Workspace selector and violates Product Positioning Workspace isolation.

### B. Add the Context Drawer as a fourth column

Rejected. It would split the learner's attention across four regions and turn orientation into a persistent surface instead of a transient, default-collapsed aid.

### C. Keep the right rail as the Learning Context Inspector plus a Notes tab

Rejected. The Delta's model is Notes / Reference during active learning, not an always-on inspector of system objects. Keeping the old inspector semantics would re-expose management facets.

### D. Expose OCR as an advanced/compatibility action in Library v1 normal UI

Rejected. Product Positioning already makes full OCR non-core; the Delta freezes that OCR is unreachable from the normal v1 UI to stop OCR from being described or perceived as a v1 capability.

## Consequences

### Positive

- The learner stays in one learning surface; reference and notes are contextual, not a second truth.
- Workspace becomes a real, shared context instead of a frontend-only selection.
- Learning stops demanding the user manage Goal/Plan/Progress/History to learn.
- OCR no longer leaks into v1 as a perceived core capability.

### Cost / Risk

- Old `/learning/goals|plan|progress|history` routes and deep links must be migrated without side effects and without deleting canonical data.
- Workspace switch recovery, UserNote durable owner, and Context Drawer query contracts must be frozen before implementation; until then implementation of those EXEC is `BLOCKED_BY_SPEC_GAP` / `BLOCKED_BY_DEPENDENCY`.
- The four management pages are no longer the completion evidence for the new UX; their owner semantics are retained but their user-facing jobs are rewritten.

## Ownership / Truth Impact

This ADR does not change SYS01..SYS08 canonical ownership, Workspace ownership (Platform Workspace Registry per ADR-0016), LearningProject/ProjectMaterial ownership, or LearningSession ownership. It does not create any second Tutor / Material / Note / Workspace truth.

UserNote durable object, Workspace switch command, and Context Drawer canonical query owners are NOT invented here. They are declared as required upstream contracts; where an existing contract does not uniquely determine the owner, the corresponding EXEC is `BLOCKED_BY_SPEC_GAP` until a narrow ADR/Spec decision is accepted.

## Security / Privacy / Recovery

- No authentication, privacy, erasure, credential or loopback boundary change.
- Route migration and Workspace switch MUST NOT trigger commands or state writes as a side effect.
- Hiding the right rail MUST NOT hide the only citation, a safety error, or a validation obligation needed to complete the current task.
- No silent data loss: unsaved notes, drafts, in-flight streams, open material tabs and active sessions must be explicitly saved / saving / failed / recoverable.
- Cross-Workspace refs fail closed without disclosing whether a foreign object exists.
- Historical deep links and back behavior are preserved via the route matrix in `UXA-IA-030`.
- UI/engineering work MUST NOT claim human learning efficacy.

## Migration / Rollback

1. Accept this ADR and register it in `docs/adr/README.md`.
2. Update `docs/specs/ui/**` with `UXA-*` clauses and the supersession / route / state matrices.
3. Freeze a new UI vertical slice and serial EXEC that explicitly depend on Workspace Product Architecture issues (XIK-171, XIK-172, XIK-177, XIK-175, XIK-179, XIK-165 where applicable).
4. Implement Workspace Context / Shell / Route migration first, then Drawer, then Notes + Material rail, then de-management, then Library no-OCR, then responsive/accessibility/release acceptance.
5. Do not delete old `/learning/**` routes until the route matrix retirement condition is met; keep them as no-side-effect redirect / bounded compatibility / task-flow entry.
6. Rollback/forward-fix: presentation-only forward-fix; never restore chat-first default, Account/Login, dual Workspace truth, or the permanent four-facet management center.

## Validation

At least verify:

- all three columns resolve the same canonical `current_workspace_id`;
- Workspace switch handles draft / stream / note / session / material-tab and shows explicit saved / saving / failed / recoverable states;
- Context Drawer is default-collapsed, shows only stage / stage goal / next 1..3, and never fails the center canvas;
- right rail is hideable and reopening restores context; no silent data loss;
- Learning builds no permanent Goal/Plan/Progress/History management center;
- Library v1 exposes no OCR entry/status/review from the normal UI and shows honest unsupported/partial for scanned PDFs;
- deferred candidates (outline, Evidence, knowledge graph, Progress, AI Summary, Flashcards, 错题本) create no placeholder / disabled tab;
- old `/learning/**` deep links migrate without business side effect;
- 1440×900 / 1024×768 / 768×1024 / 360×800 and 200% zoom complete the primary task without horizontal scroll or three-level critical nested scroll;
- keyboard / touch / screen reader can open / close / switch rails and drawer; focus returns to the trigger point;
- frontend build, UI unit/integration, browser E2E pass.

Engineering / Policy-Ownership / Learning Evidence conclusions remain separated. This ADR is an IA/interaction/presentation decision and produces no new Learning Evidence claim.

## Supersedes / Superseded By

This ADR partially supersedes `ADR-0014` per the matrix in Section 8. It specializes the product/IA implications already frozen by `PRODUCT-POSITIONING.md`, `ADR-0016` / `WSP-*`, and the `UX-Architecture-Canonical-Design-Delta.md`. It does not supersede v0.3 Teaching Policy, SYS01..SYS08 ownership, ADR-0015 LocalOwner/no-auth, or ADR-0017 LocalSecretStore.

Superseded by: none.