# Testing Standard

> Spec ID：`TEST-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Test Pyramid / Levels

现有 L0～L6 分层继续有效：

```text
L0 schema/static/architecture
L1 unit
L2 contract/component
L3 integration
L4 scenario/replay
L5 end-to-end/recovery/security
L6 research/evaluation validation
```

### TEST-001

任何“完成”声明 MUST 指明覆盖层级；mock-only、unit-only 或 happy-path-only MUST NOT 代替对应 integration/E2E/recovery gate。

## 2. v0.3 OPVE Definition

### TEST-200

`OPVE = Offline Policy Verification & Evaluation`。

它是对 deterministic/constrained Teaching Policy 的离线工程与策略正确性验证，MUST NOT 与强化学习语境中的 causal `Offline Policy Evaluation (OPE)` 混淆。

### TEST-201 — OPVE Layers

OPVE 至少 MUST 包含：

1. **Contract Verification** — schema、enum、owner、hard rule、immutability、versioning；
2. **Scenario Replay** — 固定 TeachingContext + PolicyBundle 的单决策 replay；
3. **Sequential Transition Replay** — 连续 evidence/action 序列与 anti-oscillation；
4. **Property / Metamorphic Tests** — invariants、monotonic constraints、no illegal expansion；
5. **Baseline Differential Replay** — B3 与固定/legacy/B2 baseline 的行为差异；
6. **Synthetic Learner Stress Test** — 压测 policy transitions、failure recovery 与 loops。

## 3. Gold Set Contract

### TEST-210 — Gold Classes

```text
G0 — Hard Constraint Gold
G1 — Acceptable Action Set Gold
G2 — Research / Calibration Set
```

### TEST-211 — G0 Gate

G0 MUST `100% pass`，并满足：

```text
forbidden action = 0
```

任何 hard-rule forbidden TeachingAction 被选择都属于 release blocker。

### TEST-212 — G1 Gate

G1 不要求所有教学情境只有唯一 gold action。测试标准为：

```text
selected_action ∈ acceptable_actions
```

同时仍必须满足所有 G0 hard constraints。

### TEST-213 — G2 Boundary

G2 用于研究、参数 calibration、policy comparison 或未来实验设计；MUST NOT 把尚未冻结的 G2 偏好伪装成 hard truth。

## 4. Contract Verification

### TEST-220

至少验证：

- canonical StrategyFamily 恰为六类；
- StrategyFamily/TeachingAction/InteractionMove/ActionModifier 四层分离；
- Productive Failure 不可选择，Socratic 为 bounded move；
- ErrorType = 7 + UNKNOWN；
- TeachingContext immutable/exact-version/missing semantics；
- support/hint/exposure/assistance 正交；
- PolicyBundle immutable/versioned；
- `behavior_policy_type=DETERMINISTIC`、`action_propensity=null`；
- assignment probability 与 action propensity 分离；
- OutcomeObservation 不修改 DecisionTrace；
- single-writer ownership。

## 5. Scenario Replay

### TEST-230

相同 `TeachingContext + exact PolicyBundle + ExperimentAssignment` MUST 产生同一个 semantic TeachingAction 与等价 DecisionTrace decision content。

Replay MUST NOT 读取当前 mutable state 或重新调用在线 LLM。

### TEST-231

缺历史 owner version/PolicyBundle/feature source 时，fixture MUST 期望 `PARTIAL|NON_REPLAYABLE` + reason，而不是把当前状态补成“成功 replay”。

## 6. Sequential Transition Replay / Anti-Oscillation

### TEST-240

序列测试 MUST 覆盖：

- Material Evidence Gate；
- Sticky Continuity；
- Minimum Dwell by Evidence Opportunity；
- Hysteresis；
- Transition Priority；
- Repeated Failure Override。

### TEST-241

以下变化单独发生时 MUST NOT 导致 StrategyFamily transition：额外聊天轮、重复 policy call、LLM wording 改变、wall clock 仅多几秒。

### TEST-242

Repeated failure 达到 versioned ceiling 时 MUST 能退出/升级/重新诊断，不能被 sticky continuity 锁死；独立成功 evidence 应允许 fade；answer exposure 必须产生 validation obligation。

## 7. Property / Metamorphic Tests

### TEST-250

至少建立以下 properties：

- hard-filtered candidate 永不被 score/experiment 恢复；
- SYS08/SYS02 只能收紧不能扩大 exposure envelope；
- lower confidence 不应通过伪默认值产生更激进确定性动作；
- `MISSING != 0`；
- candidate set 顺序变化不改变 stable tie-break semantic output；
- candidate composition 变化不允许 dynamic min-max 改写 normalization 语义；
- Outcome 不回写 DecisionTrace；
- fresh independent Attempt 前 validation obligation 不得自动完成；
- no infinite decision/transition loop。

## 8. Baseline Differential Replay

### TEST-260

B3 MAY 与 fixed strategy、legacy selector 或 B2 LLM baseline 做 differential replay，但 comparison MUST 使用相同 scenario inputs、hard shield 与 action vocabulary；差异输出是工程/行为证据，不自动等于学习效果证据。

## 9. Synthetic Learner Stress Test

### TEST-270

Synthetic learner MAY 用于高覆盖测试 failure sequence、oscillation、state transition、fallback、edge cases 与 performance。

Synthetic learner MUST NOT 被引用为：human learning efficacy、retention benefit、transfer benefit 或 population superiority 的证据。

## 10. Offline Evaluation Boundary

### TEST-280

OPVE 可以证明/验证：

```text
determinism
constraint compliance
transition correctness
candidate validity
anti-oscillation
no infinite loop
behavior difference
```

### TEST-281

OPVE 不能证明：

```text
human learning efficacy
retention benefit
transfer benefit
population superiority
```

这些结论需要真实学习者 outcome/实验数据与适当因果设计。

## 11. Migration / Compatibility Tests

### TEST-290

九类 migration candidates MUST 有 fixtures：historical strategy、TeachingAction、scaffold_level、hint_level、old answer exposure、legacy Socratic selector/state machine、old policy config、old DecisionTrace propensity、historical replay。

每类 fixture MUST 验证 canonical target、read compatibility、ambiguity behavior、replayability status 与 retirement condition。

### TEST-291

Ambiguous legacy propensity MUST 迁移为 null/unknown + migration reason + partial replay；不得无条件变成 action propensity。

## 12. Existing Cross-system Gates

### TEST-020

Persistence/outbox/idempotency/recovery MUST 有 integration/E2E 测试；应用重启后 durable task/event/state 必须恢复或明确失败。

### TEST-021

至少一个 E2E MUST 调用实际配置模型验证 provider/gateway/orchestration；Mock-only 不得声明真实模型链路可用。

### TEST-022

Security tests MUST 覆盖 prompt injection、tool authorization、ACL、citation/exposure leakage、cross-owner write attempt。

## 13. Test Data Governance

### TEST-300

Gold/scenario fixtures MUST 固定 schema version、PolicyBundle、source owner refs、expected constraints/acceptable actions，并标注是 G0/G1/G2；不得依赖当前 production mutable config。

### TEST-301

研究/实验参数 threshold、weights、dwell、switch margin 等 MUST 以 fixture/profile version 固定；测试不得把某个临时数值描述为科学常数。

## 14. Acceptance Criteria

- `TEST-AC-201`：OPVE 六层均有可执行 test category/fixture 入口。
- `TEST-AC-202`：G0 = 100%，forbidden action = 0。
- `TEST-AC-203`：G1 使用 acceptable action set，而非强制唯一答案。
- `TEST-AC-204`：deterministic replay 不调用在线 LLM。
- `TEST-AC-205`：anti-oscillation 顺序性质可通过 sequential replay 验证。
- `TEST-AC-206`：synthetic learner 只作为 stress test，不作为 learning evidence。
- `TEST-AC-207`：migration ambiguity 与 partial replay 有 fixture。

## 15. Forbidden Implementations

禁止：

- 把 OPVE 称为 causal RL OPE；
- 用 synthetic learner 宣称学习效果；
- G1 所有案例强制唯一 gold action；
- 只测最终 selected action、不测 hard filters/transition/replay；
- online LLM 参与 canonical policy replay；
- mock-only 作为真实 E2E；
- engagement/turn count 等过程指标替代学习 outcome gate；
- 把 Engineering Correct 推导成 Learning Effective。