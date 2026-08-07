# SYS08 — AI Orchestration & Trust

> Spec ID：`SYS08-*`  
> 对应设计：4.8 LLM 生成、Agent 编排与可信控制  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS08-001

4.8 的唯一职责是把 4.1～4.7 已确定的业务对象、教学动作和证据可靠执行为用户交互，并统一管理 workflow、模型、工具、Prompt、安全、验证、降级、事件与审计。

一句话：**执行，而不是重新决定教学业务语义。**

### SYS08-002

普通、流式和 WebSocket 教学请求 MUST 最终经过同一 canonical orchestration path。

## 2. Non-responsibility

4.8 MUST NOT：

- 修改 LearnerState/MasteryEstimate；
- 重新评分 AssessmentResult；
- 修改 TeachingAction；
- 修改 LearningPlan；
- 修改 ReviewSchedule；
- 发布知识事实；
- 检索失败后用模型常识冒充资料证据；
- 让 autonomous Agent 成为超级业务决策层。

## 3. Owned State

4.8 独占：

```text
SessionState
WorkflowRun / WorkflowStep
ModelRoute
ModelInference
PromptTemplate/PromptVersion registry
ToolCall / ToolResult
ValidationResult
ExecutionPolicy
FeedbackSignal ledger
LearningEvent ledger persistence
DecisionTrace ledger persistence
telemetry/cost execution records
```

## 4. Inputs

允许输入：

- LearningActivity/Plan read-only；
- TeachingAction；
- EvidenceBundle；
- AssessmentItem / assessment command；
- ReviewSchedule display context；
- user messages/actions；
- model/tool availability；
- security/privacy policy。

### SYS08-010

业务对象必须以 immutable/versioned reference 注入 workflow；4.8 不得持有可写副本作为第二 truth。

## 5. Outputs

输出：

- validated learner-visible response；
- ModelInference；
- ToolCall/ToolResult；
- ValidationResult；
- LearningEvent/FeedbackSignal；
- execution trace；
- 结构化 execution failure 回到对应领域系统。

## 6. Domain Objects

公共对象遵循 `domain-model.md`、`event-contract.md`、`decision-contract.md`。

内部：

```text
WorkflowDefinition
WorkflowRun
WorkflowStep
ModelTaskProfile
ModelRoute
PromptTemplate
ToolDefinition
ToolAuthorization
OutputSchema
ValidationResult
```

### SYS08-020

`ModelInference` 与 `DecisionTrace` 必须分离：前者记录模型做了什么，后者记录领域系统最终接受了什么。

## 7. Commands

建议：

```text
ExecuteTeachingAction
ExecuteLearningActivity
PresentAssessmentItem
SubmitAssessmentResponse
ExecuteModelTask
ExecuteAuthorizedTool
ResumeWorkflowRun
CancelWorkflowRun
CaptureFeedback
AppendDomainEvent
AppendDecisionTrace
```

### SYS08-021

不得暴露 `UpdateMastery`、`RewriteLearningPlan`、`SetReviewSchedule` 等直接跨领域写命令。

## 8. Events

产生/托管：

- `EngineTransitioned`
- `ExplanationPresented`
- `HintRequested`
- `HintPresented`
- `ReflectionRecorded`
- 用户交互事实；
- 各领域提交的 LearningEvent；
- DecisionTrace ledger entry。

### SYS08-030

事件账本托管权不等于业务事件定义权；领域 owner 负责 payload 语义和必要验证。

## 9. Algorithms

### SYS08-040：MVP 主流程

```text
load immutable domain inputs
→ resolve fixed workflow version
→ authorize tools/data
→ resolve model route
→ build prompt/context
→ call model/tool
→ validate schema
→ validate domain execution policy
→ validate citations/exposure
→ bounded repair/retry/fallback
→ render
→ append events/traces
```

### SYS08-041：Model Router baseline

使用静态/启发式 route：

```text
capability fit
privacy eligibility
context window
model health
latency budget
cost budget
quality tier
```

不得让模型自己决定调用哪个未经授权模型/工具。

### SYS08-042：模型任务分层

推荐：

- 结构化抽取/分类 → 小型快速模型；
- 一般资料问答/讲解 → 中等模型 + EvidenceBundle；
- 复杂推理/开放反馈 → 强推理模型；
- embedding → 专用模型；
- 确定性计算/代码 → tool，不让 LLM 猜。

### SYS08-043：Output validation

必须按任务类型组合：

- JSON/schema；
- TeachingAction fidelity；
- answer exposure；
- citation faithfulness；
- tool args；
- safety/security；
- assessment-specific constraints。

Schema pass 不代表业务 pass。

### SYS08-044：Agent 边界

Agent MAY：

- 在已授权工具集合内完成受限研究；
- 在同一 TeachingAction 下生成多个表达候选；
- 执行复杂但无业务状态所有权的局部 workflow。

Agent MUST NOT：

- 改 mastery/plan/action/review；
- 开放任意 shell/network/file write；
- 绕过 tool authorization；
- 因检索失败自行切学习目标。

### SYS08-045：学习型路由

模型路由 MAY 未来从静态→监督 route predictor→安全 Contextual Bandit；通常不需要 RL。教学策略仍归 SYS05。

## 10. Persistence

### SYS08-050

WorkflowRun 必须固定：

- workflow version；
- TeachingAction id/version semantic reference；
- Prompt version；
- model route result；
- tool definitions/authorization version；
- input object versions。

### SYS08-051

关键 event/DecisionTrace 使用 durable local ledger/outbox。Redis/Kafka 不得成为唯一事实存储。

### SYS08-052

ModelInference 必须记录 provider/model/snapshot、prompt version、latency、usage、validation references 和 trace id。

### SYS08-053

敏感全文 Prompt/文档内容不得为了观测方便无限期复制到日志；保存最小可审计信息和受控 references。

## 11. Failure Semantics

必须区分：

- provider timeout/unavailable；
- model rate limit；
- structured output invalid；
- context overflow；
- citation unsupported；
- answer leakage violation；
- tool unauthorized；
- tool timeout/failure；
- workflow invariant violation；
- persistence/event delivery failure。

### SYS08-060：Retry

retry 必须 bounded；只有 transient error 自动重试。结构化错误可有限 repair。业务 policy violation 不得盲重试同一未变化 Prompt。

### SYS08-061：Fallback

fallback 只能改变**执行路径**，不能改变 TeachingAction 业务语义。

例如：

```text
model A unavailable → model B same capability/policy
```

允许；

```text
无法生成苏格拉底提问 → 直接给完整答案
```

禁止，除非 4.5 新建动作。

### SYS08-062：Side effect retry

有副作用工具必须有幂等 key/确认机制，避免重复发送/写入。

### SYS08-063：事件持久化失败

对会影响后续学习状态的关键交互，若无法可靠写入事件账本，系统 MUST 标记 workflow degraded/failed，不得假装已完成可追踪学习闭环。

## 12. Idempotency

- WorkflowRun command 有 idempotency key；
- ToolCall side effects 幂等；
- Append event/decision 按 id 唯一；
- streaming reconnect 不重复产生用户/assistant 学习事件；
- resume 不重复完成已成功 step。

## 13. Observability

必须提供 correlation/trace spanning：

```text
API request
→ orchestration run
→ TeachingAction
→ retrieval request
→ model/tool call
→ validation
→ rendered response
→ Attempt/event
```

指标至少：

- p50/p95 latency；
- model/tool failure；
- fallback rate；
- schema pass；
- citation precision/unsupported claim；
- answer leakage；
- prompt injection block；
- workflow resume success；
- event delivery lag；
- cost/session/task；
- route distribution。

## 14. Security

### SYS08-070：Tool allowlist + least privilege

工具必须 registry/schema/allowlist；模型不可自行创建工具名或扩大权限。

### SYS08-071：Untrusted content boundary

用户文档、网页、检索结果、tool output 都是 untrusted data。它们的指令不能覆盖 system policy、TeachingAction 或 tool permissions。

### SYS08-072：External processing

发送给外部模型前必须遵循 privacy classification、provider policy 和最小必要上下文。密钥不得进入 model prompt。

### SYS08-073：Citation guard

资料型陈述必须与 EvidenceBundle 对齐；不支持的断言应删除、降级为模型通用知识并标示，或声明无法确认。

### SYS08-074：Answer exposure guard

最终输出 exposure 必须 `<= TeachingAction.answer_exposure_max`。检索/模型都不得突破。

## 15. Tests

必须覆盖：

- normal + streaming 同 canonical orchestrator；
- provider timeout fallback；
- invalid structured output bounded repair；
- context overflow；
- tool deny；
- prompt injection from document/tool output；
- hallucinated tool args；
- citation unsupported output blocked/repaired；
- answer leakage blocked；
- streaming reconnect idempotency；
- workflow resume；
- side-effect retry no duplicate；
- event ledger failure visible；
- LLM 输出 mastery/plan/review fields 无法写 canonical state。

至少一个 E2E test MUST 使用已配置真实模型验证 provider/gateway/orchestration 可用性；Mock-only 不得作为“真实模型已接通”的验收。

## 16. Acceptance Criteria

- `SYS08-AC-001`：普通与流式请求走同一 orchestrator 业务主链路。
- `SYS08-AC-002`：模型/工具 fallback 不改变 TeachingAction 语义。
- `SYS08-AC-003`：LLM 无任何直接写 mastery/plan/review/knowledge truth 的路径。
- `SYS08-AC-004`：Prompt、model、tool、workflow 版本可追踪。
- `SYS08-AC-005`：资料回答的引用能映射 EvidenceBundle→SourceSpan。
- `SYS08-AC-006`：恶意检索内容不能触发未授权工具或改变策略。
- `SYS08-AC-007`：应用重启后持久化 workflow/task 能恢复或明确失败。
- `SYS08-AC-008`：关键事件账本写入失败不会被静默忽略。
- `SYS08-AC-009`：真实 E2E 至少一次通过实际配置模型，不以 Mock 替代。

## 17. Forbidden Implementations

禁止：

- 一个 autonomous TutorAgent 同时拥有所有八类决策；
- 开放任意 shell/network/file write 给模型；
- 将 system prompt 作为唯一安全边界；
- 模型返回 `mastery=1` 后 orchestrator 直接 UPDATE；
- 检索失败后模型用常识伪装资料答案；
- fallback 自动给更高答案暴露；
- 无限 Agent loop/retry；
- 普通聊天接口绕过 orchestrator；
- Redis/Kafka 作为唯一不可恢复业务事实源；
- 日志保存密钥或无限期保存全部敏感 Prompt。

## Legacy Mapping

当前主要相关：

```text
apps/backend/app/engines/orchestrator.py
apps/backend/app/engines/*_engine.py
apps/backend/app/engines/socratic_adapter.py
apps/backend/app/engines/socratic/response_generator.py
apps/backend/app/engines/socratic/output_guardrail.py
apps/backend/app/services/dialog/
apps/backend/app/services/llm/model_router.py
apps/backend/app/workers/
apps/backend/app/api/v1/dialog.py
apps/backend/app/api/v1/orchestrator.py
apps/backend/app/api/v1/ws.py
```

迁移第一目标是消除默认 direct dialog/Socratic path 与 orchestrator path 的双主链路。
