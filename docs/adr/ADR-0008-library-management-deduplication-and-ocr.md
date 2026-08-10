# ADR-0008 — Library Management, Deduplication and OCR Governance

> Status: **partially superseded for v1 product scope**  
> Date: 2026-08-09  
> Supersession date: 2026-08-10  
> Decision authority: user-delegated Codex  
> Authorized objective: 真正关闭 P1-04 资料管理并通过相关测试  
> Current upper authority: `docs/product/PRODUCT-POSITIONING.md`  
> Current implementation contracts: `docs/specs/systems/01-library-management.md`, `docs/specs/interfaces/content-ingestion-contract.md`

## Current v1 Supersession

本 ADR 是在较早“Library + full local OCR”范围下形成的历史决策。最新 `PRODUCT-POSITIONING.md` 已冻结：

- Material 必须属于 Workspace；
- v1 不存在独立 Global Material Library；
- Material 与 LearningProject 是同一 Workspace 内多对多关系；
- 从 Project 移除 Material 只删除关系，不删除 Material；
- 普通删除采用 `Normal → Trash → Permanent Delete`；
- Import = ingest + copy 到 Askora managed local storage；
- v1 core import 只要求 EPUB、文本型 PDF、Markdown、TXT；
- v1 **不建设完整 OCR Pipeline**，扫描 PDF 可以识别为无法可靠提取文本并提示；
- Redis/PostgreSQL/外部 OCR 服务不得成为 v1 最终用户运行前提。

因此以下历史决策已被上位产品定位 supersede 或降级：

1. **完整 OCR 是 P1-04/v1 必需 release capability** → superseded。OCR 仅可作为 legacy/experimental/optional local capability，不阻塞 v1 core release。
2. **current-user scoped global library** → superseded。所有 Material/Search/Dedup/Batch 必须先有 Workspace scope；默认无 cross-workspace global search/library。
3. **archive/restore 作为普通删除产品语义** → 被两阶段 Trash/Permanent Delete 语义取代。历史 archive MAY 迁移为 Trash/legacy lifecycle projection。
4. **document IDs 是最高资料对象** → 当前产品语义以 Workspace-scoped Material + managed SourceFile 为上位对象；`SourceDocument` MAY 作为 SYS01 内部/compatibility content record 保留。
5. **SQLite/PostgreSQL migration 都是 release runtime baseline** → PostgreSQL 仅为 CI/兼容测试；v1 production baseline 是 SQLite。

以下原则继续有效：

- SYS01 独占 Material/content metadata 与 content-side duplicate decision；
- raw SourceFile/checksum 与历史 MaterialRevision 不静默覆盖；
- Search projection 可重建，不是第二资料 truth；
- duplicate detection 只形成建议，不自动 merge/delete；
- metadata/duplicate commands versioned/idempotent；
- learner-visible SourceSpan 必须有 provenance；
- optional OCR 若保留，其 candidate 在明确接纳前不得进入普通学习/retrieval；
- 外部云 OCR 不得无新的产品/隐私授权自动发送私人资料。

## Historical Context

UI-02A 当时已交付资料列表、上传、处理恢复、筛选、删除确认、知识地图和 SourceSpan Inspector，但缺少 persistent tag/collection、新写命令和 OCR。现有实现以 `original_filename` 作为标题，把 raw checksum 放在审核 JSON 中，PDF 只读取数字文本；这些事实不足以支持规模化搜索、可纠正元数据、安全去重和扫描件复核。

P1-04 同时涉及公共领域对象、API/Command、数据库迁移、生产运行依赖、错误恢复和 UI 交互，因此当时建立了本 ADR。

## Retained Decision

### 1. Ownership

Material/content metadata version、duplicate candidate/decision 由 SYS01 写入。UI/API/query assembler 不是 owner。SYS02 只消费由 SYS01 发布的 current SourceSpan/SourceChunk，不写资料管理状态。

Workspace / LearningProject / ProjectMaterial relationship 由当前 Workspace/Product Organization contract 管理；SYS01 不因持有 Material 内容而取得 Project owner 权限。

### 2. Material metadata

`original_filename` 和 managed SourceFile checksum 保持不可变来源事实。用户可编辑 `display_title`、`subject`、`author`、`language`；每次写入增加 `metadata_version`，使用 optimistic concurrency 和 idempotency receipt。元数据变化不得无意义创建 MaterialRevision。

标签和集合若继续存在，只能是 Workspace-scoped optional personal organization state；不得形成跨 Workspace Global Material Library。

### 3. Search projection

标题与正文搜索读取可重建 search projection。projection 只保存 current revision 的可重建规范文本、source revision/index version 和 freshness；不是第二 Material truth。正文命中必须返回 bounded excerpt 与 SourceSpan ref。

所有 search/cache 必须 workspace-scoped；默认不得跨 Workspace。

### 4. Duplicate governance

重复判断 MAY 使用：

- `EXACT_DUPLICATE`：raw checksum 相同；
- `CONTENT_SIMILAR`：versioned normalized-content similarity 达到策略阈值；
- `REVISION_CANDIDATE`：标题/结构一致且内容高度相似，可能是同一资料新版。

系统只创建带算法版本、evidence、confidence/reason code 的 `DuplicateSuggestion`。不得自动合并 Material、MaterialRevision、KnowledgeUnit、学习记录或 evidence。

用户可以选择使用已有资料、明确创建新副本、取消导入，或在当前合同允许时把新文件作为新 revision candidate。跨 Workspace candidate 默认不得暴露另一 Workspace 的 metadata 或自动复用。

### 5. Trash / relationship / batch operations

当前产品语义：

```text
Remove Material from Project
→ relationship only

Delete Material
→ Trash
→ explicit/policy Permanent Delete
```

Trash 不删除 managed SourceFile；Permanent Delete 继续服从 Data Control / no-resurrection contract。

批量操作只能作用于固定、显式、同一 Workspace 的 Material IDs，必须 owner/workspace scoped、幂等、可预览，并返回逐项结果。

## Historical OCR Decision — No Longer v1 Core

历史实现选择了 local-only `TesseractOcrAdapterV1`、durable OCRRun/OCRCandidate、人工接纳后形成新 MaterialRevision。这套设计 MAY 继续作为可选/实验/legacy能力存在，但：

- 不再是 v1 core capability；
- 不再是 v1 release gate；
- OCR engine unavailable 不应阻塞 EPUB/文本 PDF/Markdown/TXT；
- 扫描 PDF 可以安全返回 unsupported/partial extraction；
- 不应继续扩展为完整 layout/table/formula/vision pipeline，除非未来 Product Positioning 重新冻结。

若 optional OCR 仍启用：candidate 默认不得进入 learner-visible retrieval、KnowledgeUnit publish 或普通正文搜索；失败不得记为学习者错误；日志不保存整页图像或完整 OCR 文本。

## Historical Alternatives

### A. 单个大 Slice 一次实现全部能力

未采用。搜索、元数据、破坏性去重和 OCR 的迁移/失败模型不同，难以独立验证和回滚。

### B. 只做搜索和前端标签

未采用。frontend-only 标签形成第二 truth。

### C. 外部云 OCR

未采用。会向新第三方发送私人资料，产生授权、费用和合规变化。该拒绝原则在当前 v1 仍有效；本地 OCR 本身则已从核心范围降级。

## Current Migration Direction

```text
legacy SourceDocument/current-user library
→ Workspace-scoped Material
→ managed SourceFile
→ ProjectMaterial relationships
→ Workspace-scoped search/dedup projection
→ Trash/Permanent Delete lifecycle
```

- `display_title`/metadata version 可保留；
- historical document IDs MAY 作为 compatibility refs，但新业务语义必须能解析 Material + Workspace；
- search/index/fingerprint 是可重建 projection；
- archive MAY 映射为 Trash/legacy lifecycle state，但不得再定义新的普通删除语义；
- historical OCR records 可保留审计/optional usage，不需要为 v1 新数据强制创建；
- PostgreSQL 测试兼容可以继续，但不进入 production-local dependency。

## Verification and Claim Boundary

当前 v1 验证重点：

- Workspace isolation；
- Material/SourceFile managed copy；
- metadata version/idempotency；
- search projection rebuild；
- duplicate advisory/no auto merge；
- ProjectMaterial relationship semantics；
- Trash/Restore/Permanent Delete；
- scanned PDF unsupported/partial behavior；
- no OCR/PostgreSQL/Redis production prerequisite。

历史 OCR 自动化可以继续作为 optional regression，但不得用其存在扩大 v1 产品范围。

完成仅证明 Engineering、Policy/Ownership、Security 和资料管理正确性；Learning Evidence 不因此自动提升。

## Supersedes / Superseded By

从 2026-08-10 起：

- OCR-as-v1-core、global/current-user library scope、archive-as-primary-delete 等 mechanics 被 `PRODUCT-POSITIONING.md` 与最新 SYS01/D01 Spec supersede；
- metadata ownership、provenance、duplicate-as-suggestion、rebuildable search projection 等原则继续有效。

本 ADR 保留为历史决策记录，不得反向覆盖当前 Product Positioning。
