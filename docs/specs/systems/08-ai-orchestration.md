# SYS08 — AI Orchestration & Trust

> Spec ID：`SYS08-*`  
> 对应设计：4.8 LLM 生成、Agent 编排与可信控制  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS08-001

SYS08 的唯一职责是把 SYS01～SYS07 已确定的业务对象、TeachingAction 与 EvidenceBundle 可靠执行为用户交互，并统一管理 workflow、模型、工具、Prompt、安全、验证、降级、事件与审计。

### SYS08-002

普通、流式和 WebSocket 教学请求 MUST 最终经过同一 canonical orchestration path。

SYS08 MUST NOT 修改 LearnerState/MasteryEstimate、重新评分 AssessmentResult、拥有/改写 TeachingAction、修改 LearningPlan/ReviewSchedule、发布知识事实、override SYS05 hard rules，或让 autonomous Agent 成为超级业务决策层。

## 2. Existing v0.2 Contracts Retained

### SYS08-010 — Immutable Domain Inputs

业务对象 MUST 以 immutable/versioned reference 注入 workflow；SYS08 MUST NOT 持有可写副本作为第二 truth。

### SYS08-020 — ModelInference != DecisionTrace

`ModelInference` 与 `DecisionTrace` MUST 分离：前者记录模型做了什么；后者记录领域系统最终接受了什么、为什么。

### SYS08-021 — No Cross-domain Write Commands

MUST NOT 暴露 `UpdateMastery`、`RewriteLearningPlan`、`SetReviewSchedule`、`SetTeachingAction` 等直接跨领域写命令。

### SYS08-030 — Ledger Hosting != Event Ownership

事件/DecisionTrace/Outcome/Experiment ledger 托管权不等于业务语义定义权；领域 owner 负责 payload 语义和必要验证。

### SYS08-040 — Canonical Workflow

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

### SYS08-041 — Model Router Baseline

Model routing MAY 基于 capability、privacy、context window、model health、latency、cost、quality tier；模型 MUST NOT 自行选择未经授权的模型/工具。

### SYS08-042 — Task Routing

结构化抽取/分类、一般讲解、复杂推理 MAY 使用不同模型层级；确定性计算/代码 SHOULD 使用 tool。Route MUST NOT 改变 TeachingAction 语义。

### SYS08-043 — Output Validation

Output validation 至少 SHOULD 组合 schema、TeachingAction fidelity、support/exposure、citation faithfulness、tool args、safety/security、assessment constraints。Schema pass 不等于 business pass。

### SYS08-044 — Agent Boundary

Agent MAY 在授权工具内完成局部 workflow、生成同一 TeachingAction 的表达候选；MUST NOT 修改 mastery/plan/action/review、绕过 authorization 或因检索失败自行切换目标。

### SYS08-045 — Learned Routing Scope

Model routing MAY 未来研究 supervised routing / safe contextual bandit，但 Contextual Bandit/RL MUST NOT 成为 v0.3 canonical runtime。Teaching policy 始终归 SYS05。

### SYS08-050 — Workflow Version Pinning

WorkflowRun MUST 固定 workflow version、TeachingAction semantic ref、Prompt version、model route、tool authorization version 与 input object versions；v0.3 SHOULD 同时记录 PolicyBundle ref（若该 run 执行 SYS05 action）。

### SYS08-051 — Durable Ledgers

关键 LearningEvent/DecisionTrace 使用 durable local ledger/outbox；Redis/Kafka MUST NOT 是唯一事实存储。

### SYS08-052 — ModelInference Provenance

ModelInference MUST 记录 provider/model/snapshot、prompt version、latency、usage、validation refs 与 trace id。

### SYS08-053 — Sensitive Retention

敏感全文 Prompt/文档内容 MUST NOT 为 observability 无限期复制；保存最小可审计 metadata/reference，并遵循 retention/privacy policy。

### SYS08-060 — Bounded Retry

Retry MUST bounded；transient error MAY 自动重试。业务 policy/envelope violation MUST NOT 通过无限重试同一未变化 Prompt 解决。

### SYS08-061 — Semantic-preserving Fallback

Fallback 只能改变 execution path，MUST NOT 改变 TeachingAction 语义。

### SYS08-062 — Side-effect Retry

有 side effect 的 tool MUST 有 idempotency key/confirmation/reconciliation，避免重复副作用。

### SYS08-063 — Ledger Failure

影响后续学习状态的关键交互若无法可靠写入事件账本，workflow MUST degraded/failed；不得假装闭环已完成。

### SYS08-070 — Tool Allowlist

Tools MUST registry/schema/allowlist + least privilege；模型不可创建未授权工具或扩大权限。

### SYS08-071 — Untrusted Content Boundary

用户文档、网页、retrieval/tool output 均为 untrusted data，其指令 MUST NOT 覆盖 system policy、TeachingAction、hard constraints 或 tool permissions。

### SYS08-072 — External Processing

发送外部模型前 MUST 服从 privacy classification/provider policy/data minimization；secret/token MUST NOT 进入 prompt。

### SYS08-073 — Citation Guard

资料型输出 MUST 与 EvidenceBundle/SourceSpan 对齐；unsupported claim 必须删除、明确降级为非资料性一般知识，或声明无法确认，MUST NOT 冒充用户资料事实。

### SYS08-080 — Versioned Render Artifact

SYS08 MAY 把已验证的 reply/execution output 规范化为 `RenderPayload`，并拥有该 execution/presentation artifact。RenderPayload MUST 遵循 `interfaces/render-content-contract.md`，不得成为新的 learner/policy/assessment/plan/review truth，也不得通过视觉 block 扩大 TeachingAction envelope。

### SYS08-081 — Durable Activity Transcript Projection

SYS08 MAY 为 exact LearningActivity 保存 append-only learner-visible transcript projection，包含
accepted learner/system-start turn、rendered reply、TeachingAction/EvidenceBundle refs 与 citation payload。
该 projection MUST current-user scoped、idempotent、可跨重启恢复；MUST NOT 作为 mastery、assessment、
plan progression、activity completion 或 TeachingAction 的第二 truth。`system_start` 不得形成 learner answer evidence。

### SYS08-082 — Production Policy-bound Model Rendering

配置真实 provider 时，Book Learning canonical adaptive execution MUST 使用 production policy-bound model renderer；
模型只生成 learner-visible text，服务端固定并验证 TeachingAction/strategy/move/modifier 与 assistance/exposure。
Template renderer 只能作为显式 `local_fallback`，不得满足真实模型 gate。

Prompt MUST versioned、data-minimized，并将 learner-visible EvidenceBundle 内容标为 untrusted data；grader/internal
evidence、secret 与无关 learner history MUST NOT 发送外部模型。accepted real-model turn MUST 记录最小化
ModelInference metadata/event，并随 durable transcript 恢复 exact execution metadata。

provider/invalid output/validation/persistence failure MUST fail closed，不得写 learner failure 或 accepted transcript。

## 3. v0.3 TeachingAction Execution Envelope

### SYS08-200 — Tightening-only Rule

SYS08 MUST 在 TeachingAction canonical envelope 内执行：

```text
scaffold_control
hint_specificity
answer_exposure
InteractionMove / ActionModifier semantics
```

SYS08 MAY 因安全、证据不足、模型能力或验证收紧 envelope；MUST NOT 扩大 scaffold、hint specificity、answer exposure 或改变 StrategyFamily/InteractionMove 语义。

### SYS08-201 — No Semantic Recovery

若模型/工具不能在 envelope 内完成动作，SYS08 MUST 返回结构化 execution failure 给 SYS05 重新决策。MUST NOT 通过自行给更多 hint、直接答案或换策略恢复。

### SYS08-202 — Actual Experience

SYS08 MUST 将实际呈现的 support/hint/exposure 事件提交给 SYS04/事件账本，使 Attempt 能记录实际经历；不得只记录计划 envelope。

### SYS08-203 — v0.3 Envelope Guard

最终输出 MUST 满足：

```text
actual_scaffold_control <= allowed scaffold envelope
actual_hint_specificity <= allowed hint envelope
actual_answer_exposure <= allowed answer exposure envelope
```

具体偏序/可比规则 MUST versioned；无法比较时 MUST fail conservative。

旧 `SYS08-074 answer_exposure_max` 被本 requirement supersede；旧 ID 仅保留历史审计，不再是 canonical writer contract。

## 4. v0.3 LLM / Replay Boundary

### SYS08-210

LLM/Agent MAY 负责 explanation、worked example、hint、diagnostic candidate、feedback、self-explanation prompt、language realization 与 tool execution。

LLM/Agent MUST NOT 成为 LearnerState owner、Assessment truth owner、TeachingAction owner、LearningPlan owner、ReviewSchedule owner、hard-rule override 或 answer-exposure override。

### SYS08-211

LLM 输出包含 `mastery`、`strategy`、`next_action`、更高 exposure 等字段时，只能作为 untrusted candidate/invalid output；不得直接写 canonical state 或扩大 action envelope。

### SYS08-212 — Policy Replay Boundary

SYS08 MUST NOT 在 DecisionTrace replay 中重新调用在线 LLM 来重建 SYS05 决策。历史 policy replay 只能使用固定 TeachingContext、PolicyBundle、action/trace refs；模型调用只属于独立 execution replay/fixture。

## 5. Failure Semantics

必须区分 provider timeout/unavailable、rate limit、invalid structured output、context overflow、citation unsupported、envelope violation、tool unauthorized/failure、workflow invariant violation、persistence/event delivery failure。

## 6. Idempotency

WorkflowRun command、ToolCall side effects、Append event/decision、stream reconnect 与 resume MUST 有 idempotency/duplicate prevention；resume MUST NOT 重复已成功 step。

## 7. Observability

Trace MUST 覆盖：API request → WorkflowRun → TeachingAction → retrieval → model/tool → validation → rendered response → actual assistance/exposure → Attempt/event。

至少记录 action envelope、actual envelope、tightening reason、violation/block、model/tool versions、citation、fallback、event delivery、cost/latency。

### SYS08-220 — Operational recovery projection

SYS08 MAY publish provider/tool/workflow/persistence operational incidents for Recovery Center. This
projection is operational evidence only: it MUST NOT write learner state, assessment, plan, review,
content truth or activity completion. Successful execution MAY append a resolved event for the same
issue key; it MUST NOT rewrite the failure event.

Provider failures MUST preserve typed categories for timeout, rate limit, missing/invalid key, model
unavailable and invalid output. Raw provider bodies, keys and full prompts MUST NOT enter recovery rows
or user-visible diagnostics.

### SYS08-221 — Recovery command routing

SYS08 recovery routing may create a replacement execution only when the registered handler declares
owner scope and idempotent replay. Unknown task/schema/unscoped side effects are diagnostic-only. The
router MUST NOT mutate an original dead-letter record to conceal history.

## 8. Security

Security 进一步遵循 `quality/security-standard.md`。SYS08 的 tool、external model、citation、prompt injection 与 exposure guard 均 MUST fail conservative。

## 9. Tests

必须覆盖：normal/streaming 同主链；provider fallback；invalid output bounded repair；context overflow；tool deny；prompt injection；citation unsupported；tightening-only；attempted support/exposure expansion blocked；actual exposure event captured；stream reconnect idempotency；workflow resume；side-effect retry no duplicate；event ledger failure visible；LLM mastery/plan/review/action fields 无法写 canonical state；DecisionTrace replay 不调用在线 LLM。

至少一个 E2E MUST 使用实际配置模型验证 provider/gateway/orchestration；Mock-only 不得作为“真实模型已接通”。

## 10. Acceptance Criteria

原有 AC 保留：

- `SYS08-AC-001`：普通与流式请求走同一 orchestrator 主链。
- `SYS08-AC-002`：模型/工具 fallback 不改变 TeachingAction 语义。
- `SYS08-AC-003`：LLM 无直接写 mastery/plan/review/knowledge/TeachingAction truth 路径。
- `SYS08-AC-004`：Prompt/model/tool/workflow/input versions 可追踪。
- `SYS08-AC-005`：资料回答引用可映射 EvidenceBundle→SourceSpan。
- `SYS08-AC-006`：恶意检索内容不能触发未授权工具或改变 policy。
- `SYS08-AC-007`：应用重启后 durable workflow/task 能恢复或明确失败。
- `SYS08-AC-008`：关键事件账本写失败不静默忽略。
- `SYS08-AC-009`：真实 E2E 至少一次通过实际配置模型，不以 Mock 替代。
- `SYS08-AC-010`：provider/system failures 可恢复且不产生 learner negative evidence。
- `SYS08-AC-011`：manual recovery preserves original failure and is idempotent across restart。

新增 v0.3 AC：

- `SYS08-AC-200`：SYS08 只能收紧，不能扩大 SYS05 support/exposure envelope。
- `SYS08-AC-201`：actual experienced assistance/exposure 能进入 SYS04/事件链。
- `SYS08-AC-202`：SYS08 无法通过 LLM/Agent override hard rule。
- `SYS08-AC-203`：policy replay 不调用在线 LLM 或读取当前 mutable state。

## 11. Legacy Mapping

历史 `answer_exposure_max`/L0-L4/integer support MAY 只读映射并标记 lossy/ambiguous reason。Legacy Socratic adapter/response generator MAY 作为 bounded execution component/InteractionMove provider，但 MUST NOT final TeachingAction owner。

迁移第一目标继续是消除 default direct dialog/Socratic 与 canonical orchestrator 的双主链路。

## 12. Forbidden Implementations

禁止：autonomous TutorAgent 同时拥有八类决策；开放任意 shell/network/file write；system prompt 作为唯一安全边界；LLM 返回 mastery 后直接 UPDATE；retrieval failure 后模型常识伪装资料；fallback 自动给更高 support/exposure；无限 Agent loop/retry；普通聊天绕过 orchestrator；Redis/Kafka 唯一不可恢复 truth；日志无限保存敏感 Prompt；继续写 `answer_exposure_max`/integer support 为 canonical contract。
