# Observability Standard

> Spec ID：`OBS-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Purpose

Observability MUST 支持三类问题：系统是否正确执行、policy 为什么这样决定、学习结果后来发生了什么。三者 MUST 通过 correlation refs 连接，但不得混成同一事实。

### OBS-001

关键链路 SHOULD 可关联：request/session → TeachingContext → TeachingAction → DecisionTrace → EvidenceBundle → SYS08 execution → Attempt/AssessmentResult → LearnerEvidence/MasteryEstimate → OutcomeObservation/ExperimentAssignment。

## 2. Decision vs Outcome

### OBS-200

`DecisionTrace` 只回答 decision-time reasoning；`OutcomeObservation` 只回答 later measurement。Outcome MUST NOT 回写修改历史 DecisionTrace。

### OBS-201

Delayed outcome MUST NOT 自动 last-touch attribution 给最后一个 TeachingAction。Attribution scope 仅允许：

```text
ACTION_DIRECT
EPISODE_ASSOCIATED
TRAJECTORY_ASSOCIATED
EXPERIMENTALLY_CAUSAL
UNATTRIBUTABLE
```

只有满足实验识别条件时才可使用 `EXPERIMENTALLY_CAUSAL`。

## 3. Outcome Hierarchy

### OBS-210 — Primary Learning Outcomes

v0.3 primary learning outcomes：

```text
no-hint independent success
delayed independent performance
independent transfer
unit-time capability gain
```

实现 MUST 能从实际 assistance/exposure、delay、transfer novelty、measurement refs 与 active learning time 计算/聚合这些指标，而不是从聊天表象推断。

### OBS-211 — Secondary Learning Outcomes

Secondary MAY 包括：近迁移/解释质量、不同能力维度改善、独立成功率的稳定性、误区消退等；必须明确 measurement definition/version，不得与 primary 混名。

### OBS-212 — Process Diagnostics

Process diagnostics MAY 包括：engagement、conversation turns、likes、hint count、token count、session duration、candidate distribution、transition rate、latency/cost、retrieval metrics。

这些指标 MUST NOT 被标记为 primary learning outcome/reward，也 MUST NOT 单独用于宣称学习效果。

### OBS-213 — Safety / Trust Guardrails

至少 SHOULD 观测：forbidden-action rate、answer leakage、assessment integrity violation、hard-rule conflict、policy bypass attempt、prompt injection/tool authorization failure、trace persistence failure、replayability、learning-harm indicators。

## 4. OutcomeObservation Contract

### OBS-220

OutcomeObservation 至少 MUST 支持：

```text
outcome_type
measurement_reference
independence
assistance_state
scaffold_control
hint_specificity
answer_exposure
actual_delay
transfer_distance / novelty
score / success
measurement_confidence
active_learning_time
time_cost
hint_cost
contamination_status
attribution_scope
teaching_episode_ref
learning_trajectory_ref
experiment_association
```

### OBS-221

Measurement/confidence/contamination MUST 随 observation 保存。缺失值使用 explicit missing semantics；MUST NOT 用 0 伪装 missing。

## 5. Teaching Policy Observability

### OBS-230

每个 SYS05 decision SHOULD 暴露/记录：context fingerprint、exact source versions、PolicyBundle ref/hash、TeachingStage、available/filtered candidates + reason codes、feature values/availability/confidence/version、scores、material evidence、anti-oscillation decision、tie-break reason、selected/previous action、validation obligation、experiment assignment、replayability。

### OBS-231

B3 MUST 可审计：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

ExperimentAssignment `assignment_probability` MUST 作为独立字段观测，不得复用 action propensity 名义。

## 6. TeachingEpisode / LearningTrajectory

### OBS-240

TeachingEpisode/Trajectory MAY 用于聚合跨动作 outcome，但它们是 grouping/analytics references，不是新 TeachingAction/LearnerState owner。

### OBS-241

Trajectory outcome 的 association MUST 保留 attribution uncertainty。MUST NOT 因某 action 时间上最近就自动获得因果归因。

## 7. Engineering Metrics

### OBS-010

系统层至少 SHOULD 覆盖 latency、error/retry/fallback、queue/outbox lag、cache/index health、model/tool availability/cost、schema validation、persistence conflict、recovery success。

### OBS-011

指标/日志必须具有足够 labels 连接版本，但 MUST 避免高基数敏感全文作为标签。

## 8. Privacy / Security

### OBS-020

Logs/traces MUST 数据最小化。密钥、完整敏感 Prompt、整份用户文档、无需长期保存的原始回答 MUST NOT 为 observability 无限复制。

### OBS-021

需要 debug 的敏感内容 SHOULD 通过受控 reference、短期 retention 或授权 sampling，而不是永久明文日志。

## 9. Alerting

### OBS-250

至少应为以下条件建立 release/runtime guard/alert：forbidden action > 0、assessment leakage、hard-rule bypass、trace persistence failure、event/outbox backlog、unexpected non-null deterministic action_propensity、illegal oscillation/no-progress loop、cross-owner write violation。

## 10. Tests

测试 MUST 覆盖：DecisionTrace/Outcome separation；primary vs process metric classification；delayed outcome no last-touch；attribution enum；actual assistance/exposure observability；deterministic probability fields；trace correlation；missing semantics；privacy redaction。

## 11. Acceptance Criteria

- `OBS-AC-201`：四类 primary learning outcome 可从可审计 measurement/event refs 计算。
- `OBS-AC-202`：engagement/turns/likes/hint/token/session duration 不会进入 primary learning outcome/reward。
- `OBS-AC-203`：OutcomeObservation 不修改 DecisionTrace。
- `OBS-AC-204`：delayed outcome 不自动 last-touch attribution。
- `OBS-AC-205`：deterministic B3 可检测任何非 null `action_propensity` 异常。
- `OBS-AC-206`：SYS05 decision 可关联 exact context/bundle 与后续 outcome，而不混淆 ownership。

## 12. Forbidden Implementations

禁止：

- engagement、对话轮次、点赞、hint count、token count、session duration 作为主要 learning outcome/reward；
- delayed outcome 自动归因最后 action；
- analytics grouping object 取得 domain ownership；
- Outcome 回写 DecisionTrace；
- deterministic action_propensity 写 1.0；
- 为观测方便永久保存全部敏感 Prompt/文档；
- 用 Engineering Correct 指标替代 learning efficacy evidence。