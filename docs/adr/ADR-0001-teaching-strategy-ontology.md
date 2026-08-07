# ADR-0001 — Teaching Strategy Ontology

Status: accepted
Date: 2026-08-07
Decision owners: Askora Canonical Design / Architecture Governance
Affected specs: `docs/specs/domain/domain-model.md`, `docs/specs/systems/05-teaching-policy.md`, `docs/specs/systems/03-learner-model.md`, `docs/specs/systems/04-assessment.md`, `docs/specs/domain/decision-contract.md`, `docs/specs/architecture/state-ownership.md`

## Context

Askora v0.2 的公共领域模型与 SYS05 Spec 使用 9 个 top-level `TeachingStrategy.family`：

```text
DIRECT_INSTRUCTION
WORKED_EXAMPLE_FADING
SOCRATIC_PROBING
GUIDED_PRACTICE
ERROR_REMEDIATION
RETRIEVAL_PRACTICE
PRODUCTIVE_FAILURE
TRANSFER_CHALLENGE
METACOGNITIVE_REFLECTION
```

该模型把不同抽象层级混在同一个 enum 中：

- `DIRECT_INSTRUCTION` 更接近一次具体 explanation move；
- `WORKED_EXAMPLE_FADING` 同时编码 worked-example move 与跨多步 fading progression；
- `SOCRATIC_PROBING` 是 bounded interaction technique，却被提升为长期顶层策略；
- `METACOGNITIVE_REFLECTION` 是横切 modifier 或 SYS06 metacognitive activity，而非同级 teaching-control intent；
- `PRODUCTIVE_FAILURE` 缺乏 v0.3 可通用执行、可审计的进入条件，不适合作为 baseline selectable family；
- `GUIDED_PRACTICE`、`ERROR_REMEDIATION`、`RETRIEVAL_PRACTICE`、`TRANSFER_CHALLENGE` 则更接近稳定 episode/control intent。

因此旧 enum 过度表达教学话术/interaction technique，而不足以表达“一个相对稳定教学 episode 为什么存在、由什么控制意图驱动”。这会造成以下工程问题：

1. candidate generation 的维度不稳定，新增一个 move 往往被误建成新增 strategy；
2. DecisionTrace 难以区分“为什么选择该 episode intent”和“具体这一轮怎么说/怎么提示”；
3. anti-oscillation 无法可靠判断是 strategy transition 还是同一 strategy 内 move 变化；
4. historical migration 难以解释旧 `strategy_id` 的真实含义；
5. experiment comparison 混合了 strategy、move 与 modifier，无法形成稳定 action vocabulary；
6. legacy Socratic engine 容易继续成为隐式全局 policy owner；
7. Productive Failure 等研究性方法会因为 enum 已存在而被误认为 v0.3 已授权使用。

v0.3 Research Synthesis 与 Canonical Design 已冻结新的 ontology。本 ADR 不重新研究或重新投票，只把该 breaking domain decision 正式固化。

## Decision

### 1. Strategy Family

`StrategyFamily` 表示：

> relatively stable teaching episode / control intent。

v0.3 canonical top-level Strategy Family 仅有：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

这六类是 Askora 的工程 ontology，不主张它们是学习科学文献天然存在的唯一六类教学法。

### 2. TeachingAction

`TeachingAction` 表示：

> SYS05 基于某个 immutable `TeachingContext`、在固定 `PolicyBundle` 下产生的不可变具体教学决策。

TeachingAction 必须独立于 Strategy Family identity，并可固定：

- strategy family + version；
- action template / move plan；
- action modifiers；
- support / hint / exposure ceiling；
- validation obligation；
- success / failure / exit semantics；
- PolicyBundle ref/hash；
- decision id。

执行层不得原地改变其教学语义。

### 3. Interaction Move

`InteractionMove` 表示一次具体 tutor operation。v0.3 action vocabulary 可包含：

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

Interaction Move 是 TeachingAction 的组成语义，不得因为新增 move 就自动创建新的 top-level Strategy Family。

### 4. Action Modifier

`ActionModifier` 用于横切表达不应占用顶层 strategy taxonomy 的语义，例如：

```text
self_explanation
metacognitive_reflection
feedback_type
representation_style
transition_intent
support_reason
target_scope
delivery_mode
```

Modifier 不改变 Strategy Family ownership，也不能覆盖 hard constraints。

### 5. Legacy strategy mapping

旧 strategy 名称必须经过显式、版本化 mapping 投影到新 ontology：

| Historical value | Canonical projection |
|---|---|
| `DIRECT_INSTRUCTION` | `EXPLICIT_INSTRUCTION` 下的 Interaction Move / TeachingAction |
| `WORKED_EXAMPLE` | `EXPLICIT_INSTRUCTION` 下的 Interaction Move / TeachingAction |
| `WORKED_EXAMPLE_FADING` | `FADING_PRACTICE` 下的 action pattern；其中 `WORKED_EXAMPLE` move 仍属于具体 move 语义 |
| `SOCRATIC_PROBING` | `GUIDED_PRACTICE` 下的 bounded `SOCRATIC_PROBE` Interaction Move；诊断场景仍受同一边界约束 |
| `GUIDED_PRACTICE` | 同名 canonical Strategy Family |
| `ERROR_REMEDIATION` | 同名 canonical Strategy Family |
| `RETRIEVAL_PRACTICE` | 同名 canonical Strategy Family |
| `TRANSFER_CHALLENGE` | 同名 canonical Strategy Family |
| `METACOGNITIVE_REFLECTION` | Action Modifier，或 SYS06 `METACOGNITIVE_REVIEW` activity |
| `PRODUCTIVE_FAILURE` | v0.3 deferred；不得自动映射到任一 canonical family |

### 6. TeachingStage remains separate

`TeachingStage` 不是 Strategy Family 的持久状态副本，也不是 LearnerState。其语义继续固定为：

```text
TeachingStage = f(TeachingContext, PolicyBundle)
```

它是 activity-specific、transient、derived policy feature。若进入 DecisionTrace，只记录本次派生值及 mapper version；任何 cache 都必须可删除、可重建。

### 7. Support / Hint / Exposure compatibility

本 ADR 不创建第三个独立 support ontology ADR。与 TeachingAction vocabulary 直接相关的帮助语义按 Canonical Design 归属本 ADR 的 action semantics：

```text
scaffold_control: NONE | LOW | MEDIUM | HIGH
hint_specificity: NONE | ORIENTATION | CONCEPTUAL_STRATEGIC | SUBGOAL | PARTIAL_STEP | BOTTOM_OUT
answer_exposure: NONE | PARTIAL | COMPLETE
assistance_state: INDEPENDENT | ASSISTED | ANSWER_EXPOSED
```

所有权保持：

```text
SYS05 → allowed scaffold / hint / exposure envelope
SYS08 → execute inside envelope, may only tighten
SYS04 → record actual assistance / exposure
SYS03 → evidence eligibility / weighting
```

这些字段的具体 schema 由后续 Spec Delta 冻结；本 ADR 只固定它们不能继续被单一 strategy/move enum 或单一整数帮助等级混合表达。

## Alternatives Considered

### Alternative A — 保留原 9 个 strategy enum

优点：迁移成本最低，当前代码/Spec 改动较少。

不采用原因：

- 抽象层级混杂的问题继续存在；
- Socratic、direct instruction、metacognitive reflection 会继续被错误理解为同级长期策略；
- worked-example fading 同时承载 move 与 progression；
- Productive Failure 的 enum 存在会被误解为 v0.3 已授权 baseline；
- candidate generation、trace、anti-oscillation 与 experiment action comparison 继续不稳定。

### Alternative B — 把所有 Interaction Move 都提升成 Strategy

优点：taxonomy 看似统一，每一种教学动作都有唯一名字。

不采用原因：

- strategy 数量会随话术/交互能力增长而膨胀；
- 同一 episode 内的正常 move variation 会被误判为 strategy switching；
- anti-oscillation、episode attribution、experiment comparison 失去稳定控制层；
- policy table 维度变得过细且难治理。

### Alternative C — 完全不使用 Strategy Family，只使用 flat TeachingAction

优点：对象更少，所有决策都落在单一 action vocabulary。

不采用原因：

- 缺少稳定 episode/control-intent 层，无法可靠表达 continuity、fading progression 与 transition；
- trace 无法将“高层教学意图”与“具体动作实现”分开；
- experiment 与长期 outcome 分析难以聚合相同行为目的的不同 action templates；
- action vocabulary 会承担过多控制语义。

### Alternative D — 由 LLM 自由生成 strategy name / policy taxonomy

优点：表面灵活，可快速适应不同学科与话术。

不采用原因：

- taxonomy 不稳定、不可版本化；
- prompt/model drift 会改变策略名称和语义；
- candidate availability、migration、trace 与 replay 无法形成稳定合同；
- 会把 SYS05 的 canonical policy ownership重新交给模型；
- hard-rule、support/exposure 与 experiment 分析无法可靠绑定到动态名称。

## Consequences

### Positive

- Strategy ontology 的抽象层级明确；
- candidate table 可以围绕稳定 Strategy Family 构建；
- action/move vocabulary 可独立版本化和扩展；
- anti-oscillation 可以区分 episode transition 与同一 family 内 move variation；
- DecisionTrace 可以分别解释 strategy family、TeachingAction、move、modifier；
- B2/B3 与后续实验可比较稳定的 action vocabulary；
- Socratic 被限制为 bounded move，降低 always-on Socratic tutor 风险；
- metacognitive semantics 可横切复用，而不是污染 strategy enum；
- Productive Failure 明确 deferred，避免 enum 驱动的范围蔓延。

### Negative / Cost

- 现有 `TeachingStrategy.family` 是 breaking enum change；
- 历史 strategy records 必须增加 mapping/version metadata；
- `TeachingAction` schema、UI、DecisionTrace、policy config 需要迁移；
- legacy Socratic selector/state machine 需要 adapter/拆分；
- 原 `scaffold_level`、`hint_level`、0–4 exposure 不能保证无损映射到正交语义；
- 部分历史记录只能 best-effort projection，historical replay 可能只能 partial replay；
- 需要维护 canonical mapping table、legacy reader/upcaster 和 replay fixtures。

## Migration / Rollback

### Migration principles

1. 不允许旧 9-value enum 与新 6-family enum 长期并列成为两个 truth source。
2. legacy 数据 MAY 保留 `original_strategy_value`、原 action payload 与原 policy version 作为审计信息。
3. canonical projection MUST 记录 `strategy_mapping_version` 或等价 mapping version。
4. mapping 必须输出 canonical family + move/pattern/modifier/deferred classification，而不是只做字符串 rename。
5. 无法无损映射的数据必须标记 `migration_ambiguity`、`partial_replayability` 或等价状态。
6. `PRODUCTIVE_FAILURE` 不得自动映射到任一 family；历史记录可以保留 original value，但 v0.3 selector 不得生成该 canonical family。
7. legacy Socratic selector/state machine 不再拥有 TeachingStrategy truth；迁移后只能作为 adapter/执行组件，最终 TeachingAction ownership 归 SYS05。
8. 迁移期如必须双读/双写，必须明确新 ontology 为 canonical truth，并设置终止旧字段的条件；不得永久双 truth。

### Rollback

如新 Spec/实现需要回滚，只能回滚 implementation deployment 或 PolicyBundle activation，不能把已经 Accepted 的 ontology 重新解释成旧 9-family canonical truth。若未来确需改变该决策，应新建 superseding ADR。

## Spec Impact

后续 `v0.3 Spec Delta` 至少必须处理：

- Domain Model Delta：`TeachingStrategy.family` 9 → 6；
- SYS05 Delta：Strategy/Action/Move/Modifier 的正式 contract；
- `TeachingAction` schema：strategy family、move plan、modifiers、support/exposure envelope；
- legacy strategy enum mapping 与 adapter；
- SYS03/SYS04 对正交 assistance/exposure 字段的消费/记录；
- DecisionTrace strategy/action/move/modifier 字段；
- legacy Socratic selector/state-machine migration；
- historical replayability / upcaster semantics。

本 ADR 不修改上述 Spec。

## Validation

后续 Spec/implementation 必须至少证明：

1. canonical top-level Strategy Family 只有 6 个；
2. `DIRECT_INSTRUCTION`、`WORKED_EXAMPLE`、`SOCRATIC_PROBE`、`METACOGNITIVE_CHECK` 等不会被重新注册为 top-level family；
3. `PRODUCTIVE_FAILURE` 不可由 v0.3 canonical selector 生成；
4. 同一 family 内改变 Interaction Move 不自动视为 strategy transition；
5. historical strategy records 经过显式 mapping version 投影；
6. ambiguous mapping 不被伪装成 lossless replay；
7. legacy Socratic engine 不能直接拥有最终 TeachingAction；
8. support/hint/exposure 与 actual assistance 的 owner 边界保持不变。

## Out of Scope

本 ADR 不授权：

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

本 ADR 不冻结任何具体数值。以下继续属于 `versioned configurable parameter` 和/或 `Askora Experiment Required`：

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

ADR 固定的是这些参数所属机制、版本化与审计要求，而不是具体值。

## References

- `docs/design/research/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md`
- `docs/design/个人AI辅助学习平台设计方案.md`
- `docs/design/AI学习系统算法与教学内核设计.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/architecture/state-ownership.md`

## Supersedes / Superseded By

Supersedes: none. This ADR changes the downstream v0.2 implementation contract only after Spec Delta; it does not rewrite historical ADRs.

Superseded by: none.