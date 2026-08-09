# P1-03 Data Control and Recovery Canonical Design

> 状态：Canonical Design / Accepted Baseline
> 日期：2026-08-09
> 授权：用户采纳 P1-03 推荐方案，并明确要求最终真正关闭 P1-03、通过相关测试
> 下游：ADR-0103、Data Control Contract、P1-03 Vertical Slice、EXEC-1031～1034

## 1. Product Promise

Askora 的私人桌面模式必须让用户在 App 内完成四件事：创建并验证加密恢复点、在不破坏现有数据的前提下恢复、导出可读的个人数据、按明确范围删除数据。产品不得把普通目录复制、未验证 ZIP、数据库软删除或“测试能启动”描述为完成。

P1-03 的正式完成范围是 macOS 私人桌面模式的本地 SQLite 数据集。Docker/PostgreSQL 继续遵循部署管理员流程，直到独立 adapter 通过同等级合同；桌面能力不得暗示已覆盖服务模式。

## 2. Data Surfaces

恢复数据面分为：

- canonical relational state：SQLite 数据库；
- raw assets：用户上传资料；
- rebuildable projections：chunk/index/map 等可失效重建数据；
- recovery secrets：解密数据库内受保护字段所必需的 KEK；
- control metadata：恢复包 manifest、校验值、恢复报告与删除 checkpoint。

浏览器 Session/cache、日志、Redis、临时文件、构建产物和模型供应商 API Key 不属于恢复包。JWT secret 恢复时重新生成，使恢复前会话失效。普通用户导出永不包含 KEK、JWT、密码哈希、供应商密钥、内部 Prompt 或 grader-only 内容。

## 3. Recovery Architecture

桌面恢复点必须在后端停止写入时创建。Electron 只负责桌面生命周期、用户选址、维护进程与原子目录切换；Python maintenance core 负责 SQLite 快照、加密容器、manifest、校验、迁移 preflight 和 reconciliation。UI 只提交请求和展示报告，不成为恢复 truth。

恢复包使用版本化、分块 AEAD 加密容器；每个包保存固定格式 manifest、数据库快照、受管原始资料、恢复所需的加密 secrets 与删除 checkpoint。密钥从独立随机 Recovery Key 派生；设备保存副本必须受平台安全存储保护，跨设备恢复要求用户提供 Recovery Key。

恢复流程必须在 staging 完成：

```text
authenticate/decrypt
→ container + manifest integrity
→ safe extraction
→ SQLite integrity + foreign keys
→ schema compatibility / forward migration
→ raw asset checksum
→ owner-reference reconciliation
→ erasure checkpoint application
→ projection invalidate/rebuild
→ atomic activation
→ readiness check
→ durable report
```

任一步失败时当前数据保持不变。激活前创建 rescue snapshot；激活后 readiness 失败则回滚。恢复不得调用在线 LLM 补齐历史。

## 4. Backup and Retention

恢复点原因固定为 `MANUAL`、`SCHEDULED`、`PRE_MIGRATION`、`PRE_RESTORE`、`POST_ERASURE`。只有完整写入、重新打开解密、manifest/hash/SQLite 校验通过的恢复点才可标记 `VERIFIED`。

默认策略保留最近 7 个日恢复点、4 个周恢复点、6 个月恢复点；这是可配置产品默认值，不是普适常数。最后一个 verified、最新 pre-migration、最新 pre-restore 与最新 post-erasure 恢复点不得被普通 retention 清理删除。

scheduled backup 失败必须显式告警但不自动把系统故障记为用户错误；pre-migration backup 失败必须阻止 migration。恢复点所在磁盘与主数据同盘时，UI 必须说明它能防迁移/误操作损坏但不能防整盘丢失，并允许选择外部目录。

## 5. Export Architecture

用户导出与恢复包是两个不同合同：

- Recovery Package：lossless、加密、Askora-only、可恢复；
- User Data Export：current-user scoped、可读、版本化、不可直接作为数据库恢复输入。

导出采用 manifest + JSON/JSONL + 可选原始资料。每个记录必须保留 owner/source/version 或明确 legacy source；不得从当前投影反推不存在的历史事实。

## 6. Erasure Architecture

删除由 durable `DataErasureWorkflowV1` 协调，但不获得 SYS01～SYS08 的业务写入权。流程先生成影响预览和短期确认 token；确认后每个 owner 通过自己的 command 删除、invalidate 或重投影，文件存储适配器清除 raw assets，最后写不含被删内容的最小 tombstone/receipt。

首版固定四种 scope：

- `DOCUMENT`：单份资料、专属来源事实与派生 projection；
- `LEARNING_RECORDS`：对话、尝试、证据、learner state、计划、复习与其用户级执行记录；
- `MODEL_EXECUTION`：可归属当前用户的模型执行/转录/执行 metadata；
- `ALL_PERSONAL_DATA`：前三者加账号/profile/认证状态；账号生命周期 UI 与 token revocation 由 P1-05 调用同一基础能力。

共享 KnowledgeUnit 只有在仍存在其他有效 provenance 时保留；引用被删 evidence 的 projection 必须失效并重建。删除期间受影响 scope fail closed，不再对学习链可见。重复确认/重试不得重复副作用。

为防恢复复活已删除事实，删除完成后必须：

1. 写 `ErasureCheckpointV1`；
2. 使受管理且早于 checkpoint 的不安全恢复点不可激活；
3. 创建并验证 `POST_ERASURE` 新基线；
4. 恢复时先应用当前 checkpoint，再允许 projection rebuild。

产品保证只覆盖 Askora 受管理恢复点。用户自行复制、脱离 catalog 的历史包必须被标记为历史导入；缺少可验证 checkpoint 时不得静默激活为当前数据。

## 7. Failure and Trust Boundaries

- maintenance 与普通写入互斥；运行中的普通请求必须先完成或返回稳定 maintenance error；
- 路径必须 canonicalize，禁止 traversal、symlink escape、重复 ZIP entry 与解压炸弹；
- 密钥、密码与敏感原文不得进入命令行参数、日志或恢复报告；
- 恢复包未知 major、未来 schema、错误 key、损坏 chunk、文件缺失、migration 失败均 fail closed；
- 删除无法完全收敛时 scope 保持不可见，workflow 为 `PARTIAL/FAILED_RETRYABLE`，不得显示“已删除”；
- backup/export/restore/delete 的 Engineering/Ownership 结论不得成为 Learning Evidence。

## 8. Alternatives

### Copy the whole userData directory

拒绝。不能证明 SQLite 与文件一致，无法安全处理 secrets、migration 或删除复活。

### Domain-by-domain rebuild as the only recovery path

拒绝作为 P1 首版。当前存在 41 张表、legacy payload 和无外键引用，完全重建会扩大 owner/migration 风险；可读导出保留为未来 portability 基础。

### One cross-domain delete transaction

拒绝。它会让 data-control service 直接写多个 owner truth，违反 single-writer；采用 durable owner workflow 与 fail-closed visibility。

## 9. Completion Boundary

只有备份、验证、恢复、导出、四类删除、migration snapshot、旧恢复点防复活、设置页体验、SQLite/文件/密钥/投影 reconciliation、失败回滚和真实桌面验收全部通过，P1-03 才能标记 `DONE`。Mock、单元测试或手工复制目录不能单独关闭缺口。
