# Askora Canonical Domain Model

> Spec ID 范围：`DOMAIN-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 目的

本文件定义八类技术系统跨边界共享的最小领域语义。系统内部可以有额外私有对象，但不得复制、改变或模糊这些公共对象的含义。

## 2. 通用规则

### DOMAIN-001：Stable Identity + Immutable Revision

具有长期引用价值的对象 SHOULD 使用：

```text
stable_id + immutable revision/version
```

内容变化时优先生成新 revision，而不是覆盖旧记录。

### DOMAIN-002：Provenance First

任何影响教学、评估、掌握或引用的对象 MUST 能追溯来源、算法/模型版本与创建上下文。

### DOMAIN-003：事实、推断与决策必须可区分

公共对象字段或 metadata MUST 能区分：

- user fact；
- source fact；
- system inference；
- policy decision；
- generated content；
- human review。

### DOMAIN-004：时间使用带时区 datetime

持久化时间 MUST 使用带时区 UTC 或明确 offset 的时间戳。业务展示层可转换本地时区。

## 3. LearningGoal

**Owner**：4.6 Learning Planner。

```yaml
learning_goal:
  goal_id: uuid
  version: integer
  user_id: uuid
  title: string
  topic: string
  target_capabilities: [string]
  application_context: string|null
  success_criteria: [string]
  deadline_at: datetime|null
  weekly_time_budget_minutes: integer|null
  source_document_ids: [uuid]
  status: candidate|confirmed|active|achieved|paused|archived
  confirmed_by_user: boolean
  created_at: datetime
  supersedes_version: integer|null
```

### DOMAIN-010

LLM MAY 从自然语言生成 candidate，但 `confirmed|active` 的目标必须经过用户确认或显式产品规则确认。

## 4. LearningObjective

**Owner**：4.6。

```yaml
learning_objective:
  objective_id: uuid
  plan_id: uuid
  plan_version: integer
  knowledge_unit_ids: [uuid]
  capability: string
  cognitive_process: recall|understand|apply|transfer|explain
  success_criteria: [string]
  priority: float
  status: planned|active|satisfied|reopened|superseded
```

### DOMAIN-011

Objective 必须可被 4.4 通过一个或多个 AssessmentItem 测量，不能只是“了解”“熟悉”等不可验证描述。

## 5. SourceDocument / MaterialRevision

**Owner**：4.1。

```yaml
source_document:
  document_id: uuid
  canonical_title: string
  media_type: string
  current_revision_id: uuid
  status: imported|parsed|modeled|published|superseded|failed|quarantined

material_revision:
  revision_id: uuid
  document_id: uuid
  checksum: string
  source_uri: string|null
  parser_version: string
  extraction_version: string|null
  created_at: datetime
  supersedes_revision_id: uuid|null
```

### DOMAIN-020

原始文件改变、parser 产生语义性不同结果或安全修复要求重建内容时，必须形成可追踪 revision。

## 6. SourceSpan / SourceChunk

**Owner**：4.1。

```yaml
source_span:
  span_id: uuid
  revision_id: uuid
  node_id: uuid|null
  page: integer|null
  chapter: string|null
  start_offset: integer|null
  end_offset: integer|null
  text: string
  anchor_version: string

source_chunk:
  chunk_id: uuid
  revision_id: uuid
  segmentation_version: string
  source_span_ids: [uuid]
  text: string
  metadata: object
```

### DOMAIN-021

任何用户可见引用必须最终回到 `SourceSpan` 或等价稳定原文锚点。

### DOMAIN-022

SourceChunk 是可重建索引投影，不可作为长期知识身份。

## 7. KnowledgeUnit

**Owner**：4.1。

```yaml
knowledge_unit:
  knowledge_unit_id: uuid
  revision: integer
  kind: concept|fact|principle|procedure|method|representation|skill
  canonical_name: string
  description: string
  concept_ids: [uuid]
  evidence_span_ids: [uuid]
  provenance_type: source_explicit|system_inferred|human_curated
  confidence: float|null
  status: candidate|verified|published|rejected|superseded
```

### DOMAIN-030

已发布 KnowledgeUnit 必须有至少一个可回放来源证据，除非其 provenance 明确是用户/专家人工创建且产品允许无材料来源对象。

## 8. Concept

**Owner**：4.1。

```yaml
concept:
  concept_id: uuid
  revision: integer
  canonical_name: string
  aliases: [string]
  definition: string|null
  evidence_span_ids: [uuid]
  status: candidate|published|superseded
```

`KnowledgeMention` 属于 4.1 私有解析对象，不能与 canonical Concept 混用。

## 9. PrerequisiteRelation

**Owner**：4.1。

```yaml
prerequisite_relation:
  relation_id: uuid
  revision: integer
  prerequisite_id: uuid
  target_knowledge_unit_id: uuid
  strength: hard|soft|contextual
  evidence_span_ids: [uuid]
  inference_method: explicit|rule|model|human
  confidence: float|null
  status: candidate|published|rejected|superseded
```

### DOMAIN-040

章节先后顺序不得自动等同 hard prerequisite。

### DOMAIN-041

低置信推断关系不得自动提升为 hard prerequisite。

## 10. Misconception Definition

**Owner**：4.1。

```yaml
misconception:
  misconception_id: uuid
  revision: integer
  knowledge_unit_ids: [uuid]
  name: string
  description: string
  diagnostic_patterns: [object]
  evidence_span_ids: [uuid]
  status: candidate|published|retired
```

这是规范误区定义，不代表某用户实际存在该误区。

## 11. EvidenceBundle

**Owner**：4.2。

```yaml
evidence_bundle:
  bundle_id: uuid
  request_id: uuid
  teaching_action_id: uuid|null
  assessment_context_id: uuid|null
  source_scope: object
  index_versions: object
  items:
    - evidence_id: uuid
      source_span_ids: [uuid]
      knowledge_unit_ids: [uuid]
      pedagogical_role: definition|example|counterexample|prerequisite|hint|rubric|solution|context
      content: string
      relevance: float|null
      confidence: float|null
      exposure_level: 0|1|2|3|4
      allowed_use: learner_visible|grader_only|internal_only
  conflicts: [object]
  missing_roles: [string]
  bundle_confidence: float|null
  retrieval_trace_id: uuid
```

### DOMAIN-050

EvidenceBundle 必须执行 TeachingAction 的 `answer_exposure_max`。4.2 可以进一步收紧，不能放宽。

## 12. AssessmentItem

**Owner**：4.4。

```yaml
assessment_item:
  item_id: uuid
  item_version: string
  status: draft|reviewed|active|retired
  item_type: multiple_choice|numeric|short_answer|code|open_response
  stem: string
  options: [object]
  claims:
    - knowledge_unit_id: uuid
      weight: float
      cognitive_process: recall|apply|transfer|explain
  difficulty:
    source: expert|calibrated|generated
    value: float|null
    uncertainty: float|null
  scoring:
    method: exact|equivalence|tests|rubric|model_assisted
    answer_key: object|null
    rubric_id: uuid|null
    rubric_version: string|null
    max_score: float
  provenance:
    source_content_revision_ids: [uuid]
    author_type: human|model|imported
    generator_model: string|null
    generator_prompt_version: string|null
    reviewer: string|null
    reviewed_at: datetime|null
  exposure:
    exposure_count: integer
    last_exposed_at: datetime|null
    alternate_form_group: string|null
```

### DOMAIN-060

模型生成题默认 `draft`，通过可解性、答案一致性和安全检查后才能进入 `active`。

## 13. Attempt

**Owner**：4.4。

```yaml
attempt:
  attempt_id: uuid
  user_id: uuid
  session_id: uuid
  item_id: uuid
  item_version: string
  assessment_type: diagnostic|formative|summative|review|transfer
  started_at: datetime
  first_response_at: datetime|null
  submitted_at: datetime
  response_time_ms: integer
  raw_response: object
  normalized_response: object
  revision_count: integer
  assistance:
    class: none|metacognitive|conceptual|strategic|structural|partial_solution|full_solution|answer_exposed
    max_hint_level: integer
    hint_event_ids: [uuid]
    source_visible: boolean
    answer_visible: boolean
```

### DOMAIN-061

Attempt 必须记录帮助/答案暴露状态，否则不能可靠判断 evidence eligibility。

## 14. AssessmentResult

**Owner**：4.4。

```yaml
assessment_result:
  result_id: uuid
  result_version: integer
  attempt_id: uuid
  item_id: uuid
  item_version: string
  score: float
  passed: boolean|null
  correctness: correct|partial|incorrect|unscorable
  rubric_scores: object
  error_type: knowledge_gap|misconception|condition_omission|method_selection|execution|retrieval_failure|transfer_failure|expression_incomplete|metacognitive|unknown|null
  misconception_evidence: [object]
  independence: independent|assisted|answer_exposed
  assessment_confidence: float
  evaluator_versions: [string]
  reason_codes: [string]
  reviewer_result: accepted|rejected|needs_review
  created_at: datetime
  supersedes_result_id: uuid|null
```

### DOMAIN-070

AssessmentResult 不能包含 canonical `mastery_status` 作为最终裁决字段。

## 15. LearnerEvidence

**Owner of acceptance/projected use**：4.3；来源主要为 4.4 结果。

```yaml
learner_evidence:
  evidence_id: uuid
  user_id: uuid
  knowledge_unit_id: uuid
  attempt_id: uuid|null
  result_id: uuid|null
  accepted_at: datetime
  dimension: recall|routine_application|transfer|explanation
  outcome: success|partial|failure
  score: float
  confidence: float
  independence: independent|assisted|answer_exposed
  delay_seconds: integer
  novelty: repeated|near_variant|far_variant
  evidence_weight: float
  item_difficulty: float|null
  source_event_ids: [uuid]
  eligibility_reason_codes: [string]
```

### DOMAIN-071

完整答案已暴露、评分不可审计、版本不一致或重复提交的结果不得成为高权 mastery evidence。

## 16. MasteryEstimate

**Owner**：4.3。

```yaml
mastery_estimate:
  estimate_id: uuid
  version: integer
  user_id: uuid
  knowledge_unit_id: uuid
  competence_probability: float|null
  confidence: float
  independent_success_count: integer
  hint_dependency_score: float
  last_independent_success_at: datetime|null
  delayed_recall_evidence_count: integer
  transfer_evidence_count: integer
  active_misconception_ids: [uuid]
  evidence_count: integer
  effective_evidence_weight: float
  algorithm_id: string
  algorithm_version: string
  source_evidence_ids: [uuid]
  created_at: datetime
```

### DOMAIN-080

`competence_probability` 是模型估计，不是真实概率宣称；UI 展示必须配合 confidence/evidence。

### DOMAIN-081

稳定掌握与迁移掌握的产品标签必须由显式规则计算，至少考虑独立性、延迟证据、迁移证据和活跃误区，而不是只比较一个概率阈值。

## 17. LearnerState

**Owner**：4.3。

```yaml
learner_state:
  learner_state_id: uuid
  version: integer
  user_id: uuid
  mastery_estimate_ids: [uuid]
  active_misconception_hypotheses: [object]
  learning_stage_summary: object
  uncertainty_summary: object
  created_from_event_sequence: integer
  algorithm_bundle_version: string
  created_at: datetime
```

偏好、人格、语气等长期体验偏好不得混入 mastery 核心字段。

## 18. TeachingStrategy

**Owner**：4.5。

```yaml
teaching_strategy:
  strategy_id: string
  version: string
  family: direct_instruction|worked_example_fading|socratic_probing|guided_practice|error_remediation|retrieval_practice|productive_failure|transfer_challenge|metacognitive_reflection
  eligibility_rules: object
  default_constraints: object
  status: draft|active|retired
```

## 19. TeachingAction

**Owner**：4.5。

```yaml
teaching_action:
  action_id: uuid
  learning_objective_id: uuid
  learning_activity_id: uuid
  strategy_id: string
  strategy_version: string
  action_type: explain|worked_example|socratic_question|hint|practice|assessment|feedback|transfer_task|reflection
  scaffold_level: integer
  hint_level: integer
  answer_exposure_max: 0|1|2|3|4
  evidence_requirements: [string]
  expected_evidence_type: string|null
  success_condition: object
  failure_condition: object
  max_attempts: integer|null
  time_budget_seconds: integer|null
  reason_codes: [string]
  policy_version: string
  decision_id: uuid
```

### DOMAIN-090

4.8 必须执行该动作，不得把 `action_type` 改成另一教学语义；执行失败要返回 4.5 重新决策。

## 20. LearningActivity / LearningPlan

**Owner**：4.6。

```yaml
learning_activity:
  activity_id: uuid
  plan_id: uuid
  plan_version: integer
  objective_id: uuid
  type: learn_new|prerequisite_remediation|diagnostic|practice|delayed_review|transfer_check|metacognitive_review
  knowledge_unit_ids: [uuid]
  estimated_duration_minutes: integer
  priority: float
  reason_codes: [string]
  status: planned|available|active|completed|skipped|superseded

learning_plan:
  plan_id: uuid
  version: integer
  learning_goal_id: uuid
  planning_horizon: object
  objective_ids: [uuid]
  activity_ids: [uuid]
  constraints: object
  assumptions: object
  created_from_learner_state_version: integer
  knowledge_graph_version: string
  review_schedule_version: string|null
  reason_codes: [string]
  status: active|superseded|completed|paused
```

## 21. ReviewSchedule

**Owner**：4.7。

```yaml
review_schedule:
  schedule_id: uuid
  version: integer
  user_id: uuid
  knowledge_unit_id: uuid
  memory_model: string
  model_version: string
  difficulty: float|null
  stability: float|null
  retrievability: float|null
  desired_retention: float
  last_valid_retrieval_at: datetime|null
  next_due_at: datetime|null
  review_priority: float
  evidence_quality: float
  source_event_ids: [uuid]
  created_at: datetime
```

### DOMAIN-100

`next_due_at` 是 4.7 的推荐时点；4.6 决定它是否以及何时被纳入实际日计划。

## 22. ModelInference

**Owner**：4.8。

```yaml
model_inference:
  inference_id: uuid
  workflow_run_id: uuid
  task_type: string
  provider: string
  model_name: string
  model_snapshot: string|null
  prompt_id: string
  prompt_version: string
  input_hash: string
  output_schema_version: string|null
  latency_ms: integer
  token_usage: object
  cost: object|null
  validation_result_ids: [uuid]
  created_at: datetime
```

不得把敏感原始 prompt 全量复制到不可删除日志；按 privacy contract 存储必要审计内容。

## 23. FeedbackSignal

**Owner ledger**：4.8；由相应领域系统消费。

```yaml
feedback_signal:
  feedback_id: uuid
  user_id: uuid
  session_id: uuid|null
  target_type: teaching|assessment|learner_state|content|plan|experience
  target_id: uuid|string
  signal_type: thumbs_up|thumbs_down|incorrect|too_easy|too_hard|state_dispute|content_error|free_text
  payload: object
  created_at: datetime
```

### DOMAIN-110

体验反馈不得直接进入 mastery；需要 4.3 明确 evidence adapter 才可作为低权辅助信号。

## 24. DecisionTrace / LearningEvent

具体字段由：

- `domain/event-contract.md`
- `domain/decision-contract.md`

定义，本文件只固定其语义：

- LearningEvent = 已发生、被系统接纳的不可变事实；
- DecisionTrace = 关键系统决策的可审计记录；
- 两者都不是新的业务状态 owner。

## 25. Forbidden Domain Shortcuts

禁止创建以下长期公共对象：

- `TutorState`：同时塞入 mastery/plan/review/action；
- `AIJudgement`：同时承担评分与 mastery；
- `KnowledgeChunk`：既表示检索 chunk 又表示 canonical KnowledgeUnit；
- `UserSkillScore`：没有 evidence/version/algorithm provenance 的裸分数；
- `NextAction`：不区分 LearningActivity 与 TeachingAction；
- `MemoryScore`：既表示 retrievability 又表示完整掌握。
