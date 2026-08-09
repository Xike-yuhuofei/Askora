# ADR-0008 — Library Management, Deduplication and OCR Governance

> Status: Accepted
> Date: 2026-08-09
> Decision authority: user-delegated Codex
> Authorized objective: 真正关闭 P1-04 资料管理并通过相关测试

## Context

UI-02A 已交付 current-user 资料列表、上传、处理恢复、精确学科筛选、删除确认、知识地图和 SourceSpan Inspector，但明确排除了 persistent tag/collection、新写命令和 OCR。当前实现以 `original_filename` 作为标题，把 raw checksum 放在审核 JSON 中，PDF 只读取数字文本；这些事实不足以支持规模化搜索、可纠正元数据、安全去重和扫描件复核。

P1-04 同时涉及公共领域对象、API/Command、数据库迁移、生产运行依赖、错误恢复和 UI 交互，必须先接受统一决策。

## Decision

### 1. Ownership

资料组织、文档元数据版本、重复候选/处理决定、OCR run/candidate/review decision 均由 SYS01 写入。UI/API/query assembler 不是 owner。SYS02 只消费由 SYS01 发布的 current SourceSpan/SourceChunk，不写资料管理状态。

### 2. SourceDocument metadata

`original_filename` 和 raw asset checksum 保持不可变来源事实。用户可编辑 `display_title`、`subject`、`author`、`language`；每次写入增加 `metadata_version`，使用 optimistic concurrency 和 idempotency receipt。元数据变化不得无意义创建 MaterialRevision。

标签和集合是 SYS01-owned personal organization state。v1 采用 flat collection + flat tag，多对多绑定；不实现嵌套目录、智能集合、云同步或自动分类。

### 3. Search projection

标题与正文搜索读取 `LibrarySearchProjectionV1`。它只保存 current revision 的可重建规范文本、source revision/index version 和 freshness；不是第二文档 truth。搜索必须 current-user scoped，隔离/拒绝/grader-only 内容不得进入正文匹配；正文命中必须返回 bounded excerpt 与 SourceSpan ref。

### 4. Duplicate governance

重复判断分为：

- `EXACT_DUPLICATE`：raw checksum 相同；
- `CONTENT_SIMILAR`：versioned normalized-content similarity 达到策略阈值；
- `REVISION_CANDIDATE`：标题/结构一致且内容高度相似，可能是同一资料新版。

系统只创建带算法版本、evidence、confidence/reason code 的 `DuplicateSuggestion`。不得自动合并 SourceDocument、MaterialRevision、KnowledgeUnit、学习记录或 evidence。用户只能显式选择保留、忽略、可恢复归档，或把候选作为新 revision；最后一种必须重新走安全扫描、解析、SourceSpan 和 projection pipeline。

### 5. Recoverable archive and batch operations

P1-04 的用户界面用可恢复 archive/restore 取代物理删除。archive 不删除 raw asset；永久删除继续属于 P1-03 数据控制合同。批量 v1 只接受显式 document IDs（最多 100），支持 tag/collection/subject/archive/restore；所有操作必须 owner-scoped、幂等、可预览，并返回逐项结果。不得以“当前查询的全部结果”作为未固定集合执行破坏性操作。

### 6. OCR

扫描 PDF 使用 local-only `TesseractOcrAdapterV1`，通过无 shell 的 bounded subprocess 调用；不发送外部服务。PDF 先按页检测数字文本覆盖率，只有明确请求的 PDF 才进入 durable OCR task。

`OCRRun` 和 `OCRCandidate` append/versioned：固定 raw checksum、engine/version、languages、policy、page/bbox、text、confidence 和 image hash。OCR confidence 是引擎信号，不是校准事实概率。候选默认不得进入 learner-visible retrieval、KnowledgeUnit publish 或普通正文搜索。

用户逐块修正、接受或拒绝。只有显式接纳后，SYS01 才以相同 raw checksum + 新 parser/extraction semantic version 创建新 MaterialRevision，生成带 PDF page/bbox locator 的 SourceSpan 并重建 projection。旧 revision 和原始 PDF 不覆盖。

### 7. Failure and privacy

OCR engine unavailable、timeout、invalid output、partial page failure、projection stale 和 version conflict 使用稳定错误码。失败不得记为学习者错误。日志不保存整页图像或完整 OCR 文本。所有 document/tag/collection/suggestion/run/candidate access 必须验证 owner。

## Alternatives

### A. 单个大 Slice 一次实现全部能力

未采用。搜索、元数据、破坏性去重和 OCR 的迁移/失败模型不同，难以独立验证和回滚。

### B. 只做搜索和前端标签

未采用。frontend-only 标签形成第二 truth，也无法关闭去重和 OCR 缺口。

### C. 外部云 OCR

未采用。会向新第三方发送私人资料，产生授权、费用和合规变化；当前目标可由本地引擎完成。

## Migration and rollback

- additive tables/columns；旧 `subject/original_filename` dual-read compatibility 有明确退休条件；
- backfill `display_title=original_filename`、`metadata_version=1`、raw checksum/search projection；
- 新 UI 只写 canonical metadata command；旧字段停止作为主动写入口；
- migration 可 downgrade 删除新 projection/organization/candidate/run 表，不删除 raw asset、旧 revision 或学习事实；
- OCR accepted revision 采用 forward-fix/superseding revision，不回写历史。

## Verification and claim boundary

三个独立 Slice/EXEC 必须覆盖 contract、architecture、SQLite/PostgreSQL migration、auth、idempotency、concurrency、recovery、security、frontend、responsive/accessibility 与真实本地 OCR。完成仅证明 Engineering、Policy/Ownership、Security 和产品可用性；Learning Evidence 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
