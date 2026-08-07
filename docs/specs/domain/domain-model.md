# Askora Canonical Domain Model

> Spec ID 范围：`DOMAIN-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. 目的

本文件定义八类技术系统跨边界共享的最小领域语义。系统内部 MAY 有额外私有对象，但 MUST NOT 复制、改变或模糊这些公共对象的含义。

v0.3 对 Adaptive Teaching Loop 的 canonical truth 以本文件、`decision-contract.md` 与各系统 Spec 为准。历史 v0.2 字段只允许按 Legacy Mapping 读取，不得继续双写为第二 canonical truth。

## 2. 通用规则

### DOMAIN-001：Stable Identity + Immutable Revision

具有长期引用价值的对象 SHOULD 使用 `stable_id + immutable revision/version`。内容变化时 SHOULD 生成新 revision，而不是覆盖旧记录。

### DOMAIN-002：Provenance First

任何影响教学、评估、掌握或引用的对象 MUST 能追溯来源、算法/模型/PolicyBundle 版本与创建上下文。

### DOMAIN-003：事实、推断与决策必须可区分

公共对象字段或 metadata MUST 能区分：user fact、source fact、system inference、policy decision、generated content、human review。

### DOMAIN-004：时间

持久化时间 MUST 使用带时区 UTC 或明确 offset 的时间戳；展示层 MAY 转换本地时区。

### DOMAIN-005：Missing Semantics

需要表达输入可用性的公共字段/派生特征 MUST 使用：

```text
AVAILABLE
MISSING
STALE
LOW_CONFIDENCE
NOT_APPLICABLE
```

`MISSING` MUST NOT 用数值 `0`、空字符串或伪造默认值表示。

## 3. LearningGoal

**Owner**：SYS06 Learning Planner。

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

**Owner**：SYS06。

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

Objective MUST 可被 SYS04 通过一个或多个 AssessmentItem 测量，不能只使用“了解”“熟悉”等不可验证描述。

## 5. SourceDocument / MaterialRevision

**Owner**：SYS01。

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

原始文件改变、parser 产生语义性不同结果或安全修复要求重建内容时，MUST 形成可追踪 revision。

## 6. SourceSpan / SourceChunk

**Owner**：SYS01。

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

任何用户可见引用 MUST 最终回到 `SourceSpan` 或等价稳定原文锚点。

### DOMAIN-022

SourceChunk 是可重建索引投影，MUST NOT 作为长期知识身份。

## 7. KnowledgeUnit / Concept / Prerequisite / Misconception

**Owner**：SYS01。

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

concept:
  concept_id: uuid
  revision: integer
  canonical_name: string
  aliases: [string]
  definition: string|null
  evidence_span_ids: [uuid]
  status: candidate|published|superseded

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

### DOMAIN-030

已发布 KnowledgeUnit MUST 有至少一个可回放来源证据，除非 provenance 明确是用户/专家人工创建且产品允许无材料来源对象。

### DOMAIN-040

章节顺序 MUST NOT 自动等同 hard prerequisite；低置信推断关系 MUST NOT 自动提升为 hard prerequisite。

### DOMAIN-041

`Misconception` 是 SYS01 的规范定义，不代表某学习者存在该误区。`MisconceptionEvidence` 由 SYS04 产生，`MisconceptionHypothesis` 由 SYS03 拥有，remediation decision 由 SYS05 拥有。

## 8. EvidenceBundle

**Owner**：SYS02。

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
      answer_exposure: NONE|PARTIAL|COMPLETE
      allowed_use: learner_visible|grader_only|internal_only
  conflicts: [object]
  missing_roles: [string]
  bundle_confidence: float|null
  retrieval_trace_id: uuid
```

### DOMAIN-050 — v0.3 Exposure Envelope

EvidenceBundle MUST 执行 TeachingAction 的 `answer_exposure` 上限。SYS02 MAY 进一步收紧，MUST NOT 放宽。历史 `exposure_level: 0..4` 只允许兼容读取并映射到 v0.3 `answer_exposure`，不得继续作为 canonical 写入字段。

## 9. AssessmentItem

**Owner**：SYS04。

```yaml
assessment_item:
  item_id: uuid
  item_version: string
  status: draft|reviewed|active|retired
  item_type: multiple_choice|numeric|short_answer|code|open_response
  stem: string
  options: [object]
  claims: [object]
  difficulty: object
  scoring: object
  provenance: object
  exposure: object
```

### DOMAIN-060

模型生成题默认 `draft`，通过可解性、答案一致性和安全检查后才能进入 `active`。

## 10. Assistance / Support Canonical Model

### DOMAIN-061 — Orthogonal Assistance Snapshot

Attempt MUST 记录实际经历的四个正交维度：

```text
scaffold_control = NONE | LOW | MEDIUM | HIGH
hint_specificity = NONE | ORIENTATION | CONCEPTUAL_STRATEGIC | SUBGOAL | PARTIAL_STEP | BOTTOM_OUT
answer_exposure = NONE | PARTIAL | COMPLETE
assistance_state = INDEPENDENT | ASSISTED | ANSWER_EXPOSED
```

这些维度 MUST NOT 被一个全局整数 `scaffold_level`、`hint_level` 或 `answer_exposure_max` 替代。

### DOMAIN-062

`assistance_state` 是实际经历的汇总标签：无帮助且无答案暴露为 `INDEPENDENT`；任何实质帮助但无答案暴露为 `ASSISTED`；发生 complete/semantically answer-revealing exposure 时为 `ANSWER_EXPOSED`。具体映射规则 MUST 版本化。

## 11. Attempt

**Owner**：SYS04。

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
    scaffold_control: NONE|LOW|MEDIUM|HIGH
    hint_specificity: NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
    answer_exposure: NONE|PARTIAL|COMPLETE
    assistance_state: INDEPENDENT|ASSISTED|ANSWER_EXPOSED
    hint_event_ids: [uuid]
    support_reason: [string]
    delivery_mode: string|null
```

## 12. AssessmentResult / Diagnosis

**Owner**：SYS04。

Canonical `ErrorType`：

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
  assessment_confidence: float
  diagnosis:
    error_type: KNOWLEDGE_GAP|CONCEPTUAL_MISCONCEPTION|METHOD_SELECTION|EXECUTION|RETRIEVAL_FAILURE|TRANSFER_FAILURE|EXPRESSION_FORMAT|UNKNOWN
    diagnostic_confidence: float|null
    diagnostic_evidence_refs: [string]
    misconception_evidence_refs: [string]
    alternative_hypotheses: [object]
    needs_probe: boolean
    reason_codes: [string]
  assistance_state: INDEPENDENT|ASSISTED|ANSWER_EXPOSED
  evaluator_versions: [string]
  reviewer_result: accepted|rejected|needs_review
  created_at: datetime
  supersedes_result_id: uuid|null
```

### DOMAIN-070

AssessmentResult MUST NOT 包含 canonical `mastery_status` 作为最终裁决字段。

### DOMAIN-072

`assessment_confidence` 与 `diagnostic_confidence` MUST 独立表达；评分可信度高不代表错误归因可信度高。

### DOMAIN-073

`UNKNOWN` 是合法诊断结果。系统 MUST NOT 为满足 enum 完整性而强制猜测 ErrorType。

### DOMAIN-074 — Legacy Error Mapping

兼容读取时：`condition_omission` MUST 降级为 reason code/subcategory；`metacognitive` MUST 迁移为 behavioral/policy signal、ActionModifier 或 reason code；`expression_incomplete` MUST 映射为 `EXPRESSION_FORMAT`。无法无歧义映射的历史诊断 MUST 使用 `UNKNOWN + migration_reason`。

## 13. LearnerEvidence / MasteryEstimate / LearnerState

**Owner of evidence acceptance/projection**：SYS03；来源主要为 SYS04。

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
  assistance_state: INDEPENDENT|ASSISTED|ANSWER_EXPOSED
  delay_seconds: integer
  novelty: repeated|near_variant|far_variant
  evidence_weight: float
  item_difficulty: float|null
  source_event_ids: [uuid]
  eligibility_reason_codes: [string]

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

learner_state:
  learner_state_id: uuid
  version: integer
  user_id: uuid
  mastery_estimate_ids: [uuid]
  active_misconception_hypotheses: [object]
  learner_progress_summary: object
  uncertainty_summary: object
  created_from_event_sequence: integer
  algorithm_bundle_version: string
  created_at: datetime
```

### DOMAIN-071

`ANSWER_EXPOSED`、评分不可审计、版本不一致或重复提交的结果 MUST NOT 成为高权 mastery evidence；`ASSISTED` evidence MUST 与独立 evidence 区分并按版本化规则降权/限制用途。

### DOMAIN-080

`competence_probability` 是模型估计，不是真实概率宣称；UI 展示必须配合 confidence/evidence。

### DOMAIN-081

稳定掌握与迁移掌握的产品标签 MUST 由显式规则计算，至少考虑独立性、延迟证据、迁移证据和活跃误区，而不是只比较一个概率阈值。

### DOMAIN-082 — TeachingStage Separation

历史 `LearnerState.learning_stage_summary` 在 v0.3 被 `learner_progress_summary` 取代。该字段只是 SYS03 的学习进展摘要，MUST NOT 与 SYS05 `TeachingStage` 共享 owner、枚举或继承关系。

## 14. Teaching Strategy Ontology

**Owner**：SYS05。

Canonical `StrategyFamily` 仅允许：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

### DOMAIN-083 — Four-layer Ontology

v0.3 MUST 正式区分：

```text
StrategyFamily     = relatively stable teaching episode/control intent
TeachingAction     = SYS05 一次具体、不可变、可执行决策
InteractionMove    = 一轮或局部交互动作
ActionModifier     = 不改变 family 的组合修饰语义
```

`StrategyFamily != TeachingAction != InteractionMove`。

### DOMAIN-084 — InteractionMove Vocabulary

至少支持：

```text
DIRECT_INSTRUCTION
WORKED_EXAMPLE
SOCRATIC_PROBE
SELF_EXPLANATION_PROMPT
ORIENTATION_HINT
CONCEPTUAL_HINT
SUBGOAL_HINT
PARTIAL_STEP
COMPLETION_PROBLEM
FADING_STEP
CORRECTNESS_FEEDBACK
PROCESS_FEEDBACK
RETRIEVAL_REQUEST
DELAYED_RETRIEVAL_REQUEST
TRANSFER_TASK
DIRECT_ANSWER_OVERRIDE
METACOGNITIVE_CHECK
```

### DOMAIN-085 — ActionModifier Vocabulary

至少能够表达：`self_explanation`、`metacognitive_reflection`、`feedback_type`、`representation_style`、`transition_intent`、`support_reason`、`target_scope`、`delivery_mode`。

### DOMAIN-086 — Non-family Terms

`Productive Failure` MUST NOT 成为 v0.3 selectable StrategyFamily；Socratic MUST 作为 bounded `SOCRATIC_PROBE` move；worked example、direct instruction、self-explanation、metacognitive reflection MUST 处于 move/modifier 层而非新增 top-level family。

## 15. TeachingStage

**Derived by**：SYS05；不是持久学习者状态。

```text
DIAGNOSE
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
DELAYED_RETRIEVAL
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

### DOMAIN-087

`TeachingStage = f(TeachingContext, PolicyBundle)`。它 MUST NOT 被持久化为 LearnerState/MasteryState truth，也 MUST NOT 由 SYS03 拥有。

## 16. TeachingContext

**Owner of snapshot construction/evaluation semantics**：SYS05。TeachingContext 是 immutable decision-input snapshot，不是新的 state truth。

```yaml
teaching_context:
  context_id: uuid
  context_schema_version: string
  decision_time: datetime
  context_fingerprint: string
  objective:
    learning_objective_ref: versioned_ref
    learning_activity_ref: versioned_ref
    activity_type: value_with_availability
    target_capability: value_with_availability
    current_task_ref: versioned_ref|null
    task_structure_refs: [versioned_ref]
  learner:
    mastery_estimate_ref: versioned_ref|null
    mastery_confidence: value_with_availability
    prerequisite_state_refs: [versioned_ref]
    prerequisite_confidence: value_with_availability
    evidence_sufficiency: value_with_availability
  assessment:
    recent_assessment_result_ref: versioned_ref|null
    correctness_score: value_with_availability
    assessment_confidence: value_with_availability
  diagnosis:
    error_type: value_with_availability
    diagnostic_confidence: value_with_availability
    misconception_evidence_refs: [versioned_ref]
    alternative_diagnostic_hypotheses: [object]
    needs_probe: value_with_availability
  assistance_history:
    assistance_history_summary: object
    scaffold_history: [object]
    hint_history: [object]
    answer_exposure_history: [object]
    worked_example_exposure: value_with_availability
    independent_success_history: [versioned_ref]
    assisted_success_history: [versioned_ref]
  previous_decision:
    previous_teaching_action_ref: versioned_ref|null
    previous_action_outcome_refs: [versioned_ref]
  validation:
    delayed_independent_evidence: value_with_availability
    review_context: value_with_availability
    transfer_evidence: value_with_availability
    transfer_distance_novelty: value_with_availability
  request:
    direct_answer_request: boolean
    explanation_request: boolean
    time_budget: value_with_availability
    accessibility_constraints: [object]
  experiment:
    experiment_assignment_ref: versioned_ref|null
    experiment_opt_out: boolean
  source_refs: [versioned_ref]
```

### DOMAIN-088 — Replayable Context

TeachingContext MUST 固定 exact owner versions；任何 derived feature MUST 可回到 source refs；`decision_time` MUST 显式进入 snapshot；policy evaluator MUST NOT 隐式读取 mutable state；canonical replay MUST NOT 重新调用在线 LLM。

## 17. PolicyBundle

**Owner**：SYS05 configuration governance。

```yaml
policy_bundle:
  bundle_id: string
  schema_version: string
  policy_version: string
  hard_rule_set_version: string
  stage_mapper_version: string
  candidate_table_version: string
  feature_schema_version: string
  normalization_version: string
  weight_profile_version: string
  anti_oscillation_profile_version: string
  tie_break_version: string
  fallback_profile_version: string
  subject_profile_version: string|null
  content_digest: string
  published_at: datetime
```

### DOMAIN-089 — PolicyBundle Lifecycle

PolicyBundle MUST immutable publish、atomic activation、exact version pinning 并保留历史 bundle。Activation 只影响新 TeachingAction；历史 TeachingAction MUST NOT 被新 bundle 重解释。PolicyBundle MUST NOT 包含 executable DSL、embedded Python/free-form runtime policy code 或 LLM-generated rules。

## 18. TeachingAction

**Owner**：SYS05。

```yaml
teaching_action:
  action_id: uuid
  action_schema_version: string
  learning_objective_ref: versioned_ref
  learning_activity_ref: versioned_ref
  strategy_family: EXPLICIT_INSTRUCTION|GUIDED_PRACTICE|FADING_PRACTICE|RETRIEVAL_PRACTICE|ERROR_REMEDIATION|TRANSFER_CHALLENGE
  strategy_version: string
  teaching_stage: string
  interaction_moves: [string]
  action_modifiers: object
  scaffold_control: NONE|LOW|MEDIUM|HIGH
  hint_specificity: NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
  answer_exposure: NONE|PARTIAL|COMPLETE
  evidence_requirements: [string]
  expected_evidence_type: string|null
  success_condition: object
  failure_condition: object
  max_attempts: integer|null
  time_budget_seconds: integer|null
  validation_obligation: NONE|INDEPENDENT_VALIDATION_REQUIRED
  reason_codes: [string]
  policy_bundle_ref: versioned_ref
  teaching_context_ref: versioned_ref
  decision_id: uuid
  created_at: datetime
```

### DOMAIN-090 — Immutable Action Fidelity

SYS08 MUST 执行该动作语义；它 MAY 收紧 scaffold/hint/exposure envelope，但 MUST NOT 扩大支架、hint specificity、answer exposure 或改变 StrategyFamily/InteractionMove 语义。执行无法遵守时 MUST 返回 SYS05 重新决策。

### DOMAIN-091 — Independent Validation Obligation

`ASSISTED` success MUST 产生 `INDEPENDENT_VALIDATION_REQUIRED`；`ANSWER_EXPOSED` success MUST 产生该 obligation，且当前结果 MUST NOT 作为 independent mastery evidence。该 obligation 是 SYS05 policy-control semantics，不是 MasteryState；SYS03 MUST NOT 在 fresh independent Attempt 发生前假定其已完成。

## 19. LearningActivity / LearningPlan

**Owner**：SYS06。

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

## 20. ReviewSchedule

**Owner**：SYS07。

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

`next_due_at` 是 SYS07 的推荐时点；SYS06 决定它是否以及何时被纳入实际日计划。

## 21. TeachingEpisode / LearningTrajectory / OutcomeObservation / ExperimentAssignment

这些对象是 additive domain/analytics/experiment contract，MUST NOT 建立第九个领域 truth owner，也 MUST NOT 接管八系统既有状态所有权。

```yaml
teaching_episode:
  episode_id: uuid
  user_id: uuid
  learning_objective_ref: versioned_ref
  teaching_action_refs: [versioned_ref]
  started_at: datetime
  ended_at: datetime|null
  policy_bundle_refs: [versioned_ref]

learning_trajectory:
  trajectory_id: uuid
  user_id: uuid
  learning_goal_ref: versioned_ref
  episode_refs: [versioned_ref]
  started_at: datetime
  ended_at: datetime|null

outcome_observation:
  outcome_id: uuid
  outcome_type: string
  measurement_reference: versioned_ref
  independence: boolean|null
  assistance_state: INDEPENDENT|ASSISTED|ANSWER_EXPOSED|null
  scaffold_control: NONE|LOW|MEDIUM|HIGH|null
  hint_specificity: NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT|null
  answer_exposure: NONE|PARTIAL|COMPLETE|null
  actual_delay_seconds: integer|null
  transfer_distance: string|null
  novelty: string|null
  score: float|null
  success: boolean|null
  measurement_confidence: float|null
  active_learning_time_seconds: integer|null
  time_cost_seconds: integer|null
  hint_cost: float|null
  contamination_status: CLEAN|POSSIBLE|CONTAMINATED|UNKNOWN
  attribution_scope: ACTION_DIRECT|EPISODE_ASSOCIATED|TRAJECTORY_ASSOCIATED|EXPERIMENTALLY_CAUSAL|UNATTRIBUTABLE
  teaching_episode_ref: versioned_ref|null
  learning_trajectory_ref: versioned_ref|null
  experiment_association: versioned_ref|null
  observed_at: datetime

experiment_assignment:
  assignment_id: uuid
  experiment_id: string
  experiment_version: string
  unit_ref: string
  variant_id: string
  assignment_probability: float|null
  assigned_at: datetime
  opt_out: boolean
```

### DOMAIN-111 — Attribution Integrity

Delayed outcome MUST NOT 自动 last-touch attribution 给最后一个 TeachingAction。只有满足实验设计/识别条件时才可使用 `EXPERIMENTALLY_CAUSAL`；否则使用 episode/trajectory association 或 `UNATTRIBUTABLE`。

### DOMAIN-112 — Decision vs Outcome

`DecisionTrace` = 当时为什么这么决定；`OutcomeObservation` = 后来实际测到了什么。Outcome MUST NOT 回写修改历史 DecisionTrace。

### DOMAIN-113 — Experiment Probability

`ExperimentAssignment.assignment_probability` 表示随机分配概率，MUST NOT 被解释为 TeachingAction selection propensity。

## 22. ModelInference / FeedbackSignal

**ModelInference owner**：SYS08。**FeedbackSignal ledger host**：SYS08；由相应领域系统消费。

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

体验反馈 MUST NOT 直接进入 mastery；需要 SYS03 明确 evidence adapter 才可作为低权辅助信号。

## 23. DecisionTrace / LearningEvent

具体字段由 `domain/event-contract.md` 与 `domain/decision-contract.md` 定义。

- LearningEvent = 已发生、被系统接纳的不可变事实；
- DecisionTrace = 关键系统决策的不可变审计记录；
- 两者都不是新的业务状态 owner。

## 24. Versioned Configurable Parameters

### DOMAIN-120

以下 MUST 作为 versioned/traceable configurable parameters，而不是写死为科学常数：mastery threshold、failure ceiling、minimum dwell、switch margin、hint sequence、scaffold fade amount、diagnostic confidence cutoff、transfer novelty threshold、delay windows、policy weights、practical harm margin。

Spec 只冻结参数存在、所属机制、版本与 trace 要求；具体值 MAY 通过实验/校准调整，MUST NOT 无证据声称为“学习科学固定值”。

## 25. Legacy Mapping & Migration

| Legacy candidate | Canonical target | Compatibility read | Ambiguity / replay | Retirement condition |
|---|---|---|---|---|
| historical strategy records | six `StrategyFamily` + audit legacy value | MAY read legacy value | ambiguous mapping → UNKNOWN migration mapping / partial replay | all supported histories migrated or archived read-only |
| historical TeachingAction | v0.3 immutable TeachingAction | MAY adapt read-only | non-lossless semantics → partial replay | no active workflow depends on v0.2 schema |
| `scaffold_level` | `scaffold_control` | read-only adapter | unknown mapping → unavailable + reason | migrated records + no active writer |
| `hint_level` | `hint_specificity` | read-only adapter | unknown mapping → unavailable + reason | migrated records + no active writer |
| answer exposure `0..4` / `answer_exposure_max` | `answer_exposure` | read-only adapter | lossy mapping MUST be marked | migrated records + no active writer |
| legacy Socratic selector/state machine | bounded InteractionMove provider/legacy adapter | MAY invoke only behind SYS05 | MUST NOT own final TeachingAction | canonical SYS05 path covers supported flows |
| old policy config | immutable `PolicyBundle` | audit/read-only import | executable/free-form config MUST NOT execute | equivalent policy migrated or retired |
| `experiment.propensity` | assignment probability only when provenance proves it; otherwise unknown | preserve raw audit value | unclear semantics → action_propensity=null + migration_reason + partial replay | historical trace migrator completed |
| historical replay | exact historical refs when available | supported best-effort | missing refs/version → partial/non-replayable status | retained audit record with explicit status |

### DOMAIN-121 — No Permanent Dual Truth

Legacy fields MUST NOT 与 v0.3 canonical fields 双写为两个事实源。兼容层只可保留 legacy/audit value，并 MUST 有关闭条件。

## 26. Out of Scope（v0.3）

v0.3 MUST NOT 将以下实现为 canonical runtime：Contextual Bandit、Offline RL、Online RL、Deep KT canonical truth、complex IRT-CAT、open-world misconception discovery、school-level population A/B、multi-agent teaching control、automatic learned reward、synthetic learner as learning evidence、free-form LLM TeachingAction ownership、generic Productive Failure strategy、always-on Socratic tutor、generic executable policy DSL。

B2 LLM selector MAY 作为 experiment baseline，但 MUST 使用同一 hard shield、同一 action vocabulary，且 MUST NOT bypass hard rules。

## 27. Forbidden Domain Shortcuts

禁止创建：

- `TutorState` 同时塞入 mastery/plan/review/action；
- `AIJudgement` 同时承担评分与 mastery；
- `KnowledgeChunk` 同时表示 retrieval chunk 与 canonical KnowledgeUnit；
- 无 evidence/version/algorithm provenance 的裸 `UserSkillScore`；
- 不区分 LearningActivity 与 TeachingAction 的 `NextAction`；
- 同时表示 retrievability 与完整掌握的 `MemoryScore`；
- 由 LLM/Agent 持久化 LearnerState、Assessment truth、TeachingAction、LearningPlan 或 ReviewSchedule。