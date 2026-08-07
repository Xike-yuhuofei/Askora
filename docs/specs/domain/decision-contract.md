# Decision Contract

> Spec ID：`DECISION-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Purpose

DecisionTrace 记录**决策发生当时为什么这样决定**。它 MUST immutable、可审计、可 replay，并与后续 OutcomeObservation 严格分离。

### DECISION-001

所有会改变 canonical system behavior 的关键决策 SHOULD 有 DecisionTrace；SYS05 TeachingAction selection MUST 有 DecisionTrace。

## 2. DecisionTrace v0.3

### DECISION-200 — Required Shape

```yaml
decision_trace:
  decision_id: uuid
  decision_schema_version: string
  decision_type: teaching_action_selection|string
  decision_time: datetime

  teaching_context_ref: versioned_ref
  teaching_context_schema_version: string
  context_fingerprint: string
  context_source_refs: [versioned_ref]

  policy_bundle_ref: versioned_ref
  policy_bundle_hash: string
  policy_version: string

  strategy_family: string
  strategy_version: string
  derived_teaching_stage: string
  stage_mapper_version: string

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
  selected_teaching_action_ref: versioned_ref
  previous_teaching_action_ref: versioned_ref|null

  transition_reason_codes: [string]
  material_evidence_refs: [versioned_ref]
  anti_oscillation_decision: object
  tie_break_reason: string|null

  experiment_assignment_ref: versioned_ref|null
  experiment_assignment_probability: float|null

  behavior_policy_type: DETERMINISTIC|STOCHASTIC_EXPERIMENTAL|UNKNOWN
  action_propensity: float|null

  replayability_status: FULL|PARTIAL|NON_REPLAYABLE
  replayability_reason_codes: [string]
  migration_metadata: object|null

  created_at: datetime
```

### DECISION-201 — Trace Completeness

SYS05 trace MUST 保存所有 available candidates、hard-filter reasons、feature availability/confidence/version、candidate scores、selected/previous action、transition/material evidence、anti-oscillation 与 tie-break reason。MUST NOT 只保存赢家。

### DECISION-202 — Immutable Historical Semantics

DecisionTrace MUST 固定 decision-time TeachingContext、PolicyBundle 与 source versions。后续 LearnerState、PolicyBundle 或 OutcomeObservation 变化 MUST NOT 回写修改旧 trace。

## 3. Probability Semantics

### DECISION-210 — Deterministic B3

canonical B3 runtime MUST 写：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

`action_propensity = 1.0` 禁止，因为 deterministic selection 没有需要伪装成概率的 stochastic propensity。

### DECISION-211 — Assignment Probability Separation

`ExperimentAssignment.assignment_probability` 表示实验 variant 分配概率；它 MUST NOT 被解释为 action selection propensity。

```text
experiment assignment probability
!=
action selection propensity
```

### DECISION-212 — Historical Propensity

历史 `experiment.propensity` 只有在 provenance 明确证明其表示 assignment probability 或真实 stochastic behavior propensity 时 MAY 迁移到对应字段。

若语义不明：

```text
action_propensity = null
behavior_policy_type = UNKNOWN（若历史行为策略类型也不明）
migration_reason = AMBIGUOUS_LEGACY_PROPENSITY
replayability_status = PARTIAL
```

原始值 MAY 保留为 legacy/audit metadata，MUST NOT 无条件解释成 action propensity。

## 4. Replay Contract

### DECISION-220

`FULL` replay 至少要求 exact TeachingContext snapshot/source versions、exact PolicyBundle、deterministic evaluator components、experiment assignment 与 stable tie-break 可用。

### DECISION-221

Canonical policy replay MUST NOT 重新读取当前 mutable state，也 MUST NOT 重新调用在线 LLM。缺失历史 owner version/bundle/feature source 时 MUST 返回 PARTIAL/NON_REPLAYABLE，并给 reason code。

### DECISION-222

同 TeachingContext + exact PolicyBundle + ExperimentAssignment MUST 产生同一个 semantic TeachingAction；若不能，属于 determinism defect 或历史 replayability 不足。

## 5. Decision vs Outcome

### DECISION-230

`DecisionTrace = 当时为什么这么决定`；`OutcomeObservation = 后来实际测到了什么`。

OutcomeObservation MUST NOT 修改 candidate score、transition reason、feature value 或 selected-action reasoning。延迟 outcome 的 attribution 在 Outcome contract 中处理。

## 6. Hard / Soft / Experiment Trace

### DECISION-240

Trace MUST 能区分：

- typed Hard Constraint filter；
- Soft Preference feature/score；
- Experiment Guardrail/assignment。

Hard-filtered action MUST NOT 出现在被 soft score/experiment 恢复后的合法候选集中。

### DECISION-241

`learning_value_proxy` MAY 作为 soft feature 名称，但 trace/documentation MUST 明确它是 heuristic/proxy，MUST NOT 称为 causal learning-effect estimate。

## 7. Persistence / Idempotency

### DECISION-250

DecisionTrace MUST append-only/immutable。相同 `decision_id` 或 idempotency key 重试 MUST NOT 创建语义重复记录。

### DECISION-251

trace persistence 失败时，依赖该 trace 的 canonical action emission MUST degraded/failed；不得把无审计决策标为 replayable。

## 8. Observability / Security

### DECISION-260

Trace SHOULD 可通过 correlation id 连接 TeachingAction、AssessmentResult、LearningEvent、OutcomeObservation、ExperimentAssignment、ModelInference；敏感 raw prompt/response 不应为方便 debug 无限复制到 trace。

## 9. Tests

必须覆盖：

- deterministic B3 `action_propensity=null`；
- assignment probability/action propensity 分离；
- ambiguous historical propensity → null + PARTIAL；
- trace includes losing candidates/hard filters/features/anti-oscillation/tie-break；
- full replay 不读 mutable state、不调用在线 LLM；
- same context+bundle+assignment deterministic；
- OutcomeObservation 不修改 trace；
- hard-filtered action 不被 scoring/experiment 恢复。

## 10. Acceptance Criteria

- `DECISION-AC-201`：任一 SYS05 action 可从 trace 恢复 decision-time context/bundle 与筛选过程。
- `DECISION-AC-202`：B3 trace 不出现 `action_propensity=1.0`。
- `DECISION-AC-203`：assignment probability 与 action propensity 有独立字段和语义。
- `DECISION-AC-204`：历史 ambiguous propensity 的 migration/replay status 显式。
- `DECISION-AC-205`：Outcome 不会回写历史 DecisionTrace。

## 11. Superseded v0.2 Register

以下旧要求保留审计含义但不再是 v0.3 canonical behavior：

- 旧 `DECISION-031` 中 `expected_learning_value` 示例由 `DECISION-241` 的 `learning_value_proxy` 语义替代；
- 旧 `DECISION-060` 将 A/B/Bandit/OPE 混合描述的 propensity 语义由 `DECISION-210..212` 明确拆分；
- 旧 `experiment.propensity` 字段由 v0.3 assignment probability / action propensity 两套字段替代。

旧字段 MAY read-only/audit，MUST NOT 双写为第二 canonical probability truth。

## 12. Forbidden Implementations

禁止：

- deterministic policy 写 `action_propensity=1.0`；
- 把 experiment assignment probability 当 action propensity；
- ambiguous legacy propensity 强行解释；
- 只记录 selected action、不记录候选/过滤过程；
- replay 重新调用在线 LLM 或读取当前 mutable state；
- OutcomeObservation 回写 DecisionTrace；
- dynamic/current PolicyBundle 重解释历史 action；
- 把 `learning_value_proxy` 宣称为 causal effect。