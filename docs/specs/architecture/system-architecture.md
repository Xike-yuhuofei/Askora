# Askora System Architecture Specification

> Spec ID 范围：`ARCH-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Goal

Askora MUST 以模块化单体优先实现个人长期学习闭环。未经新的 Canonical Design + ADR + Spec，MUST NOT 将八类系统拆成独立微服务或让 LLM/Agent 成为跨域超级 owner。

## 2. Existing Top-level Principles Retained

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

LLM MAY 生成候选、讲解、worked example、hint、feedback、self-explanation prompt、language realization、tool execution；MUST NOT 成为 mastery、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule、knowledge publication owner，也 MUST NOT override hard rules/exposure envelope。

### ARCH-003 — Single Writer

每类 canonical truth MUST 有唯一 owner。其他系统只可读取 exact-version snapshot、发送 command/event/evidence 或执行已决定动作；MUST NOT 跨系统直接 ORM 写入。

### ARCH-004 — Fact / Measurement / Inference / Decision / Execution / Outcome

Source fact、Measurement、Learner inference、Policy/planning decision、Execution MUST 分层；v0.3 进一步要求 Later OutcomeObservation 与 DecisionTrace 分离，Outcome MUST NOT 回写历史 reasoning。

### ARCH-005 — Immutable History + Replayable Projection

关键 event、TeachingAction、TeachingContext、DecisionTrace、PolicyBundle refs 与 OutcomeObservation SHOULD immutable/versioned。状态更正通过 new version/supersede/reprojection；MUST NOT 静默覆盖历史。

### ARCH-006 — Local-first

当前阶段继续优先单用户、单设备、本地优先、SQLite 可运行、PostgreSQL 兼容；MUST NOT 为未来多租户提前强制微服务/2PC/复杂消息基础设施。

### ARCH-007 — Baseline Before Advanced Algorithms

高级算法必须有透明 baseline。v0.3 Teaching Policy canonical runtime 是 ADR-0002 B3 constrained deterministic architecture；Contextual Bandit、Offline/Online RL、Deep KT canonical truth、autonomous multi-agent 均不在 v0.3 runtime scope。

## 3. v0.3 Eight Systems & Ownership

> v0.3 新增 ownership requirements 使用 `ARCH-3xx`，避免复用旧 requirement ID。

### ARCH-300 — SYS01 Content & Knowledge

Owner：SourceDocument/MaterialRevision、KnowledgeUnit、Concept、PrerequisiteRelation、Misconception definition。MUST NOT own mastery/action/plan/review/EvidenceBundle final selection。

### ARCH-301 — SYS02 Retrieval

Owner：EvidenceBundle、RetrievalTrace。读取 TeachingAction envelope 并 MAY 收紧 `answer_exposure`；MUST NOT 扩大或自行改变 TeachingAction。

### ARCH-302 — SYS03 Learner Model

Owner：LearnerEvidence acceptance、MasteryEstimate、LearnerState、MisconceptionHypothesis。TeachingStage MUST NOT 成为 SYS03 persistent truth。

### ARCH-303 — SYS04 Assessment

Owner：AssessmentItem、Attempt、AssessmentResult、MisconceptionEvidence、actual assistance/exposure。`assessment_confidence != diagnostic_confidence`。

### ARCH-304 — SYS05 Teaching Policy

唯一 owner：TeachingAction；同时负责 TeachingContext snapshot/evaluation semantics、TeachingStage derivation、PolicyBundle governance、independent validation obligation。

Canonical StrategyFamily 仅：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

Allowed envelope：

```text
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

`StrategyFamily != TeachingAction != InteractionMove`。Socratic/worked example/direct instruction/self-explanation/metacognition 属 bounded move/modifier；generic Productive Failure MUST NOT selectable。

### ARCH-305 — SYS06 Learning Planner

Owner：LearningGoal controlled version、LearningObjective、LearningActivity、LearningPlan、replan/day priority。MUST NOT 决定 hint/explanation 或 `next_due_at` truth。

### ARCH-306 — SYS07 Review Scheduler

Owner：ReviewSchedule、memory scheduling state、retrievability estimate、`next_due_at`。MUST NOT own daily plan、TeachingAction、mastery truth。

### ARCH-307 — SYS08 AI Orchestration & Trust

Owner：Session/Workflow execution state、ModelRoute/Inference、ToolCall/Result、PromptVersion、execution validation/telemetry。MAY host LearningEvent/DecisionTrace/Outcome/Experiment ledger persistence，但 hosting MUST NOT 成为 payload/domain ownership。SYS08 MAY tighten action envelope；MUST NOT expand semantics。

## 4. v0.3 Canonical Policy Architecture

### ARCH-320

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

Hard Constraint MUST NOT 被 soft score、LLM、experiment 恢复。

### ARCH-321

TeachingContext MUST exact-version/immutable，并显式处理 `AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE`；replay MUST NOT 读当前 mutable state 或重新调用在线 LLM。

### ARCH-322

Anti-oscillation MUST 覆盖 Material Evidence Gate、Sticky Continuity、Minimum Dwell by Evidence Opportunity、Hysteresis、Transition Priority、Repeated Failure Override。

### ARCH-323

PolicyBundle MUST immutable/versioned/atomic activate/exact pin/historical retain；MUST NOT 包含 executable DSL、embedded Python、free-form runtime policy code 或 LLM-generated rules。

### ARCH-324

B3 trace MUST 写 `behavior_policy_type=DETERMINISTIC`、`action_propensity=null`；ExperimentAssignment probability MUST 与 action propensity 分离。

## 5. Existing Cross-system Data Flow Retained

### ARCH-020 — Standard Teaching Round

```text
SYS06 selects LearningActivity
→ SYS05 snapshots TeachingContext + creates TeachingAction
→ SYS02 creates EvidenceBundle if required
→ SYS08 executes within/tighter envelope
→ SYS04 records Attempt / AssessmentResult / actual assistance
→ SYS03 updates learner projection from accepted evidence
→ SYS07 updates ReviewSchedule from valid retrieval evidence
→ SYS06 replans only on trigger
```

### ARCH-021 — No Synchronous Multi-owner Mutation

循环 MUST 通过 new events/versions/commands 形成；MUST NOT 在一个 transaction/call stack 直接修改多个 owner tables。

### ARCH-022 — Failure Return

SYS02/SYS08 MAY 返回 missing evidence、conflict、low confidence、model/tool unavailable、validation failure；MUST NOT 自行改变 TeachingAction semantics。需要改变教学策略时 MUST 回 SYS05 创建新 action。

## 6. Existing Legacy Architecture Governance Retained

### ARCH-030 — Legacy Freeze

对应 migration 完成前，legacy 模块 MAY 修复，但 MUST NOT 继续向错误边界增加长期 state ownership。

### ARCH-031 — No Dual Truth Source

状态迁移后，旧路径 MUST 进入 read-only/adapter/removal 阶段；MUST NOT 新旧两套 truth 持续 dual-write 且无 reconciliation/retirement contract。

## 7. v0.3 Misconception / Validation Boundaries

### ARCH-330

`Misconception definition → SYS01`；`MisconceptionEvidence → SYS04`；`MisconceptionHypothesis → SYS03`；`Remediation decision → SYS05`。

### ARCH-331

ASSISTED/ANSWER_EXPOSED success → SYS05 `INDEPENDENT_VALIDATION_REQUIRED`。Obligation 不是 MasteryState；只有 fresh independent Attempt/result 才能提供满足事实。

## 8. v0.3 Outcome / Experiment Architecture

### ARCH-340

TeachingEpisode、LearningTrajectory、OutcomeObservation、ExperimentAssignment 是 additive domain/analytics/experiment contracts，不建立第九 state owner。

### ARCH-341

Delayed outcome MUST NOT 自动 last-touch；attribution 使用 ACTION_DIRECT / EPISODE_ASSOCIATED / TRAJECTORY_ASSOCIATED / EXPERIMENTALLY_CAUSAL / UNATTRIBUTABLE。

## 9. Target Module Layout

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

不要求大爆炸重写；后续 Vertical Slice/EXEC 渐进迁移。

## 10. v0.3 Legacy Mapping Direction

### ARCH-350

`services/documents/` → SYS01+SYS02；`services/kt/` → SYS03 baseline；`services/dkt/` → challenger；`services/assessment/` → SYS04；legacy Socratic selector/state graph → bounded provider/adapter but not final owner；`engines/*_engine.py` → SYS08 execution adapters；dialog/session mastery → read-only migration projection。

### ARCH-351 — No Permanent Dual Truth

Old nine-family strategy、integer scaffold/hint/exposure、legacy Socratic selector、old policy config、ambiguous propensity MAY only read/audit compatibility with retirement conditions；MUST NOT dual-write canonical truth。

## 11. v0.3 Quality / Release Architecture

### ARCH-360

Testing MUST include L0～L6 + OPVE；G0 hard constraints MUST 100% pass、forbidden action=0；G1 selected action MUST belong to acceptable set。

### ARCH-361

Release MUST distinguish Engineering Gate、Policy Correctness Gate、Learning Evidence Gate。Engineering/Policy Correct MUST NOT be claimed learning efficacy。Primary learning outcomes：no-hint independent success、delayed independent performance、independent transfer、unit-time capability gain；engagement/turns/likes/hints/tokens/session duration 仅 process diagnostics。

## 12. Acceptance Criteria

原有 AC 保留并按 v0.3 contract 解释：

- `ARCH-AC-001`：任一核心业务 state 可指出唯一 owner，且不存在无合同第二 writer。
- `ARCH-AC-002`：普通/流式教学请求经过同一 canonical orchestrator 主链。
- `ARCH-AC-003`：AssessmentResult 不直接等于 MasteryEstimate，存在 explicit evidence → learner model boundary。
- `ARCH-AC-004`：TeachingAction 与 LearningPlan 分离，SYS05 不重排长期目标。
- `ARCH-AC-005`：ReviewSchedule 与 LearnerState 分离，Planner 不重复计算 forgetting model。
- `ARCH-AC-006`：LLM/Agent 无直接写 SYS01/SYS03/SYS04/SYS05/SYS06/SYS07 canonical state 通道。
- `ARCH-AC-007`：关键 decisions/model calls 可用 version + trace id 追踪。
- `ARCH-AC-008`：固定 projection/algorithm 的 event replay 不依赖在线 LLM。

新增 v0.3 AC：

- `ARCH-AC-201`：八系统 single-writer ownership 无第二 truth。
- `ARCH-AC-202`：SYS05 only six StrategyFamily，four-layer ontology 可审计。
- `ARCH-AC-203`：SYS02/SYS08 only tighten action envelope。
- `ARCH-AC-204`：TeachingStage 不进入 LearnerState truth。
- `ARCH-AC-205`：Policy replay 无 online LLM/current mutable reads。
- `ARCH-AC-206`：Outcome/Experiment records 不形成第九 owner。
- `ARCH-AC-207`：legacy Socratic 无 final TeachingAction ownership。

## 13. Spec-ID Governance

`ARCH-001..007`、`ARCH-020..022`、`ARCH-030/031`、`ARCH-AC-001..008` 保留既有职责；v0.3 新 ontology/policy/outcome/migration/quality requirements 使用 `ARCH-300+`。MUST NOT 复用旧 ID 改变原义。

## 14. Forbidden Architecture

禁止：TutorAgent 同时拥有八类决策；direct chat 与 canonical teaching 两条默认主链；cross-owner writes；SYS08/SYS02 envelope expansion；old strategy/support fields canonical writing；TeachingStage persistent learner truth；DecisionTrace/Outcome 混写；deterministic `action_propensity=1.0`；Contextual Bandit/RL/Deep KT 自动成为 v0.3 canonical runtime；ledger hosting = domain ownership；为架构美观大爆炸重写。