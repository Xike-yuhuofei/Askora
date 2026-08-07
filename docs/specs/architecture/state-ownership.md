# State Ownership

> Spec ID：`STATE-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Single-writer Principle

### STATE-001

每类 canonical domain truth MUST 有且只有一个写 owner。其他系统 MAY 读取、缓存、投影或托管 ledger，但 MUST NOT 形成可独立演进的第二事实源。

## 2. Eight-system Ownership Matrix

| Canonical truth / decision | Owner | Other systems may |
|---|---|---|
| Knowledge truth / relations / Misconception definition | SYS01 | read / retrieve / reference |
| EvidenceBundle / RetrievalTrace | SYS02 | consume |
| LearnerEvidence acceptance / MasteryEstimate / LearnerState / MisconceptionHypothesis | SYS03 | read |
| AssessmentItem / Attempt / AssessmentResult / MisconceptionEvidence / actual assistance | SYS04 | consume |
| TeachingAction / TeachingContext decision snapshot semantics / TeachingStage derivation / PolicyBundle governance / validation obligation | SYS05 | execute/read |
| LearningGoal / Objective / LearningActivity / LearningPlan | SYS06 | read |
| ReviewSchedule / next_due | SYS07 | read / plan from |
| WorkflowRun / ModelInference / Tool execution / execution validation | SYS08 | execute / host ledgers |

### STATE-002

固定边界：

```text
AssessmentResult != MasteryEstimate
LearningPlan != TeachingAction
ReviewSchedule != LearnerState
MisconceptionEvidence != MisconceptionHypothesis
TeachingStage != LearnerState
StrategyFamily != TeachingAction
TeachingAction != InteractionMove
DecisionTrace != OutcomeObservation
Experiment assignment probability != action selection propensity
```

## 3. v0.3 Non-state / Derived Objects

### STATE-200 — TeachingContext

TeachingContext 是 SYS05 的 immutable decision-input snapshot。它引用 exact owner versions，但 MUST NOT 成为第二 LearnerState/AssessmentResult/Plan truth。Snapshot retention 是 replay/audit 需求，不改变 source ownership。

### STATE-201 — TeachingStage

TeachingStage 由 SYS05 以 `TeachingContext + PolicyBundle` 派生，只在 policy-control 语义中存在。MUST NOT 持久化为 SYS03 learner stage truth。

### STATE-202 — PolicyBundle

PolicyBundle 是 SYS05 的 immutable/versioned policy configuration artifact；它不是 LearnerState，也不是 experiment result。Activation 只影响新 TeachingAction。

### STATE-203 — Independent Validation Obligation

Validation obligation 属于 SYS05 policy-control semantics。SYS04 产生可满足它的 fresh Attempt/AssessmentResult；SYS03 仅消费 evidence，不拥有/预先完成 obligation。

## 4. Outcome / Experiment Additive Contracts

### STATE-210 — OutcomeObservation

OutcomeObservation 是 immutable measurement/analytics record。其 measurement truth 必须引用既有 owner 的事实（例如 SYS04 result、SYS03 estimate），MUST NOT 替代这些 owner 的 canonical state。

### STATE-211 — ExperimentAssignment

ExperimentAssignment 是 experiment control/analytics record。它 MAY 被 durable ledger 托管并被 SYS05 只读消费，但 MUST NOT 成为第二 TeachingAction owner 或第二 LearnerState truth。

### STATE-212 — Ledger Hosting

SYS08 MAY 托管 LearningEvent、DecisionTrace、OutcomeObservation、ExperimentAssignment 的 durable persistence/outbox。托管权 = storage/transport responsibility，MUST NOT 被实现为修改领域 payload 语义的 ownership。

## 5. LLM / Agent Boundary

### STATE-220

LLM/Agent MAY 生成 explanation、worked example、hint、diagnostic candidate、feedback、self-explanation prompt、language realization、tool result。

LLM/Agent MUST NOT 成为：LearnerState owner、Assessment truth owner、TeachingAction owner、LearningPlan owner、ReviewSchedule owner、hard-rule override、answer-exposure override。

### STATE-221

SYS08 MAY 收紧 TeachingAction envelope；MUST NOT 扩大 scaffold、hint specificity、answer exposure 或 action semantics。

## 6. Misconception Ownership

### STATE-230

```text
Misconception definition      → SYS01
MisconceptionEvidence         → SYS04
MisconceptionHypothesis       → SYS03
Remediation decision          → SYS05
```

任一 shortcut 将 definition/evidence/hypothesis/remediation 合并为一个跨系统可写对象均禁止。

## 7. Write-path Rules

### STATE-010

跨 owner 写入 MUST 通过 owner command/application service 或 accepted event/evidence path；禁止跨模块直接 ORM UPDATE 他人 canonical table。

### STATE-011

Projection/cache MUST 标明 source owner/version，并可删除重建。Cache 不得在 source unavailable 时被自动升级为 truth。

### STATE-012

状态更新与关键 outbox/event 应满足对应 persistence transaction contract；失败必须可见，不得产生“业务已成功但审计链丢失”的静默分叉。

## 8. State Ownership Sweep Requirements

### STATE-240

每次新增公共对象必须回答：

1. 是否是真实领域 state、derived decision artifact、measurement record 或 ledger record；
2. 谁可写；
3. 谁只读/执行；
4. 是否可能复制现有 truth；
5. replay 时使用哪一个 exact version。

### STATE-241

v0.3 implementation MUST 通过 architecture tests 证明不存在：第二 LearnerState、第二 TeachingAction、第二 Experiment truth、第二 Outcome truth。

## 9. Legacy Compatibility

### STATE-250

legacy `DialogSession.mastery_estimate`、Socratic selector/state graph、old policy config、integer support/exposure MAY 暂留为 read projection/adapter/audit source，但 MUST 有 canonical source 与 retirement condition；MUST NOT 与 v0.3 fields 双写并独立演进。

## 10. Tests

必须覆盖：cross-owner write prohibition；TeachingContext/TeachingStage 非第二 state；SYS08 tightening-only；Misconception four-way boundary；Outcome/Experiment ledger hosting 不等于 truth ownership；legacy adapter no write；replay uses exact owner version。

## 11. Acceptance Criteria

- `STATE-AC-201`：SYS01～SYS08 每类 canonical truth 只有一个 writer。
- `STATE-AC-202`：TeachingContext/TeachingStage 不形成第二 LearnerState。
- `STATE-AC-203`：validation obligation 由 SYS05 控制，SYS03 不能无 fresh Attempt 完成。
- `STATE-AC-204`：OutcomeObservation/ExperimentAssignment 的托管记录不覆盖八系统 domain truth。
- `STATE-AC-205`：LLM/SYS08/legacy Socratic 无 final TeachingAction ownership。

## 12. Forbidden Implementations

禁止：跨系统直接写 canonical tables；聊天/session shared context 写 mastery；SYS04 写 mastery；SYS05 写 plan/review；SYS08 因模型输出改 action；TeachingStage 进入 LearnerState truth；analytics table 反向成为 outcome/experiment 的独立业务 truth；legacy 和 v0.3 双写。