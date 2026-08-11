# EXEC-075 — Learning Conversation Message System Vertical Slice

> Status: **DONE / ARCHIVED**
> Priority: Learning Experience / Architecture Closure
> Frozen: 2026-08-11
> Completed: 2026-08-11
> Governing: Product Positioning、Product Definition CAP-04..07、LCMS Canonical Design Delta、ADR-0020、`LCMS-*`、LCMS Vertical Slice
> Depends on: current v0.3 Learning Core and ADR-0004/0005 transcript/rendering baseline
> Concurrency: do not overlap frontend message/ActivityLearning or backend transcript/contract files with another active EXEC without coordination

## Objective

实现第一个 owner-safe Learning Conversation Message vertical slice：canonical LearningActivity transcript 产生 `LearningMessageV1` + six typed blocks，frontend 通过稳定 renderer/component boundary 呈现，interactive capability 只 dispatch 到 frozen owner port，并保持 history/replay/idempotency/security/ownership 完整。

本 EXEC 不修改 Product Positioning、Product Definition、Teaching Policy/mastery/review algorithms，也不实现 UserNote。

## Dependencies

- ADR-0020 accepted；
- `LCMS-*` FROZEN；
- LCMS Vertical Slice FROZEN；
- current branch rebased/refreshed from latest `origin/main` before implementation；
- no concurrent writer on allowed transcript/message files；
- any needed database migration must first pass the Blocking Conditions below。

## Required Sources

1. `AGENTS.md`
2. `docs/product/PRODUCT-POSITIONING.md`
3. `docs/product/PRODUCT-DEFINITION.md`
4. `docs/specs/README.md`
5. architecture/domain/system/interface/UI/quality specs referenced by `LCMS-*`
6. `docs/design/features/Learning-Conversation-Message-System-Canonical-Design-Delta.md`
7. `docs/architecture/decisions/ADR-0020-learning-conversation-message-presentation-and-interaction-boundary.md`
8. `docs/specs/interfaces/learning-conversation-message-system-spec-delta.md`
9. `docs/specs/vertical-slices/learning-conversation-message-system.md`
10. current code and tests for BookLearning transcript、RenderPayloadV1、ActivityLearning、RichMessage、WorkspaceMessage、Dialog compatibility

## Current Reality

At freeze baseline `origin/main@a192b54`：

- `BookLearningTranscriptTurnV1` is canonical LearningActivity-scoped SYS08 transcript but only exposes learner/reply text and refs；
- `RenderPayloadV1` supports markdown/non-interactive card/citations and MUST remain unchanged；
- `ActivityLearning` directly renders `reply_text`；
- `RichMessage` safely renders RenderPayloadV1 for legacy/other views；
- `DialogMessage` remains compatibility history with optional render payload；
- local Prototype contains invalid frontend assessment/next-action/review-success behavior and is not implementation truth。

## Allowed Files

The implementation SHOULD stay inside：

```text
apps/backend/app/contracts/learning_messages.py                 # new
apps/backend/app/contracts/book_learning.py
apps/backend/app/contracts/__init__.py
apps/backend/app/application/book_learning.py
apps/backend/app/infrastructure/book_learning_transcript.py
apps/backend/app/orchestration/learning_facade.py                # only if canonical path requires
apps/backend/app/api/v1/book_learning.py
apps/backend/app/api/v1/dialog.py                                # compatibility adapter only
apps/backend/app/contracts/rendering.py                           # compatibility import only; no V1 semantic mutation
apps/backend/tests/**learning_message**
apps/backend/tests/**book_learning**
apps/backend/tests/**dialog**                                    # targeted compatibility only

apps/frontend/src/api/bookLearning.js
apps/frontend/src/components/messages/ConversationView*.jsx      # new
apps/frontend/src/components/messages/ConversationView*.css
apps/frontend/src/components/messages/MessageRenderer*.jsx       # new
apps/frontend/src/components/messages/MessageRenderer*.css
apps/frontend/src/components/messages/BlockRenderer*.jsx         # new
apps/frontend/src/components/messages/BlockRenderer*.css
apps/frontend/src/components/messages/blocks/**                   # new six typed components
apps/frontend/src/components/messages/InteractiveElement*.jsx    # new
apps/frontend/src/components/messages/RichMessage.jsx             # compatibility reuse only
apps/frontend/src/components/messages/WorkspaceMessage.jsx        # bounded adapter only if needed
apps/frontend/src/pages/ActivityLearning.jsx
apps/frontend/src/pages/ActivityLearning.css
apps/frontend/src/test/**LearningMessage**
apps/frontend/src/test/ActivityLearning.test.jsx
apps/frontend/src/components/messages/**/*.test.jsx

docs/specs/interfaces/learning-conversation-message-system-spec-delta.md
docs/specs/vertical-slices/learning-conversation-message-system.md
docs/planning/execs/EXEC-075-learning-conversation-message-system-vertical-slice.md
docs/archive/exec-plans/EXEC-075-learning-conversation-message-system-vertical-slice.md
docs/planning/README.md
docs/archive/exec-plans/README.md
docs/governance/document-inventory.md
```

Any file expansion must be justified against an LCMS AC. Database model/migration files are deliberately not allowed by default.

## Forbidden Changes

- modify `RenderPayloadV1 schema_version=1.0` block/action semantics；
- create a new learning owner or generic cross-owner state table；
- add `ReviewItem` or write ReviewSchedule/next_due from Message/UI；
- implement UserNote/CAPTURE_NOTE；
- put TeachingAction/next activity/scoring/mastery/review rules in frontend；
- let LLM/block name arbitrary component/tool/command；
- infer AssessmentResult/mastery from text/DOM/local state；
- online LLM backfill historical messages；
- maintain permanent DialogMessage + LearningMessage dual writer；
- add raw HTML/MDX/script/remote image/unsafe URL；
- weaken tests/ownership/exposure/grader-only/security；
- claim human learning efficacy from Engineering/Policy tests。

## Implementation Tasks

### 1. Baseline and RED tests

- fetch latest main, record branch/status/uncommitted changes；
- confirm no conflicting active work；
- add RED contract tests for Message/common refs/six blocks/capabilities/errors；
- add RED architecture tests for no frontend business rules/arbitrary command；
- add RED normal/history/replay/idempotency/fallback tests。

### 2. Backend contracts and adapters

- implement strict `LearningConversationViewV1` / `LearningMessageV1` / refs/provenance；
- implement six discriminated block schemas；
- implement capability/invocation/result schemas；
- implement deterministic plain/RenderPayloadV1 read adapters without invented refs/capabilities；
- preserve existing fallback and error envelope。

### 3. Canonical transcript integration

- add one accepted Message envelope to the existing SYS08 LearningActivity transcript path；
- preserve exact activity/action/bundle/trace refs；
- maintain `reply_text/content` fallback；
- return same envelope in immediate response/history/replay/final event where applicable；
- duplicate idempotency key returns existing envelope without model/event duplication。

### 4. Frontend component boundary

- implement ConversationView→MessageRenderer→BlockRenderer→specific components；
- reuse safe Markdown/citation primitives；
- implement fallback/unknown/legacy/partial/stale/unavailable；
- keyboard/pointer/touch/focus/live-region/single-flight；
- remove direct `reply_text` rendering only after fallback-equivalent behavior is proven。

### 5. Capability paths

- wire only capabilities with exact frozen owner contract；
- start with read/request paths, then SYS04 submit/SYS06 start where preconditions exist；
- server revalidates scope/version/availability/idempotency；
- UI success requires owner receipt and re-query；
- unavailable owner command remains unavailable, never local mock success。

### 6. Integrity/security/recovery

- prove opened/copy/read/turn count no learner-state effect；
- prove Feedback exact SYS04 or non-assessment label；
- prove review/apply exact SYS06 activity only；
- prove no exposure expansion or grader-only leakage；
- prove restart/reconnect/replay/no duplicate；
- verify rollback to readable fallback。

### 7. Final gates and archive

- run targeted/applicable full gates；
- record current evidence and separate gate conclusions；
- if all AC pass, move EXEC to completed and update indexes in a dedicated completion step；
- do not archive on partial/blocking gap。

## Acceptance Criteria

- `EXEC075-AC-001`：all `LCMS-AC-001..033` applicable criteria PASS with traceable tests。
- `EXEC075-AC-002`：all `LCMS-VS-AC-001..010` PASS。
- `EXEC075-AC-003`：canonical activity renders the same accepted Message in immediate/history/replay and refresh。
- `EXEC075-AC-004`：six block schemas/renderers strict；unknown/invalid safely fall back。
- `EXEC075-AC-005`：interactive action is traceable to capability/owner receipt/result；duplicate key causes no second side effect。
- `EXEC075-AC-006`：frontend contains no policy/scoring/mastery/review rules or arbitrary command route。
- `EXEC075-AC-007`：Feedback/Attempt/Assessment/LearnerState ownership remains SYS04/SYS03；review/apply remains SYS06/SYS07 bounded。
- `EXEC075-AC-008`：RenderPayloadV1 remains backwards compatible and non-interactive；legacy history has no online backfill/fabricated capability。
- `EXEC075-AC-009`：security, scope, exposure, grader-only and prompt-injection regression tests PASS。
- `EXEC075-AC-010`：Engineering、Policy-Ownership、Learning Evidence status reported separately；no efficacy overclaim。

## Required Tests

Targeted first：

```bash
cd apps/backend
pytest <new LCMS contract/integration test paths>
ruff check app tests
mypy app

cd ../frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

Before DONE, run applicable repository Required gates per current CI contract. If a full suite fails, distinguish new regression from pre-existing/current-main failure; do not weaken tests.

## Blocking Conditions

Stop implementation and report `SPEC GAP` if：

- exact owner command for a required capability is absent；
- safe persistence requires a new table/column/migration not covered by current transcript payload；
- multiple valid storage/API options produce different compatibility/idempotency results；
- implementation would mutate RenderPayloadV1 semantics；
- UserNote/Capture or ReviewItem becomes necessary；
- a second canonical transcript/message writer cannot be avoided；
- another active EXEC modifies the same critical files without coordination。

Continue unaffected contract/renderer work, but do not claim DONE or expand architecture before the gap is governed.

## Completion Report Format

Report：

1. modified/new files；
2. Message/Block/capability schema delivered；
3. owner routing and no-frontend-business-logic evidence；
4. compatibility/migration/rollback/retirement state；
5. targeted/full test commands and exact outcomes；
6. Engineering / Policy-Ownership / Learning Evidence gates separately；
7. remaining SPEC/POSITIONING gaps and deferred items；
8. commit/PR only if separately authorized by the user。

## Completion Evidence

- Final verified baseline：`origin/main@3799ac7`；候选实现在提交前完成复核。
- Domain/Public Contract：交付 `LearningConversationViewV1`、`LearningMessageV1`、六类 strict Block、versioned owner/provenance/trace refs、capability/invocation/result 与 stable errors。
- Canonical integration：BookLearning immediate response、durable transcript history 与 conversation projection 读取同一 `message_envelope`；现有 `response_payload` JSON 足以保存 envelope，无数据库 migration。
- Capability：仅启用具备 exact owner path 的 `ASK_FOLLOW_UP`；同 idempotency key replay 返回同一 owner result 且不产生第二次 model/event/message；旧消息的新 invocation fail closed。缺 exact owner refs/command 的其他 capability 保持未启用。
- Frontend：`ConversationView → MessageRenderer → BlockRenderer → six block components → InteractiveElement`；未知/无效 payload 回退 mandatory content；owner failure 可见且可重试；成功态来自 owner result。
- Targeted：backend LCMS contract/architecture/integration `11 passed`；frontend Message/ActivityLearning `9 passed`。
- Full backend：`576 passed, 6 skipped`；Ruff PASS；Mypy `201 source files` PASS。
- Full frontend：`135 passed`；production build PASS；`npm audit --audit-level=high` 为 `0 vulnerabilities`。
- Documentation：`287 files, 0 broken local links`；`git diff --check` PASS。
- Gate：Engineering PASS；Policy / Ownership PASS；Learning Evidence `LEARNING_EVIDENCE_INSUFFICIENT`。
- Product / Positioning / Design / Spec Gap：none。显式 deferred：UserNote/CAPTURE_NOTE、缺 exact owner contract 的 capability、human learning efficacy claim。
