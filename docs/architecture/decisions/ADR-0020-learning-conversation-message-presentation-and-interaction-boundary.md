# ADR-0020 — Learning Conversation Message Presentation and Interaction Boundary

Status: accepted
Date: 2026-08-11
Decision owners: user-authorized Askora architecture governance
Decision authority: user-delegated Codex；用户于 2026-08-11 明确采纳 LearningActivity-scoped message artifact 建议并要求开始执行
Authorized objective: 将 Learning Conversation Message System 从 Prototype 推进到 Spec Freeze，不修改产品代码
Upper authority: `docs/product/PRODUCT-POSITIONING.md`, `docs/product/PRODUCT-DEFINITION.md`
Canonical design input: `docs/design/features/Learning-Conversation-Message-System-Canonical-Design-Delta.md`
Affected specs: `docs/specs/interfaces/learning-conversation-message-system-spec-delta.md`, `render-content-contract.md`, `api-contract.md`, `schema-versioning.md`, UI specs, LCMS vertical slice / EXEC-075

## Context

本地 Message Prototype 验证了 typed content、block-level actions、理解测试、feedback、review/apply 等视觉和交互表达，但它同时在浏览器中模拟了 SYS04 Assessment、SYS05 TeachingAction、SYS06 LearningActivity、SYS07 ReviewSchedule 和 UserNote success。

当前正式实现有：

- legacy `DialogMessage`，含 `content + optional RenderPayloadV1`；
- canonical `BookLearningTranscriptTurnV1`，按 exact LearningActivity 保存 accepted learner/reply text 与 owner refs；
- `RenderPayloadV1`，只有 markdown、non-interactive card、citations，且禁止 executable card/command；
- `ActivityLearning`，直接显示 transcript `reply_text`。

需要决定 Message 的 canonical target、Block schema、interaction/owner boundary、状态拆分和 legacy migration。该决定不能由 Prototype 或当前表结构隐式形成。

## Decision

### 1. Canonical target

正式 Message System 使用 `LearningActivity-scoped transcript/message presentation artifact`：

```text
LearningConversationViewV1
→ LearningMessageV1
→ MessageBlockV1
→ InteractiveElementV1 / capability
→ narrow owner command/query
```

- Conversation 是同一 LearningActivity transcript 的 read projection；
- Message 是 SYS08 accepted presentation/transcript artifact；
- Block 是 typed learner-visible presentation semantics；
- Interactive Element 是 server-issued capability descriptor；
- Learning Action 仍由 SYS03～SYS07/应用 owner command 拥有。

不建立第九 learning owner，不把 Message 提升为 Product Definition 的核心学习对象。

### 2. New versioned message envelope

新增独立公共合同 `LearningMessageV1`，包含 mandatory text fallback、ordered typed blocks、context/owner refs、trace refs 与 capability descriptors。

不修改 `RenderPayloadV1` 的现有 1.0 语义，也不向其 card 增加 executable command。

### 3. Six block types

V1 一等类型固定为：

```text
EXPLANATION
KNOWLEDGE
EVIDENCE
LEARNING_ACTIVITY
FEEDBACK
REVIEW_APPLY
```

视觉 variant、heading/list/bold、math/code/table 等属于 payload/renderer composition，不新增同级领域类型。

### 4. Owner-safe interaction

Interactive Element 只能使用冻结的 capability vocabulary：

```text
ASK_FOLLOW_UP
INSPECT_SOURCE
SUBMIT_ATTEMPT
REQUEST_HINT
REQUEST_EXPLANATION
START_ACTIVITY
```

每个 capability 必须包含 semantic primitive、owner port ref、exact input refs、availability/reason、idempotency requirement 和 expected result ref types。前端只能 dispatch；server/owner 必须重新验证 scope/version/availability/envelope。

成功 UI state 只表示收到 receipt；canonical business success 来自 owner result/query。

`CAPTURE_NOTE` 明确 deferred，直到 UserNote owner/anchor/version/conflict/recovery contract 被单独冻结。

### 5. State separation

拒绝 `created→presented→opened→attempted→evaluated→mastered/needs-review` 单一状态机。

状态分别归属：

- SYS08 workflow/message acceptance；
- UI/SYS08 optional delivery telemetry；
- frontend transient invocation state + owner receipt；
- SYS06 activity lifecycle；
- SYS04 Attempt/AssessmentResult；
- SYS03 evidence acceptance/mastery projection；
- SYS05 validation obligation；
- SYS07 ReviewSchedule/version stream。

presented/opened/copy/hover/turn count 不属于 mastery evidence。

### 6. Review and apply boundary

本 ADR 不新增 `ReviewItem`。

- Review Block 只能启动 exact SYS06 `delayed_review` activity，并可只读引用 SYS07 schedule/due；
- Apply Block 只能启动 exact SYS06 `transfer_check|practice` activity，并引用 SYS05 allowed transfer action；
- 缺 exact refs 时 capability 必须 unavailable；
- UI 不创建 activity、不修改 `next_due_at`、不宣布“已加入复习”。

### 7. Feedback boundary

Feedback Block 必须引用 exact SYS04 AssessmentResult/diagnosis/actual assistance，或显式标记为 `NON_ASSESSMENT_EXECUTION_FEEDBACK`。它不能拥有 `mastered`、不能产生 LearnerEvidence，也不能由 LLM 文本替代评分事实。

### 8. Compatibility and retirement

- `message.content` / transcript `reply_text` 保持 mandatory fallback；
- existing RenderPayloadV1 通过 deterministic safe adapter 只读映射；
- 缺 exact owner refs 的旧记录标 `LEGACY_COMPAT/PARTIAL`，不生成 interactive capability；
- HTTP/history/SSE final/replay 返回同一 accepted message envelope；
- 历史记录不调用在线 LLM 回填；
- legacy DialogMessage 继续 bounded compatibility，不成为 canonical LearningActivity writer；
- canonical new writer/readers 切换且历史 adapter coverage/retirement evidence 完成后，停止 Message 双协议写入。

### 9. Persistence mapping

本 ADR 先冻结 Domain/Public contract，不设计数据库表。后续 implementation 必须优先映射现有 SYS08 append-only transcript projection；若确需 schema/migration，必须在实现前补充 exact migration/forward-fix，而不得改变本 ADR owner 语义。

## Alternatives Considered

### A. Message as a new learning aggregate

Rejected. 它会复制 LearningActivity、Assessment、TeachingAction、Mastery 与 Review truth，形成第九 owner 和永久 reconciliation 问题。

### B. Extend RenderPayloadV1 card with actions

Rejected. 同 major version 改变安全与执行语义，旧客户端可能把 executable content 当普通 card，renderer 也会成为任意 command router。

### C. Keep Prototype local-state interactions

Rejected. 前端无法审计/replay owner decision，provider/UI failure 会被误记为 learner result，刷新后会丢失或伪造成功。

### D. New LearningMessage envelope with exact refs and capabilities

Accepted. 它复用 ADR-0004 SYS08 transcript、保持八系统 single-writer，并允许 block/rendering 逐步演进。

## Consequences

### Positive

- Block 可以扩展而不把业务规则放进 renderer；
- Message/Conversation 与 Learning Evidence 明确分离；
- Assessment、Teaching Policy、Planner、Review 的既有 owner 保持不变；
- legacy plain text 与 RenderPayloadV1 可以安全 fallback；
- interaction 可以追踪到 command、receipt、result 和 next owner transition。

### Cost / Risk

- 需要新增公共 Message/Block/Capability schema 和 strict validators；
- canonical transcript 与 legacy dialog 需要 bounded adapter/retirement；
- HTTP/history/SSE/refresh 必须保持同一 envelope；
- 六类 renderer、capability availability 与 owner error mapping 需要多层测试；
- UserNote/Capture 不在本次闭环内，UI 必须诚实 unavailable。

## Ownership and Duplicate-truth Invariants

- SYS08 只拥有 accepted message/transcript/execution ledger，不拥有 SYS01～SYS07 truth；
- capability descriptor 不复制 owner state，dispatch 不绕过 owner application service；
- persisted message interaction snapshot 只用于审计“当时提供了什么”，当前可用性仍由 server/owner 重验；
- AssessmentResult != Feedback Block != MasteryEstimate；
- ReviewSchedule != Review Block != LearningActivity；
- no frontend/LLM direct canonical write；
- no permanent DialogMessage + LearningMessage dual writer。

## Security / Privacy / Replay / Idempotency

- Message/Block/model output 视为 untrusted，frontend 使用 typed allowlist；禁止 raw HTML/MDX/script/dynamic component/arbitrary command；
- grader-only、answer-only、secret、raw Prompt、完整无关资料、跨 Workspace refs 不进入 learner-visible envelope；
- capability dispatch 必须 current LocalOwner/Workspace scoped、exact version、idempotent；
- duplicate command 不产生第二 Attempt/Evidence/Activity transition；
- reconnect/replay 返回已接受 envelope，不重复模型调用或 side effect；
- fallback 只能改变呈现/执行路径，不得改变 TeachingAction semantics 或 exposure envelope。

## Migration / Rollback

1. 先实现 schema/validator/adapter，不改变 existing owner tables；
2. canonical LearningActivity writer additive 产生 `LearningMessageV1`；
3. history/HTTP/SSE 统一读取同一 accepted envelope；
4. frontend 切到 `ConversationView→MessageRenderer→BlockRenderer`；
5. capability dispatcher 逐个接入已有 owner command；缺 command 的 capability 不显示或 unavailable；
6. legacy Dialog/RenderPayload 仅通过 deterministic read adapter；
7. 达到 retirement conditions 后关闭 canonical path 的旧双写。

Rollback/forward-fix：新客户端始终可回退 mandatory content；后端可暂时停止发送 structured envelope，但不得恢复 Prototype local business truth。已保存 envelope 保持可读，不在线重写。

## Validation

至少验证：

- six block strict schema / unknown type / unknown major / limits；
- plain fallback 与 legacy deterministic adapter；
- HTTP/history/SSE final/replay envelope equivalence；
- capability scope/version/idempotency/revalidation；
- frontend renderer 无 Teaching Policy、scoring、mastery、review rules；
- SUBMIT_ATTEMPT 只通过 SYS04，Assessment 不直接写 SYS03；
- review/apply 只能 start exact SYS06 activity；
- actual assistance/exposure/AssessmentResult refs 可追踪；
- malicious block/URL/command/prompt injection fail closed；
- Engineering、Policy-Ownership、Learning Evidence gate 独立。

本 ADR 的通过不证明学习效果；Learning Evidence 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。

## Supersedes / Superseded By

本 ADR additive specializes ADR-0004 的 durable SYS08 transcript 与 ADR-0005 的 policy-bound rendering；不 supersede ADR-0001/0002、SYS03～SYS07 ownership、ADR-0014/0018 UI primitives/architecture 或 Product Positioning。

Superseded by: none.
