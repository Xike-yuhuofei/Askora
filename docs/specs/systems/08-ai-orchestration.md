# SYS08 — AI Orchestration & Trust

> Spec ID：`SYS08-*`  
> 对应设计：4.8 LLM 生成、Agent 编排与可信控制  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS08-001

SYS08 的唯一职责是把 SYS01～SYS07 已确定的业务对象、TeachingAction 与 EvidenceBundle 可靠执行为用户交互，并统一管理 workflow、模型、工具、Prompt、安全、验证、降级、事件与审计。

一句话：**执行，而不是重新决定教学业务语义。**

### SYS08-002

普通、流式和 WebSocket 教学请求 MUST 最终经过同一 canonical orchestration path。

## 2. Non-responsibility

SYS08 MUST NOT：

- 修改 LearnerState/MasteryEstimate；
- 重新评分 AssessmentResult；
- 拥有或改写 TeachingAction；
- 修改 LearningPlan/ReviewSchedule；
- 发布知识事实；
- override SYS05 hard rule；
- 扩大 scaffold/hint/answer exposure envelope；
- 让 autonomous Agent 成为超级业务决策层。

## 3. Owned / Hosted Records

SYS08 独占 execution-state：SessionState、WorkflowRun/Step、ModelRoute/Inference、Prompt registry、ToolCall/Result、ValidationResult、ExecutionPolicy 与 telemetry/cost records。

SYS08 MAY 托管 durable LearningEvent/DecisionTrace/OutcomeObservation/ExperimentAssignment ledger persistence，但 **ledger hosting != domain truth ownership**；payload 语义仍由对应领域 owner/contract 定义。

### SYS08-010

业务对象必须以 immutable/versioned reference 注入 workflow；SYS08 MUST NOT 持有可写副本作为第二 truth。

## 4. TeachingAction Execution Envelope

### SYS08-200 — Tightening-only Rule

SYS08 MUST 在 TeachingAction 的 canonical envelope 内执行：

```text
scaffold_control
hint_specificity
answer_exposure
InteractionMove / ActionModifier semantics
```

SYS08 MAY 因安全、证据不足、模型能力或输出验证收紧 envelope；MUST NOT 扩大 scaffold、hint specificity、answer exposure，也 MUST NOT 将一个 InteractionMove/StrategyFamily 改成另一教学语义。

### SYS08-201 — No Semantic Recovery

若模型/工具不能在 envelope 内完成动作，SYS08 MUST 返回结构化 execution failure 给 SYS05 重新决策。MUST NOT 通过“给更多提示/直接答案/换策略”自行恢复。

### SYS08-202 — Actual Experience

SYS08 MUST 将实际展示的 support/hint/exposure 事件提交给 SYS04/事件账本，使 Attempt 能记录实际经历；不得只记录计划 envelope。

## 5. Canonical Workflow

### SYS08-040

```text
load immutable domain inputs
→ resolve fixed workflow version
→ authorize tools/data
→ resolve model route
→ build prompt/context
→ call model/tool
→ validate schema
→ validate TeachingAction fidelity
→ validate citations + scaffold/hint/exposure envelope
→ bounded repair/retry/fallback
→ render
→ append actual-experience events/traces
```

### SYS08-041

Model routing MAY 基于 capability、privacy、context、health、latency、cost、quality tier；模型 MUST NOT 自行选择未经授权的模型/工具。

### SYS08-042

确定性计算/代码 SHOULD 使用 tool；结构化抽取/分类、一般讲解、复杂推理 MAY 使用不同模型层级，但 route MUST NOT 改变 TeachingAction 语义。

### SYS08-043

Output validation 至少 SHOULD 组合 JSON/schema、TeachingAction fidelity、scaffold/hint/exposure、citation faithfulness、tool args、safety/security、assessment constraints。Schema pass 不等于 business pass。

### SYS08-044

Agent MAY 在授权工具内完成局部 workflow、生成同一 TeachingAction 的表达候选；MUST NOT 修改 mastery/plan/action/review、绕过 authorization 或因检索失败自行切换目标。

## 6. LLM Boundary

### SYS08-210

LLM/Agent MAY 负责 explanation、worked example、hint、diagnostic candidate、feedback、self-explanation prompt、language realization 与 tool execution。

LLM/Agent MUST NOT 成为 LearnerState owner、Assessment truth owner、TeachingAction owner、LearningPlan owner、ReviewSchedule owner、hard-rule override 或 answer-exposure override。

### SYS08-211

LLM 输出包含 `mastery`、`strategy`、`next_action`、更高 exposure 等字段时，只能作为未受信 candidate/invalid output；不得直接写 canonical state 或扩大 action envelope。

## 7. Persistence / Replay

### SYS08-050

WorkflowRun MUST 固定 workflow version、TeachingAction id/schema semantic ref、PolicyBundle ref（若可用）、Prompt version、model route、tool authorization version 与 input object versions。

### SYS08-051

关键 event/DecisionTrace 使用 durable local ledger/outbox；Redis/Kafka MUST NOT 是唯一事实存储。

### SYS08-052

ModelInference MUST 记录 provider/model/snapshot、prompt version、latency、usage、validation refs 与 trace id。

### SYS08-212 — Policy Replay Boundary

SYS08 MUST NOT 在 DecisionTrace replay 中重新调用在线 LLM 来重建 SYS05 决策。历史 replay 只能使用已固定 TeachingContext、PolicyBundle、action/trace refs；模型调用仅属于 execution replay/fixture 的独立层。

## 8. Failure Semantics

必须区分 provider timeout/unavailable、rate limit、structured output invalid、context overflow、citation unsupported、envelope violation、tool unauthorized/failure、workflow invariant violation、persistence/event delivery failure。

### SYS08-060

Retry MUST bounded；transient error MAY 自动重试。业务 policy/envelope violation MUST NOT 通过无限重试同一 Prompt 解决。

### SYS08-061

Fallback 只能改变 execution path，不得改变 TeachingAction 业务语义。例如 model A→model B 同能力可允许；无法生成 bounded SOCRATIC_PROBE 后直接给 COMPLETE answer 禁止，除非 SYS05 产生新 action。

### SYS08-063

影响后续学习状态的关键交互若无法可靠写入事件账本，workflow MUST degraded/failed；不得假装闭环已完成。

## 9. Observability

trace MUST 覆盖：API request → WorkflowRun → TeachingAction → retrieval → model/tool → validation → rendered response → actual assistance/exposure → Attempt/event。

至少记录 action envelope、实际 envelope、tightening reason、violation/block、model/tool versions、citation、fallback、event delivery、cost/latency。

## 10. Security

### SYS08-070

Tools MUST registry/schema/allowlist + least privilege；模型不可创建未授权工具或扩大权限。

### SYS08-071

用户文档、网页、retrieval/tool output 均为 untrusted data，其指令 MUST NOT 覆盖 system policy、TeachingAction、hard constraints 或 tool permissions。

### SYS08-074 — v0.3 Envelope Guard

最终输出 MUST 满足：

```text
actual_scaffold_control <= allowed scaffold envelope
actual_hint_specificity <= allowed hint envelope
actual_answer_exposure <= allowed answer exposure envelope
```

具体偏序/可比规则 MUST versioned；无法比较时 MUST fail conservative。旧 `answer_exposure_max` MUST NOT 作为 canonical writer contract。

## 11. Tests

必须覆盖：normal/streaming 同主链；provider fallback；invalid output bounded repair；tool deny；prompt injection；citation unsupported；tightening-only；attempted scaffold/hint/exposure expansion blocked；actual exposure event captured；stream reconnect idempotency；workflow resume；event ledger failure visible；LLM mastery/plan/review/action fields 无法写 canonical state；DecisionTrace replay 不调用在线 LLM。

## 12. Acceptance Criteria

- `SYS08-AC-001`：普通与流式走同一 orchestrator 主链。
- `SYS08-AC-002`：fallback 不改变 TeachingAction 语义。
- `SYS08-AC-003`：LLM 无直接写 mastery/plan/review/action truth 路径。
- `SYS08-AC-004`：Prompt/model/tool/workflow/input versions 可追踪。
- `SYS08-AC-005`：资料回答引用可映射 EvidenceBundle→SourceSpan。
- `SYS08-AC-006`：恶意内容不能触发未授权工具或改变 policy。
- `SYS08-AC-008`：关键账本写失败不静默忽略。
- `SYS08-AC-200`：SYS08 只能收紧，不能扩大 SYS05 scaffold/hint/exposure envelope。
- `SYS08-AC-201`：actual experienced assistance/exposure 能进入 SYS04/事件链。
- `SYS08-AC-202`：SYS08 无法通过 LLM/Agent override hard rule。

## 13. Legacy Mapping

旧 `SYS08-074 answer_exposure_max` 由本文件 v0.3 `SYS08-074` envelope guard 语义 supersede；这是同一安全职责的字段迁移，不再允许旧数值 writer。历史 L0-L4/整数 exposure MAY 只读映射并标记 lossy/ambiguous reason。

legacy Socratic adapter/response generator MAY 继续作为 bounded execution component/InteractionMove provider，但 MUST NOT 成为 final TeachingAction owner。迁移第一目标仍是消除 direct dialog/Socratic 与 canonical orchestrator 的双主链路。

## 14. Forbidden Implementations

禁止：autonomous TutorAgent 同时拥有八类决策；开放任意 shell/network/file write；system prompt 作为唯一安全边界；LLM 返回 mastery 后直接 UPDATE；retrieval failure 后模型常识伪装资料；fallback 自动给更高 support/exposure；无限 Agent loop；普通聊天绕过 orchestrator；Redis/Kafka 唯一不可恢复 truth；日志无限保存敏感 Prompt；继续写 `answer_exposure_max`/integer support 为 canonical contract。