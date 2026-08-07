# Askora System Architecture Specification

> Spec ID 范围：`ARCH-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Goal

Askora MUST 以模块化单体优先实现个人长期学习闭环。未经新的 Canonical Design + ADR + Spec，MUST NOT 将八类系统拆成独立微服务或让 LLM/Agent 成为跨域超级 owner。

## 2. Top-level Principles

### ARCH-001 — Learning Loop, Not Chat-first

canonical 主链：

```text
LearningGoal / LearningPlan
→ LearningActivity
→ TeachingContext Snapshot
→ SYS05 TeachingAction
→ SYS02 EvidenceBundle
→ SYS08 Execution
→ SYS04 Attempt / AssessmentResult
→ SYS03 LearnerEvidence / LearnerState
→ SYS07 ReviewSchedule
→ SYS06 Replan when triggered
→ next TeachingContext
```

普通、流式、桌面请求 MUST 汇入同一 canonical teaching/orchestration boundary；direct chat/Socratic path MUST NOT 长期并存为第二生产主链。

### ARCH-002 — Decision vs Generation

LLM MAY 生成候选、讲解、worked example、hint、feedback、self-explanation prompt、language realization、tool execution；MUST NOT 成为 mastery、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule、knowledge publication 的 owner，也 MUST NOT override hard rules/exposure envelope。

### ARCH-003 — Single Writer

每类 canonical truth MUST 有唯一 owner。其他系统只可读取 exact-version snapshot、发送 command/event/evidence 或执行已决定动作；MUST NOT 跨系统直接 ORM 写入。

### ARCH-004 — Fact / Measurement / Inference / Decision / Execution / Outcome

以下语义 MUST 分开：

```text
Source fact
Measurement
Learner inference
Policy/planning decision
Execution
Later OutcomeObservation
```

DecisionTrace 与 OutcomeObservation MUST 分离；Outcome MUST NOT 回写历史 decision reasoning。

### ARCH-005 — Immutable History + Replayable Projection

关键事件、TeachingAction、TeachingContext、DecisionTrace、PolicyBundle refs 与 OutcomeObservation SHOULD immutable/versioned。状态更正通过 new version/supersede/reprojection；MUST NOT 静默覆盖历史。

### ARCH-006 — Local-first

当前阶段继续优先单用户、单设备、本地优先、SQLite 可运行、PostgreSQL 兼容；MUST NOT 为未来多租户提前强制微服务/2PC/复杂消息基础设施。

### ARCH-007 — Baseline Before Advanced Learning Algorithms

高级算法必须有透明 baseline。v0.3 Teaching Policy canonical runtime 是 ADR-0002 B3 constrained deterministic architecture；Contextual Bandit、Offline/Online RL、Deep KT canonical truth、autonomous multi-agent 均不在 v0.3 runtime scope。

## 3. Eight Systems & Ownership

### ARCH-020 — SYS01 Content & Knowledge

Owner：SourceDocument/MaterialRevision、KnowledgeUnit、Concept、PrerequisiteRelation、规范 Misconception definition。MUST NOT own mastery/action/plan/review/EvidenceBundle final selection。

### ARCH-021 — SYS02 Retrieval

Owner：EvidenceBundle、RetrievalTrace。读取 TeachingAction envelope 并 MAY 收紧 `answer_exposure`；MUST NOT 扩大或自行改变 TeachingAction。

### ARCH-022 — SYS03 Learner Model

Owner：LearnerEvidence acceptance、MasteryEstimate、LearnerState、MisconceptionHypothesis。TeachingStage MUST NOT 成为 SYS03 persistent truth。

### ARCH-023 — SYS04 Assessment

Owner：AssessmentItem、Attempt、AssessmentResult、MisconceptionEvidence、actual experienced assistance/exposure。`assessment_confidence != diagnostic_confidence`。

### ARCH-024 — SYS05 Teaching Policy

唯一 owner：TeachingAction；同时拥有 TeachingContext snapshot/evaluation semantics、TeachingStage derivation、PolicyBundle governance、independent validation obligation。

Canonical StrategyFamily 仅：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

SYS05 allowed envelope：

```text
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

`StrategyFamily != TeachingAction != InteractionMove`。Socratic/worked example/direct instruction/self-explanation/metacognition 属于 bounded move/modifier semantics；generic Productive Failure MUST NOT selectable。

### ARCH-025 — SYS06 Learning Planner

Owner：LearningGoal controlled version、LearningObjective、LearningActivity、LearningPlan、replan/day priority。MUST NOT 决定 hint/explanation 或 `next_due_at` truth。

### ARCH-026 — SYS07 Review Scheduler

Owner：ReviewSchedule、memory scheduling state、retrievability estimate、`next_due_at`。MUST NOT own daily plan、TeachingAction、mastery truth。

### ARCH-027 — SYS08 AI Orchestration & Trust

Owner：Session/Workflow execution state、ModelRoute/Inference、ToolCall/Result、PromptVersion、execution validation/telemetry。MAY 托管 LearningEvent/DecisionTrace/Outcome/Experiment ledger persistence，但 hosting MUST NOT 成为 payload/domain ownership。

SYS08 MAY tighten TeachingAction envelope；MUST NOT expand scaffold/hint/exposure/action semantics。

## 4. Canonical Policy Architecture

### ARCH-200

SYS05 B3 runtime MUST 实现：

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

Hard Constraint MUST NOT 被 soft score、LLM 或 experiment 恢复。

### ARCH-201

TeachingContext MUST exact-version/immutable，并显式处理 `AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE`；replay MUST NOT 读当前 mutable state 或重新调用在线 LLM。

### ARCH-202

Anti-oscillation MUST 覆盖 Material Evidence Gate、Sticky Continuity、Minimum Dwell by Evidence Opportunity、Hysteresis、Transition Priority、Repeated Failure Override。

### ARCH-203

PolicyBundle MUST immutable/versioned/atomic activate/exact pin/historical retain；MUST NOT 包含 executable DSL、embedded Python、free-form runtime policy code 或 LLM-generated rules。

### ARCH-204

B3 DecisionTrace probability semantics：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

ExperimentAssignment probability MUST 与 action propensity 分离。

## 5. Cross-system Data Flow

### ARCH-030 — Teaching Round

```text
SYS06 selects activity
→ SYS05 snapshots context + decides action
→ SYS02 builds evidence within envelope
→ SYS08 executes within/tighter envelope
→ SYS04 records actual experience + assessment
→ SYS03 accepts evidence / updates learner projection
→ SYS07 updates review when valid
→ SYS06 replans only on trigger
```

### ARCH-031 — No Synchronous Multi-owner Mutation

上述循环 MUST 通过 new events/versions/commands 形成；MUST NOT 在一个 transaction/call stack 直接修改多个 owner tables。

### ARCH-032 — Failure Return

SYS02/SYS08 MAY 返回 missing evidence、conflict、low confidence、model/tool failure、validation failure。若需改变 teaching semantics MUST 回到 SYS05 创建新 action。

## 6. Misconception & Validation Boundaries

### ARCH-210

```text
Misconception definition      → SYS01
MisconceptionEvidence         → SYS04
MisconceptionHypothesis       → SYS03
Remediation decision          → SYS05
```

### ARCH-211

ASSISTED/ANSWER_EXPOSED success → SYS05 `INDEPENDENT_VALIDATION_REQUIRED`。Obligation 不是 MasteryState；只有 fresh independent Attempt/result 才能提供满足它的事实。

## 7. Outcome / Experiment Architecture

### ARCH-220

TeachingEpisode、LearningTrajectory、OutcomeObservation、ExperimentAssignment 是 additive domain/analytics/experiment contracts，不建立第九个 state owner。

### ARCH-221

Delayed outcomes MUST NOT 自动 last-touch attribution；attribution 使用 ACTION_DIRECT / EPISODE_ASSOCIATED / TRAJECTORY_ASSOCIATED / EXPERIMENTALLY_CAUSAL / UNATTRIBUTABLE。

## 8. Target Module Layout

目标后端 SHOULD 逐步收敛：

```text
apps/backend/app/
├── domains/
│   ├── content_knowledge/
│   ├── retrieval/
│   ├── learner_model/
│   ├── assessment/
│   ├── teaching_policy/
│   ├── learning_planner/
│   └── review_scheduler/
├── orchestration/
├── ai/
├── contracts/
├── infrastructure/
├── api/
└── legacy/ or adapters/
```

不要求大爆炸重写；应通过后续 Vertical Slice/EXEC 渐进迁移。

## 9. Legacy Mapping Direction

### ARCH-230

- `services/documents/`：content/model/provenance → SYS01；retrieval/ranking → SYS02；
- `services/kt/`：SYS03 baseline candidate；
- `services/dkt/`：challenger only；
- `services/assessment/`：SYS04，MUST remove direct mastery write；
- `engines/socratic/strategy_selector.py` / state graph：MUST NOT final TeachingAction owner；MAY bounded move/provider/adapter；
- `engines/*_engine.py`：SYS08 execution adapters；
- dialog/session mastery fields：read-only projection during migration, never second truth。

### ARCH-231 — No Permanent Dual Truth

Old nine-family strategy、integer scaffold/hint/exposure、legacy Socratic selector、old policy config、ambiguous propensity MAY remain only as read/audit compatibility with retirement conditions。MUST NOT dual-write canonical truth。

## 10. Quality / Release Architecture

### ARCH-240

Testing MUST include L0～L6 + OPVE；G0 hard constraints MUST 100% pass、forbidden action=0；G1 selected action must belong to acceptable set。

### ARCH-241

Release MUST distinguish Engineering Gate、Policy Correctness Gate、Learning Evidence Gate。Engineering Correct/Policy Correct MUST NOT be claimed as learning efficacy。

Primary learning outcomes：no-hint independent success、delayed independent performance、independent transfer、unit-time capability gain。Engagement/turns/likes/hints/tokens/session duration are process diagnostics, not primary reward。

## 11. Architecture Acceptance Criteria

- `ARCH-AC-201`：八系统 single-writer ownership 无第二 truth。
- `ARCH-AC-202`：SYS05 only six StrategyFamily，four-layer ontology 可审计。
- `ARCH-AC-203`：SYS02/SYS08 only tighten action envelope。
- `ARCH-AC-204`：TeachingStage 不进入 LearnerState truth。
- `ARCH-AC-205`：Policy replay 无 online LLM/current mutable reads。
- `ARCH-AC-206`：Outcome/Experiment records 不形成第九 owner。
- `ARCH-AC-207`：legacy Socratic 无 final TeachingAction ownership。

## 12. Forbidden Architecture

禁止：

- 一个 TutorAgent 同时拥有八类决策；
- direct chat 与 canonical teaching 两条长期生产主链；
- SYS08/SYS02 扩大 action envelope；
- old strategy/support fields 继续 canonical 写入；
- TeachingStage 作为 persistent learner state；
- DecisionTrace 与 Outcome 混写；
- deterministic action_propensity=1.0；
- Contextual Bandit/RL/Deep KT 自动升级为 v0.3 canonical runtime；
- ledger hosting 等同 domain ownership；
- 为架构美观一次性大爆炸重写。