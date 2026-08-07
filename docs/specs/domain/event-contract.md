# Askora Learning Event Contract

> Spec ID 范围：`EVENT-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Event Semantics

### EVENT-001 — Command / Event / Projection Separation

- Command：希望系统执行的动作；
- Event：已发生且被系统接纳的事实；
- Projection：由事件/证据计算得到的状态。

Event MUST 使用过去时事实语义，MUST NOT 表示“希望发生什么”。

### EVENT-002 — Immutable Event

已持久化 LearningEvent MUST append-only；业务纠正通过 correction/invalidation event，MUST NOT 原地重写历史。

### EVENT-003 — Ledger Hosting != Business Ownership

SYS08 MAY 托管 Event Ledger，但 payload 业务语义由对应领域 owner 定义。托管权 MUST NOT 被实现为重新解释领域结论或第二 truth owner。

## 2. LearningEvent Envelope

```yaml
learning_event:
  event_id: uuid
  event_type: string
  schema_version: string
  aggregate_type: string
  aggregate_id: uuid|string
  aggregate_version: integer
  sequence: integer
  occurred_at: datetime
  recorded_at: datetime
  idempotency_key: string
  correlation_id: uuid|string
  causation_id: uuid|string|null
  actor: object
  context: object
  producer_system: SYS01|SYS02|SYS03|SYS04|SYS05|SYS06|SYS07|SYS08
  payload: object
  provenance:
    source: string
    model_provider: string|null
    model_name: string|null
    model_snapshot: string|null
    prompt_id: string|null
    prompt_version: string|null
    policy_version: string|null
    policy_bundle_ref: versioned_ref|null
    projection_version: string|null
    algorithm_version: string|null
  trace: object
  privacy: object
```

## 3. Existing Envelope Constraints Retained

### EVENT-010

`event_id` MUST 全局唯一。

### EVENT-011

同一 aggregate 内 `(aggregate_id, aggregate_version)` MUST 唯一且 version 单调递增。

### EVENT-012

`sequence` 表示 aggregate/stream logical order。实现 MUST NOT 假设跨 aggregate 有全局严格时序。

### EVENT-013

`occurred_at` 与 `recorded_at` MUST 分离，不得混用。

### EVENT-014

`idempotency_key` MUST 在 command 幂等范围唯一。重复同一用户动作 MUST 返回原/等价结果，不产生第二份学习证据。

### EVENT-015

`correlation_id` MUST 串联一次业务 workflow/teaching round；`causation_id` SHOULD 指向直接 command/event/decision。

### EVENT-016

事件正文 SHOULD 使用假名化标识，MUST NOT 无必要写 password、secret、完整凭据或多余 PII。

### EVENT-017

关键 event 若由模型/算法参与且影响 mastery/plan/assessment/policy，相关 model/prompt/policy/algorithm versions MUST 可追溯。缺必要 version 时，不得成为无条件高权 evidence。

## 4. Existing Canonical Event Families Retained

### EVENT-020 — Goal / Plan

至少支持 `GoalCreated`、`GoalConfirmed`、`PlanCreated`、`PlanReplanned`、`ActivitySelected`，由 SYS06 定义 payload 语义。

### EVENT-021 — Content / Retrieval

至少支持 `ContentImported`、`ContentPublished`、`KnowledgeRelationPublished`、`ContentRetrieved`、`RetrievalFailed`，分别由 SYS01/SYS02 定义 payload 语义。

### EVENT-022 — Teaching Execution

至少支持：

- `PolicyDecisionMade` / `TeachingActionDecided`：action ref、DecisionTrace ref、TeachingContext ref/fingerprint、PolicyBundle ref/hash、StrategyFamily、TeachingStage、reason codes；
- `EngineTransitioned`；
- `ExplanationPresented`；
- `HintRequested`；
- `HintPresented`；
- `AnswerExposed`；
- `ReflectionRecorded`。

`HintPresented`/support events 的 canonical payload MUST 使用：

```text
scaffold_control
hint_specificity
answer_exposure
interaction_move
support_reason
delivery_mode
```

旧 `hint_level/exposure_level` MAY 仅 legacy metadata/read-upcast，MUST NOT 继续作为 v0.3 canonical truth。

### EVENT-023 — Assessment / Evidence

至少支持 `DiagnosticStarted`、`AssessmentAttemptStarted`、`ResponseSubmitted`、`ResponseRevised`、`AssessmentResultProduced/AttemptScored`、`DiagnosisProduced/DiagnosisUncertain`、`EvidenceAccepted`、`EvidenceRejected`、`MisconceptionDetected`、`MasteryProjectionUpdated`、`TransferAttemptCompleted`。

AssessmentResult/Diagnosis event MUST 能表达 `assessment_confidence` 与独立的 `diagnostic_confidence`，并允许 ErrorType `UNKNOWN`。

### EVENT-024 — Review

至少支持 `ReviewScheduled`、`ReviewCompleted`、`ReviewScheduleUpdated`。ReviewCompleted MUST 引用 actual Attempt/AssessmentResult/assistance facts，而不是只引用计划状态。

## 5. Existing Payload Rules Retained

### EVENT-030 — Minimal Facts, Not Full State Copy

Event payload SHOULD 保存 replay/audit 所需最小事实/引用，MUST NOT 无限制复制整个 LearnerState、文档或 Prompt。

### EVENT-031 — Stable References for Large Objects

原始回答、文档片段、模型输出过大时 MAY 保存稳定 content ref/hash，但在 retention policy 内必须可审计。

### EVENT-032 — Assistance Frozen at Attempt Time

`ResponseSubmitted` MUST 能还原提交时 actual assistance：

```text
assistance_state = INDEPENDENT|ASSISTED|ANSWER_EXPOSED
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

MUST NOT 在评分后根据当前 UI 或 planned TeachingAction 猜历史帮助程度。

## 6. Persistence / Delivery

### EVENT-040 — Transactional Outbox

Domain state update 与需传播 event/outbox MUST 在相应 persistence transaction contract 下原子写入。

### EVENT-041 — At-least-once

Consumers MUST 按 at-least-once delivery 设计，projection/side-effect consumer MUST idempotent。

### EVENT-042 — Failure Classification

Transient infrastructure error MAY retry/backoff；schema/business validation error MUST NOT blind retry；unrecoverable poison event MUST 进入 dead-letter/review 并保留诊断。

### EVENT-043 — Late Events

不得假设事件永不迟到。Late but valid evidence MAY 触发局部 replay/reprojection。

## 7. Schema Evolution

### EVENT-050

`schema_version` 使用明确版本治理；minor/additive change MUST backward compatible。

### EVENT-051

删除字段、改变字段/enum 语义等 breaking change MUST 新 major/versioned migration/upcaster strategy。

### EVENT-052

Consumer MUST 声明支持版本范围。未知 major/enum MUST NOT 被静默解释为当前语义。

## 8. Replay

### EVENT-060

固定 event set + fixed projection/algorithm version MUST 得到 deterministic projection。

### EVENT-061

Replay MUST NOT 调用在线 LLM 或依赖当前 provider 重建历史判断。历史 LLM 结论必须使用已持久化结构化 result/inference；新模型重评必须显式 reassessment/recompute 并创建新版本。

### EVENT-062

Algorithm upgrade MUST 支持 old log + old projector = old state；old log + new projector = candidate state；compare → approved migration。

## 9. Correction / Deletion

### EVENT-070

普通错误修正 MUST 追加 correction/invalidation event，不修改原 event row。

### EVENT-071

用户/法律删除要求下，MUST 删除受保护内容，在允许范围保留不含被删数据的 audit tombstone，并重建受影响 projection；不得继续引用已删除 evidence。

## 10. Legacy Event Naming

### EVENT-080

旧 dotted event names 迁移时 MUST adapter 到 canonical names，MUST NOT 长期维护两套语义相同 event names。

## 11. v0.3 Adaptive Teaching Additions

### EVENT-200 — TeachingActionDecided Detail

Teaching decision event MUST 引用 action、DecisionTrace、TeachingContext/context_fingerprint、PolicyBundle/hash、StrategyFamily、TeachingStage、validation obligation、ExperimentAssignment（如有）。

### EVENT-201 — Actual Support / Exposure

Support/exposure event MUST 使用 v0.3 orthogonal vocabulary，并能关联 rendered response/Attempt。Legacy integer support only audit/read。

### EVENT-202 — Assessment Diagnosis Detail

Assessment/diagnosis event MUST 支持 canonical ErrorType 7 + UNKNOWN、assessment confidence、diagnostic confidence、alternative hypotheses、needs_probe、diagnostic evidence refs。

### EVENT-203 — Independent Validation Obligation

SYS05 MAY 记录 `IndependentValidationRequired` / `IndependentValidationSatisfied` policy-control event。`Satisfied` MUST 引用 fresh independent Attempt/AssessmentResult evidence；MUST NOT 因计划已创建、聊天继续或时间经过自动满足。

### EVENT-210 — OutcomeObserved

OutcomeObservation MAY 发布 `OutcomeObserved`：至少引用 outcome id/version、measurement ref、independence/assistance、delay/transfer、score/success、contamination、attribution_scope、episode/trajectory/experiment refs。MUST NOT 回写 DecisionTrace。

### EVENT-211 — ExperimentAssigned

ExperimentAssignment event MUST 使用 `assignment_probability`，MUST NOT 命名/解释为 action propensity。

### EVENT-220 — Additive Record Ownership

OutcomeObservation/ExperimentAssignment MAY 由 durable ledger 托管，但 MUST NOT 接管八系统既有 domain truth ownership。

### EVENT-230 — Legacy Ambiguity

旧 support/error/propensity payload 无法无损映射时 MUST 保留 raw legacy value + migration reason，并把 canonical value 标记 unknown/unavailable/partial replay；MUST NOT 猜测。

### EVENT-231 — v0.3 Policy Replay

Policy replay MUST 使用 event-time exact object/policy versions；缺失版本必须 PARTIAL/NON_REPLAYABLE。MUST NOT 调用在线 LLM。

## 12. Acceptance Criteria

原有 AC 保留并按 v0.3 assistance fields 更新：

- `EVENT-AC-001`：重复 idempotency key 不产生第二 Attempt/Evidence。
- `EVENT-AC-002`：同 aggregate version 冲突由唯一约束拒绝。
- `EVENT-AC-003`：固定 event set 可重放得到相同 projection content。
- `EVENT-AC-004`：replay 不发起在线模型请求。
- `EVENT-AC-005`：domain state + outbox 具备原子性。
- `EVENT-AC-006`：ANSWER_EXPOSED ResponseSubmitted 可在历史事件稳定识别。
- `EVENT-AC-007`：未知 major schema version 不被静默接纳。

新增 v0.3 AC：

- `EVENT-AC-201`：Hint/Exposure/Attempt events 不依赖 canonical integer support 字段。
- `EVENT-AC-202`：Diagnosis events 可表达 UNKNOWN 与独立 confidence。
- `EVENT-AC-203`：validation satisfaction 可追溯 fresh independent evidence。
- `EVENT-AC-204`：ExperimentAssigned probability 与 action propensity 不混用。
- `EVENT-AC-205`：OutcomeObserved 不修改 DecisionTrace。

## 13. Forbidden Implementations

禁止：修改旧 event row；聊天消息表替代 event ledger；non-idempotent consumer 重复 mastery/review；policy replay 重新调用 LLM；完整用户文档复制进每个 payload；重复 EvidenceAccepted；仅记录 correct 而不记录 actual assistance/exposure；ledger host 取得 domain ownership；unknown diagnosis 强制分类；assignment probability 写成 action propensity；Outcome event 改写 DecisionTrace。