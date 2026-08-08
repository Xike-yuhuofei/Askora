# SPEC-D01 — Content Ingestion & Source Locator Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D01`  
> 冻结日期：2026-08-08  
> Owner：SYS01 Content & Knowledge  
> 上游：Canonical Design、`systems/01-content-knowledge.md`、`domain/domain-model.md`、UI-02A Frozen Baseline  
> 目的：把“能读取 EPUB”升级为可审计、可重放、保留结构的 canonical ingestion，而不改变现有 SourceSpan 公共语义。

## 1. Position

本合同是 `SYS01` 的增量实现合同，不 supersede 既有 `SYS01-*` / `DOMAIN-*` 要求。

UI-02A 已完成的 durable upload、security scan、`MaterialRevision`、`SourceSpan`、`deterministic-structure-v2` candidate、`SourceChunk` projection 是实现基线，MUST 复用；禁止建立第二条 document truth 流水线。

## 2. Required Pipeline

```text
RawAsset
→ security gate
→ MaterialRevision
→ deterministic format parser
→ DocumentIR
→ DocumentNode hierarchy
→ canonical linearized text
→ SourceSpan
→ downstream semantic/modeling stages
```

`SourceChunk`/embedding/index MUST NOT 出现在 canonical parse truth 之前。

## 3. Material Revision Identity

### D01-010

`MaterialRevision` MUST 保持 immutable。以下任一语义性变化 MUST 形成新 revision 或显式等价的新 revision identity：

- raw asset checksum 改变；
- parser semantic version 改变并可能改变结构/锚点；
- extraction semantic version 改变并要求重新解释 canonical content；
- 安全修复要求重新建模。

相同 raw checksum + 相同 parser/extraction semantic versions 的重复处理 MUST 幂等。

### D01-011

SafetyScanRun / reinspection 是 append-only 安全审计，不得通过覆盖历史 MaterialRevision 表示“重新检查”。Quarantine 未显式解除前不得进入 learner-visible modeling/projection。

## 4. DocumentIR

### D01-020

`DocumentIR` 是 SYS01 内部、版本化、可重建的解析中间表示，不是新的跨系统 canonical truth。至少包含：

```yaml
document_ir:
  document_id: uuid
  revision_id: uuid
  parser_version: string
  format: epub|pdf|docx|markdown|text
  root_node_id: uuid
  node_ids: [uuid]
  canonical_text_hash: string
  structure_hash: string
```

### D01-021

`DocumentIR` MUST 能在不调用在线 LLM 的情况下从固定 RawAsset + parser version 重建。

## 5. DocumentNode

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

## 6. Source Locator

### D01-040

`source_locator` 是 DocumentNode 的 SYS01-owned persisted value object，用于把 canonical SourceSpan 重放回原始载体。它不是第二 SourceSpan truth。

共同字段：

```yaml
kind: epub|pdf|docx|markdown|text
locator_version: string
source_path: string|null
node_path: string|null
```

### D01-041 — EPUB

EPUB locator MUST 至少保留：

```yaml
spine_index: integer
spine_item_id: string|null
href: string
nav_path: [string]
dom_path: string
```

并 SHOULD 保存有效的 `epub_cfi`；如果当前实现不能在不新增未批准生产依赖的前提下可靠生成 CFI，可暂缺 CFI，但 `spine + href + dom_path + content hash` MUST 足以稳定重放。实现不得伪造无效 CFI。

### D01-042 — PDF / DOCX / Text

- PDF SHOULD 保留 page + block/line locator；
- DOCX SHOULD 保留 paragraph/table cell path；
- Markdown/Text SHOULD 保留 heading/node path + offsets；
- 所有格式都 MUST 有 deterministic fallback locator。

## 7. SourceSpan Replay

### D01-050

现有 canonical `SourceSpan` 字段语义保持不变。新实现 MUST：

- 设置 `node_id` 指向对应 DocumentNode；
- 保留现有 material-linearized `start_offset/end_offset` 兼容语义；
- 通过 `node_id → DocumentNode.source_locator` 重放到原始载体；
- 通过 span text/hash 防止错误锚点静默成功。

### D01-051

Replay 结果 MUST 返回 `EXACT | RECOVERED | FAILED`：

- `EXACT`：locator + hash 精确匹配；
- `RECOVERED`：版本允许的 deterministic fallback 找回且 hash/上下文验证通过；
- `FAILED`：不能可靠定位。

`FAILED` anchor MUST NOT 支撑新的 published knowledge fact。

## 8. EPUB Structural Requirements

EPUB parser MUST 保持：

- spine reading order；
- TOC/nav hierarchy；
- XHTML heading hierarchy；
- paragraph/list boundaries；
- footnote/endnote relation；
- image/figure reference；
- internal anchor/link metadata。

MUST NOT 用 `strip HTML → whitespace normalize → flat text` 作为 canonical EPUB parse 结果；该路径仅可作为 legacy compatibility/fallback extraction，不得形成新 canonical structure truth。

## 9. Security

- archive bomb、path traversal、external entity/reference、oversized entry 等继续服从现有 security contract；
- XHTML/script/style/embedded prompt 作为不可信内容数据处理；
- parser 不得执行脚本、远程资源或文档内命令；
- quarantined/rejected 内容不得生成 learner-visible SourceChunk/KnowledgeUnit。

## 10. Observability

至少记录：

```text
parser_version
format
node_count
structure_hash
canonical_text_hash
anchor_exact/recovered/failed count
spine/nav mismatch
malformed resource count
processing latency
```

## 11. Tests

MUST 覆盖：

1. EPUB spine 顺序；
2. TOC / heading hierarchy；
3. footnote/internal link；
4. DOM locator replay；
5. CFI 存在时的 replay；
6. SourceSpan → node → original position；
7. parser version change creates traceable revision；
8. duplicate processing idempotency；
9. malformed EPUB bounded failure；
10. archive/path traversal safety；
11. replay failure blocks downstream publication。

## 12. Acceptance Criteria

- `D01-AC-001`：任一新 EPUB SourceSpan 可通过 `node_id` 重放至原始 XHTML 结构位置。
- `D01-AC-002`：spine/TOC/DOM 结构不会在 canonical parse 阶段被压平成不可恢复文本。
- `D01-AC-003`：固定 RawAsset + parser version 可 deterministic 重建相同 semantic DocumentIR。
- `D01-AC-004`：parser semantic version 改变不静默覆盖旧 MaterialRevision。
- `D01-AC-005`：anchor replay failed 的证据不能支持 published KnowledgeUnit/Relation。
- `D01-AC-006`：UI-02A durable processing、quarantine、idempotency 语义保持兼容。
- `D01-AC-007`：无第二 SourceSpan/Document truth store。

## 13. Forbidden Implementations

禁止：

- canonical EPUB ingestion 只保留纯文本和 chunk；
- 以 SourceChunk metadata 代替 DocumentIR/DocumentNode truth；
- 无验证地根据文本搜索“猜”原始位置并标 EXACT；
- parser 升级原地覆盖历史 revision；
- 为生成 CFI 自行引入未冻结生产依赖；
- Source locator 取得 SYS02/SYS06/SYS08 状态所有权。

## 14. Freeze Decision

`SPEC-D01`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。如实现必须改变现有 `SourceSpan` 公共字段含义、引入外部解析服务或新增生产依赖，必须报告 `SPEC GAP`，不得由 Codex 自主决定。