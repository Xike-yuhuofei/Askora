# ADR-0021 — UserNote Ownership and Source Inspection Boundary

Status: accepted
Date: 2026-08-11
Decision owners: user-authorized Askora architecture governance
Decision authority: user-delegated Codex；用户于 2026-08-11 明确采纳“先冻结 UserNote + Current Material Spec，再实现 Backend Foundation，最后执行 EXEC-070”的建议并要求开始执行
Authorized objective: 冻结 EXEC-070 所需的 durable UserNote owner、save/conflict/recovery contract 与 Current Material exact source-inspection handoff；本决策不修改产品代码
Upper authority: `docs/product/PRODUCT-STRATEGY.md`, `docs/product/PRODUCT-POSITIONING.md`, `docs/product/PRODUCT-DEFINITION.md`
Affected specs: `state-ownership.md`, `system-architecture.md`, `domain-model.md`, `user-note-source-inspection-contract.md`, `persistence-contract.md`, `api-contract.md`, `error-contract.md`, `recovery-contract.md`, `data-control-contract.md`, `schema-versioning.md`, UI read-model / LCMS / UI-04 contracts

## Context

Product Definition 已把 `UserNote` 定义为用户围绕学习材料或学习过程主动沉淀的个人笔记，并把 source-grounded citation/provenance 与学习笔记纳入 v1。Experience 与 UI contracts 进一步要求：

- Learning Notes 是 Workspace-scoped、anchored、versioned durable data；
- autosave 必须诚实区分 `SAVING / SAVED / FAILED / CONFLICT / RECOVERABLE`；
- Current Material 由 citation / view-source 在 Right Rail 中打开；
- Material / SourceSpan 必须属于当前 Workspace，跨 Workspace fail closed；
- frontend/localStorage 不能成为 UserNote 或 Material 的第二 truth。

但在本 ADR 之前，current contracts 只声明 `UserNote` 是 durable fact，没有指定唯一 writer、query/command、optimistic concurrency、durable recovery 或 erasure/export mechanics。ADR-0020 也明确 deferred `CAPTURE_NOTE`；EXEC-075 只启用了 `ASK_FOLLOW_UP`，`INSPECT_SOURCE` 尚无完整可执行 handoff。当前代码没有 UserNote model/repository/API，Current Material 也没有 exact `Material → MaterialRevision → SourceSpan` scoped query。

因此 EXEC-070 不能合法使用 frontend-only state、localStorage、mock API 或 filename/summary fallback 制造“已完成”。必须先冻结 owner 与公共接口，再由独立 Backend Foundation EXEC 实现。

## Decision

### 1. UserNote owner

`UserNote` 的唯一 writer 是 **Platform Workspace Notes**。

Platform Workspace Notes 是 Workspace 下的 durable personal-artifact owner，不是第九个 Learning Core system。它只拥有：

- UserNote identity、Workspace scope、anchor、user-authored content 与 version chain；
- UserNote save command receipt / idempotency record；
- unresolved conflict recovery draft 与显式 resolution receipt；
- UserNote lifecycle / erasure integration。

它不得写 Material/SourceSpan/Knowledge truth、LearningActivity/Plan、TeachingAction、AssessmentResult、LearnerState/Mastery、ReviewSchedule、Message/transcript 或 Retrieval truth。

SYS01 继续拥有 Material content semantics、MaterialRevision 与 SourceSpan；SYS02 继续拥有 EvidenceBundle/RetrievalTrace；SYS08/LCMS 只保存 exact refs 与 interaction result，不取得 UserNote writer 权限。

### 2. UserNote aggregate and anchor

每个 UserNote 使用 stable `note_id`、mandatory `workspace_id` 与单调 `version`。公开 v1 anchor kinds 固定为：

```text
LEARNING_ACTIVITY
STAGE
MATERIAL
SOURCE_SPAN
FREE
```

- `LEARNING_ACTIVITY` 必须引用 exact SYS06 LearningActivity；
- `STAGE` 必须引用 exact SYS05 TeachingAction；
- `MATERIAL` 必须引用 exact current-Workspace Material；
- `SOURCE_SPAN` 必须同时 pin exact Material、MaterialRevision、SourceSpan；
- `FREE` 不携带 owner ref，但仍必须属于 current Workspace。

Anchor 在 UserNote 创建后不可由普通 autosave 静默改变。未来若需要 move/re-anchor，必须使用独立 versioned command；不能用内容保存顺带改 scope。

### 3. Save, concurrency and autosave

Canonical write 是 `SaveUserNoteV1`：

- client 预先生成 stable `note_id`；
- create 必须使用 `expected_version=0`；
- update 必须使用当前 exact `expected_version`；
- 每次 command 必须带 current `workspace_id`、完整 anchor 与 `idempotency_key`；
- owner 以 append-version + optimistic concurrency 保存；
- duplicate key + identical payload 返回原 receipt/result；duplicate key + different payload 拒绝；
- 禁止 last-write-wins、frontend timestamp winner 或 silent merge。

Autosave 必须 single-flight。同一 note 的较新 dirty draft MAY 排队，但不得与旧请求并发覆盖。只有 owner 返回 durable receipt 与 accepted exact note version 后，UI 才能显示 `SAVED`。

### 4. Conflict and durable recovery

Version conflict 返回 HTTP 409 + stable `USER_NOTE_VERSION_CONFLICT`，并携带 current durable note ref/view 与 owner-persisted `UserNoteRecoveryDraftV1` ref。提交内容不得覆盖 current note，也不得只留在浏览器内存后声称可恢复。

冲突恢复只能由用户显式选择：

```text
KEEP_CURRENT
REPLACE_WITH_DRAFT
SAVE_MERGED
```

`REPLACE_WITH_DRAFT` / `SAVE_MERGED` 必须重新验证 current version 并追加新 note version；`KEEP_CURRENT` 只解决 recovery draft，不重写 note。再次冲突继续返回 409，不自动 merge。

`RECOVERABLE` 只表示 owner query 找到 unresolved durable recovery draft。Local Server 不可达、请求超时或 browser-only dirty state 只能显示 `FAILED` / data-at-risk；UI 必须保留当前进程内输入并在 rail/route/Workspace 离开前显式阻止或确认，但不得把内存、localStorage、sessionStorage 或 IndexedDB 描述为 durable recovery。

### 5. Source truth and inspection query

Current Material 不建立新 Material owner或持久化副本：

- Material / MaterialRevision / SourceSpan truth 继续由 SYS01 提供；
- Workspace membership/scope 继续服从 Platform Workspace + SYS01 canonical refs；
- application source-inspection query 只读组合 exact refs，不写业务状态、不调用 LLM；
- SYS02 EvidenceBundle 只提供 provenance input，不成为 Material/SourceSpan writer；
- Right Rail tab/position/open state 是 presentation state，不是 source truth。

Canonical query 使用 current Workspace + exact `material_id` + exact `revision_id` + optional exact `source_span_id`。返回 strict `SourceInspectionViewV1`，包含 readable label、exact refs、bounded canonical excerpt、locator、current-revision indicator 与 `READY | MISSING | STALE`。

- `READY`：exact revision/span 可回放；历史但仍可回放的 accepted revision可以 READY，同时 `is_current_revision=false`；
- `MISSING`：未提供 SourceSpan，或 current-Workspace material 已验证但 exact span/source content 不再可用；不得用 filename、AI summary、模型记忆或其他 span 补齐；
- `STALE`：exact refs 存在但 anchor 已 invalidated、不可重放或版本关系不再可信；不得呈现为 READY。

foreign Workspace 与不存在 Material 使用同一 404/not-found 外观，不泄露对象存在性。不得回退到 global Material、其他 Workspace、current mutable revision 或相似文件。

### 6. LCMS citation / view-source handoff

ADR-0020 的 `INSPECT_SOURCE` action vocabulary 保持兼容；现有 `command_contract_ref=SYS02.InspectSourceV1` 不在 LearningMessage 1.0 中静默改名。它表示从 EvidenceBundle/citation 进入 source-inspection application façade，不授予 SYS02 source writer 权限。

只有 learner-visible EvidenceBundle 同时具备 exact current-Workspace Material、MaterialRevision、SourceSpan refs 时，LCMS 才能发布 AVAILABLE `INSPECT_SOURCE`。Invocation 必须重验 message/block/capability/version/workspace/ref coherence；成功结果返回 exact source refs 与：

```text
next_transition.kind = OPEN_SOURCE
next_transition.target_system = SYS01
```

Right Rail 随后用 exact refs 调用 `SourceInspectionQueryV1`。缺 exact refs 的 legacy citation 保持 unavailable；模型生成 citation、filename-only citation 或 current-revision fallback 不得升级为 inspect capability。

本 ADR 不启用 `CAPTURE_NOTE`。UserNote owner 已冻结不等于 Message V1 自动新增 note capability；若未来需要 source-to-note/message-to-note action，必须单独冻结 capability schema 与 exposure/confirmation semantics。

### 7. Persistence and data lifecycle

Backend Foundation 使用 SQLite durable tables/repository 表达 UserNote current aggregate、append-only versions、idempotent receipts 与 unresolved recovery drafts。`workspace_id` 必须直接持久化并参与 index/constraint；`(note_id, version)` 与 idempotency scope 必须唯一。

Recovery Package 包含这些 SQLite durable records。User Data Export 的 `LEARNING_RECORDS` allowlist 包含 note id/workspace/anchor/content/version/timestamps 与 unresolved recovery draft。`LEARNING_RECORDS` / `ALL_PERSONAL_DATA` erasure 删除相应 UserNote content、versions/recovery drafts，并写入既有 erasure checkpoint。

Material/Document permanent delete 默认不删除用户笔记正文；它必须使相关 MATERIAL/SOURCE_SPAN anchor 显式 `MISSING`/invalidated，并在 preview/report 中说明影响。只有显式 UserNote/LEARNING_RECORDS/ALL_PERSONAL_DATA erasure 才删除 note content。Projection/restore 不得复活已擦除笔记。

## Alternatives Considered

### A. SYS01 owns UserNote

Rejected. UserNote 可引用 Material/SourceSpan，但其正文是 user-authored personal artifact，不是 canonical content/knowledge truth。让 SYS01 写 UserNote 会混淆“用户写了什么”与“资料/知识是什么”，并扩大 SYS01 的 data-control 与 conflict/recovery 职责。

### B. Platform Workspace Notes owns UserNote

Accepted. 它与 Workspace scope、个人 durable artifact、export/erasure 相符，同时不新增 Learning Core owner，也不授予 frontend 或 SYS08 写权限。代价是增加一个明确 platform repository/application port，但边界与冲突处理更可审计。

### C. Frontend/localStorage owns note autosave

Rejected. 它无法提供跨刷新 durable receipt、server-side optimistic concurrency、backup/export/erasure/no-resurrection，也会在 Workspace switch 时形成第二 truth。

### D. Current Material reads excerpt directly from Message/citation payload

Rejected. Message payload 是当时的 presentation artifact，不能证明 current scope、Material lifecycle 或 SourceSpan replay；直接呈现会复制 source truth并可能泄露跨 Workspace refs。

### E. Exact SYS01 source-inspection query behind application handoff

Accepted. 它复用 canonical MaterialRevision/SourceSpan，允许历史 exact revision replay，并用统一 scope/version/error contract fail closed。代价是 LCMS capability 与 Right Rail 需要一次明确 handoff/requery。

## Consequences

### Positive

- EXEC-070 获得真实 owner query/command，不需要 mock/localStorage durable truth；
- conflict 与 recovery 不再依赖浏览器生命周期；
- SourceSpan available/missing/stale 与 cross-Workspace 行为可自动测试；
- LCMS citation/view-source 与 Right Rail 通过 exact refs 连接，不复制 Message truth；
- UserNote backup/export/erasure/no-resurrection 进入既有数据治理链。

### Cost / Risk

- 需要新 SQLite schema/migration、repository、application service、API 与 data-control registry；
- conflict recovery draft 会保存一份明确标识的用户内容，需要同等隐私/备份/擦除保护；
- 现有 Material/SourceSpan 的 JSON compatibility storage 需要严格 adapter，不能假设全新规范表；
- EXEC-070 的 Allowed Files 必须包含真实 parent integration/API adapter files，否则仍会被 scope gate 阻断；
- 本地 server 完全不可达时无法创造 durable recovery，UI 只能诚实提示风险并防止静默离开。

## Ownership and Duplicate-truth Invariants

- Platform Workspace Notes 是 UserNote/RecoveryDraft 唯一 writer；
- SYS01 是 MaterialRevision/SourceSpan 唯一 writer；
- query assembler、API、LCMS、Right Rail 都不是 owner；
- recovery draft 明确标记为 unresolved user content，不是 current UserNote；
- message excerpt/citation 不成为 source truth；
- localStorage/sessionStorage/IndexedDB 不保存 canonical note/material content；
- no global notes library / no global material fallback / no cross-Workspace merge。

## Security / Privacy / Replay / Idempotency

- 所有 note/source query/command 绑定 current LocalOwner + current Workspace；
- foreign/missing resource 不可枚举；error/details/log 不含绝对路径、Prompt、grader-only、secret 或其他 Workspace ref；
- note body、recovery draft、source excerpt 受大小限制与 safe Markdown/plain-text rendering；禁止 raw HTML/MDX/script；
- duplicate save/resolve/invocation 返回原 receipt，不产生第二 version/recovery/result；
- historical source inspection pin exact accepted revision，不用 online LLM/current mutable state回填；
- material/note erasure 后 replay/restore 必须消费 erasure checkpoint。

## Migration / Rollback

1. 先建立 strict contracts/tests；
2. additive 创建 UserNote/version/recovery/receipt tables 与 privacy/data-control registration；
3. 实现 current-Workspace note query/save/resolve；
4. 实现 SYS01 exact source-inspection query；
5. 启用具 exact refs 的 LCMS Evidence/`INSPECT_SOURCE → OPEN_SOURCE`；
6. Backend Foundation 全部 gate 通过后，EXEC-070 才可解除 dependency block。

当前没有 canonical durable UserNote legacy source，因此 migration 不从 frontend/localStorage/mock 自动导入或猜测笔记。Rollback 应停止新 endpoint/capability并保留 additive tables/data；旧版本可忽略新表。若 migration 已写入用户笔记，禁止 downgrade 丢表，使用 forward-fix。

## Validation

至少验证：

- owner architecture/no cross-owner ORM write；
- create/update/duplicate idempotency/monotonic version；
- autosave single-flight contract 与 owner receipt；
- 409 conflict 持久化 recovery draft，不覆盖 current；
- keep/replace/merge resolution 与 second conflict；
- restart 后 recovery 可查询；server unavailable 只显示 FAILED；
- Workspace switch isolation、foreign/missing indistinguishable；
- exact Material/Revision/Span coherence、historical revision replay、MISSING/STALE；
- LCMS Evidence exact refs 与 `INSPECT_SOURCE → OPEN_SOURCE`；
- backup/restore/export/erasure/material-delete anchor invalidation；
- no secret/path/prompt/grader-only/source-content leakage；
- SQLite fresh upgrade / current upgrade / Alembic single head/check。

本 ADR 的通过只冻结工程合同，不证明 EXEC-076 或 EXEC-070 已实现，也不证明学习效果。

## Supersedes / Superseded By

本 ADR additive specializes ADR-0016 的 Workspace scope、ADR-0018/0019 的 UI Workspace boundary 与 ADR-0020 的 deferred UserNote/source-inspection handoff。它不 supersede Product Definition、SYS01/SYS02 ownership、Teaching Policy、Assessment、LearnerState、Review 或 LCMS Message 1.0 semantics。

Superseded by: none.
