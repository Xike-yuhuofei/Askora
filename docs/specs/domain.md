# Askora Canonical Domain Model

> Spec ID 范围：`DOMAIN-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 Learning Core + v1 Product Positioning Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. Purpose

本文件定义八类技术系统跨边界共享的最小领域语义。系统内部 MAY 有私有对象，但 MUST NOT 复制、改变或模糊这些公共对象含义。v0.3 canonical truth 以本文件、`decision-contract.md` 与各系统 Spec 为准；legacy 字段只允许按迁移合同 read/audit。

本文件中早于 v1 Product Positioning Alignment 的 `user_id`、`source_document_ids`、`SourceDocument` 等示例字段，必须结合第 25 节解释；不得再将其理解为 Account、Global Material Library 或用户原始文件路径 truth。

## 2. Common Rules

### DOMAIN-001 — Stable Identity + Immutable Revision

具有长期引用价值的对象 SHOULD 使用 `stable_id + immutable revision/version`；语义变化 SHOULD 生成新 revision，而不是覆盖旧记录。

### DOMAIN-002 — Provenance First

任何影响教学、评估、掌握或引用的对象 MUST 能追溯来源、算法/模型/PolicyBundle 版本与创建上下文。

### DOMAIN-003 — Fact / Inference / Decision Separation

公共对象 MUST 能区分 user fact、source fact、system inference、policy decision、generated content、human review。

### DOMAIN-004 — Time

持久化时间 MUST 使用带时区 UTC 或明确 offset；展示层 MAY 转换本地时区。

### DOMAIN-005 — Missing Semantics

需要表达输入可用性的字段/派生 feature MUST 使用 `AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE`。`MISSING` MUST NOT 用 `0`、空字符串或伪默认值表达。

## 3. LearningGoal / LearningObjective

**Owner**：SYS06。

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

### DOMAIN-010

LLM MAY 从自然语言生成 goal candidate，但 `confirmed|active` 必须经过用户确认或显式产品规则确认。

### DOMAIN-011

Objective MUST 可由 SYS04 一个或多个 AssessmentItem 测量，MUST NOT 只用“了解/熟悉”等不可验证描述。

## 4. SourceDocument / MaterialRevision / SourceSpan / SourceChunk

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

### DOMAIN-020

原始文件改变、parser 产生语义性不同结果或安全修复要求重建内容时，MUST 形成可追踪 revision。

### DOMAIN-021

任何用户可见引用 MUST 最终回到 SourceSpan 或等价稳定原文锚点。

### DOMAIN-022

SourceChunk 是可重建 retrieval projection，MUST NOT 作为长期 KnowledgeUnit identity。

## 5. KnowledgeUnit / Concept / Prerequisite / Misconception

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

Published KnowledgeUnit MUST 有至少一个可 replay source evidence，除非 provenance 明确是用户/专家人工创建且产品允许无材料来源对象。

### DOMAIN-040

章节先后顺序 MUST NOT 自动等同 hard prerequisite。

### DOMAIN-041

低置信 inferred prerequisite MUST NOT 自动提升为 hard prerequisite。

### DOMAIN-042 — Misconception Boundary

`Misconception definition → SYS01`；`MisconceptionEvidence → SYS04`；`MisconceptionHypothesis → SYS03`；`Remediation decision → SYS05`。Misconception definition 不代表某学习者实际存在该误区。

## 6. EvidenceBundle

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

### DOMAIN-050 — Exposure Envelope

EvidenceBundle MUST 执行 TeachingAction `answer_exposure` hard envelope。SYS02 MAY 收紧，MUST NOT 放宽。Legacy `exposure_level:0..4` / `answer_exposure_max` MAY read-only mapping，MUST NOT canonical write；lossy mapping MUST 显式标记。

## 7. AssessmentItem / Attempt / Assistance

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

### DOMAIN-060

模型生成 AssessmentItem 默认 `draft`，通过 solvability、answer consistency、safety checks 后才 MAY `active`。

### DOMAIN-061 — Assistance Must Be Recorded

Attempt MUST 记录实际帮助/答案暴露状态，否则不能可靠判断 evidence eligibility。

### DOMAIN-062 — Orthogonal Assistance Axes

Canonical assistance MUST 正交表达：

```text
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
assistance_state = INDEPENDENT|ASSISTED|ANSWER_EXPOSED
```

MUST NOT 继续以一个全局 integer `scaffold_level`、`hint_level` 或 `answer_exposure_max` 作为 canonical semantics。

### DOMAIN-063 — Assistance State Mapping

`INDEPENDENT` = 无实质帮助/答案暴露；`ASSISTED` = 有实质帮助但未达到 answer-exposed；`ANSWER_EXPOSED` = complete/semantically answer-revealing exposure。具体映射 MUST versioned。

## 8. AssessmentResult / Diagnosis

**Owner**：SYS04。

Canonical ErrorType：

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

### DOMAIN-071

ANSWER_EXPOSED、评分不可审计、版本不一致或重复提交结果 MUST NOT 成为高权 mastery evidence；ASSISTED evidence MUST 与 independent evidence 区分并按 versioned rules 降权/限制用途。

### DOMAIN-072

`assessment_confidence != diagnostic_confidence`；评分可信度高 MUST NOT 隐式等于错因归因可信度高。

### DOMAIN-073

`UNKNOWN` 是合法 ErrorType。系统 MUST NOT 为 enum 完整性强制猜一个错误类型。

### DOMAIN-074 — Legacy Error Mapping

`condition_omission → reason code/subcategory`；`metacognitive → behavioral/policy signal、ActionModifier 或 reason code`；`expression_incomplete → EXPRESSION_FORMAT`。无法无歧义映射 MUST `UNKNOWN + migration_reason`，不得伪造 diagnostic confidence。

## 9. LearnerEvidence / MasteryEstimate / LearnerState

**Owner**：SYS03。

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

### DOMAIN-080

`competence_probability` 是模型估计，不是真实概率宣称；UI MUST 配合 confidence/evidence 展示。

### DOMAIN-081

Stable/transfer mastery product labels MUST 由显式 versioned rules 计算，至少考虑 independence、delay evidence、transfer evidence、active misconception；MUST NOT 只比较单一 probability threshold。

### DOMAIN-082 — TeachingStage Separation

Legacy `LearnerState.learning_stage_summary` 在 v0.3 迁移/重命名为 `learner_progress_summary` 或等价 progress summary；MUST NOT 与 SYS05 TeachingStage 共享 owner、enum、inheritance。

## 10. Teaching Strategy Ontology

**Owner**：SYS05。

Canonical StrategyFamily only：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

### DOMAIN-083 — Four-layer Ontology

MUST 区分 `StrategyFamily`（稳定 episode/control intent）、`TeachingAction`（一次 immutable executable decision）、`InteractionMove`（局部 interaction move）、`ActionModifier`（不改变 family 的组合修饰）。`StrategyFamily != TeachingAction != InteractionMove`。

### DOMAIN-084 — InteractionMove Vocabulary

至少支持：`DIRECT_INSTRUCTION`、`WORKED_EXAMPLE`、`SOCRATIC_PROBE`、`SELF_EXPLANATION_PROMPT`、`ORIENTATION_HINT`、`CONCEPTUAL_HINT`、`SUBGOAL_HINT`、`PARTIAL_STEP`、`COMPLETION_PROBLEM`、`FADING_STEP`、`CORRECTNESS_FEEDBACK`、`PROCESS_FEEDBACK`、`RETRIEVAL_REQUEST`、`DELAYED_RETRIEVAL_REQUEST`、`TRANSFER_TASK`、`DIRECT_ANSWER_OVERRIDE`、`METACOGNITIVE_CHECK`。

### DOMAIN-085 — ActionModifier Vocabulary

至少支持 `self_explanation`、`metacognitive_reflection`、`feedback_type`、`representation_style`、`transition_intent`、`support_reason`、`target_scope`、`delivery_mode`。

### DOMAIN-086 — Non-family Terms

Productive Failure MUST NOT 是 v0.3 selectable StrategyFamily；Socratic 只能 bounded `SOCRATIC_PROBE` move；worked example/direct instruction/self-explanation/metacognitive reflection 属 move/modifier，不新增 top-level family。

## 11. TeachingStage

Canonical vocabulary：`DIAGNOSE|EXPLICIT_INSTRUCTION|GUIDED_PRACTICE|FADING_PRACTICE|RETRIEVAL_PRACTICE|DELAYED_RETRIEVAL|ERROR_REMEDIATION|TRANSFER_CHALLENGE`。

### DOMAIN-087

`TeachingStage = f(TeachingContext, PolicyBundle)`，由 SYS05 派生。MUST NOT 持久化为 LearnerState/MasteryState truth，也 MUST NOT 由 SYS03 owner。

## 12. TeachingContext

**Snapshot semantics owner**：SYS05。TeachingContext 是 immutable decision-input snapshot，不是新的 state truth。

```yaml
teaching_context:
  context_id: uuid
  context_schema_version: string
  decision_time: datetime
  context_fingerprint: string
  learning_objective_ref: versioned_ref
  learning_activity_ref: versioned_ref
  activity_type: value_with_availability
  target_capability: value_with_availability
  current_task_ref: versioned_ref|null
  task_structure_refs: [versioned_ref]
  mastery_estimate_ref: versioned_ref|null
  mastery_confidence: value_with_availability
  prerequisite_state_refs: [versioned_ref]
  prerequisite_confidence: value_with_availability
  evidence_sufficiency: value_with_availability
  recent_assessment_result_ref: versioned_ref|null
  correctness_score: value_with_availability
  assessment_confidence: value_with_availability
  error_type: value_with_availability
  diagnostic_confidence: value_with_availability
  misconception_evidence_refs: [versioned_ref]
  alternative_diagnostic_hypotheses: [object]
  needs_probe: value_with_availability
  assistance_history_summary: object
  scaffold_history: [object]
  hint_history: [object]
  answer_exposure_history: [object]
  worked_example_exposure: value_with_availability
  independent_success_history: [versioned_ref]
  assisted_success_history: [versioned_ref]
  previous_teaching_action_ref: versioned_ref|null
  previous_action_outcome_refs: [versioned_ref]
  delayed_independent_evidence: value_with_availability
  review_context: value_with_availability
  transfer_evidence: value_with_availability
  transfer_distance_novelty: value_with_availability
  direct_answer_request: boolean
  explanation_request: boolean
  time_budget: value_with_availability
  accessibility_constraints: [object]
  experiment_assignment_ref: versioned_ref|null
  experiment_opt_out: boolean
  source_refs: [versioned_ref]
```

### DOMAIN-088 — Replayable Context

TeachingContext MUST pin exact owner versions；derived features MUST trace source refs；decision_time MUST enter snapshot；evaluator MUST NOT implicit-read mutable state；canonical replay MUST NOT call online LLM。

## 13. PolicyBundle

**Owner**：SYS05 policy configuration governance。

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

PolicyBundle MUST immutable publish、atomic activate、exact-version pin、historical retain。Activation 只影响新 TeachingAction；MUST NOT 重解释历史 action。MUST NOT 包含 executable DSL、embedded Python/free-form runtime policy code、LLM-generated rules。

## 14. TeachingAction

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

### DOMAIN-090 — Action Fidelity

SYS08 MUST 执行 action semantics；MAY 收紧 scaffold/hint/exposure，MUST NOT 扩大或改变 StrategyFamily/InteractionMove semantics。无法遵守时 MUST 返回 SYS05 重新决策。

### DOMAIN-091 — Independent Validation Obligation

ASSISTED success 与 ANSWER_EXPOSED success MUST 产生 `INDEPENDENT_VALIDATION_REQUIRED`；answer-exposed current result MUST NOT 是 independent mastery evidence。Obligation 属 SYS05 policy-control，不是 MasteryState；fresh independent Attempt 前 SYS03 MUST NOT 假定完成。

## 15. LearningActivity / LearningPlan

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

## 16. ReviewSchedule

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

`next_due_at` 是 SYS07 recommended time；SYS06 决定是否/何时纳入 actual plan。

## 17. TeachingEpisode / LearningTrajectory / OutcomeObservation / ExperimentAssignment

这些对象是 additive domain/analytics/experiment contracts，MUST NOT 建立第九 domain truth owner 或接管八系统 ownership。

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

Delayed outcome MUST NOT 自动 last-touch 给最后 TeachingAction。只有满足实验识别条件才 MAY `EXPERIMENTALLY_CAUSAL`；否则 episode/trajectory association 或 `UNATTRIBUTABLE`。

### DOMAIN-112 — Decision vs Outcome

DecisionTrace = 当时为什么决定；OutcomeObservation = 后来测到了什么。Outcome MUST NOT 回写修改旧 DecisionTrace。

### DOMAIN-113 — Experiment Probability

ExperimentAssignment `assignment_probability` 表示 random assignment probability，MUST NOT 解释为 TeachingAction selection propensity。

## 18. ModelInference / FeedbackSignal

**ModelInference owner**：SYS08。**FeedbackSignal ledger host**：SYS08；由相应领域 owner 消费。

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

Experience feedback MUST NOT 直接进入 mastery；需要 SYS03 explicit evidence adapter 才 MAY 作为低权辅助 signal。

## 19. DecisionTrace / LearningEvent

字段由 `domain/event-contract.md`、`domain/decision-contract.md` 定义。LearningEvent = accepted immutable fact；DecisionTrace = immutable decision audit；二者均不是新 business state owner。

## 20. Versioned Configurable Parameters

### DOMAIN-120

mastery threshold、failure ceiling、minimum dwell、switch margin、hint sequence、scaffold fade amount、diagnostic confidence cutoff、transfer novelty threshold、delay windows、policy weights、practical harm margin MUST 是 versioned/traceable configurable parameters，MUST NOT 写死成科学常数。

## 21. Legacy Mapping & Migration

| Legacy candidate | Canonical target | Compatibility read | Ambiguity / replay | Retirement condition |
|---|---|---|---|---|
| historical strategy records | six StrategyFamily + legacy audit | MAY read | ambiguous mapping explicit / partial replay | migrated or archived read-only |
| historical TeachingAction | v0.3 immutable TeachingAction | MAY read-adapt | non-lossless → PARTIAL | no active v0.2 workflow |
| `scaffold_level` | `scaffold_control` | read adapter | unknown → unavailable + reason | migrated + no active writer |
| `hint_level` | `hint_specificity` | read adapter | unknown → unavailable + reason | migrated + no active writer |
| old exposure / `answer_exposure_max` | `answer_exposure` | read adapter | lossy mapping marked | migrated + no active writer |
| legacy Socratic selector/state machine | bounded InteractionMove provider/adapter | bounded compatibility | never final action owner | canonical SYS05 covers flows |
| old policy config | immutable PolicyBundle | audit/import only | executable/free-form config never executes | migrated/retired |
| old `experiment.propensity` | assignment probability only when provenance proves; otherwise unknown | raw audit | ambiguous → action_propensity=null + reason + PARTIAL | historical migrator complete |
| historical replay | exact historical refs | best effort | missing version → PARTIAL/NON_REPLAYABLE | explicit status retained |

### DOMAIN-121 — No Permanent Dual Truth

Legacy fields MUST NOT 与 v0.3 canonical fields permanent dual-write。Compatibility layer MUST 明确 canonical source、raw legacy/audit role 与 retirement condition。

## 22. Out of Scope

v0.3 canonical runtime MUST NOT 实现 Contextual Bandit、Offline/Online RL、Deep KT canonical truth、complex IRT-CAT、open-world misconception discovery、school-level population A/B、multi-agent teaching control、automatic learned reward、synthetic learner as learning evidence、free-form LLM TeachingAction ownership、generic Productive Failure strategy、always-on Socratic tutor、generic executable policy DSL。B2 LLM selector MAY experiment baseline behind same hard shield/action vocabulary。

v1 还明确不包含：多用户/Tenant/RBAC、Global Material Library、跨设备实时同步、完整 OCR/原生音视频 pipeline、开放式长期自治 Agent、Desktop/Electron 作为产品 shell、Redis/PostgreSQL/Docker/Kafka 运行依赖。

## 23. Forbidden Domain Shortcuts

禁止长期公共 `TutorState` 同时塞 mastery/plan/review/action；`AIJudgement` 同时承担 scoring+mastery；`KnowledgeChunk` 同时表示 retrieval chunk+KnowledgeUnit；无 provenance 的 `UserSkillScore`；不区分 LearningActivity/TeachingAction 的 `NextAction`；同时表示 retrievability/mastery 的 `MemoryScore`；LLM/Agent 持久化 LearnerState、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule。

## 24. P1-01 Goal Management Additions

`LearningGoalDefinitionV2` 是不含 current status 的 immutable semantic version；
`LearningGoalStateV1` 与 `LearningPlanStateV1` 是 append-only current truth；draft/preview/focus 是
SYS06-owned control records。`LearningObjectiveV1` 把 criterion、cognitive process、target refs 与
evidence requirements 结构化。`GoalAchievementEvaluationV1` 是证据门禁决定，不是 mastery truth。

## 25. v1 Product Positioning Alignment

本节是对前述 v0.3 Learning Core 对象的**规范性上位对齐**。当早期 YAML 示例与本节冲突时，本节优先。

### DOMAIN-200 — LocalOwner / Legacy `user_id`

v1 无 Account/Login/Tenant/RBAC。唯一 durable local ownership subject 是 `LocalOwner`；Learner MAY 与 LocalOwner 首版共用稳定 UUID，但语义不是 credential principal。

本文件历史 YAML 中：

```text
user_id
```

在完成 migration 前 MAY 继续作为 storage/API compatibility 字段，但 canonical semantics MUST 解释为：

```text
LocalOwner / Learner subject id
```

MUST NOT 再解释为登录账号、JWT subject 或 tenant user。

### DOMAIN-201 — Workspace

Workspace 是 LocalOwner 下的高层数据隔离边界，不是 Tenant/Organization，也不是 SYS09。

```yaml
workspace:
  workspace_id: uuid
  owner_id: uuid
  version: integer
  name: string
  lifecycle: active|trash
  created_at: datetime
```

Platform Workspace Registry MAY additionally own one owner-scoped versioned current-selection preference：

```yaml
workspace_selection:
  owner_id: uuid
  version: integer
  current_workspace_id: uuid
  reason: FIRST_CREATE|LEGACY_MIGRATION|EXPLICIT_SWITCH|RECOVERY_RECONCILIATION
  updated_at: datetime
```

This preference is not Workspace identity/default/lifecycle truth。Its exact contract is ADR-0023 / `CWSP-*`。

规则：

- 一个 LocalOwner MAY 有多个 Workspace；
- fresh LocalOwner MAY have zero Workspace until explicit Course create；legacy-data migration creates one default Workspace；
- Material、LearningProject、LearningGoal、LearningSession、LearnerState/LearningEvidence scope、LearningHistory、UserNote、Search/Retrieval MUST 可解析到 workspace；
- 默认不得跨 Workspace 搜索、融合 LearnerState 或共享 Material membership；
- 跨 Workspace 能力未来必须通过新的 Product Positioning / Design / Spec 明确授权。

### DOMAIN-202 — Material / SourceFile / SourceDocument Compatibility

Material 是 Workspace-scoped 用户资料领域对象；SourceFile 是 Askora managed raw asset。

```yaml
material:
  material_id: uuid
  workspace_id: uuid
  metadata_version: integer
  display_title: string
  current_revision_id: uuid|null
  lifecycle: active|trash
  created_at: datetime

source_file:
  asset_id: uuid
  material_id: uuid
  checksum: string
  original_filename: string
  managed_storage_ref: string
  created_at: datetime
```

Import MUST 是：

```text
user-selected file
→ ingest + copy
→ managed SourceFile
→ Material / MaterialRevision
```

后续使用 MUST NOT 依赖用户最初文件路径仍存在。

历史 `SourceDocument` / `document_id` MAY 作为 SYS01 content record / compatibility id 保留，但：

- MUST subordinate to exactly one Material/Workspace scope；
- MUST NOT 形成 v1 Global Material Library；
- MUST NOT 代替 managed SourceFile truth；
- `source_document_ids` 在新 Goal/API 中 SHOULD 迁移为 Material/source refs。

### DOMAIN-203 — LearningProject / ProjectMaterial

LearningProject 是 Workspace 内长期学习组织单位，不是开始学习的强制门禁。

```yaml
learning_project:
  project_id: uuid
  workspace_id: uuid
  version: integer
  title: string
  status: active|paused|archived
  created_at: datetime

project_material:
  project_id: uuid
  material_id: uuid
  relation_version: integer
  created_at: datetime
```

关系：

```text
Workspace 1 ── N Material
Workspace 1 ── N LearningProject
LearningProject N ── M Material
LearningProject 1 ── N LearningGoal (optional association)
```

`ProjectMaterial` 只表示关系。Remove Material from Project MUST NOT 删除 Material/SourceFile。

LearningProject / ProjectMaterial 的组织语义属于 Platform Workspace/Product Organization boundary；它不取得 SYS01 content 或 SYS06 Goal/Plan 的写权限。

### DOMAIN-204 — LearningGoal and LearningSession Scope

新 LearningGoal MUST 有 `workspace_id`；`project_id` MAY 为空。用户可以直接基于 Material 创建/开始学习，再决定是否组织进 Project。

v1 Goal tree 最多：

```text
Goal
└── Subgoal
```

不建设无限层级目标树。

LearningSession 是连续学习活动，不是 Conversation 的同义词：

```yaml
learning_session:
  session_id: uuid
  workspace_id: uuid
  learning_activity_id: uuid|null
  project_id: uuid|null
  learning_goal_id: uuid|null
  material_refs: [versioned_ref]
  started_at: datetime
  ended_at: datetime|null
```

Session MUST 属于 Workspace；MAY 不属于 Project。

New Activity-scoped Session MUST pin exact `learning_activity_id` and validate the SYS06 Activity resolves to the same Workspace。Legacy Session MAY remain null only when exact backfill would require guessing；LearningSession does not acquire Activity lifecycle write ownership。

### DOMAIN-205 — RetrievalScope

所有 production retrieval 必须拥有显式 Workspace scope：

```yaml
retrieval_scope:
  workspace_id: uuid
  project_ids: [uuid]
  material_ids: [uuid]
  knowledge_unit_ids: [uuid]
  session_context: object|null
```

`workspace_id` REQUIRED；其余为 optional narrowing。MUST NOT 用 LocalOwner 代替 workspace hard filter；MUST NOT 默认全本地数据检索。

### DOMAIN-206 — Durable Facts / Canonical Rebuildable Projections / Infrastructure-derived Data

v1 数据分类：

```text
Durable Facts
├── LocalOwner / Workspace / LearningProject
├── Material / SourceFile
├── LearningGoal / UserNote
├── Attempt / AssessmentResult / LearningEvidence
├── LearningHistory / canonical decisions needed for replay
└── user configuration / deletion facts

Canonical Rebuildable Projections
├── MasteryEstimate
└── LearnerState

Infrastructure-derived
├── SourceChunk
├── Embedding
├── Vector/Lexical Index
├── retrieval cache
└── rebuildable AI summaries
```

LearnerState / MasteryEstimate 仍由 SYS03 single writer 维护并作为当前 authoritative read projection，但其 correctness source MUST 是 durable accepted LearningEvidence + exact projector/version。

删除/修正某条 LearningEvidence 后：

```text
Evidence removed/corrected
→ invalidate affected projection
→ SYS03 replay/reproject
→ new MasteryEstimate/LearnerState version
```

MUST NOT 继续保留受已删除 evidence 影响的旧状态作为当前 truth。

### DOMAIN-207 — Conversation Is Not LearningEvidence

Conversation / Message / Prompt 可以是 LearningSession 的交互/执行记录，但不自动形成 LearningEvidence。

```text
“I understand” / thumbs-up / conversation turn
≠ mastery evidence
```

有效学习证据需要经过结构化 owner contract，例如：

```text
Attempt
→ AssessmentResult
→ LearnerEvidence acceptance
→ LearnerState projection
```

用户自评 MAY 形成结构化 `SelfAssessmentEvidence`，但其权重必须低于独立作答、延迟保持与迁移证据，并由 SYS03 规则接纳。

### DOMAIN-208 — Configuration Scope

配置层级：

```text
Application
↓
Workspace
↓
Project
```

下层只允许覆盖明确声明可覆盖的字段。不得建立无边界动态继承系统，也不得把 API Key 写入 Workspace/Project 普通配置文件。

Provider/model routing metadata 由 SYS08 `ModelRouteProfile` owner 管理；SecretStore 只托管 secret material。

### DOMAIN-209 — Local Background Job

后台任务是 Platform Job Runtime durable control object，不是第九学习 domain：

```yaml
local_job:
  job_id: uuid
  workspace_id: uuid|null
  material_id: uuid|null
  job_type: string
  input_fingerprint: string
  status: pending|running|succeeded|failed|interrupted
  attempt_count: integer
  next_attempt_at: datetime|null
  last_error_code: string|null
  idempotency_key: string
  created_at: datetime
  updated_at: datetime
```

任务可调用 SYS01～SYS08 owner application services，但不得取得其业务 truth 写权限。App shutdown/restart 后任务必须可安全 resume/retry/restart。

### DOMAIN-210 — Material Pipeline State

Material ingestion/derived lifecycle SHOULD 能表达：

```text
Uploaded
→ SourceStored
→ Parsed
→ Structured
→ Indexed
→ KnowledgeModeled
→ Ready
```

overall status 至少：`pending|processing|ready|partial|failed`。

Stage success/failure 与 Material durable lifecycle 分离；某 derived stage failed MUST NOT 删除 SourceFile 或把 durable Material 变成不可恢复 truth loss。

### DOMAIN-211 — Trash and Permanent Delete

普通用户删除使用：

```text
Normal
→ Trash
→ Permanent Delete
```

- 从 Project 移除 Material：只删 relationship；
- 删除 Material：进入 Trash；
- Permanent Delete：由用户明确触发或预定义本地清理策略执行，并服从 no-resurrection/data-control contract；
- 通用 Undo / Command History / 全局版本历史不属于 v1。

### DOMAIN-212 — Source-grounded vs External Model Knowledge

任何声称来自用户资料的事实性内容 MUST 有可回到 Material → SourceSpan/等价 locator 的 provenance。

模型自身知识 MAY 用于补充解释，但必须与 Source-grounded Knowledge 区分；找不到资料证据时 MUST 降级/承认缺少来源，不得伪造 citation。

### DOMAIN-213 — v1 Domain-level Forbidden Shortcuts

除第 23 节外，v1 额外禁止：

- Workspace = Tenant / Organization；
- `owner_id` 代替 `workspace_id` 做资料/学习状态隔离；
- Global Material Library / cross-workspace default search；
- Material 只保存外部原文件路径；
- ProjectMaterial relation 删除级联删除 Material；
- SourceChunk/Embedding/Index 成为不可重建权威；
- LearnerState 成为无法从 LearningEvidence 重建的基础事实；
- Conversation/Message/Prompt 直接写 mastery；
- LLM 直接修改 SQLite/canonical state；
- Desktop/Electron 对象成为 v1 公共领域模型；
- Account/AuthSession/JWT 成为 learner ownership；
- Redis/PostgreSQL/Kafka job state 成为 production-local 唯一 truth。

---

## Askora Decision Trace Contract

> Spec ID 范围：`DECISION-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

### 1. Purpose

Askora 的关键决策 MUST 能回答：当时看到了什么、有哪些候选、受什么约束、为什么选择该结果、由哪个算法/策略/模型/PolicyBundle 版本产生。

DecisionTrace 是 immutable audit/replay record，不是新的业务状态 owner；它记录**当时为什么这样决定**，与后续 OutcomeObservation 严格分离。

### 2. Existing Cross-system Contracts Retained

#### DECISION-001 — Decision Payload Ownership

做出业务决策的领域系统负责产生 DecisionTrace payload；SYS08 Decision Ledger MAY 负责 append-only 持久化、索引和查询。

#### DECISION-002 — Ledger Must Not Rewrite Semantics

SYS08 MUST NOT 修改 `selected_action`、`reason_codes`、candidate/score 或其他领域决策语义来“修复”记录。

#### DECISION-010 — SYS01 High-impact Knowledge Publication

KnowledgeUnit merge/split、hard prerequisite publish/reject 与高影响人工审核 MUST 有 trace。

#### DECISION-011 — SYS02 EvidenceBundle Selection

MUST 记录 retrieval request、主要 candidates/rank source、hard filter reason、selected evidence、exposure filter、missing/conflict。

#### DECISION-012 — SYS03 MasteryEstimate Update

MUST 记录 evidence ids/weights、prior/new state version、algorithm/config version 与 reason codes。

#### DECISION-013 — SYS04 Non-trivial Assessment

开放题、模型辅助评分、evaluator conflict 或 misconception diagnosis MUST 记录 evaluator results、rubric/version、constraints/adjudication 与 selected AssessmentResult。纯 deterministic grader MAY 使用精简 trace。

#### DECISION-014 — SYS05 TeachingAction

MUST 记录全部可行动作候选、typed hard filters、features/scores、anti-oscillation、tie-break、最终 TeachingAction 与 reason codes，并满足 v0.3 `DECISION-200..222`。

#### DECISION-015 — SYS06 Plan / Replan

MUST 记录 feasible candidates、prerequisite/deadline/time constraints、priority factors、selected activities 与 replan trigger。

#### DECISION-016 — SYS07 ReviewSchedule Update

MUST 记录 prior memory state、valid retrieval evidence、desired retention、new next_due_at、scheduler/model version。

#### DECISION-017 — SYS08 High-impact Route / Degradation

隐私导致的 model choice、primary-model fallback、tool permission denial、validation-triggered retry/degradation 与影响质量/成本的重要 route MUST 有 trace。

#### DECISION-020 — Stable Reason Codes

每个关键决策 MUST 至少有一个稳定、机器可查询 reason code。自然语言解释 MAY 附加，MUST NOT 替代 reason code。

#### DECISION-021 — Reason-code Versioning

Reason code 发布后 MUST NOT 复用同一 code 改变含义；语义变化必须新 code 或新主版本。

#### DECISION-030 — Candidate Retention

存在真实候选选择时，trace MUST 保存足够 candidates/features/scores/eligibility 支持 replay/shadow/counterfactual comparison；MUST NOT 只保存赢家。

#### DECISION-031 — Hard vs Soft Separation

Hard constraint 与 soft score MUST 分开记录。Hard constraint MUST NOT 仅表示为可被高分抵消的 penalty。v0.3 soft example 使用 `learning_value_proxy`，该值 MUST NOT 被称为 causal learning-effect estimate。

#### DECISION-040 — Confidence

`confidence` 只有在有明确定义/校准方法时才 MAY 使用；否则 MUST null 或使用离散 reason code，MUST NOT 让 LLM 自报 0.93 作为系统置信度。

#### DECISION-050 — ModelInference Link

模型参与关键决策时 MUST 通过 `model_inference_ids`/等价 versioned refs 关联 ModelInference，而不是只记录模型名字。

#### DECISION-051 — Model Output != Final Decision

`ModelInference = 模型产生了什么`；`DecisionTrace = 领域系统最终接受了什么、为什么`。二者 MUST 分离。

#### DECISION-060 — Experiment Logging, v0.3 Clarified

Experiment MUST 记录 experiment id/version、variant、assignment unit、assignment probability 与可用 guardrail/context。只有行为策略本身真实 stochastic 时才 MAY 记录 action propensity。Deterministic B3 MUST 服从 `DECISION-210`。

#### DECISION-061 — OPE Claim Boundary

若未来进行 IPS/SNIPS/DR 等 causal off-policy analysis，必须有真实 behavior-policy action availability/propensity 语义。v0.3 canonical runtime 不实施 causal RL OPE；assignment probability MUST NOT 伪装 action propensity。

#### DECISION-062 — Reward / Outcome Boundary

实验主要学习目标 MUST NOT 使用聊天时长、点击率、点赞、hint/token/session duration 替代真实学习 outcome；这些只能作为 process/experience guardrail。

#### DECISION-070 — Replay Uses

DecisionTrace MUST 支持历史解释、同版本 replay、新旧算法 shadow compare、candidate counterfactual compare 与回滚定位（在可用数据边界内）。

#### DECISION-071 — Replayability Gap

历史输入/version 不可取得时 MUST 明确标记 replayability 缺口，MUST NOT 声称 FULL replay。

#### DECISION-080 — User-facing Explanation

用户可见“为什么” SHOULD 从稳定 reason codes + 真实 evidence 生成，MUST NOT 由 LLM 事后自由编造。

#### DECISION-090 — Append-only

DecisionTrace MUST append-only；更正通过新 trace/correction record，MUST NOT 原地修改历史。

#### DECISION-091 — Ledger Indexing

Decision Ledger SHOULD 支持按 decision_id/type、owner_system、correlation/trace id、input entity、algorithm/PolicyBundle version、experiment id、created_at 查询。

### 3. DecisionTrace v0.3

#### DECISION-200 — Required Shape

```yaml
decision_trace:
  decision_id: uuid
  decision_schema_version: string
  decision_type: teaching_action_selection|string
  owner_system: string
  decision_time: datetime

  teaching_context_ref: versioned_ref|null
  teaching_context_schema_version: string|null
  context_fingerprint: string|null
  context_source_refs: [versioned_ref]

  policy_bundle_ref: versioned_ref|null
  policy_bundle_hash: string|null
  policy_version: string|null

  strategy_family: string|null
  strategy_version: string|null
  derived_teaching_stage: string|null
  stage_mapper_version: string|null

  available_actions: [object]
  hard_filtered_actions:
    - action_ref: string
      filter_reason_codes: [string]

  features:
    - feature_name: string
      value: number|null
      availability: AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE
      confidence: float|null
      feature_version: string
      source_refs: [versioned_ref]

  candidate_scores: [object]
  selected_teaching_action_ref: versioned_ref|null
  previous_teaching_action_ref: versioned_ref|null

  transition_reason_codes: [string]
  material_evidence_refs: [versioned_ref]
  anti_oscillation_decision: object|null
  tie_break_reason: string|null

  experiment_assignment_ref: versioned_ref|null
  experiment_assignment_probability: float|null

  behavior_policy_type: DETERMINISTIC|STOCHASTIC_EXPERIMENTAL|UNKNOWN
  action_propensity: float|null

  algorithm:
    algorithm_id: string
    algorithm_version: string
    model_inference_ids: [uuid]
    prompt_versions: [string]

  reason_codes: [string]
  replayability_status: FULL|PARTIAL|NON_REPLAYABLE
  replayability_reason_codes: [string]
  migration_metadata: object|null
  correlation_id: uuid|string
  trace_id: string
  created_at: datetime
```

Non-SYS05 decision types MAY leave teaching-specific fields null/not-applicable while still obeying common ownership/reason/version/replay contracts。

#### DECISION-201 — Teaching Trace Completeness

SYS05 trace MUST 保存 all available candidates、hard-filter reasons、feature availability/confidence/version、candidate scores、selected/previous action、transition/material evidence、anti-oscillation、tie-break reason。MUST NOT 只保存赢家。

#### DECISION-202 — Immutable Historical Semantics

DecisionTrace MUST 固定 decision-time TeachingContext、PolicyBundle/source versions。后续 LearnerState、PolicyBundle、OutcomeObservation MUST NOT 回写旧 trace。

### 4. Probability Semantics

#### DECISION-210 — Deterministic B3

Canonical B3 runtime MUST 写：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

MUST NOT 写 `action_propensity = 1.0`。

#### DECISION-211 — Assignment Probability Separation

`ExperimentAssignment.assignment_probability` 表示 experiment variant 分配概率；它 MUST NOT 被解释为 action selection propensity。

#### DECISION-212 — Historical Propensity Migration

历史 `experiment.propensity` 只有在 provenance 明确证明其语义时 MAY 迁移到对应字段。若语义不明：

```text
action_propensity = null
behavior_policy_type = UNKNOWN（若行为策略类型也不明）
migration_reason = AMBIGUOUS_LEGACY_PROPENSITY
replayability_status = PARTIAL
```

原始值 MAY 保留 legacy/audit metadata，MUST NOT 无条件解释成 action propensity。

### 5. v0.3 Replay Contract

#### DECISION-220

`FULL` replay 至少要求 exact TeachingContext/source versions、exact PolicyBundle、deterministic evaluator components、ExperimentAssignment 与 stable tie-break 可用。

#### DECISION-221

Canonical policy replay MUST NOT 读取当前 mutable state，也 MUST NOT 重新调用在线 LLM。缺失历史 owner version/bundle/feature source 时 MUST 返回 PARTIAL/NON_REPLAYABLE + reason code。

#### DECISION-222

同 TeachingContext + exact PolicyBundle + ExperimentAssignment MUST 产生同一个 semantic TeachingAction；否则属于 determinism defect 或 historical replayability 不足。

### 6. Decision vs Outcome

#### DECISION-230

`DecisionTrace = 当时为什么这么决定`；`OutcomeObservation = 后来实际测到了什么`。

OutcomeObservation MUST NOT 修改 candidate scores、transition reasons、feature values 或 selected-action reasoning。Delayed outcome attribution 由 Outcome contract 决定。

### 7. v0.3 Hard / Soft / Experiment Trace

#### DECISION-240

Trace MUST 区分 typed Hard Constraint filter、Soft Preference feature/score、Experiment Guardrail/assignment。Hard-filtered action MUST NOT 被 soft score/experiment 恢复。

#### DECISION-241

`learning_value_proxy` MAY 作为 soft feature，但 MUST 明确为 heuristic/proxy，MUST NOT 描述为 causal learning-effect estimate。

### 8. v0.3 Persistence / Failure

#### DECISION-250

相同 `decision_id`/idempotency key 重试 MUST NOT 创建语义重复 trace。

#### DECISION-251

Trace persistence failure 时，依赖该 trace 的 canonical action emission MUST degraded/failed；不得产生“已可 replay”的假记录。

#### DECISION-260

Trace SHOULD 通过 correlation refs 连接 TeachingAction、AssessmentResult、LearningEvent、OutcomeObservation、ExperimentAssignment、ModelInference；敏感 raw prompt/response MUST 遵循 data-minimization/retention policy。

### 9. Tests

必须覆盖：deterministic B3 `action_propensity=null`；assignment/action probability separation；ambiguous historical propensity → null + PARTIAL；losing candidates/hard filters/features/anti-oscillation/tie-break trace completeness；replay no mutable state/no online LLM；same context+bundle+assignment determinism；Outcome no trace rewrite；hard-filtered action not restored；legacy cross-system trace IDs continue semantics。

### 10. Acceptance Criteria

原有 AC 保留：

- `DECISION-AC-001`：任一 TeachingAction 可追溯到 decision-time owner inputs/versions。
- `DECISION-AC-002`：任一 MasteryEstimate update 可列出 source evidence/algorithm version。
- `DECISION-AC-003`：EvidenceBundle 被排除的高暴露 candidate 可由 reason code 解释。
- `DECISION-AC-004`：Plan replan 可说明 trigger 与前后版本。
- `DECISION-AC-005`：model fallback 有 ModelInference/route trace。
- `DECISION-AC-006`：用户看到的“为什么”可映射真实 reason codes。

新增 v0.3 AC：

- `DECISION-AC-201`：任一 SYS05 action 可恢复 decision-time context/bundle 与筛选过程。
- `DECISION-AC-202`：B3 trace 不出现 `action_propensity=1.0`。
- `DECISION-AC-203`：assignment probability 与 action propensity 独立。
- `DECISION-AC-204`：ambiguous historical propensity migration/replay status 显式。
- `DECISION-AC-205`：Outcome 不会回写历史 DecisionTrace。

### 11. Legacy Probability Mapping

旧 `experiment.propensity` 被 v0.3 assignment probability / action propensity 两套语义拆分。旧 raw value MAY read-only/audit；MUST NOT permanent dual-write 或无条件解释。

### 12. Forbidden Implementations

禁止：只保存最终动作而缺关键输入版本；无 machine-readable reason code；ModelInference/DecisionTrace 合并；ledger 反向修改领域 state；deterministic `action_propensity=1.0`；assignment probability 当 action propensity；ambiguous legacy propensity 强行解释；policy replay 调在线 LLM/当前 mutable state；Outcome 回写 DecisionTrace；current PolicyBundle 重解释历史 action；点赞/会话时长作为主要教学 reward；LLM 事后编造历史理由。

---

## Askora Learning Event Contract

> Spec ID 范围：`EVENT-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

### 1. Event Semantics

#### EVENT-001 — Command / Event / Projection Separation

- Command：希望系统执行的动作；
- Event：已发生且被系统接纳的事实；
- Projection：由事件/证据计算得到的状态。

Event MUST 使用过去时事实语义，MUST NOT 表示“希望发生什么”。

#### EVENT-002 — Immutable Event

已持久化 LearningEvent MUST append-only；业务纠正通过 correction/invalidation event，MUST NOT 原地重写历史。

#### EVENT-003 — Ledger Hosting != Business Ownership

SYS08 MAY 托管 Event Ledger，但 payload 业务语义由对应领域 owner 定义。托管权 MUST NOT 被实现为重新解释领域结论或第二 truth owner。

### 2. LearningEvent Envelope

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

### 3. Existing Envelope Constraints Retained

#### EVENT-010

`event_id` MUST 全局唯一。

#### EVENT-011

同一 aggregate 内 `(aggregate_id, aggregate_version)` MUST 唯一且 version 单调递增。

#### EVENT-012

`sequence` 表示 aggregate/stream logical order。实现 MUST NOT 假设跨 aggregate 有全局严格时序。

#### EVENT-013

`occurred_at` 与 `recorded_at` MUST 分离，不得混用。

#### EVENT-014

`idempotency_key` MUST 在 command 幂等范围唯一。重复同一用户动作 MUST 返回原/等价结果，不产生第二份学习证据。

#### EVENT-015

`correlation_id` MUST 串联一次业务 workflow/teaching round；`causation_id` SHOULD 指向直接 command/event/decision。

#### EVENT-016

事件正文 SHOULD 使用假名化标识，MUST NOT 无必要写 password、secret、完整凭据或多余 PII。

#### EVENT-017

关键 event 若由模型/算法参与且影响 mastery/plan/assessment/policy，相关 model/prompt/policy/algorithm versions MUST 可追溯。缺必要 version 时，不得成为无条件高权 evidence。

### 4. Existing Canonical Event Families Retained

#### EVENT-020 — Goal / Plan

至少支持 `GoalCreated`、`GoalConfirmed`、`PlanCreated`、`PlanReplanned`、`ActivitySelected`，由 SYS06 定义 payload 语义。

#### EVENT-021 — Content / Retrieval

至少支持 `ContentImported`、`ContentPublished`、`KnowledgeRelationPublished`、`ContentRetrieved`、`RetrievalFailed`，分别由 SYS01/SYS02 定义 payload 语义。

#### EVENT-022 — Teaching Execution

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

#### EVENT-023 — Assessment / Evidence

至少支持 `DiagnosticStarted`、`AssessmentAttemptStarted`、`ResponseSubmitted`、`ResponseRevised`、`AssessmentResultProduced/AttemptScored`、`DiagnosisProduced/DiagnosisUncertain`、`EvidenceAccepted`、`EvidenceRejected`、`MisconceptionDetected`、`MasteryProjectionUpdated`、`TransferAttemptCompleted`。

AssessmentResult/Diagnosis event MUST 能表达 `assessment_confidence` 与独立的 `diagnostic_confidence`，并允许 ErrorType `UNKNOWN`。

#### EVENT-024 — Review

至少支持 `ReviewScheduled`、`ReviewCompleted`、`ReviewScheduleUpdated`。ReviewCompleted MUST 引用 actual Attempt/AssessmentResult/assistance facts，而不是只引用计划状态。

### 5. Existing Payload Rules Retained

#### EVENT-030 — Minimal Facts, Not Full State Copy

Event payload SHOULD 保存 replay/audit 所需最小事实/引用，MUST NOT 无限制复制整个 LearnerState、文档或 Prompt。

#### EVENT-031 — Stable References for Large Objects

原始回答、文档片段、模型输出过大时 MAY 保存稳定 content ref/hash，但在 retention policy 内必须可审计。

#### EVENT-032 — Assistance Frozen at Attempt Time

`ResponseSubmitted` MUST 能还原提交时 actual assistance：

```text
assistance_state = INDEPENDENT|ASSISTED|ANSWER_EXPOSED
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

MUST NOT 在评分后根据当前 UI 或 planned TeachingAction 猜历史帮助程度。

### 6. Persistence / Delivery

#### EVENT-040 — Transactional Outbox

Domain state update 与需传播 event/outbox MUST 在相应 persistence transaction contract 下原子写入。

#### EVENT-041 — At-least-once

Consumers MUST 按 at-least-once delivery 设计，projection/side-effect consumer MUST idempotent。

#### EVENT-042 — Failure Classification

Transient infrastructure error MAY retry/backoff；schema/business validation error MUST NOT blind retry；unrecoverable poison event MUST 进入 dead-letter/review 并保留诊断。

#### EVENT-043 — Late Events

不得假设事件永不迟到。Late but valid evidence MAY 触发局部 replay/reprojection。

### 7. Schema Evolution

#### EVENT-050

`schema_version` 使用明确版本治理；minor/additive change MUST backward compatible。

#### EVENT-051

删除字段、改变字段/enum 语义等 breaking change MUST 新 major/versioned migration/upcaster strategy。

#### EVENT-052

Consumer MUST 声明支持版本范围。未知 major/enum MUST NOT 被静默解释为当前语义。

### 8. Replay

#### EVENT-060

固定 event set + fixed projection/algorithm version MUST 得到 deterministic projection。

#### EVENT-061

Replay MUST NOT 调用在线 LLM 或依赖当前 provider 重建历史判断。历史 LLM 结论必须使用已持久化结构化 result/inference；新模型重评必须显式 reassessment/recompute 并创建新版本。

#### EVENT-062

Algorithm upgrade MUST 支持 old log + old projector = old state；old log + new projector = candidate state；compare → approved migration。

### 9. Correction / Deletion

#### EVENT-070

普通错误修正 MUST 追加 correction/invalidation event，不修改原 event row。

#### EVENT-071

用户/法律删除要求下，MUST 删除受保护内容，在允许范围保留不含被删数据的 audit tombstone，并重建受影响 projection；不得继续引用已删除 evidence。

### 10. Legacy Event Naming

#### EVENT-080

旧 dotted event names 迁移时 MUST adapter 到 canonical names，MUST NOT 长期维护两套语义相同 event names。

### 11. v0.3 Adaptive Teaching Additions

#### EVENT-200 — TeachingActionDecided Detail

Teaching decision event MUST 引用 action、DecisionTrace、TeachingContext/context_fingerprint、PolicyBundle/hash、StrategyFamily、TeachingStage、validation obligation、ExperimentAssignment（如有）。

#### EVENT-201 — Actual Support / Exposure

Support/exposure event MUST 使用 v0.3 orthogonal vocabulary，并能关联 rendered response/Attempt。Legacy integer support only audit/read。

#### EVENT-202 — Assessment Diagnosis Detail

Assessment/diagnosis event MUST 支持 canonical ErrorType 7 + UNKNOWN、assessment confidence、diagnostic confidence、alternative hypotheses、needs_probe、diagnostic evidence refs。

#### EVENT-203 — Independent Validation Obligation

SYS05 MAY 记录 `IndependentValidationRequired` / `IndependentValidationSatisfied` policy-control event。`Satisfied` MUST 引用 fresh independent Attempt/AssessmentResult evidence；MUST NOT 因计划已创建、聊天继续或时间经过自动满足。

#### EVENT-210 — OutcomeObserved

OutcomeObservation MAY 发布 `OutcomeObserved`：至少引用 outcome id/version、measurement ref、independence/assistance、delay/transfer、score/success、contamination、attribution_scope、episode/trajectory/experiment refs。MUST NOT 回写 DecisionTrace。

#### EVENT-211 — ExperimentAssigned

ExperimentAssignment event MUST 使用 `assignment_probability`，MUST NOT 命名/解释为 action propensity。

#### EVENT-220 — Additive Record Ownership

OutcomeObservation/ExperimentAssignment MAY 由 durable ledger 托管，但 MUST NOT 接管八系统既有 domain truth ownership。

#### EVENT-230 — Legacy Ambiguity

旧 support/error/propensity payload 无法无损映射时 MUST 保留 raw legacy value + migration reason，并把 canonical value 标记 unknown/unavailable/partial replay；MUST NOT 猜测。

#### EVENT-231 — v0.3 Policy Replay

Policy replay MUST 使用 event-time exact object/policy versions；缺失版本必须 PARTIAL/NON_REPLAYABLE。MUST NOT 调用在线 LLM。

### 12. Acceptance Criteria

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

### 13. Forbidden Implementations

禁止：修改旧 event row；聊天消息表替代 event ledger；non-idempotent consumer 重复 mastery/review；policy replay 重新调用 LLM；完整用户文档复制进每个 payload；重复 EvidenceAccepted；仅记录 correct 而不记录 actual assistance/exposure；ledger host 取得 domain ownership；unknown diagnosis 强制分类；assignment probability 写成 action propensity；Outcome event 改写 DecisionTrace。

### 14. P1-01 Goal Events

SYS06 至少产生 `GoalDraftCreated/Previewed/Applied`、`GoalStateChanged`、`GoalFocusChanged`、
`GoalAchievementEvaluated/Confirmed`。payload 只保存 exact refs、reason codes 与 policy version；不得复制
全文资料、grader-only rubric 或把 plan/activity completion 写成 achievement。

---

## Askora Lifecycle State Machines

> Spec ID 范围：`LIFE-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

### 1. 通用规则

#### LIFE-001

公共领域对象的 `status` MUST 具有显式允许转换；Codex 不得在未更新治理合同的情况下增加可改变业务语义的新状态。用户已委托架构自治时，新增状态仍 MUST 先经 Accepted ADR、Spec 与冻结 EXEC 明确定义。

#### LIFE-002

已发布/已完成结论需要修改时，优先创建新 revision/version 并把旧版本标记 superseded，而不是回退并覆盖旧数据。

#### LIFE-003

状态转换 MUST 由对象 owner 执行，并记录产生转换的 command/event、reason code 与 trace id。

### 2. SourceDocument

Owner：4.1。

```text
imported
  → parsed
  → modeled
  → published
  → superseded

imported/parsed/modeled
  → failed
  → imported/parsed       # 明确 retry/reprocess 后产生新 processing run

任意预发布状态
  → quarantined           # 安全风险

quarantined
  → imported              # 所有者显式使用更新版安全策略复检通过
```

#### LIFE-010

只有 `published` revision 可以作为默认教学/评估事实来源。

#### LIFE-011

`quarantined` 内容不得进入检索索引或 LLM learner-visible context。

#### LIFE-012 — Explicit Quarantine Reinspection

`quarantined → imported` 不是 retry。只有资源所有者显式提交
`ReinspectQuarantinedContent`，且目标 safety scanner/policy version 与上次执行版本不同，
才 MAY 产生该转换。应用升级、worker reconciliation 或普通 processing retry MUST NOT 自动解除隔离。

每次复检 MUST 保存 append-only `SafetyScanRun`，至少包含 run id、原始资产 checksum、
scanner/policy version、阈值、verdict、reason codes 与时间。旧 run MUST NOT 被覆盖；
复检通过后仍须重新走正常 parse/model/publish 流程。

复检任务等待或执行期间对象仍按 `quarantined` 处理，不得进入 chunk projection、检索、
知识地图或 learner-visible context。复检结论为：

```text
allow/review → imported
security risk → quarantined
unsupported/corrupt → rejected processing outcome（不伪装为 security risk）
transient/internal failure → quarantined（任务可按基础设施策略 bounded retry）
```

历史隔离记录若没有 checksum，MAY 仅在本地 owner-bound 私有存储路径、持久化文件大小一致且
新版 scanner 对当前字节执行完整扫描时建立一次兼容 checksum baseline；必须记录
`LEGACY_RAW_ASSET_CHECKSUM_BASELINE_ESTABLISHED`，不得声称已证明历史字节从未变化。

### 3. KnowledgeUnit / Relation

Owner：4.1。

```text
candidate
  → verified
  → published
  → superseded

candidate/verified
  → rejected
```

#### LIFE-020

低证据 `candidate` 不得被 4.2/4.6 当作正式 hard prerequisite。

#### LIFE-021

published relation 的纠正生成新 revision 或 superseding relation，不直接改旧 edge。

### 4. LearningGoal

Owner：4.6。

```text
candidate
  → confirmed
  → active
  → achieved

active ↔ paused
confirmed/active/paused → archived
```

#### LIFE-030

未确认的 candidate goal 不得触发长期自动规划，除非产品有显式“快速开始”规则并留下等价确认记录。

### 5. LearningObjective

Owner：4.6。

```text
planned
  → active
  → satisfied

satisfied → reopened      # 新证据显示能力退化/目标提高
planned/active/reopened → superseded
```

`reopened` 不意味着旧完成记录被删除。

### 6. LearningActivity

Owner：4.6。

```text
planned
  → available
  → active
  → completed

planned/available → skipped
planned/available/active → superseded
```

#### LIFE-040

4.8 可以执行 `active` activity，但不能把另一个 activity 自行设为 active；选择权仍属于 4.6。

#### LIFE-041 — Canonical Activity Lifecycle

activity current status 由 SYS06-owned、append-only、单调版本 `LearningActivityStateV1` 决定。
`LearningActivity` definition payload 中的 status 只表示创建时 initial/legacy snapshot；cutover 后
不得原地更新，也不得由 transcript、UI local state 或 event recency 推断 current status。

#### LIFE-042 — Completion Boundary

`active → completed` 必须经过 versioned、idempotent owner command 与 type-specific completion
precondition。completed 只表示该计划任务执行结束，MUST NOT 自动写 MasteryEstimate、把
LearningObjective 设为 satisfied 或把 LearningGoal 设为 achieved。

#### LIFE-043 — Atomic Progression

活动完成、`ActivityCompleted` event/outbox 与下一 eligible activity 的 `planned → available`
必须由 SYS06 原子提交。没有剩余非终态 activity 时 plan MAY completed；goal achievement 仍需
独立冻结合同。详细合同见 `../systems/06-activity-lifecycle.md`。

### 7. LearningPlan

Owner：4.6。

```text
active
  → completed
active ↔ paused
active/paused → superseded
```

#### LIFE-050

Replan MUST 创建新 plan version；旧 active version 转为 superseded。不得原地重排历史 activity 后假装仍是同一版本。

### 8. AssessmentItem

Owner：4.4。

```text
draft
  → reviewed
  → active
  → retired

draft/reviewed → retired
```

#### LIFE-060

模型生成 item MUST 从 `draft` 开始。

#### LIFE-061

`active` item 的 answer/rubric/claim 发生语义修改时 MUST 创建新 item version。

### 9. Attempt

Owner：4.4。

Attempt 的生命周期状态建议：

```text
started
  → submitted
  → scored

started → abandoned
submitted → scoring_failed
scoring_failed → scored      # 明确 retry 后
```

#### LIFE-070

提交后的回答修订不得覆盖旧提交；使用 response revision chain 并保留 assistance snapshot。

#### LIFE-071

`scoring_failed` 不得产生高权 EvidenceAccepted。

### 10. AssessmentResult

Owner：4.4。

AssessmentResult 结论采用版本化而非可变 status：

```text
result v1 accepted/rejected/needs_review
→ reassessment
→ result v2 supersedes v1
```

#### LIFE-080

重新评分不得静默覆盖 v1。

### 11. Learner Evidence

Owner：4.3 对 evidence eligibility 的最终接纳。

```text
candidate
  → accepted
candidate → rejected
accepted → invalidated       # 后续发现题目/评分/数据损坏
```

#### LIFE-090

`invalidated` evidence 必须触发相关 MasteryEstimate 的 replay/recompute。

### 12. MasteryEstimate / LearnerState

Owner：4.3。

它们采用 immutable version stream，不使用 mutable workflow status：

```text
v1 → v2 → v3 ...
```

UI 派生标签 MAY 为：

```text
insufficient_evidence
forming
basic_mastery
stable_mastery
transfer_capable
```

#### LIFE-100

标签是投影结果，不是用户可直接写状态。

#### LIFE-101

`stable_mastery` 不得仅由一次即时正确或单一 probability threshold 触发。

### 13. TeachingStrategy

Owner：4.5。

```text
draft → active → retired
```

策略内容语义改变时创建新 semantic version。

### 14. TeachingAction

Owner：4.5。

TeachingAction 是单轮不可变决策。执行状态属于 4.8，二者必须区分：

```text
TeachingAction created (4.5)
  ↓
WorkflowStep pending/running/succeeded/failed (4.8)
```

#### LIFE-110

执行失败不得修改原 TeachingAction；若教学语义需要变化，4.5 创建新 action。

### 15. ReviewSchedule

Owner：4.7。

采用 version stream：

```text
schedule v1
→ valid retrieval evidence
→ schedule v2
→ ...
```

可派生：

```text
not_due | due | overdue
```

#### LIFE-120

`due/overdue` 是时间投影，不需要修改 schedule row 才成立。

#### LIFE-121

实际复习执行时间与推荐 `next_due_at` 必须分别记录。

### 16. WorkflowRun

Owner：4.8。

```text
pending
  → running
  → succeeded
running → failed_retriable → running
running → failed_terminal
running → cancelled
```

#### LIFE-130

有副作用的 tool step 重试必须带幂等键或 side-effect reconciliation；不得因自动 retry 重复创建外部副作用。

#### LIFE-131

恢复运行必须固定 workflow/prompt/policy 版本，除非显式启动新的 run。

### 17. ModelRouteProfile Activation

Owner：4.8；desktop Electron 是 storage/activation adapter。

```text
no desktop revision → external_read_only | unconfigured
candidate (transient) → probing → active(new revision)
active → probing replacement → active(new revision)
active | external_read_only → disabled(new tombstone revision)
probing/applying failure → prior revision restored | rollback_failed
```

#### LIFE-132

候选 credential 在探测成功前 MUST NOT 成为 active revision。探测只使用固定 synthetic text，不携带个人资料、学习历史或用户资料内容。

#### LIFE-133

激活必须是 revision-aware 的事务式序列：probe → encrypted atomic write → backend restart/readiness → runtime revision verification。任一步失败必须恢复上一 encrypted revision 并重启旧配置；rollback 失败必须显式报告，不能声称旧配置已恢复。

#### LIFE-134

clear 必须创建 `DISABLED` tombstone；不得编辑或删除用户 `.env`。同一 candidate/revision 的重复 command 必须幂等或以稳定 revision conflict 拒绝。

### 18. Feedback Dispute

当用户争议 learner state / assessment / content 时：

```text
FeedbackSignal
→ open dispute/review
→ validate evidence or retest
→ accepted_correction | rejected_dispute | unresolved
→ new domain version if needed
```

#### LIFE-140

用户纠错不能跳过对应 owner，直接修改 canonical state。

### 19. Acceptance Criteria

- `LIFE-AC-001`：quarantined SourceDocument 无法进入 learner-visible retrieval。
- `LIFE-AC-008`：没有显式 owner command 或 scanner/policy version 未变化时，quarantined SourceDocument 无法出站。
- `LIFE-AC-009`：复检保留旧 SafetyScanRun；失败或仍有风险时内容继续不可见。
- `LIFE-AC-002`：模型生成 AssessmentItem 未 review/validate 前不能 active。
- `LIFE-AC-003`：replan 后旧 LearningPlan 可查询且标记 superseded。
- `LIFE-AC-004`：AssessmentResult 重评产生新版本而非覆盖。
- `LIFE-AC-005`：invalidated evidence 会触发 mastery recompute。
- `LIFE-AC-006`：TeachingAction 执行失败不会原地改变教学策略。
- `LIFE-AC-007`：WorkflowRun 重试不会重复不可逆副作用。
- `LIFE-AC-010`：失败候选不会覆盖上一 active ModelRouteProfile。
- `LIFE-AC-011`：激活后 backend runtime revision 与 encrypted desktop revision 一致。
- `LIFE-AC-012`：clear 后重启保持 DISABLED，rollback failure 可见。

### 20. Forbidden Implementations

禁止：

- 任意字符串 status 且无转换校验；
- 修改 `published` KnowledgeUnit 内容但保留相同 revision；
- 原地编辑已完成 LearningPlan；
- 模型生成题直接 `active`；
- 重评分数覆盖旧 AssessmentResult；
- 把 WorkflowRun failure 当成 TeachingAction failure 并自动改教学策略；
- probe 前保存候选 credential 为 active；
- 激活失败后仍把新 revision 显示为已生效；
- clear 仅删除内存值而允许 `.env` 重启恢复；
- 用户点击“我会了”直接把 mastery label 改成 stable_mastery。

### 19. P1-01 Definition, Draft and Goal State

Definition immutable version stream；draft：`draft → preview_ready → applying → applied`，active activity
时 `preview_ready → approved_pending_boundary → applying`；任意未应用状态可 `blocked|cancelled`。

Goal State：`confirmed → active ↔ paused`、`active → achieved`、
`confirmed|active|paused → archived`；achieved/archived terminal。Plan State：
`active ↔ paused`、`active|paused → superseded`、`active → completed`。所有转换由 SYS06 写新 row。
