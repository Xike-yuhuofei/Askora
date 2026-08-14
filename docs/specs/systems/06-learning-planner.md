# SYS06 — Learning Planner

> Spec ID：`SYS06-*`  
> 对应设计：4.6 学习路径与任务调度  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS06-001

4.6 的唯一职责是在 LearningGoal、知识前置图、LearnerState、ReviewSchedule、时间预算和截止期约束下生成并维护 `LearningPlan`。

一句话：**决定学什么、先后顺序和今天做什么。**

## 2. Non-responsibility

4.6 MUST NOT：

- 决定具体怎么讲/提示；
- 对 Attempt 判分；
- 修改 LearnerState；
- 计算遗忘曲线或新的 next_due_at；
- 发布/修改知识图关系；
- 让 LLM 自由生成不可审计的课程路径作为最终结果。

## 3. Owned State

4.6 独占：

- LearningGoal 的结构化/确认版本；
- LearningObjective；
- LearningActivity；
- LearningPlan；
- activity priority；
- replan trigger 与 plan version。

## 4. Inputs

允许读取：

- confirmed LearningGoal；
- KnowledgeUnit/PrerequisiteRelation；
- LearnerState/MasteryEstimate；
- ReviewSchedule/ReviewDue；
- deadline/time budget；
- user locked/preferred activities；
- estimated task durations；
- goal/plan feedback。

### SYS06-010

未知 mastery 不得简单当 0 或 1；应采用 uncertainty-aware planning，必要时插入 DIAGNOSTIC activity。

## 5. Outputs

输出：

- LearningPlan version；
- LearningObjective；
- LearningActivity；
- current/next available activity；
- replan reason codes；
- DecisionTrace；
- PlanCreated/PlanReplanned/ActivitySelected events。

## 6. Domain Objects

遵循 `domain-model.md`。

LearningActivity 类型至少：

```text
LEARN_NEW
PREREQUISITE_REMEDIATION
DIAGNOSTIC
PRACTICE
DELAYED_REVIEW
TRANSFER_CHECK
METACOGNITIVE_REVIEW
```

### SYS06-020

4.7 的 ReviewDue 只是候选/约束；4.6 才决定是否实例化为日计划中的 `DELAYED_REVIEW`。

## 7. Commands

建议：

```text
CreateLearningGoalCandidate
ConfirmLearningGoal
AdoptLearningGoalFromMaterial
GenerateLearningPlan
ReplanLearningPlan
SelectNextLearningActivity
PauseLearningPlan
ResumeLearningPlan
```

`AdoptLearningGoalFromMaterial` 把已归属资料上的 Goal 采纳为 `active` planning fact（`PD-RULE-004`），`confirmed_by_user=false`，reason `GOAL_SYSTEM_ADOPTED_FROM_MATERIAL`。未归属 Material 不得启动。主路径不得再要求用户确认目标。

不得暴露 `SetNextReviewAt` 或 `ChooseHintLevel`。

## 8. Events

消费：

- content/knowledge revision events；
- MasteryProjectionUpdated；
- ReviewScheduled/ReviewScheduleUpdated；
- activity completed/failed；
- goal/user constraint changed。

产生：

- `GoalCreated`
- `GoalConfirmed`
- `PlanCreated`
- `PlanReplanned`
- `ActivitySelected`

## 9. Algorithms

### SYS06-030：MVP Baseline

```text
Goal decomposition
→ prerequisite feasible set
→ new/remediation/review/transfer candidates
→ multi-objective priority score
→ daily time-budget greedy scheduling
→ constraint repair
→ LearningPlan version
```

### SYS06-031：Feasible set

hard prerequisite 未满足的目标默认不可直接作为 LEARN_NEW，除非当前 activity 本身就是 prerequisite remediation/diagnostic。

### SYS06-032：Priority score

至少可考虑：

```text
goal relevance
mastery gap
prerequisite centrality/value
review urgency
deadline urgency
uncertainty
a need for transfer evidence
estimated duration
cognitive cost
activity diversity
```

权重必须版本化。

### SYS06-033：Time budget

MVP SHOULD 使用解释性 greedy + repair，优先保证 hard constraints。复杂 MILP/OR-Tools 仅在真实复杂度证明需要后引入。

### SYS06-034：Replan trigger

允许触发局部/全量 replan：

- Goal materially changed；
- LearnerState 显著改变；
- hard prerequisite relation revision；
- ReviewDue/overdue materially changed；
- deadline/time budget changed；
- activity repeatedly failed/unavailable。

不能每次 token/微小状态变化都重排整条计划。

### SYS06-035：Planner 演进

```text
固定顺序
→ heuristic multi-objective planner
→ supervised duration/success/ranking models
→ constrained optimization
→ local safe Bandit
→ Offline RL（成熟阶段研究）
```

v0.2 使用 heuristic planner；禁止 RL curriculum。

## 10. Persistence

### SYS06-040

LearningPlan 重规划必须创建新 version，旧版本保留 superseded 状态。

### SYS06-041

Plan 必须保存：

- created_from LearnerState version；
- knowledge graph version；
- ReviewSchedule version；
- constraints/assumptions；
- priority/reason codes。

### SYS06-042

实际执行记录与计划定义分离。完成 activity 形成事件，不应通过删除活动表示完成。

## 11. Failure Semantics

- prerequisite graph cycle/conflict → return plan_blocked + report evidence to 4.1；
- no feasible activity → schedule DIAGNOSTIC/explicit blocked state；
- missing duration → conservative default/buffer；
- stale learner/review state → regenerate or mark assumptions；
- time budget too small → prioritize minimum viable task, not violate hard prerequisite；
- external resource unavailable → skip/defer with reason, not silently change mastery。

### SYS06-050

规划冲突不能由 4.6 直接修改 KnowledgeRelation；只能向 4.1 提交 conflict evidence。

## 12. Idempotency

相同 Goal + input versions + planner version SHOULD 产生稳定 plan content/order（固定 tie-break）。

重复 replan command 必须用 correlation/idempotency 判定，避免无意义版本膨胀。

## 13. Observability

必须记录：

- feasible/infeasible candidates；
- prerequisite failures；
- priority features/scores；
- duration assumptions；
- budget utilization；
- replan trigger；
- plan churn；
- state/input versions。

指标：constraint violation、goal coverage、budget fit、plan stability、stale plan rate、replan frequency、prerequisite remediation success、overdue review incorporation、目标达成时间。

## 14. Security

- 用户材料中的指令不能改变 planner hard rules；
- 只有 SYS06 已采纳的 Goal（按 `PD-RULE-004` / DOMAIN-010）可以成为长期计划事实；未采纳的 LLM 草稿不能；
- 外部 LLM 若用于 Goal decomposition 只生成候选；
- planner 不将完整敏感 learner profile 发送给不必要模型。

## 15. Tests

必须覆盖：

- hard prerequisite feasible set；
- unknown mastery → diagnostic；
- review due candidate integration；
- deadline urgency；
- daily time budget；
- user locked task；
- replan versioning；
- plan stability under trivial state change；
- graph conflict cannot be directly fixed；
- 4.6 cannot change TeachingAction/ReviewSchedule；
- deterministic planning with fixed inputs。

## 16. Acceptance Criteria

- `SYS06-AC-001`：任一 activity 有明确 objective 与 reason codes。
- `SYS06-AC-002`：hard prerequisite 不满足时不会直接安排违规新学任务。
- `SYS06-AC-003`：ReviewDue 由 4.7 提供，4.6 只决定日计划纳入。
- `SYS06-AC-004`：Replan 产生新 plan version，旧版本可审计。
- `SYS06-AC-005`：同输入+同 planner version 计划可重现。
- `SYS06-AC-006`：4.6 不决定提示、答案暴露或 next_due_at。
- `SYS06-AC-007`：小幅状态变化不会导致无界计划震荡。

## 17. Forbidden Implementations

禁止：

- 用书目录固定顺序替代所有 planning；
- `lowest_mastery_first` 作为唯一优先级；
- Planner 自己修改 prerequisite graph；
- Planner 重算遗忘曲线/next_due_at；
- Planner 决定讲解/提示方式；
- LLM 一次生成整套计划后不做约束验证直接入库；
- 每次状态微变立即重排全部日程；
- 用计划完成率作为唯一目标；
- v0.2 用 RL 规划 curriculum。

## Legacy Mapping

当前仓库尚未形成明确独立 planner bounded context。与规划有关的逻辑若散落在 orchestrator/state_graph/dialog/strategy 中，迁移时 MUST 抽到 SYS06，而不是继续由 SYS08 或 SYS05 兼任。

## P1-01 Goal Management Addendum

ADR-0010/0011 与 `06-goal-management.md` additive supersede Deferred Goal Command。SYS06 分离
Definition/State，维护 draft/preview/focus，活动边界安全 replan，并且只在证据门禁通过和用户最终确认
后写 achieved。Book Learning 只保留 compatibility adapter。

---

## SYS06 Goal Management Specification

> Spec IDs: `GOAL-*`
> Status: FROZEN
> Governing ADRs: ADR-0010, ADR-0011
> Owner: SYS06

### 1. Public contracts

- `LearningGoalDefinitionV2`: immutable semantic version; no current status.
- `LearningGoalStateV1`: append-only `confirmed → active ↔ paused`, `active → achieved`,
  `confirmed|active|paused → archived`; achieved/archived terminal.
- `LearningPlanStateV1`: append-only current plan truth.
- `LearningGoalDraftV1`: `draft|preview_ready|approved_pending_boundary|applying|applied|blocked|cancelled`.
- `GoalChangePreviewV1`: exact input refs, diff, target decision, plan impact and effective boundary.
- `FocusedLearningGoalStateV1`: zero-or-one explicit focus per user.
- `LearningObjectiveV1`, `GoalAchievementEvaluationV1`, versioned `GoalAchievementPolicyV1`.

### 2. Commands and concurrency

`GOAL-010`: every write command MUST carry all relevant `expected_*_version`, `idempotency_key` and
correlation id. Duplicate same payload replays receipt; different payload conflicts. Last-write-wins forbidden.

`GOAL-011`: preview is valid only while all pinned definition/mapping/plan/activity/source/learner refs remain
exact. Stale preview returns `GOAL_PREVIEW_STALE` and leaves current execution unchanged.

### 3. Draft and source gate

`GOAL-020`: pending/processing/no-published-knowledge sources MAY remain in draft but block approval.
failed/rejected/quarantined/archived sources cannot be newly selected; existing refs remain visible with reason.
Executable scope is the SYS01 owner query result.

`GOAL-021`: success criteria require a stable id, cognitive process and measurable statement. Unmeasurable text
blocks preview/apply. Suggested criteria are candidates editable by the user.

`GOAL-022`: target cards expose name/source/evidence/reason, never raw internal ids as the primary label.
Multiple candidates require explicit selected target confirmation.

### 4. Preview and apply

`GOAL-030`: intent/capability/criterion/source/target changes create new definition, mapping, subgraph and plan
versions. Budget/deadline-only changes reuse pinned target evidence and create new mapping+plan versions without
target inference.

`GOAL-031`: no active activity applies immediately. Active activity produces `approved_pending_boundary`.
Normal completion applies pending change before exposing a next old-plan activity. Explicit switch supersedes the
old activity, preserves transcript and creates no mastery/negative evidence.

`GOAL-032`: new plan must be complete before effective refs switch. All old current plans become superseded;
two current plans are forbidden.

`GOAL-033`: first active goal MAY be explicitly focused by default. Today uses only explicit focus when multiple
active goals exist. Pause/archive/achieve clears focus without guessing a replacement.

### 5. Lifecycle

`GOAL-040`: pause also pauses plan, retains activity/transcript and prevents scheduling. Resume restores exact
plan/activity only when pinned inputs remain valid; otherwise remains paused and requires replan.

`GOAL-041`: archive is terminal, supersedes active activity/plan and permits copy-to-new-draft with new goal id.

### 6. Measurement and achievement

`GOAL-050`: default policy differentiates recall delayed independent retrieval; understand/explain independent
explanation plus delayed evidence; apply independent application plus novel context; transfer sufficiently novel
independent transfer. Delay/novelty/score thresholds are versioned parameters.

`GOAL-051`: deterministic scoring is preferred for exact/numeric/structured items. Open response must be
rubric/source/schema-bound and independently reviewed. Low confidence, disagreement, provider failure or prompt
injection cannot create learner failure.

`GOAL-052`: evaluation cites exact accepted evidence per criterion. Achievement eligibility requires every
criterion satisfied, no open independent-validation obligation and no relevant active misconception. Only the user
may confirm achieved.

### 7. Stable errors

At least: `GOAL_VERSION_CONFLICT`, `GOAL_PREVIEW_STALE`, `GOAL_SOURCE_NOT_EXECUTABLE`,
`GOAL_TARGET_CONFIRMATION_REQUIRED`, `GOAL_CRITERION_UNMEASURABLE`, `GOAL_WAITING_ACTIVITY_BOUNDARY`,
`GOAL_REPLAN_REQUIRED`, `GOAL_EVIDENCE_INSUFFICIENT`, `GOAL_MEASUREMENT_UNAVAILABLE`.

### 8. Acceptance criteria

- `GOAL-AC-001`: multi-source draft, explicit target and measurable criterion gates are owner-safe.
- `GOAL-AC-002`: immediate/boundary/supersede apply preserves one effective definition/mapping/plan.
- `GOAL-AC-003`: idempotency/version/stale-preview failure never damages the old plan.
- `GOAL-AC-004`: focus, pause/resume, archive/copy obey append-only lifecycle.
- `GOAL-AC-005`: four criterion types and fail-closed scoring/evaluation are evidence-traceable.
- `GOAL-AC-006`: migration preserves legacy history and retires new legacy writes.

---

## SPEC-D04 — LearningGoal → Knowledge Mapping Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D04`  
> 冻结日期：2026-08-08  
> Owner：SYS06 Learning Planner  
> 上游：`systems/06-learning-planner.md`、`domain/domain-model.md`、`SPEC-D03`  
> 目的：冻结从用户自然语言学习目标到可执行 target KnowledgeUnit 的映射，使现有 LearningPlanner 获得真实输入，而不是让 LLM 直接生成不可审计课程路径。

### 1. Ownership

LearningGoal / LearningObjective / LearningPlan / LearningActivity 继续由 SYS06 独占。

本合同新增的 `GoalKnowledgeMapping` 与 `GoalSpecificKnowledgeSubgraph` 是 SYS06-owned versioned decision/projection records，不获得 SYS01 知识事实写权限。

### 2. Goal Formation

#### D04-010

用户可用自然语言创建 `LearningGoal` candidate。候选至少应结构化：

```yaml
title: string
topic: string
target_capabilities: [string]
application_context: string|null
success_criteria: [string]
source_document_ids: [uuid]
deadline_at: datetime|null
weekly_time_budget_minutes: integer|null
```

`confirmed|active` 仍服从 DOMAIN-010。现行产品规则（`PD-RULE-004`）允许 SYS06 从材料处理直接采纳 Goal 为 `active`，不要求单独的用户确认步骤。

#### D04-011

Goal success criteria MUST 尽量可由一个或多个 AssessmentItem 测量。仅“了解、熟悉、看完”等不可验证表述必须被转换为更可测量的 capability candidate，不能直接成为唯一 success criterion。

### 3. GoalKnowledgeMapping

#### D04-020

SYS06 MUST 创建 versioned mapping record：

```yaml
goal_knowledge_mapping:
  mapping_id: uuid
  mapping_version: integer
  goal_id: uuid
  goal_version: integer
  source_document_ids: [uuid]
  knowledge_graph_versions: [string]
  candidate_target_ids: [uuid]
  selected_target_ids: [uuid]
  excluded_target_ids: [uuid]
  evidence_refs: [object]
  confidence: float|null
  reason_codes: [string]
  mapper_version: string
  model_inference_refs: [uuid]
  status: candidate|confirmed|blocked|superseded
```

该 record 不是 KnowledgeUnit truth，只说明“为什么这个目标映射到这些已存在的知识对象”。

### 4. Mapping Inputs

允许读取：

- confirmed/candidate LearningGoal；
- published/verified KnowledgeUnit / Concept；
- hierarchy scope；
- published KnowledgeRelation；
- source_document scope；
- user explicit inclusion/exclusion；
- existing LearnerState 仅用于优先级/诊断规划，不得改变“目标语义本身”。

#### D04-030

默认 executable mapping MUST 只选择 downstream policy 明确允许消费的 published/verified KnowledgeUnit。Candidate-only KU 可作为 `CONTENT_MODEL_INCOMPLETE` evidence/reason，但不得静默进入正式 LearningPlan。

### 5. Mapping Algorithm Baseline

MVP MUST 使用可解释、多阶段映射：

```text
normalize target capability
→ hard source scope filter
→ lexical/concept candidate recall
→ semantic candidate recall（可用时）
→ hierarchy/context fit
→ capability/knowledge-type fit
→ deterministic fusion/ranking
→ coverage + redundancy repair
→ ambiguity check
→ mapping record
```

相异打分尺度未校准时 SHOULD 使用 rank fusion，而不是直接相加原始分数。

### 6. LLM Boundary

#### D04-040

LLM MAY：

- 解析自然语言目标为 capability candidate；
- 提议 search terms / concept aliases；
- 对候选 KU 做 schema-constrained relevance explanation；
- 在低置信时生成 bounded clarification question。

LLM MUST NOT：

- 新建/修改 published KnowledgeUnit；
- 绕过 source scope；
- 直接确认用户目标；
- 直接生成最终 LearningPlan；
- 用模型常识补造材料中不存在的知识节点。

模型参与时必须持久化 inference/version，replay 不重新调用当前模型。

### 7. User Confirmation Semantics

#### D04-050

开始学习不要求用户确认 LearningGoal。系统按 `PD-RULE-004` 采纳 Goal 后即可进入 mapping。不要求逐个确认 KU。

若 mapping 存在会产生显著不同学习路径的 blocking ambiguity，SYS06 MUST：

- 标记 mapping `blocked/candidate`；
- 提供最小 bounded clarification；
- 不猜测最终 target set。

非 blocking 低风险排序差异 MAY 由 deterministic mapper 选择，并保留 reason/evidence。

### 8. Goal-specific Knowledge Subgraph

#### D04-060

SYS06 可构建 versioned read-only subgraph snapshot：

```yaml
goal_subgraph:
  subgraph_id: uuid
  goal_mapping_ref: versioned_ref
  target_knowledge_unit_ids: [uuid]
  included_prerequisite_ids: [uuid]
  relation_refs: [versioned_ref]
  knowledge_graph_versions: [string]
  closure_policy_version: string
  reason_codes: [string]
```

它是规划 projection，不是第二知识图。所有 edge 必须引用 SYS01 published relation revision。

#### D04-061

Goal subgraph MUST 限于 confirmed source scope + required prerequisite closure；不得默认把整本书全部 KU 加入目标。

### 9. Determinism / Versioning

相同：

```text
Goal version
+ exact knowledge revisions
+ mapper version
+ fixed persisted model inference（如有）
```

MUST 得到相同 selected target set/stable ordering。

Goal materially changed、knowledge revision changed、scope changed 时 MUST 新建 mapping version；不得覆盖历史。

### 10. Failure Semantics

至少区分：

```text
NO_PUBLISHED_TARGET_MATCH
AMBIGUOUS_GOAL_MAPPING
CONTENT_MODEL_INCOMPLETE
SOURCE_SCOPE_EMPTY
STALE_KNOWLEDGE_GRAPH
MAPPING_MODEL_UNAVAILABLE
SUCCESS_CRITERIA_UNMEASURABLE
```

模型不可用时 SHOULD 降级到 deterministic lexical/hierarchy path；不得扩展 source scope。

### 11. Tests

MUST 覆盖：

1. goal source scope hard filter；
2. 一般“理解全书核心思想”映射为有限 target set；
3. 明确专题目标只映射相关 KU；
4. candidate-only KU 不进入 executable mapping；
5. blocking ambiguity 触发 clarification；
6. model unavailable deterministic fallback；
7. fixed input/version deterministic mapping；
8. goal change creates new mapping version；
9. mapping 不修改 SYS01 knowledge truth。

### 12. Acceptance Criteria

- `D04-AC-001`：每个 selected target KU 有 mapping reason/evidence 和 exact knowledge version。
- `D04-AC-002`：用户 Goal 不再要求人工预填 target KU id 才能进入主流程。
- `D04-AC-003`：LLM mapping proposal 不具有知识发布或 Goal confirmation 权限。
- `D04-AC-004`：source scope 不能被 mapper/LLM 静默扩大。
- `D04-AC-005`：Goal-specific subgraph 只引用 SYS01 canonical relation，不复制第二 graph truth。
- `D04-AC-006`：mapping blocking ambiguity 不被静默猜测。
- `D04-AC-007`：现有 LearningPlanner contract 无需重写即可消费 selected target ids。

### 13. Forbidden Implementations

禁止：

- `LLM(goal) → full course JSON → directly persist LearningPlan`；
- 用目录章节作为唯一 target mapping；
- candidate KU 当 published truth；
- mapper 修改 prerequisite graph；
- learner mastery 反向改变用户目标语义；
- 未保存模型推断结果的在线 LLM replay。

### 14. Freeze Decision

`SPEC-D04`：**FROZEN / UI-02B2 ADDITIVE**。`selected_target_ids` 的稳定顺序按 deterministic
fusion rank 降序；第一个 target 是首轮 prerequisite diagnostic 的
`primary_diagnostic_target_id`。该规则只选择首轮诊断入口，不删除其余目标，也不改变完整
Goal subgraph/plan scope。`PD-RULE-004` 已冻结「开始学习不要求用户确认 Goal」。若实现必须新增跨系统公共 Goal 类型或改变 LearningGoal owner，必须先报告 `SPEC GAP`。

---

## SPEC-D05 — Prerequisite Diagnostic Bootstrap Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D05`  
> 冻结日期：2026-08-08  
> Owners：SYS06（诊断需求/活动规划）、SYS04（Assessment/Diagnosis）、SYS03（LearnerState projection）  
> 上游：`SPEC-D04`、`systems/03-learner-model.md`、`systems/04-assessment.md`、`systems/06-learning-planner.md`  
> 目的：冻结 Goal-specific subgraph 进入第一版 LearnerState / LearningPlan 之前的 prerequisite diagnosis，不重建第二套 assessment 或 mastery engine。

### 1. Boundary

本合同严格保持：

```text
哪些 prerequisite 需要测      → SYS06
AssessmentItem / Attempt / Result → SYS04
长期 evidence / MasteryEstimate  → SYS03
下一步 LearningPlan             → SYS06
```

SYS04 MUST NOT 修改 LearningPlan/Mastery；SYS06 MUST NOT 自行判分；SYS03 MUST NOT 自行创建 AssessmentResult。

### 2. Diagnostic Need

#### D05-010

SYS06 根据：

```text
confirmed GoalKnowledgeMapping
+ GoalSpecificKnowledgeSubgraph
+ exact LearnerState/MasteryEstimate
+ time/diagnostic budget
```

构建 `DiagnosticNeed` decision record：

```yaml
diagnostic_need:
  need_id: uuid
  goal_mapping_ref: versioned_ref
  target_knowledge_unit_id: uuid
  prerequisite_knowledge_unit_ids: [uuid]
  unknown_ids: [uuid]
  unmet_ids: [uuid]
  reason_codes: [string]
  planner_version: string
  created_from_learner_state_version: integer
```

它是 SYS06 决策记录，不是 learner truth。

### 3. Unknown Semantics

#### D05-020

`UNKNOWN/MISSING/LOW_CONFIDENCE` mastery MUST NOT 当 0 或 1。

若 hard prerequisite 状态未知且会改变 target feasibility，SYS06 MUST 优先创建 `DIAGNOSTIC` activity 或明确 blocked state。

若 prerequisite 已有足够 current independent evidence，则不得为固定流程强制重复测量。

### 4. Adaptive Diagnostic Baseline

MVP 采用 deterministic、可解释的 graph-adaptive diagnostic：

```text
Goal target
→ immediate/high-value prerequisite unknowns
→ choose diagnostic item
→ Attempt / AssessmentResult
→ SYS03 projection update
→ re-evaluate prerequisite feasibility
→ if failure: descend toward prerequisite causes
→ if success: continue only with unresolved decision-relevant unknowns
→ stop on sufficient feasibility or budget limit
```

#### D05-030

成功测得较高层 prerequisite 不得自动把其所有祖先 MasteryEstimate 改为 mastered；是否接受何种推断证据仍由 SYS03 projector contract 决定。

SYS06 仅可因为“当前直接 prerequisite 已有足够 evidence”减少无必要测试。

### 5. Selection Objective

#### D05-040

诊断 item/knowledge-unit selection SHOULD 最大化：

```text
decision relevance
prerequisite coverage
uncertainty reduction
centrality/value
expected time efficiency
```

并受：

```text
source/goal scope
assessment availability
exposure history
security
user time budget
```

约束。

Complex IRT-CAT 不属于本 bootstrap；使用现有 SYS04 information-gain heuristic 范围。

### 6. Assessment Asset Contract

#### D05-050

SYS04 优先复用已 active、可稳定判分的 AssessmentItem。

若缺 item：

- SYS08 MAY 在 SYS04 约束下生成 draft candidate；
- SYS04 MUST 完成 schema/scoring/reference validation 后才可 active；
- 能 deterministic 评分的题型优先 exact/MCQ/numeric；
- grader-only solution/rubric 不得泄漏 learner-visible context。

不得为了完成诊断直接使用未验证 LLM question+answer。

### 7. Diagnostic Run

SYS04 MAY 维护 assessment workflow/run ref，但 canonical facts 仍是已有：

```text
AssessmentItem
Attempt
AssessmentResult
Diagnosis
```

`DiagnosticStarted` 等事件继续使用现有 Event Contract；不新增第二 assessment result schema。

### 8. LearnerState Update

#### D05-060

每个 AssessmentResult 由 SYS03 通过现有 evidence eligibility/projector 消费。

必须保留：

```text
actual assistance
independence
assessment confidence
diagnostic confidence
delay/transfer semantics
source evidence refs
```

系统/模型/工具失败不得形成 learner failure evidence。

### 9. Stop Conditions

诊断停止条件 MUST versioned，至少允许：

```text
ALL_DECISION_RELEVANT_PREREQUISITES_RESOLVED
TARGET_READY
REMEDIATION_REQUIRED
DIAGNOSTIC_BUDGET_EXHAUSTED
NO_VALID_ASSESSMENT_ITEM
LOW_CONFIDENCE_REQUIRES_REVIEW
USER_STOPPED
SYSTEM_BLOCKED
```

固定题数/固定阈值不得被描述为普适科学常数。

#### D05-070

Budget exhausted 时：

- 保留 unknown；
- Planner 使用 uncertainty-aware conservative planning；
- MUST NOT 把未测状态默认 mastered/failed。

### 10. Replanning

诊断产生 material LearnerState change 后，SYS06 MUST 使用现有 replan contract，而不是维护独立“诊断课程表”。

典型结果：

```text
unknown prerequisite → DIAGNOSTIC
unmet prerequisite   → PREREQUISITE_REMEDIATION
prerequisite ready   → LEARN_NEW / PRACTICE
already mastered     → TRANSFER_CHECK as needed
```

### 11. Idempotency / Replay

固定：

```text
Goal mapping version
+ subgraph relation refs
+ learner state version
+ diagnostic planner version
+ assessment item/version
```

必须能重放诊断决策。Replay 不调用在线 LLM；若历史 item 是模型生成，使用持久化 exact item/version。

重复 SubmitResponse/idempotency key 不得生成第二 AssessmentResult/evidence。

### 12. Failure Semantics

至少：

```text
DIAGNOSTIC_ITEM_UNAVAILABLE
DIAGNOSTIC_ITEM_INVALID
ASSESSMENT_SYSTEM_FAILURE
DIAGNOSTIC_LOW_CONFIDENCE
PREREQUISITE_GRAPH_STALE
DIAGNOSTIC_BUDGET_EXHAUSTED
LEARNER_STATE_STALE
```

任何 system failure MUST 与 learner error 分离。

### 13. Tests

MUST 覆盖：

1. unknown prerequisite → DIAGNOSTIC；
2. success 后减少无决策价值的下钻；
3. failure 后向更基础 prerequisite 下钻；
4. assessment result 经 SYS03 才影响 mastery；
5. budget exhausted 保留 unknown；
6. grader/model failure != learner failure；
7. answer-exposed success 不满足 independent evidence；
8. deterministic item route；
9. replay 不调用 LLM；
10. diagnosis 后触发现有 Planner replan。

### 14. Acceptance Criteria

- `D05-AC-001`：Goal-specific hard prerequisite 未知时可形成真实 DIAGNOSTIC activity。
- `D05-AC-002`：一次诊断 AssessmentResult 只经 SYS03 owner path 更新 LearnerState。
- `D05-AC-003`：诊断过程不会把 unknown 默认为 failed/mastered。
- `D05-AC-004`：失败可触发更基础 prerequisite 检查或 remediation，而不是重复同题无限循环。
- `D05-AC-005`：诊断预算、停止原因、输入版本均可审计。
- `D05-AC-006`：不存在第二 Assessment/Mastery/Planner truth。
- `D05-AC-007`：最终输出可直接进入现有 LearningPlanner / Adaptive Teaching Loop。

### 15. Forbidden Implementations

禁止：

- SYS06 内实现 grader；
- SYS04 直接写 mastery/plan；
- LLM 判断“用户应该会了”后直接设置 prerequisite satisfied；
- 一个失败结果永久标记 misconception/mastery；
- complex CAT/RL 作为 bootstrap 必需条件；
- 固定诊断题数作为普适教学规律。

### 16. Freeze Decision

`SPEC-D05`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。若实现需要新的 canonical assessment type、改变 SYS03 evidence semantics 或引入 complex CAT，必须先报告 `SPEC GAP`。

---

## SYS06 Activity Lifecycle and Completion

> Spec ID：`SYS06-ACT-*`
> 状态：Canonical Implementation Contract / Frozen
> 版本：v1.0
> 冻结日期：2026-08-09
> Governing decision：ADR-0007

### 1. Ownership and Meaning

`LearningActivityStateV1` 是 SYS06-owned current lifecycle truth。它只回答计划任务的可用、执行和完成状态，不回答 learner mastery、assessment correctness、objective satisfaction 或 goal achievement。

`LearningActivity` definition immutable；payload status 是 initial/legacy snapshot。cutover 后所有 current-state query、Today、Path 与 execution guard MUST 读取 latest lifecycle state。

### 2. State Contract

```yaml
learning_activity_state_v1:
  schema_version: "1.0"
  activity_id: uuid
  version: integer >= 1
  plan_id: uuid
  plan_version: integer >= 1
  status: planned|available|active|completed|skipped|superseded
  previous_status: planned|available|active|completed|skipped|superseded|null
  transition_reason: string
  source_refs: [versioned_ref]
  actor_type: system|learner
  started_at: datetime|null
  completed_at: datetime|null
  correlation_id: uuid
  created_at: datetime
```

唯一约束为 `(activity_id, version)`；version 单调递增。state row、SYS06 event 与 outbox MUST 同事务提交。

### 3. Transitions

允许：

```text
planned → available        SelectNextLearningActivity
available → active         StartLearningActivityV1
active → completed         CompleteLearningActivityV1
planned/available → skipped
planned/available/active → superseded
```

禁止 completed 回退；需要再次学习时由 replan 创建新 activity。superseded plan 下的 activity 不得 start/complete。

#### SYS06-ACT-010 — Availability

只有 SYS06 可根据 immutable plan order、前置约束与当前状态把 activity 置为 available。选择不得重排 `LearningPlan.activity_ids`。

#### SYS06-ACT-011 — Start

`StartLearningActivityV1` 仅接受 current `available`，必须校验 owner chain、current plan、expected state version、idempotency 与 execution capability。成功产生 `ActivityStarted`，重复相同 command 返回原结果。

#### SYS06-ACT-012 — Completion

`CompleteLearningActivityV1` 仅接受 current `active`。UI-02C v1 的 `learner_finished` 只适用于 transcript-backed `learn_new|prerequisite_remediation|practice|metacognitive_review`，且必须引用至少一个 current-user accepted transcript turn。

`diagnostic|delayed_review|transfer_check` 返回 `ACTIVITY_COMPLETION_EVIDENCE_REQUIRED`，直到对应 evaluator/review contract 冻结。completion 不写 SYS03/SYS04/SYS05/SYS07 state。

#### SYS06-ACT-013 — Progression

completion 与 next eligible activity `planned → available` 必须原子提交。不存在下一非终态 activity 时，SYS06 MAY 将 plan 置为 completed；goal 保持原状态，除非独立 goal-achievement command 已冻结。

### 4. Commands

```yaml
start_learning_activity_v1:
  schema_version: "1.0"
  activity_id: uuid
  expected_state_version: integer >= 1
  idempotency_key: string

complete_learning_activity_v1:
  schema_version: "1.0"
  activity_id: uuid
  expected_state_version: integer >= 1
  completion_intent: learner_finished
  transcript_turn_refs: [versioned_ref]
  idempotency_key: string
```

客户端不得提交 target status、next activity、mastery、objective/goal status、plan order 或 evidence score。

### 5. Events

`ActivityAvailable`、`ActivityStarted`、`ActivityCompleted` 使用现有 `LearningEventEnvelope`，payload 至少包含 activity/plan/goal refs、previous/new status、lifecycle version、reason、source refs；event provenance owner 为 SYS06。aggregate version 使用 lifecycle version，不复用 plan version。

### 6. API and Query

- `POST /api/v1/workspace/activities/{activity_id}/start`
- `POST /api/v1/workspace/activities/{activity_id}/complete`
- `GET /api/v1/workspace/activities/{activity_id}`

写响应返回 strict v1 state、next activity ref/plan status 与 correlation id；query 返回 execution capability 与 stable `/learn/{activity_id}` product route，但不得把 route/session 当作 lifecycle truth。所有资源 current-user scoped，未授权与不存在不可枚举，read response `private, no-store`。

### 7. Stable Errors

```text
ACTIVITY_NOT_AVAILABLE
ACTIVITY_NOT_ACTIVE
ACTIVITY_STALE_OR_SUPERSEDED
ACTIVITY_COMPLETION_EVIDENCE_REQUIRED
ACTIVITY_EXECUTION_UNAVAILABLE
ACTIVITY_STATE_VERSION_CONFLICT
ACTIVITY_IDEMPOTENCY_CONFLICT
LEGACY_ACTIVITY_STATE_UNMIGRATED
```

provider/transcript persistence failure不得映射成 learner failure 或 completion。version/idempotency/business errors non-retryable；transient DB/outbox failure可 bounded retry。

### 8. Migration and Compatibility

按 ADR-0007 backfill。所有新 plan 创建时原子创建 lifecycle v1。迁移完成后 active readers 不再以 payload status、event recency 或 transcript presence 推断 current state；legacy fallback 必须显式 reason 且有删除 gate。

### 9. Security and Privacy

completion source refs 必须属于同一 current user/activity；不复制 transcript正文、Prompt、grader answer 或 secret。外部模型无 lifecycle command 权限。

### 10. Acceptance Criteria

- `SYS06-ACT-AC-001`：latest version 是唯一 current truth，payload/transcript/UI 不形成第二 writer。
- `SYS06-ACT-AC-002`：允许转换、禁止转换、expected version 与 duplicate idempotency 可机器验证。
- `SYS06-ACT-AC-003`：start/complete/next availability/outbox 原子、可重启恢复。
- `SYS06-ACT-AC-004`：completion 不写 mastery/assessment/policy/review，不自动 achieved/satisfied。
- `SYS06-ACT-AC-005`：evaluator-required activity fail closed；provider failure不形成 completion/evidence。
- `SYS06-ACT-AC-006`：SQLite/PostgreSQL migration、backfill、reconciliation 与 forward-fix 有测试。
- `SYS06-ACT-AC-007`：cross-user、stale plan、superseded activity 与 source-ref ownership 不泄漏。

### 11. First Activity Completion Projection

#### SYS06-ACT-080

SYS06 MUST 提供 current-user scoped `FirstActivityCompletionProjectionV1` 只读 query：只纳入 canonical
latest `status=completed` 且 completion transition 已验证 accepted transcript source 的 activity；按
`completed_at ASC, activity_id ASC` 稳定选择首个。

该 projection MUST 返回 exact activity/state/completion source refs，不复制 transcript 正文；不存在时
返回 MISSING。它不新增 lifecycle writer，也不得以 inference/message/duration/plan ready/Attempt/UI click
补齐。

#### SYS06-ACT-AC-008

相同 owner state 重查必须返回相同 first completion；删除/supersede/unauthorized/stale source 时不得保留
onboarding 缓存完成状态。

### 12. Course-scoped Activity Index Source

#### SYS06-ACT-090

ADR-0023 / `CWSP-050..054` authorizes a read-only Course Activity index assembler to consume exact immutable LearningActivity + latest `LearningActivityStateV1` refs after resolving the Activity's exact Goal/Plan Workspace chain。The assembler is not a SYS06 writer；it MUST NOT infer current/resumable/available from transcript、Conversation、route、session recency or frontend state。

#### SYS06-ACT-091

`active` MAY be presented as resumable；`available` still requires `StartLearningActivityV1`；all other states are unavailable unless a future SYS06 command says otherwise。Multiple active current-plan activities are returned as `PARTIAL` integrity state, not arbitrarily selected。

#### SYS06-ACT-AC-009

Course Activity index refresh is deterministic/side-effect-free、same-Workspace only、stable ordered and preserves exact Activity/lifecycle/Plan/Goal source refs；it does not create Session、Activity state、Evidence or completion。
