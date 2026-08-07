# Askora Error Contract

> Spec ID：`ERROR-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 原则

### ERROR-001

错误必须区分：业务拒绝、输入无效、并发冲突、暂时基础设施失败、永久外部依赖失败、安全拒绝和内部不变量破坏。不得全部变成 HTTP 500 或自由文本异常。

### ERROR-002

错误对象必须可机器处理，至少包含：

```yaml
error:
  code: string
  category: validation|business|conflict|not_found|authorization|security|dependency|transient|internal
  message: string
  retryable: boolean
  correlation_id: string|null
  details: object|null
```

## 2. 稳定错误码

错误码语义发布后不得改变。建议命名：

```text
CONTENT_UNSUPPORTED_TYPE
CONTENT_QUARANTINED
RETRIEVAL_MISSING_EVIDENCE
RETRIEVAL_ACCESS_DENIED
ASSESS_ITEM_VERSION_MISMATCH
ASSESS_SCORING_UNAVAILABLE
LEARNER_EVIDENCE_INELIGIBLE
TEACH_NO_ELIGIBLE_ACTION
PLAN_NO_FEASIBLE_ACTIVITY
REVIEW_INVALID_OBSERVATION
AI_MODEL_UNAVAILABLE
AI_OUTPUT_VALIDATION_FAILED
TOOL_NOT_AUTHORIZED
CONCURRENT_VERSION_CONFLICT
SCHEMA_VERSION_UNSUPPORTED
```

## 3. Retry

### ERROR-010

只有 `retryable=true` 的 transient/dependency error MAY 自动重试。业务校验、安全拒绝、版本冲突不得盲重试同一输入。

### ERROR-011

自动 retry 必须有上限、退避、trace，并对副作用操作保证幂等。

## 4. Domain vs Transport

### ERROR-020

领域错误不能依赖 HTTP status。API adapter 负责映射：

- validation → 400/422；
- auth → 401/403；
- not found → 404；
- conflict/version → 409；
- dependency unavailable → 502/503；
- rate/temporary → 429/503；
- invariant/internal → 500。

具体 transport status 可调整，但领域 code 必须稳定。

## 5. 学习语义错误

### ERROR-030

基础设施/模型/工具故障不得记录成“学习者答错”“学习者忘记”或其他负向学习 evidence。

### ERROR-031

检索证据不足应返回 `RETRIEVAL_MISSING_EVIDENCE` 或等价结构化结果，不得伪造资料答案。

### ERROR-032

评分器不可用时 Attempt 可进入 `scoring_failed/needs_review`，不得自动记 0 分。

## 6. Security

安全拒绝默认 `retryable=false`；对用户返回的信息不得泄露敏感规则、密钥、内部路径或可被利用的检测细节。

## 7. Logging

错误日志必须带 correlation/trace id、error code 和必要上下文；不得把原始密钥、密码、完整敏感 Prompt 写入日志。

## 8. Acceptance Criteria

- `ERROR-AC-001`：模型超时与用户答错在数据层完全不同。
- `ERROR-AC-002`：同一稳定领域错误在 HTTP/WS/streaming 都保留同一 error code。
- `ERROR-AC-003`：非 retryable 业务错误不会进入自动重试循环。
- `ERROR-AC-004`：副作用 retry 不产生重复操作。

## 9. Forbidden Implementations

禁止：

- `except Exception: return None` 吞掉关键失败；
- 所有异常统一 retry；
- 模型超时给 AssessmentResult 记失败；
- 依赖自由文本判断错误类型；
- 把 stack trace/密钥直接返回前端。
