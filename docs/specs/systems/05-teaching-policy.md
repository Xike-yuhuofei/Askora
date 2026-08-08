# SYS05 — Teaching Policy

> Spec ID：`SYS05-*`  
> 对应设计：4.5 教学策略选择  
> 状态：Canonical Implementation Contract  
> 版本：v0.3  
> ADR：ADR-0001、ADR-0002、ADR-0003（Accepted）

## 1. Responsibility

### SYS05-001

SYS05 是 `TeachingAction` 的唯一 owner。它 MUST 将 immutable `TeachingContext` 与 exact `PolicyBundle` 转换成一个 immutable、可解释、可 replay、可测试的 TeachingAction，并产生完整 DecisionTrace。

SYS05 MUST NOT 持久化第二份 LearnerState、AssessmentResult、LearningPlan 或 ReviewSchedule truth。

## 2. Canonical Strategy Ontology

### SYS05-201 — StrategyFamily

v0.3 top-level canonical StrategyFamily 仅允许：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

`DIRECT_INSTRUCTION`、`WORKED_EXAMPLE`、`SOCRATIC_PROBE`、`SELF_EXPLANATION_PROMPT`、`METACOGNITIVE_CHECK` 等 MUST 处于 InteractionMove/ActionModifier 层；`PRODUCTIVE_FAILURE` MUST NOT 成为 selectable v0.3 StrategyFamily。

### SYS05-202 — Four-layer Model

SYS05 MUST 区分：

```text
StrategyFamily
TeachingAction
InteractionMove
ActionModifier
```

TeachingAction MUST NOT 被实现为“strategy enum 的别名”；InteractionMove MUST NOT 取得 final TeachingAction ownership。

### SYS05-203 — Canonical Moves

InteractionMove vocabulary 至少支持：

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

ActionModifier 至少支持：`self_explanation`、`metacognitive_reflection`、`feedback_type`、`representation_style`、`transition_intent`、`support_reason`、`target_scope`、`delivery_mode`。

## 3. TeachingContext Contract

### SYS05-210 — Immutable Snapshot

每次 canonical policy evaluation MUST 先构造 immutable `TeachingContext`。它是 decision-input snapshot，不是 learner state truth。

Snapshot 语义 MUST 覆盖：

- objective/activity/task/capability 与 task structure；
- exact MasteryEstimate、prerequisite state 与 confidence/evidence sufficiency；
- recent AssessmentResult/correctness/assessment confidence；
- ErrorType、diagnostic confidence、misconception evidence、alternative hypotheses、needs_probe；
- assistance/scaffold/hint/answer exposure/worked-example history；
- independent/assisted success history；
- previous TeachingAction/outcomes；
- delayed independent/review/transfer evidence 与 novelty；
- direct-answer/explanation request；
- time/accessibility constraints；
- ExperimentAssignment/opt-out；
- decision_time、context_schema_version、context_fingerprint。

### SYS05-211 — Missing Semantics

每个可缺失语义 MUST 显式表达 `AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE`。`missing = 0` 禁止。

### SYS05-212 — Replay Boundary

TeachingContext MUST 固定 exact owner version；derived feature MUST 可追溯 source refs；policy evaluator MUST NOT 隐式读取 mutable state；replay MUST NOT 重新调用在线 LLM。

## 4. Support / Hint / Exposure Envelope

### SYS05-220 — Orthogonal Envelope

TeachingAction 的 canonical envelope MUST 使用：

```text
scaffold_control = NONE | LOW | MEDIUM | HIGH
hint_specificity = NONE | ORIENTATION | CONCEPTUAL_STRATEGIC | SUBGOAL | PARTIAL_STEP | BOTTOM_OUT
answer_exposure = NONE | PARTIAL | COMPLETE
```

`assistance_state = INDEPENDENT|ASSISTED|ANSWER_EXPOSED` 是 SYS04 对实际经历的记录，不是 SYS05 预写的学习结果。

### SYS05-221 — Ownership

SYS05 MUST 定义 allowed scaffold/hint/exposure envelope；SYS08 MAY 在执行时收紧，但 MUST NOT 扩大；SYS04 MUST 记录 actual experienced assistance/exposure；SYS03 MUST 基于实际记录判断 evidence eligibility/weight。

### SYS05-222 — Independent Validation Obligation

`ASSISTED` success 或 `ANSWER_EXPOSED` success 后，SYS05 MUST 产生 `INDEPENDENT_VALIDATION_REQUIRED`。Answer-exposed 当前结果 MUST NOT 视为 independent mastery evidence。该 obligation 是 policy-control semantics，MUST NOT 成为新的 MasteryState；在 fresh independent Attempt 前不得标记完成。

## 5. Canonical Policy Stack

### SYS05-230

B3 canonical runtime MUST 严格按以下语义栈执行：

```text
TeachingContext Snapshot
→ Typed Hard Constraints
→ Derived TeachingStage
→ Typed Candidate Generation / Decision Table
→ Feature Builder
→ Normalized Weighted Scoring
→ Anti-Oscillation Gate
→ Deterministic Tie-break
→ Immutable TeachingAction
→ DecisionTrace
```

不得让 LLM、legacy selector 或实验层跳过任一 hard shield。

### SYS05-231 — Layer Contract

| Layer | Input | Output | Responsibility | Must Not | Failure semantics | Versioning | Testability |
|---|---|---|---|---|---|---|---|
| Context Snapshot | owner refs + decision time | TeachingContext | freeze exact decision inputs | implicit mutable reads | missing/stale/invalid context status | context schema | fixture + fingerprint replay |
| Hard Constraints | context + PolicyBundle | allowed/blocked set + reasons | enforce non-negotiable integrity | weighted override/LLM override | conflict/fail-closed/fallback | hard rule set | G0 + property tests |
| Stage Mapper | filtered context | TeachingStage | derive current control stage | persist learner stage | unknown/low-confidence stage path | stage mapper | deterministic mapper tests |
| Candidate Table | stage + context | typed candidates | enumerate legal actions | free-form LLM action creation | no candidate → typed fallback/failure | candidate table | scenario fixtures |
| Feature Builder | context + candidates | versioned features | build comparable evidence-based features | hide missing as zero | availability/confidence preserved | feature schema | feature contract tests |
| Normalized Scoring | features + weights | candidate scores | apply soft preferences | cancel hard rule | invalid normalization → fallback/fail | normalization + weights | differential/property tests |
| Anti-Oscillation | score result + previous action + material evidence | transition permission/hold | control unnecessary switching | wall-clock/chat-turn switching | repeated-failure override/fallback | anti-oscillation profile | sequential replay |
| Tie-break | surviving candidates | one selected candidate | stable final selection | random runtime tie-break | no stable order → config error | tie-break version | determinism test |
| Action Build | selected candidate | immutable TeachingAction | freeze executable semantic envelope | post-build mutation | validation failure → no action | action schema + policy bundle | schema/immutability test |
| Trace | all above | DecisionTrace | explain/replay decision | omit losing candidates/reasons | trace persistence failure visible | trace schema | trace completeness test |

## 6. Typed Hard Constraints

### SYS05-240 — Taxonomy

Policy MUST distinguish：

```text
Hard Constraint
Soft Preference
Experiment Guardrail
```

Hard Constraint MUST NOT 被 weighted score 抵消、被 LLM override、被实验恢复或被 SYS08 扩大。

### SYS05-241 — Required Hard Constraint Families

PolicyBundle 至少 MUST 定义以下 typed hard-constraint family，并给出稳定 reason code：

1. `Assessment Integrity` — 独立评估期间禁止不允许的 hint/answer exposure；
2. `Answer Exposure Integrity` — 不得超过 action envelope，exposure 后建立 validation obligation；
3. `Prerequisite Safety` — hard prerequisite evidence 不足时不得直接选择不安全高阶挑战；
4. `Repeated Failure Ceiling` — 达到版本化失败上限时必须退出/升级支持/重新诊断；
5. `Independent Success Constraint` — 新独立成功证据允许 fade，不得无证据增加支架；
6. `Low-confidence Conservatism` — 关键证据低置信时选择保守诊断/支持路径，不得伪确定；
7. `Objective Ownership` — SYS05 不得改写 SYS06 objective/plan；
8. `Model/LLM Override` — LLM/Agent 不得拥有或扩大 TeachingAction；
9. `Unsupported Configuration` — 缺失/未知 policy component 必须 fail closed 或走 versioned fallback；
10. `Hard-rule Conflict` — 冲突必须显式检测并记录，不得靠 score/tie-break 隐式解决；
11. `User Direct Answer` — explicit user request MAY 触发 bounded `DIRECT_ANSWER_OVERRIDE`，但必须仍满足 assessment integrity、安全与 exposure hard rules。

### SYS05-242 — Direct Answer Semantics

用户明确索要答案时 MAY 改变候选集/InteractionMove；它 MUST NOT 自动取消 assessment integrity、answer exposure guard、prerequisite safety 或后续 independent validation obligation。

## 7. Derived TeachingStage

### SYS05-250

`TeachingStage = f(TeachingContext, PolicyBundle)`，canonical vocabulary：

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

TeachingStage MUST NOT 被解释为 LearnerState、MasteryState 或 persistent learner stage；SYS03 的 progress summary 与其无 ownership/inheritance 关系。

### SYS05-251

Stage mapper MUST versioned、deterministic、traceable。关键 evidence `MISSING|STALE|LOW_CONFIDENCE` 时 MUST 走显式保守路径，而不是用默认数值假定 stage。

## 8. Candidate Generation & Error Remediation

### SYS05-260

Candidate generation MUST 使用 typed decision table。候选只能来自当前 PolicyBundle 支持的 StrategyFamily/InteractionMove/action template；MUST NOT 由 LLM 自由发明 semantic TeachingAction。

### SYS05-261

SYS05 对 SYS04 的 ErrorType 只读消费：

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

`UNKNOWN` 或低 diagnostic confidence MUST 允许 probe/保守候选；MUST NOT 强制猜错因后进入特定 remediation。

## 9. Feature / Scoring Contract

### SYS05-270 — Feature Shape

每个 scoring feature MUST 至少包含：

```yaml
value: number|null
availability: AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE
confidence: float|null
feature_version: string
source_refs: [versioned_ref]
```

### SYS05-271 — Soft Score

Soft scoring MAY 包含：

```text
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

`learning_value_proxy` MUST 被标记为 policy heuristic/proxy，MUST NOT 被描述为 causal learning-effect estimate。

### SYS05-272 — Normalization

Normalization MUST 独立版本化。MUST NOT 根据当前 candidate set 动态 min-max 后把结果当稳定语义，因为 candidate composition 改变会导致不可追踪漂移。

### SYS05-273 — Parameters

Weights、mastery threshold、failure ceiling、minimum dwell、switch margin、hint sequence、scaffold fade amount、diagnostic confidence cutoff、transfer novelty threshold、delay windows、practical harm margin MUST 进入 versioned PolicyBundle/profile；Spec MUST NOT 写死并宣称为学习科学常数。

## 10. Anti-Oscillation

### SYS05-280 — Material Evidence Gate

Strategy/major action transition MUST 由 material evidence 支持。至少可包括：new AssessmentResult、new independent Attempt、diagnostic probe result、LearnerState update、explicit user request、prerequisite evidence、exposure event、meaningful review/delay transition。

以下 MUST NOT 单独触发 transition：又多一轮聊天、policy 再调用一次、LLM wording 改变、wall clock 多几秒。

### SYS05-281 — Sticky Continuity

无 material evidence 且旧动作仍合法时，policy SHOULD 保持当前 StrategyFamily/episode continuity；重新评分不等于必须切换。

### SYS05-282 — Minimum Dwell by Evidence Opportunity

Minimum dwell MUST 以“获得新 evidence 的机会/事件”建模，而非纯 wall-clock 秒数或聊天轮数；阈值属于 versioned profile。

### SYS05-283 — Hysteresis

从当前动作切换到替代动作 MUST 满足版本化 switch margin/transition condition，防止边界附近反复横跳。

### SYS05-284 — Transition Priority

当多个转换同时满足时 MUST 使用 versioned transition priority；hard constraint 与 repeated-failure override 高于 soft score improvement。

### SYS05-285 — Repeated Failure Override

达到 failure ceiling 或出现新的 material failure evidence 时，anti-oscillation MUST NOT 以“保持稳定”为由阻止必要退出、升级支持、重新诊断或 prerequisite remediation。

## 11. Deterministic Tie-break

### SYS05-290

B3 runtime MUST 使用 stable、versioned deterministic tie-break；禁止随机 tie-break。

在相同 `TeachingContext + exact PolicyBundle + ExperimentAssignment` 下 MUST 产生同一个 semantic TeachingAction。

### SYS05-291

若候选在 score 后仍相同，tie-break MUST 使用 PolicyBundle 中显式稳定序（例如 typed candidate priority + stable action key），并写 DecisionTrace `tie_break_reason`。

## 12. PolicyBundle

### SYS05-300

PolicyBundle MUST immutable/versioned，至少包含：

```text
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
```

### SYS05-301

Publish MUST immutable；activation MUST atomic；每个 TeachingAction MUST pin exact bundle；历史 bundle MUST 保留用于 replay/audit。

### SYS05-302

新 bundle activation 只影响新 TeachingAction。历史 action/DecisionTrace MUST NOT 被新 bundle 重解释。

### SYS05-303

禁止 PolicyBundle 承载 executable DSL、embedded Python、free-form runtime policy code、LLM-generated rules。

### SYS05-304 — Production Profile Artifact

生产 `PolicyRuntimeProfile` MUST 来自仓库管理的 immutable、versioned artifact；测试 fixture MUST NOT 成为 production config source。首个 production profile 采用 `ADR-0003` 批准的既有 EXEC-009 行为参数，但参数仍是 versioned policy heuristic，不是学习科学常数。

Profile `content_digest` MUST 按以下唯一算法计算：移除顶层 `content_digest` 后，对完整 JSON 对象使用 UTF-8、key 升序、compact separators 的 canonical JSON，再计算 SHA-256 并编码为 `sha256:<lowercase hex>`。artifact 自带 digest、运行时重算 digest 与 exact PolicyBundle digest MUST 全部一致。

### SYS05-305 — Active Runtime Resolution

新 TeachingAction 的 production resolver MUST 从最新 atomic `PolicyBundleActivation` 解析 exact PolicyBundle，再解析与 manifest 各 component version 和 digest 完全匹配的 profile。activation 稳定顺序为 `activated_at DESC, activation_id DESC`。

缺失 activation、bundle、profile artifact，或 digest/component version 不匹配时 MUST 作为 unsupported configuration fail closed；MUST NOT 回退到测试 fixture、代码常量、任意“最新”文件或 LLM 推断。

### SYS05-306 — Bootstrap and Replay

首个 production bundle/activation MUST 通过确定性、幂等 migration bootstrap。已有已发布 bundle/profile 不得原地修改；配置变化必须发布新 artifact、新 digest、新 bundle 并原子激活。

历史 replay MUST 使用 TeachingAction/DecisionTrace 已 pin 的 exact bundle/profile；当前 active activation 只影响新 TeachingAction，MUST NOT 重解释历史 action。

## 13. DecisionTrace & Probability

### SYS05-310

每个 canonical TeachingAction MUST 产生符合 `decision-contract.md` 的 DecisionTrace，并记录 context fingerprint、PolicyBundle hash/ref、hard filters、stage、features、scores、anti-oscillation、tie-break、material evidence、experiment assignment 与 replayability。

### SYS05-311

B3 deterministic behavior MUST 写：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

MUST NOT 写 `action_propensity = 1.0`。

### SYS05-312

ExperimentAssignment probability MUST 与 action selection propensity 分离。历史 `experiment.propensity` 只有在 provenance 明确证明其含义时才能迁移；否则 action propensity MUST 为 null/unknown，并记录 migration reason 与 partial replayability。

## 14. LLM / Legacy Socratic Boundary

### SYS05-320

LLM/Agent MAY 生成 explanation、worked example、hint、diagnostic candidate、feedback、self-explanation prompt、language realization 或执行 tool；MUST NOT 成为 TeachingAction owner、hard-rule override 或 answer-exposure override。

### SYS05-321 — Legacy Socratic Engine

以下 legacy components：

```text
apps/backend/app/engines/socratic/strategy_selector.py
apps/backend/app/engines/socratic/strategy_library.py
apps/backend/app/engines/state_graph.py
apps/backend/app/data/strategies/
```

MUST NOT 作为 final TeachingAction owner。迁移期间 MAY 仅作为 legacy adapter、bounded InteractionMove provider、stage-definition source 或 execution component，并始终受 SYS05 canonical decision envelope 约束。

### SYS05-322 — B2 Baseline

B2 LLM selector MAY 作为 experiment baseline，但 MUST 使用与 B3 相同 hard shield、相同 action vocabulary，且 MUST NOT bypass hard rule。

## 15. Failure Semantics

### SYS05-330

必须显式区分 invalid/missing/stale TeachingContext、unsupported PolicyBundle/config、hard-rule conflict、no legal candidate、feature/normalization failure、anti-oscillation profile failure、tie-break configuration failure、DecisionTrace persistence failure。

### SYS05-331

Hard-rule conflict、unsupported configuration 或无法确定合法候选时 MUST fail closed 或使用 PolicyBundle 内 versioned fallback；MUST NOT 让 LLM 临时创造规则。

### SYS05-332

DecisionTrace 无法可靠持久化时，系统 MUST 将 action emission 标为 degraded/failed；不得产生“已可 replay”的假记录。

## 16. Persistence & Idempotency

### SYS05-340

TeachingAction、TeachingContext snapshot、DecisionTrace 与 PolicyBundle refs MUST immutable/versioned。相同 decision request/idempotency key MUST NOT 产生语义重复 action。

### SYS05-341

Replay MUST 使用历史 exact refs；缺失 owner version、PolicyBundle 或 context source 时必须返回 `PARTIAL`/`NON_REPLAYABLE`，不得静默用当前状态补齐。

## 17. Observability

### SYS05-350

至少记录：context_fingerprint/source versions、TeachingStage、available/filtered candidates + reason codes、feature value/availability/confidence/version、scores、material evidence refs、anti-oscillation、tie-break reason、selected/previous action、validation obligation、PolicyBundle ref/hash、behavior policy/action propensity、experiment assignment、replayability status。

## 18. Tests

### SYS05-360

测试 MUST 覆盖：six StrategyFamily only；InteractionMove/Modifier 分层；Productive Failure 不可选；Socratic 仅 bounded move；TeachingContext exact-version replay/missing semantics；hard rule 不被 score/LLM/experiment 覆盖；UNKNOWN diagnosis 保守；orthogonal support envelope；assisted/answer-exposed validation obligation；independent success fade；repeated failure exit/escalation；low-confidence conservatism；Material Evidence Gate、Sticky Continuity、Minimum Dwell、Hysteresis、Transition Priority；no illegal oscillation/no infinite loop；normalization versioning；deterministic tie-break；same context+bundle+assignment → same semantic action；`action_propensity=null`；production profile canonical digest；active activation exact resolution/fail-closed；bootstrap migration/replay pinning；legacy Socratic cannot own action；historical partial replay。

## 19. Acceptance Criteria

- `SYS05-AC-201`：canonical StrategyFamily 恰为六类。
- `SYS05-AC-202`：每个 TeachingAction 可追溯 immutable TeachingContext 与 exact PolicyBundle。
- `SYS05-AC-203`：hard constraint 的 forbidden action 为 0。
- `SYS05-AC-204`：无 material evidence 时不会因重复调用或 wording 改变而非法切换。
- `SYS05-AC-205`：repeated failure 能越过 continuity 约束进入合法退出/升级路径。
- `SYS05-AC-206`：assisted/answer-exposed success 均建立 independent validation obligation。
- `SYS05-AC-207`：相同 context+bundle+assignment 的 semantic action deterministic。
- `SYS05-AC-208`：B3 trace 固定 `behavior_policy_type=DETERMINISTIC`、`action_propensity=null`。
- `SYS05-AC-209`：LLM、SYS08、legacy Socratic 均无法扩大 action envelope 或取得 final ownership。
- `SYS05-AC-210`：所有 configurable thresholds/weights 可版本化、可 trace，不以伪科学常数写死。
- `SYS05-AC-211`：production profile 来自 immutable artifact，digest 可重算且与 exact active PolicyBundle 完全一致。
- `SYS05-AC-212`：缺失或不一致的 active runtime fail closed；历史 action 不被当前 activation 重解释。

## 20. Superseded v0.2 Requirement Register

为保留审计线索，以下旧 ID 不复用；其 v0.2 语义已被 v0.3 新 ID supersede：

| v0.2 ID | v0.3 canonical replacement |
|---|---|
| `SYS05-010` direct-answer candidate rule | `SYS05-242` |
| `SYS05-020` integer TeachingAction contract | `SYS05-220`、`DOMAIN-090` |
| `SYS05-030` vague baseline stack | `SYS05-230/231` |
| `SYS05-031` old hard constraints | `SYS05-240/241` |
| `SYS05-032` old learner-like state machine | `SYS05-250/251` |
| `SYS05-033` `expected_learning_value` score | `SYS05-270/271` |
| `SYS05-034/035` evolution/RL wording | `SYS05-322` + v0.3 Out of Scope |
| `SYS05-040` old version pin wording | `SYS05-300/301/340` |
| `SYS05-050` old failure semantics | `SYS05-330..332` |
| `SYS05-AC-001..007` | `SYS05-AC-201..210` |

旧 ID 只存在于历史版本/本映射表，MUST NOT 被实现为 v0.3 runtime contract。

## 21. Forbidden Implementations

禁止：

- 旧九类 strategy enum 继续作为 v0.3 top-level truth；
- generic Productive Failure family；
- always-on Socratic tutor；
- LLM/free-form Agent 直接选 final TeachingAction；
- executable policy DSL / embedded Python rules；
- hard rule 作为可被 score 抵消的 penalty；
- candidate-set dynamic min-max 作为 canonical normalization；
- random tie-break；
- `action_propensity=1.0` 伪装 deterministic probability；
- 用聊天轮数/几秒 wall clock 单独触发 strategy switch；
- SYS05 写 LearnerState/AssessmentResult/LearningPlan/ReviewSchedule；
- 新旧 support/strategy 字段永久双写。
