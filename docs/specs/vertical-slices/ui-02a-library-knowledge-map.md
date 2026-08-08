# UI-02A Canonical Library and Scoped Knowledge Map Vertical Slice

> 状态：Frozen  
> 实现入口：EXEC-016（DONE）
> 冻结日期：2026-08-08  
> 用户决策：采纳“Canonical 学习资料库 MVP + 拆分 UI-02A”  
> 范围：资料上传与处理恢复、版本化来源、结构化知识候选、范围化知识地图、来源 Inspector

## 1. Objective

在不改变 SYS01/SYS02 ownership、不把 SourceChunk/legacy KnowledgePoint 伪装成 KnowledgeUnit、不新增人工审核写命令的前提下，把 `/library` 从占位页交付为真实可用的私人资料库，并让用户从文档处理状态追踪到 KnowledgeUnit candidate 与可回放 SourceSpan。

本 Slice 是原 UI-02 umbrella 的第一阶段。Goals/Path/Evidence profile 保留给 UI-02B；UI-02A 不以资料库完成为由伪造这些页面的数据。

## 2. End-to-End Path

```text
current-user auth
→ GET /api/v1/workspace/library
→ upload PDF/EPUB/DOCX/Markdown/TXT
→ durable local outbox processing task
→ security scan
→ deterministic parse / structure recovery
→ immutable MaterialRevision + replayable SourceSpan
→ deterministic structural KnowledgeUnit candidates
→ rebuildable SourceChunk projection
→ GET /api/v1/workspace/knowledge-map?document_id=<uuid>
→ document list → scoped nodes/relations → SourceSpan Inspector
```

若没有可靠 relation，UI 必须显示“尚无可验证关系”，不得绘制装饰性 edge。章节顺序不得自动成为 prerequisite。

## 3. Current Reality and Baseline

- `/library` 是 UI-01 诚实占位页；旧 `/knowledge` 已 redirect 到 `/library`。
- `/api/v1/documents/**` 已支持上传、列表、状态、删除和 RAG；公开列表包含 UI 不需要的 storage metadata，不作为 UI-02A 页面 Query。
- 文档处理已生成 `MaterialRevision`、`SourceSpan` 和 `SourceChunk`，但 `minimal-binding-v1` 每文档仅生成一个 file-level `published/confidence=1.0` KnowledgeUnit；它只可作为历史兼容绑定，不得直接展示成成熟知识地图。
- 文档处理由进程内 `asyncio.create_task` 触发；任务本身不 durable，重启后可能遗留 pending/processing 文档。
- 没有 `/workspace/library`、`/workspace/knowledge-map`、SourceSpan Inspector Query。
- 冻结前基线：backend `255 passed / 1 skipped`，Ruff/mypy/Alembic PASS；frontend `31 passed`，production build PASS，npm high audit 0。

## 4. Scope

IN：

- `GET /api/v1/workspace/library` strict v1.0 current-user read model；
- `GET /api/v1/workspace/knowledge-map` strict v1.0，要求单一 `document_id` scope；
- 资料列表、上传、处理状态、筛选、重试提示和删除确认；
- 使用现有 outbox ledger/worker 实现 durable processing task、bounded retry、stale claim recovery 与启动 reconciliation；
- `deterministic-structure-v2`：从显式标题/结构生成 source-bound KnowledgeUnit candidate；无结构时仅生成诚实 file-level candidate；
- 同一 source checksum 在 parser/extraction semantic version 改变时形成新 MaterialRevision；
- `minimal-binding-v1` 只读兼容，自动排队重建到 v2；不得在 map 中继续显示为高置信 published truth；
- SourceSpan label/locator/text Inspector，所有 span 必须经 current-user document ownership；
- 文档、KnowledgeUnit、SourceChunk、relation 的视觉/文案区分；
- scope/node/edge/span 上限、stable ordering、private/no-store、partial/stale/empty/error semantics；
- desktop、1024、768、360、keyboard/focus/reduced-motion/accessibility tests。

OUT：

- Goal/Path/Evidence profile（UI-02B）；
- KnowledgeUnit/Relation 人工 review/publish/reject/supersede command；
- 自动 prerequisite 推断、GraphRAG、LLM knowledge publication；
- 网页抓取、音视频转录、笔记、代码仓库导入；
- persistent collection/tag/note、跨设备同步、云端对象存储；
- 新生产依赖、外部任务队列、图数据库、向量数据库；
- LearningGoal/Plan/Activity、LearnerState、TeachingAction、ReviewSchedule 写语义变化。

## 5. Read Contracts

### 5.1 Library Workspace V1

`GET /api/v1/workspace/library?status=&subject=&page=1&page_size=20` MUST：

- 只返回当前授权用户未删除文档；
- 不返回 `storage_path`、本地绝对路径、raw parser exception 或完整安全规则；
- 返回 document/revision/knowledge availability、processing/moderation status、稳定 reason codes 与计数；
- 按 `created_at desc, document_id` 稳定排序；
- 使用 `schema_version=1.0`、timezone-aware timestamps、`Cache-Control: private, no-store`。

### 5.2 Knowledge Map V1

`GET /api/v1/workspace/knowledge-map?document_id=<uuid>` MUST：

- 要求明确单文档 scope；无权限与不存在不得通过差异泄露其他用户资源；
- 只从 SYS01 current MaterialRevision 读取 KnowledgeUnit/Relation truth；
- `minimal-binding-v1` 返回 `PARTIAL + LEGACY_MINIMAL_BINDING_PENDING_REBUILD`，不得伪装 READY；
- candidate/published status 原样呈现；不得由 Query/UI 提升状态；
- SourceSpan 必须能回放且只返回所选 scope 所需的 bounded excerpt；
- 默认 cap：nodes ≤ 100、edges ≤ 200、source spans ≤ 300；超限返回 stable truncation reason，而非静默丢失；
- 无 relation 时返回空 edges + `NO_VERIFIED_RELATIONS`，不得推断章节 prerequisite。

## 6. Content and Processing Semantics

- SYS01-owned `content_knowledge_v1` revision stream 继续是本 Slice canonical truth；`DocumentChunk` 只是可重建 SYS02 projection。
- `deterministic-structure-v2` 只发布 candidate，不自动 verified/published。每个 candidate 必须绑定至少一个 current revision SourceSpan。
- candidate stable id 由 document identity + normalized explicit structure identity 确定；同标题未变化时 SHOULD 跨 revision 保持 identity。
- parser/extraction version 进入 MaterialRevision identity；升级 extraction 不覆盖旧 revision。
- upload transaction 与 durable processing outbox task 同事务提交；重复 worker execution 必须幂等。
- quarantined 内容不得进入 chunk projection/map learner-visible text；安全错误不记录为学习失败。

## 7. UI Contract

桌面布局：

```text
文档列表（选择/上传/状态）
→ 知识结构（节点列表 + 有证据时的关系）
→ Inspector（状态、版本、来源位置、原文摘录）
```

- 窄屏改为单列 drill-down，返回时保持选中文档/节点；
- processing/retry 状态使用 live region；
- 图结构必须有等价文本列表；
- 删除为现有 document command，必须二次确认，成功后清除选中/cache；
- candidate 使用“待建模/候选”文案，不使用“已掌握”；
- 不显示内部 SYS 编号、UUID 或路径作为主标签；审计详情可复制 ref/version。

## 8. Failure and Recovery

- pending/processing task 在 restart 后由 outbox reconciliation 恢复；
- transient parse/storage failure bounded retry，exhausted 后进入 failed/dead-letter，并提供可理解状态；
- unsupported/corrupt → rejected/failed；security risk → quarantined；
- projection failure不得删除 canonical revision，map 标 STALE/PARTIAL；
- library 列表局部可用时保留数据并显示 PARTIAL；
- upload/query unauthorized、not found、invalid scope 使用 stable structured error。

## 9. Acceptance Criteria

- `UI02A-VSLICE-AC-001`：真实 current-user 资料列表、上传、状态、筛选和删除可用，不暴露 storage/internal path。
- `UI02A-VSLICE-AC-002`：文档处理任务 durable、幂等、bounded retry，restart 后 pending/stale processing 可恢复。
- `UI02A-VSLICE-AC-003`：v2 KnowledgeUnit candidates 全部可追溯 current MaterialRevision SourceSpan；SourceChunk 不作为 node truth。
- `UI02A-VSLICE-AC-004`：legacy minimal binding 明确 compatibility/pending rebuild，不显示为成熟 published map。
- `UI02A-VSLICE-AC-005`：knowledge map 强制 current-user + single-document scope、caps、stable ordering、source/version/availability。
- `UI02A-VSLICE-AC-006`：无可靠 relation 时 edge 为空且诚实说明；章节顺序不产生 prerequisite。
- `UI02A-VSLICE-AC-007`：quarantined/grader-only/unauthorized 内容不进入 learner-visible map/Inspector。
- `UI02A-VSLICE-AC-008`：`/library` 三栏/单列 UI 覆盖 loading/empty/ready/partial/stale/error/unauthorized 与 live processing。
- `UI02A-VSLICE-AC-009`：1440/1024/768/360、keyboard/focus/reduced-motion、图的文本等价通过验证。
- `UI02A-VSLICE-AC-010`：frontend/backend/docs/diff gates 全部有真实结果；无删除测试、弱化断言或越界 ignore。
- `UI02A-VSLICE-AC-011`：无新 production dependency、外部服务、第二 truth 或跨 owner write；无 blocking SPEC GAP。
- `UI02A-VSLICE-AC-012`：只声明 UI Engineering/Contract/Security gates，Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 10. Gate

只有 `UI02A-VSLICE-AC-001..012` 全部满足时 UI-02A 为 DONE。若实现必须新增人工 publish/review、collection/tag/note、自动关系推断或其他未冻结写命令，必须 `BLOCKED_BY_SPEC_GAP`，不得用 frontend-only state 绕过。

## 11. R1 Frozen Amendment — Explicit Quarantine Reinspection

> 冻结日期：2026-08-08
>
> 用户决策：确认 `quarantined → imported` 显式新版策略复检；禁止自动解封。

资料库 MUST 在后端声明 `CONTENT_REINSPECTION_AVAILABLE` 时提供“使用新版策略重新检查”；
提交后展示 `CONTENT_REINSPECTION_PENDING` 并持续轮询。same-policy、checksum mismatch、任务耗尽必须
显示可理解错误。UI 不得自行改变文档状态，也不得把普通删除重传伪装成历史连续复检。

- `UI02A-R1-AC-001`：owner-only 显式复检 durable、幂等，旧 SafetyScanRun append-only。
- `UI02A-R1-AC-002`：复检等待/失败/仍隔离时无 chunk、map 或 learner-visible 内容。
- `UI02A-R1-AC-003`：新版策略通过后进入 imported/正常建模；真实历史 revision/run 可审计。
- `UI02A-R1-AC-004`：UI 仅在 AVAILABLE 时显示按钮，PENDING 时防重复并自动刷新。
