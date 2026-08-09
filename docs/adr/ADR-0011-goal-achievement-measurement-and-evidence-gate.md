# ADR-0011 — Goal Achievement Measurement and Evidence Gate

> Status: Accepted
> Date: 2026-08-09
> Decision authority: user-delegated Codex

## Context

现有 goal 可显示 `achieved`，但没有 criterion-specific measurement、accepted evidence 与用户最终
确认门禁。直接以计划完成或模型评分宣布达成会越过 SYS04/SYS03 ownership。

## Decision

1. `LearningObjectiveV1` 将 criterion id、认知类型、target refs 和 evidence requirements 结构化。
2. versioned `GoalAchievementPolicyV1` 冻结 delay、novelty、rubric、confidence 和 reviewer 参数；
   这些是产品参数，不宣称普适科学常数。
3. SYS06 创建 criterion-specific AssessmentActivity；SYS04 对 exact/numeric/structured 优先确定性
   评分，开放题使用 rubric/source/schema-bound grader 并独立复核。
4. 低置信、grader 分歧、provider failure 或 Prompt Injection 风险进入
   `needs_review/scoring_failed`，不得成为 learner failure。SYS03 只接纳 accepted result。
5. `GoalAchievementEvaluationV1` 逐 criterion 引用 exact accepted evidence。全部满足、无未完成独立
   验证义务、无相关 active misconception 后，用户才可确认 `active → achieved`。
6. pause/resume/archive/copy 均写 append-only Goal/Plan state。archive/achieved 为终态；恢复输入过期
   时保持 paused 并要求 P1-01A replan。

## Alternatives

- activity/plan 完成即 achieved：拒绝，任务完成不等于能力证据。
- 单次 LLM 打分：拒绝，无法满足 grader independence 与 fail-closed。
- 自动 achievement：拒绝，最终状态必须由用户在证据门禁后确认。

## Claim boundary

Goal achieved 只表示该个人目标在指定 policy 版本下满足；不等于一般化 mastery、产品学习效果或
真人因果证据。Learning Evidence Gate 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
