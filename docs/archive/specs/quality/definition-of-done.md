# Askora Definition of Done

> Spec ID：`DOD-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + Product Definition Traceability  
> 上游产品定义：`docs/product/PRODUCT-DEFINITION.md`

## 0. Acceptance Ownership

Askora 的 DONE / PASS 必须区分：

```text
Product Acceptance
UX Acceptance
Technical / Engineering Acceptance
Quality Acceptance
Learning Evidence
```

这些层级可以相互提供证据，但不能互相替代。

### DOD-000 — Product Traceability

任何**面向产品行为**的新建或实质重构 Design / ADR / Spec / Vertical Slice / EXEC / Linear Issue，MUST 明确引用适用的：

- `CAP-*`；
- `PD-REQ-*`；
- `PD-RULE-*` / `PD-NFR-*`（适用时）；
- 已存在的 `PD-AC-*`（适用时）。

纯 infrastructure / internal maintenance 工作 MAY 标记 `Product Traceability: N/A — infrastructure-only`，但必须说明为什么不会改变 Product Capability、v1 Feature Scope、Product Rule 或 Product Acceptance。

技术 AC、Vertical Slice AC、UI AC 不得自行升级为新的 `PD-AC-*`。若产品层定义缺失，报告 `PRODUCT DEFINITION GAP`。

## 1. Existing Completion Contracts Retained

### DOD-001 — Scope

实现任务只有在以下条件满足时 MAY 报 DONE：

- 对应 Spec/EXEC Acceptance Criteria 满足；
- 修改范围合规；
- 无未声明公共 API/Schema/DB semantic change；
- 产品面向任务已引用适用 `CAP-* / PD-REQ-*`，且没有用技术 PASS 冒充 Product Acceptance；
- 若 Issue 声称“该产品能力/Feature 已完成”，则适用 Product Acceptance 必须有明确证据或在上游明确标注未完成。

Infrastructure-only 任务可以 Engineering DONE，但不得据此声称上游 Product Capability 已完整交付。

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

### DOD-008 — Product / Design / SPEC GAP

若实现需要改变已冻结的 Product Capability、v1 Feature Scope、Product Rule、Product Requirement 或 Product Acceptance，执行代理 MUST 先报告 `PRODUCT DEFINITION GAP`，不得在 Design / Spec / code 中自行决定。

若 Product Definition 已明确，但实现需要改变已冻结 Design / ADR / Spec 公共行为，则报告对应 `DESIGN GAP` / `SPEC GAP`。已获用户架构自治委托时，MUST 先在正确 authority 层完成变更并冻结，再继续修改代码；未获委托时 MUST 停止并等待决定。

任何情况下都 MUST NOT 先改代码后补 Product Definition / ADR / Spec。

### DOD-020 — PARTIAL / BLOCKED

若大部分工作完成但存在无法在当前 Product Definition / Design / Spec 安全实现的缺口，必须标 `PARTIAL`、`BLOCKED_BY_PRODUCT_DEFINITION_GAP` 或 `BLOCKED_BY_SPEC_GAP`，MUST NOT 称 DONE。

### DOD-030 — Real Model E2E

涉及 LLM gateway/orchestrator“已接通”的任务，至少一次真实已配置模型调用成功才可满足对应 AC；普通 unit/integration 仍应主要使用 Mock/fixture。

### DOD-031 — Desktop Model Settings Closure

桌面模型设置只有在 OS-protected save、synthetic probe、runtime revision verification、apply rollback、clear tombstone、renderer secret isolation 与 relaunch recovery 均通过自动化测试后才可报 Engineering DONE。若声称当前真实 provider 可用，还必须在 packaged macOS app 中重新完成 provider probe、激活、canonical learning turn 与重启恢复；历史成功记录不能替代当前证据。

该条款仅保留历史/兼容工程语义；不得据此把 Desktop 重新解释为当前 v1 Product Scope。

## 2. Migration Done Baseline

Database/state migration 只有在 migration 可执行、representative fixture backfill 正确、owner truth 明确、reconciliation test 通过、legacy write path 关闭或有关闭条件、rollback/forward-fix 明确时才算完成。

Migration DONE 只说明迁移合同完成，不自动证明用户可观察 Product Acceptance 已成立。

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

Engineering Gate PASS 只意味着系统按合同可靠执行；MUST NOT 宣称 Product Acceptance、adaptive learning outcome 或 human efficacy 已由此成立。

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

OPVE、G0/G1、synthetic learner MUST NOT 单独满足 Product Acceptance 或 Learning Evidence Gate；不能证明完整用户任务成立，也不能证明 human efficacy/retention/transfer/population superiority。

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

Issue / release MAY 另外声明：

```text
PRODUCT_ACCEPTANCE_PARTIAL
BLOCKED_BY_PRODUCT_DEFINITION_GAP
BLOCKED_BY_SPEC_GAP
```

但这些状态不得混淆 Engineering / Policy / Learning Evidence 三层 gate 的既有语义。

## 10. Acceptance Criteria

新增 v0.3 AC：

- `DOD-AC-201`：Engineering Gate 与 Policy Correctness Gate 可独立判定。
- `DOD-AC-202`：G0 < 100% 或 forbidden action > 0 时 Policy Gate 必失败。
- `DOD-AC-203`：answer-exposed/assisted success 后无 validation obligation 时 Policy Gate 必失败。
- `DOD-AC-204`：Engineering/Policy PASS 但学习证据不足时为 `LEARNING_EVIDENCE_INSUFFICIENT`。
- `DOD-AC-205`：process metrics 不可满足 primary Learning Evidence Gate。
- `DOD-AC-206`：synthetic learner/OPVE 不被当 human learning evidence。
- `DOD-AC-207`：release data foundation 区分 assignment probability/action propensity。
- `DOD-AC-208`：product-facing task 未建立 `CAP-* / PD-REQ-*` trace 时不得声称对应 Product Capability 已完成。
- `DOD-AC-209`：Vertical Slice / UI / Technical AC 不会被自动升级为 `PD-AC-*`。

## 11. Forbidden Completion / Release Claims

禁止：

- 关键 TODO/pass/NotImplemented 却声称 DONE；
- 只有 Mock 却声称真实模型可用；
- 测试未运行却说通过；
- 删除失败测试；
- 发现 Product Definition / Spec conflict 后未完成治理就隐式选方案；
- 新旧 truth 双写无 reconciliation/retirement；
- 仅 UI 正常但事件/证据/状态链未接通；
- Engineering Correct → Product Acceptance 已完成；
- Engineering Correct → 学习有效；
- Policy Correct → retention/transfer 已提升；
- Vertical Slice AC PASS → 新 Product Requirement / Product AC 已成立；
- synthetic learner → 真人效果；
- process metrics → primary reward；
- ambiguous propensity → causal experiment data；
- 隐藏 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 12. Final v0.3 Gate

当且仅当 Engineering Gate、Policy Correctness Gate 满足，release 所需学习证据状态被诚实标记、实验数据基础正确、无 blocking Product Definition / SPEC GAP 时，implementation MAY 进入相应 release/experimental stage。

如果 release 同时声称某个用户可观察 Product Feature 已完成，还必须单独核对适用 Product Acceptance。学习证据不足时 MAY 工程迭代，但 MUST 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 13. P1-06 Completion Gate

### DOD-300

P1-06 只有在 P1-02/P1-03/P1-07 真实依赖、对应 current implementation evidence、全量自动门禁、真实 provider/App restart、deep-link/recovery/accessibility 与无内部知识首次用户验收全部有当前证据后才可标 DONE。历史 EXEC 编号只作为证据引用，不作为实时状态源。

### DOD-301

Engineering、Security/Privacy、Product Acceptance / Product Usability 与 Learning Evidence 必须分开。Onboarding 完成、activity completion 或真实模型可用均不得把 Learning Evidence 从 `LEARNING_EVIDENCE_INSUFFICIENT` 改为有效。

## 14. Course Workspace Completion Gate

### DOD-320

Course Workspace implementation is not DONE until ADR-0023 / `CWSP-AC-001..012`、migration/rollback/forward-fix、contract/isolation/recovery tests、fresh SQLite upgrade/check、current full backend gates and real API evidence PASS。Frontend selected styling、mock list or default-only query cannot close the Platform gate。

### DOD-321

Course-centric frontend/route completion additionally requires live browser evidence for multi-Course create/switch/recovery、Activity resume/start、legacy route no-side-effect、responsive/accessibility/console。Engineering PASS must still report Product Acceptance、UX、Security、Quality and Learning Evidence separately。
