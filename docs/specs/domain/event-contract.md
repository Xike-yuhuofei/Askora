# Askora Learning Event Contract

> Spec ID 范围：`EVENT-*`  
> 状态：Canonical Implementation Contract  
> 版本：v1.0

## 1. 事件语义

### EVENT-001：Command、Event、Projection 必须分离

- **Command**：希望系统执行的动作，例如 `SubmitResponse`；
- **Event**：已经发生且被系统接纳的事实，例如 `ResponseSubmitted`；
- **Projection**：由事件计算得到的状态，例如 `MasteryEstimate`。

Event MUST 使用过去时语义，MUST NOT 表示“希望发生什么”。

### EVENT-002：LearningEvent 是不可变事实

已持久化事件禁止原地修改。业务纠正通过追加 correction event 处理；投影再根据新事件重建。

### EVENT-003：事件不是业务状态 owner

Event Ledger 由 4.8 托管持久化，但事件内容的业务语义由对应领域系统产生。4.8 不得借托管账本重新解释领域结论。

## 2. `LearningEventEnvelope v1`

```yaml
learning_event:
  event_id: uuid
  event_type: string
  schema_version: "1.0"

  aggregate_type: string
  aggregate_id: uuid|string
  aggregate_version: integer
  sequence: integer

  occurred_at: datetime
  recorded_at: datetime
  idempotency_key: string
  correlation_id: uuid
  causation_id: uuid|null

  actor:
    actor_type: learner|system|model|reviewer
    actor_id: string
    device_id: string|null

  context:
    user_id: uuid
    session_id: uuid|null
    goal_id: uuid|null
    knowledge_unit_ids: [uuid]
    assessment_attempt_id: uuid|null
    content_revision_ids: [uuid]

  payload: object

  provenance:
    source: ui|api|orchestrator|worker|migration|domain
    model_provider: string|null
    model_name: string|null
    model_snapshot: string|null
    prompt_id: string|null
    prompt_version: string|null
    policy_version: string|null
    projection_version: string|null
    algorithm_version: string|null

  trace:
    trace_id: string
    span_id: string|null

  privacy:
    classification: public|personal|sensitive
    external_processing: boolean
    retention_class: core_learning|diagnostic|temporary
```

## 3. 字段约束

### EVENT-010

`event_id` MUST 全局唯一。

### EVENT-011

同一 aggregate 内 `(aggregate_id, aggregate_version)` MUST 唯一且 `aggregate_version` 单调递增。

### EVENT-012

`sequence` 表示该 aggregate 或事件流中的逻辑顺序。实现不得假设跨 aggregate 存在全局严格时序。

### EVENT-013

`occurred_at` 表示事实实际发生时间；`recorded_at` 表示系统接纳并持久化时间。两者不得混用。

### EVENT-014

`idempotency_key` MUST 在命令定义的幂等范围内唯一。重复提交同一用户动作 MUST 返回原结果或等价结果，不产生第二份学习证据。

### EVENT-015

`correlation_id` MUST 串联一次业务工作流/教学轮次；`causation_id` SHOULD 指向直接导致该事件的 command/event/decision。

### EVENT-016

事件正文 SHOULD 使用假名化标识，MUST NOT 无必要写入密码、密钥、完整外部模型凭据或多余 PII。

### EVENT-017

如果某关键事件由模型参与生成、评分或分类，且后续会影响掌握、计划或评估，相关 `model/prompt/policy/algorithm` 版本 MUST 可追溯。缺少必要版本信息时，该结果不得成为高权关键 evidence。

## 4. v1 必须支持的事件

### EVENT-020：目标与计划

| Event | Owner | 最小 Payload |
|---|---|---|
| `GoalCreated` | 4.6 | goal_id, goal_version, success_criteria, deadline/time_budget |
| `GoalConfirmed` | 4.6 | goal_id, version, confirmation_source |
| `PlanCreated` | 4.6 | plan_id, version, learner_state_version, graph_version |
| `PlanReplanned` | 4.6 | old_plan_version, new_plan_version, trigger_reason_codes |
| `ActivitySelected` | 4.6 | activity_id, objective_id, reason_codes |

### EVENT-021：内容与检索

| Event | Owner | 最小 Payload |
|---|---|---|
| `ContentImported` | 4.1 | document_id, revision_id, checksum, media_type |
| `ContentPublished` | 4.1 | document_id, revision_id, knowledge_model_version |
| `KnowledgeRelationPublished` | 4.1 | relation_id, revision, evidence_span_ids |
| `ContentRetrieved` | 4.2 | request_id, bundle_id, retrieval_trace_id, index_versions |
| `RetrievalFailed` | 4.2 | request_id, reason_code, missing_roles/conflicts |

### EVENT-022：教学执行

| Event | Owner | 最小 Payload |
|---|---|---|
| `PolicyDecisionMade` | 4.5 | action_id, strategy_version, decision_id, reason_codes |
| `EngineTransitioned` | 4.8 | from_step/engine, to_step/engine, reason_code |
| `ExplanationPresented` | 4.8 | action_id, response_id, evidence_bundle_id|null |
| `HintRequested` | 4.8 | action_id, previous_attempt_id|null, requested_level|null |
| `HintPresented` | 4.8 | action_id, hint_level, exposure_level, response_id |
| `ReflectionRecorded` | 4.8 | activity_id, reflection_id |

### EVENT-023：评估与证据

| Event | Owner | 最小 Payload |
|---|---|---|
| `DiagnosticStarted` | 4.4 | objective_ids, blueprint_version |
| `AssessmentAttemptStarted` | 4.4 | attempt_id, item_id, item_version, assessment_type |
| `ResponseSubmitted` | 4.4 | attempt_id, assistance_snapshot, response_hash/reference |
| `ResponseRevised` | 4.4 | attempt_id, revision_count, parent_response_reference |
| `AttemptScored` | 4.4 | result_id, result_version, score, correctness, confidence |
| `EvidenceAccepted` | 4.3 | learner_evidence_id, source_result_id, weight, dimension |
| `EvidenceRejected` | 4.3 | source_result_id, rejection_reason_codes |
| `MisconceptionDetected` | 4.4 | misconception_id, result_id, evidence_confidence |
| `MasteryProjectionUpdated` | 4.3 | estimate_id, old_version|null, new_version, algorithm_version |
| `TransferAttemptCompleted` | 4.4 | attempt_id, result_id, novelty, independence |

### EVENT-024：复习

| Event | Owner | 最小 Payload |
|---|---|---|
| `ReviewScheduled` | 4.7 | schedule_id, version, next_due_at, model_version |
| `ReviewCompleted` | 4.7/由4.8采集行为后4.7接纳 | schedule_id, attempt/result references, actual_completed_at |
| `ReviewScheduleUpdated` | 4.7 | old_version, new_version, reason_codes |

## 5. Payload 原则

### EVENT-030：事件记录事实，不复制全状态

事件 payload SHOULD 保存重建与审计所需最小事实/引用，不应把整个 LearnerState、整个文档或整个模型 Prompt 无限制复制到每个事件。

### EVENT-031：大对象使用稳定引用

原始回答、文档片段、模型输出过大时，可以保存稳定 content reference/hash，但必须保证在其 retention policy 内可审计。

### EVENT-032：帮助状态必须在作答事实中冻结

`ResponseSubmitted` 必须能还原提交时的：

- max hint level；
- assistance class；
- source visible；
- answer visible。

不得在评分后根据当前 UI 状态猜测历史帮助程度。

## 6. 持久化与投递

### EVENT-040：Transactional Outbox

领域状态更新与需要传播的事件/outbox MUST 在同一数据库事务内写入。

### EVENT-041：At-least-once

事件消费者 MUST 按至少一次交付设计。所有投影器和 side-effect consumer MUST 幂等。

### EVENT-042：失败分类

- transient infrastructure error：可重试并指数退避；
- schema/business validation error：不得盲重试；
- unrecoverable poison event：进入 dead-letter/review 状态并保留诊断信息。

### EVENT-043：迟到事件

不得假设事件永不迟到。迟到但有效的证据 MAY 触发受影响 aggregate/knowledge unit 的局部 replay/reprojection。

## 7. Schema 演进

### EVENT-050

`schema_version` 使用 major.minor。minor 只允许向后兼容 additive change。

### EVENT-051

删除字段、改变字段语义、改变枚举含义等破坏性变化 MUST 新增 major version，并提供 upcaster/migration strategy。

### EVENT-052

消费者 MUST 明确声明支持版本范围。不得静默把未知字段/未知主版本解释成现有语义。

## 8. Replay

### EVENT-060

固定事件集合 + 固定 projection/algorithm version MUST 得到确定性业务投影。

### EVENT-061

Replay MUST NOT 调用在线 LLM 或依赖当前供应商返回重新生成历史判断。

若历史业务结论依赖 LLM，必须使用已持久化的结构化 AssessmentResult/ModelInference 输出；若要用新模型重评，必须启动显式 `reassessment/recompute` 流程并创建新结果版本。

### EVENT-062

算法升级必须允许：

```text
old event log
→ old projector = old state
old event log
→ new projector = candidate new state
→ compare
→ approved migration
```

## 9. Correction 与删除

### EVENT-070

普通错误修正 MUST 追加 correction/invalidation event，而不是修改原事件。

### EVENT-071

若因用户明确删除或法律要求必须删除事件内容：

- 删除受保护内容；
- 在允许范围内保留不可逆/不含被删数据的审计墓碑；
- 重建受影响 projection；
- 不得继续引用已删除 evidence。

## 10. Legacy 映射

### EVENT-080

旧代码若使用 dotted event names（如 `question.answered`），迁移时必须通过 adapter 映射到本合同的 PascalCase canonical event，不得长期同时维护两套语义相同事件名。

## 11. Acceptance Criteria

- `EVENT-AC-001`：重复提交同一 idempotency key 不产生第二个 Attempt/Evidence。
- `EVENT-AC-002`：同一 aggregate version 冲突由唯一约束拒绝。
- `EVENT-AC-003`：固定事件集可重放得到相同 MasteryEstimate 内容。
- `EVENT-AC-004`：replay 不发起任何在线模型请求。
- `EVENT-AC-005`：领域状态写入与 outbox 记录具备原子性。
- `EVENT-AC-006`：答案已暴露的 ResponseSubmitted 能在历史事件中稳定识别。
- `EVENT-AC-007`：未知 major schema version 不会被消费者静默接纳。

## 12. Forbidden Implementations

禁止：

- 修改旧 event row 来“修正历史”；
- 用聊天消息表替代 LearningEvent ledger；
- event consumer 非幂等地产生重复 mastery/review 更新；
- replay 时重新调用 LLM；
- 把完整用户文档复制进每个事件 payload；
- 同一用户点击重复产生多份 EvidenceAccepted；
- 仅记录 `correct=true` 而不记录当时提示/答案暴露状态。
