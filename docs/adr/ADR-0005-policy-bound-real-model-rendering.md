# ADR-0005 — Policy-bound Real-model Rendering

Status: accepted
Date: 2026-08-08
Decision authority: user-delegated Codex
Authorized objective: 以完成 EPUB→学习真实模型端到端验收为首要目标，不以 Mock 或本地模板替代
Affected specs: `SYS08`、`UI-02B3`、`DOD-030`

## Context

v0.3 Spec 已要求 SYS08 在固定 TeachingAction/EvidenceBundle envelope 内调用模型，并要求至少一次真实配置模型 E2E。
当前实现只有测试专用 `_ConfiguredAdaptiveRenderer` 调用真实 provider；生产 `LearningOrchestrationFacade`
默认使用 `PolicyBoundTemplateRenderer`。因此真实 UI 点击虽然进入 canonical policy/retrieval path，却不会产生真实
ModelInference，不能满足“从 EPUB 到真实模型教学回复”的产品验收。

## Decision

1. SYS08 新增 production `PolicyBoundModelRenderer`，在已经确定的 TeachingAction 与 learner-visible
   EvidenceBundle 内调用已配置 provider；模型只负责语言表达，不选择策略、动作或状态。
2. Prompt 固定版本、最小数据、明确 untrusted evidence 边界；只发送当前目标/用户输入与一个已选择的
   learner-visible evidence item，不发送凭据、grader-only 内容或无关学习历史。
3. 模型输出仅贡献 learner-visible text。strategy/move/modifier 与 actual assistance/exposure 由服务端按
   TeachingAction envelope 保守赋值，随后继续经过现有 tightening-only validator；模型字段不能扩大语义。
4. accepted response/transcript additive 返回 `model_execution`，至少包含 mode、provider、model、prompt version、
   inference id、latency 与 token usage。真实模型成功必须为 `mode=real_model` 且 model 不含 mock。
5. SYS08 在同一 Book Learning transaction 追加最小化 `ModelInferenceCompleted` event，并以 inference id
   关联 transcript/response；不保存完整 prompt 或密钥。
6. provider timeout/unavailable/invalid empty output 返回稳定 dependency failure，不写 learner failure 或 accepted
   transcript。版本化 local template 仅允许显式 `local_fallback`，不得满足真实模型 E2E gate。
7. 相同 idempotency key 在 accepted turn 后重放 exact response，不再次调用模型。

## Alternatives Considered

- 保留 production template，只运行独立真实模型测试：拒绝，因为不证明真实 UI/API/DB/transcript 主链。
- 复用 legacy Socratic/Explain engine：拒绝，因为会恢复第二教学主链并让 legacy selector 混入 canonical execution。
- 让模型返回完整 `RenderProposal`：拒绝，因为会把 strategy/exposure 自报字段交给不可信模型，并增加越权面。
- 将模型调用异步化为新队列：本轮不选；它增加 durable workflow 状态与 UI polling，当前单回合 30～60 秒同步
  模式足以完成受控本地验收。若未来需要长任务，再另立 ADR。

## Ownership and Invariants

- SYS05 仍唯一拥有 TeachingAction；SYS02 仍唯一选择 EvidenceBundle；SYS08 只执行并可收紧。
- ModelInference/执行元数据属于 SYS08 ledger；不得成为 mastery、assessment、plan 或 activity completion truth。
- 真实模型输出必须通过同一 envelope/citation/security validator；模型失败不得记录为学习者错误。
- `system_start` 仍不是 learner answer，不产生 Assessment/Mastery evidence。

## Migration / Rollback

- API/Transcript 仅 additive 增加 optional `model_execution`；旧记录可为 null，旧客户端继续兼容。
- 不新增业务 truth 或数据库表；复用 append-only LearningEvent ledger。
- 回滚代码可恢复 template renderer；已保存 real-model transcript/event 保持可读并继续按 exact response replay。

## Validation

- unit/contract：prompt data minimization、fixed semantic fields、provider error、empty output、model metadata schema。
- integration：真实 Book Learning start 写一条 transcript + 一条 ModelInference event，重复 key 不重复调用/写入。
- security：untrusted document instruction 不改变 action/tool/exposure；grader/internal evidence 不进入 prompt。
- real E2E：浏览器点击“开始本次学习”，响应 `mode=real_model`，provider/model/prompt 可追踪；刷新恢复 exact
  assistant reply/citations/metadata，数据库 event/transcript 与 UI 一致。

## Supersedes / Superseded By

本 ADR additive 修正 production renderer 的实现偏差；不修改 ADR-0001～0004 的 TeachingAction、ownership、
transcript 或 system-start 语义。
