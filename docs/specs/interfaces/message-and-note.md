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

---

## Askora UserNote and Source Inspection Contract

> Spec ID：`UNSI-*`
> 状态：**Canonical Implementation Contract / FROZEN**
> 版本：v1.0
> 冻结日期：2026-08-11
> Governing：Product Definition、ADR-0021
> Implementation sequence：EXEC-076 Backend Foundation → EXEC-070 Frontend Right Rail

### 1. Scope and Authority

本合同冻结 EXEC-070 所需的两个技术边界：

1. Workspace-scoped durable `UserNote` 的 owner、query、save/version/conflict/recovery/data-control；
2. citation/view-source 使用 exact Material/MaterialRevision/SourceSpan refs 打开 Current Material 的 read-only source-inspection handoff。

本合同不新增 Product Capability，不改变 SYS01～SYS08 Learning Core ownership，不实现 global notes library，不启用 `CAPTURE_NOTE`，不修改 Teaching Policy、Assessment、Mastery、Review 或 Learning Evidence semantics。

### 2. Ownership

#### UNSI-001 — UserNote single writer

`UserNote`、`UserNoteVersion`、`UserNoteRecoveryDraft` 与 save/recovery receipt 的唯一 writer 是 **Platform Workspace Notes**。

API handler、query assembler、frontend store、LCMS/SYS08、SYS01/SYS02 与 local browser storage MUST NOT 写第二份 current UserNote truth。

#### UNSI-002 — Source single writer

Material content semantics、MaterialRevision 与 SourceSpan 的唯一 writer仍为 SYS01。SYS02 只拥有 EvidenceBundle/RetrievalTrace。Source-inspection query 只读组合，不创建/修正/回填 source truth。

#### UNSI-003 — Workspace scope

所有 UserNote 与 source inspection 必须解析 current LocalOwner + current `workspace_id`。`owner_id` 相同不得替代 workspace filter。foreign 与 missing resource 对 caller 保持不可枚举。

### 3. Common Public References

#### UNSI-010 — Exact owner ref

本合同复用 LCMS `VersionedOwnerRefV1` 语义：

```yaml
versioned_owner_ref:
  source_system: SYS01|SYS02|SYS05|SYS06|PLATFORM
  entity_type: string
  entity_id: string
  version: string|integer
  workspace_id: uuid
  availability: READY|MISSING|STALE
```

`READY` 必须有 exact entity id/version/workspace。客户端不得把 nullable id、display label、filename、route 或 current mutable state转换为 READY ref。

#### UNSI-011 — Source inspection ref

```yaml
SourceInspectionRefV1:
  schema_version: "1.0"
  material_ref: versioned_owner_ref       # entity_type=Material
  material_revision_ref: versioned_owner_ref # entity_type=MaterialRevision
  source_span_ref: versioned_owner_ref|null   # entity_type=SourceSpan
```

三个 ref 如同时存在，MUST 属于同一 Workspace、同一 Material lineage与 exact revision。`source_span_ref=null` 只能表示没有可定位 SourceSpan，不能由客户端猜一个 current span。

### 4. UserNote Domain Contract

#### UNSI-020 — UserNoteV1

```yaml
UserNoteV1:
  schema_version: "1.0"
  note_ref: versioned_owner_ref           # PLATFORM/UserNote
  note_id: uuid
  workspace_id: uuid
  anchor: UserNoteAnchorV1
  content_markdown: string                # 0..65536 UTF-8 characters
  version: integer                        # >= 1
  created_at: datetime
  updated_at: datetime
  unresolved_recovery_ref: versioned_owner_ref|null
```

`content_markdown` 是 user-authored content；空内容 MAY durable 保存，但不得被解释为不存在或自动删除。Renderer 使用 safe Markdown/plain-text allowlist，禁止 raw HTML/MDX/script/dynamic component。

#### UNSI-021 — UserNoteAnchorV1

```yaml
UserNoteAnchorV1:
  schema_version: "1.0"
  kind: LEARNING_ACTIVITY|STAGE|MATERIAL|SOURCE_SPAN|FREE
  anchor_ref: versioned_owner_ref|null
  source_ref: SourceInspectionRefV1|null
```

合法组合：

| kind | required | forbidden |
|---|---|---|
| `LEARNING_ACTIVITY` | exact SYS06 LearningActivity `anchor_ref` | `source_ref` |
| `STAGE` | exact SYS05 TeachingAction `anchor_ref` | `source_ref` |
| `MATERIAL` | `source_ref.material_ref`；revision/span MAY null only through a Material-only form | unrelated `anchor_ref` |
| `SOURCE_SPAN` | exact Material + MaterialRevision + SourceSpan `source_ref` | unrelated `anchor_ref` |
| `FREE` | no owner/source ref | any ref |

Material-only anchor的 wire representation使用 `SourceInspectionRefV1` 的 material ref，并以 explicit null revision/span compatibility shape由 strict validator约束；实现不得用 fake revision/version 填空。若实现选择独立 `MaterialAnchorV1` discriminated subtype，公共语义不变。

创建后 anchor identity immutable。未来 re-anchor 必须是独立 command/version，不得由普通 save/autosave 隐式改变。

#### UNSI-022 — Query

```text
GET /api/v1/workspace/user-notes
  ?anchor_kind=<required>
  &anchor_id=<required except FREE>
  &anchor_version=<required for versioned anchor>
  &material_id=<required for MATERIAL/SOURCE_SPAN>
  &revision_id=<required for SOURCE_SPAN>
  &source_span_id=<required for SOURCE_SPAN>
  &cursor=<optional>
  &limit=<optional, 1..50>
```

返回 `UserNoteListResponseV1`：strict 1.0 envelope、current Workspace、exact normalized anchor、稳定 `(updated_at desc, note_id asc)` ordering、cursor 与 0..N `UserNoteV1`。Query MUST NOT 跨 anchor/global Workspace 聚合；`FREE` 只查询 current Workspace FREE notes。

```text
GET /api/v1/workspace/user-notes/{note_id}
```

返回 exact current note与 unresolved recovery ref；foreign/missing 使用同一 not-found外观。两类 query 均 `Cache-Control: private, no-store`、side-effect free、no LLM。

### 5. Save, Version and Idempotency

#### UNSI-030 — SaveUserNoteV1

```text
PUT /api/v1/workspace/user-notes/{note_id}
```

```yaml
SaveUserNoteV1:
  schema_version: "1.0"
  workspace_id: uuid
  anchor: UserNoteAnchorV1
  content_markdown: string
  expected_version: integer               # create=0, update>=1
  idempotency_key: string
```

Rules：

- `note_id` 由 client 预先生成并保持稳定；
- create 仅允许不存在 note + `expected_version=0`；
- update 必须匹配 current exact version、Workspace 与 immutable anchor；
- accepted save 在一个 SQLite transaction 中 append `UserNoteVersion`、更新 current aggregate并保存 receipt；
- version 每次 semantic content change +1；相同 idempotency key/payload返回原 result，不增加 version；
- 相同 idempotency key但 payload不同返回 non-retryable conflict；
- 禁止 HTTP timestamp/updated_at/client clock/last-write-wins 决定胜者。

#### UNSI-031 — UserNoteSaveResultV1

```yaml
UserNoteSaveResultV1:
  schema_version: "1.0"
  status: CREATED|UPDATED|ALREADY_APPLIED
  note: UserNoteV1
  receipt_ref: versioned_owner_ref        # PLATFORM/UserNoteSaveReceipt
  correlation_id: string
```

只有收到该 durable owner result（或随后 query 得到同一/更新 exact note ref）才能显示 `SAVED`。Transport 200/204、local debounce completion 或 browser state mutation都不是保存证据。

#### UNSI-032 — Autosave ordering

同一 note autosave必须 single-flight：

```text
dirty(vN)
→ SAVING(expected=N)
→ owner result vN+1
→ SAVED(vN+1)
```

若请求期间产生较新 draft，frontend 保留 dirty generation，在前一请求完成后以返回 version 提交下一次；不得并发发送两个相同 expected version后让最后到达者获胜。Retry 必须复用原 idempotency key；内容变化创建新 key。

### 6. Conflict and Recovery

#### UNSI-040 — Durable conflict result

expected version不匹配时 owner MUST：

1. 不修改 current UserNote；
2. 幂等持久化 submitted content 为 `UserNoteRecoveryDraftV1`；
3. 返回 HTTP 409 + `USER_NOTE_VERSION_CONFLICT`；
4. 在 typed `error.details` 返回 `UserNoteConflictV1`。

```yaml
UserNoteConflictV1:
  schema_version: "1.0"
  current_note: UserNoteV1
  submitted_expected_version: integer
  recovery_ref: versioned_owner_ref       # PLATFORM/UserNoteRecoveryDraft
  correlation_id: string
```

#### UNSI-041 — Recovery draft

```yaml
UserNoteRecoveryDraftV1:
  schema_version: "1.0"
  recovery_ref: versioned_owner_ref
  note_id: uuid
  workspace_id: uuid
  anchor: UserNoteAnchorV1
  submitted_content_markdown: string
  submitted_expected_version: integer
  status: UNRESOLVED|RESOLVED_KEEP_CURRENT|RESOLVED_REPLACED|RESOLVED_MERGED|ERASED
  created_at: datetime
  resolved_at: datetime|null
```

Recovery draft 是 durable user content，但不是 current note。Restart/refresh 后 query 必须能恢复 unresolved draft；backup/export/erasure 与 note content使用同等保护。

#### UNSI-042 — ResolveUserNoteRecoveryV1

```text
POST /api/v1/workspace/user-notes/{note_id}/recoveries/{recovery_id}/resolve
```

```yaml
ResolveUserNoteRecoveryV1:
  schema_version: "1.0"
  workspace_id: uuid
  action: KEEP_CURRENT|REPLACE_WITH_DRAFT|SAVE_MERGED
  expected_current_version: integer
  merged_content_markdown: string|null
  idempotency_key: string
```

- `KEEP_CURRENT` 要求 merged content null，只解决 recovery；
- `REPLACE_WITH_DRAFT` 使用 recovery content，merged content null；
- `SAVE_MERGED` 必须提供用户确认后的 merged content；
- replace/merge追加新 note version并返回 durable receipt；
- current version再次变化返回409，recovery仍 unresolved；
- owner不得自动选择、自动 merge 或静默丢弃任何一侧。

#### UNSI-043 — UI state truth

| UI state | Required evidence |
|---|---|
| `SAVING` | one owner request in flight |
| `SAVED` | durable owner receipt/exact returned note ref |
| `FAILED` | no accepted owner receipt；dirty input retained in current UI process |
| `CONFLICT` | typed 409 + current note + durable recovery ref |
| `RECOVERABLE` | owner query reports unresolved durable recovery draft |

Local Server unavailable cannot create durable recovery and MUST remain `FAILED`。Before rail unmount、route/Workspace switch或已知 destructive navigation，dirty failed input必须显式 block/confirm并提供 copy；不得静默 discard，也不得把 browser persistence称为 durable recovery。

### 7. Source Inspection

#### UNSI-050 — SourceInspectionQueryV1

```text
GET /api/v1/workspace/source-inspections
  ?material_id=<required UUID>
  &revision_id=<required UUID>
  &source_span_id=<optional UUID>
```

Server 从 current Workspace context解析 scope，再调用 SYS01 exact read port。API/query layer不得直接从 Message prose、filename、summary、vector index或 current revision猜测 source。

#### UNSI-051 — SourceInspectionResponseV1

```yaml
SourceInspectionResponseV1:
  schema_version: "1.0"
  generated_at: datetime
  data:
    view_state: READY|MISSING|STALE
    workspace_ref: versioned_owner_ref
    source_ref: SourceInspectionRefV1
    document_ref: versioned_owner_ref|null # compatibility/audit only
    source_label: string
    locator:
      page: integer|null
      chapter: string|null
      node_id: uuid|null
      start_offset: integer|null
      end_offset: integer|null
      anchor_version: string|null
    excerpt: string|null                   # <= 8192, exact canonical source text only
    is_current_revision: boolean
    reason_codes: [string]
  source_status: [source_status_v1]
  correlation_id: string
```

Response `private, no-store`，不得含 managed/absolute path、完整非必要资料、Prompt、grader-only或secret。

#### UNSI-052 — READY / MISSING / STALE

- `READY`：Material、exact revision、exact span关系一致，span可回放；`excerpt`与locator来自该 exact canonical span。历史 accepted revision只要仍可回放也可 READY，且 `is_current_revision=false`；
- `MISSING`：source_span_id 未提供，或 current-Workspace Material已验证但 requested span/source content缺失/已擦除；`excerpt=null`，不得 fallback；
- `STALE`：refs存在但 anchor invalidated、locator replay失败或一致性不能证明；不得显示为 READY，也不得改查 current revision。

Material/revision不属于 current Workspace、Material不存在、或 lineage不一致时，统一返回404 `SOURCE_INSPECTION_NOT_FOUND`。不得通过不同 code/message/timing/details枚举 foreign对象。

#### UNSI-053 — Side effects and fallback

Source inspection：

- MUST side-effect free、no business write、no LLM、no online historical backfill；
- MUST NOT create Activity/TeachingAction/Attempt/Evidence/UserNote；
- MUST NOT use global Material fallback、similar-title fallback、first span、current revision或message excerpt冒充 exact source；
- refresh/retry可重复执行且不产生新事实。

### 8. LCMS Citation / View-source Handoff

#### UNSI-060 — Capability issuance

AVAILABLE `INSPECT_SOURCE` 只可出现在 learner-visible block，且 `input_refs` 至少包含同一 Workspace的 exact：

```text
SYS02 EvidenceBundle
SYS01 Material
SYS01 MaterialRevision
SYS01 SourceSpan
```

缺任一 exact ref、legacy citation、stale ref或非 learner-visible evidence时，capability必须 `UNAVAILABLE|STALE`。`command_contract_ref` 继续使用 LearningMessage 1.0 已发布的 `SYS02.InspectSourceV1`；它是 read handoff contract，不是 SYS02 source ownership。

#### UNSI-061 — Invocation result

LCMS invocation必须重验 message/block/capability/version/current Workspace与全部 source refs。成功返回：

```yaml
LearningInteractionResultV1:
  status: SUCCEEDED
  result_refs: [Material, MaterialRevision, SourceSpan]
  next_transition:
    kind: OPEN_SOURCE
    target_system: SYS01
    expected_ref_types: [Material, MaterialRevision, SourceSpan]
```

Frontend 只使用 result refs 调用 `SourceInspectionQueryV1` 并打开 Current Material。它不得从 capability label、block excerpt或旧 citation重建 refs。

#### UNSI-062 — No CAPTURE_NOTE implication

本合同不向 LearningMessage V1 action enum增加 `CAPTURE_NOTE`，也不允许 source-to-note快捷动作绕过 `SaveUserNoteV1`。未来 capability需独立 schema/version/confirmation contract。

### 9. Persistence, Backup, Export and Erasure

#### UNSI-070 — SQLite durable mapping

实现至少表达：

```text
user_notes                  # current aggregate/scope/anchor/current_version
user_note_versions          # immutable content versions
user_note_command_receipts  # idempotency/result
user_note_recovery_drafts   # unresolved/resolved durable user content
```

实际 table/class名 MAY 符合仓库命名，但语义必须分离。`workspace_id`直接持久化；`(note_id, version)`、command idempotency scope、一个 recovery id的resolution必须唯一。Foreign key/index/transaction在 SQLite production-local path生效。

#### UNSI-071 — Backup and export

- Recovery Package的 consistent SQLite snapshot包含全部 UserNote/version/receipt/recovery records；
- User Data Export `LEARNING_RECORDS` 使用显式 allowlist导出 note id/workspace/anchor/content/version/timestamps与 unresolved recovery content；
- export不得含内部 path、receipt payload internals、Prompt、secret或其他 Workspace数据；
- restore后 unresolved recovery仍可查询，且不得绕过 erasure checkpoint复活已删 note。

#### UNSI-072 — Erasure and Material deletion

- `LEARNING_RECORDS` 与 `ALL_PERSONAL_DATA` erasure处理 UserNote current/version/recovery content；
- Material/Document permanent delete默认保留用户笔记正文，MATERIAL/SOURCE_SPAN anchor变为 `MISSING`/invalidated；preview/report必须计数并说明；
- owner-safe erasure之外不得跨表 hard delete UserNote；
- deleted note/recovery content不得通过 backup、receipt、projection、message或online LLM恢复。

### 10. Stable Errors

#### UNSI-080 — Error catalog

```text
USER_NOTE_NOT_FOUND
USER_NOTE_CONTENT_INVALID
USER_NOTE_ANCHOR_INVALID
USER_NOTE_VERSION_CONFLICT
USER_NOTE_IDEMPOTENCY_CONFLICT
USER_NOTE_RECOVERY_NOT_FOUND
USER_NOTE_RECOVERY_VERSION_CONFLICT
USER_NOTE_DEPENDENCY_UNAVAILABLE
SOURCE_INSPECTION_NOT_FOUND
SOURCE_INSPECTION_REF_INVALID
SOURCE_INSPECTION_UNAVAILABLE
```

Mapping：

- invalid content/anchor/ref → validation 400/422，non-retryable without new input；
- missing/foreign note/source → same not-found 404 appearance；
- version/idempotency/recovery current-version mismatch → conflict 409，non-retryable without requery/user choice；
- temporary database/local dependency failure → dependency/transient 503，MAY retry with same idempotency key；
- `MISSING/STALE` 是成功 read view state，不得机械映射成 transport error。

Error/details/log不得泄露 foreign ref、note/source content（typed conflict current/recovery payload除外且仅 current Workspace）、absolute path、Prompt、secret或grader-only。

### 11. Security and Caching

#### UNSI-090

所有 endpoints `Cache-Control: private, no-store`。Frontend cache key必须至少包含 current owner/workspace、note/source exact ref与schema version；Workspace切换时清除/隔离旧 cache和dirty presentation state。

#### UNSI-091

UserNote/recovery/source excerpt均视为 private local user content。Telemetry/log/audit只记录 opaque refs、version、size、reason/error/correlation，不记录正文。

#### UNSI-092

Source/Note Markdown与locator是untrusted display input；必须使用 typed renderer/escaping。禁止 raw HTML/MDX/script、dynamic component、local file URL、remote tracking image与arbitrary command。

### 12. Tests

#### UNSI-100 — Contract/unit

覆盖 strict schema、unknown fields/major、anchor discriminators、size limits、exact refs、stable errors、safe rendering、idempotency与version uniqueness。

#### UNSI-101 — UserNote integration

覆盖 create/update/requery、single-flight ordering oracle、duplicate replay、409 no-overwrite、durable recovery after restart、keep/replace/merge、second conflict、server unavailable、Workspace switch isolation、foreign/missing indistinguishable。

#### UNSI-102 — Source inspection integration

覆盖 citation/view-source handoff、exact historical revision、locator/excerpt、missing span、stale anchor、trashed/deleted source、foreign Workspace fail closed、no current/global/filename/summary fallback、no write/no LLM。

#### UNSI-103 — Data lifecycle

覆盖 fresh/current Alembic upgrade + single head/check、Recovery Package restore、export allowlist、LEARNING_RECORDS/ALL_PERSONAL_DATA erasure、Material deletion anchor invalidation、no resurrection与privacy registry completeness。

### 13. Acceptance Criteria

- `UNSI-AC-001`：Platform Workspace Notes是 UserNote/recovery唯一 writer；SYS01仍是 MaterialRevision/SourceSpan唯一 writer。
- `UNSI-AC-002`：UserNote是 stable-id、Workspace-scoped、anchored、append-version durable object；frontend/browser storage无第二 truth。
- `UNSI-AC-003`：create/update/idempotency/single-flight owner receipt语义完整，未持久化不显示 SAVED。
- `UNSI-AC-004`：409不覆盖 current，recovery draft durable，keep/replace/merge显式且可重启恢复。
- `UNSI-AC-005`：SourceInspection exact refs返回 READY/MISSING/STALE；无 filename/summary/current/global fallback。
- `UNSI-AC-006`：citation/view-source只从 exact LCMS refs进入 `OPEN_SOURCE`，cross-Workspace fail closed。
- `UNSI-AC-007`：backup/export/erasure/material-delete/no-resurrection覆盖 UserNote与recovery content。
- `UNSI-AC-008`：public schema/error/cache/privacy/security contracts与SQLite production-local gates PASS。

### 14. Forbidden Implementations

禁止：

- frontend/localStorage/sessionStorage/IndexedDB持久化 canonical note；
- mock save/recovery显示成功；
- last-write-wins、timestamp winner、silent overwrite/merge；
- recovery draft只存在browser memory却显示 RECOVERABLE；
- global notes library或跨 Workspace note aggregation；
- Message/SYS08/SYS01写 UserNote；
- Message excerpt/citation payload成为 Material/SourceSpan truth；
- source missing/stale时回退 filename、summary、current revision、first span、相似 Material或其他 Workspace；
- source inspection调用LLM或产生业务写入；
- Material delete静默删除 UserNote正文；
- 新增 `CAPTURE_NOTE`、generic command router、backend schema或migration而不经过 EXEC-076 gates。
