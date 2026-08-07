# ADR-0002 — Constrained Deterministic Teaching Policy Architecture

Status: accepted
Date: 2026-08-07
Decision owners: Askora Canonical Design / Architecture Governance
Affected specs: `docs/specs/domain/domain-model.md`, `docs/specs/domain/decision-contract.md`, `docs/specs/systems/05-teaching-policy.md`, `docs/specs/systems/03-learner-model.md`, `docs/specs/systems/04-assessment.md`, `docs/specs/architecture/state-ownership.md`, `docs/specs/quality/testing-standard.md`, `docs/specs/quality/observability-standard.md`

## Context

`TeachingAction` 是 Askora 的高影响教学决策。它不仅决定“这一轮说什么”，还约束：

- 选择哪一种教学控制意图；
- 给予多少支架；
- 提示具体到什么程度；
- 是否允许答案暴露；
- 是否产生 fresh independent validation obligation；
- 什么证据允许推动下一次 transition。

这些决策直接影响学习测量有效性与后续 learner-state evidence eligibility。因此 canonical selector 必须满足比普通内容生成更严格的确定性、审计、安全、版本化和 replay 要求。

v0.2 SYS05 已存在 `hard constraints → strategy state machine → candidate generation → weighted scoring → deterministic tie-break` 的 baseline，但层次仍不够完整：

- TeachingContext 缺少完整 immutable/version semantics；
- hard rule、candidate、feature、score、transition 仍可能混入大型 if/else；
- 缺少独立 Feature Builder 与稳定 normalization contract；
- anti-oscillation 尚未被正式建模为 material-evidence/sticky/dwell/hysteresis/failure-override stack；
- policy config 只有宽泛 version，没有 immutable component bundle；
- DecisionTrace 不能完整解释 stage、features、transition、tie-break、replayability；
- `experiment.propensity` 单字段容易把实验分配概率与 action-selection propensity 混淆。

同时，v0.3 不具备把 canonical policy 交给 learned selector 的数据条件：

- 单用户优先，action coverage 和 overlap 有限；
- delayed retention / transfer reward 延迟；
- reward attribution 跨 action/episode/trajectory；
- partial observability 明显；
- exploration 可能产生答案泄漏、无效挣扎或测量污染；
- 当前 deterministic baseline 尚未被证明是性能瓶颈；
- action availability、propensity、outcome linkage 尚需先形成正确数据基础。

Free-form LLM selector 也不能成为 canonical owner：模型与 Prompt 会漂移，hard constraint enforcement 不可靠，action availability 不稳定，且无法保证 deterministic replay。

通用 rule engine / executable DSL 同样不是 v0.3 的必要复杂度。当前 policy domain 足够小，typed declarative data + code-defined evaluator 可以提供更强的 validation、debugging、security 和审计边界。

因此需要把 SYS05 的 baseline 正式冻结为一套 constrained deterministic policy architecture。

## Decision

v0.3 SYS05 canonical decision path 固定为：

```text
TeachingContext Snapshot
→ Typed Hard Constraints
→ Derived TeachingStage
→ Candidate Generation / Typed Decision Table
→ Feature Builder
→ Normalized Weighted Scoring
→ Anti-Oscillation Gate
→ Deterministic Tie-break
→ Immutable TeachingAction
→ DecisionTrace
```

给定：

```text
same immutable TeachingContext
+ same immutable PolicyBundle
+ same experiment assignment
```

必须产生相同 semantic TeachingAction。

### Layer 1 — TeachingContext Snapshot

`TeachingContext` 是一次 policy decision 的 immutable、reference/version-based snapshot。

要求：

- authoritative state 通过 exact-version references 进入；
- derived summaries/features 必须能追溯 source refs 与 feature version；
- `missing`、`stale`、`low-confidence`、`not-applicable` 必须显式区分；
- `missing != 0`；
- decision time 必须作为输入，而不是 evaluator 内部隐式调用 wall clock；
- context 必须有 schema version，并应有 deterministic fingerprint；
- context 不成为 LearnerState、AssessmentResult、LearningPlan、ReviewSchedule 的第二事实源。

### Layer 2 — Typed Hard Constraints

Hard Constraints 只决定：

```text
admissibility
obligation
fail-safe / fail-closed
```

不得成为主要 action selector，也不得被 weighted scoring、LLM 或 experiment override。

v0.3 至少包含以下 typed hard-constraint families：

1. **Assessment Integrity** — active no-hint assessment 禁止 solution-bearing hint / answer exposure；
2. **Answer Exposure Integrity** — answer-exposed success 不得作为 independent validation，并产生 validation obligation；
3. **Prerequisite Safety** — severe prerequisite gap 时禁止持续同难度无支架 challenge；
4. **Repeated Failure Ceiling** — 达到版本化 ceiling 后禁止原样重复低支架策略；
5. **Independent Success Constraint** — stable independent success 后无新证据不得无理由增加高支架；
6. **Low-confidence Conservatism** — 低置信禁止激进、高确定 personalization；
7. **Objective Ownership** — SYS05 不得改变 SYS06 的 Objective / Activity；
8. **Model/LLM Override** — SYS08/LLM 不得提高 exposure 或改变 TeachingAction semantics；
9. **Unsupported Configuration** — 未知 strategy/action/config 不得执行；
10. **Hard-rule Conflict** — 无合法动作时必须显式 fail-safe/fail-closed，scorer/LLM 不得仲裁冲突；
11. **User Direct Answer** — 用户可请求直接答案，但不能绕过 active assessment integrity；允许暴露时必须记录 exposure 并产生 independent-validation obligation。

严格保持：

```text
Hard Constraint
≠ Soft Preference
≠ Experiment Guardrail
```

Experiment Guardrail 只能限制哪些已经合法的候选可进入实验，不能把 hard-filtered action 重新放回候选集。

### Layer 3 — Derived TeachingStage

定义：

```text
TeachingStage = f(
  TeachingContext,
  PolicyBundle
)
```

TeachingStage 是 activity-specific、transient、derived policy feature，不是：

```text
LearnerState
MasteryState
persistent learner stage
```

stage definition、entry/stay/exit guards、transition priority 与 fallback transition 可以版本化；当前 stage 本身不成为 authoritative learner truth。任何 cache 只能是可删除、可重建 projection。

### Layer 4 — Typed Candidate Table

Candidate Generation 使用 typed decision table / typed declarative configuration，大致表达：

```text
strategy family
× TeachingStage
× ErrorType
× LearningActivity type
× assistance / exposure obligation
→ candidate TeachingAction templates
```

明确禁止：

- arbitrary embedded Python；
- runtime free-form policy code；
- LLM-generated rules；
- Prompt text 直接充当 executable policy；
- generic expression language 在 config 中变成第二编程语言。

规则与 evaluator 的边界是：config 描述 typed data；code-defined evaluator 实现可测试、可审计语义。

### Layer 5 — Feature Builder

每个 feature 必须显式携带：

```text
value
availability
confidence
feature_version
```

Feature Builder 不得：

- 把 missing/stale/unknown 当作 0；
- 让 LLM 自报置信度直接成为 canonical feature confidence；
- 生成未版本化自由特征；
- 读取未进入 TeachingContext 的 mutable state。

### Layer 6 — Normalized Weighted Scoring

在 hard-eligible candidates 之间允许使用版本化 normalized weighted scoring，例如：

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

必须明确：

> `learning_value_proxy` 是 heuristic，不是 causal learning-effect estimate。

`feature_schema_version`、`normalization_version`、`weight_profile_version` 必须独立版本化。

Normalization 不得对当前 candidate set 动态 min/max，从而使同一个 candidate 的 feature meaning 随候选集合变化。应使用固定版本化范围、变换或稳定统计基线。

### Layer 7 — Anti-Oscillation Gate

Anti-oscillation 至少由以下机制组成：

#### Material Evidence Gate

能够推动 re-evaluation / transition 的 material evidence 包括：

- new AssessmentResult；
- new independent attempt；
- diagnostic probe result；
- LearnerState update；
- explicit user request；
- prerequisite evidence；
- exposure event；
- meaningful review / delay transition。

以下本身不构成 material evidence：

- policy 再调用一次；
- 对话多一轮；
- LLM wording 变化；
- wall clock 多几秒。

#### Sticky Continuity

```text
current action remains legal
AND exit guard not met
AND no material negative evidence
→ default stay
```

#### Minimum Dwell by Evidence Opportunity

minimum dwell 用 evidence opportunities 计，不用聊天轮数计。具体值是版本化参数。

#### Hysteresis

challenger 必须超过版本化 switch margin 才能替换 current action。margin 不是科学常数。

#### Transition Priority

hard transition 优先于 soft continuity。

#### Repeated Failure Override

达到版本化 failure ceiling 时可以强制突破 sticky continuity / minimum dwell，避免无限重复同一无效策略。

### Layer 8 — Deterministic Tie-break

B3 canonical runtime 禁止 random tie-break。

必须有稳定、版本化 tie-break profile。典型顺序可以表达：

```text
hard-priority class
→ score
→ continuity preference
→ lower exposure / lower irreversible cost
→ stable action-template order
```

具体顺序属于版本化 policy profile，不在本 ADR 固定数值或完整优先级表。

实验随机分配属于独立 Experiment Router。给定 assignment 后，B3 selector 仍必须 deterministic。

### Layer 9 — Immutable TeachingAction

每个 TeachingAction 至少必须 pin：

- PolicyBundle ref/hash；
- strategy family + version；
- derived TeachingStage；
- action template / move plan；
- action modifiers；
- scaffold-control ceiling；
- hint-specificity ceiling；
- answer-exposure ceiling；
- validation obligations；
- decision id。

SYS08/LLM 可以把执行做得更保守，但不能扩大 support/exposure 或改变 action semantics。

### Layer 10 — DecisionTrace

DecisionTrace 必须支持 replay、audit、debug、shadow comparison 与 experiment foundation。

至少应能表达：

```text
TeachingContext refs/version
context fingerprint
PolicyBundle version/hash
strategy family/version
available actions
hard-filtered actions
filter reason codes
derived TeachingStage
stage mapper version
features + availability + confidence + feature version
candidate scores
selected TeachingAction
previous action
transition reason
material evidence refs
tie-break reason
experiment assignment
behavior policy type
action propensity
replayability status
```

DecisionTrace 是 append-only audit record，不成为业务状态 owner。

## PolicyBundle

v0.3 正式采用 immutable、versioned `PolicyBundle`。至少包含：

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

PolicyBundle 必须满足：

```text
immutable publish
atomic activation
exact version pinning
historical bundle retention
no executable DSL
```

进一步要求：

- 每个 TeachingAction pin exact bundle/version/hash；
- activation 只影响新 TeachingAction，不修改旧 action；
- config hot reload 不允许在一次 decision 中混合组件版本；
- 历史 replay 必须取得当时 exact bundle；
- missing historical bundle → `not fully replayable`，不得假装 fully replayable；
- previous known-good bundle MAY 作为明确 fallback，但必须有 reason code 与 trace。

## DecisionTrace Probability Semantics

v0.3 deterministic canonical policy 固定：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

禁止写：

```text
action_propensity = 1.0
```

原因：数学上的 deterministic selection 与 statistical behavior-policy propensity 不是同一个数据语义。写 `1.0` 会让后续分析误判该日志满足 IPS/SNIPS/DR/OPE 所需 propensity contract。

同时必须分离：

```text
experiment assignment probability
≠
action selection propensity
```

例如 B2/B3 variant 可以有 `assignment_probability = 0.5`；B3 内部仍是 deterministic，因此 `action_propensity = null`。

只有未来真的在 hard-filtered safe action set 上按已知分布随机选择 action，才允许记录真实 action propensity，且必须在 decision time 产生，不能事后推断。

## Alternatives Considered

### Alternative A — Giant deterministic if/else

优点：

- 实现简单；
- 初始开发快；
- 完全可以做到 deterministic。

不采用为 canonical architecture 的原因：

- hard rules、candidate generation、feature logic、score、transition 混在一起；
- 边界难测试，规则之间产生隐式优先级；
- replay 很难解释“当时哪个组件版本导致结果”；
- 演化后容易形成不可审计的隐式 policy；
- anti-oscillation 与 fallback 会逐步散落在分支中。

允许局部 evaluator 内部使用普通代码条件，但不能把整个 canonical policy 收敛成一个 giant selector function。

### Alternative B — Generic Rule Engine / DSL

包括：

- Drools-like engine；
- JSON rules；
- embedded expression language；
- executable Python config。

优点：

- 动态规则能力强；
- 配置表面上可由非代码方式扩展。

不采用原因：

- v0.3 policy domain 规模仍小，不需要通用推理引擎；
- 引入第二语言/第二执行环境；
- validation、debugging、security、sandbox 与版本治理成本增加；
- config 很容易演化成不可审计代码；
- arbitrary expressions 使 deterministic semantics 与 migration 更难稳定；
- typed declarative data + code-defined evaluator 已足够表达当前需求。

### Alternative C — LLM Strategy Selector

优点：

- 可以利用模型语义理解；
- 对未知内容和自然语言上下文表面上更灵活。

不采用为 canonical owner 的原因：

- nondeterministic；
- prompt/model drift；
- hard rule enforcement 不可靠；
- replay 困难；
- action availability 不稳定；
- failure / answer-exposure semantics 不适合安全委托；
- 模型输出不能成为未经 typed validation 的最终 TeachingAction truth。

LLM selector 可以作为 B2 experiment baseline，但必须：

```text
same action vocabulary
same assessment/retrieval/model execution assumptions
same hard shield
```

即 B2 也不能绕过 canonical hard constraints。

### Alternative D — Contextual Bandit

不采用原因：

- 当前数据不足；
- delayed reward；
- action availability / propensity foundation 尚未成熟；
- outcome linkage 尚在建立；
- 单用户探索价值有限；
- current deterministic baseline 尚未证明是瓶颈；
- exploration 仍可能产生学习与测量风险。

Bandit 只在未来满足数据覆盖、真实 propensity、稳定 reward、safe action set 与可信 evaluation 后重新评估。

### Alternative E — Offline / Online RL

不采用原因至少包括：

- long-horizon reward attribution；
- delayed retention / transfer outcome；
- partial observability；
- action safety / answer exposure；
- logged-data coverage 不足；
- OPE reliability 不足；
- online exploration harm；
- explainability / rollback 成本；
- learned reward 容易偏离真实 learning outcome。

v0.3 不采用 Offline RL、Online RL 或 learned reward 作为 canonical policy。

## Consequences

### Positive

- deterministic replay；
- auditability；
- hard-rule safety；
- stable behavior under fixed inputs/version；
- clear TeachingStage / candidate / feature / score / transition semantics；
- anti-oscillation 具有显式机制，而不是依赖隐藏 heuristics；
- PolicyBundle 支持 atomic activation 与历史重放；
- clear LLM boundary；
- DecisionTrace 可解释 hard filter、score、stay/switch 与 tie-break；
- versioned experiments 更容易控制；
- 为未来 supervised model、Contextual Bandit 或其他 challenger 先建立正确 action-availability/outcome 数据基础。

### Negative / Cost

- policy 需要持续手工设计和领域治理；
- feature/normalization/weight calibration 有维护负担；
- PolicyBundle component version 管理复杂度上升；
- candidate table 与 rule set 会随领域扩展增长；
- 需要维护 gold set、scenario replay、sequential replay、property tests 与 migration fixtures；
- deterministic heuristic policy 的长期 personalization ceiling 可能低于成熟 learned policy；
- historical bundle/context 缺失时只能 partial replay；
- legacy policy config 和 DecisionTrace schema 需要 migration/upcaster。

## Migration / Rollback

### Migration implications

后续 Spec Delta 必须显式处理：

1. **TeachingContext**：现有 input-list 语义升级为 immutable refs/version snapshot；历史缺失字段不可伪造，应标 replayability gap。
2. **Old policy config**：现有 loose `policy_version/weights/config` 迁入 versioned PolicyBundle manifest；无法重建 component version 的记录只做 best-effort。
3. **Old state machine**：保留为 stage-definition/transition input 的 legacy source，不得成为 learner truth；需要迁移到 versioned `stage_mapper`/anti-oscillation profiles。
4. **Old giant selector / Socratic selector**：拆分成 typed candidates/evaluator/adapter；不得继续拥有最终 TeachingAction。
5. **DecisionTrace v1 experiment.propensity**：必须区分其历史语义。若不能证明是 action-selection propensity，就不能投影为新 `action_propensity`；应标 migration ambiguity 或 null。
6. **Historical replay**：缺 TeachingContext exact refs、PolicyBundle 或 old component version 时标 `partial/not_replayable`。
7. **Support/exposure**：旧整数/scale 的迁移遵循 ADR-0001 与后续 Spec mapping，不能让 selector 假定旧值已经具备新语义。

### Rollback

PolicyBundle activation 可以回滚到 previous known-good bundle，但必须形成新 activation event/trace，并只影响后续 decision。

不能通过 rollback：

- 修改历史 TeachingAction；
- 重写历史 DecisionTrace；
- 把 hard constraint 降级成 soft penalty；
- 恢复 LLM 为 canonical owner；
- 伪造 historical propensity。

如未来需要推翻本架构，应建立新的 superseding ADR。

## Spec Impact

后续 `v0.3 Spec Delta` 至少需要更新：

- **TeachingContext**：immutable refs/version/fingerprint/missing semantics；
- **SYS05**：完整 10-layer deterministic policy stack；
- **PolicyBundle**：manifest、component version、digest、activation、retention；
- **TeachingAction**：exact bundle pin、stage、support/exposure envelope、validation obligation；
- **DecisionTrace**：context/stage/features/candidate scores/transition/material evidence/tie-break/replayability；
- **Decision probability contract**：assignment probability 与 action propensity 分离；
- **Testing**：OPVE、G0/G1/G2、scenario/sequential replay、property/metamorphic、baseline differential、synthetic stress；
- **Observability**：DecisionTrace / outcome linkage、policy/replayability metrics；
- **Vertical Slice**：同一 LearningActivity 在不同 TeachingContext 下产生不同但可解释 action，并覆盖 support increase/fade、independent validation、delayed/transfer outcome；
- **Experiment logging**：B2/B3 assignment 与 action-selection semantics 分离。

本 ADR 不修改这些 Spec。

## Validation

后续 Spec/implementation 必须至少证明：

1. fixed context + fixed bundle + fixed assignment → same semantic TeachingAction；
2. hard-filtered action 永远不能被 scorer、LLM 或 experiment 恢复；
3. TeachingStage 不写入 LearnerState；
4. missing feature 不被当成 0；
5. candidate table 不允许 arbitrary runtime code / LLM-generated rules；
6. weighted scoring 不宣称 causal learning-effect estimate；
7. anti-oscillation 实现 material evidence、sticky continuity、evidence-opportunity dwell、hysteresis、transition priority、repeated-failure override；
8. tie-break 在 runtime 无随机性；
9. TeachingAction pin exact PolicyBundle；
10. `action_propensity = null` for deterministic B3；
11. experiment assignment probability 与 action propensity 是不同字段/语义；
12. missing historical bundle/context 时 replayability 明确降级；
13. B2 LLM selector 仍经过同一个 hard shield；
14. no eligible action / hard-rule conflict 显式 fail-safe/fail-closed，不由 LLM 仲裁。

## Out of Scope

v0.3 本 ADR 不授权：

```text
Contextual Bandit
Offline RL
Online RL
Deep KT as canonical truth
complex IRT-CAT
open-world misconception discovery
school-level population A/B
multi-agent teaching control
automatic learned reward
synthetic learner as learning evidence
free-form LLM TeachingAction ownership
generic Productive Failure strategy
always-on Socratic tutor
generic executable policy DSL
```

## Open Parameters

本 ADR 不冻结具体数值：

```text
mastery threshold
failure ceiling
minimum dwell
switch margin
hint sequence
scaffold fade amount
diagnostic confidence cutoff
transfer novelty threshold
delay windows
policy weights
practical harm margin
```

这些值继续属于：

```text
versioned configurable parameter
```

和/或：

```text
Askora Experiment Required
```

本 ADR 只固定：这些参数属于哪个机制、必须版本化、必须进入 PolicyBundle/实验配置，并且不能被描述成学习科学常数。

## References

- `docs/design/research/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md`
- `docs/design/个人AI辅助学习平台设计方案.md`
- `docs/design/AI学习系统算法与教学内核设计.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/observability-standard.md`

## Supersedes / Superseded By

Supersedes: none. This ADR formalizes the v0.3 Canonical Design decision; downstream v0.2 implementation contracts remain unchanged until Spec Delta.

Superseded by: none.