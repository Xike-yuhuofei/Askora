# Definition of Done

> Spec ID：`DOD-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Purpose

“Done” MUST 同时区分工程正确、策略正确与学习证据。任何一层通过都 MUST NOT 被包装成另一层已经成立。

### DOD-001

功能完成至少要求：contract implemented、tests passed、failure semantics explicit、state ownership respected、version/recovery/observability available、无未声明 blocking SPEC GAP。

## 2. Release Gate — Layer 1: Engineering Gate

### DOD-200

Engineering Gate 至少 MUST 验证：

```text
deterministic replay
immutable TeachingAction
TeachingContext / PolicyBundle exact version pinning
DecisionTrace completeness
no policy bypass
assessment integrity
explicit failure semantics
state ownership / no duplicate truth
schema/config versioning
persistence / idempotency / recovery
SYS08/SYS02 tightening-only
```

### DOD-201

Engineering Gate PASS 只意味着系统按合同可靠执行；MUST NOT 宣称 adaptive policy 已改善 learning outcomes。

## 3. Release Gate — Layer 2: Policy Correctness Gate

### DOD-210

Policy Correctness Gate 至少 MUST 满足：

```text
G0 = 100%
forbidden action = 0
G1 selected_action ∈ acceptable_actions
repeated failure exits/escalates/re-diagnoses
independent success can fade support
answer exposure → independent validation obligation
assisted success → independent validation obligation
low confidence → conservative behavior
no illegal oscillation
no infinite policy loop
deterministic tie-break
action_propensity = null for B3
```

### DOD-211

任何 hard-rule violation、forbidden action、policy bypass、随机 tie-break 或无法解释的非法 oscillation MUST 阻断 Policy Correctness Gate。

### DOD-212

G1 MAY 有多个 acceptable actions；MUST NOT 为方便测试把所有教学情境强制成唯一 gold action。

## 4. Release Gate — Layer 3: Learning Evidence Gate

### DOD-220

Learning Evidence Gate 的 canonical condition：

```text
Engineering Correct
+
Policy Correct
+
No Learning Harm
+
Directional Individual Learning Evidence
+
Correct Experimental Data Foundation
```

### DOD-221 — Primary Outcomes

Learning evidence SHOULD 以以下 primary outcomes 为核心：

```text
no-hint independent success
delayed independent performance
independent transfer
unit-time capability gain
```

Engagement、conversation turns、likes、hint count、token count、session duration MUST NOT 作为主要 learning outcome/reward。

### DOD-222 — Insufficient Evidence Status

当 Engineering/Policy gates 已通过，但真实学习者证据尚不足以支持学习效果结论时，release/evaluation status MUST 使用：

```text
LEARNING_EVIDENCE_INSUFFICIENT
```

该状态不是工程失败，也 MUST NOT 被改写成“已证明有效”。

### DOD-223 — No Learning Harm

No Learning Harm 的 practical margin/criteria MUST versioned、traceable，并基于真实 OutcomeObservation/实验设计；具体 margin 是 configurable/experimental parameter，MUST NOT 在 Spec 中伪装成固定学习科学常数。

### DOD-224 — Experimental Data Foundation

至少要求 ExperimentAssignment、assignment probability、TeachingContext/PolicyBundle/action refs、actual assistance/exposure、OutcomeObservation、attribution/contamination、active learning time 与 replayability 足以支持后续分析。Assignment probability MUST NOT 与 action propensity 混淆。

## 5. OPVE Boundary in DoD

### DOD-230

OPVE PASS MAY 支持 Engineering/Policy Correctness Gate，能证明 determinism、constraint compliance、transition correctness、candidate validity、anti-oscillation、no infinite loop、behavior difference。

### DOD-231

OPVE、G0/G1、synthetic learner MUST NOT 单独满足 Learning Evidence Gate；它们不能证明 human efficacy、retention、transfer 或 population superiority。

## 6. v0.3 Spec / Migration Gate

### DOD-240

实现进入 v0.3 Vertical Slice 前，必须确认：

- ADR-0001/0002 reflected；
- SD-01～SD-11 resolved；
- six StrategyFamily canonical only；
- TeachingContext/TeachingStage/PolicyBundle contract available；
- ErrorType 7 + UNKNOWN；
- assistance axes orthogonal；
- anti-oscillation/tie-break deterministic；
- DecisionTrace probability semantics unambiguous；
- Outcome/Experiment contracts do not create second truth；
- legacy Socratic does not own final TeachingAction；
- all six Breaking Changes and nine Migration Candidates have migration semantics。

### DOD-241

任何 active writer 继续把 legacy strategy enum、integer scaffold/hint/exposure、ambiguous propensity 写为 canonical truth，均视为 migration gate failure。

## 7. Recovery / Security Gate

### DOD-020

关键 durable state/event/task 在进程重启后 MUST 恢复或明确失败；outbox/idempotency MUST 防止重复 side effect。

### DOD-021

Prompt injection、tool authorization、ACL、citation/exposure guard、cross-owner writes MUST 有测试；已知绕过路径 MUST 阻断 release。

### DOD-022

至少一个真实配置模型 E2E MUST 验证 provider/gateway/orchestration 可用；Mock-only 不能满足真实模型集成 DoD。

## 8. Observability Gate

### DOD-250

Release candidate MUST 能从一个 TeachingAction 追到 context/bundle/trace/execution/Attempt/AssessmentResult，并在有 outcome 时关联 OutcomeObservation/ExperimentAssignment；不能要求 Outcome 回写 DecisionTrace 才能关联。

## 9. Status Vocabulary

### DOD-260

至少支持：

```text
ENGINEERING_GATE_FAILED
POLICY_CORRECTNESS_GATE_FAILED
LEARNING_EVIDENCE_INSUFFICIENT
RELEASE_ELIGIBLE
```

具体产品 release policy MAY 进一步细分，但 MUST 保留三层 gate 的语义边界。

## 10. Acceptance Criteria

- `DOD-AC-201`：Engineering Gate 与 Policy Correctness Gate 可独立判定。
- `DOD-AC-202`：G0 < 100% 或 forbidden action > 0 时 Policy Gate 必失败。
- `DOD-AC-203`：answer-exposed/assisted success 后无 validation obligation 时 Policy Gate 必失败。
- `DOD-AC-204`：Engineering/Policy PASS 但学习证据不足时状态为 `LEARNING_EVIDENCE_INSUFFICIENT`。
- `DOD-AC-205`：process metrics 不可满足 primary Learning Evidence Gate。
- `DOD-AC-206`：synthetic learner/OPVE 不被当作 human learning evidence。
- `DOD-AC-207`：release data foundation 能区分 assignment probability 与 action propensity。

## 11. Forbidden Release Claims

禁止：

- Engineering Correct → “学习有效”；
- Policy Correct → “保持率/迁移已提升”；
- synthetic learner → “真人学习效果”；
- engagement/turns/likes/token/session → primary reward；
- ambiguous propensity → causal experiment data；
- `LEARNING_EVIDENCE_INSUFFICIENT` 被隐藏成 PASS。

## 12. Final v0.3 Gate

当且仅当 Engineering Gate、Policy Correctness Gate 满足，且 release 所需的学习证据状态被诚实标记、数据基础正确、无 blocking SPEC GAP 时，v0.3 implementation MAY 进入相应 release/experimental stage。学习证据不足时允许工程继续迭代，但 MUST 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。