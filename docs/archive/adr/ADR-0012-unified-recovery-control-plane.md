# ADR-0012 — Unified Recovery Control Plane and Bootstrap Diagnostics

> Status: accepted
> Date: 2026-08-09
> Decision authority: user-delegated Codex
> Authorized objective: 真正关闭 P1-07 错误恢复中心

## Context

Askora 已有 durable outbox、bounded retry、document quarantine reinspection 与模型 fail-closed，
但错误仍分散在页面自由文本、worker 日志与 Electron 启动输出中。当前用户无法稳定回答：
发生了什么、数据是否安全、应采取什么动作，以及重试是否会重复副作用。后端错误 envelope
也没有完整实现既有 `ERROR-002` 的 `category/retryable/correlation_id`。

恢复涉及 SYS01 文档、SYS08 模型/任务执行、数据库和桌面 bootstrap。若建立一个可任意改写
这些状态的 Recovery Service，会形成第九个 truth owner 并绕过八类系统边界；若只做前端文案
映射，则无法审计、幂等或在重启后恢复。

## Decision

采用“双入口、单合同、Owner Command”方案：

1. 运行期入口为 `/settings/recovery`，并在 AppShell 提供仅在存在 active issue 时显示的全局
   指示器；它查询 current-user scoped `RecoveryIssueViewV1`。
2. 后端不可达时由 Electron bootstrap recovery shell 显示 `BootstrapDiagnosticV1`，允许重试
   启动和复制脱敏诊断；它不得依赖业务 API。
3. `RecoveryIssueViewV1` 是 SYS08 托管的操作投影或 owner state 的只读组合，不拥有文档、
   Goal、LearningActivity、LearnerState、Assessment、ReviewSchedule 或 outbox 原任务状态。
4. 恢复动作使用 `RecoveryActionV1` 闭集。服务端 command router 只把动作分派给原 owner：
   SYS01 处理/复检资料，SYS08 重建允许重放的执行任务；数据库恢复由 P1-03 已验证能力承担；
   provider 配置由 P1-02 owner command 承担。UI 不直接 patch ORM/outbox。
5. manual retry 不复活或覆盖 dead-letter 历史；它追加 `RecoveryActionAuditRecord`，并在 handler
   明确声明可幂等重放时创建新 task/run，带 `recovery_of`、新 idempotency key 与固定预算。
6. provider、文档、数据库、outbox 与 bootstrap 使用稳定错误目录。所有 HTTP 错误返回完整
   `ERROR-002` envelope，并可选携带服务端允许的 recovery actions。
7. provider/工具/存储/数据库失败只产生 operational incident/event，不产生 learner error、
   0 分、mastery decrease、review failure 或 activity completion。

## Issue truth and lifecycle

`RecoveryIssueViewV1` 的 current state 来自两类来源：

- owner projection：document/outbox/OCR/backup 等已有 owner state，query 时组合；
- SYS08 operational incident stream：provider/output/workflow 等没有持久业务 owner row 的执行失败。

操作事件采用 append-only `opened/action_requested/action_succeeded/action_failed/resolved`；current
issue 是 deterministic latest-event projection。它只保存稳定 code、分类、资源引用、重试预算、
安全摘要、correlation 与时间，不保存密钥、Prompt、完整文件路径、原始 provider body 或 learner
答案。owner state 与 operational projection 冲突时 owner state 优先并标记 projection stale。

## Recovery action safety

- `retry_owner_command`：必须有 handler allowlist、current-user scope、expected version（适用时）、
  idempotency key、最大次数和 next eligible time；
- `reinspect_document`：只允许已隔离资料且部署了更新策略，成功前持续隔离；
- `open_model_settings`、`open_data_recovery`、`open_activity`：仅导航到已存在的 owner 页面，
  不声称已恢复；`reselect_file` 只有在 SYS01 提供 versioned owner command 时才能启用，
  不得用无语义的 query string 冒充替换动作；
- `wait_until`：无副作用，必须返回服务端时间；
- `copy_diagnostics`：只含脱敏字段；
- `acknowledge`：只改变提示可见性，不解决 owner failure；
- 未知 task type、未知 schema、无法确认 owner scope 或 non-idempotent side effect 只允许诊断，
  不允许 replay。

## Bootstrap diagnostics

Electron 维护进程内 `BootstrapDiagnosticV1`，稳定 code 至少区分：

- `BOOTSTRAP_BACKEND_BINARY_MISSING`；
- `BOOTSTRAP_BACKEND_SPAWN_FAILED`；
- `BOOTSTRAP_BACKEND_EXITED`；
- `BOOTSTRAP_BACKEND_START_TIMEOUT`；
- `BOOTSTRAP_DATABASE_MIGRATION_REQUIRED`；
- `BOOTSTRAP_DATABASE_UNAVAILABLE`。

Python backend 通过单行、固定前缀、strict JSON 的受限 startup diagnostic channel 发布分类结果；
Electron 不根据任意自由文本决定恢复动作。未知异常归为 `BOOTSTRAP_BACKEND_EXITED`。诊断不得含
绝对路径、SQL、环境变量值或 traceback。retry 必须先确认旧进程停止，并保证同一时间只有一个
启动 promise。

## Alternatives

### 只增强页面级 toast

拒绝。不能覆盖启动失败、重启恢复、DLQ 与跨页面动作，也无法证明副作用幂等。

### 建立中央 RecoveryCase 表并直接修改所有 owner 状态

拒绝。形成第二 truth 和跨 owner writer，破坏 state ownership。

### 原地把 dead-letter task 改回 pending

拒绝。覆盖耗尽历史、无法表达 recovery generation，并可能重放未知副作用。

### 所有错误统一自动重试

拒绝。Key 无效、安全隔离、schema mismatch 与 version conflict 不可盲重试，并会放大费用和重复
副作用。

## Invariants

- recovery query/control plane 不是第九个领域 owner；
- owner state 只能由 owner command 改变；
- retryable 不等于立即可重试，必须同时满足 budget 和 `next_eligible_at`；
- duplicate recovery command 返回原结果，不创建第二 task/run/transition；
- resolved 只表示该 operational issue 不再 active，不表示学习成功或数据完整性已自动证明；
- bootstrap 无后端依赖，运行期 recovery 不暴露本地绝对路径或 secret；
- `system/provider/storage failure != learner failure`。

## Migration and rollback

新增 append-only recovery action/incident 表，不回填 learner evidence。文档与 outbox issue 由现有
owner rows 即时投影；历史 provider failure 无可靠安全字段时不猜测 backfill。旧客户端继续读取
原 error fields，新字段为 additive。回滚可停止新 endpoint/UI 并保留审计表；不删除 owner state，
优先 forward-fix。

## Validation

- strict contracts、unknown major/field rejection 与 stable error catalog；
- current-user scope、unknown task no replay、duplicate/concurrent retry、budget exhausted、restart；
- provider timeout/rate/key/model/output 分类与无 learner evidence；
- failed/quarantined/missing-file/OCR-low-confidence owner actions；
- migration/database/startup failure在后端不可用时仍可见并可重试；
- 360px、200% zoom、keyboard、screen-reader live region；
- deterministic browser E2E 和真实配置 provider 的受控恢复；
- Engineering、Policy/Ownership、Security/Privacy 与 Learning Evidence 分开报告。
