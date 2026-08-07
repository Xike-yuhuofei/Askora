# Askora Observability Standard

> Spec ID：`OBS-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Existing Observability Contracts Retained

### OBS-001 — End-to-end Traceability

任何关键学习结果 MUST 能从用户请求追踪到领域决策、retrieval/model/tool execution、AssessmentResult、LearnerEvidence/state update，并在 v0.3 有 OutcomeObservation 时继续关联 outcome/experiment refs。

### OBS-002 — Observability Is Not Truth

Logs、metrics、traces 是观测/审计投影，MUST NOT 成为业务事实源。

### OBS-010 — Process Metrics Are Not Primary Learning Outcomes

聊天时长、token 数、点赞只能作为体验/成本/process metrics，MUST NOT 作为主要 learning outcome/reward。v0.3 同样适用于 conversation turns、hint count、session duration 与 engagement。

## 2. Correlation / Logging Baseline

每个教学 round SHOULD 传播 request_id、correlation_id、trace_id、session_id、workflow_run_id；关键 domain object/DecisionTrace/Event/Outcome SHOULD 可关联。

Structured logs 至少 SHOULD 包含 timestamp、level、component/system、event/error code、trace/correlation、object ids/versions。MUST NOT 默认记录 password、token、API key、完整敏感文档或完整 privacy-sensitive Prompt。

DecisionTrace 按 `decision-contract.md`；ModelInference 至少记录 provider/model/snapshot、task、prompt version、latency、usage、fallback、validation、error；retrieval observability 必须包含 candidates/routes/ranks/filters/selected evidence/index versions/citation validation/leakage reason。

## 3. v0.3 Decision vs Outcome

### OBS-200

`DecisionTrace = decision-time reasoning`；`OutcomeObservation = later measurement`。Outcome MUST NOT 回写历史 DecisionTrace。

### OBS-201 — Attribution

Delayed outcome MUST NOT 自动 last-touch attribution 给最后一个 TeachingAction。Attribution scope 仅允许：

```text
ACTION_DIRECT
EPISODE_ASSOCIATED
TRAJECTORY_ASSOCIATED
EXPERIMENTALLY_CAUSAL
UNATTRIBUTABLE
```

只有满足实验识别条件时 MAY 使用 `EXPERIMENTALLY_CAUSAL`。

## 4. Outcome Hierarchy

### OBS-210 — Primary Learning Outcomes

v0.3 primary learning outcomes：

```text
no-hint independent success
delayed independent performance
independent transfer
unit-time capability gain
```

实现 MUST 能从 actual assistance/exposure、delay、transfer novelty、measurement refs 与 active learning time 计算/聚合，而不是从聊天表象推断。

### OBS-211 — Secondary Learning Outcomes

Secondary MAY 包含 near-transfer/explanation quality、不同 capability dimension improvement、independent success stability、misconception recurrence/decay 等；必须固定 measurement definition/version。

### OBS-212 — Process Diagnostics

Engagement、conversation turns、likes、hint count、token count、session duration、candidate distribution、transition rate、latency/cost、retrieval metrics 均属于 process/experience diagnostics；MUST NOT 标记为 primary learning outcome/reward。

### OBS-213 — Safety / Trust Guardrails

至少 SHOULD 观测 forbidden-action rate、answer leakage、assessment integrity violation、hard-rule conflict、policy bypass attempt、prompt-injection/tool-authorization failure、trace persistence failure、replayability 与 learning-harm indicators。

## 5. OutcomeObservation Contract

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

### OBS-221 — Missing / Confidence

Measurement confidence、contamination、missing status MUST 与 observation 一起保存；`MISSING` MUST NOT 伪装成 0。

## 6. Teaching Policy Observability

### OBS-230

每个 SYS05 decision SHOULD 记录 context fingerprint/exact source versions、PolicyBundle ref/hash、TeachingStage、available/filtered candidates + reasons、feature value/availability/confidence/version、scores、material evidence、anti-oscillation、tie-break、selected/previous action、validation obligation、ExperimentAssignment 与 replayability。

### OBS-231 — Probability Observability

B3 MUST 可审计：

```text
behavior_policy_type = DETERMINISTIC
action_propensity = null
```

ExperimentAssignment `assignment_probability` MUST 独立观测，MUST NOT 复用 action propensity 名义。

## 7. TeachingEpisode / LearningTrajectory

### OBS-240

TeachingEpisode/Trajectory MAY 聚合跨 action outcomes，但只是 grouping/analytics refs，不是新 TeachingAction/LearnerState owner。

### OBS-241

Trajectory association MUST 保留 attribution uncertainty。时间上最近的 action MUST NOT 自动获得 causal attribution。

## 8. Engineering / AI / Learning Observability

系统指标 SHOULD 包括 availability、p95 latency、error/fallback、queue/outbox lag、restart recovery、cache/index health、persistence conflict；AI 指标包括 model/tool failure、schema fail、citation unsupported、answer leakage、tool denial、cost。

学习 observability SHOULD 包括 Attempt actual assistance、AssessmentResult/diagnosis confidence、EvidenceAccepted/Rejected、Mastery prior/new version、Review prior/new schedule、Plan/TeachingAction reasons 与 primary/secondary OutcomeObservation。

## 9. Privacy / Health

Telemetry MUST 按 privacy classification 最小化采集；raw content 非必要时优先 hash/reference/reason code。Health 至少区分 liveness、DB readiness、durable queue/outbox、configured model availability（可 degraded）、index freshness。

## 10. Alerts

### OBS-250

至少 SHOULD 对 forbidden action > 0、assessment leakage、hard-rule bypass、trace persistence failure、outbox backlog、deterministic non-null action_propensity、illegal oscillation/no-progress loop、cross-owner write violation 建 alert/release guard。

## 11. Tests

测试 MUST 覆盖 DecisionTrace/Outcome separation；primary vs process metric classification；delayed outcome no last-touch；attribution enum；actual assistance/exposure observability；deterministic probability fields；trace correlation；missing semantics；privacy redaction。

## 12. Acceptance Criteria

原有 AC 保留：

- `OBS-AC-001`：任一 TeachingAction 可通过 trace 找到执行模型与最终 response。
- `OBS-AC-002`：任一 MasteryEstimate 可找到 source AssessmentResult/LearnerEvidence。
- `OBS-AC-003`：fallback/repair 可区分并可统计。
- `OBS-AC-004`：日志扫描不包含测试 secret/token。
- `OBS-AC-005`：queue/outbox lag/failure 可观测。

新增 v0.3 AC：

- `OBS-AC-201`：四类 primary learning outcome 可从审计 measurement/event refs 计算。
- `OBS-AC-202`：process metrics 不进入 primary learning outcome/reward。
- `OBS-AC-203`：OutcomeObservation 不修改 DecisionTrace。
- `OBS-AC-204`：delayed outcome 不自动 last-touch attribution。
- `OBS-AC-205`：deterministic B3 可检测任何 non-null `action_propensity` 异常。
- `OBS-AC-206`：SYS05 decision 可关联 exact context/bundle 与后续 outcome，而不混淆 ownership。

## 13. Forbidden Implementations

禁止：只有自由文本日志无 stable code；默认记录完整敏感 Prompt；无 trace 的模型调用；只统计 engagement 不统计学习/可信指标；engagement/turns/likes/hint/token/session 作为主要 learning outcome/reward；delayed outcome 自动归因最后 action；analytics grouping 取得 domain ownership；Outcome 回写 DecisionTrace；deterministic action_propensity=1.0；Engineering Correct 指标替代 learning efficacy。