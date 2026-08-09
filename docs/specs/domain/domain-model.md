# Askora Canonical Domain Model

> Spec ID 范围：`DOMAIN-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Purpose

本文件定义八类技术系统跨边界共享的最小领域语义。系统内部 MAY 有私有对象，但 MUST NOT 复制、改变或模糊这些公共对象含义。v0.3 canonical truth 以本文件、`decision-contract.md` 与各系统 Spec 为准；legacy 字段只允许按迁移合同 read/audit。

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

## 23. Forbidden Domain Shortcuts

禁止长期公共 `TutorState` 同时塞 mastery/plan/review/action；`AIJudgement` 同时承担 scoring+mastery；`KnowledgeChunk` 同时表示 retrieval chunk+KnowledgeUnit；无 provenance 的 `UserSkillScore`；不区分 LearningActivity/TeachingAction 的 `NextAction`；同时表示 retrievability/mastery 的 `MemoryScore`；LLM/Agent 持久化 LearnerState、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule。

## 24. P1-01 Goal Management Additions

`LearningGoalDefinitionV2` 是不含 current status 的 immutable semantic version；
`LearningGoalStateV1` 与 `LearningPlanStateV1` 是 append-only current truth；draft/preview/focus 是
SYS06-owned control records。`LearningObjectiveV1` 把 criterion、cognitive process、target refs 与
evidence requirements 结构化。`GoalAchievementEvaluationV1` 是证据门禁决定，不是 mastery truth。
