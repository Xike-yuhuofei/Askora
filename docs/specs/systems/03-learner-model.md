# SYS03 — Learner Model

> Spec ID：`SYS03-*`  
> 对应设计：4.3 学习者建模与状态估计  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS03-001

SYS03 是 `LearnerEvidence`、`MasteryEstimate`、`LearnerState` 与 `MisconceptionHypothesis` 的唯一 owner。它把已发生且可审计的学习证据投影为学习者状态估计。

### SYS03-002

SYS03 MUST NOT：判分 AssessmentResult、选择 TeachingAction、拥有 TeachingStage、修改 LearningPlan/ReviewSchedule、把 LLM 自评直接写成 mastery truth。

## 2. Input Boundary

SYS03 MAY 读取：AssessmentResult/Attempt、实际 assistance/exposure、delayed/transfer evidence、SYS01 misconception definition、Review evidence、用户纠错/反馈的明确 adapter 输出。

### SYS03-010

只有通过 evidence eligibility 规则的事实才能进入 LearnerEvidence。聊天文本、LLM 语言判断、点赞、对话轮次 MUST NOT 直接成为高权 mastery evidence。

### SYS03-200 — Assistance-aware Evidence

Evidence eligibility/weight MUST 基于 SYS04 的实际：

```text
assistance_state
scaffold_control
hint_specificity
answer_exposure
```

不得基于 SYS05 的 allowed envelope 假定实际经历，也不得继续依赖全局 integer `hint_level/scaffold_level/answer_exposure_max` 作为 canonical 语义。

### SYS03-201 — Independence Rules

`ANSWER_EXPOSED` success MUST NOT 成为 independent mastery evidence；`ASSISTED` success MUST 与 independent evidence 分离并按 versioned rules 降权/限制用途。只有 fresh `INDEPENDENT` Attempt 可形成新的 independent success evidence。

## 3. Misconception Boundary

### SYS03-210

边界固定：

```text
Misconception definition      → SYS01
MisconceptionEvidence         → SYS04
MisconceptionHypothesis       → SYS03
Remediation decision          → SYS05
```

SYS03 MAY 根据多个 evidence 更新 hypothesis/confidence，但 MUST NOT 把单个 SYS04 evidence 无条件提升为 confirmed learner misconception。

## 4. LearnerState vs TeachingStage

### SYS03-220

`TeachingStage` 属于 SYS05 对当前 TeachingContext 的派生控制语义，MUST NOT 存入 LearnerState 作为 persistent learner stage。

历史 `LearnerState.learning_stage_summary` 在 v0.3 MUST 迁移/重命名为 `learner_progress_summary` 或等价非教学策略摘要，并 MUST 明确与 SYS05 TeachingStage 没有 ownership/inheritance 关系。

## 5. Independent Validation Boundary

### SYS03-230

`INDEPENDENT_VALIDATION_REQUIRED` 是 SYS05 policy-control obligation，不是 MasteryState。SYS03 MUST NOT 创建、完成或清除该 obligation。

### SYS03-231

在 fresh independent Attempt 实际发生并被 SYS04 接纳前，SYS03 MUST NOT 因“已安排独立验证”“时间已过去”或“LLM 判断会做”而假定 obligation 已完成。

## 6. Projection & Algorithms

### SYS03-020

MVP MAY 使用透明、可解释、可版本化的 evidence-weighted projection；Deep KT/DKT/AKT MUST NOT 成为 v0.3 canonical truth。

### SYS03-021

MasteryEstimate MUST 保存 algorithm/version/source_evidence_ids/confidence。`competence_probability` 是模型估计，不是真实概率宣称。

### SYS03-022

稳定掌握标签 SHOULD 同时考虑独立成功、证据数量/质量、延迟保持、迁移、活跃误区与不确定性，不能只用一个概率阈值。

### SYS03-023

mastery threshold、evidence weights、hint dependency weighting、delay/transfer qualification 等参数 MUST versioned/traceable，MUST NOT 写成不可变科学常数。

## 7. Persistence / Replay

### SYS03-030

LearnerEvidence SHOULD immutable；新的状态计算产生新 MasteryEstimate/LearnerState version。历史结果/证据更正 MUST 通过 supersede/reprojection，而非原地改历史审计记录。

### SYS03-031

相同 ordered evidence set + exact algorithm bundle MUST 重放得到相同 semantic projection。缺失历史版本时 MUST 显式返回 partial/non-replayable，不得使用当前算法伪装历史 replay。

## 8. Failure Semantics

必须区分：evidence ineligible、assistance unknown、source result superseded、algorithm unavailable、projection failure、insufficient evidence、state version conflict。

### SYS03-040

assistance/exposure 不可确定时 MUST conservative：降低 eligibility/weight 或标记 uncertain；MUST NOT 默认 independent。

## 9. Observability

必须记录 evidence acceptance/rejection reason、assistance snapshot refs、algorithm/version、old/new estimate refs、misconception hypothesis updates、confidence 与 reprojection reason。

## 10. Tests

### SYS03-240

测试 MUST 覆盖：

- independent/assisted/answer-exposed eligibility；
- answer-exposed success 不产生 independent mastery evidence；
- assisted success 不等于 validation complete；
- fresh independent Attempt 才能提供 independent validation evidence；
- `learning_stage_summary` 不再作为 TeachingStage truth；
- MisconceptionEvidence→Hypothesis 需要 versioned inference；
- same evidence+algorithm replay deterministic；
- missing assistance fail conservative；
- LLM/engagement/turn count 不能直接提升 mastery。

## 11. Acceptance Criteria

- `SYS03-AC-201`：LearnerState 没有 persistent SYS05 TeachingStage truth。
- `SYS03-AC-202`：ANSWER_EXPOSED result 无法成为 independent mastery evidence。
- `SYS03-AC-203`：SYS03 不能在 fresh independent Attempt 前假定 validation obligation 完成。
- `SYS03-AC-204`：每个 MasteryEstimate 可追溯 exact evidence 与 algorithm bundle。
- `SYS03-AC-205`：MisconceptionHypothesis 与 SYS04 MisconceptionEvidence 可独立审计。

## 12. Legacy Mapping

- `learning_stage_summary` → `learner_progress_summary` read migration；旧字段只作 legacy/audit。
- integer hint/scaffold/exposure → v0.3 orthogonal assistance snapshot；无法确定时标记 unavailable/uncertain。
- 历史 mastery 若依赖已失去版本的旧 weighting rule，replayability MUST 标为 partial/non-replayable。

Retirement condition：所有 active writers/readers 切至 v0.3 schema，旧记录已迁移或有明确 audit/replay status 后，legacy adapter SHOULD 删除。

## 13. Forbidden Implementations

禁止：

- SYS03 判分或选择 TeachingAction；
- TeachingStage 持久化为 learner truth；
- answer-exposed correct 直接提升 stable mastery；
- `missing assistance = independent`；
- DKT/AKT/Deep KT 作为 v0.3 canonical truth；
- LLM 自述/engagement/likes/token count 直接作为 mastery truth；
- SYS03 预先完成 SYS05 validation obligation。