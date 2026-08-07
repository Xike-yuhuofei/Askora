# SYS07 — Review Scheduler

> Spec ID：`SYS07-*`  
> 对应设计：4.7 记忆保持与复习调度  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS07-001

4.7 的唯一职责是根据有效提取证据和版本化记忆模型，维护 learner × KnowledgeUnit 的记忆调度状态，并计算建议 `next_due_at`。

一句话：**决定什么时候最好复习。**

## 2. Non-responsibility

4.7 MUST NOT：

- 裁决完整 mastery；
- 修改 LearnerState；
- 生成完整日计划；
- 选择 TeachingAction；
- 对 Attempt 重新判分；
- 把所有知识类型强制等同闪卡 recall。

## 3. Owned State

4.7 独占：

- ReviewSchedule；
- memory model state；
- desired retention policy/config；
- retrievability estimate；
- next_due_at；
- review priority。

## 4. Inputs

允许读取：

- AssessmentResult；
- Attempt assistance/exposure metadata；
- ReviewCompleted/valid retrieval events；
- MasteryEstimate read-only；
- knowledge type；
- user workload/retention preference（经产品确认）。

### SYS07-010

只有经过 evidence filter 的真实 retrieval observation 才能高权更新 memory state。

## 5. Outputs

输出：

- ReviewSchedule version；
- ReviewDue/due context；
- retrievability estimate；
- DecisionTrace；
- ReviewScheduled/ReviewScheduleUpdated events。

4.6 决定是否将 due 候选纳入实际日计划。

## 6. Domain Objects

遵循 `domain-model.md`。

有效复习观察至少包含：

```text
retrieval_required
independence_level
hint_level
answer_seen_before_attempt
assessment_confidence
elapsed_since_last_valid_retrieval
knowledge_type
```

### SYS07-020

`retrievability ≠ mastery`。ReviewSchedule 不得持有完整 mastery label。

## 7. Commands

建议：

```text
InitializeReviewSchedule
ApplyReviewObservation
RecomputeReviewSchedule
SetDesiredRetentionPolicy
InvalidateReviewObservation
```

不得暴露 `SetMastery` 或 `AddToTodayPlan`。

## 8. Events

消费：

- `AttemptScored`
- `ReviewCompleted`
- evidence invalidation/correction
- MasteryProjectionUpdated（只读特征刷新）

产生：

- `ReviewScheduled`
- `ReviewScheduleUpdated`

## 9. Algorithms

### SYS07-030：MVP Baseline

MVP 使用 FSRS-compatible scheduler 或等价可解释记忆模型，并保留 SM-2/simple exponential baseline 进行比较。

流程：

```text
assessment/review result
→ retrieval evidence validation
→ load prior memory state
→ update difficulty/stability
→ estimate retrievability
→ solve next_due_at for desired retention
→ ReviewSchedule version
```

### SYS07-031：Evidence filter

强提示成功、答案暴露后复述、评分置信度过低等情况不得当成完整独立 recall。

### SYS07-032：Cold start

无个体数据时使用 population/default parameters；不得因为历史少而伪造高精度个体化参数。

### SYS07-033：Knowledge type

事实记忆、概念理解、程序技能和迁移任务 MAY 使用不同 scheduling policy/observation adapter；不得用单一 flashcard rating 代表全部学习能力。

### SYS07-034：目标保持率

`desired_retention` 是产品/用户策略参数，不是学术常数。必须版本化，并限制合理上下界，避免无限工作量。

### SYS07-035：算法演进

```text
固定间隔
→ SM-2/FSRS/HLR类模型
→ 参数校准/监督优化
→ workload-retention optimization
→ Bandit/RL only if proven necessary
```

v0.2 禁止 RL。

## 10. Persistence

### SYS07-040

ReviewSchedule 采用 immutable/version stream。

### SYS07-041

必须分别保存：

- recommended next_due_at；
- actual review execution time；
- source evidence/event ids；
- memory model/version；
- desired retention version。

### SYS07-042

4.3/4.6 不得维护语义重复的 canonical next_due_at。

## 11. Failure Semantics

- invalid/low-quality observation → record but no/low update；
- model/parameter unavailable → fallback stable baseline；
- impossible desired retention/workload → clamp/policy error with reason code；
- historical schedule missing → cold-start initialize；
- late valid event → recompute affected schedule；
- invalidated evidence → replay/recompute。

### SYS07-050

调度器故障不能被解释成 learner forgetting；必须保留 last valid schedule 并标明 stale/fallback。

## 12. Idempotency

- 同一 observation/event 只能应用一次；
- fixed prior state + observation + model version 必须得到相同新 schedule；
- repeated due-check 不产生新 schedule version，除非 underlying state 改变。

## 13. Observability

必须记录：

- valid/invalid observation reasons；
- prior/new memory state；
- model/version；
- desired retention；
- predicted retrievability；
- next_due_at；
- interval change reason；
- fallback/stale state。

指标：Brier/log loss、calibration、observed vs predicted recall、reviews per retained unit、overdue rate、hint-free review ratio、schedule update p95、workload。

## 14. Security

- ReviewSchedule 属于个人学习数据，最小权限访问；
- 外部模型不是调度必需项，v0.2 SHOULD 不依赖外部 LLM；
- 用户材料中的指令不能修改 desired retention/model parameters；
- user preference 更新必须经显式配置/command。

## 15. Tests

必须覆盖：

- independent recall extends interval；
- failure shortens interval；
- hinted success receives weaker/no full update；
- answer exposed not full recall；
- cold start；
- duplicate observation idempotency；
- desired retention change versioning；
- evidence invalidation recompute；
- actual vs recommended time separation；
- 4.6 cannot modify memory state；
- fixed model replay determinism。

## 16. Acceptance Criteria

- `SYS07-AC-001`：任一 next_due_at 可追溯 source evidence 与 memory model version。
- `SYS07-AC-002`：强提示/答案暴露成功不会等同完整独立 recall。
- `SYS07-AC-003`：ReviewSchedule 与 MasteryEstimate 分离。
- `SYS07-AC-004`：4.6 只能消费 due candidate，不能修改 memory state。
- `SYS07-AC-005`：同 observation/model version 更新确定性。
- `SYS07-AC-006`：参数/模型故障有 baseline fallback。
- `SYS07-AC-007`：推荐复习时点与实际执行时点可分别审计。

## 17. Forbidden Implementations

禁止：

- 所有知识固定 1/3/7/14 天；
- `next_review_at` 同时由 4.3、4.6、4.7 多方写；
- 把完整答案后复述当成功 recall；
- 用 retrievability 直接标 stable mastery；
- 复习调度器创建完整日计划；
- LLM 凭感觉决定下次复习日期；
- 参数历史不足时训练/启用不稳定个体模型；
- v0.2 使用 RL 替代成熟 SRS baseline。

## Legacy Mapping

当前仓库尚未形成明确 SYS07 bounded context。若已有 `next_review_at`、memory strength 或类似字段散落在 profile/KT/plan 逻辑中，应通过 EXEC 统一迁移到单一 ReviewSchedule owner，而不是保留多处计算。
