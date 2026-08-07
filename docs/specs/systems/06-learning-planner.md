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
GenerateLearningPlan
ReplanLearningPlan
SelectNextLearningActivity
PauseLearningPlan
ResumeLearningPlan
```

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
- 只有确认的 Goal/用户约束可以成为长期计划事实；
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
