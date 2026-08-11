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
