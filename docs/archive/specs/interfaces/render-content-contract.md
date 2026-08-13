# Askora Rich Response Rendering Contract

> Spec ID：`RENDER-*`
> 状态：Canonical Implementation Contract
> 版本：v1.0

## 1. Purpose and Ownership

### RENDER-001 — Presentation Artifact

`RenderPayload` 是 SYS08 根据已决定的 TeachingAction、EvidenceBundle 与经过验证的模型/模板输出生成的版本化呈现产物。它不是新的领域 truth，也不得取得 LearnerState、AssessmentResult、TeachingAction、LearningPlan 或 ReviewSchedule 的 ownership。

### RENDER-002 — Semantic Fidelity

富文本、公式、卡片、引用与视觉层次只能改变表达和布局，不得扩大 `scaffold_control`、`hint_specificity`、`answer_exposure`，不得改变 StrategyFamily、InteractionMove 或 validation obligation。

## 2. RenderPayloadV1

### RENDER-010 — Envelope

公共响应使用以下 additive contract：

```text
render_payload:
  schema_version: "1.0"
  blocks: [RenderBlockV1]
```

`blocks` MUST 保持稳定顺序，数量 MUST 为 1～32。每个 block MUST 有 response 内唯一 `id`。未知 major version MUST 明确拒绝或回退到 `message.content`，MUST NOT 猜测语义。

### RENDER-011 — Markdown Block

```text
markdown_block:
  id: string
  type: "markdown"
  source: string
```

`source` 支持 CommonMark、GFM 与 `$...$`/`$$...$$` 数学语法。原始 HTML、MDX、script 与 executable directive MUST NOT 被执行。

### RENDER-012 — Card Block

```text
card_block:
  id: string
  type: "card"
  variant: "concept" | "hint" | "question" | "feedback" | "source"
  title: string
  body_markdown: string
```

Card 仅是 typed presentation component。v1.0 MUST NOT 包含任意 URL、JavaScript、tool name、cross-domain command、mastery、next action 或 canonical decision 字段。

### RENDER-013 — Citation Block

```text
citation_block:
  id: string
  type: "citations"
  items:
    - label: string
      source_span_id: uuid
```

资料型引用 MUST 可追踪到 SYS02 EvidenceBundle/SourceSpan；不得用无法追踪的模型文本伪造引用。

## 3. Compatibility and Persistence

### RENDER-020 — Plain-text Fallback

`message.content` 继续作为必填纯文本/可读降级内容。`message.render_payload` 是 optional additive 字段：旧消息保持 `null`；旧客户端忽略它；新客户端在 payload 缺失、未知或无效时 MUST 安全显示 `message.content`。

### RENDER-021 — Durable Conversation History

Assistant completion 的 accepted `RenderPayload` MUST 与该消息一起持久化，或可由同一版本化 deterministic renderer 从持久化输入无损重建。v1.0 选择 nullable JSON 持久化；历史消息不得调用在线 LLM 回填。

### RENDER-022 — Single Source

同一 assistant message MUST 只有一个 accepted RenderPayload。HTTP normal、SSE final 与历史消息读取 MUST 返回语义等价的 payload，不得产生三套独立渲染协议。

### RENDER-023 — Learning Message System Boundary

ADR-0020 / `LCMS-*` 新增的 `LearningMessageV1` 是 LearningActivity-scoped SYS08 message/transcript contract，不改变 `RenderPayloadV1 schema_version=1.0`：

- RenderPayloadV1 card 继续 non-interactive；不得添加 arbitrary command/tool/mastery/next-action 字段；
- LCMS interactive capability 只能存在于 strict LearningMessage contract，并由 server/owner revalidate；
- existing RenderPayloadV1 MAY 通过 deterministic read adapter 映射为无业务交互的 LCMS block；
- 缺 exact owner refs 时不得补造 capability、AssessmentResult、TeachingAction 或 ReviewSchedule；
- fallback/history/no-online-LLM-backfill 规则对两者同时适用。

## 4. Generation and Validation

### RENDER-030 — Candidate Is Untrusted

模型产生的 Markdown/block candidate 一律视为 untrusted。SYS08 MUST 完成 schema、长度、block allowlist、citation、TeachingAction fidelity、support/exposure 与安全校验后，才可发布 accepted RenderPayload。

### RENDER-031 — Deterministic Baseline

任何已有纯文本 `reply_text` MUST 可通过固定 `render-payload/1.0` baseline 包装为单一 MarkdownBlock。该包装不得调用在线 LLM，也不得改变回复文本语义。

### RENDER-032 — Failure

结构化候选无效时 MUST 丢弃不可信结构并回退到安全的单 MarkdownBlock 或 `message.content`。不得把渲染失败记录为 learner failure，也不得通过放宽 TeachingAction envelope 恢复。

## 5. Transport

### RENDER-040 — HTTP

非流式消息响应与历史消息 query MAY 新增：

```text
message.render_payload: RenderPayloadV1 | null
```

这是 `/api/v1` additive minor evolution；`message.content` 的存在和既有含义保持不变。

### RENDER-041 — Streaming

文本可继续通过现有 content delta/compatibility event 传输。结构化 payload MUST 只在完整验证后随 final/run_completed event 提交；客户端 MUST NOT 执行半截 JSON block。重连/幂等 replay MUST 返回已持久化的同一 payload。

## 6. Frontend Security

### RENDER-050 — Safe Renderer

前端 MUST 使用 typed React component allowlist。MUST NOT 使用 `dangerouslySetInnerHTML`、执行 raw HTML/MDX、动态 import 模型指定组件或运行代码块。

### RENDER-051 — URL and Media

链接协议 MUST allowlist 为 `http`/`https`。v1.0 Markdown image MUST disabled；`javascript:`、`data:`、`file:`、远程 tracking image 与任意 iframe/object/embed MUST blocked。

### RENDER-052 — Formula Limits

公式 renderer MUST 禁止 trusted commands/external resources，并限制 expansion、size 与错误回显。公式错误 MUST 局部降级为可读源码，不得使整个对话页崩溃。

## 7. Tests and Acceptance Criteria

必须覆盖：strict schema、unknown major、unknown/extra fields、block/count/length limits、plain fallback、DB round-trip、idempotent replay、normal/history/stream equivalence、Markdown/GFM/math/card rendering、raw HTML/XSS/unsafe URL/remote image blocking、formula failure、citation traceability、TeachingAction envelope fidelity。

- `RENDER-AC-001`：历史纯文本消息无需回填即可正常显示。
- `RENDER-AC-002`：canonical reply 可生成并持久化 `RenderPayloadV1`。
- `RENDER-AC-003`：Markdown、GFM、公式与五类 card 可通过 typed renderer 显示。
- `RENDER-AC-004`：raw HTML、MDX、script、unsafe URL、remote image 与 executable code 不可执行。
- `RENDER-AC-005`：unknown/invalid payload 安全回退，不导致页面崩溃。
- `RENDER-AC-006`：HTTP normal、history query、SSE final/replay 返回同一 accepted payload。
- `RENDER-AC-007`：引用可追踪 SourceSpan；无法追踪的 citation 不发布。
- `RENDER-AC-008`：富文本/卡片不得扩大 SYS05 action envelope 或改变 canonical decision。

## 8. Forbidden Implementations

禁止：任意 HTML string 直出；`dangerouslySetInnerHTML`；MDX/动态组件执行；模型 JSON 未验证直传前端；magic fenced block 作为第二公共协议；卡片携带任意 command/tool/URL；历史消息在线 LLM 回填；渲染层修改 mastery/action/plan/review；Markdown/image 加载本地文件或远程 tracking resource。
