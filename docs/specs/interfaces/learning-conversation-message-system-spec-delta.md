# Askora Learning Conversation Message System Spec Delta

> Spec ID：`LCMS-*`
> 状态：**Canonical Implementation Contract — FROZEN**
> 版本：v1.0
> 冻结日期：2026-08-11
> 上位：Product Positioning、Product Definition CAP-04..07、Learning Conversation Message System Canonical Design Delta、ADR-0020
> 相关：`RENDER-*`、`API-*`、`ERROR-*`、`UI-*`、SYS03～SYS08、v0.3 Adaptive Teaching Loop
> 实现状态：EXEC-075 DONE（2026-08-11）；本文件不设计 SQLite table

## 1. Purpose and Scope

本 Spec 将 Learning Conversation Message System 从 Prototype 推进到可执行的 Spec Freeze，冻结：

- Message Architecture；
- 六类 Message Block；
- Domain Data Contract；
- interaction/capability contract；
- state decomposition；
- Teaching System boundary；
- frontend component boundary；
- compatibility/migration/rollback；
- testing and acceptance criteria。

本 Spec 不：

- 把 Conversation/Message 变成核心学习领域模型；
- 修改 SYS01～SYS08 single-writer ownership；
- 设计数据库表、列、index 或 migration revision；
- 冻结 UserNote/Capture command；
- 修改 Teaching Policy、mastery algorithm 或 review algorithm；
- 以 UI Preview/Mock 声称真实 assessment/review/learning efficacy。

## 2. Normative Language and Authority

`MUST / MUST NOT / SHOULD / MAY` 为规范性要求。冲突时服从：

```text
Product Positioning
→ Product Definition
→ current specs / accepted ADR
→ this additive interface spec
→ vertical slice / EXEC
→ implementation
```

若本 Spec 与现有 SYS03～SYS08 owner 合同冲突，必须修正本 Spec 的下位表达，不得把 owner 移到 Message/UI。

## 3. Message Architecture

### LCMS-001 — Hierarchy

```text
LearningConversationViewV1
        ↓ contains ordered
LearningMessageV1
        ↓ contains ordered
MessageBlockV1
        ↓ exposes zero or more
InteractiveElementV1
        ↓ dispatches
LearningInteractionInvocationV1
        ↓ accepted by
owner command/query
        ↓ returns
owner receipt / result refs / next transition
```

### LCMS-002 — Semantic classification

| Concern | Contract layer | Examples | Canonical owner |
|---|---|---|---|
| 内容 | Message/Block presentation | explanation、knowledge、evidence text | SYS08 artifact；source truth remains SYS01/SYS02 |
| 教学行为 | exact refs, not local state | TeachingAction、hint/exposure、activity | SYS05/SYS06 |
| 用户操作 | capability invocation | submit、request、inspect、start | corresponding owner application port |
| 系统状态 | owner refs/projections | assessment、mastery、review due | SYS03/SYS04/SYS07 |
| 呈现状态 | renderer/UI | focused、expanded、submitting | frontend transient only |

### LCMS-003 — Conversation boundary

`LearningConversationViewV1` 是 current Workspace + exact LearningActivity scoped read projection。它只拥有 ordering/cursor/availability，不拥有 LearningSession、LearningActivity、Plan 或 learning state。

### LCMS-004 — Message boundary

`LearningMessageV1` 是 SYS08 accepted presentation/transcript artifact。它 MAY 引用其他 owner records，但 MUST NOT：

- write/patch their state；
- carry unvalidated arbitrary command；
- interpret `opened/read/copy/like` as learning evidence；
- replace Attempt/AssessmentResult/LearnerEvidence；
- store mutable “current mastery/next due/next action” as its own truth。

### LCMS-005 — Learning Action boundary

Learning Action is not a nested mutable Message object. An interaction only dispatches a strict command/query; the actual result is owned by the target system and linked by exact ref.

## 4. Common Reference Contracts

### LCMS-010 — VersionedOwnerRefV1

```yaml
owner_ref:
  source_system: SYS01|SYS02|SYS03|SYS04|SYS05|SYS06|SYS07|SYS08|PLATFORM
  entity_type: string
  entity_id: string
  version: string|integer
  workspace_id: uuid
  availability: READY|MISSING|PARTIAL|STALE|NOT_APPLICABLE|LEGACY_COMPAT
  freshness_at: datetime|null
```

- `source_system/entity_type/entity_id/version/workspace_id` MUST be exact for READY refs；
- `MISSING != empty != zero`；
- foreign Workspace refs MUST fail closed；
- mutable current state MUST NOT be inserted into an immutable historical message without the historical exact version。

### LCMS-011 — TraceReferencesV1

```yaml
trace_references:
  correlation_id: string
  workflow_run_ref: versioned_owner_ref|null
  decision_trace_ref: versioned_owner_ref|null
  model_inference_ref: versioned_owner_ref|null
  learning_event_refs: [versioned_owner_ref]
```

Raw Prompt、provider secret、grader-only rubric/answer 和完整无关资料正文 MUST NOT be included.

### LCMS-012 — ProvenanceV1

```yaml
provenance:
  mode: SOURCE_GROUNDED|EXTERNAL_MODEL|MIXED|USER_AUTHORED|NOT_APPLICABLE
  source_refs: [versioned_owner_ref]
  source_span_refs: [versioned_owner_ref]
  evidence_bundle_ref: versioned_owner_ref|null
  generated_by_ref: versioned_owner_ref|null
```

`SOURCE_GROUNDED` claims MUST have traceable SYS01/SYS02 refs. `EXTERNAL_MODEL` MUST NOT fabricate citation/SourceSpan.

## 5. Conversation and Message Domain Contract

### LCMS-020 — LearningConversationViewV1

```yaml
learning_conversation_view:
  schema_version: "1.0"
  conversation_id: string
  conversation_kind: LEARNING_ACTIVITY_TRANSCRIPT|LEGACY_DIALOG_COMPAT
  workspace_ref: versioned_owner_ref
  learning_activity_ref: versioned_owner_ref
  learning_session_ref: versioned_owner_ref|null
  transcript_ref: versioned_owner_ref
  messages: [learning_message]
  next_cursor: string|null
  view_state: READY|EMPTY|PARTIAL|STALE
  generated_at: datetime
  correlation_id: string
```

Rules：

- canonical new use MUST be `LEARNING_ACTIVITY_TRANSCRIPT`；
- `learning_session_ref` 只有在 exact Platform LearningSession binding 可证明时出现；不得把 DialogSession 改名冒充；
- `messages` 按 immutable sequence 排序；同一 cursor replay MUST not duplicate message；
- legacy dialog response MUST be labeled `LEGACY_DIALOG_COMPAT` and MUST not fabricate activity/policy/evidence refs。

### LCMS-021 — LearningMessageV1

```yaml
learning_message:
  schema_version: "1.0"
  id: string
  revision: integer
  conversation_id: string
  sequence: integer
  role: LEARNER|ASSISTANT|SYSTEM_NOTICE
  timestamp: datetime
  content: string
  blocks: [message_block]
  context:
    workspace_ref: versioned_owner_ref
    learning_activity_ref: versioned_owner_ref
    learning_session_ref: versioned_owner_ref|null
    transcript_turn_ref: versioned_owner_ref
    teaching_action_ref: versioned_owner_ref|null
    evidence_bundle_ref: versioned_owner_ref|null
    attempt_ref: versioned_owner_ref|null
    assessment_result_ref: versioned_owner_ref|null
  trace_references: trace_references
  compatibility:
    source: CANONICAL|RENDER_PAYLOAD_V1_ADAPTER|PLAIN_TEXT_ADAPTER|LEGACY_DIALOG
    fidelity: FULL|PARTIAL
    reason_codes: [string]
```

Rules：

- `id + revision` immutable；correction creates new revision/supersession record；
- `content` REQUIRED safe readable fallback and MUST preserve the accepted learner-visible meaning；
- canonical new `ASSISTANT` message MUST have 1..32 blocks；learner/system/legacy adapter MAY have 0..32；
- block ids MUST be unique in a message and stable across history/replay；
- assistant owner refs MUST correspond to the accepted execution, not current mutable state；
- learner text does not automatically become Attempt；`attempt_ref` only appears after SYS04 acceptance；
- `SYSTEM_NOTICE` cannot carry scoring/mastery/policy decisions。

### LCMS-022 — Message revision and deletion

Messages/transcript artifacts use append/revision semantics. Ordinary correction MUST NOT overwrite historical accepted meaning. Owner-safe erasure may remove durable content according to Data Control contract and MUST invalidate affected projections; LCMS does not create its own undeletable copy.

## 6. Message Block Common Contract

### LCMS-030 — MessageBlockV1

```yaml
message_block:
  id: string
  type: EXPLANATION|KNOWLEDGE|EVIDENCE|LEARNING_ACTIVITY|FEEDBACK|REVIEW_APPLY
  payload: object
  metadata:
    schema_version: "1.0"
    semantic_role: string
    provenance: provenance
    owner_refs: [versioned_owner_ref]
    availability: READY|MISSING|PARTIAL|STALE|NOT_APPLICABLE|LEGACY_COMPAT
    reason_codes: [string]
    accessibility_label: string|null
  interactions: [interactive_element]
```

Rules：

- strict discriminated union；unknown type/major MUST fallback to `message.content`；
- extra arbitrary executable fields MUST be rejected；
- `payload` is learner-visible content/presentation only；
- business refs/status belong in metadata/context, not copied into free-form Markdown；
- a stale/missing owner ref MUST disable dependent capability；
- renderer MAY choose visual variant but MUST not change block type/owner semantics。

## 7. Block Type Specification

### LCMS-040 — Explanation Block

| Property | Contract |
|---|---|
| Purpose | 呈现讲解、步骤、例子、类比、对比或总结 |
| When Used | SYS08 在已决定 TeachingAction/EvidenceBundle envelope 内发布 learner-visible explanation |
| Input | exact TeachingAction ref；EvidenceBundle/source refs when grounded；validated model/template output |
| Output | ordered safe rich text segments；optional formula/code/table presentation |
| Required Metadata | provenance mode；TeachingAction ref for canonical teaching reply；generated_by/model ref when AI-generated；availability |
| User Interaction | ASK_FOLLOW_UP、REQUEST_EXPLANATION；INSPECT_SOURCE only when exact SourceSpan exists |
| Learning Value | 建构理解/降低表征负担；阅读本身不是 mastery evidence |
| Rendering Requirement | safe Markdown/math allowlist；raw HTML/MDX/script/remote image/arbitrary component forbidden |

```yaml
payload:
  title: string|null
  body_markdown: string
  presentation: DEFAULT|STEPS|EXAMPLE|COMPARISON|SUMMARY
```

`presentation` is visual composition, not StrategyFamily/InteractionMove.

### LCMS-041 — Knowledge Block

| Property | Contract |
|---|---|
| Purpose | 突出一个概念、原则、关系或关键点 |
| When Used | 需要稳定寻址或独立 provenance 的知识表达 |
| Input | SYS01 published KnowledgeUnit/relation ref，或 explicitly presentation-only content |
| Output | term/title + concise learner-visible body + optional qualifier |
| Required Metadata | `knowledge_status=CANONICAL_REF|PRESENTATION_ONLY`；SYS01 ref when canonical；provenance |
| User Interaction | ASK_FOLLOW_UP、INSPECT_SOURCE；测试只能由 owner-issued separate LearningActivity capability 提供 |
| Learning Value | 帮助组织 mental model；不能单凭查看/保存形成 evidence |
| Rendering Requirement | visually distinct but quiet；不得把 arbitrary card variant 当 canonical knowledge status |

```yaml
payload:
  title: string
  body_markdown: string
  knowledge_status: CANONICAL_REF|PRESENTATION_ONLY
  qualifier: string|null
```

### LCMS-042 — Evidence Block

| Property | Contract |
|---|---|
| Purpose | 显示资料原文、citation、locator 与来源上下文入口 |
| When Used | learner-visible EvidenceBundle/SourceSpan 可验证时 |
| Input | SYS02 EvidenceBundle + SYS01 SourceSpan/Material revision |
| Output | excerpt、source label、locator、source refs |
| Required Metadata | SOURCE_GROUNDED provenance；EvidenceBundle + SourceSpan exact refs；learner-visible classification |
| User Interaction | INSPECT_SOURCE、ASK_FOLLOW_UP |
| Learning Value | 支持 grounding、核验、上下文理解；不是 assessment evidence |
| Rendering Requirement | source/locator always visible；missing source honest unavailable；grader-only/answer-only structurally excluded |

```yaml
payload:
  excerpt: string
  source_label: string
  locator: string|null
  citation_label: string|null
```

### LCMS-043 — Learning Activity Block

| Property | Contract |
|---|---|
| Purpose | 呈现当前 owner-issued question/task/prompt 与允许的响应入口 |
| When Used | exact SYS06 LearningActivity + SYS05 TeachingAction requires learner action；evaluative activity also requires SYS04 item ref |
| Input | activity/action/item refs、allowed response schema、assistance/exposure envelope |
| Output | prompt、response-mode presentation、capability descriptor；actual output belongs to owner command |
| Required Metadata | SYS06 activity ref；SYS05 action ref；SYS04 item ref when evaluative；actual/allowed assistance semantics；availability |
| User Interaction | SUBMIT_ATTEMPT、REQUEST_HINT、REQUEST_EXPLANATION |
| Learning Value | 产生主动生成/retrieval/application opportunity；只有 owner-accepted Attempt may enter evidence chain |
| Rendering Requirement | accessible form；single-flight；loading/error/retry；不得 reveal grader-only answer；no half-JSON execution |

```yaml
payload:
  prompt_markdown: string
  response_mode: TEXT|SINGLE_CHOICE|MULTI_CHOICE|NUMERIC|CODE|NONE
  options: [object]
  response_constraints: object
```

The client MUST NOT submit score、correctness、mastery、next action、assistance state or target status.

### LCMS-044 — Feedback Block

| Property | Contract |
|---|---|
| Purpose | 呈现一次作答的评价/诊断/纠错，或明确的执行反馈 |
| When Used | exact SYS04 AssessmentResult exists，或 non-assessment execution status needs presentation |
| Input | Attempt/AssessmentResult/actual assistance refs；validated feedback realization |
| Output | correctness/score summary、diagnosis uncertainty、learner-visible feedback and next owner-issued capability |
| Required Metadata | `feedback_basis=ASSESSMENT_RESULT|NON_ASSESSMENT_EXECUTION_FEEDBACK`；result ref required for assessment；actual assistance/exposure；confidence/unknown semantics |
| User Interaction | owner-issued retry/request explanation/start activity；never SetMastery |
| Learning Value | correction and error diagnosis；not equivalent to LearnerState/mastery |
| Rendering Requirement | partial/correct/unscorable/system failure distinct；failure must not look like learner failure；uncertainty visible |

```yaml
payload:
  feedback_basis: ASSESSMENT_RESULT|NON_ASSESSMENT_EXECUTION_FEEDBACK
  heading: string
  body_markdown: string
  correctness: CORRECT|PARTIAL|INCORRECT|UNSCORABLE|null
  assessment_confidence: float|null
  diagnostic_summary: string|null
```

`mastered`/`needs_review` fields are forbidden.

### LCMS-045 — Review / Apply Block

| Property | Contract |
|---|---|
| Purpose | 呈现并启动已由 owner 创建的延迟复习或迁移/应用活动 |
| When Used | exact SYS06 activity is available；review MAY read SYS07 due/schedule；apply references SYS05 transfer action when already decided |
| Input | activity ref；review due/schedule ref or transfer action ref；start capability |
| Output | reason/goal/prompt preview + START_ACTIVITY capability；success returns SYS06 lifecycle receipt |
| Required Metadata | `mode=REVIEW|APPLY`；exact SYS06 ref；SYS07/SYS05 refs as applicable；availability/reason |
| User Interaction | START_ACTIVITY only；other request actions MAY create a new owner decision but cannot mutate this block |
| Learning Value | delayed retrieval or transfer opportunity；starting/completing activity is not itself mastery evidence |
| Rendering Requirement | distinguish due candidate vs planned activity；unavailable state honest；never display “已加入复习” before owner success |

```yaml
payload:
  mode: REVIEW|APPLY
  title: string
  description_markdown: string
  timing_label: string|null
```

No `ReviewItem` is introduced. `next_due_at` is read-only SYS07 data; actual plan/activity remains SYS06.

## 8. Interactive Element and Invocation Contract

### LCMS-050 — InteractiveElementV1

```yaml
interactive_element:
  id: string
  capability_id: string
  semantic_primitive: ACTION|NAVIGATION|DISCLOSURE|INTERACTIVE_CONTENT|STATUS_FEEDBACK
  action_type: ASK_FOLLOW_UP|INSPECT_SOURCE|SUBMIT_ATTEMPT|REQUEST_HINT|REQUEST_EXPLANATION|START_ACTIVITY
  label: string
  command_contract_ref: string
  input_refs: [versioned_owner_ref]
  input_schema_ref: string
  expected_result_ref_types: [string]
  availability: AVAILABLE|UNAVAILABLE|STALE|COMPLETED
  reason_codes: [string]
  requires_idempotency_key: boolean
  risk: READ_ONLY|LOW_RISK_WRITE
```

Rules：

- `command_contract_ref` MUST be server allowlisted and versioned；model/block cannot name arbitrary tool；
- dependent owner refs stale/missing → capability `STALE|UNAVAILABLE`；
- current availability is revalidated at invocation time；
- destructive/cross-boundary commands are out of scope；
- UI labels MAY localize, but cannot change action type/owner semantics。

### LCMS-051 — LearningInteractionInvocationV1

```yaml
interaction_invocation:
  schema_version: "1.0"
  interaction_id: uuid
  conversation_id: string
  message_id: string
  message_revision: integer
  block_id: string
  capability_id: string
  action_type: string
  expected_owner_versions: [versioned_owner_ref]
  user_response:
    payload: object|null
    accepted_response_ref: versioned_owner_ref|null
  idempotency_key: string
  requested_at: datetime
  correlation_id: string
```

`user_response.payload` is strict command input, not durable Message truth. After owner acceptance, durable identity is `accepted_response_ref` (e.g. Attempt/command receipt/transcript turn). Sensitive/raw response retention follows the target owner contract.

### LCMS-052 — LearningInteractionResultV1

```yaml
interaction_result:
  schema_version: "1.0"
  interaction_id: uuid
  status: ACCEPTED|SUCCEEDED|FAILED|CONFLICT|UNAVAILABLE
  owner_receipt_ref: versioned_owner_ref|null
  result_refs: [versioned_owner_ref]
  evaluation_result_ref: versioned_owner_ref|null
  next_transition:
    kind: REQUERY_OWNER|AWAIT_ASSESSMENT|REQUEST_NEW_TEACHING_DECISION|OPEN_SOURCE|NAVIGATE_ACTIVITY|NONE
    target_system: SYS01|SYS02|SYS03|SYS04|SYS05|SYS06|SYS07|SYS08|PLATFORM|null
    expected_ref_types: [string]
  error: stable_error|null
  correlation_id: string
```

`next_transition` is an application routing expectation, not authority to choose business outcome. Target owner still validates and decides.

### LCMS-053 — Action routing

| Action type | Application/owner path | Result | Forbidden shortcut |
|---|---|---|---|
| ASK_FOLLOW_UP | SYS08 canonical façade captures user turn → SYS05 new decision → SYS08 execution | new transcript/message + action refs | mutate old message/action |
| INSPECT_SOURCE | SYS01/SYS02 scoped read query | SourceSpan/material view ref | model-generated citation |
| REQUEST_HINT | SYS08 captures explicit request → SYS05 new action within policy | new TeachingAction/message | frontend raises hint level |
| REQUEST_EXPLANATION | same request/decision path | new TeachingAction/message | renderer directly answers outside envelope |
| SUBMIT_ATTEMPT | SYS04 SubmitAttempt/evaluate；then SYS03 evidence acceptance as separate owner flow | Attempt/AssessmentResult refs | client submits correctness/mastery |
| START_ACTIVITY | SYS06 StartLearningActivityV1 exact activity/version | lifecycle receipt/activity ref | UI creates review/apply activity |

### LCMS-054 — Stable errors

LCMS façade may add only these boundary errors；target owner stable errors MUST be preserved:

```text
MESSAGE_NOT_FOUND
MESSAGE_REVISION_CONFLICT
MESSAGE_BLOCK_NOT_FOUND
MESSAGE_CAPABILITY_NOT_FOUND
MESSAGE_CAPABILITY_UNAVAILABLE
MESSAGE_CAPABILITY_STALE
MESSAGE_CONTEXT_SCOPE_VIOLATION
MESSAGE_SCHEMA_UNSUPPORTED
MESSAGE_INTERACTION_INVALID
```

- schema/scope/version/business validation errors non-retryable without new input/ref；
- transient dependency errors MAY be retryable per `ERROR-*`；
- provider/render/ledger failure MUST NOT map to learner incorrect；
- duplicate idempotency key returns original receipt/result, not a second side effect。

## 9. Interaction State Model

### LCMS-060 — Workflow/message acceptance

```text
SYS08 WorkflowRun: pending → running → succeeded | failed | cancelled
                                  ↓ on validated success
LearningMessage: accepted immutable revision
```

Candidate/validation status belongs to WorkflowRun. Only accepted Message is exposed as durable transcript artifact. Failed candidate MUST NOT become a learner message or learner failure.

### LCMS-061 — Delivery and opening

```text
accepted → presented → opened
```

This is optional delivery/telemetry, not the Message's canonical learning lifecycle. Events MUST be idempotent if persisted and MUST NOT affect LearnerState/Mastery/Review/Teaching Policy alone.

### LCMS-062 — Frontend invocation state

```text
idle
→ submitting
→ succeeded | failed | conflict | unavailable
```

This state is transient UI state. `succeeded` requires owner receipt; stable business state must be re-read from owner. Reload MUST NOT restore success only from localStorage.

### LCMS-063 — Canonical owner lifecycles remain separate

```text
SYS06 LearningActivity: planned → available → active → completed/...
SYS04 Attempt: started → submitted → scored | scoring_failed/...
SYS04 AssessmentResult: immutable version chain
SYS03 LearnerEvidence: candidate → accepted/rejected → invalidated
SYS03 LearnerState/MasteryEstimate: immutable projection versions
SYS05 validation obligation: policy-controlled, satisfied by fresh refs
SYS07 ReviewSchedule: immutable version stream
```

### LCMS-064 — State impact matrix

| Input/state | LearnerState | MasteryEstimate | Memory Scheduling | Teaching Policy |
|---|---:|---:|---:|---:|
| message accepted/presented/opened | No | No | No | No |
| copy/hover/disclosure/time/turn count | No | No | No | No |
| explicit request for hint/explanation | No direct write | No | No | Yes, as structured request input only |
| Attempt accepted | via later evidence | via later evidence | only if valid retrieval observation | Yes, material context |
| AssessmentResult | via SYS03 acceptance | via SYS03 acceptance | may be SYS07 input | Yes, material context |
| LearnerEvidence accepted | Yes via SYS03 projection | Yes | may be validated observation source | Yes via exact state/evidence refs |
| ReviewSchedule update | No | No | Yes, SYS07 | read-only review context |
| Activity completed | No automatic | No automatic | No automatic | may be activity/context change, not mastery |

## 10. Teaching System Boundary

### LCMS-070 — Responsibility matrix

| System | Decides/owns | Message System may do | Must not do |
|---|---|---|---|
| Content Understanding / SYS01 | published knowledge/source/provenance | cite exact refs | publish knowledge from block text |
| Retrieval / SYS02 | EvidenceBundle selection within scope/envelope | render learner-visible evidence | expand exposure or fabricate source |
| Learner Modeling / SYS03 | evidence acceptance、MasteryEstimate、LearnerState | present exact read refs | infer/update mastery from interaction |
| Teaching Strategy / SYS05 | TeachingAction、stage、hint/exposure、validation obligation | render action/capabilities/reasons | choose strategy/next move in UI |
| Assessment / SYS04 | item、Attempt、AssessmentResult、diagnosis、actual assistance | submit response and render exact result | score/diagnose locally |
| Memory / SYS07 | ReviewSchedule、retrievability、next_due | present due/schedule refs | create/update schedule from block click |
| Learning Planner / SYS06 | Goal/Objectives/Plan/Activity/order/lifecycle | render/start exact activity | create/reorder activity locally |
| Conversation Orchestration / SYS08 | workflow/model/tool execution、accepted Message、trace hosting | validate/render/dispatch | own SYS01～SYS07 decisions |

### LCMS-071 — Four key questions

```text
教什么
→ SYS06 Objective / LearningActivity + SYS01 knowledge boundary

为什么现在教
→ SYS06 plan/activity reason + SYS05 TeachingAction/DecisionTrace
  (SYS07 supplies due context, not plan decision)

如何评价
→ SYS04 Attempt/AssessmentResult/diagnosis
→ SYS03 evidence acceptance/mastery projection

如何展示
→ SYS08 accepted Message/Blocks within TeachingAction/EvidenceBundle envelope
→ frontend typed safe renderer
```

## 11. Frontend Component Boundary

### LCMS-080 — Component hierarchy

```text
ConversationView
├── ConversationStateFeedback
└── MessageRenderer
    ├── MessageFallback
    └── BlockRenderer
        ├── ExplanationBlockComponent
        ├── KnowledgeBlockComponent
        ├── EvidenceBlockComponent
        ├── LearningActivityBlockComponent
        ├── FeedbackBlockComponent
        ├── ReviewApplyBlockComponent
        └── InteractiveElementRenderer
            └── CapabilityDispatchAdapter
```

### LCMS-081 — Stable vs extensible

Stable：

- Conversation ordering/virtualization and history cursor；
- Message fallback/security boundary；
- Block discriminated-union dispatcher；
- safe Markdown/math/citation renderer；
- Interactive Element semantic primitive mapping；
- capability dispatch/error/single-flight adapter。

Extensible：

- block payload presentation variants；
- additive minor fields；
- new capability only after owner command/ADR/Spec is frozen；
- new block major/minor only under schema-versioning rules。

### LCMS-082 — Forbidden frontend logic

Frontend components/store MUST NOT contain：

- StrategyFamily/TeachingStage/TeachingAction selection；
- hint/exposure escalation rules；
- assessment scoring/diagnosis；
- evidence eligibility/mastery thresholds；
- next_due/review scheduling；
- LearningActivity creation/order/next selection；
- success derived from DOM/local state；
- arbitrary command/tool name execution；
- current owner state reconstructed from message prose。

### LCMS-083 — Accessibility and interaction

- pointer/keyboard/touch equivalent paths；
- semantic primitives/ARIA role/state match；
- focus returns after disclosure/modal；
- single-flight/disabled blocks duplicate invocation；
- errors announced without replacing learner result；
- hover-only actions forbidden；
- raw HTML/MDX/script/dynamic imports/unsafe URL/remote tracking media forbidden。

## 12. Transport and Compatibility

### LCMS-090 — Additive transport

Existing canonical LearningActivity transcript/teaching response MAY additive return:

```yaml
message_envelope: LearningMessageV1|null
```

Existing `reply_text` / `message.content` remains REQUIRED fallback during migration. This Spec does not authorize changing existing endpoint identity or inventing a generic cross-owner HTTP router; transport MUST call the same canonical application façade.

### LCMS-091 — Normal/history/stream equivalence

HTTP normal response、history query、SSE final/run-completed and reconnect replay MUST return the same accepted Message id/revision/blocks/refs. Structured blocks MUST only be published after full validation; partial JSON MUST NOT execute/render.

### LCMS-092 — RenderPayloadV1 compatibility

`RenderPayloadV1` remains unchanged. Deterministic adapter mapping：

| V1 source | LCMS target | Interaction |
|---|---|---|
| markdown | EXPLANATION | none unless exact owner capability separately exists |
| card/concept | KNOWLEDGE/PRESENTATION_ONLY | none |
| card/source | EVIDENCE/PARTIAL if SourceSpan missing | INSPECT only with exact ref |
| card/question | LEARNING_ACTIVITY/PARTIAL | no SUBMIT without exact activity/action/item refs |
| card/feedback | FEEDBACK/NON_ASSESSMENT unless exact result ref exists | none by default |
| citations | EVIDENCE | INSPECT only with valid SourceSpan |

Adapter MUST NOT invent knowledge, TeachingAction, AssessmentResult, ReviewSchedule or capability.

### LCMS-093 — Unknown/invalid payload

Unknown major、unknown block、extra executable fields、invalid refs、limits violation or validation failure → discard structured payload and render mandatory content fallback. This is not learner failure.

## 13. Persistence, Migration and Retirement

### LCMS-100 — Domain first

This Spec defines Domain/Public contracts, not tables. Storage mapping MUST preserve：

- SYS08 ownership；
- immutable accepted message revision；
- exact transcript/activity/owner refs；
- one accepted envelope per message revision；
- idempotent replay；
- owner-safe erasure/no resurrection。

### LCMS-101 — Migration sequence

```text
strict contracts + validators + deterministic adapters
→ canonical new writer emits LearningMessageV1
→ history/normal/SSE read same accepted envelope
→ frontend switches to MessageRenderer/BlockRenderer
→ capabilities wired one owner port at a time
→ legacy adapters audited
→ old canonical-path dual writer retired
```

No online LLM backfill. No bulk rewrite required for historical plain text.

### LCMS-102 — Retirement conditions

Legacy canonical-path dual protocol MAY retire only when：

1. all canonical LearningActivity new writes emit MessageV1；
2. normal/history/SSE/refresh equivalence tests pass；
3. plain/RenderPayload legacy adapters cover retained history；
4. no production UI depends on legacy action fields (`strategy`, integer `hint_level`, frontend inferred next action)；
5. rollback/fallback has been verified；
6. legacy Dialog remains explicitly compatibility-only or is separately retired。

### LCMS-103 — Rollback/forward-fix

Rollback MAY stop sending structured envelope and use mandatory content fallback. It MUST NOT restore frontend assessment/next-action/review success logic. Accepted envelopes remain readable. Public schema semantic defects require new minor/major or forward-fix, never silent reinterpretation of `1.0`.

## 14. Security and Privacy

### LCMS-110

- model/document/user text/block payload untrusted；
- strict block/capability allowlists；
- no arbitrary URL/tool/component/command；
- http/https links only under existing renderer contract；remote image/file/data/javascript blocked；
- grader-only/rubric/answer-only structurally isolated；
- Prompt Injection cannot modify owner refs/capabilities/policy/tool permission；
- current Workspace hard scope for message, source, activity and command；
- logs/traces minimize content and exclude secret/raw unnecessary Prompt；
- provider/render/system failure never becomes learner failure。

## 15. Observability

### LCMS-120

At minimum record/reference：

- message id/revision/schema/compatibility source；
- block types and validation outcome, not full sensitive body by default；
- capability id/action/availability/reason；
- invocation correlation/idempotency/owner receipt/error；
- exact activity/action/bundle/attempt/result refs when present；
- fallback/adapter/replay mode；
- no raw secret/grader-only/full unrelated material。

Telemetry such as opened/copy/hover/turn count is process/UX telemetry only and MUST NOT be labeled Learning Evidence.

## 16. Testing Requirements

### LCMS-130 — L0 Architecture

Tests MUST prove：

- Message/UI/renderer cannot write SYS03～SYS07 repositories；
- no Teaching Policy/scoring/mastery/review rules in frontend components；
- capability allowlist does not expose arbitrary command/tool；
- Conversation/Message not registered as LearningEvidence/Mastery owner；
- RenderPayloadV1 semantics unchanged。

### LCMS-131 — L1/L2 Schema and Component

Cover：

- strict six-block discriminated union；
- required metadata/ref/availability；
- unknown major/type/extra executable fields；
- size/count/unique id limits；
- each block renderer and content fallback；
- interaction accessible state/single-flight/error；
- malicious Markdown/HTML/URL/command payload。

### LCMS-132 — L2/L3 Contract and Integration

Cover：

- exact owner refs and Workspace fail-closed；
- idempotent capability invocation/receipt replay；
- stale version/conflict/error mapping；
- ASK/REQUEST creates new SYS05 decision path, not old action mutation；
- SUBMIT_ATTEMPT produces SYS04 refs, not direct mastery；
- START_ACTIVITY only exact SYS06 ref；
- Feedback uses exact result or non-assessment label；
- review/apply cannot create schedule/activity locally；
- normal/history/SSE/reconnect equivalence；
- persistence/restart/erasure behavior when storage mapping is implemented。

### LCMS-133 — L4 E2E

At least one canonical LearningActivity E2E MUST demonstrate：

```text
owner-selected LearningActivity/TeachingAction
→ SYS08 accepted Message with typed blocks
→ learner invokes allowed capability
→ owner command/receipt/result refs
→ refreshed history shows same accepted envelope
→ no duplicate message/Attempt/event on retry
```

Real-model E2E is required only for claims that model-backed Message generation is connected；Mock remains valid for deterministic schema/component/owner tests.

### LCMS-134 — Educational/Policy tests

- message opened/read/like/copy does not update learner state；
- Feedback is backed by exact SYS04 result or labeled non-assessment；
- assisted/answer-exposed actual state remains traceable and cannot be presented as independent mastery；
- validation obligation is not completed by chat continuation/time/UI click；
- review/apply activity completion alone does not imply mastery；
- UI cannot expand SYS05 exposure envelope。

## 17. Acceptance Criteria

### Functional

- `LCMS-AC-001`：canonical assistant Message renders mandatory content fallback and ordered typed blocks correctly。
- `LCMS-AC-002`：six block types are strict, explainable and extensible only through schema governance。
- `LCMS-AC-003`：every interactive action is traceable from message/block/capability to owner receipt/result/correlation。
- `LCMS-AC-004`：normal/history/SSE/reconnect return the same accepted Message revision without duplicate side effects。
- `LCMS-AC-005`：invalid/unknown/legacy payload fails safely to readable content。

### Educational

- `LCMS-AC-010`：only structured Attempt→AssessmentResult→LearnerEvidence path can influence LearnerState/mastery。
- `LCMS-AC-011`：Feedback is not mere untyped generated text when assessment claims are shown；it references exact SYS04 result。
- `LCMS-AC-012`：actual assistance/exposure is preserved and answer-exposed/assisted success is not shown as independent mastery。
- `LCMS-AC-013`：review/apply blocks create an opportunity by starting exact activity；they do not themselves prove retention/transfer。
- `LCMS-AC-014`：opened/read/copy/turn count is never accepted as mastery evidence。

### Architecture / Ownership

- `LCMS-AC-020`：Message System does not decide TeachingAction, LearningPlan, AssessmentResult, MasteryEstimate or ReviewSchedule。
- `LCMS-AC-021`：UI/renderer contains no teaching, scoring, mastery or scheduling rules and no arbitrary command router。
- `LCMS-AC-022`：all cross-system fields retain exact owner/source/version/availability/freshness refs；no second truth。
- `LCMS-AC-023`：RenderPayloadV1 remains non-interactive；new LCMS schema is versioned and fallback-compatible。
- `LCMS-AC-024`：legacy Dialog/RenderPayload adapters are bounded, no permanent dual writer, with retirement conditions。

### Security / Quality

- `LCMS-AC-030`：untrusted Markdown/block/model content cannot execute HTML/MDX/script/component/tool/command or leak grader-only/secret content。
- `LCMS-AC-031`：scope/version/idempotency/conflict/error semantics are machine-verifiable。
- `LCMS-AC-032`：provider/render/ledger failure does not create learner failure/evidence/mastery/review state。
- `LCMS-AC-033`：Engineering、Policy-Ownership、Learning Evidence results are reported separately。

## 18. Forbidden Implementations

禁止：

- Message JSON 同时拥有 TeachingAction/Assessment/Mastery/ReviewSchedule/UI truth；
- frontend `partial/correct` switch selects retry/test/apply；
- local `reviewAdded=true` or DOM insertion claims owner success；
- generic `ReviewItem` without owner contract；
- Block/Card carries arbitrary tool/command/URL/component；
- `opened/read/like/copy` updates mastery；
- FeedbackBlock contains `mastered=true`；
- Review/Apply block writes next_due/plan/activity；
- model text invents source/AssessmentResult/next action；
- historical message online LLM backfill；
- same `RenderPayloadV1 1.0` silently gains executable semantics；
- UI localStorage/React state becomes durable interaction/business truth；
- duplicate capability invocation creates second Attempt/Evidence/activity transition；
- renderer or SYS08 expands TeachingAction exposure envelope。

## 19. Explicit Deferred Items

The following are non-blocking, explicitly deferred：

- UserNote `CAPTURE_NOTE` capability and TextRangeAnchor conflict/recovery contract；
- exact SQLite mapping/migration/index；
- media/visualization-specific block family；
- branch conversation/tree editing；
- generic plugin-defined blocks/actions；
- learning-effect claim beyond existing gate。

Any future addition MUST follow Product/Design/ADR/Spec governance and cannot be inferred from Prototype UI.

**Spec Freeze Result：FROZEN / PASS. Implementation remains governed by the LCMS Vertical Slice and EXEC-075.**
