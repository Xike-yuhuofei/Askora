# Learning Conversation Message System Vertical Slice

> 状态：**FROZEN — IMPLEMENTED BY EXEC-075**
> 版本：v1.0
> 日期：2026-08-11
> Governing：Product Positioning、Product Definition CAP-04..07、LCMS Canonical Design Delta、ADR-0020、`LCMS-*`
> EXEC：`EXEC-075`
> Implementation：DONE（2026-08-11）

## 1. Slice Goal

在一项 canonical LearningActivity 内，将一个 owner-decided TeachingAction 安全执行为 typed LearningMessage，并让学习者通过 block capability 提交真实操作，最终得到可追踪的 owner receipt/result，而不把任何教学、评估、mastery 或 review 规则放入 Message/UI。

```text
SYS06 LearningActivity
→ SYS05 TeachingAction
→ SYS02 EvidenceBundle
→ SYS08 LearningMessageV1 + six typed block schema
→ frontend typed renderer
→ capability invocation
→ SYS04/SYS05/SYS06 owner path
→ exact result refs
→ same persisted/history/replayed Message
```

## 2. Entry Baseline

Current main already provides：

- ADR-0004 SYS08 append-only Book Learning transcript；
- ADR-0005 policy-bound model rendering；
- v0.3 TeachingAction/EvidenceBundle/DecisionTrace contracts；
- canonical SYS06 activity lifecycle；
- legacy `RenderPayloadV1` safe renderer/fallback；
- LearningActivity transcript query/teaching round；
- ActivityLearning UI and Learning Context Drawer。

Known gaps：

- ActivityLearning renders `reply_text` directly；
- transcript contract has no LearningMessage blocks/capabilities；
- RenderPayloadV1 is intentionally non-interactive；
- legacy DialogMessage remains separate compatibility path；
- Prototype interaction state is not owner-safe。

## 3. Primary E2E Scenario

1. User starts/resumes an exact SYS06 LearningActivity.
2. SYS05 creates immutable TeachingAction; SYS02 supplies scoped learner-visible EvidenceBundle.
3. SYS08 validates and accepts one `LearningMessageV1` with fallback content and typed blocks.
4. Frontend renders the same Message through `ConversationView → MessageRenderer → BlockRenderer`.
5. A `LEARNING_ACTIVITY` block exposes one server-issued capability such as `SUBMIT_ATTEMPT` or `REQUEST_HINT`.
6. User invokes it with message/block/capability identity, exact versions and idempotency key.
7. The canonical owner path accepts/rejects the command; UI does not score, choose the next action or update mastery.
8. Result returns exact Attempt/AssessmentResult/new TeachingAction/transcript refs as applicable.
9. Refresh/history/reconnect returns the same accepted Message revision and no duplicate side effect.
10. Engineering, Policy-Ownership and Learning Evidence gates are reported separately.

## 4. In Scope

- `LearningConversationViewV1` / `LearningMessageV1` / six strict block schemas；
- exact owner/provenance/trace refs；
- capability descriptor/invocation/result contracts；
- deterministic plain/RenderPayloadV1 adapters；
- normal/history/SSE-final or equivalent final-response consistency；
- safe frontend component hierarchy；
- owner-safe ASK/INSPECT/REQUEST/SUBMIT/START dispatch；
- Feedback exact-result vs non-assessment distinction；
- Review/Apply start-exact-activity semantics；
- targeted architecture/contract/integration/E2E/security tests；
- legacy compatibility and retirement evidence。

## 5. Out of Scope

- Product Positioning or Product Definition changes；
- UserNote/CAPTURE_NOTE contract；
- new ReviewItem；
- new Teaching Policy/mastery/review algorithm；
- database schema until domain-to-storage mapping proves it is needed；
- generic plugin blocks/actions；
- arbitrary HTML/MDX/media/remote images；
- replacing all legacy Dialog UI in one step；
- learning efficacy claim。

## 6. Architecture Slice

```text
┌───────────────────────────────────────────────────────────┐
│ SYS08 LearningConversation projection                    │
│  └─ accepted LearningMessageV1                            │
│      ├─ fallback content                                  │
│      ├─ exact SYS01..08 refs                              │
│      ├─ six typed MessageBlockV1                          │
│      └─ server-issued capability descriptors              │
└───────────────────────┬───────────────────────────────────┘
                        │ strict API/query
┌───────────────────────▼───────────────────────────────────┐
│ Frontend typed renderer                                   │
│ ConversationView → MessageRenderer → BlockRenderer        │
│ → SpecificBlock → InteractiveElement → dispatch adapter   │
└───────────────────────┬───────────────────────────────────┘
                        │ strict invocation + idempotency
┌───────────────────────▼───────────────────────────────────┐
│ Canonical application/owner ports                         │
│ SYS01/02 query | SYS04 Attempt | SYS05 new decision       │
│ SYS06 Start Activity | SYS03/07 owner flows remain indirect│
└───────────────────────────────────────────────────────────┘
```

## 7. Phase A — Contracts and Safe Adapters

Implement strict Pydantic/transport schemas and frontend validators for：

- conversation/message/common refs/provenance；
- six blocks；
- capability/invocation/result；
- stable boundary errors；
- content fallback；
- deterministic RenderPayloadV1/plain adapters。

Exit criteria：

- unknown major/type/extra executable fields fail closed；
- adapters never invent owner refs/capability；
- existing RenderPayloadV1 behavior remains unchanged；
- contract tests cite `LCMS-AC-*`。

## 8. Phase B — Canonical Transcript Integration

Add Message envelope to the existing LearningActivity-scoped SYS08 transcript path without creating a parallel canonical transcript.

Requirements：

- one accepted envelope per message revision；
- exact activity/action/bundle/trace refs；
- `reply_text/content` remains fallback；
- idempotency replay returns same message；
- history/normal/final response equivalence；
- failed provider/validation/ledger path produces no accepted Message/learner failure。

If persistence cannot be mapped safely to the existing append-only transcript payload, stop implementation and create a narrow persistence/migration delta before schema changes.

## 9. Phase C — Frontend Renderer

Build/reuse：

```text
ConversationView
→ MessageRenderer
→ BlockRenderer
→ six SpecificBlockComponents
→ InteractiveElementRenderer
```

Requirements：

- fallback/legacy/canonical messages coexist safely；
- no raw HTML/MDX/script/dynamic component/arbitrary command；
- keyboard/pointer/touch equivalence；
- loading/error/conflict/unavailable/single-flight；
- no frontend policy/scoring/mastery/review logic；
- current ActivityLearning and compatible transcript views use the same renderer where applicable。

## 10. Phase D — Capability Dispatch

Wire capabilities one owner path at a time：

1. `INSPECT_SOURCE` scoped read；
2. `ASK_FOLLOW_UP` / `REQUEST_HINT` / `REQUEST_EXPLANATION` through canonical teaching façade and new SYS05 decision；
3. `SUBMIT_ATTEMPT` through SYS04 contract when exact evaluative item/activity exists；
4. `START_ACTIVITY` through SYS06 exact lifecycle command for Review/Apply blocks。

Missing owner command/ref means capability unavailable; no placeholder local success.

## 11. Phase E — Owner and Educational Integrity

Prove：

- message open/copy/read does not change learner state；
- AssessmentResult remains SYS04 and MasteryEstimate remains SYS03；
- Feedback exact-result requirement；
- actual assistance/exposure traceability；
- Request Hint creates new owner decision rather than local hint escalation；
- Review/Apply only starts exact SYS06 activity；
- activity completion does not equal mastery；
- no validation obligation completion without fresh independent refs。

## 12. Phase F — Compatibility, Recovery and Security

Prove：

- restart/history/reconnect replay；
- no duplicate message/Attempt/event/transition；
- legacy plain/RenderPayload adapters；
- cross-Workspace fail closed；
- malicious document/model/block/capability payload rejected；
- grader-only/secret/raw unnecessary Prompt excluded；
- rollback to content fallback；
- canonical-path dual writer retirement conditions documented and measured。

## 13. Acceptance Criteria

- `LCMS-VS-AC-001`：`LCMS-AC-001..005` Functional criteria PASS。
- `LCMS-VS-AC-002`：`LCMS-AC-010..014` Educational criteria PASS。
- `LCMS-VS-AC-003`：`LCMS-AC-020..024` Architecture/Ownership criteria PASS。
- `LCMS-VS-AC-004`：`LCMS-AC-030..033` Security/Quality criteria PASS。
- `LCMS-VS-AC-005`：at least one canonical activity E2E traces Message→capability→owner receipt/result→history replay。
- `LCMS-VS-AC-006`：duplicate idempotency/reconnect creates no second Message/Attempt/Event/activity transition。
- `LCMS-VS-AC-007`：frontend source has no policy/scoring/mastery/review decision path；architecture test enforces it。
- `LCMS-VS-AC-008`：legacy history remains readable without online LLM backfill or fabricated capability。
- `LCMS-VS-AC-009`：RenderPayloadV1 1.0 remains non-interactive and backwards compatible。
- `LCMS-VS-AC-010`：Engineering/Policy-Ownership/Learning Evidence status is reported separately。

## 14. Required Test Levels

```text
L0  architecture/import/static forbidden paths
L1  schema/renderer/pure adapter
L2  command/error/API/compatibility contracts
L3  SQLite transcript/idempotency/owner integration
L4  canonical LearningActivity browser E2E
L5  restart/replay/migration-or-adapter/erasure
L6  prompt injection/answer leakage/capability authorization
```

Real configured model evidence is required only when the implementation claims model-backed Message generation is connected. Mock-only cannot make that claim.

## 15. Blocking Conditions

Stop and report `SPEC GAP` before expanding scope if implementation requires：

- new owner or state writer；
- `RenderPayloadV1 1.0` semantic mutation；
- new database schema/migration not safely derived from existing transcript；
- UserNote command/owner；
- ReviewItem or direct ReviewSchedule write；
- generic cross-owner command router；
- Teaching Policy/mastery/review algorithm change；
- raw model-defined component/tool execution。

## 16. Definition of Slice Done

This slice is DONE only when all `LCMS-VS-AC-*` pass with current evidence, applicable Required gates pass, no undeclared public/schema/database changes remain, compatibility/rollback is verified, and no blocking gap remains.

Engineering completion MUST NOT be described as human learning efficacy. If no new human outcome study exists, Learning Evidence status remains `LEARNING_EVIDENCE_INSUFFICIENT`.
