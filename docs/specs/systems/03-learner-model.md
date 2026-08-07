# SYS03 — Learner Model

> Spec ID：`SYS03-*`  
> 对应设计：4.3 学习者建模  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS03-001

4.3 的唯一职责是把跨时间的有效学习证据融合为可版本化、带不确定性的 `LearnerState` 与 `MasteryEstimate`。

### SYS03-002

4.3 是以下状态唯一写入者：

- LearnerState；
- MasteryEstimate；
- learner-specific misconception hypothesis；
- LearnerEvidence 的最终 accepted/rejected/invalidated 状态。

## 2. Non-responsibility

4.3 MUST NOT：

- 对单次 Attempt 判分；
- 发布 AssessmentItem；
- 选择 TeachingAction；
- 生成 LearningPlan；
- 计算 next_due_at；
- 用 LLM 自评直接覆盖 mastery。

## 3. Owned State

核心状态：

```text
LearnerEvidence
MasteryEstimate version stream
LearnerState snapshot stream
MisconceptionHypothesis
LearnerModelParameters
ProjectionCheckpoint
```

### SYS03-010

MasteryEstimate 是推断，不是客观事实。必须同时保存 confidence/evidence sufficiency。

## 4. Inputs

允许读取/消费：

- AssessmentResult；
- Attempt assistance metadata；
- LearningEvent；
- FeedbackSignal；
- Review outcome / retrievability 只读特征；
- KnowledgeUnit identity/revision；
- item difficulty（若已校准）。

### SYS03-011

4.3 MUST NOT 接受来自 4.4/4.8 的 `SetMastery` 或等价命令。

## 5. Outputs

输出：

- LearnerEvidence accepted/rejected；
- MasteryEstimate；
- LearnerState；
- learner misconception hypothesis；
- state changed events；
- DecisionTrace payload；
- 面向 Open Learner Model 的可解释 reason codes。

## 6. Domain Objects

遵循 `domain-model.md`。

MasteryEstimate 至少要区分：

- competence probability/estimate；
- confidence；
- independent success；
- hint dependency；
- delayed recall evidence；
- transfer evidence；
- active misconception；
- evidence count/weight；
- algorithm version。

## 7. Commands

建议：

```text
AcceptAssessmentEvidence
RejectAssessmentEvidence
InvalidateEvidence
ProjectLearnerState
RecomputeLearnerState
HandleLearnerStateDispute
```

### SYS03-020

用户争议状态时只能进入 dispute/retest/recompute 流程，不能提供通用 `SetMasteryProbability`。

## 8. Events

消费：

- `AttemptScored`
- `ReviewCompleted`
- `TransferAttemptCompleted`
- FeedbackSignal/state dispute

产生：

- `EvidenceAccepted`
- `EvidenceRejected`
- `MasteryProjectionUpdated`

每次高影响状态更新 MUST 写 DecisionTrace。

## 9. Algorithms

### SYS03-030：MVP Baseline

默认采用：

```text
AssessmentResult
→ evidence eligibility
→ evidence weighting
→ BKT / simple interpretable probabilistic update
→ uncertainty/effective evidence calculation
→ MasteryEstimate version
→ LearnerState snapshot
```

### SYS03-031：Evidence weighting

至少考虑：

- correctness/score；
- assessment confidence；
- hint level；
- answer exposure；
- delay；
- novelty/transfer distance；
- item difficulty；
- repeated item；
- error/misconception evidence。

### SYS03-032：掌握标签

稳定掌握至少要求：

- 足够的独立成功证据；
- 延迟提取证据；
- 无高置信活跃误区；
- 掌握估计与 confidence 达到配置门槛。

迁移能力必须额外要求足够新颖的独立迁移证据。

具体阈值属于版本化 policy/config，不得硬编码成“学术定律”。

### SYS03-033：BKT

BKT 是 v0.2 推荐 baseline；参数必须版本化。简单加权证据模型 MUST 保留为可比较 baseline。

### SYS03-034：IRT/PFA/DKT

- PFA：MAY 作为离线 challenger；
- IRT：题库稳定且有校准数据后 MAY 用于难度/能力校正；
- DKT/SAKT/SAINT：当前只能 challenger/auxiliary feature，MUST NOT 作为 v0.2 canonical truth source。

### SYS03-035：RL

Learner modeling 是状态估计问题。MUST NOT 引入 RL 来“更新 mastery”。

## 10. Persistence

### SYS03-040

LearnerEvidence、MasteryEstimate 与 LearnerState 必须逻辑分离。

### SYS03-041

MasteryEstimate 更新必须 append/version；历史估计可查询。

### SYS03-042

每个 estimate MUST 关联 source evidence ids 与 algorithm version。

### SYS03-043

Recompute 必须支持从事件/accepted evidence 重新投影，不依赖在线 LLM。

## 11. Failure Semantics

- AssessmentResult confidence 过低 → reject/low weight；
- assistance metadata 缺失 → conservative/reject stable-mastery evidence；
- unknown KnowledgeUnit revision → quarantine/reconciliation；
- projector algorithm failure → 保留 last valid state，记录 lag/failure；
- parameter unavailable → fallback baseline；
- challenger unavailable → 不影响 canonical baseline。

### SYS03-050

低质量/不完整证据导致的正确行为是“不确定”，不是伪造精确 mastery。

## 12. Idempotency

### SYS03-060

同一 `LearnerEvidence`/source result 只能被 canonical projector 接纳一次。

### SYS03-061

重复事件消费不得再次增加 evidence_count 或重复更新 mastery。

### SYS03-062

固定 evidence 集合 + fixed algorithm version 必须得到确定性 state content。

## 13. Observability

必须记录：

- evidence eligibility/weight reason codes；
- prior/posterior estimate；
- algorithm/parameter version；
- projection latency/lag；
- replay divergence；
- active misconception changes；
- confidence/effective sample size。

指标：log loss、Brier、ECE/calibration、next-attempt prediction、false mastery promotion、hint-dependency identification、replay determinism。

## 14. Security

- mastery/learner state 属于 personal/sensitive learning data，访问必须最小权限；
- 外部模型不得默认接收完整 learner history；
- LLM 仅可用于说明/分类辅助，不拥有直接 repository write；
- 用户可查看、纠正、导出、删除其长期状态所依据的证据，具体遵循 privacy contract。

## 15. Tests

必须覆盖：

- independent vs hinted vs answer-exposed 权重差异；
- single immediate success 不直接 stable mastery；
- delayed evidence；
- transfer evidence；
- low-confidence assessment rejection；
- duplicate evidence idempotency；
- invalidated evidence replay；
- learner dispute 不直接改概率；
- deterministic replay；
- DKT challenger 无法直接写 canonical state；
- misconception evidence 与 active hypothesis 分离。

## 16. Acceptance Criteria

- `SYS03-AC-001`：任一 MasteryEstimate 可列出全部 source evidence ids 和算法版本。
- `SYS03-AC-002`：提示后成功与独立成功产生不同 evidence 权重。
- `SYS03-AC-003`：完整答案已暴露的成功不会产生 stable-mastery 高权证据。
- `SYS03-AC-004`：相同事件/evidence 重放得到相同状态内容。
- `SYS03-AC-005`：Assessment 模块不能直接写 mastery repository。
- `SYS03-AC-006`：用户状态争议可触发复测/重算并保留审计记录。
- `SYS03-AC-007`：DKT 失败不影响 canonical baseline 可用性。

## 17. Forbidden Implementations

禁止：

- `mastery = last_score`；
- 连续答对固定 N 次就无条件稳定掌握；
- LLM 输出 `mastery_probability` 直接入库；
- DKT 与 KT 各保存一套 canonical truth；
- 用户点赞直接提高 mastery；
- 不保存 source evidence 的裸 `skill_score`；
- replay 调用在线 LLM；
- 4.3 计算 next_due_at 或 LearningPlan。

## Legacy Mapping

当前主要相关：

```text
apps/backend/app/services/kt/knowledge_tracing_service.py
apps/backend/app/services/dkt/dkt_service.py
apps/backend/app/models/profile.py
apps/backend/app/models/assessment.py
```

迁移目标：明确一个 canonical learner-state projector；`dkt/` 降为 challenger，不再形成独立事实源。
