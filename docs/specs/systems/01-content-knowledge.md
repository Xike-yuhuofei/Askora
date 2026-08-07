# SYS01 — Content & Knowledge

> Spec ID：`SYS01-*`  
> 对应设计：4.1 内容解析与知识建模  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS01-001

4.1 的唯一职责是把不可信原始材料转换为**可版本化、可定位原文、可审核、可教学/评估**的规范知识模型。

### SYS01-002

4.1 是以下状态的唯一写入者：`SourceDocument`、`MaterialRevision`、`SourceSpan`、`SourceChunk`、`KnowledgeUnit`、`Concept`、`PrerequisiteRelation`、规范 `Misconception`、索引投影元数据。

## 2. Non-responsibility

4.1 MUST NOT：

- 判断用户 mastery；
- 选择 TeachingAction；
- 生成 LearningPlan；
- 计算 ReviewSchedule；
- 选择本轮最终 EvidenceBundle；
- 直接把材料中的练习当正式 AssessmentItem 发布；
- 执行最终用户交互。

## 3. Owned State

必须遵守 `state-ownership.md`。核心持久状态：

```text
RawAsset metadata
MaterialRevision
DocumentIR / DocumentNode
SourceSpan
KnowledgeUnit revision
Concept revision
KnowledgeRelation revision
PedagogicalAsset candidate
ExtractionRun
ReviewDecision
IndexProjection metadata
```

### SYS01-010

已发布知识对象必须采用 stable id + immutable revision。

## 4. Inputs

允许输入：

- 用户上传的 PDF/EPUB/DOCX/Markdown/TXT；
- 网页/音视频转录等未来受控来源；
- parser/extractor 配置；
- 人工 ReviewDecision；
- 4.6 提交的 prerequisite/path conflict evidence；
- 安全扫描结果。

所有外部内容 MUST 默认视为不可信数据，而不是系统指令。

## 5. Outputs

必须能够输出：

- SourceDocument/MaterialRevision；
- 可回放 SourceSpan；
- SourceChunk；
- KnowledgeUnit/Concept；
- PrerequisiteRelation；
- 规范 Misconception；
- PedagogicalAsset candidate；
- content/index version events；
- 可供 4.2/4.4/4.6 查询的只读接口。

## 6. Domain Objects

公共对象引用 `domain-model.md`。

内部对象至少允许：

```text
RawAsset
DocumentIR
DocumentNode
KnowledgeMention
PedagogicalAsset
ExtractionRun
ReviewDecision
IndexProjection
```

### SYS01-020

`KnowledgeMention` MUST NOT 与 canonical `Concept` 等价。

### SYS01-021

`SourceChunk` MUST NOT 与 `KnowledgeUnit` 等价。

## 7. Commands

建议公共命令：

```text
ImportContent
ParseMaterialRevision
ExtractKnowledgeCandidates
ReviewKnowledgeCandidate
PublishKnowledgeRevision
RebuildIndexProjection
ReportKnowledgeConflict
```

每个 command MUST 支持幂等语义或明确不可重复范围。

## 8. Events

至少产生/消费：

- `ContentImported`
- `ContentPublished`
- `KnowledgeRelationPublished`
- processing failed/review-required 类事件

关键发布决策 MUST 关联 DecisionTrace。

## 9. Algorithms

### SYS01-030：默认流水线

```text
validate file
→ compute checksum / revision
→ deterministic parse
→ recover structure
→ semantic segmentation
→ schema-constrained candidate extraction
→ bind SourceSpan
→ conservative entity resolution
→ relation inference
→ reverse evidence validation
→ graph quality checks
→ human review if required
→ publish revision
→ build replaceable projections
```

### SYS01-031：Baseline

MVP MUST 优先：

- deterministic parser；
- 结构规则；
- schema constrained LLM extraction；
- evidence binding；
- conservative merge；
- graph cycle/duplicate checks。

### SYS01-032：Hard prerequisite

hard prerequisite 自动发布要求高 precision。章节顺序、LLM 单次推断或低置信关系 MUST NOT 直接成为 hard prerequisite。

### SYS01-033：高级算法

不得自行引入 RL。监督模型可用于 entity resolution/candidate validation，但进入主路径前必须优于 baseline 并可回退。

## 10. Persistence

### SYS01-040

原始文件、规范内容、知识对象和索引投影必须逻辑分层：

```text
source of truth
→ canonical knowledge records
→ rebuildable lexical/vector/graph projections
```

图数据库/向量库若未来引入，默认只是 projection，不是第二事实源。

### SYS01-041

文档更新 MUST 形成新 MaterialRevision；受影响范围支持局部重算，stable KnowledgeUnit id SHOULD 尽量保留。

### SYS01-042

Published KnowledgeUnit/Relation 不能原地静默覆盖。

## 11. Failure Semantics

失败必须分类：

- unsupported/corrupted file → reject；
- security risk → quarantine；
- partial parser failure → partial + review_required；
- anchor failure → 不得发布受影响事实；
- low-confidence relation → candidate/review；
- projection build failure → canonical content 可保留，projection 标 stale/failed 并重建。

### SYS01-050

索引构建失败不得回滚已成功提交的 canonical content revision，除非该 revision 无任何可用访问路径且产品定义要求原子发布。

## 12. Idempotency

- 相同 checksum + import scope 重复导入 SHOULD 返回已有 revision；
- extraction run 必须绑定 parser/extractor/prompt/model version；
- projection rebuild 必须可重复执行；
- ReviewDecision 重放不得重复创建同一 published revision。

## 13. Observability

必须记录：

- parse/extract/review/index trace；
- parser/extractor/model versions；
- object/edge publish/reject reason codes；
- anchor replay failures；
- processing latency；
- quarantine count；
- relation cycle/duplicate count；
- index freshness。

关键指标：object/relationship P/R/F1、hard prerequisite precision、anchor replay rate、hallucinated unsupported object rate。

## 14. Security

### SYS01-060

上传内容中的 Prompt Injection 只能作为内容数据，不得覆盖 system/developer/policy 指令。

### SYS01-061

解析器必须限制文件类型、大小、压缩炸弹/路径穿越/外部引用等风险；具体阈值由 security spec 配置。

### SYS01-062

模型抽取不得拥有任意 shell、文件写入或网络副作用权限。

## 15. Tests

必须至少覆盖：

- PDF/Markdown 基础解析；
- SourceSpan anchor replay；
- revision 更新；
- duplicate import idempotency；
- KnowledgeUnit stable identity；
- hard prerequisite cycle/rejection；
- unsupported relation 无证据不得发布；
- prompt injection 文档不会控制系统；
- quarantined 内容不入检索；
- projection 重建不会改变 canonical facts。

## 16. Acceptance Criteria

- `SYS01-AC-001`：导入文档后任一 published KnowledgeUnit 可追溯到 SourceSpan。
- `SYS01-AC-002`：修改源文档产生新 MaterialRevision，旧 revision 仍可审计。
- `SYS01-AC-003`：低置信 hard prerequisite 不自动发布。
- `SYS01-AC-004`：重新分块不无条件改变 canonical KnowledgeUnit identity。
- `SYS01-AC-005`：图/向量索引可从 canonical records 重建。
- `SYS01-AC-006`：恶意文档指令不会触发未授权工具或改变系统策略。
- `SYS01-AC-007`：4.6 报告路径冲突只能形成 evidence/review，不直接改知识图。

## 17. Forbidden Implementations

禁止：

- 直接把 LLM 抽取 JSON 当已发布知识库；
- 没有 SourceSpan 的关键知识对象自动发布；
- 把章节顺序直接当 prerequisite；
- 用 vector index / graph database 作为唯一事实源；
- 重建 chunk 时重置全部 KnowledgeUnit id；
- 4.1 修改 mastery/plan/action/review；
- 让文档 Prompt Injection 进入系统指令层。

## Legacy Mapping

当前主要相关路径：

```text
apps/backend/app/services/documents/parsers.py
apps/backend/app/services/documents/document_service.py
apps/backend/app/services/knowledge_graph/kg_service.py
apps/backend/app/models/document.py
apps/backend/app/models/knowledge.py
```

`rag_service.py` 的检索/排序职责应逐步迁入 SYS02，而不是继续扩展在 SYS01。
