# SYS03 — Learner Model

> Spec ID：`SYS03-*`  
> 对应设计：4.3 学习者建模与状态估计  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS03-001

SYS03 的唯一职责是把跨时间的有效学习证据融合为可版本化、带不确定性的 `LearnerState` 与 `MasteryEstimate`。

### SYS03-002

SYS03 是 `LearnerEvidence` accepted/rejected/invalidated 状态、`MasteryEstimate`、`LearnerState` 与 `MisconceptionHypothesis` 的唯一 owner。

SYS03 MUST NOT 判分 AssessmentResult、选择 TeachingAction、拥有 TeachingStage、修改 LearningPlan/ReviewSchedule，或把 LLM 自评直接写成 mastery truth。

## 2. Existing v0.2 Contracts Retained

### SYS03-010 — Mastery Is Inference

MasteryEstimate 是推断，不是客观事实。MUST 同时保存 confidence/evidence sufficiency，并可追溯算法与证据。

### SYS03-011 — No SetMastery

SYS03 MUST NOT 接受来自 SYS04/SYS08 的 `SetMastery`、`SetMasteryProbability` 或等价越权命令。

### SYS03-020 — Learner State Dispute

用户争议状态时 MUST 进入 dispute/retest/recompute 流程，MUST NOT 提供通用直接改 mastery probability 的命令。

### SYS03-030 — MVP Baseline

v0.3 canonical projector SHOULD 使用透明、可解释、可版本化的 evidence eligibility/weighting + BKT 或等价简单概率/证据投影 baseline；必须保留可比较的简单 baseline。Deep KT MUST NOT 成为 canonical truth。

### SYS03-031 — Evidence Weighting

Evidence weighting 至少 MUST 考虑：correctness/score、assessment confidence、`assistance_state`、`scaffold_control`、`hint_specificity`、`answer_exposure`、delay、novelty/transfer distance、item difficulty（若可靠）、重复 item 与 error/misconception evidence。

### SYS03-032 — Mastery Labels

稳定掌握至少 SHOULD 需要足够的独立成功证据、延迟提取证据、无高置信活跃误区、足够 confidence/evidence sufficiency；迁移能力必须额外要求足够新颖的独立迁移证据。具体阈值属于版本化 policy/config，不得硬编码为科学定律。

### SYS03-033 — BKT Baseline

BKT MAY 作为可解释 baseline；参数必须版本化。简单加权证据模型 MUST 保留为可比较 baseline。

### SYS03-034 — Challenger Boundary

PFA MAY 作为离线 challenger；IRT 只有在题库稳定且有校准数据后 MAY 用于难度/能力校正；DKT/SAKT/SAINT/AKT/Deep KT 只能作为 challenger/auxiliary feature，MUST NOT 作为 v0.3 canonical truth source。

### SYS03-035 — No RL Mastery Update

Learner modeling 是状态估计问题。MUST NOT 引入 RL 来“更新 mastery”。

### SYS03-040 — Logical Separation

`LearnerEvidence`、`MasteryEstimate` 与 `LearnerState` MUST 逻辑分离。

### SYS03-041 — Version Stream

MasteryEstimate/LearnerState 更新 MUST append/version；历史估计必须可查询。

### SYS03-042 — Provenance

每个 MasteryEstimate MUST 关联 source evidence ids、algorithm/version 与必要 parameter bundle version。

### SYS03-043 — Recompute / Replay

Recompute MUST 支持从 accepted evidence/event 重新投影，MUST NOT 依赖在线 LLM。

### SYS03-050 — Uncertainty

低质量/不完整证据的正确语义是“不确定”，MUST NOT 伪造精确 mastery。

### SYS03-060 — Evidence Idempotency

同一 LearnerEvidence/source result 只能被 canonical projector 接纳一次。

### SYS03-061 — Event Idempotency

重复事件消费 MUST NOT 再次增加 evidence_count 或重复更新 mastery。

### SYS03-062 — Deterministic Projection

固定 ordered evidence set + exact algorithm/config version MUST 得到相同 semantic state content。

## 3. v0.3 Assistance-aware Evidence

### SYS03-200 — Assistance-aware Evidence

Evidence eligibility/weight MUST 基于 SYS04 记录的实际：

```text
assistance_state
scaffold_control
hint_specificity
answer_exposure
```

不得基于 SYS05 allowed envelope 假定实际经历，也不得继续使用全局 integer `hint_level/scaffold_level/answer_exposure_max` 作为 canonical 语义。

### SYS03-201 — Independence Rules

`ANSWER_EXPOSED` success MUST NOT 成为 independent mastery evidence；`ASSISTED` success MUST 与 independent evidence 分离并按 versioned rules 降权/限制用途。只有 fresh `INDEPENDENT` Attempt 可形成新的 independent success evidence。

### SYS03-202 — Missing Assistance

assistance/exposure 不可确定时 MUST conservative：降低 eligibility/weight 或标记 uncertain；MUST NOT 默认 `INDEPENDENT`。

## 4. Misconception Boundary

### SYS03-210

```text
Misconception definition      → SYS01
MisconceptionEvidence         → SYS04
MisconceptionHypothesis       → SYS03
Remediation decision          → SYS05
```

SYS03 MAY 根据多个 evidence 更新 hypothesis/confidence，但 MUST NOT 把单个 SYS04 evidence 无条件提升为 confirmed learner misconception。

## 5. LearnerState vs TeachingStage

### SYS03-220

`TeachingStage` 属于 SYS05 对当前 TeachingContext 的派生控制语义，MUST NOT 存入 LearnerState 作为 persistent learner stage。

历史 `LearnerState.learning_stage_summary` 在 v0.3 MUST 迁移/重命名为 `learner_progress_summary` 或等价非教学策略摘要，并 MUST 明确与 SYS05 TeachingStage 没有 ownership/inheritance 关系。

## 6. Independent Validation Boundary

### SYS03-230

`INDEPENDENT_VALIDATION_REQUIRED` 是 SYS05 policy-control obligation，不是 MasteryState。SYS03 MUST NOT 创建、完成或清除该 obligation。

### SYS03-231

在 fresh independent Attempt 实际发生并被 SYS04 接纳前，SYS03 MUST NOT 因“已安排独立验证”“时间已过去”或“LLM 判断会做”而假定 obligation 已完成。

### SYS03-232 — Configurable Parameters

mastery threshold、evidence weights、hint-dependency weighting、delay/transfer qualification 等参数 MUST versioned/traceable，MUST NOT 写成不可变科学常数。

## 7. Failure Semantics

必须区分：evidence ineligible、assistance unknown、source result superseded、unknown KnowledgeUnit revision、algorithm/parameter unavailable、projection failure、insufficient evidence、state version conflict。

Projector failure MUST 保留 last valid state 并记录 failure/lag；challenger failure MUST NOT 影响 canonical baseline。

## 8. Observability

必须记录 evidence acceptance/rejection/weight reason、actual assistance snapshot refs、prior/posterior estimate、algorithm/parameter version、projection latency/lag、replay divergence、misconception hypothesis changes、confidence/effective evidence size。

Metrics MAY 包含 log loss、Brier、ECE/calibration、next-attempt prediction、false mastery promotion、hint-dependency identification 与 replay determinism；这些预测指标不等于学习效果证据。

## 9. Security

LearnerState/MasteryEstimate 属个人学习数据，访问必须最小权限；外部模型不得默认接收完整 learner history；用户可查看、纠正、导出、删除其长期状态所依据证据，具体遵循 privacy/security contract。

## 10. Tests

### SYS03-240

测试 MUST 覆盖：

- independent vs assisted vs answer-exposed eligibility/weight；
- single immediate success 不直接 stable mastery；
- delayed/transfer evidence；
- answer-exposed success 不产生 independent mastery evidence；
- assisted success 不等于 validation complete；
- fresh independent Attempt 才能提供 independent validation evidence；
- low-confidence assessment conservative；
- duplicate evidence/event idempotency；
- invalidated evidence replay；
- learner dispute 不直接改概率；
- `learning_stage_summary` 不再作为 TeachingStage truth；
- MisconceptionEvidence→Hypothesis 需要 versioned inference；
- same evidence+algorithm replay deterministic；
- DKT/Deep KT challenger 无 canonical write；
- LLM/engagement/turn count 不能直接提升 mastery。

## 11. Acceptance Criteria

原有 AC 保留并按 v0.3 字段语义更新：

- `SYS03-AC-001`：任一 MasteryEstimate 可列出全部 source evidence ids 和算法版本。
- `SYS03-AC-002`：ASSISTED 与 INDEPENDENT success 产生不同 evidence eligibility/weight。
- `SYS03-AC-003`：ANSWER_EXPOSED success 不会产生 stable-mastery 高权独立证据。
- `SYS03-AC-004`：相同事件/evidence + exact algorithm/config 重放得到相同状态内容。
- `SYS03-AC-005`：Assessment 模块不能直接写 mastery repository。
- `SYS03-AC-006`：用户状态争议可触发复测/重算并保留审计记录。
- `SYS03-AC-007`：DKT/Deep KT challenger 失败不影响 canonical baseline 可用性。

新增 v0.3 AC：

- `SYS03-AC-201`：LearnerState 没有 persistent SYS05 TeachingStage truth。
- `SYS03-AC-202`：ANSWER_EXPOSED result 无法成为 independent mastery evidence。
- `SYS03-AC-203`：SYS03 不能在 fresh independent Attempt 前假定 validation obligation 完成。
- `SYS03-AC-204`：MisconceptionHypothesis 与 SYS04 MisconceptionEvidence 可独立审计。

## 12. Legacy Mapping

- `learning_stage_summary` → `learner_progress_summary` read migration；旧字段只作 legacy/audit。
- integer hint/scaffold/exposure → v0.3 orthogonal assistance snapshot；无法确定时标记 unavailable/uncertain。
- 历史 mastery 若依赖已失去版本的旧 weighting rule，replayability MUST 标记 partial/non-replayable。

Retirement condition：所有 active writers/readers 切至 v0.3 schema，旧记录已迁移或有明确 audit/replay status 后，legacy adapter SHOULD 删除。

## 13. Forbidden Implementations

禁止：

- `mastery = last_score`；
- 连续答对固定 N 次就无条件 stable mastery；
- LLM 输出 mastery_probability 直接入库；
- DKT/KT 各保存一套 canonical truth；
- 用户点赞/engagement/turn count 直接提高 mastery；
- replay 调用在线 LLM；
- SYS03 计算 next_due_at/LearningPlan/TeachingStage；
- answer-exposed correct 直接提升 stable mastery；
- `missing assistance = independent`；
- SYS03 预先完成 SYS05 validation obligation。