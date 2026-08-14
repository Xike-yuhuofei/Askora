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

### SYS08-083 — Desktop Model Configuration

SYS08 拥有版本化 `ModelRouteProfileV1` 语义、路由与运行时 revision；具体合同见
`systems/08-model-configuration.md`。Electron main process 仅作为 OS-protected storage/activation adapter。
候选配置必须先经 local-only、synthetic、no-fallback probe，成功后才能激活；激活失败必须恢复上一
encrypted revision。renderer、普通 API、日志、Prompt 与 telemetry 均不得获得明文 credential。

### SYS08-084 — Learning Message Artifact

ADR-0020 / `LCMS-*` 冻结 `LearningMessageV1` 为 LearningActivity-scoped accepted presentation/transcript artifact。SYS08 MAY own its validation、acceptance、ordering、fallback、history/replay and execution trace；MUST NOT 因此取得 SYS01～SYS07 truth ownership。

Canonical Message MUST preserve exact activity/action/bundle/attempt/result refs when present、mandatory readable fallback and six strict block types. Historical plain/RenderPayloadV1 adapter MUST deterministic、no-online-LLM and MUST NOT invent capability/owner refs。

### SYS08-085 — Capability Dispatch

SYS08 MAY host the message capability application façade and invocation ledger, but every capability MUST map to an allowlisted versioned query/command port and be revalidated for scope/version/availability/idempotency. SYS08 MUST NOT expose generic `SetMastery/SetReviewSchedule/SetTeachingAction/CreateActivity` through Message blocks。

ASK/REQUEST user intent MAY enter a new SYS05 decision；SUBMIT_ATTEMPT must enter SYS04；START_ACTIVITY must enter SYS06；INSPECT_SOURCE is scoped read. Owner receipt/result is canonical，frontend/local invocation state is not。

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

必须区分 provider timeout/unavailable、rate limit、invalid credential/model、invalid structured output、context overflow、citation unsupported、envelope violation、tool unauthorized/failure、workflow invariant violation、credential storage/schema/revision conflict、configuration apply/rollback、persistence/event delivery failure。

## 6. Idempotency

WorkflowRun command、ToolCall side effects、Append event/decision、stream reconnect 与 resume MUST 有 idempotency/duplicate prevention；resume MUST NOT 重复已成功 step。

## 7. Observability

Trace MUST 覆盖：API request → WorkflowRun → TeachingAction → retrieval → model/tool → validation → rendered response → actual assistance/exposure → Attempt/event。

至少记录 action envelope、actual envelope、tightening reason、violation/block、model/tool versions、citation、fallback、event delivery、cost/latency，以及脱敏的 model configuration source/revision/apply outcome。不得记录 secret、ciphertext、control token 或原始 provider body。

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

必须覆盖：normal/streaming 同主链；provider fallback；invalid output bounded repair；context overflow；tool deny；prompt injection；citation unsupported；tightening-only；attempted support/exposure expansion blocked；actual exposure event captured；stream reconnect idempotency；workflow resume；side-effect retry no duplicate；event ledger failure visible；LLM mastery/plan/review/action fields 无法写 canonical state；DecisionTrace replay 不调用在线 LLM；desktop vault/IPC/probe/restart/revision verification/rollback/disabled tombstone。

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
- `SYS08-AC-204`：候选模型配置 probe 成功且 runtime revision 验证通过后才成为 active。
- `SYS08-AC-205`：renderer、普通 API、日志、Prompt 与 telemetry 无明文 credential。
- `SYS08-AC-206`：apply 失败恢复上一 revision；rollback 失败以稳定错误显式呈现。

## 11. Legacy Mapping

历史 `answer_exposure_max`/L0-L4/integer support MAY 只读映射并标记 lossy/ambiguous reason。Legacy Socratic adapter/response generator MAY 作为 bounded execution component/InteractionMove provider，但 MUST NOT final TeachingAction owner。

迁移第一目标继续是消除 default direct dialog/Socratic 与 canonical orchestrator 的双主链路。

## 12. Forbidden Implementations

禁止：autonomous TutorAgent 同时拥有八类决策；开放任意 shell/network/file write；system prompt 作为唯一安全边界；LLM 返回 mastery 后直接 UPDATE；retrieval failure 后模型常识伪装资料；fallback 自动给更高 support/exposure；无限 Agent loop/retry；普通聊天绕过 orchestrator；Redis/Kafka 唯一不可恢复 truth；日志无限保存敏感 Prompt；继续写 `answer_exposure_max`/integer support 为 canonical contract。

---

## SYS08 Model Configuration and Local Secret Boundary Contract

> Spec ID：`MODEL-CONFIG-*`  
> 状态：Canonical Implementation Contract / FROZEN  
> 版本：v1 Local Web / BYOK Alignment  
> Historical governing decision：ADR-0013（desktop-specific mechanics superseded）  
> Current secret-store decision：ADR-0017 + `docs/specs/platform/local-secret-store.md`  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

### 1. Responsibility and Ownership

#### MODEL-CONFIG-001

SYS08 MUST 是 `ModelRouteProfileV1` 的唯一 semantic writer，负责 provider/model/task route/revision/verification/activation。

Local SecretStore MAY 作为 infrastructure adapter 托管 API Key，但 MUST NOT 产生第二 routing truth。

#### MODEL-CONFIG-002

Browser Settings、provider instances、health/readiness response 与 UI state 都只是 active exact revision 的运行/展示投影。它们 MUST NOT 独立修改或推断另一个 active profile。

#### MODEL-CONFIG-003

配置、probe、activation 或 provider failure MUST NOT 写入 learner、assessment、policy、plan、activity、review、knowledge 或 accepted transcript truth。

#### MODEL-CONFIG-004 — Local Web Boundary

v1 model settings interaction：

```text
Browser Settings
→ loopback API
→ Model Configuration Application Service
├── validate / probe
├── SYS08 ModelRouteProfile
└── Local SecretStore
        ↓
    External AI Provider
```

MUST NOT 依赖 Electron main/preload IPC、desktop vault 或 native desktop shell 才能完成 v1 model configuration。

### 2. Public Profile Contract

#### MODEL-CONFIG-010

非敏感 profile summary SHOULD 至少表达：

```yaml
schema_version: "1.0"
revision: integer|null
state: ACTIVE|DISABLED|UNCONFIGURED|DEGRADED
provider: string|null
model: string|null
embedding_provider: string|null
embedding_model: string|null
task_routes: object
source: LOCAL_USER_CONFIG|DEVELOPMENT_ENVIRONMENT|NONE
verified_at: datetime|null
runtime_ready: boolean
runtime_revision: integer|null
reason_codes: [string]
```

summary MUST NOT 包含：

- API Key；
- Key fragment/fingerprint；
- ciphertext；
- `secret_ref` / OS credential identifier；
- Authorization header；
- internal absolute path；
- provider raw error/body。

#### MODEL-CONFIG-011

apply/clear command MUST 显式 schema version、expected revision 与 idempotency key。已有 revision 时若 expected revision 不匹配，返回 `MODEL_CONFIG_REVISION_CONFLICT`，不得 last-write-wins。

#### MODEL-CONFIG-012 — Task Routes

v1 MAY 为不同任务配置不同 provider/model，例如：

```text
KnowledgeExtraction
TeachingDialogue
Assessment
Embedding
```

route 选择 MUST 来自用户配置或确定性 versioned routing policy；不得由 LLM 自由决定或静默跨 provider 切换。

一个 profile MAY 内部引用多个 provider credential binding，但 browser/public summary 不得暴露 secret refs。SecretStore 中存在某个 credential 本身不构成 route activation。

### 3. Configuration Source Precedence

#### MODEL-CONFIG-020 — Production Local

Production Local canonical precedence：

```text
explicit LOCAL_USER_CONFIG ACTIVE
→ exact configured route

explicit DISABLED / UNCONFIGURED
→ no configured external route
```

Development/testing environment variables MAY 作为非生产 compatibility source，但 MUST NOT：

- 成为 v1 用户必须配置方式；
- 在 production clear 后静默复活 provider；
- 覆盖用户明确保存的 revision；
- 被自动复制进 SecretStore。

#### MODEL-CONFIG-021

Askora MUST NOT 编辑或删除用户开发环境 `.env`；也 MUST NOT 把 `.env` secret 自动迁移为正式用户配置。

### 4. Secret Storage

#### MODEL-CONFIG-030 — Local SecretStore

API Key 仅保存在本机，并通过 `LocalSecretStore` port 隔离具体存储机制。

v1 production persistent adapter 已由 ADR-0017 / `LSS-*` 冻结：

```text
macOS   → exact keyring.backends.macOS.Keyring
Windows → exact keyring.backends.Windows.WinVaultKeyring
```

Production MUST explicit select + allowlist + fail closed；MUST NOT 把 keyring automatic discovery、Null、third-party、file/plaintext backend 当作安全存储。

Windows persistence MUST 使用 local-machine scope，而不是 enterprise-roaming default。

无论具体 approved adapter 如何：

- MUST NOT plaintext persist；
- MUST NOT 存入 Workspace/Project普通文件；
- MUST NOT 存入 browser localStorage/sessionStorage/IndexedDB；
- MUST NOT 进入普通 SQLite profile payload；
- MUST NOT 进入默认 Backup / Export / Diagnostics / Logs。

若安全持久化不可用，系统 MUST fail closed for persistence；不得自动降级明文保存。实现 MAY 允许用户重新输入临时 session credential，但不得把该行为伪装为“已安全保存”。

#### MODEL-CONFIG-031 — Secret/Profile Separation

`ModelRouteProfileV1` 只保存非敏感 routing metadata 与 internal exact secret binding/status；SecretStore 保存 secret material。二者必须通过 revision/idempotency application transaction 协调，但 SecretStore 不拥有 provider/model语义。

Internal `secret_ref` MUST 是 opaque random identity，不编码 provider/model/key fragment，也不得进入 ordinary browser profile summary/log/export/diagnostic。

#### MODEL-CONFIG-032 — Browser Exposure

Browser MAY 在用户输入时短暂持有候选 API Key，并通过 loopback HTTP request 提交给 Local Server；提交完成、失败或离开表单后 SHOULD 清除内存中的敏感值。

Browser MUST NOT 提供“显示已保存 Key”能力，也不得把 candidate key 放入 URL/query params、durable client cache 或 browser persistence。

#### MODEL-CONFIG-033 — Logs and Diagnostics

任何 log、telemetry、error response、diagnostic bundle MUST redact：

- Key；
- secret ref internals；
- Authorization；
- request body containing secret；
- provider raw body that may echo secret。

### 5. Candidate Validation / Connection Probe

#### MODEL-CONFIG-050

candidate 在激活前 MUST 通过真实 provider probe 或等价的明确验证步骤。probe 只能发送 fixed synthetic content，不得包含 user document、conversation、learner state、goal、grader data 或 stored Prompt。

#### MODEL-CONFIG-051

probe MUST 使用 candidate provider/model/Key 的 isolated provider instance、fixed prompt/version、bounded timeout、small output budget、no fallback。

成功至少要求：

- provider 可认证；
- model 可用；
- response 非 mock；
- returned route 与 candidate 一致（若 provider API 可验证）。

#### MODEL-CONFIG-052 — Loopback Control Boundary

Model settings write/probe API MUST 只暴露在 Local Web loopback application boundary，并服从 LocalOwnerContext/origin/security contract。

MUST NOT 为此建立公网 secret-control endpoint、remote credential service 或 Askora 官方 proxy。

#### MODEL-CONFIG-053

probe request/response/log MUST NOT 保存或返回 Key、Authorization header、私人学习资料、完整 raw provider response 或 stack trace。只允许 provider/model、prompt version、latency、stable result/error code、retryable、tested_at、correlation id。

### 6. Activation and Rollback

#### MODEL-CONFIG-060 — Apply

apply canonical semantic order：

```text
validate command/revision
→ durable non-secret PREPARED activation journal
→ probe candidate using in-memory credential
→ persist secret through approved LocalSecretStore
→ persist/activate exact ModelRouteProfile revision
→ refresh runtime route
→ verify runtime revision/readiness
→ complete journal
→ retire superseded secret only after successful runtime verification
```

Detailed phases/recovery MUST follow `LSS-040..073`。

用户不应手工重启 Local Server 才能完成配置生效。

实现 MAY 使用 hot reload 或由 Askora 自己协调的受控 Local Server restart，但 restart 属内部实现，不得要求 Desktop/Electron launcher。

#### MODEL-CONFIG-061

activation/readiness verify 失败 MUST 恢复 exact prior profile/secret association when reconstructible，或进入明确 degraded/recovery state；不得留下“UI 显示新配置，runtime 仍使用旧配置”的 split-brain。

#### MODEL-CONFIG-062 — Clear

clear MUST 使用 expected revision + confirmation，先创建明确 `DISABLED` / `UNCONFIGURED` profile revision 并使 runtime 停止路由旧 credential，再删除/retire 对应 secret。

如果 secret cleanup 失败，canonical routing 仍保持 disabled，并产生 recoverable orphan-secret issue。重启后不得被 legacy `.env`、browser cache、旧 secret presence 或旧 process state 静默恢复。

#### MODEL-CONFIG-063

同一 expected revision 的并发 apply/clear 只有一个可提交；后续请求返回 conflict。重复 idempotency key/command fingerprint MUST 返回已提交 summary，不重复 probe/side effect。

#### MODEL-CONFIG-064 — Cross-store Crash Consistency

SQLite profile state 与 OS credential store 不存在跨存储原子事务。实现 MUST 使用 ADR-0017 / `LSS-*` durable non-secret activation journal 进行 phase reconciliation。

Startup 在报告 model configuration `runtime_ready=true` 前 MUST reconcile incomplete operations。任何无法证明 exact prior/new state 的情况必须 fail closed/degraded，不得猜测、不得 env fallback。

### 7. Routing and Fallback

#### MODEL-CONFIG-070

SYS08 可以支持多个 provider/model adapter，但 v1 不建设通用插件 marketplace/runtime plugin ecosystem。

每个任务实际使用 provider/model MUST 可追踪。

#### MODEL-CONFIG-071

关键任务禁止不可追踪的 silent failover。以下至少必须记录 route + fallback reason：

- Assessment；
- Knowledge Extraction；
- Learner State 相关关键推导；
- Teaching Dialogue when route change affects behavior；
- Embedding/index rebuild when model/version changes derived artifacts。

如果 workflow contract 不允许 fallback，则 provider failure MUST 返回稳定 dependency/transient error。

#### MODEL-CONFIG-072

所有 provider adapter 在显式或默认 output budget 下 MUST 有 bounded semantics；不得因某 provider 忽略 omitted `max_tokens` 而形成无声明费用边界。

### 8. Cost Governance

#### MODEL-CONFIG-075

BYOK 不等于无成本治理。Askora SHOULD 记录或估计：

```text
request count
input tokens
output tokens
provider
model
estimated cost
```

高成本/批量操作 MAY 有本地 limit/confirmation，但 cost estimate 不是计费事实，不得伪装为 provider 账单。

### 9. Error Contract

#### MODEL-CONFIG-080

至少支持：

| Code | Category | Retryable | Required action |
|---|---|---:|---|
| `MODEL_CONFIG_STORAGE_UNAVAILABLE` | security/dependency | false | 恢复安全凭据存储或重新输入临时凭据 |
| `MODEL_CONFIG_SECRET_MISSING` | security/dependency | false | 重新输入并验证 Key |
| `MODEL_CONFIG_STORAGE_LOCKED` | security/dependency | true/conditional | 解锁 OS credential store 后重试 |
| `MODEL_CONFIG_SCHEMA_UNSUPPORTED` | validation | false | 升级 Askora 或按迁移流程重建 |
| `MODEL_CONFIG_REVISION_CONFLICT` | conflict | false | 刷新后重试 |
| `MODEL_CREDENTIAL_REJECTED` | authorization/dependency | false | 更新 Key |
| `MODEL_NOT_AVAILABLE` | dependency | false | 选择受支持模型/开通权限 |
| `MODEL_RATE_LIMITED` | transient | true | 按 retry-after 等待 |
| `MODEL_PROVIDER_TIMEOUT` | transient | true | bounded retry / 稍后再试 |
| `MODEL_PROVIDER_UNAVAILABLE` | dependency/transient | true | bounded retry / 稍后再试 |
| `MODEL_CONFIG_APPLY_FAILED` | internal | true | prior profile restored 时可重试 |
| `MODEL_CONFIG_ROLLBACK_FAILED` | internal | false | 进入本地恢复流程 |

Raw keyring/OS exceptions MUST map to stable errors and MUST NOT cross the public API.

### 10. Data and Cost Disclosure

#### MODEL-CONFIG-090

Settings MUST 在 probe 动作前说明该动作只发送固定合成文本、可能产生极小 provider 费用。

#### MODEL-CONFIG-091

设置页 MUST 明确 Askora 是 BYOK，真实学习时会将完成任务所需的最小资料/上下文发送给用户选择的外部 AI Provider。不得使用“全部数据永不离开本机”等与产品实际网络依赖冲突的绝对文案。

#### MODEL-CONFIG-092 — Material parse enhancement preference

SYS08 拥有用户偏好 `use_ai_parse_enhancement`（用户文案：**用 AI 增强资料解析**）。

- 与模型配置放在同一 Settings 分类；
- 模型未 `runtime_ready` 时该 Control 必须 disabled，并给出可读原因；forced value 对 SYS01 视为 `false`；
- 模型就绪时默认 `true`，用户可改为 `false`；
- 该偏好只授权 **资料解析阶段** 是否调用外部模型。它不得被解释为关闭教学 / 评估 / Review 的模型使用；
- 偏好从 `false` → `true` MUST NOT 自动 enqueue 既有 Material 的 hybrid run。

SYS01 读取该偏好决定 `execution_mode`；SYS08 不得自己写 KnowledgeUnit / DocumentIR。

### 11. Observability

#### MODEL-CONFIG-100

至少记录 sanitized：command id/fingerprint、operation id/phase、prior/new revision、provider/model/task route、probe status/latency/error code、activation/runtime verify/rollback result、token usage/cost metadata、correlation id。

MUST NOT 记录 Key/secret reference internals/request body/raw provider error。

### 12. Tests

必须覆盖：

- schema/enum/revision；
- no Electron/Desktop dependency in production-local path；
- exact macOS/Windows LocalSecretStore backend allowlist；
- Null/third-party/config/env backend override rejection；
- Windows local-machine persistence；
- Local SecretStore unavailable/locked/no plaintext fallback；
- browser no secret persistence/readback；
- probe 401/403/404/429/timeout/5xx/empty/mock；
- probe contains no user material；
- apply no persistent-secret/profile switch on probe failure；
- activation/runtime revision verify；
- crash/restart injection after each activation/clear phase；
- orphan-secret cleanup safety；
- rollback/degraded handling；
- disabled/unconfigured state survives restart and secret-cleanup failure；
- development env does not resurrect cleared/restored production config；
- restore with missing secret requires re-entry；
- secret leakage scan for API/SQLite/log/backup/export/diagnostic；
- multi-task route deterministic resolution；
- no silent cross-provider failover；
- one real provider integration/E2E with BYOK in Local Web flow when release evidence requires it。

### 13. Acceptance Criteria

- `MODEL-CONFIG-AC-001`：用户在 Local Web Settings 内完成 provider/model/Key 配置和真实验证，无 Desktop/Electron prerequisite。
- `MODEL-CONFIG-AC-002`：Key 不进入 browser persistence/API response/ordinary SQLite/log/Prompt metadata/export/default backup/diagnostic。
- `MODEL-CONFIG-AC-003`：probe 失败无 persistent secret/new active config；activation 失败可恢复 exact prior revision 或明确 fail closed。
- `MODEL-CONFIG-AC-004`：clear 后重启仍是 DISABLED/UNCONFIGURED，即使旧 secret cleanup 失败，也不被 `.env`/secret presence 复活。
- `MODEL-CONFIG-AC-005`：runtime provider/model/revision 与 canonical active summary 一致。
- `MODEL-CONFIG-AC-006`：provider/storage errors 稳定分类并产生正确恢复动作。
- `MODEL-CONFIG-AC-007`：无 silent external failover/mock-as-ready/learner failure evidence。
- `MODEL-CONFIG-AC-008`：退出并重开 Askora Local Server 后 exact verified config 可恢复；若安全 SecretStore 缺失则明确 degraded/reconfigure。
- `MODEL-CONFIG-AC-009`：真实 provider、自动化、安全和 Local Web UI 门禁有当前证据。
- `MODEL-CONFIG-AC-010`：不同 task route 实际使用的 provider/model/fallback reason 可审计。
- `MODEL-CONFIG-AC-011`：implementation satisfies all `LSS-AC-001..010` production secret-store/crash-consistency requirements。

### 14. Legacy / Supersession

ADR-0013 与旧版 `MODEL-CONFIG-*` 中以下 Desktop-specific mechanics 对 v1 已 superseded：

```text
Electron safeStorage as required adapter
main/preload IPC
DESKTOP_VAULT source
Desktop child-backend port/control-token handshake
Desktop launcher environment injection
macOS App E2E as only release path
```

仍保留的原则：

- SYS08 owns routing semantics；
- secret 与 routing metadata 分离；
- safe local secret persistence；
- real candidate probe before activation；
- exact revision / optimistic concurrency；
- activation/rollback verification；
- no silent failover；
- no secret leakage。

Concrete current secret mechanism is ADR-0017 + `LSS-*`; implementation agents MUST NOT revive ADR-0013 Desktop mechanics to satisfy current requirements。

### 15. Forbidden Implementations

禁止：

- UI 编辑 `.env`；
- Key/Key fragment/secret ref 回显；
- plaintext fallback；
- automatic/unverified production keyring backend；
- browser localStorage/sessionStorage/IndexedDB 保存 Key；
- ordinary SQLite profile/journal payload 保存明文/ciphertext Key；
- Electron IPC 成为 v1 必需 model settings 路径；
- probe 携带用户资料；
- probe 失败仍持久化 secret/激活；
- activation 失败不处理 split-brain；
- clear 后回落旧环境 Key；
- secret presence 自动激活 provider；
- silent cross-provider failover；
- mock 显示为已连接；
- provider failure 记 learner error；
- 模型连通性宣称学习有效；
- Askora 官方云 proxy 成为 BYOK 必经路径。
