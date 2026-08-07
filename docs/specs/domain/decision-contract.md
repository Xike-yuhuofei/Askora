# Askora Decision Trace Contract

> Spec ID 范围：`DECISION-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Purpose

Askora 的关键决策 MUST 能回答：当时看到了什么、有哪些候选、受什么约束、为什么选择该结果、由哪个算法/策略/模型/PolicyBundle 版本产生。

DecisionTrace 是 immutable audit/replay record，不是新的业务状态 owner；它记录**当时为什么这样决定**，与后续 OutcomeObservation 严格分离。

## 2. Existing Cross-system Contracts Retained

### DECISION-001 — Decision Payload Ownership

做出业务决策的领域系统负责产生 DecisionTrace payload；SYS08 Decision Ledger MAY 负责 append-only 持久化、索引和查询。

### DECISION-002 — Ledger Must Not Rewrite Semantics

SYS08 MUST NOT 修改 `selected_action`、`reason_codes`、candidate/score 或其他领域决策语义来“修复”记录。

### DECISION-010 — SYS01 High-impact Knowledge Publication

KnowledgeUnit merge/split、hard prerequisite publish/reject 与高影响人工审核 MUST 有 trace。

### DECISION-011 — SYS02 EvidenceBundle Selection

MUST 记录 retrieval request、主要 candidates/rank source、hard filter reason、selected evidence、exposure filter、missing/conflict。

### DECISION-012 — SYS03 MasteryEstimate Update

MUST 记录 evidence ids/weights、prior/new state version、algorithm/config version 与 reason codes。

### DECISION-013 — SYS04 Non-trivial Assessment

开放题、模型辅助评分、evaluator conflict 或 misconception diagnosis MUST 记录 evaluator results、rubric/version、constraints/adjudication 与 selected AssessmentResult。纯 deterministic grader MAY 使用精简 trace。

### DECISION-014 — SYS05 TeachingAction

MUST 记录全部可行动作候选、typed hard filters、features/scores、anti-oscillation、tie-break、最终 TeachingAction 与 reason codes，并满足 v0.3 `DECISION-200..222`。

### DECISION-015 — SYS06 Plan / Replan

MUST 记录 feasible candidates、prerequisite/deadline/time constraints、priority factors、selected activities 与 replan trigger。

### DECISION-016 — SYS07 ReviewSchedule Update

MUST 记录 prior memory state、valid retrieval evidence、desired retention、new next_due_at、scheduler/model version。

### DECISION-017 — SYS08 High-impact Route / Degradation

隐私导致的 model choice、primary-model fallback、tool permission denial、validation-triggered retry/degradation 与影响质量/成本的重要 route MUST 有 trace。

### DECISION-020 — Stable Reason Codes

每个关键决策 MUST 至少有一个稳定、机器可查询 reason code。自然语言解释 MAY 附加，MUST NOT 替代 reason code。

### DECISION-021 — Reason-code Versioning

Reason code 发布后 MUST NOT 复用同一 code 改变含义；语义变化必须新 code 或新主版本。

### DECISION-030 — Candidate Retention

存在真实候选选择时，trace MUST 保存足够 candidates/features/scores/eligibility 支持 replay/shadow/counterfactual comparison；MUST NOT 只保存赢家。

### DECISION-031 — Hard vs Soft Separation

Hard constraint 与 soft score MUST 分开记录。Hard constraint MUST NOT 仅表示为可被高分抵消的 penalty。v0.3 soft example 使用 `learning_value_proxy`，该值 MUST NOT 被称为 causal learning-effect estimate。

### DECISION-040 — Confidence

`confidence` 只有在有明确定义/校准方法时才 MAY 使用；否则 MUST null 或使用离散 reason code，MUST NOT 让 LLM 自报 0.93 作为系统置信度。

### DECISION-050 — ModelInference Link

模型参与关键决策时 MUST 通过 `model_inference_ids`/等价 versioned refs 关联 ModelInference，而不是只记录模型名字。

### DECISION-051 — Model Output != Final Decision

`ModelInference = 模型产生了什么`；`DecisionTrace = 领域系统最终接受了什么、为什么`。二者 MUST 分离。

### DECISION-060 — Experiment Logging, v0.3 Clarified

Experiment MUST 记录 experiment id/version、variant、assignment unit、assignment probability 与可用 guardrail/context。只有行为策略本身真实 stochastic 时才 MAY 记录 action propensity。Deterministic B3 MUST 服从 `DECISION-210`。

### DECISION-061 — OPE Claim Boundary

若未来进行 IPS/SNIPS/DR 等 causal off-policy analysis，必须有真实 behavior-policy action availability/propensity 语义。v0.3 canonical runtime 不实施 causal RL OPE；assignment probability MUST NOT 伪装 action propensity。

### DECISION-062 — Reward / Outcome Boundary

实验主要学习目标 MUST NOT 使用聊天时长、点击率、点赞、hint/token/session duration 替代真实学习 outcome；这些只能作为 process/experience guardrail。

### DECISION-070 — Replay Uses

DecisionTrace MUST 支持历史解释、同版本 replay、新旧算法 shadow compare、candidate counterfactual compare 与回滚定位（在可用数据边界内）。

### DECISION-071 — Replayability Gap

历史输入/version 不可取得时 MUST 明确标记 replayability 缺口，MUST NOT 声称 FULL replay。

### DECISION-080 — User-facing Explanation

用户可见“为什么” SHOULD 从稳定 reason codes + 真实 evidence 生成，MUST NOT 由 LLM 事后自由编造。

### DECISION-090 — Append-only

DecisionTrace MUST append-only；更正通过新 trace/correction record，MUST NOT 原地修改历史。

### DECISION-091 — Ledger Indexing

Decision Ledger SHOULD 支持按 decision_id/type、owner_system、correlation/trace id、input entity、algorithm/PolicyBundle version、experiment id、created_at 查询。

## 3. DecisionTrace v0.3

### DECISION-200 — Required Shape

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

### DECISION-201 — Teaching Trace Completeness

SYS05 trace MUST 保存 all available candidates、hard-filter reasons、feature availability/confidence/version、candidate scores、selected/previous action、transition/material evidence、anti-oscillation、tie-break reason。MUST NOT 只保存赢家。

### DECISION-202 — Immutable Historical Semantics

DecisionTrace MUST 固定 decision-time TeachingContext、PolicyBundle/source versions。后续 LearnerState、PolicyBundle、OutcomeObservation MUST NOT 回写旧 trace。

## 4. Probability Semantics

### DECISION-210 — Deterministic B3

Canonical B3 runtime MUST 写：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

MUST NOT 写 `action_propensity = 1.0`。

### DECISION-211 — Assignment Probability Separation

`ExperimentAssignment.assignment_probability` 表示 experiment variant 分配概率；它 MUST NOT 被解释为 action selection propensity。

### DECISION-212 — Historical Propensity Migration

历史 `experiment.propensity` 只有在 provenance 明确证明其语义时 MAY 迁移到对应字段。若语义不明：

```text
action_propensity = null
behavior_policy_type = UNKNOWN（若行为策略类型也不明）
migration_reason = AMBIGUOUS_LEGACY_PROPENSITY
replayability_status = PARTIAL
```

原始值 MAY 保留 legacy/audit metadata，MUST NOT 无条件解释成 action propensity。

## 5. v0.3 Replay Contract

### DECISION-220

`FULL` replay 至少要求 exact TeachingContext/source versions、exact PolicyBundle、deterministic evaluator components、ExperimentAssignment 与 stable tie-break 可用。

### DECISION-221

Canonical policy replay MUST NOT 读取当前 mutable state，也 MUST NOT 重新调用在线 LLM。缺失历史 owner version/bundle/feature source 时 MUST 返回 PARTIAL/NON_REPLAYABLE + reason code。

### DECISION-222

同 TeachingContext + exact PolicyBundle + ExperimentAssignment MUST 产生同一个 semantic TeachingAction；否则属于 determinism defect 或 historical replayability 不足。

## 6. Decision vs Outcome

### DECISION-230

`DecisionTrace = 当时为什么这么决定`；`OutcomeObservation = 后来实际测到了什么`。

OutcomeObservation MUST NOT 修改 candidate scores、transition reasons、feature values 或 selected-action reasoning。Delayed outcome attribution 由 Outcome contract 决定。

## 7. v0.3 Hard / Soft / Experiment Trace

### DECISION-240

Trace MUST 区分 typed Hard Constraint filter、Soft Preference feature/score、Experiment Guardrail/assignment。Hard-filtered action MUST NOT 被 soft score/experiment 恢复。

### DECISION-241

`learning_value_proxy` MAY 作为 soft feature，但 MUST 明确为 heuristic/proxy，MUST NOT 描述为 causal learning-effect estimate。

## 8. v0.3 Persistence / Failure

### DECISION-250

相同 `decision_id`/idempotency key 重试 MUST NOT 创建语义重复 trace。

### DECISION-251

Trace persistence failure 时，依赖该 trace 的 canonical action emission MUST degraded/failed；不得产生“已可 replay”的假记录。

### DECISION-260

Trace SHOULD 通过 correlation refs 连接 TeachingAction、AssessmentResult、LearningEvent、OutcomeObservation、ExperimentAssignment、ModelInference；敏感 raw prompt/response MUST 遵循 data-minimization/retention policy。

## 9. Tests

必须覆盖：deterministic B3 `action_propensity=null`；assignment/action probability separation；ambiguous historical propensity → null + PARTIAL；losing candidates/hard filters/features/anti-oscillation/tie-break trace completeness；replay no mutable state/no online LLM；same context+bundle+assignment determinism；Outcome no trace rewrite；hard-filtered action not restored；legacy cross-system trace IDs continue semantics。

## 10. Acceptance Criteria

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

## 11. Legacy Probability Mapping

旧 `experiment.propensity` 被 v0.3 assignment probability / action propensity 两套语义拆分。旧 raw value MAY read-only/audit；MUST NOT permanent dual-write 或无条件解释。

## 12. Forbidden Implementations

禁止：只保存最终动作而缺关键输入版本；无 machine-readable reason code；ModelInference/DecisionTrace 合并；ledger 反向修改领域 state；deterministic `action_propensity=1.0`；assignment probability 当 action propensity；ambiguous legacy propensity 强行解释；policy replay 调在线 LLM/当前 mutable state；Outcome 回写 DecisionTrace；current PolicyBundle 重解释历史 action；点赞/会话时长作为主要教学 reward；LLM 事后编造历史理由。