# Askora v0.3 DR-03-03 Teaching Policy 决策算法与数据契约研究

> 状态：Deep Research / Research Delta  
> 基线：Askora v0.2 FROZEN + DR-03-01 + DR-03-02  
> 研究范围：SYS05 Teaching Policy  
> 约束：不采用 RL；不改变冻结 state ownership；本报告不是 Canonical Design / Spec

---

## 1. Executive Summary

### 1.1 核心结论

Askora v0.3 不应在 A–F 中选择一种“纯架构”，而应采用组合式的：

> **Constrained Deterministic Policy Stack（约束式确定性教学策略栈）**

```text
TeachingContext snapshot
        ↓
Layer 1 — Typed Hard Constraints
        ↓
Layer 2 — Derived Teaching Stage + Transition Guards
        ↓
Layer 3 — Typed Candidate Generation / Decision Tables
        ↓
Layer 4 — Normalized Weighted Scoring
        ↓
Layer 4.5 — Anti-Oscillation Transition Gate
        ↓
Layer 5 — Deterministic Tie-break
        ↓
Layer 6 — Immutable TeachingAction
        ↓
DecisionTrace
```

它本质上是：

**E. Hard Constraints + Weighted Scoring** 作为主体，吸收：

- **B. Decision Table**：用于候选生成；
- **C. FSM/HSM**：用于 episode transition semantics；
- **A. Rules**：仅用于不可违背的不变量；

而不是采用：

- 通用 Rule Engine；
- 完整 MCDA/AHP Runtime；
- Supervised Ranking；
- Contextual Bandit；
- RL。

这与现有 SYS05 已冻结的：

```text
hard constraints
→ strategy state machine
→ candidate generation
→ weighted action scoring
→ deterministic tie-break
→ TeachingAction
```

完全一致，无需推翻现有架构。

### 1.2 六个最重要的设计决定

1. **Hard Constraint 永远不能被 score 抵消。**
2. **Teaching Stage 是 activity-specific derived policy feature，不是 LearnerState。**
3. **State Machine 描述转换规则，不新增第二套学习者状态。**
4. **Weighted Score 只比较已经合法的候选动作。**
5. **策略切换默认 sticky；没有 material new evidence 就不切换。**
6. **v0.3 收集未来学习算法需要的数据，但 deterministic policy 不伪造 propensity。**

### 1.3 为什么现在不采用 Bandit

当前 Askora 缺少：

- randomized action coverage；
- 真实 action propensity；
- 多策略重叠数据；
- 稳定 delayed retention / transfer outcome；
- 可靠 OPE；
- 足够证据证明长期序列决策复杂度值得。

v0.3 范围分析已经明确指出这些缺口，因此此时上 Bandit/RL 会把“算法先进程度”置于“数据可识别性”之前。

**Evidence Strength：High（架构约束） / Medium（具体组合设计）**  
**Applicability to Askora：Direct**

---

## 2. Frozen Constraints

### 2.1 v0.2 冻结边界

v0.2 已冻结：

```text
Material / SourceSpan
→ LearningGoal / LearningActivity
→ TeachingAction
→ EvidenceBundle
→ deterministic AssessmentResult
→ LearnerEvidence
→ MasteryEstimate
→ ReviewSchedule
→ LearningPlan
→ replay / recovery
```

并明确后续不得从代码反推新的 canonical architecture。

因此 DR-03-03 必须接受：

| Canonical Truth | Owner |
|---|---|
| AssessmentResult | SYS04 |
| LearnerState / MasteryEstimate / MisconceptionHypothesis | SYS03 |
| TeachingStrategy / TeachingAction | SYS05 |
| EvidenceBundle | SYS02 |
| LearningActivity / Plan | SYS06 |
| ReviewSchedule | SYS07 |
| execution state | SYS08 |

`STATE-001` 的核心是不允许多个模块共同拥有同一个状态。

### 2.2 SYS05 不得产生第二 LearnerState

SYS05 可以读取：

- mastery；
- mastery confidence；
- prerequisites；
- AssessmentResult；
- diagnostic confidence；
- misconceptions；
- prior assistance；
- review context；
- previous TeachingAction outcome。

但不得写：

- mastery；
- misconception hypothesis；
- error diagnosis truth；
- LearningPlan；
- ReviewSchedule。

因此：

> `TeachingStage` 不能成为新的 learner truth。

### 2.3 LLM 边界

DR-03-01 / DR-03-02 已冻结：

> LLM 可以帮助语义分析和执行 TeachingAction，但不得改变 policy decision、exposure ceiling、LearnerState 或最终 TeachingAction。

---

## 3. Candidate Architecture Comparison

| 架构 | Deterministic | 可审计 | 复杂权衡 | Anti-Oscillation | 可扩展性 | v0.3 结论 |
|---|---|---|---|---|---|---|
| A Pure Rule | 强 | 强 | 弱 | 弱 | 易 if/else 爆炸 | **局部保留** |
| B Decision Table | 强 | 很强 | 中 | 弱 | 维度多后组合爆炸 | **用于 Candidate Generation** |
| C FSM/HSM | 强 | 强 | 弱 | 很强 | 状态过多会爆炸 | **用于 transition semantics** |
| D Rule Engine | 可强 | 中 | 强 | 中 | DSL 治理复杂 | **拒绝 baseline** |
| E Hard Constraints + Weighted Scoring | 强 | 强 | 很强 | 中 | 很强 | **核心方案** |
| F Full MCDA | 强 | 中强 | 很强 | 弱 | 方法学负担较高 | **仅分析工具** |
| G Supervised Ranking | 可强 | 中 | 很强 | 需额外设计 | 依赖数据 | **未来** |
| H Contextual Bandit | 否 | 中 | 很强 | 需额外设计 | 依赖随机探索 | **未来** |

Decision Table 本身非常适合表达清晰、可验证的业务决策，但 Askora 没有必要引入完整 DMN/FEEL 运行时；OMG DMN 的价值更多说明“结构化 decision table”比任意规则文本更容易审计。

Weighted-sum 方法适合候选数量和指标数量有限、透明性要求高的决策问题，但结果会受到权重和 normalization 影响，因此必须做 sensitivity analysis。

**Evidence Strength：Medium**  
**Applicability：Direct**

---

## 4. Recommended Policy Architecture

### 4.1 推荐架构

```text
                 ┌───────────────────────┐
                 │ TeachingContext       │
                 │ immutable snapshot    │
                 └───────────┬───────────┘
                             ↓
                ┌────────────────────────┐
                │ Hard Constraint        │
                │ admissibility envelope │
                └───────────┬────────────┘
                            ↓
                ┌────────────────────────┐
                │ Derived Policy Stage   │
                │ + obligations          │
                └───────────┬────────────┘
                            ↓
                ┌────────────────────────┐
                │ Candidate Generator    │
                │ typed tables/catalog   │
                └───────────┬────────────┘
                            ↓
                ┌────────────────────────┐
                │ Feature Builder        │
                │ value + confidence     │
                └───────────┬────────────┘
                            ↓
                ┌────────────────────────┐
                │ Weighted Scorer        │
                └───────────┬────────────┘
                            ↓
                ┌────────────────────────┐
                │ Transition Guard       │
                │ hysteresis / dwell     │
                └───────────┬────────────┘
                            ↓
                ┌────────────────────────┐
                │ Deterministic Selector │
                └───────────┬────────────┘
                            ↓
                ┌────────────────────────┐
                │ TeachingAction         │
                │ immutable              │
                └────────────────────────┘
```

### 4.2 推荐执行流程

```text
1. resolve immutable PolicyBundle
2. validate TeachingContext
3. calculate hard admissibility envelope
4. derive policy stage / active obligations
5. generate candidate actions
6. hard-filter candidate actions
7. compute features + confidence
8. calculate normalized scores
9. apply transition / anti-oscillation rules
10. deterministic tie-break
11. emit immutable TeachingAction
12. append canonical DecisionTrace
```

整个流程必须是：

> **pure deterministic decision function + append-only audit result**

而不是会在运行中自行改变规则的 agent。

---

## 5. Hard Constraint Layer

### 5.1 Hard Constraint 应表达“绝对禁止”，而不是“偏好”

推荐原则：

> Hard rules 尽量负责 **disqualify**，不要直接指定唯一 TeachingAction。

这样能避免重新演化成巨大 if/else。

#### v0.3 Hard Constraint Categories

| 类别 | 示例 |
|---|---|
| State ownership | SYS05 不得修改 LearnerState / objective |
| Assessment integrity | no-hint assessment 禁止高 answer exposure |
| Objective integrity | TeachingAction 不得改变当前 LearningActivity objective |
| Exposure integrity | answer-exposed 后不能把该表现当独立验证 |
| Prerequisite safety | 严重 prerequisite gap 时禁止继续同难度独立挑战 |
| Failure ceiling | 达到 repeated-failure ceiling 后禁止原样低支架重复 |
| Scaffold ceiling | 已有稳定独立证据时禁止无理由增加高支架 |
| Low-confidence safety | 低置信度时禁止高度个性化、强诊断依赖动作 |
| Compatibility | strategy / move / activity 类型必须兼容 |
| Unsupported config | 未知 strategy/action/config 不能执行 |
| User override boundary | 用户直接答案请求与 assessment integrity 冲突时 integrity 优先 |

现有 SYS05 已明确 hard constraints 不能被 soft score 抵消。

### 5.2 哪些不应该 Hard Code

以下主要属于 soft preference：

- worked example 是否比 direct explanation 更好；
- question 是否比 explanation 更好；
- remediation representation 选择；
- review fit；
- time cost；
- cognitive load；
- mild hint dependency risk；
- 哪个合法动作预期教学价值更高。

### 5.3 Hard-rule conflict

若：

```text
Hard Rules
→ eligible_action_set = ∅
```

不得：

- 忽略某条 hard rule；
- 让 scorer 选择；
- 交给 LLM 仲裁。

必须输出：

```text
POLICY_HARD_CONSTRAINT_CONFLICT
```

并进入显式 safe fallback / fail-closed 路径。

---

## 6. Teaching Stage Layer

### 6.1 Stage 应是 Derived Feature

核心结论：

> **Teaching Stage 是 SYS05 根据当前 TeachingContext 派生出的 policy-control interpretation，不是持久化 LearnerState。**

可表达为：

```text
DerivedTeachingStage =
f(
  LearningActivity,
  MasteryEstimate,
  mastery_confidence,
  AssessmentResult,
  diagnostic_confidence,
  assistance_history,
  exposure_history,
  review_context,
  previous TeachingAction,
  previous outcome
)
```

DR-03-01 已明确 learner stage 应是 activity-specific，而不是全局 learner identity。

### 6.2 State Machine 应存什么

严格来说，v0.3 **无需新增 authoritative mutable stage state**。

FSM/HSM 应存的是**定义**：

```text
stage definitions
entry guards
stay guards
exit guards
fallback transitions
transition priority
```

而不是：

```text
learner ability
mastery
misconception
error diagnosis
review state
learning plan
```

当前 stage 可以从已有 canonical state + previous actions 重建。

如果实现层为了性能维护 `EpisodeControlCache`：

> 它必须是 non-authoritative、可丢弃、可重建的 projection。

### 6.3 为什么不能把 Stage 做成 LearnerState

否则会出现：

```text
SYS03: learner mastery = X
SYS05: learner stage = NOVICE
```

随后两个状态可能发生分叉，形成事实双写。

正确模型是：

```text
SYS03 owns learner truth
        ↓
SYS05 derives current teaching interpretation
```

---

## 7. Candidate Generation

### 7.1 推荐 Typed Decision Table，而不是 Rule DSL

Candidate Generator 建议使用有限维度、schema-validated 的表：

```text
strategy_family
× derived_stage
× error_type
× activity_type
× assistance/exposure obligation
→ candidate action templates
```

例如：

```text
CONCEPTUAL_MISCONCEPTION
+ sufficient diagnostic confidence
→ {
    DIRECT_INSTRUCTION,
    ALTERNATIVE_REPRESENTATION,
    COUNTEREXAMPLE,
    WORKED_EXAMPLE,
    GUIDED_PRACTICE
}
```

而：

```text
UNKNOWN
→ {
    DIAGNOSTIC_PROBE,
    LOW_EXPOSURE_GUIDANCE,
    MAINTAIN_CURRENT_ACTION
}
```

DR-03-02 已明确 error → remediation 只是 **candidate generation**，最终 TeachingAction 仍归 SYS05。

### 7.2 防止配置变成不可审计 DSL

禁止配置：

```text
if (
  mastery > ...
  && error == ...
  || confidence...
) then ...
```

这类任意表达式最终会成为另一门编程语言。

推荐：

> **predicate implementation in code + stable predicate_id + config parameters**

例如：

```text
predicate_id: DIAGNOSIS_ACTIONABLE
threshold_profile: diagnosis/default-v1

predicate_id: INDEPENDENT_EVIDENCE_STABLE
threshold_profile: mastery/default-v2
```

YAML/JSON 只允许：

- enum；
- ID；
- bounded parameter；
- mapping；
- ordered priority；
- weight。

不允许：

- arbitrary expression；
- script；
- embedded Python；
- LLM-generated condition。

---

## 8. Scoring Model

### 8.1 推荐模型

用户提出的模型方向正确，但 `expected_learning_value` 在 v0.3 不能暗示它是真实因果 effect estimate。

建议语义改为：

```text
score(action) =

  + learning_value_proxy
  + diagnostic_value
  + stage_fit
  + remediation_fit
  + review_fit

  - hint_dependency_risk
  - cognitive_load_penalty
  - time_cost
  - transition_cost
  - oscillation_penalty
```

其中：

> `learning_value_proxy` 是 heuristic policy feature，不是模型预测的 causal learning gain。

### 8.2 是否需要 normalization

**需要。**

建议每个 factor 有固定语义范围，例如：

```text
benefit ∈ [0,1]
penalty ∈ [0,1]
```

然后：

```text
raw_score =
Σ benefit_weight_i × benefit_i
-
Σ penalty_weight_j × penalty_j
```

#### 禁止

不要根据“当前候选动作集合”的 min/max 动态 normalization。

否则：

```text
增加一个候选动作
→ 其他动作 normalized score 改变
```

这会降低可解释性与 replay 稳定性。

Normalization 应由：

```text
feature_schema_version
+ normalization_version
```

固定。

MCDA 研究也显示 normalization 和 weight choice 本身可能改变最终排序，因此必须版本化并做 sensitivity analysis。

### 8.3 是否 hierarchical scoring

**推荐有限层级化，但不是再建立一个“goal scorer”。**

正确结构：

```text
Hard Constraint
↓
Mandatory pedagogical obligations
↓
eligible action candidates
↓
weighted scoring
```

例如：

```text
answer exposed
→ independent verification obligation
```

此时“不需要独立验证”的动作不能靠高 score 胜出。

但对于：

```text
EXPLAIN
vs
WORKED_EXAMPLE
vs
GUIDED_PRACTICE
```

无需先选一个抽象 goal，再第二次 score。

否则会增加：

- 两级误差；
- 两套权重；
- 两套 DecisionTrace；
- 更多 oscillation。

### 8.4 Missing Feature

禁止：

```text
missing = 0
```

因为 0 可能本身具有业务含义。

每个 feature 应有：

```text
value
availability
confidence
```

推荐：

```text
missing feature
→ neutral contribution
+ explicit uncertainty handling
```

而不是重新 normalize 剩余 weights。

否则“数据越少，剩余证据权重反而越大”。

安全相关 feature 缺失则进入 hard/fallback semantics，而不是 neutral。

### 8.5 Confidence 如何进入 score

禁止：

```text
final_score *= global_confidence
```

推荐 **component-level confidence shrinkage**：

```text
effective_signal_i =
confidence_i × normalized_signal_i
```

例如：

```text
remediation_fit =
diagnostic_confidence
× conceptual_misconception_fit
```

而：

```text
stage_fit
```

可以由 mastery confidence 单独调节。

这样不会因为一个 error diagnosis 置信度低而把所有其它可靠信息一起削弱。

现有 DecisionTrace 的 global `confidence` 只有在经过校准时才应填写，否则保持 `null`。

### 8.6 不同学科是否允许不同权重

**允许，但有限制。**

可采用：

```text
base_policy_profile
      +
subject_weight_profile
```

例如：

```text
math/problem-solving
language/vocabulary
conceptual-reading
```

但：

- Hard Constraints 不允许学科覆盖；
- feature semantics 不允许改变；
- weights 必须有独立版本；
- subject profile 只能在预声明范围内覆盖；
- 禁止 LLM 动态生成 weights。

### 8.7 Weight Versioning

至少：

```text
feature_schema_version
normalization_version
weight_profile_version
subject_profile_version
```

Score 本身不是跨版本可直接比较的绝对量。

### 8.8 Sensitivity Analysis

不得寻找“科学最佳权重”。

v0.3 应测试：

1. weight perturbation 后 top-1 action flip rate；
2. normalization 变化后的 ranking stability；
3. top-1 / top-2 score margin；
4. tie frequency；
5. subject profile stability；
6. low-confidence context 的 action stability；
7. hard constraint violation 必须始终为 0；
8. expert gold scenarios 的 decision consistency。

如果轻微 weight perturbation 就频繁改变动作：

> 问题不是继续优化小数点，而是 policy feature / hierarchy 设计不稳定。

**Evidence Strength：Medium**  
**Applicability：Direct**

---

## 9. Anti-Oscillation

策略震荡是 v0.3 必须显式处理的问题。

例如：

```text
EXPLAIN
→ QUESTION
→ EXPLAIN
→ QUESTION
```

或：

```text
hint up
→ hint down
→ hint up
```

DR-03-01 已建议 material-evidence gate、hysteresis 和 minimal-change。

### 9.1 v0.3 推荐组合

#### ① Material Evidence Gate

没有新的决策相关证据：

> 默认不切换。

Material evidence 包括：

- 新 AssessmentResult；
- new independent attempt；
- 新 diagnostic probe；
- explicit user request；
- prerequisite evidence；
- exposure event；
- review/delay state materially changed。

不是 material evidence：

- 又调用了一次 policy；
- wall-clock 多了几秒；
- LLM wording 不同。

#### ② Sticky Current Action / Stage

若 previous action：

- 仍合法；
- 尚未触发 exit；
- 没有新负面证据；

则默认保留。

#### ③ Minimum Dwell

推荐用：

> **evidence opportunities**

而不是“固定 N 个 turn”或“固定秒数”。

例如：

```text
GUIDED_PRACTICE
至少观察一次可评价 attempt
才允许因为 soft score 切换
```

Hard failure / user override / integrity violation 可立即跳出。

#### ④ Hysteresis

若 current action 仍合法：

```text
switch only if:

material_evidence = true

AND

adjusted_score(challenger)
-
adjusted_score(current)
>
switch_margin
```

`switch_margin` 是版本化 heuristic parameter，不是教育科学常数。

#### ⑤ Transition Cost

```text
adjusted_score(new_action)
=
base_score
- transition_cost
- oscillation_penalty
```

策略改变越大：

```text
FADING_PRACTICE → EXPLICIT_INSTRUCTION
```

transition cost 可以高于：

```text
CONCEPTUAL_HINT → SUBGOAL_HINT
```

但 hard exit 可以忽略 transition cost。

#### ⑥ Directional Cooldown / Recent Pattern Penalty

重点针对：

```text
A → B → A
```

而不是简单惩罚“重复教学”。

例如 retrieval practice 本身就可能需要重复。

因此应该惩罚：

```text
recent inverse transition
```

而不是：

```text
recent same action
```

### 9.2 推荐最终规则

```text
if hard_transition_required:
    switch

elif no_material_evidence:
    stay

elif minimum_dwell_not_met:
    stay

elif challenger_score - current_score <= hysteresis_margin:
    stay

else:
    deterministic_select(challengers)
```

这是 v0.3 最简单、最容易测试的 anti-oscillation baseline。

**Evidence Strength：Medium**  
**Applicability：Direct**  
**具体 dwell/margin 数值：Hypothesis / Askora Experiment Required**

---

## 10. Low Confidence / Failure Semantics

### 10.1 Low-confidence Fallback Hierarchy

推荐顺序：

```text
1. enforce hard constraints

2. 判断缺失/低置信度是否会改变 TeachingAction

3. 若多个 plausible diagnoses 导向不同 remediation：
      → diagnostic probe

4. probe 不可行但 current action 仍合法：
      → minimal-change / maintain current action

5. current action 不适合：
      → plausible hypotheses 的 common-safe action
        + low exposure
        + low personalization

6. 若用户明确要求 direct answer：
      → 在 assessment integrity 允许时执行
      → 记录 exposure
      → 后续 independent verification

7. 无合法 safe action：
      → explicit policy failure
```

DR-03-02 对 diagnostic probe 的条件也是：

> 至少两个合理诊断会导致不同 remediation，现有证据不足，而且 probe 成本合理。

#### 不建议

低 confidence 自动进入：

```text
“你显然不理解 X，因此……”
```

这属于 over-personalization。

### 10.2 Ask User 的边界

Askora 应向用户询问：

- 用户偏好的任务目标；
- 是否希望直接解释；
- 时间限制；
- accessibility needs。

不应要求用户充当诊断器：

```text
“你是不是因为 prerequisite X 没掌握？”
```

除非这本身就是 diagnostic probe。

### 10.3 Failure Semantics

| 情况 | 类型 | v0.3 行为 |
|---|---|---|
| no eligible action | Policy Decision Failure | safe fallback；否则显式失败 |
| hard-rule conflict | Policy Config/SPEC Failure | fail closed；禁止 LLM 仲裁 |
| stale LearnerState | Input Readiness | conservative/default/probe |
| missing AssessmentResult | Input Incomplete | 禁用依赖该结果的 candidates |
| low diagnostic confidence | Uncertainty，不是系统故障 | UNKNOWN/probe/common-safe |
| missing EvidenceBundle | dependency/execution-precondition failure | 不补造；必要时重新决策 |
| policy config corruption | Policy Infrastructure Failure | last-known-good 或 fail closed |
| unsupported strategy | Policy Catalog Failure | filter；若已选择则失败 |
| execution failure | **Execution Failure** | SYS08 retry 或重新请求 SYS05 |
| user override conflict | Policy Constraint | integrity 优先，并解释可用替代动作 |

最重要的边界：

```text
POLICY_DECISION_FAILED
≠
TEACHING_ACTION_EXECUTION_FAILED
≠
MODEL_INFERENCE_FAILED
```

现有 SYS05 Spec 已明确 policy business failure 与 execution/model-provider failure 必须分离。

---

## 11. Determinism / Idempotency / Replay

目标：

当以下固定时：

```text
TeachingContext snapshot
+ PolicyBundle version
+ TeachingStrategy version
+ experiment assignment
```

必须得到：

> 相同 semantic TeachingAction。

### 11.1 Replay Rules

#### R1 — Immutable Input Snapshot

决策过程中不能重新读取变化中的 LearnerState。

只读取：

```text
entity_id + immutable version
```

#### R2 — Immutable PolicyBundle

进入一次决策前先 resolve：

```text
active policy
→ exact immutable PolicyBundle
```

决策过程中 hot reload 不得改变它。

#### R3 — No Wall Clock

policy evaluator 禁止直接：

```text
now()
```

若时间重要，应把：

```text
decision_time
time_remaining
delay_since_last_evidence
review_due_state
```

作为 snapshot feature。

#### R4 — No Online LLM

canonical replay 不能重新调用 LLM。

这已经是 Askora testing/state ownership 的冻结原则。

#### R5 — Deterministic Tie-break

禁止：

```text
random.choice(top_actions)
```

建议稳定排序键：

```text
1. final_score DESC
2. lower answer exposure
3. smaller scaffold/strategy transition
4. lower configured time cost
5. stable action_definition_priority
6. stable action_definition_id
```

具体顺序本身属于 policy version。

#### R6 — Stable Numeric Semantics

必须版本化：

```text
numeric_precision
score_rounding / quantization
tie_epsilon
```

避免由于浮点实现差异改变 tie-break。

#### R7 — Random Seed

v0.3 deterministic baseline：

> **不需要 seed。**

未来实验若随机化：

- randomization 应属于 Experiment Router；
- assignment 必须先持久化；
- policy 输入已经是固定 assignment；
- replay 使用记录的 assignment，而不是重新抽样。

#### R8 — Experiment Assignment

需要固定：

```text
experiment_id
experiment_version
assignment_unit
variant_id
assignment_probability（若随机）
```

Experiment assignment 与 action propensity 必须区分。

#### R9 — Config Hot Reload

```text
new config
→ validate
→ immutable publish
→ atomic activation
```

只能影响：

> 新 decision。

已经开始或已经执行的 TeachingAction pin 原版本，这与 SYS05 当前 Spec 一致。

#### R10 — Missing Historical Config

若历史 policy/config 已丢失：

```text
replayability = NOT_FULLY_REPLAYABLE
```

禁止：

```text
拿当前 config 重跑
→ 宣称历史 decision 已 replay
```

现有 DecisionTrace 也明确：缺失历史版本不能宣称 fully replayable。

### 11.2 Idempotency

推荐区分：

```text
decision_request_id
decision_id
decision_round_id
```

相同：

```text
decision_request_id
```

重试时返回：

> 原 DecisionTrace + 原 TeachingAction。

不得再次 append 一个语义完全相同的 TeachingAction。

---

## 12. DecisionTrace Delta

现有 DecisionTrace 已包含：

- decision_id/type；
- inputs；
- candidates；
- selected；
- constraints；
- reason_codes；
- algorithm/version；
- experiment；
- propensity；
- correlation/trace information。

并已要求 TeachingAction 记录候选、hard constraints、scoring 与最终 action。

DR-03-03 不应重新发明 DecisionTrace，而只增加 SYS05 所需结构。

### 12.1 Canonical Audit Trail — 必须保存

| 字段 | 建议 |
|---|---|
| decision_id | 已有 |
| TeachingContext refs/version | 必须 |
| context_fingerprint | **新增建议** |
| policy_bundle_version/hash | **新增建议** |
| strategy_version | 必须 |
| available_action_set | 必须，存 ID |
| hard_filtered_actions | 必须 |
| hard_filter_reason_codes | 必须 |
| derived_policy_stage | **新增建议** |
| stage_mapper_version | **新增建议** |
| feature vector | 只存真正参与决策者 |
| feature confidence | 必须 |
| base/raw score | 必须 |
| normalized score | 必须 |
| transition_adjusted_score | 建议 |
| selected_action | 必须 |
| previous_action_id | **新增建议** |
| transition_reason | **新增建议** |
| material_evidence_refs | **新增建议** |
| tie_break_rule/reason | **新增建议** |
| experiment assignment | 必须 |
| behavior policy type | **新增建议** |
| valid action propensity | 条件性 |
| replayability status | **新增建议** |

#### Candidate score 建议结构

```text
candidate_id
eligible
filter_reason_codes

features:
  feature_id
  normalized_value
  confidence

score:
  base_score
  transition_cost
  oscillation_penalty
  final_score
```

Weights 不需要每个 candidate 重复保存。

通过：

```text
policy_bundle_version
```

即可重建。

### 12.2 只进入 Observability / Analytics

不进入 canonical DecisionTrace：

- evaluator latency；
- cache hit/miss；
- CPU/memory；
- 每个 predicate 的完整 debug stack；
- 敏感原始学习内容；
- 原始长文本；
- LLM chain/debug content；
- sensitivity-analysis 临时结果；
- histogram；
- profiling data；
- token usage。

Observability standard 已明确 logs/metrics/traces 是 projection，不应成为 canonical truth。

### 12.3 防止 DecisionTrace 无限膨胀

原则：

```text
store references, not duplicate canonical objects
store feature IDs, not entire TeachingContext
store action IDs, not duplicate action definitions
store bounded structured reason codes
```

即：

> 足以 replay，而不是“把运行时的一切都永久保存”。

---

## 13. Policy Configuration

### 13.1 推荐 PolicyBundle

建议逻辑结构：

```text
PolicyBundleManifest

schema_version
policy_version

hard_rule_set_version
stage_mapper_version
candidate_table_version

feature_schema_version
normalization_version
weight_profile_version

anti_oscillation_profile_version
tie_break_version
fallback_profile_version

subject_profile_version

content_digest
created_at
activation_metadata
```

### 13.2 Versioning

推荐同时采用：

```text
semantic version
+
content digest
```

SemVer 表达兼容意义；

digest 保证：

> replay 时拿到完全相同内容。

### 13.3 Config 不允许成为 DSL

配置只允许：

```text
threshold
weight
enum
mapping
priority
action ID
feature ID
reason-code ID
```

禁止 arbitrary executable logic。

### 13.4 Activation Gate

每个新 PolicyBundle 至少经过：

```text
schema validation
→ hard-rule conflict detection
→ candidate coverage test
→ golden scenario replay
→ sensitivity analysis
→ deterministic replay test
→ activate
```

失败则保持：

```text
last-known-good
```

---

## 14. Future Learning Data Contract

这是 DR-03-03 最需要提前做对的部分。

### 14.1 今天应该记录什么

#### Decision-side

```text
decision_id

context_snapshot_ref
context_schema_version

available_action_set
hard_filtered_action_set

behavior_policy_type
behavior_policy_version

selected_action

experiment_id
variant_id
assignment_probability

action_propensity   # nullable

policy_version
feature_schema_version
```

#### Outcome-side

不要直接往 DecisionTrace 不断追加。

使用 append-only outcome records：

```text
decision_id
action_id

outcome_type

measurement_ref
observed_at

independence
assistance_level
answer_exposure

delay
novelty / transfer_distance

success/value
measurement_confidence

time_cost
hint_cost

attribution_version
censoring/missing_reason
```

### 14.2 建议 outcome taxonomy

至少保留：

```text
SHORT_TERM_OUTCOME

NEXT_INDEPENDENT_OUTCOME

DELAYED_RETENTION_OUTCOME

TRANSFER_OUTCOME

TIME_COST

HINT_COST
```

这与 DR-03-01 的证据层级一致：

> 当前 correctness 的教学价值低于 fresh independent success，再低于 delayed independent retention / meaningful transfer。

不要现在把这些强行合成为唯一 reward。

未来应另有：

```text
reward_definition_version
```

### 14.3 Deterministic Policy 下 propensity 有什么意义？

假设 deterministic policy：

```text
A = π(X)
```

数学上：

```text
P(A = selected | X) = 1
P(A ≠ selected | X) = 0
```

但这意味着：

> alternative actions 没有 overlap / support。

因此虽然“1”在数学上不是错误，却**不能为其他动作提供 OPE 所需的反事实信息**。

所以 Askora 推荐：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
propensity_status = NOT_APPLICABLE_NO_RANDOMIZATION
```

而不要机械写：

```text
propensity = 1.0
```

并让未来分析系统误认为该日志 OPE-ready。

反事实学习文献的核心条件正是 logging policy 的 propensity 与 action coverage；当目标策略选择历史行为策略从未选择过的动作时，标准 IPS 类估计缺乏支持。

2026 年针对 deterministic logging 的研究仍将“零支持导致标准 IPS 失效”作为核心问题，这进一步说明不能通过伪造概率字段解决。

**Evidence Strength：High**  
**Applicability：Direct**

### 14.4 Experiment Assignment ≠ Action Propensity

例如：

```text
A/B experiment

Variant A probability = 0.5
Variant B probability = 0.5
```

如果两个 variant 内部都是 deterministic：

```text
assignment_probability = 0.5
```

是真实的实验概率。

但它**不自动等于**：

```text
selected_action_propensity = 0.5
```

必须区分：

```text
variant assignment probability
vs
action selection probability
```

### 14.5 propensity 的正确产生条件

只有以下情况应该填写 action propensity：

#### Randomized Controlled Exploration

```text
hard-filtered safe actions
→ stochastic selection distribution
→ sample action
```

并在选择前能够明确：

```text
P(action | context, available_actions)
```

#### Contextual Bandit

算法本身返回：

```text
action distribution
```

并记录所选 action 的精确 probability。

必须：

> decision time 记录，不能事后猜测。

### 14.6 IPS / SNIPS / Doubly Robust

#### IPS

利用：

```text
target_policy_probability
/
behavior_policy_probability
```

进行 importance weighting。

优势：

- 在正确 propensity 和 support 条件下具有良好理论性质。

问题：

- propensity 很小时 variance 极高。

#### SNIPS

用 self-normalization 稳定 importance weights。

主要价值：

> 降低高 variance / propensity overfitting 风险，但以有限样本 bias 等 trade-off 为代价。

#### Doubly Robust

组合：

```text
reward/outcome model
+
propensity weighting
```

在适当条件下，只要 outcome model 或 logging-policy model 中一个足够正确，就具有更强稳健性。

但：

> DR 也不能凭空创造 deterministic policy 从未覆盖的 action outcome。

### 14.7 OPE 的 Askora 特有局限

Askora 比普通推荐系统更难，因为：

```text
action_t
→ 改变 learner state
→ 影响 action_t+1
→ 影响 delayed retention
```

因此完整 Teaching Loop 并不天然是 one-step contextual bandit。

v0.3 应把未来 Bandit 限定为：

> **局部、短 horizon、hard-constrained 的策略选择问题。**

例如在教学目标与状态已经固定时选择：

```text
WORKED_EXAMPLE
vs
GUIDED_PRACTICE
```

而不是让 Bandit 控制整个长期 curriculum。

---

## 15. Algorithm Upgrade Gates

不设：

```text
“达到 10,000 次交互后升级”
```

这种伪科学阈值。

使用：

> data quality + identifiability + statistical stability + safety evidence。

### 15.1 Rules → Heuristic Scoring

进入条件：

- hard constraints 已稳定；
- feature semantics 明确；
- candidate action catalog 稳定；
- gold scenarios 存在；
- deterministic replay 完整；
- reason codes 可审计；
- 单纯 rules 已出现真实 soft trade-off。

#### v0.3

**满足采用 heuristic scoring 的架构条件。**

### 15.2 Heuristic Scoring → Supervised Outcome Model

需要：

#### Data

- stable context feature schema；
- stable TeachingAction ontology；
- reliable outcome linkage；
- independent outcome；
- delayed outcome；
- action/context coverage；
- missing/censoring semantics。

#### Modeling

候选模型至少预测：

```text
P(next independent success | context, action)

或

expected delayed outcome
```

#### Gate

- temporal held-out validation；
- calibration；
- uncertainty estimation；
- 无明显 leakage；
- shadow replay 优于 heuristic；
- robustness / subgroup checks；
- learned model 不突破 hard constraints。

尤其：

> deterministic logs 可以训练“已选择动作后的 outcome prediction”，但如果没有 action overlap，就不能证明模型正确估计未选择动作的相对效果。

### 15.3 Supervised Model → Contextual Bandit

必须同时满足：

1. 有明确且安全的探索空间；
2. hard constraints 已经过充分验证；
3. controlled randomized exploration 可接受；
4. action availability 完整记录；
5. propensity 真实、decision-time logging；
6. adequate overlap；
7. IPS/SNIPS/DR 等 OPE 结果方向基本一致；
8. effective sample size 与 CI 足够稳定；
9. delayed outcome attribution 可解释；
10. rollback / kill switch 完整；
11. Bandit shadow evaluation 优于 deterministic baseline；
12. 最终仍需在线受控实验验证。

CRM、IPS、DR 的理论均依赖 logging-policy 信息和适当 action coverage。

### 15.4 Contextual Bandit → Offline RL

只有在证据显示：

> TeachingAction 的长期序列效应确实不能由“当前 context → 当前 action → bounded outcome”充分建模

时，才有理由升级。

至少需要：

- longitudinal trajectory schema 稳定；
- state representation 具有决策充分性；
- delayed reward 稳定；
- trajectory attribution；
- diverse behavior policies；
- state-action coverage；
- policy distribution shift diagnostics；
- reliable sequential OPE；
- conservative policy improvement；
- safety constraints 永久保留；
- shadow + controlled deployment validation。

Offline RL 的主要困难恰恰是 behavior data 与学习后策略之间的 distribution shift，以及未覆盖动作的价值过估计。

因此：

> Offline RL 是“数据问题被解决之后的算法选择”，不是解决数据不足的方法。

---

## 16. Rejected Alternatives

### 16.1 Pure Rule System — 不作为完整架构

保留：

- hard constraints；
- 极少数 mandatory transitions。

拒绝作为完整 policy，因为：

```text
error type
× learner confidence
× stage
× review context
× assistance history
× exposure
× time constraint
```

很快形成组合爆炸。

### 16.2 Pure Decision Table — 不作为最终 selector

适合：

```text
context class → candidate set
```

不适合持续表达多个连续 soft factors。

因此嵌入 Candidate Generator，而非控制全部决策。

### 16.3 Pure FSM/HSM — 拒绝

若把所有变量编码为状态：

```text
NOVICE_WITH_CONCEPT_ERROR_WITH_HINT_2...
```

状态数量会快速爆炸，并很容易形成第二 LearnerState。

FSM 只承担：

> entry / stay / exit / fallback / transition semantics。

### 16.4 Generic Rule Engine — v0.3 拒绝

主要问题不是性能，而是治理：

- arbitrary rule ordering；
- priority conflict；
- DSL；
- dynamic expression；
- hot reload；
- 隐式行为；
- replay 复杂；
- code review 困难。

Askora 当前规模没有足够收益证明引入通用 rule engine 的必要性。

### 16.5 Full MCDA / AHP — 拒绝 Runtime 化

MCDA 对：

- factor decomposition；
- normalization；
- weight sensitivity；
- ranking robustness；

很有价值。

但没有必要引入：

- pairwise comparison；
- 复杂 outranking；
- AHP 层次权重运行时。

v0.3 的 normalized weighted scoring 已足够透明。

### 16.6 Supervised Ranking — Deferred

未来可作为：

```text
shadow challenger
→ score component
→ supervised policy
```

但当前缺少跨 action outcome coverage。

### 16.7 Contextual Bandit — Deferred

不是因为算法本身不好，而是：

```text
propensity
overlap
exploration
reliable learning outcome
OPE
```

尚未建立。

### 16.8 Offline RL — 明确 Out of Scope

当前既无数据需求，也无证据证明其复杂度值得。

---

## 17. Spec Implications

以下只是 **建议 Delta**，本研究不修改 SYS05 Spec。

### Delta 01 — 明确 TeachingStage 语义

增加：

> `DerivedTeachingStage` 是 SYS05 的 activity-specific derived policy feature，不属于 LearnerState，不成为 canonical learner truth。

### Delta 02 — 明确 PolicyBundle

把目前笼统的：

```text
policy_version
```

扩展定义为可解析到 immutable：

```text
hard rules
stage mapper
candidate table
features
normalization
weights
anti-oscillation
tie-break
fallback
```

的 PolicyBundle。

### Delta 03 — Hard Constraint Semantics

明确：

> hard constraint 优先负责 disqualify action class，不应通过 score 表达。

增加：

```text
HARD_CONSTRAINT_CONFLICT
NO_ELIGIBLE_ACTION
```

语义。

### Delta 04 — Candidate Generation Contract

规定：

```text
typed action catalog
+ typed decision tables
```

禁止 generic executable rule DSL。

### Delta 05 — Scoring Contract

明确：

```text
feature value
feature availability
feature confidence
normalization version
weight version
base score
transition-adjusted score
```

并声明：

> score 不是 probability。

### Delta 06 — Missing Feature Contract

增加：

```text
MISSING ≠ 0
```

并规定 per-feature missing semantics。

### Delta 07 — Anti-Oscillation

加入：

```text
material evidence gate
minimum evidence dwell
hysteresis
transition cost
inverse-transition cooldown
minimal-change preference
```

具体参数配置化。

### Delta 08 — Low Confidence Semantics

冻结 fallback hierarchy：

```text
diagnostic probe
→ maintain legal current action
→ common-safe low-exposure action
→ explicit policy failure
```

避免 aggressive personalization。

### Delta 09 — Deterministic Replay

补充：

- no wall clock；
- fixed numeric semantics；
- immutable resolved PolicyBundle；
- deterministic iteration order；
- no random tie-break；
- experiment assignment materialized before policy；
- missing historical config ≠ fully replayable。

### Delta 10 — DecisionTrace Delta

增加：

```text
context_fingerprint
derived_policy_stage
feature confidence
hard-filter reason
previous_action
transition_reason
material_evidence_refs
tie_break_reason
behavior_policy_type
replayability_status
```

### Delta 11 — Propensity Semantics

现有：

```text
experiment.propensity
```

建议进一步区分：

```text
experiment_assignment_probability

vs

behavior_policy.selected_action_propensity
```

deterministic baseline：

```text
selected_action_propensity = null
```

而不是伪造一个 OPE-ready 概率。

### Delta 12 — Failure Taxonomy

明确三类：

```text
PolicyDecisionFailure

ExecutionFailure

ModelInferenceFailure
```

禁止混用。

### Delta 13 — Testing Delta

在现有 testing standard 基础上增加：

#### Golden Decision Tests

```text
context fixture
+ policy version
→ exact TeachingAction
```

#### Property Tests

必须始终成立：

```text
hard-filtered action never selected

same snapshot + same versions
→ same action

lower diagnostic confidence
cannot increase diagnosis-specific personalization
without new evidence

answer exposure
→ subsequent independent verification obligation
```

#### Sequence Tests

专门覆盖：

```text
EXPLAIN → QUESTION → EXPLAIN

hint up → hint down → hint up

failure → remediation → independent retry

answer exposure → independent verification
```

#### Config Tests

```text
corrupt bundle
historical bundle missing
hot reload
version rollback
candidate table overlap
hard-rule conflict
```

现有测试标准已经要求 deterministic policy unit test、replay 和 failure isolation，因此上述 Delta 是自然扩展，而非新的测试体系。

---

## 18. References

### 18.1 Askora Frozen / Internal Research

1. **Askora v0.2 — First Vertical Learning Loop Completion Report**：确认 v0.2 baseline FROZEN、canonical learner path、replay/recovery 与 architecture ownership。

2. **Askora v0.3 候选范围分析**：确认 Adaptive Teaching Loop 为 v0.3 主线，并明确 Bandit/RL 的数据前置缺口。

3. **Askora v0.3 深度研究议程**：冻结 DR-03-03 的研究范围和“Research for Delta”原则。

4. **DR-03-01 教学策略与支架转换研究**：支撑 strategy/move/scaffold/exposure 分离、material evidence、hysteresis、minimal change、independent outcome 等原则。

5. **DR-03-02 错误诊断到教学补救研究**：支撑最小 error taxonomy、diagnostic uncertainty、probe 条件以及 error→candidate remediation 边界。

6. **4.5 教学策略选择系统设计研究**：已提出 hard constraints + state machine + weighted scoring 与未来 rules→model→bandit→RL 路径。

7. **SYS05 Teaching Policy Spec**：冻结 SYS05 ownership、决策 pipeline、idempotency、failure semantics 与 hot config 行为。

8. **Decision Contract**：现有 DecisionTrace / experiment / replay / propensity 基础。

9. **Domain Model / State Ownership / Observability / Testing**：冻结 canonical entities、单写 owner、审计与 deterministic replay 原则。

### 18.2 Decision Architecture / MCDA

10. Object Management Group, **Decision Model and Notation (DMN)**：decision table / structured business decision modeling。  
https://www.omg.org/dmn/  
**Evidence Strength：Medium | Applicability：Indirect**

11. Cinelli et al. related systematic literature, **Sensitivity analysis approaches in multi-criteria decision analysis**：支持对 weights、normalization 与 ranking robustness 做 sensitivity analysis。  
https://www.sciencedirect.com/science/article/pii/S156849462300933X  
**Evidence Strength：High | Applicability：Conditional**

### 18.3 Contextual Bandit / Counterfactual Evaluation

12. Li, Chu, Langford & Wang, **Unbiased Offline Evaluation of Contextual-bandit-based News Article Recommendation Algorithms**：contextual-bandit replay / partial feedback 基础。  
https://arxiv.org/abs/1003.5956  
**Evidence Strength：High | Applicability：Conditional**

13. Dudík, Langford & Li, **Doubly Robust Policy Evaluation and Learning**, ICML 2011：DR policy evaluation。  
https://www.microsoft.com/en-us/research/publication/doubly-robust-policy-evaluation-and-learning-2/  
**Evidence Strength：High | Applicability：Direct to future OPE**

14. Swaminathan & Joachims, **Counterfactual Risk Minimization**, ICML 2015：propensity scoring、logged bandit learning 与 variance-aware policy learning。  
https://proceedings.mlr.press/v37/swaminathan15.html  
**Evidence Strength：High | Applicability：Direct to future OPE**

15. Swaminathan & Joachims, **The Self-Normalized Estimator for Counterfactual Learning**, NeurIPS 2015：SNIPS / propensity overfitting。  
https://papers.nips.cc/paper/2015/hash/39027dfad5138c9ca0c474d71db915c3-Abstract.html  
**Evidence Strength：High | Applicability：Direct to future OPE**

16. Saito, Ren & Joachims, **Off-Policy Evaluation for Large Action Spaces**, ICML 2023：进一步说明 importance weighting 在 action-space / weak-support 环境中的 variance 问题。  
https://proceedings.mlr.press/v202/saito23b.html  
**Evidence Strength：High | Applicability：Conditional**

17. **Deterministic Logging / Zero-Support Off-Policy Evaluation**：用于说明 deterministic behavior policy 在零支持区域不能通过伪造 propensity 恢复标准 OPE 所需的 overlap。  
https://arxiv.org/abs/2603.21485  
**Evidence Strength：Emerging | Applicability：Direct to propensity semantics**

### 18.4 Offline RL

18. Levine, Kumar, Tucker & Fu, **Offline Reinforcement Learning: Tutorial, Review, and Perspectives**：offline RL 的 coverage / distribution shift 基础问题。  
https://arxiv.org/abs/2005.01643  
**Evidence Strength：High | Applicability：Future / Conditional**

19. Kumar et al., **Conservative Q-Learning for Offline Reinforcement Learning**, NeurIPS 2020：offline RL 中 OOD action/value overestimation 与 conservative learning。  
https://proceedings.neurips.cc/paper/2020/hash/0d2b2061826a5df3221116a5085a6052-Abstract.html  
**Evidence Strength：High | Applicability：Future / Conditional**

---

# Final Recommendation

DR-03-03 推荐冻结为后续 Synthesis 的候选结论：

```text
Askora v0.3 Teaching Policy

= Typed Hard Constraints
+ Derived Policy Stage / Transition FSM
+ Typed Decision-Table Candidate Generation
+ Normalized Confidence-Aware Heuristic Scoring
+ Material-Evidence Anti-Oscillation
+ Deterministic Tie-break
+ Immutable TeachingAction
+ Bounded Canonical DecisionTrace
+ Versioned PolicyBundle
+ Future-Learning-Ready Outcome Logging
```

其中最重要的三个架构原则是：

```text
1. Hard constraints are non-compensatory.

2. TeachingStage is derived policy state,
   never a second LearnerState.

3. Log future learning data correctly,
   but never pretend deterministic logs
   provide counterfactual propensity/coverage.
```

### v0.3 Algorithm Baseline

```text
Rules                     → only hard invariants
Heuristic Scoring         → YES, v0.3 baseline
Supervised Outcome Model  → shadow/future
Contextual Bandit         → deferred
Offline RL                → deferred
```

因此，**当前 SYS05 已冻结的总体算法方向无需推翻；真正需要的 v0.3 Delta 是把每一层的职责、uncertainty、anti-oscillation、replay、DecisionTrace 和 future-learning logging semantics 精确定义出来。**
