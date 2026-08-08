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

## 6. Error

遵循 `error-contract.md`。HTTP/WS/streaming 必须保留稳定 domain error code。

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

## 11. Acceptance Criteria

- `API-AC-001`：普通与流式请求的同一教学场景产生相同领域决策链。
- `API-AC-002`：API 层不存在 mastery/teaching policy 算法。
- `API-AC-003`：重复 idempotency key 不产生第二份领域事实。
- `API-AC-004`：WS/stream reconnect 不重复学习事件。
- `API-AC-005`：legacy dialog endpoint 如保留，只是 canonical facade adapter。
- `API-AC-006`：复检 API 只 enqueue 显式 SYS01 command；重复请求不产生第二个 run/task。

## 12. Forbidden Implementations

禁止：

- FastAPI endpoint 内直接更新 mastery；
- streaming endpoint 另写一套教学策略；
- `/dialog` 绕过 orchestrator 直接调用 LLM 作为默认路径；
- HTTP status/free text 作为唯一错误合同；
- API response 暴露内部 reference answer/rubric secret。
