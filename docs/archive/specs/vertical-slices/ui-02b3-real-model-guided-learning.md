# UI-02B3 — Real-model Guided Learning

> 状态：**FROZEN / EXEC-027 DONE**
>
> 冻结日期：2026-08-08
>
> 决策权限：user-delegated Codex（ADR-0005）
>
> 上游：UI-02B2、SYS05、SYS08、DOD-030

## 1. Objective

证明真实用户路径而非测试专用 adapter：

```text
真实 EPUB → confirmed Goal/diagnostic/plan/activity
→ 浏览器点击“开始本次学习”
→ configured provider real inference
→ policy/envelope/citation validation
→ accepted transcript + ModelInference event
→ 刷新恢复 exact reply/evidence/model metadata
```

## 2. Production Model Renderer Contract

### UI02B3-010

Book Learning canonical adaptive execution 在配置真实 provider 时 MUST 使用 production policy-bound model renderer。
模型只生成 text；TeachingAction、EvidenceBundle、strategy、move、modifier、assistance/exposure 与 owner refs 由服务端
提供和验证，模型不得自报后成为 truth。

### UI02B3-011

Prompt MUST versioned，并把 retrieved evidence 标为 untrusted data。仅可发送本轮最小必要的 goal/user intent 与一个
`learner_visible` evidence item；MUST NOT 发送 secret、grader/internal evidence 或无关 learner history。

### UI02B3-012

provider timeout/unavailable、empty/invalid output、validation failure MUST fail closed，返回 stable dependency/execution
error；不得创建 accepted transcript、ActualAssistance 或 learner-failure evidence。local template fallback 必须标记
`mode=local_fallback`，不得满足 real-model gate。

客户端教学请求 timeout MUST 大于服务端 provider bounded timeout，并保留可重试错误；不得在服务端仍可能接受回合时
用相同长度的客户端 timeout 提前制造假失败。

### UI02B3-013

真实 EPUB 的 canonical retrieval MUST 在当前用户和 source scope 内加载发布元数据与分块；
不得把同一大型文档发布元数据与每个分块重复联表传输。查询优化 MUST 保持 current revision、
publication、visibility 与 learner-visible citation 校验语义不变。

## 3. Model Execution Evidence

### UI02B3-020

accepted response/transcript MAY additive 包含 `model_execution`：

```yaml
mode: real_model|local_fallback
provider: string|null
model: string|null
prompt_version: string
inference_id: uuid
latency_ms: integer
input_tokens: integer
output_tokens: integer
total_tokens: integer
```

真实 gate 要求 `mode=real_model`、provider/model 非空、model 不含 `mock`。

### UI02B3-021

SYS08 MUST append exactly one minimal `ModelInferenceCompleted` LearningEvent for each accepted real-model turn，
并通过 inference id/correlation id 关联 transcript、TeachingAction 与 EvidenceBundle。event 不保存完整 prompt/response。

### UI02B3-022

相同 user + idempotency key 重试 MUST 返回 exact accepted response，transcript/event/model call 均不得重复。

## 4. Acceptance Criteria

- `UI02B3-AC-001`：production facade 在 configured model 下不再默认使用 template renderer。
- `UI02B3-AC-002`：浏览器真实点击产生非 mock configured-provider reply。
- `UI02B3-AC-003`：reply 通过 SYS08 tightening-only 与 learner-visible citation validation。
- `UI02B3-AC-004`：PostgreSQL 中恰有一条 accepted transcript 与对应 ModelInference event。
- `UI02B3-AC-005`：刷新后 exact reply、citation、model metadata 可恢复。
- `UI02B3-AC-006`：重复请求不产生第二次模型调用、event 或 transcript。
- `UI02B3-AC-007`：provider/validation/persistence failure 不产生 learner failure/accepted turn。
- `UI02B3-AC-008`：自动化 suite、真实浏览器/DB/API 证据和 release report 完整。
- `UI02B3-AC-009`：千级分块 EPUB 不因重复发布元数据联表而在模型调用前超时。

## 5. Evidence Boundary

该 Slice 证明真实模型主链连通与工程可信性，不证明真人学习效果；Learning Evidence 仍为
`LEARNING_EVIDENCE_INSUFFICIENT`。
