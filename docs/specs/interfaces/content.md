# SPEC-D01 — Content Ingestion & Source Locator Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D01`  
> 冻结日期：2026-08-08  
> v1 产品对齐：2026-08-10  
> Owner：SYS01 Content & Knowledge  
> 上位：`docs/product/PRODUCT-POSITIONING.md`、Canonical Design、`systems/01-content-knowledge.md`、`domain/domain-model.md`  
> 目的：把资料导入定义为可审计、可重放、保留结构、可局部恢复的本地 canonical ingestion，不改变 SourceSpan 的来源可追溯原则。

## 1. Position

本合同是 `SYS01` 的增量实现合同，不 supersede 既有 `SYS01-*` / `DOMAIN-*` 学习语义；若旧实现与 `PRODUCT-POSITIONING.md` 冲突，以产品定位为上位约束。

v1 正式输入核心范围：

```text
EPUB
PDF（文本型）
Markdown
TXT
```

DOCX/PPTX/XLSX、网页 URL、Podcast、YouTube、RSS、原生音视频与完整 OCR Pipeline 不属于 v1 core input contract。已有实验/legacy adapter MAY 保留，但不得成为 v1 readiness/release 的必需路径。

## 2. Import Means Ingest + Copy

### D01-001 — Managed Source Copy

用户选择文件后，Askora MUST 将原始文件复制到 Askora managed local data directory，再进入后续 parse pipeline。

```text
User-selected file
→ copy into Askora managed SourceFile storage
→ checksum / durable asset identity
→ security gate
→ parse / structure / index / knowledge modeling
```

MUST NOT 只记录用户原始路径并长期依赖该路径存在。

### D01-002 — SourceFile Durability

Managed SourceFile 是 durable data。Cache 清理、Embedding/Index 重建、AI Provider failure、parser retry 或 Knowledge Modeling failure MUST NOT 删除/覆盖原始 SourceFile。

原始用户路径 MAY 作为 transient import provenance 保存，但不得作为 canonical replay dependency。

### D01-003 — Workspace Scope

Material import MAY 先以 `workspace_id=null` 创建 unassigned Material（`WSP-021` / `EXP-JOURNEY-001`）。导入任务、MaterialRevision、SourceSpan、derived index/rebuild task MUST 能解析 LocalOwner，并在已归属后解析 Workspace。

Unassigned Material MUST NOT 作为某一 Workspace 的普通 retrieval 成员，也 MUST NOT 启动有依据的 LearningActivity。

归属后，后续 revision / span / index MUST 解析该 workspace scope。不得因为同一 LocalOwner 存在多个 Workspace 而默认建立全局已归属 Material scope。

## 3. Required Pipeline and Stage State

v1 ingestion lifecycle：

```text
Uploaded
→ SourceStored
→ Parsed
→ Structured
→ Indexed
→ KnowledgeModeled
→ Ready
```

整体状态至少支持：

```text
pending
processing
ready
partial
failed
```

### D01-004 — Stage Independence

每个 stage SHOULD 保存 exact input/output/version fingerprint 和 durable job state。下游失败不得默认重跑无变化的全部上游步骤。

例如：

```text
SourceStored ✅
Parsed ✅
Structured ✅
Indexed ✅
KnowledgeModeled ❌

Overall = partial
```

系统 MAY 允许用户在可靠 SourceSpan/structure 已可用时开始受限学习，不要求所有 Embedding / Knowledge Modeling 完成后才可进入任何学习活动。

### D01-005 — Restart-safe Jobs

Import/Parse/Index/KnowledgeModeling 等长任务 MUST 由本地 durable job runtime 跟踪，App 关闭后下次启动可 resume/retry/restart。任务中断 MUST NOT 损坏 durable SourceFile 或已提交成功 stage。

## 4. Canonical Parse Pipeline

```text
Managed SourceFile
→ security gate
→ MaterialRevision
→ deterministic format parser
→ DocumentIR
→ DocumentNode hierarchy
→ canonical linearized text
→ SourceSpan
→ downstream derived stages
```

`SourceChunk`/embedding/index MUST NOT 出现在 canonical parse truth 之前。

## 5. Material Revision Identity

### D01-010

`MaterialRevision` MUST 保持 immutable。以下任一语义性变化 MUST 形成新 revision 或显式等价的新 revision identity：

- managed SourceFile checksum 改变；
- parser semantic version 改变并可能改变结构/锚点；
- extraction semantic version 改变并要求重新解释 canonical content；
- 安全修复要求重新建模。

相同 raw checksum + 相同 parser/extraction semantic versions 的重复处理 MUST 幂等。

### D01-011

SafetyScanRun / reinspection 是 append-only 安全审计，不得通过覆盖历史 MaterialRevision 表示“重新检查”。Quarantine 未显式解除前不得进入 learner-visible modeling/projection。

### D01-012 — Duplicate Detection Is Advisory

导入 MAY 基于 raw checksum/版本化 fingerprint 检测可能重复 Material，但 duplicate detection MUST 只形成建议：

- 使用已有 Material；
- 明确创建新副本；
- 取消导入。

MUST NOT 自动跨 Material merge、跨 Workspace deduplicate 或删除用户选择的副本。

## 6. DocumentIR

### D01-020

`DocumentIR` 是 SYS01 内部、版本化、可重建的解析中间表示，不是新的跨系统 canonical truth。至少包含：

```yaml
document_ir:
  material_id: uuid
  revision_id: uuid
  workspace_id: uuid|null
  parser_version: string
  format: epub|pdf|markdown|text
  root_node_id: uuid
  node_ids: [uuid]
  canonical_text_hash: string
  structure_hash: string
```

历史实现若仍使用 `document_id` MAY 作为 compatibility identifier，但不得丢失 Material/Workspace 语义。

### D01-021

`DocumentIR` MUST 能在不调用在线 LLM 的情况下从固定 managed SourceFile + parser version 重建。

## 7. DocumentNode

### D01-030

`DocumentNode` 是 SYS01 内部结构事实，至少允许：

```text
BOOK / PART / CHAPTER / SECTION / PARAGRAPH
LIST / TABLE / IMAGE / FIGURE / FORMULA / CODE
FOOTNOTE / ENDNOTE / OTHER
```

每个节点至少保存：

```yaml
node_id: uuid
revision_id: uuid
parent_node_id: uuid|null
node_type: enum
ordinal: integer
heading: string|null
text: string|null
source_locator: object
content_hash: string
```

`node_id` MUST 在同一 MaterialRevision 内稳定；跨 revision 的 identity matching MAY 生成 stable mapping，但不得用文本相似度静默覆盖旧节点。

## 8. Source Locator

### D01-040

`source_locator` 是 DocumentNode 的 SYS01-owned persisted value object，用于把 canonical SourceSpan 重放回 Askora managed SourceFile。它不是第二 SourceSpan truth。

共同字段：

```yaml
kind: epub|pdf|markdown|text
locator_version: string
managed_asset_ref: string
source_path: string|null      # internal managed relative path only when needed
node_path: string|null
```

MUST NOT 使用用户原始导入绝对路径作为 replay 所需字段。

### D01-041 — EPUB

EPUB locator MUST 至少保留：

```yaml
spine_index: integer
spine_item_id: string|null
href: string
nav_path: [string]
dom_path: string
```

并 SHOULD 保存有效的 `epub_cfi`；如果当前实现不能可靠生成 CFI，可暂缺 CFI，但 `spine + href + dom_path + content hash` MUST 足以稳定重放。实现不得伪造无效 CFI。

### D01-042 — PDF / Markdown / Text

- 文本型 PDF SHOULD 保留 page + block/line locator；
- Markdown/Text SHOULD 保留 heading/node path + offsets；
- 所有格式都 MUST 有 deterministic fallback locator。

扫描 PDF 若无法可靠提取文本，MUST 明确识别为 unsupported/partial extraction 并提示用户；v1 不要求完整 OCR、版面分析、表格/公式视觉识别。

## 9. SourceSpan Replay

### D01-050

现有 canonical `SourceSpan` 来源语义保持不变。新实现 MUST：

- 设置 `node_id` 指向对应 DocumentNode；
- 保留 material-linearized `start_offset/end_offset` 兼容语义；
- 通过 `node_id → DocumentNode.source_locator → managed SourceFile` 重放到原始载体；
- 通过 span text/hash 防止错误锚点静默成功。

### D01-051

Replay 结果 MUST 返回 `EXACT | RECOVERED | FAILED`：

- `EXACT`：locator + hash 精确匹配；
- `RECOVERED`：版本允许的 deterministic fallback 找回且 hash/上下文验证通过；
- `FAILED`：不能可靠定位。

`FAILED` anchor MUST NOT 支撑新的 published knowledge fact。

## 10. EPUB Structural Requirements

EPUB parser MUST 保持：

- spine reading order；
- TOC/nav hierarchy；
- XHTML heading hierarchy；
- paragraph/list boundaries；
- footnote/endnote relation；
- image/figure reference；
- internal anchor/link metadata。

MUST NOT 用 `strip HTML → whitespace normalize → flat text` 作为 canonical EPUB parse 结果；该路径仅可作为 legacy compatibility/fallback extraction，不得形成新 canonical structure truth。

## 11. Derived Artifact Versions

### D01-060

至少记录并传播：

```text
source_version
parser_version
chunker_version
embedding_version
knowledge_model_version
```

当 dependency version 改变：

```text
version changed
→ mark affected derived artifacts stale
→ rebuild affected stages
```

MUST NOT 因 Chunker/Embedding 变化重写 SourceFile/Material truth 或无条件改变 KnowledgeUnit identity。

## 12. Security

- archive bomb、path traversal、external entity/reference、oversized entry 等继续服从 security contract；
- XHTML/script/style/embedded prompt 作为不可信内容数据处理；
- parser 不得执行脚本、远程资源或文档内命令；
- quarantined/rejected 内容不得生成 learner-visible SourceChunk/KnowledgeUnit；
- import/replay/log 不得暴露用户原始绝对文件路径作为普通诊断字段。

## 13. Observability

至少记录：

```text
workspace_id / safe material ref
pipeline stage
stage status
parser_version
format
node_count
structure_hash
canonical_text_hash
anchor_exact/recovered/failed count
spine/nav mismatch
malformed resource count
processing latency
retry/interruption reason
```

默认不记录整本原文。

## 14. Tests

MUST 覆盖：

1. import copies source and survives deletion/move of original user file；
2. Workspace isolation；
3. EPUB spine 顺序；
4. TOC / heading hierarchy；
5. footnote/internal link；
6. SourceSpan → node → managed source position；
7. parser version change creates traceable revision；
8. duplicate processing idempotency；
9. duplicate detection does not auto-merge；
10. malformed EPUB bounded failure；
11. archive/path traversal safety；
12. scanned PDF unsupported/partial without mandatory OCR；
13. stage partial/retry/restart；
14. derived version stale/rebuild；
15. replay failure blocks downstream publication。

## 15. Acceptance Criteria

- `D01-AC-001`：任一新 EPUB SourceSpan 可通过 `node_id` 重放至 managed SourceFile 中的原始 XHTML 结构位置。
- `D01-AC-002`：spine/TOC/DOM 结构不会在 canonical parse 阶段被压平成不可恢复文本。
- `D01-AC-003`：固定 SourceFile + parser version 可 deterministic 重建相同 semantic DocumentIR。
- `D01-AC-004`：parser semantic version 改变不静默覆盖旧 MaterialRevision。
- `D01-AC-005`：anchor replay failed 的证据不能支持 published KnowledgeUnit/Relation。
- `D01-AC-006`：导入后原用户路径消失不影响 Askora 使用 managed source。
- `D01-AC-007`：无第二 SourceSpan/Material truth store。
- `D01-AC-008`：各 pipeline stage 可 partial、局部 retry/rebuild，成功 stage 不被无意义重跑。
- `D01-AC-009`：v1 core format 仅 EPUB/PDF(text)/Markdown/TXT；OCR/DOCX 等非核心能力不阻塞 release。

## 16. Forbidden Implementations

禁止：

- Import 只保存用户原文件路径；
- canonical EPUB ingestion 只保留纯文本和 chunk；
- 以 SourceChunk metadata 代替 DocumentIR/DocumentNode truth；
- 无验证地根据文本搜索“猜”原始位置并标 EXACT；
- parser 升级原地覆盖历史 revision；
- 为 v1 强制引入完整 OCR/视觉文档 pipeline；
- 把 DOCX/PPTX/XLSX/URL/音视频错误宣称为 v1 core support；
- Source locator 取得 SYS02/SYS06/SYS08 状态所有权；
- derived stage failure 删除 durable SourceFile；
- 跨 Workspace 自动 deduplicate/merge Material。

## 17. Freeze Decision

`SPEC-D01`：**FROZEN / PRODUCT-POSITIONING-ALIGNED**。如实现必须改变现有 SourceSpan 公共字段含义、引入外部解析服务、新增 v1 production dependency 或突破 core input scope，必须先按 Product Positioning / ADR / Spec 治理，不得在产品代码中隐式决定。

---

## Askora Rich Response Rendering Contract

> Spec ID：`RENDER-*`
> 状态：Canonical Implementation Contract
> 版本：v1.0

### 1. Purpose and Ownership

#### RENDER-001 — Presentation Artifact

`RenderPayload` 是 SYS08 根据已决定的 TeachingAction、EvidenceBundle 与经过验证的模型/模板输出生成的版本化呈现产物。它不是新的领域 truth，也不得取得 LearnerState、AssessmentResult、TeachingAction、LearningPlan 或 ReviewSchedule 的 ownership。

#### RENDER-002 — Semantic Fidelity

富文本、公式、卡片、引用与视觉层次只能改变表达和布局，不得扩大 `scaffold_control`、`hint_specificity`、`answer_exposure`，不得改变 StrategyFamily、InteractionMove 或 validation obligation。

### 2. RenderPayloadV1

#### RENDER-010 — Envelope

公共响应使用以下 additive contract：

```text
render_payload:
  schema_version: "1.0"
  blocks: [RenderBlockV1]
```

`blocks` MUST 保持稳定顺序，数量 MUST 为 1～32。每个 block MUST 有 response 内唯一 `id`。未知 major version MUST 明确拒绝或回退到 `message.content`，MUST NOT 猜测语义。

#### RENDER-011 — Markdown Block

```text
markdown_block:
  id: string
  type: "markdown"
  source: string
```

`source` 支持 CommonMark、GFM 与 `$...$`/`$$...$$` 数学语法。原始 HTML、MDX、script 与 executable directive MUST NOT 被执行。

#### RENDER-012 — Card Block

```text
card_block:
  id: string
  type: "card"
  variant: "concept" | "hint" | "question" | "feedback" | "source"
  title: string
  body_markdown: string
```

Card 仅是 typed presentation component。v1.0 MUST NOT 包含任意 URL、JavaScript、tool name、cross-domain command、mastery、next action 或 canonical decision 字段。

#### RENDER-013 — Citation Block

```text
citation_block:
  id: string
  type: "citations"
  items:
    - label: string
      source_span_id: uuid
```

资料型引用 MUST 可追踪到 SYS02 EvidenceBundle/SourceSpan；不得用无法追踪的模型文本伪造引用。

### 3. Compatibility and Persistence

#### RENDER-020 — Plain-text Fallback

`message.content` 继续作为必填纯文本/可读降级内容。`message.render_payload` 是 optional additive 字段：旧消息保持 `null`；旧客户端忽略它；新客户端在 payload 缺失、未知或无效时 MUST 安全显示 `message.content`。

#### RENDER-021 — Durable Conversation History

Assistant completion 的 accepted `RenderPayload` MUST 与该消息一起持久化，或可由同一版本化 deterministic renderer 从持久化输入无损重建。v1.0 选择 nullable JSON 持久化；历史消息不得调用在线 LLM 回填。

#### RENDER-022 — Single Source

同一 assistant message MUST 只有一个 accepted RenderPayload。HTTP normal、SSE final 与历史消息读取 MUST 返回语义等价的 payload，不得产生三套独立渲染协议。

#### RENDER-023 — Learning Message System Boundary

ADR-0020 / `LCMS-*` 新增的 `LearningMessageV1` 是 LearningActivity-scoped SYS08 message/transcript contract，不改变 `RenderPayloadV1 schema_version=1.0`：

- RenderPayloadV1 card 继续 non-interactive；不得添加 arbitrary command/tool/mastery/next-action 字段；
- LCMS interactive capability 只能存在于 strict LearningMessage contract，并由 server/owner revalidate；
- existing RenderPayloadV1 MAY 通过 deterministic read adapter 映射为无业务交互的 LCMS block；
- 缺 exact owner refs 时不得补造 capability、AssessmentResult、TeachingAction 或 ReviewSchedule；
- fallback/history/no-online-LLM-backfill 规则对两者同时适用。

### 4. Generation and Validation

#### RENDER-030 — Candidate Is Untrusted

模型产生的 Markdown/block candidate 一律视为 untrusted。SYS08 MUST 完成 schema、长度、block allowlist、citation、TeachingAction fidelity、support/exposure 与安全校验后，才可发布 accepted RenderPayload。

#### RENDER-031 — Deterministic Baseline

任何已有纯文本 `reply_text` MUST 可通过固定 `render-payload/1.0` baseline 包装为单一 MarkdownBlock。该包装不得调用在线 LLM，也不得改变回复文本语义。

#### RENDER-032 — Failure

结构化候选无效时 MUST 丢弃不可信结构并回退到安全的单 MarkdownBlock 或 `message.content`。不得把渲染失败记录为 learner failure，也不得通过放宽 TeachingAction envelope 恢复。

### 5. Transport

#### RENDER-040 — HTTP

非流式消息响应与历史消息 query MAY 新增：

```text
message.render_payload: RenderPayloadV1 | null
```

这是 `/api/v1` additive minor evolution；`message.content` 的存在和既有含义保持不变。

#### RENDER-041 — Streaming

文本可继续通过现有 content delta/compatibility event 传输。结构化 payload MUST 只在完整验证后随 final/run_completed event 提交；客户端 MUST NOT 执行半截 JSON block。重连/幂等 replay MUST 返回已持久化的同一 payload。

### 6. Frontend Security

#### RENDER-050 — Safe Renderer

前端 MUST 使用 typed React component allowlist。MUST NOT 使用 `dangerouslySetInnerHTML`、执行 raw HTML/MDX、动态 import 模型指定组件或运行代码块。

#### RENDER-051 — URL and Media

链接协议 MUST allowlist 为 `http`/`https`。v1.0 Markdown image MUST disabled；`javascript:`、`data:`、`file:`、远程 tracking image 与任意 iframe/object/embed MUST blocked。

#### RENDER-052 — Formula Limits

公式 renderer MUST 禁止 trusted commands/external resources，并限制 expansion、size 与错误回显。公式错误 MUST 局部降级为可读源码，不得使整个对话页崩溃。

### 7. Tests and Acceptance Criteria

必须覆盖：strict schema、unknown major、unknown/extra fields、block/count/length limits、plain fallback、DB round-trip、idempotent replay、normal/history/stream equivalence、Markdown/GFM/math/card rendering、raw HTML/XSS/unsafe URL/remote image blocking、formula failure、citation traceability、TeachingAction envelope fidelity。

- `RENDER-AC-001`：历史纯文本消息无需回填即可正常显示。
- `RENDER-AC-002`：canonical reply 可生成并持久化 `RenderPayloadV1`。
- `RENDER-AC-003`：Markdown、GFM、公式与五类 card 可通过 typed renderer 显示。
- `RENDER-AC-004`：raw HTML、MDX、script、unsafe URL、remote image 与 executable code 不可执行。
- `RENDER-AC-005`：unknown/invalid payload 安全回退，不导致页面崩溃。
- `RENDER-AC-006`：HTTP normal、history query、SSE final/replay 返回同一 accepted payload。
- `RENDER-AC-007`：引用可追踪 SourceSpan；无法追踪的 citation 不发布。
- `RENDER-AC-008`：富文本/卡片不得扩大 SYS05 action envelope 或改变 canonical decision。

### 8. Forbidden Implementations

禁止：任意 HTML string 直出；`dangerouslySetInnerHTML`；MDX/动态组件执行；模型 JSON 未验证直传前端；magic fenced block 作为第二公共协议；卡片携带任意 command/tool/URL；历史消息在线 LLM 回填；渲染层修改 mastery/action/plan/review；Markdown/image 加载本地文件或远程 tracking resource。
