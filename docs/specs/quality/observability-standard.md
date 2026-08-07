# Askora Observability Standard

> Spec ID：`OBS-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 原则

### OBS-001

任何关键学习结果必须能够从用户请求追踪到领域决策、检索/模型/工具执行、AssessmentResult、LearnerEvidence 和状态更新。

### OBS-002

日志、指标、trace 是观测投影，不得成为业务事实源。

## 2. Correlation

每个教学轮次必须传播：

```text
request_id
correlation_id
trace_id
session_id
workflow_run_id
```

关键 domain object/decision/event 应关联 correlation/trace。

## 3. Structured Logging

日志至少包含：timestamp、level、component/system、event/error code、trace/correlation、object ids/versions（适用时）。

不得默认记录：密码、token、API key、完整敏感文档、完整用户隐私 Prompt。

## 4. Decision Observability

所有 `DecisionTrace` 按 `decision-contract.md` 持久化。用户解释不能只依赖运行时自然语言日志。

## 5. Model Observability

`ModelInference` 至少记录：provider/model/snapshot、task、prompt version、latency、usage、fallback、validation result、error code。

## 6. Retrieval Observability

必须可查看：candidate routes/ranks、filters、selected evidence、index versions、citation validation、leakage reason。

## 7. Learning Observability

必须可查看：

- Attempt assistance state；
- AssessmentResult；
- EvidenceAccepted/Rejected；
- Mastery prior/new version；
- Review prior/new schedule；
- Plan/TeachingAction reason codes。

## 8. 核心指标

系统指标：availability、p95 latency、error/fallback、queue lag、restart recovery。

AI 指标：model failure、schema fail、citation unsupported、answer leakage、tool denial、cost。

学习指标：independent success、hint dependency、delayed retention、transfer success、false mastery promotion、misconception recurrence。

### OBS-010

聊天时长、token 数、点赞只能作为体验/成本指标，不得作为主要学习效果指标。

## 9. Privacy

Telemetry 必须按 privacy classification 最小化采集。若 raw content 对问题诊断不是必要项，优先保存 hash/reference/结构化 reason code。

## 10. Health

至少区分：

- liveness；
- database readiness；
- durable queue/outbox health；
- configured model availability（可单独 degraded）；
- index freshness。

模型 unavailable 不一定意味着整个本地应用不可启动。

## 11. Acceptance Criteria

- `OBS-AC-001`：任一 TeachingAction 可通过 trace 找到执行模型与最终 response。
- `OBS-AC-002`：任一 MasteryEstimate 可找到 source AssessmentResult/LearnerEvidence。
- `OBS-AC-003`：fallback/repair 可区分并可统计。
- `OBS-AC-004`：日志扫描不包含测试密钥/认证 token。
- `OBS-AC-005`：queue/outbox lag 和 failure 可观测。

## 12. Forbidden Implementations

禁止：

- 只有自由文本日志，无稳定 event/reason code；
- 把完整敏感 Prompt 当默认日志字段；
- 没有 trace 关联的模型调用；
- 仅统计 engagement 而不统计学习结果和可信指标。
