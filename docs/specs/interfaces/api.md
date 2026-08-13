# Askora API Boundary Contract

> Spec ID：`API-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. API 职责

### API-001

API 层是 transport adapter，只负责：认证授权、请求校验、command/query 调用、流式/WS 映射、错误映射和 response serialization。

API MUST NOT 承担 mastery、评分、教学策略、计划、复习或知识建模算法。

## 2. Canonical Teaching Entry

### API-010

普通 HTTP、streaming HTTP 与 WebSocket 教学入口 MUST 调用同一个 canonical orchestration/application facade。

不得保留一个 `dialog → direct LLM/SocraticEngine` 与一个 `orchestrator → formal learning` 的长期双默认路径。

### API-011

Transport 差异只能改变：连接、chunking、backpressure、客户端事件格式；不得改变 TeachingAction/assessment/state 业务语义。

## 3. Request Identity

关键写请求 SHOULD 带：

```text
request_id
idempotency_key
session_id
correlation_id
client_schema_version
```

服务端必须生成/传播 trace id。

## 4. Command / Query 分离

### API-020

写请求映射显式 command；读请求映射 query。API 不得通过 ORM model patch 直接变更跨领域业务状态。

### API-021

用户自然语言“我会了”“改成已掌握”只能映射 feedback/command 候选，不能通过 API 直接 PATCH mastery truth。

### API-022 — Explicit Content Reinspection

`POST /api/v1/documents/{document_id}/reinspect` 映射 SYS01
`ReinspectQuarantinedContent`，MUST：

- 使用 current-user scope 查询，未授权与不存在保持不可枚举；
- 只接受 `quarantined` 文档；
- 目标为当前部署的更新版 scanner/policy，不接受客户端指定任意策略；
- durable enqueue，并以 `document_id + target_scanner_version` 幂等；
- 返回 accepted/already-pending 与 target scanner version，不返回内部正则、路径或 exploit detail；
- MUST NOT 在 API adapter 中直接解除隔离或执行解析/知识建模。

### API-023 — Data Control Boundary

P1-03 backend API 只负责 current-user status/query、export、erasure preview/confirm/report；backup/verify/restore 的 filesystem、backend stop/start 与 atomic activation 通过 desktop typed IPC + maintenance core 执行。API/IPC 都不得直接跨 owner patch canonical state。

Erasure preview token MUST 绑定 scope/target/digest/expiry；confirm 必须带 idempotency key。Restore success 后相关 control token/cache 必须失效。完整 schema、errors 与 ownership 见 `data-control-contract.md`。

## 5. Streaming

### API-030

流式输出必须区分：

```text
run_started
content_delta
citation_delta/reference
validation/fallback status（必要时）
run_completed
run_failed
```

具体 wire format 可由实现定义，但同一 response/run 必须可关联 workflow_run_id/correlation_id。

### API-031

客户端断线重连不得重复写入 assistant completion、Attempt、LearningEvent 或 side effect。

### API-032 — Rich Response Rendering

Assistant message MAY additive 返回 `render_payload`，其 canonical contract 见 `render-content-contract.md`。`message.content` MUST 继续存在作为可读 fallback。普通响应、历史 query 与 streaming final/replay MUST 返回同一 accepted payload；结构化 block 只能在完整验证后提交，不得流式执行半截 JSON。

### API-033 — Learning Message and Capability Boundary

Canonical LearningActivity response/transcript MAY additive 返回 `LearningMessageV1`，其唯一合同为 `learning-conversation-message-system-spec-delta.md` (`LCMS-*`)：

- `reply_text/message.content` 继续 REQUIRED fallback；
- normal/history/stream final/reconnect MUST return the same accepted message id/revision/blocks/refs；
- capability invocation MUST carry exact message/block/capability/version/idempotency identity and route to the target owner application port；
- API MUST preserve target owner stable errors and MUST NOT become a generic cross-owner state writer；
- RenderPayloadV1 remains non-interactive compatibility；partial structured message MUST NOT execute/render。

## 6. Error

遵循 `error-contract.md`。HTTP/WS/streaming 必须保留稳定 domain error code。

### API-040 — Recovery query and command

- `GET /api/v1/recovery/issues` 只返回 current-user 可见的 owner projection 与 operational issues；
- `POST /api/v1/recovery/actions` 只接受 strict `RecoveryCommandV1`，并路由到服务端允许的 owner
  command；
- API adapter MUST NOT 直接修改 document/outbox/model/data-control state；
- unknown issue/action/version 返回稳定 non-retryable error；
- successful command 返回 `RecoveryResultV1` 后，客户端 MUST re-query owner projection；
- endpoint response 使用 `Cache-Control: private, no-store`。

### API-041 — Local Desktop Model Control Adapter

桌面模型配置控制面不是公共服务 API，也不得进入 OpenAPI。它只可在 private/local desktop mode 注册于 loopback，要求 Electron main 为每次 backend start 随机生成的高熵 control token，并只接受固定版本 schema。该 token 同时保护固定私有 readiness endpoint 与 probe；公共 `/ready` 不构成 desktop child identity 证明。probe 请求中的 credential 只用于当前内存中的单次 provider 调用；不得持久化、记录、返回或进入普通业务 request。

控制面 response 只返回 sanitized provider/model、probe outcome、稳定 error code 与 runtime configuration revision；MUST NOT 返回 credential、ciphertext、control token、原始 provider body 或完整 request。非 loopback、token 错误、schema 不支持与非 desktop mode 均 fail closed。Electron 每个 App process 选择并复用自己的未占用 loopback port；不得因默认 port 已被占用而附着到另一 Askora backend。

## 7. Versioning

公共 API schema 遵循 `schema-versioning.md`。破坏性变化需要新 major/API version，不得静默改变 `/api/v1` 语义。

## 8. Security

- 所有资源 query/write 必须绑定当前授权用户；
- 本地单用户模式也不得把“无登录”理解为任意文件系统权限；
- 上传文件先安全检查再进入解析；
- API 不返回密钥、内部 Prompt 或 grader-only answer；
- CORS/WS origin/desktop bridge 权限按部署模式最小化。

## 9. Compatibility

Legacy endpoint MAY 暂时存在，但必须：

- 内部调用 canonical facade；
- 不维护第二份业务逻辑；
- 有 migration/deprecation 计划；
- contract test 确认与新入口的关键语义一致。

## 10. Tests

必须覆盖：

- HTTP normal/stream/WS 同 orchestration path；
- auth ownership；
- idempotent submit；
- disconnect/reconnect；
- stable error code；
- schema unsupported；
- legacy endpoint adapter equivalence；
- grader-only/private fields 不泄漏。
- quarantined reinspection ownership、idempotency、same-policy conflict 与 durable recovery；
- recovery issue ownership、action allowlist、expected version、idempotency、budget 与 audit；
- data export current-user allowlist、erasure preview/confirm idempotency；
- desktop IPC allowlist、maintenance mutual exclusion、restore re-login。
- desktop control adapter 的 loopback/token/schema 限制与 secret-free response；

## 11. Acceptance Criteria

- `API-AC-001`：普通与流式请求的同一教学场景产生相同领域决策链。
- `API-AC-002`：API 层不存在 mastery/teaching policy 算法。
- `API-AC-003`：重复 idempotency key 不产生第二份领域事实。
- `API-AC-004`：WS/stream reconnect 不重复学习事件。
- `API-AC-005`：legacy dialog endpoint 如保留，只是 canonical facade adapter。
- `API-AC-006`：复检 API 只 enqueue 显式 SYS01 command；重复请求不产生第二个 run/task。
- `API-AC-007`：Recovery API 仅是 query/transport adapter，不形成跨 owner writer。
- `API-AC-008`：model probe 不出现在 OpenAPI/公网，普通 API 永不接收或返回 credential。

## 12. Forbidden Implementations

禁止：

- FastAPI endpoint 内直接更新 mastery；
- streaming endpoint 另写一套教学策略；
- `/dialog` 绕过 orchestrator 直接调用 LLM 作为默认路径；
- HTTP status/free text 作为唯一错误合同；
- API response 暴露内部 reference answer/rubric secret。
- 用公开 `/api/v1` endpoint 接收、保存或返回模型 credential。

## 13. P1-03 Data Control and Erasure API (去账号化)

> P1-05 账号/认证生命周期已被 ADR-0015 / `LID-*` supersede；Askora 不提供用户账号、注册、登录、密码、
> 用户 session 或账号删除。本节仅保留仍适用的 P1-03 数据控制与擦除语义。

### API-200

Data-control / erasure preview / confirm / report API MUST 调用 `DATA-CONTROL-*` application ports。API
handler 只负责 erasure scope、strict schema validation、command/query、serialization 与 stable error
mapping；MUST NOT 跨 owner 删除数据或绕过 owner-safe erasure 语义。

### API-201

Erasure preview / confirm / cancel MUST 使用 strict v1 schema。关键写入必须携带 idempotency key；
删除 request 还必须 pin preview digest 与 policy version。

### API-202

Erasure preview 使用 single-purpose control token，只允许访问该 deletion request 的 status/cancel/retry，
MUST NOT 访问任何学习数据。status MAY 返回 canonical P1-03 workflow/receipt/checkpoint refs 与
`requires_post_erasure_maintenance`，不得返回 manifest/content。

### API-204

公共 P1-03 erasure preview API MUST NOT 直接接受 `ALL_PERSONAL_DATA` 作为绕过 owner-safe erasure 流程的
入口；该 scope 只能由已确认 erasure scope 与明确确认的内部授权 bridge 调用。普通 Settings 必须路由到
数据与隐私/数据删除 destination。

### API-203

Erasure preview/status、erasure report 与 control-token response MUST 使用 `Cache-Control: private, no-store`，
不得返回 password/hash/recovery digest、完整 phone、原始 device fingerprint、内部文件路径或删除内容正文。

## 14. P1-06 Onboarding API

### API-300

`GET /api/v1/onboarding/journey` 与 `POST /api/v1/onboarding/preferences` MUST 调用 `ONBOARD-*`
query/command port。API handler 不得计算 step completion、挑选业务对象、执行 provider probe、写领域
state 或从 HTTP/free text 决定 recovery action。

### API-301

两端点 current-user scoped、strict v1、`private, no-store`。Preference command MUST 携带 expected
version 与 idempotency key；response 不得包含 secret、Prompt、grader-only、raw provider body、绝对
路径或其他用户 resource ref。

## 14. P1-01 Goal API

`/api/v1/goals` 提供 draft/query/preview/apply/state/evaluation command。每个 write body 必须携带
expected aggregate version 与 idempotency key，correlation id 由 header/middleware 传播。legacy
Book Learning goal writes 只能调用同一 SYS06 application service；前端迁移完成后停止旧合同写入。

## 15. UI-04 Workspace Read Projections

### API-310 — Canonical Workspace Context Query

`GET /api/v1/workspace/context` MUST 调用 Platform Workspace Registry read query，返回 strict
`WorkspaceContextResponseV1`。它 current-owner scoped、`private, no-store`，不得使用 route/localStorage/React
state 提供 `current_workspace_id`，不得触发 Workspace command。V1 单一 Workspace 返回
`switch_capability=SINGLE_WORKSPACE`。

### API-311 — Learning Context Drawer Query

`GET /api/v1/workspace/learning-context?activity_id=<optional UUID>` MUST 返回 strict
`LearningContextResponseV1`：stage 来自 exact SYS05 TeachingAction；next 1..3 来自 exact ordered SYS06
LearningActivity；每项保留 source system/ref/version。query MUST 表达 READY/MISSING/PARTIAL/STALE，
不得调用 LLM、执行 owner command、从 transcript/chat 推断或写任何 canonical state。

### API-AC-310

两个 query current Workspace scoped、side-effect free、foreign ref fail closed、response 无 Prompt/transcript
正文/grader-only/secret/local path，且 refresh/retry 不产生新事实。

## 16. Course Workspace Selection and Activity Projection

### API-320 — Canonical Course Workspace Surface

ADR-0023 / `CWSP-*` defines：

```text
GET  /api/v1/workspaces
POST /api/v1/workspaces
GET  /api/v1/workspaces/current
GET  /api/v1/workspaces/{workspace_id}
POST /api/v1/workspaces/{workspace_id}/switch
GET  /api/v1/workspaces/{workspace_id}/activities
```

API handler only validates strict v1、resolves LocalOwner、dispatches Platform command/query or read-only SYS06 composition、maps stable errors and serializes response。It MUST NOT write ORM state directly。

### API-321 — Current vs Explicit Scope

`/api/v1/workspace/context` becomes a compatibility adapter over canonical WorkspaceSelection and MUST NOT hard-code default Workspace。Explicit Workspace GET/deep link does not mutate selection；write commands continue to validate exact Workspace scope rather than trusting ambient/browser state。

### API-322 — Create / Switch Safety

Create/switch require expected selection version、idempotency key and strict transition guard。`RECOVERY_REQUIRED`/version/idempotency conflict returns no partial write。Response uses `private, no-store` and never exposes foreign Workspace metadata、draft/note/transcript content or local path。

### API-323 — Activity Index

Activity index is side-effect-free and preserves exact Workspace/Goal/Plan/Activity/lifecycle refs。It does not auto-start available Activity、create Session or infer from Conversation。Unknown/foreign/ambiguous chain fails closed per `CWSP-050..054`。

### API-AC-320

Contract/integration tests prove create-and-select atomicity、switch CAS/idempotency/recovery、GET/deep-link no write、foreign non-enumerability and read-only exact-SYS06 Activity projection。

---

## Askora Error Contract

> Spec ID：`ERROR-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

ADR-0012 / P1-07 adds the recovery presentation fields below without changing
the meaning of existing stable codes.

### 1. 原则

#### ERROR-001

错误必须区分：业务拒绝、输入无效、并发冲突、暂时基础设施失败、永久外部依赖失败、安全拒绝和内部不变量破坏。不得全部变成 HTTP 500 或自由文本异常。

#### ERROR-002

错误对象必须可机器处理，至少包含：

```yaml
error:
  code: string
  category: validation|business|conflict|not_found|authorization|security|dependency|transient|internal
  message: string
  retryable: boolean
  correlation_id: string|null
  details: object|null
  recovery:
    issue_ref: string|null
    retry_after_seconds: integer|null
    actions: [RecoveryActionV1]
```

`request_id` MAY remain as an additive compatibility alias, but
`correlation_id` is canonical. API adapters MUST emit `category`, `retryable`
and `correlation_id` for every `AppError` and unhandled error.

### 2. 稳定错误码

错误码语义发布后不得改变。建议命名：

```text
CONTENT_UNSUPPORTED_TYPE
CONTENT_QUARANTINED
CONTENT_REINSPECTION_NOT_ALLOWED
CONTENT_REINSPECTION_POLICY_UNCHANGED
CONTENT_REINSPECTION_CHECKSUM_MISMATCH
CONTENT_REINSPECTION_UNAVAILABLE
RETRIEVAL_MISSING_EVIDENCE
RETRIEVAL_ACCESS_DENIED
ASSESS_ITEM_VERSION_MISMATCH
ASSESS_SCORING_UNAVAILABLE
LEARNER_EVIDENCE_INELIGIBLE
TEACH_NO_ELIGIBLE_ACTION
PLAN_NO_FEASIBLE_ACTIVITY
REVIEW_INVALID_OBSERVATION
AI_MODEL_UNAVAILABLE
AI_PROVIDER_TIMEOUT
AI_PROVIDER_RATE_LIMITED
AI_PROVIDER_KEY_INVALID
AI_PROVIDER_KEY_MISSING
AI_OUTPUT_VALIDATION_FAILED
MODEL_CONFIG_STORAGE_UNAVAILABLE
MODEL_CONFIG_SCHEMA_UNSUPPORTED
MODEL_CONFIG_REVISION_CONFLICT
MODEL_CREDENTIAL_REJECTED
MODEL_NOT_AVAILABLE
MODEL_RATE_LIMITED
MODEL_PROVIDER_TIMEOUT
MODEL_PROVIDER_UNAVAILABLE
MODEL_CONFIG_APPLY_FAILED
MODEL_CONFIG_ROLLBACK_FAILED
TOOL_NOT_AUTHORIZED
CONCURRENT_VERSION_CONFLICT
SCHEMA_VERSION_UNSUPPORTED
CONTENT_PROCESSING_FAILED
CONTENT_FILE_MISSING
CONTENT_OCR_REVIEW_REQUIRED
DATABASE_UNAVAILABLE
DATABASE_MIGRATION_REQUIRED
DATABASE_INTEGRITY_FAILED
OUTBOX_RETRY_WAITING
OUTBOX_RETRY_EXHAUSTED
OUTBOX_HANDLER_UNAVAILABLE
DATA_MODE_UNSUPPORTED
DATA_MAINTENANCE_BUSY
DATA_RECOVERY_KEY_REQUIRED
DATA_RECOVERY_KEY_INVALID
DATA_BACKUP_NOT_VERIFIED
DATA_BACKUP_INTEGRITY_FAILED
DATA_BACKUP_LIMIT_EXCEEDED
DATA_RESTORE_SCHEMA_UNSUPPORTED
DATA_RESTORE_RECONCILIATION_FAILED
DATA_RESTORE_FAILED_ROLLED_BACK
DATA_EXPORT_SCOPE_INVALID
DATA_EXPORT_EXPIRED
DATA_ERASURE_PREVIEW_EXPIRED
DATA_ERASURE_CONFIRMATION_INVALID
DATA_ERASURE_PARTIAL
MESSAGE_NOT_FOUND
MESSAGE_REVISION_CONFLICT
MESSAGE_BLOCK_NOT_FOUND
MESSAGE_CAPABILITY_NOT_FOUND
MESSAGE_CAPABILITY_UNAVAILABLE
MESSAGE_CAPABILITY_STALE
MESSAGE_CONTEXT_SCOPE_VIOLATION
MESSAGE_SCHEMA_UNSUPPORTED
MESSAGE_INTERACTION_INVALID
WORKSPACE_NOT_FOUND_OR_INACCESSIBLE
WORKSPACE_SELECTION_MISSING
WORKSPACE_SELECTION_VERSION_CONFLICT
WORKSPACE_IDEMPOTENCY_CONFLICT
WORKSPACE_SWITCH_RECOVERY_REQUIRED
WORKSPACE_NAME_INVALID
WORKSPACE_SCHEMA_UNSUPPORTED
WORKSPACE_INTEGRITY_FAILED
WORKSPACE_ACTIVITY_SCOPE_VIOLATION
WORKSPACE_ACTIVITY_PROJECTION_UNAVAILABLE
```

上述 recovery 错误的 category、retryability、data safety、retry budget 与允许动作由
`recovery-contract.md` 的单一目录冻结。Provider adapter MUST 根据 typed exception/HTTP status
分类，不得把 provider message 文本作为主分支。

`MESSAGE_*` 是 ADR-0020 / `LCMS-*` façade boundary errors。Target owner 的 assessment/activity/policy/source error code MUST 原样保留；Message adapter 不得把它们改写成自由文本或 learner failure。重复 idempotency key 返回原 receipt/result，不产生第二 side effect。

`WORKSPACE_*` semantics are frozen by ADR-0023 / `CWSP-*`。Not-found/foreign use the same non-enumerable code；selection version、idempotency、recovery-required、invalid name/schema are non-retryable until re-query/input/recovery changes。Only temporary projection/database dependency MAY be retryable；retry reuses the same idempotency key and cannot create a second Workspace/selection version。

P1-03 data-control errors 的 category/retryability 由 `data-control-contract.md` 冻结：wrong key、unsafe package、future schema 与 invalid confirmation non-retryable；maintenance busy、temporary storage 与未完成 owner step MAY retryable。任何 error details 不得包含 key、内容原文或完整本地路径。

### 3. Retry

#### ERROR-010

只有 `retryable=true` 的 transient/dependency error MAY 自动重试。业务校验、安全拒绝、版本冲突不得盲重试同一输入。

#### ERROR-011

自动 retry 必须有上限、退避、trace，并对副作用操作保证幂等。

#### ERROR-012

`retryable=true` 只表示该错误类别允许重试，不表示现在立即重试。若存在 rate limit、lease、
backoff 或预算，响应 MUST 同时给出 `next_eligible_at/retry_after` 与剩余预算。预算耗尽后同一
run/task 不得继续自动重试。

#### ERROR-013

Manual recovery MUST append audit and create an owner-approved replacement task/run when replay is
safe. It MUST NOT erase or reset the original dead-letter/exhausted history.

### 4. Domain vs Transport

#### ERROR-020

领域错误不能依赖 HTTP status。API adapter 负责映射：

- validation → 400/422；
- auth → 401/403；
- not found → 404；
- conflict/version → 409；
- dependency unavailable → 502/503；
- rate/temporary → 429/503；
- invariant/internal → 500。

具体 transport status 可调整，但领域 code 必须稳定。

### 5. 学习语义错误

#### ERROR-030

基础设施/模型/工具故障不得记录成“学习者答错”“学习者忘记”或其他负向学习 evidence。

#### ERROR-031

检索证据不足应返回 `RETRIEVAL_MISSING_EVIDENCE` 或等价结构化结果，不得伪造资料答案。

#### ERROR-032

评分器不可用时 Attempt 可进入 `scoring_failed/needs_review`，不得自动记 0 分。

### 6. Security

安全拒绝默认 `retryable=false`；对用户返回的信息不得泄露敏感规则、密钥、内部路径或可被利用的检测细节。

`CONTENT_REINSPECTION_POLICY_UNCHANGED` 与 `CONTENT_REINSPECTION_NOT_ALLOWED` 是 non-retryable
business/conflict；`CONTENT_REINSPECTION_CHECKSUM_MISMATCH` 是 non-retryable integrity conflict。
它们不得进入普通 processing 自动 retry。复检任务内部仅允许 transient storage/database failure
按固定预算重试，耗尽后返回 `CONTENT_REINSPECTION_UNAVAILABLE` 并保持隔离。

### 7. Logging

错误日志必须带 correlation/trace id、error code 和必要上下文；不得把原始密钥、密码、完整敏感 Prompt 写入日志。

#### ERROR-040 — Model Configuration Retry Semantics

`MODEL_CREDENTIAL_REJECTED`、`MODEL_NOT_AVAILABLE`、`MODEL_CONFIG_SCHEMA_UNSUPPORTED` 与
`MODEL_CONFIG_REVISION_CONFLICT` 默认 non-retryable；必须修改输入或刷新 revision。
`MODEL_RATE_LIMITED`、`MODEL_PROVIDER_TIMEOUT`、`MODEL_PROVIDER_UNAVAILABLE` MAY retry，UI 必须保留候选输入且不得声称已保存。
`MODEL_CONFIG_APPLY_FAILED` 表示新配置未激活且已恢复旧 revision；只有实际无法恢复旧 revision 时使用
`MODEL_CONFIG_ROLLBACK_FAILED`，该错误 non-retryable 且必须明确当前状态未知/不可用。

### 8. Acceptance Criteria

- `ERROR-AC-001`：模型超时与用户答错在数据层完全不同。
- `ERROR-AC-002`：同一稳定领域错误在 HTTP/WS/streaming 都保留同一 error code。
- `ERROR-AC-003`：非 retryable 业务错误不会进入自动重试循环。
- `ERROR-AC-004`：副作用 retry 不产生重复操作。
- `ERROR-AC-005`：全部 HTTP application/unhandled errors 实现完整 `ERROR-002` envelope。
- `ERROR-AC-006`：provider timeout/rate/key/model/output errors 使用稳定 code 且不依赖自由文本。
- `ERROR-AC-007`：credential/model/rate-limit/timeout/provider/apply/rollback 错误可机器区分。
- `ERROR-AC-008`：任何 model configuration 错误 payload 与日志不含 credential/ciphertext/token/provider raw body。

### 9. Forbidden Implementations

禁止：

- `except Exception: return None` 吞掉关键失败；
- 所有异常统一 retry；
- 模型超时给 AssessmentResult 记失败；
- 依赖自由文本判断错误类型；
- 把 stack trace/密钥直接返回前端。

### 10. P1-06 Onboarding Errors

#### ERROR-100

Onboarding stable codes 至少包括：

```text
ONBOARDING_SCHEMA_UNSUPPORTED
ONBOARDING_PREFERENCE_VERSION_CONFLICT
ONBOARDING_PREFERENCE_NOT_FOUND
ONBOARDING_COMPLETION_PRECONDITION_FAILED
ONBOARDING_DEPENDENCY_UNAVAILABLE
```

依赖 owner error MUST 保留原 stable code 和服务端允许的 P1-07 recovery action。partial/stale source 可
返回 read view，但不得映射为 READY；provider/document/activity failure 不得写 learner negative evidence。

### 11. P1-01 Goal Errors

Stable codes：`GOAL_VERSION_CONFLICT`、`GOAL_PREVIEW_STALE`、`GOAL_SOURCE_NOT_EXECUTABLE`、
`GOAL_TARGET_CONFIRMATION_REQUIRED`、`GOAL_CRITERION_UNMEASURABLE`、
`GOAL_WAITING_ACTIVITY_BOUNDARY`、`GOAL_REPLAN_REQUIRED`、`GOAL_EVIDENCE_INSUFFICIENT`、
`GOAL_MEASUREMENT_UNAVAILABLE`。冲突/门禁失败不得终止当前活动或写 learner failure。

---

## Askora Schema Versioning Contract

> Spec ID：`SCHEMA-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

### 1. 范围

本规范适用于：

- API request/response；
- Command/Event；
- DecisionTrace；
- 公共 Pydantic/domain schema；
- persisted structured payload；
- Prompt structured output schema；
- tool input/output schema。
- RenderPayload / RenderBlock presentation schema。
- LearningConversation / LearningMessage / MessageBlock / capability / interaction schema (`LCMS-*`)。
- Electron preload IPC request/response schema；
- desktop encrypted `ModelRouteProfile` payload；
- local desktop control adapter request/response schema。
- Course Workspace list/create/current/switch、transition guard、receipt and Activity index schema (`CWSP-*`)。

### 2. 版本规则

#### SCHEMA-001

公共协议使用显式版本。不得仅依赖 Git commit 猜测历史语义。

#### SCHEMA-002

兼容新增字段可升 minor；删除字段、改类型、改枚举语义、改必填含义等破坏性变化必须升 major。

#### SCHEMA-003

消费者必须明确支持版本范围；未知 major 版本必须拒绝或通过显式 upcaster 处理。

### 3. 演进原则

#### SCHEMA-010

优先 additive evolution：新增 optional 字段、保留旧字段直到迁移窗口结束。

#### SCHEMA-011

字段一旦废弃，必须经历：

```text
mark deprecated
→ dual-read compatibility window
→ backfill/migrate
→ stop writing old field
→ remove in new major
```

#### SCHEMA-012

不得改变同一枚举值的既有语义；语义变化使用新值。

### 4. Upcaster

历史 Event/Decision/Domain payload 如需读取到新模型，使用 pure deterministic upcaster；不得调用在线 LLM 推断缺失字段。

### 5. Public vs Internal

内部私有结构可自由演进，但一旦被另一个 bounded context、API、事件消费者、数据库历史 payload 或测试 fixture 依赖，即视为公共合同，必须遵守本规范。

### 6. Prompt Structured Output

模型 structured output schema 必须版本化，并与 Prompt version、ModelInference 关联。Schema 通过只是语法通过，仍需业务验证。

### 7. Tool Schema

Tool definition 的参数或副作用语义破坏性变化必须升 major，并固定到 WorkflowRun；正在运行的 workflow 不得热切换到不兼容 tool schema。

### 8. Acceptance Criteria

- `SCHEMA-AC-001`：旧 event fixture 可通过 upcaster 被当前支持版本读取。
- `SCHEMA-AC-002`：未知 major event/API schema 被明确拒绝。
- `SCHEMA-AC-003`：字段废弃存在兼容窗口和 migration test。
- `SCHEMA-AC-004`：replay 不依赖模型填补历史 schema。
- `SCHEMA-AC-005`：未知 major ModelRouteProfile/desktop IPC/control schema 被明确拒绝，旧 active revision 不被覆盖。

### 9. Forbidden Implementations

禁止：

- 同一 `schema_version=1.0` 改字段语义；
- 未版本化修改公共 Pydantic model 并假设所有历史数据自动兼容；
- LLM 猜测旧事件缺失字段作为 upcaster；
- tool 参数变化但 workflow version 不变。
- 同一 RenderPayload major version 静默改变 block 或 card 语义。
- 同一 LearningMessage major version 静默改变 block、capability、owner routing 或 interaction-result 语义。

### 10. P1-06 Onboarding Schemas

#### SCHEMA-100

`OnboardingPreferenceV1`、`OnboardingJourneyViewV1`、`OnboardingNextActionV1` 与 preference command
均遵循 strict v1。新增 step/action enum 必须保持旧值语义；改变完成判定、路由或 preference 字段含义
属于破坏性变化，必须新 major 或显式 migration/upcaster。

### 11. Course Workspace Schemas

#### SCHEMA-110

`WorkspaceSelectionV1`、`WorkspaceListResponseV1`、`CreateWorkspaceV1`、`SwitchWorkspaceV1`、`WorkspaceMutationResultV1` and `WorkspaceActivityIndexResponseV1` are strict v1 under `CWSP-*`。Changing current/default semantics、transition guard obligation、idempotency scope、Activity grouping/launch meaning or owner routing is breaking and requires a new major or explicit migration/upcaster。
