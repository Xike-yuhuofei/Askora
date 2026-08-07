# Askora Testing Standard

> Spec ID：`TEST-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Existing Testing Contracts Retained

### TEST-001 — Contract-oriented Testing

测试目标不只是“代码能跑”，而是验证 Spec 的业务边界、状态所有权、失败语义与学习闭环。

### TEST-002 — Spec Traceability

新增/修改关键行为 MUST 有自动化测试，并在测试名/docstring/marker/邻近注释中引用至少一个 Spec/AC ID。

## 2. L0～L6 Levels

```text
L0 Static / Architecture
L1 Unit
L2 Contract
L3 Integration
L4 End-to-End
L5 Replay / Migration / Recovery
L6 AI Quality / Security Evaluation
```

### TEST-010 — L0

验证 lint、type、import/dependency rules、禁止 cross-owner repository writes 等。

### TEST-011 — L1

纯领域算法/规则使用 deterministic unit tests，不依赖 DB/network/LLM。

### TEST-012 — L2

验证 Command/Event/API/public schema、error code、version compatibility、adapter contract。

### TEST-013 — L3

使用真实 SQLite repository/outbox/worker/orchestration adapter；模型/外部依赖 MAY mock。

### TEST-014 — L4

验证真实教学 vertical loop；至少一个受控 E2E MUST 使用实际配置模型，Mock-only 不算模型接通验收。

### TEST-015 — L5

验证 restart recovery、event/policy replay、migration、projection rebuild、idempotency、late event、invalidated evidence recompute。

### TEST-016 — L6

固定 eval dataset 验证 citation、answer leakage、prompt injection、grader consistency、Teaching Policy、retrieval quality 等。

## 3. Existing Invariants / AI Rules

### TEST-020 — Architecture Invariants

至少自动验证：Assessment 不直接写 mastery；SYS08/LLM 不直接写 mastery/plan/review/action；Planner 不改 ReviewSchedule；SYS02/SYS08 不扩大 TeachingAction support/exposure；replay 不调用在线 LLM；ordinary/streaming 使用同 canonical facade。

### TEST-030 — Mock vs Real Model

Unit/多数 integration 使用 mock/fixture；provider connectivity/真实 structured output/E2E 使用真实模型；eval SHOULD 固定 model snapshot/config。

### TEST-031

不得用真实模型替代 deterministic unit test，也不得用 Mock 宣称真实模型可用。

### TEST-032

AI 输出测试 SHOULD 验证 structure/constraints/grounding，而不是对完整自然语言字符串做脆弱 exact match。

### TEST-040 — Determinism

Event replay、learner projection、review update、fixed planner/policy 在 fixed inputs/version 下 MUST deterministic。

### TEST-041 — Nondeterminism Isolation

模型生成 nondeterminism MUST 隔离在 ModelInference；canonical replay MUST NOT 重新生成历史决策。

### TEST-050 — Fixture Classification

Test fixture MUST 标记 synthetic/public/user-provided-local；CI MUST NOT 依赖私密用户资料。

### TEST-051 — Minimal Curriculum Fixture

关键学习闭环 MUST 维护至少一个 deterministic curriculum fixture：material → KnowledgeUnit → item → responses → evidence → mastery → review；v0.3 SHOULD 再包含 TeachingContext/TeachingAction/DecisionTrace。

### TEST-060 — Existing Failures

若全量 suite 有与本任务无关的历史失败，执行代理 MUST 区分 targeted/new/known failures，不得删除、skip 或弱化测试伪造通过。

## 4. v0.3 OPVE Definition

### TEST-200

`OPVE = Offline Policy Verification & Evaluation`。

它验证 constrained deterministic Teaching Policy 的离线工程/策略正确性，MUST NOT 与 RL 的 causal Offline Policy Evaluation (OPE) 混淆。

### TEST-201 — OPVE Layers

OPVE 至少 MUST 包含：

1. Contract Verification；
2. Scenario Replay；
3. Sequential Transition Replay；
4. Property / Metamorphic Tests；
5. Baseline Differential Replay；
6. Synthetic Learner Stress Test。

## 5. Gold Set Contract

### TEST-210

```text
G0 — Hard Constraint Gold
G1 — Acceptable Action Set Gold
G2 — Research / Calibration Set
```

### TEST-211 — G0 Gate

G0 MUST `100% pass`，且 `forbidden action = 0`。任一 hard-rule forbidden TeachingAction 被选择都是 release blocker。

### TEST-212 — G1 Gate

G1 标准：`selected_action ∈ acceptable_actions`。MUST NOT 要求所有教学案例只有唯一 gold action；同时仍须满足 G0。

### TEST-213 — G2 Boundary

G2 用于研究/calibration/policy comparison；MUST NOT 把未冻结的 G2 preference 伪装为 hard truth。

## 6. OPVE Contract Verification

### TEST-220

至少验证：six StrategyFamily only；four-layer ontology；Productive Failure non-selectable/Socratic bounded move；ErrorType 7+UNKNOWN；TeachingContext exact-version/missing semantics；orthogonal assistance；immutable PolicyBundle；deterministic action propensity semantics；Outcome/Decision separation；single-writer ownership。

## 7. Scenario Replay

### TEST-230

相同 `TeachingContext + exact PolicyBundle + ExperimentAssignment` MUST 产生同一个 semantic TeachingAction 与等价 decision content。Replay MUST NOT 读取当前 mutable state 或调用在线 LLM。

### TEST-231

缺历史 owner version/PolicyBundle/feature source 时 MUST 期望 `PARTIAL|NON_REPLAYABLE` + reason，MUST NOT 用当前状态补成 FULL replay。

## 8. Sequential Transition Replay / Anti-Oscillation

### TEST-240

序列测试 MUST 覆盖 Material Evidence Gate、Sticky Continuity、Minimum Dwell by Evidence Opportunity、Hysteresis、Transition Priority、Repeated Failure Override。

### TEST-241

额外聊天轮、重复 policy call、LLM wording change、wall clock 仅多几秒，单独发生时 MUST NOT 触发 StrategyFamily transition。

### TEST-242

Repeated failure 达到 versioned ceiling 时 MUST 能 exit/escalate/re-diagnose；independent success evidence 应允许 fade；answer/assisted success 必须建立 validation obligation。

## 9. Property / Metamorphic Tests

### TEST-250

至少验证：hard-filtered candidate 永不被 score/experiment 恢复；SYS02/SYS08 only tighten；low confidence 不因伪 default 变激进；`MISSING != 0`；stable tie-break 不受 candidate order 影响；no candidate-set dynamic min-max semantic drift；Outcome 不回写 DecisionTrace；fresh independent Attempt 前 obligation 不自动完成；no infinite policy loop。

## 10. Baseline Differential Replay

### TEST-260

B3 MAY 与 fixed strategy、legacy selector 或 B2 LLM baseline 做 differential replay，但 comparison MUST 使用同 scenario inputs、hard shield、action vocabulary。Behavior difference 是工程/策略证据，MUST NOT 自动称为 learning efficacy。

## 11. Synthetic Learner Stress Test

### TEST-270

Synthetic learner MAY 用于 failure sequence、oscillation、transition、fallback、edge case、performance stress；MUST NOT 被引用为 human learning efficacy、retention、transfer 或 population superiority 证据。

## 12. Offline Evaluation Boundary

### TEST-280

OPVE 可以验证：determinism、constraint compliance、transition correctness、candidate validity、anti-oscillation、no infinite loop、behavior difference。

### TEST-281

OPVE 不能证明：human learning efficacy、retention benefit、transfer benefit、population superiority。

## 13. Migration / Compatibility Tests

### TEST-290

九类 migration candidates MUST 有 fixtures：historical strategy、TeachingAction、scaffold_level、hint_level、old answer exposure、legacy Socratic selector/state machine、old policy config、old DecisionTrace propensity、historical replay。

每类 MUST 验证 canonical target、read compatibility、ambiguity behavior、replayability 与 retirement condition。

### TEST-291

Ambiguous legacy propensity MUST 迁移为 null/unknown + migration reason + PARTIAL，MUST NOT 无条件变成 action propensity。

## 14. Database / Failure / Security Gates

Database tests MUST 覆盖 SQLite FK/constraints、unique aggregate version、transactional outbox、idempotency、concurrency conflict、migration fixture、projection rebuild。

每个外部依赖 MUST 测 timeout/unavailable/invalid response/partial failure/retry exhausted/fallback success/failure，并验证不会错误记录为 learner failure。

Security tests MUST 覆盖 malicious document prompt injection、unauthorized tool call、answer/rubric leakage、citation mismatch、cross-user access（服务模式）、path traversal/unsafe upload、secret leakage/logging、cross-owner write attempt。

## 15. Test Data / Parameter Governance

### TEST-300

Gold/scenario fixtures MUST 固定 schema version、PolicyBundle、owner refs、expected constraints/acceptable actions，并标注 G0/G1/G2；MUST NOT 依赖 production mutable config。

### TEST-301

Threshold/weights/dwell/switch margin 等 MUST 以 fixture/profile version 固定；测试 MUST NOT 把临时值描述为科学常数。

## 16. Acceptance Criteria

原有 AC 保留：

- `TEST-AC-001`：每个系统 Spec 至少有对应 contract/unit test suite。
- `TEST-AC-002`：首个 vertical slice 有真实 SQLite E2E。
- `TEST-AC-003`：至少一个 E2E 使用真实配置模型。
- `TEST-AC-004`：event replay 固定版本 deterministic。
- `TEST-AC-005`：architecture tests 捕获 cross-owner direct write。
- `TEST-AC-006`：restart/outbox recovery 通过。
- `TEST-AC-007`：prompt injection/answer leakage 有固定回归样本。

新增 v0.3 AC：

- `TEST-AC-201`：OPVE 六层均有 test category/fixture entry。
- `TEST-AC-202`：G0 = 100%，forbidden action = 0。
- `TEST-AC-203`：G1 使用 acceptable action set。
- `TEST-AC-204`：deterministic policy replay 不调用在线 LLM。
- `TEST-AC-205`：anti-oscillation 可 sequential replay 验证。
- `TEST-AC-206`：synthetic learner 不作为 learning evidence。
- `TEST-AC-207`：migration ambiguity / partial replay 有 fixture。

## 17. Forbidden Implementations

禁止：happy-path only；Mock-only E2E；为 CI 删除/弱化测试；实时网络内容作为无版本关键 fixture；AI full-string brittle match；provider timeout 被记 learner incorrect；把 OPVE 称 causal RL OPE；synthetic learner 宣称学习效果；G1 强制唯一 gold；online LLM 参与 policy replay；engagement/turn count 替代 learning outcome；Engineering Correct 推导 Learning Effective。