# Learning Event Contract

> Spec ID：`EVENT-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Semantics

LearningEvent = 已发生且被系统接纳的不可变事实。事件账本托管 MAY 在 SYS08，但 payload 语义与验证仍由对应 domain owner 定义；ledger hosting MUST NOT 形成第二 truth owner。

### EVENT-001

关键学习状态变化 MUST 可追溯到 immutable event/evidence；聊天文本、LLM shared context 或 UI cache MUST NOT 直接替代 canonical event/evidence chain。

## 2. Envelope

```yaml
learning_event:
  event_id: uuid
  event_type: string
  event_schema_version: string
  occurred_at: datetime
  recorded_at: datetime
  aggregate_type: string|null
  aggregate_id: string|null
  aggregate_version: integer|string|null
  user_id: uuid|null
  session_id: uuid|null
  correlation_id: uuid|string|null
  causation_id: uuid|string|null
  idempotency_key: string|null
  producer_system: SYS01|SYS02|SYS03|SYS04|SYS05|SYS06|SYS07|SYS08
  payload: object
  provenance_refs: [versioned_ref]
```

### EVENT-010

Event MUST append-only。更正通过 superseding/correction event 或对应 domain revision 完成，MUST NOT 原地重写历史事实。

## 3. v0.3 Teaching / Assessment Events

### EVENT-200 — TeachingActionDecided

至少携带：TeachingAction ref、DecisionTrace ref、TeachingContext ref/fingerprint、PolicyBundle ref/hash、StrategyFamily、TeachingStage、validation obligation、experiment assignment ref（如有）。

### EVENT-201 — Support Presented / Experienced

`HintPresented`、`ExplanationPresented`、`WorkedExamplePresented`、`AnswerExposed` 或等价 event MUST 使用 canonical assistance vocabulary：

```text
scaffold_control
hint_specificity
answer_exposure
InteractionMove
support_reason
delivery_mode
```

历史整数 `hint_level/scaffold_level/exposure_level` MAY 保留在 legacy metadata，但 MUST NOT 继续作为 v0.3 canonical payload truth。

### EVENT-202 — ResponseSubmitted

ResponseSubmitted/AttemptCreated MUST 引用实际 assistance snapshot：

```text
assistance_state = INDEPENDENT|ASSISTED|ANSWER_EXPOSED
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

不得只从计划 TeachingAction envelope 推断实际经历。

### EVENT-203 — AssessmentResultProduced

至少引用 AssessmentResult version、score/correctness、`assessment_confidence` 与 diagnosis ref/fields。`diagnostic_confidence` MUST 与 assessment confidence 独立。

### EVENT-204 — DiagnosisProduced / Uncertain

Canonical ErrorType 仅允许：

```text
KNOWLEDGE_GAP
CONCEPTUAL_MISCONCEPTION
METHOD_SELECTION
EXECUTION
RETRIEVAL_FAILURE
TRANSFER_FAILURE
EXPRESSION_FORMAT
UNKNOWN
```

UNKNOWN/low confidence/needs_probe MUST 可显式进入事件，不得强制猜具体 ErrorType。

### EVENT-205 — Validation Obligation

SYS05 MAY 记录 `IndependentValidationRequired` / `IndependentValidationSatisfied` policy-control event。`Satisfied` MUST 引用 fresh independent Attempt/AssessmentResult evidence；MUST NOT 因计划已创建或时间经过自动触发。

## 4. Outcome / Experiment Events

### EVENT-210 — OutcomeObserved

OutcomeObservation 创建时 MAY 发布 `OutcomeObserved`，payload 至少引用 outcome id/version、measurement ref、independence/assistance、delay/transfer、score/success、contamination、attribution_scope、episode/trajectory/experiment refs。

Outcome event MUST NOT 回写修改 historical DecisionTrace。

### EVENT-211 — ExperimentAssigned

ExperimentAssignment event MUST 明确 `assignment_probability`。该字段 MUST NOT 命名/解释为 action propensity。

## 5. Ownership Routing

```text
Knowledge/modeling facts      → SYS01 events
EvidenceBundle retrieval       → SYS02 events
LearnerEvidence/state update   → SYS03 events
Attempt/Assessment/Diagnosis   → SYS04 events
TeachingAction/policy control  → SYS05 events
Plan/activity                  → SYS06 events
Review schedule                → SYS07 events
Execution/model/tool/ledger    → SYS08 events
```

### EVENT-220

OutcomeObservation/ExperimentAssignment 作为 additive analytics/experiment contract MAY 由 durable ledger 托管，但 MUST NOT 接管上述八系统的 domain truth ownership。

## 6. Idempotency / Ordering

### EVENT-020

同一 idempotency key 的 domain command MUST NOT 产生多个语义重复事件。

### EVENT-021

需要 aggregate ordering 的 consumer MUST 使用 aggregate version/event sequence，而不是仅依赖 wall-clock timestamp。

### EVENT-022

At-least-once delivery consumer MUST idempotent；outbox retry MUST NOT 导致 mastery/action/plan/review 双写。

## 7. Versioning / Replay

### EVENT-030

Event schema evolution MUST 遵循 versioned reader/upcaster contract。Upcaster MAY 补结构，不得伪造历史不可知语义。

### EVENT-200A — Legacy Ambiguity Rule

旧 support/error/propensity payload 无法无损映射时 MUST 保留 raw legacy value + migration reason，并把 canonical value 标记为 unknown/unavailable/partial replay，而不是猜测。

### EVENT-201A — Replay

Historical replay MUST 使用 event-time object/policy versions；缺失版本时必须显式 PARTIAL/NON_REPLAYABLE。Policy replay MUST NOT 重新调用在线 LLM。

## 8. Security / Privacy

Event payload MUST 最小化敏感数据；raw prompts、完整文档、密钥、无需长期保存的用户文本 MUST NOT 因审计方便无限复制。引用优先于重复全文。

## 9. Tests

必须覆盖：event append-only/idempotency/outbox retry；canonical support vocabulary；actual assistance captured；UNKNOWN diagnosis；assessment vs diagnostic confidence；validation satisfied requires fresh independent evidence；assignment probability naming；Outcome 不修改 DecisionTrace；legacy ambiguous upcast；replay missing version status。

## 10. Acceptance Criteria

- `EVENT-AC-201`：v0.3 Hint/Exposure/Attempt events 不依赖 canonical integer hint/exposure 字段。
- `EVENT-AC-202`：AssessmentResult/Diagnosis events 可表达 UNKNOWN 与独立 confidence。
- `EVENT-AC-203`：validation obligation satisfaction 可追溯 fresh independent evidence。
- `EVENT-AC-204`：ExperimentAssigned 的 probability 与 action propensity 不混用。
- `EVENT-AC-205`：OutcomeObserved 不修改 DecisionTrace。

## 11. Legacy Mapping

旧 `HintPresented.hint_level/exposure_level`、ResponseSubmitted 的旧 assistance class、历史 ErrorType 与 `experiment.propensity` 只允许 read/upcast/audit。canonical writer MUST 只写 v0.3 fields；无法确定语义时保留 uncertainty + migration reason + replayability status。

## 12. Forbidden Implementations

禁止：

- event ledger host 取得所有 domain ownership；
- missing assistance 默认 independent；
- 继续把 L0-L4/int hint/exposure 作为 canonical event truth；
- unknown diagnosis 被强制分类；
- experiment assignment probability 写成 action propensity；
- Outcome event 改写历史 DecisionTrace；
- replay 用当前 mutable state 或在线 LLM 补历史缺失。