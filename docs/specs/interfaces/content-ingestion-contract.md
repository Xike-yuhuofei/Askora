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

每个 Material/SourceFile import MUST 属于一个明确 Workspace。导入任务、MaterialRevision、SourceSpan、derived index/rebuild task MUST 能解析该 workspace scope。

不得因为同一 LocalOwner 存在多个 Workspace 而默认建立全局 Material scope。

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
  workspace_id: uuid
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
