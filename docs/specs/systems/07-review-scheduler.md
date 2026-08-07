# SYS07 — Review Scheduler

> Spec ID：`SYS07-*`  
> 对应设计：4.7 记忆保持与复习调度  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS07-001

SYS07 的唯一职责是根据有效 retrieval evidence 与 versioned memory model，维护 learner × KnowledgeUnit 的 ReviewSchedule，并计算建议 `next_due_at`。

SYS07 MUST NOT 裁决完整 mastery、修改 LearnerState、生成完整日计划、选择 TeachingAction、重新判分 Attempt 或把所有知识类型强制等同 flashcard recall。

## 2. Owned State

SYS07 独占：ReviewSchedule、memory scheduling state、desired retention policy/config、retrievability estimate、next_due_at、review priority。

## 3. Inputs

允许读取 AssessmentResult、Attempt actual assistance/exposure、valid retrieval/review events、MasteryEstimate read-only、knowledge type、用户 workload/retention preference。

### SYS07-010

只有通过 evidence filter 的真实 retrieval observation 才能高权更新 memory state。

### SYS07-200 — v0.3 Review Observation

有效 observation 至少 MUST 能表达：

```text
retrieval_required
assistance_state = INDEPENDENT|ASSISTED|ANSWER_EXPOSED
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
assessment_confidence
actual_delay / elapsed_since_last_valid_retrieval
knowledge_type
source Attempt/AssessmentResult refs
```

历史 `hint_level`/整数 exposure MAY read-only 迁移，MUST NOT 继续作为 v0.3 canonical observation writer。

### SYS07-201 — Independence Integrity

`ANSWER_EXPOSED` observation MUST NOT 作为完整独立 retrieval；`ASSISTED` observation MUST 与 independent evidence 分开处理。只有 fresh `INDEPENDENT` retrieval observation 才 MAY 满足需要独立验证/延迟保持的证据条件。

## 4. Outputs

输出 ReviewSchedule version、ReviewDue/context、retrievability estimate、DecisionTrace、ReviewScheduled/ReviewScheduleUpdated events。SYS06 决定 due candidate 是否进入实际日计划。

### SYS07-020

`retrievability != mastery`。ReviewSchedule MUST NOT 持有完整 mastery label。

## 5. Algorithms

### SYS07-030 — Baseline

MVP SHOULD 使用 FSRS-compatible 或等价可解释 memory scheduler，并保留 simpler baseline 比较：

```text
assessment/review result
→ retrieval evidence validation
→ load prior memory state
→ update model state
→ estimate retrievability
→ solve next_due_at for desired retention
→ new ReviewSchedule version
```

### SYS07-031 — Evidence Filter

强提示/partial step/bottom-out、答案暴露后复述、评分置信度过低等 MUST NOT 当作完整 independent recall。具体 weighting/eligibility MUST versioned。

### SYS07-032 — Cold Start

无个体数据时 MAY 使用 default/population parameters；MUST NOT 因历史少而伪造高精度 personalization。

### SYS07-033 — Knowledge Type

事实、概念、程序、迁移任务 MAY 使用不同 observation adapter/policy；MUST NOT 用单一 flashcard rating 代表全部能力。

### SYS07-034 — Desired Retention

`desired_retention` 是产品/用户 strategy parameter，不是学术常数；MUST versioned/traceable。

### SYS07-035 — v0.3 Scope

Bandit/RL scheduler MAY 作为未来研究方向，但 MUST NOT 成为 v0.3 canonical runtime。

## 6. Persistence / Replay

### SYS07-040

ReviewSchedule 使用 immutable/version stream。

### SYS07-041

MUST 分别保存 recommended next_due_at、actual review time、source evidence/event ids、memory model/version、desired retention version。

### SYS07-042

SYS03/SYS06 MUST NOT 维护语义重复的 canonical next_due_at。

### SYS07-043

Fixed prior schedule + exact observation + model/config version MUST 产生相同 semantic next schedule。缺 historical version 时 MUST 标记 partial/non-replayable，而不是用当前 model 伪 replay。

## 7. Failure Semantics

invalid/low-quality observation → no/low update；model/config unavailable → versioned fallback；impossible desired retention/workload → policy error/clamp with reason；late valid event/evidence invalidation → recompute affected versions。

### SYS07-050

Scheduler failure MUST NOT 被解释为 learner forgetting；保留 last valid schedule 并标 stale/fallback。

## 8. Idempotency

同一 observation/event 只能应用一次；repeated due-check 不产生新 schedule version，除非 underlying state 改变。

## 9. Observability

记录 observation eligibility/reason、actual assistance/exposure、prior/new memory state、model/version、desired retention、retrievability、next_due_at、actual/recommended delay、fallback/stale。

Metrics MAY 包含 calibration、observed vs predicted recall、reviews per retained unit、overdue rate、hint-free independent review ratio、schedule update latency、workload。

## 10. Security

ReviewSchedule 属个人学习数据；外部模型不是 scheduler 必需项；用户材料指令 MUST NOT 修改 desired retention/model parameters；用户 preference 更新必须经显式 command/config。

## 11. Tests

必须覆盖：independent recall；failure；assisted success weaker/no full update；ANSWER_EXPOSED not independent；fresh independent delayed observation；cold start；duplicate idempotency；desired retention versioning；evidence invalidation recompute；actual vs recommended time；fixed-model replay；legacy hint_level migration ambiguity。

## 12. Acceptance Criteria

- `SYS07-AC-001`：任一 next_due_at 可追溯 source evidence 与 memory model version。
- `SYS07-AC-002`：ASSISTED/ANSWER_EXPOSED 不等同完整 independent recall。
- `SYS07-AC-003`：ReviewSchedule 与 MasteryEstimate 分离。
- `SYS07-AC-004`：SYS06 只能消费 due candidate，不能修改 memory state。
- `SYS07-AC-005`：同 observation/model version 更新确定性。
- `SYS07-AC-007`：推荐复习时点与实际执行时点分别审计。
- `SYS07-AC-200`：v0.3 canonical review observation 不使用 integer `hint_level` 作为 truth。

## 13. Legacy Mapping

旧 `hint_level`、old assistance/exposure scale MAY 由 read adapter 映射到 v0.3 orthogonal assistance snapshot；无法无损映射 MUST 标记 unknown/ambiguous + migration reason，并降低 evidence eligibility/replayability。所有 active writers/readers 切换且历史迁移状态明确后旧 adapter SHOULD retirement。

## 14. Forbidden Implementations

禁止：固定 1/3/7/14 天适配所有知识；多方写 next_due；完整答案后复述当 independent recall；retrievability 直接标 stable mastery；scheduler 创建完整日计划；LLM 凭感觉决定 next_due；v0.3 用 RL 替代成熟 SRS baseline；继续写 integer hint/exposure 为 canonical review observation。