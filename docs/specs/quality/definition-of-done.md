# Askora Definition of Done

> Spec ID：`DOD-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Existing Completion Contracts Retained

### DOD-001 — Scope

实现任务只有在对应 Spec/EXEC Acceptance Criteria 满足、修改范围合规、无未声明公共 API/Schema/DB semantic change 时 MAY 报 DONE。

### DOD-002 — Architecture

MUST 遵守 `ARCH-*`、`DEP-*`、`STATE-*`；不得新增第二 truth、绕过 canonical orchestration/policy path，legacy adapter 必须有迁移目的/retirement condition。

### DOD-003 — Data

新状态必须有 owner；关键更新可追溯 event/evidence/decision；idempotency/concurrency/version/migration 语义明确；需要恢复的 durable task/outbox 有效。

### DOD-004 — AI

Model/Prompt/schema/version 可追踪；fallback MUST NOT 改领域语义；prompt injection / exposure leakage / tool authorization guard 不得绕过；Mock MUST NOT 当真实模型连接证据。

### DOD-005 — Tests

新增关键行为有自动化测试；targeted/applicable suites 已运行；lint/type/build 按范围执行；不得 skip/delete/weaken tests 伪造通过。

### DOD-006 — Failure

Timeout、invalid input、dependency failure、retry exhausted 等适用失败路径必须定义/测试；系统故障 MUST NOT 记录为 learner error；side-effect retry 必须 idempotent。

### DOD-007 — Observability

新关键 decision/event/model call 有 trace；新 error 使用稳定 code；logs 不泄漏 secret/不必要敏感内容。

### DOD-008 — Documentation / SPEC GAP

若实现需要改变已冻结公共行为，执行代理 MUST 先报告 SPEC GAP。已获用户架构自治委托时，
MUST 先创建/接受所需 ADR、更新 Spec 并冻结 EXEC，再继续修改代码；未获委托时 MUST 停止
并等待决定。任何情况下都 MUST NOT 先改代码后补文档。

### DOD-020 — PARTIAL / BLOCKED

若大部分工作完成但存在无法在当前 Spec 安全实现的缺口，必须标 `PARTIAL` 或 `BLOCKED_BY_SPEC_GAP`，MUST NOT 称 DONE。

### DOD-030 — Real Model E2E

涉及 LLM gateway/orchestrator“已接通”的任务，至少一次真实已配置模型调用成功才可满足对应 AC；普通 unit/integration 仍应主要使用 Mock/fixture。

## 2. Migration Done Baseline

Database/state migration 只有在 migration 可执行、representative fixture backfill 正确、owner truth 明确、reconciliation test 通过、legacy write path 关闭或有关闭条件、rollback/forward-fix 明确时才算完成。

## 3. v0.3 Release Gate — Engineering

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
SYS02/SYS08 tightening-only
```

### DOD-201

Engineering Gate PASS 只意味着系统按合同可靠执行；MUST NOT 宣称 adaptive policy 已改善 learning outcomes。

## 4. v0.3 Release Gate — Policy Correctness

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

任何 hard-rule violation、forbidden action、policy bypass、random tie-break 或无法解释的 illegal oscillation MUST 阻断 Policy Correctness Gate。

### DOD-212

G1 MAY 有多个 acceptable actions；MUST NOT 为方便测试强制所有教学情境唯一 gold action。

## 5. v0.3 Release Gate — Learning Evidence

### DOD-220

Learning Evidence Gate canonical condition：

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

学习证据 SHOULD 以 no-hint independent success、delayed independent performance、independent transfer、unit-time capability gain 为 primary outcomes。Engagement、conversation turns、likes、hint count、token count、session duration MUST NOT 作为 primary learning outcome/reward。

### DOD-222 — Insufficient Evidence

Engineering/Policy gates 已通过但真实学习证据不足时，status MUST 为：

```text
LEARNING_EVIDENCE_INSUFFICIENT
```

该状态不是 engineering failure，也 MUST NOT 改写成“已证明有效”。

### DOD-223 — No Learning Harm

Practical harm margin/criteria MUST versioned/traceable，并基于真实 OutcomeObservation/experiment design；具体值是 configurable/experimental parameter，MUST NOT 伪装成学习科学常数。

### DOD-224 — Experimental Data Foundation

至少要求 ExperimentAssignment、assignment probability、TeachingContext/PolicyBundle/action refs、actual assistance/exposure、OutcomeObservation、attribution/contamination、active learning time 与 replayability 可支持后续分析。Assignment probability MUST NOT 与 action propensity 混淆。

## 6. OPVE Boundary

### DOD-230

OPVE PASS MAY 支持 Engineering/Policy Correctness Gate，验证 determinism、constraint compliance、transition correctness、candidate validity、anti-oscillation、no infinite loop、behavior difference。

### DOD-231

OPVE、G0/G1、synthetic learner MUST NOT 单独满足 Learning Evidence Gate；不能证明 human efficacy/retention/transfer/population superiority。

## 7. v0.3 Spec / Migration Gate

### DOD-240

进入 v0.3 Vertical Slice 前必须确认：ADR-0001/0002 reflected；SD-01～SD-11 resolved；six StrategyFamily only；TeachingContext/TeachingStage/PolicyBundle contracts；ErrorType 7+UNKNOWN；orthogonal assistance；anti-oscillation/deterministic tie-break；DecisionTrace probability unambiguous；Outcome/Experiment no second truth；legacy Socratic no final action owner；6 Breaking Changes + 9 Migration Candidates 有 migration semantics。

### DOD-241

任何 active writer 继续把 legacy strategy enum、integer scaffold/hint/exposure、ambiguous propensity 写为 canonical truth，均为 migration gate failure。

## 8. Recovery / Security / Observability Gates

### DOD-250

Release candidate MUST 能从 TeachingAction 追到 context/bundle/DecisionTrace/execution/Attempt/AssessmentResult，并在有 outcome 时关联 OutcomeObservation/ExperimentAssignment；MUST NOT 要求 Outcome 回写 DecisionTrace 才能关联。

## 9. Status Vocabulary

### DOD-260

至少支持：

```text
ENGINEERING_GATE_FAILED
POLICY_CORRECTNESS_GATE_FAILED
LEARNING_EVIDENCE_INSUFFICIENT
RELEASE_ELIGIBLE
```

产品 release policy MAY 细分，但 MUST 保留三层 gate 语义边界。

## 10. Acceptance Criteria

新增 v0.3 AC：

- `DOD-AC-201`：Engineering Gate 与 Policy Correctness Gate 可独立判定。
- `DOD-AC-202`：G0 < 100% 或 forbidden action > 0 时 Policy Gate 必失败。
- `DOD-AC-203`：answer-exposed/assisted success 后无 validation obligation 时 Policy Gate 必失败。
- `DOD-AC-204`：Engineering/Policy PASS 但学习证据不足时为 `LEARNING_EVIDENCE_INSUFFICIENT`。
- `DOD-AC-205`：process metrics 不可满足 primary Learning Evidence Gate。
- `DOD-AC-206`：synthetic learner/OPVE 不被当 human learning evidence。
- `DOD-AC-207`：release data foundation 区分 assignment probability/action propensity。

## 11. Forbidden Completion / Release Claims

禁止把以下称为 DONE/learning efficacy：关键 TODO/pass/NotImplemented；只有 Mock 却声称真实模型可用；测试未运行却说通过；删除失败测试；发现 Spec conflict 后未完成授权与 ADR/Spec/EXEC 治理就隐式选方案；新旧 truth 双写无 reconciliation/retirement；仅 UI 正常但事件/证据/状态链未接通；Engineering Correct → 学习有效；Policy Correct → retention/transfer 已提升；synthetic learner → 真人效果；process metrics → primary reward；ambiguous propensity → causal experiment data；隐藏 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 12. Final v0.3 Gate

当且仅当 Engineering Gate、Policy Correctness Gate 满足，release 所需学习证据状态被诚实标记、实验数据基础正确、无 blocking SPEC GAP 时，implementation MAY 进入相应 release/experimental stage。学习证据不足时 MAY 工程迭代，但 MUST 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。
