# ADR-0013 — Desktop Model Credential and Atomic Activation

Status: **partially superseded for v1 deployment mechanics**  
Date: 2026-08-09  
Supersession date: 2026-08-10  
Decision authority: user-delegated Codex  
Authorized objective: 真正关闭 P1-02 模型设置体验并通过相关测试  
Current upper authority: `docs/product/PRODUCT-POSITIONING.md`  
Current implementation contract: `docs/specs/systems/08-model-configuration.md`

## Current v1 Supersession

本 ADR 是 2026-08-09 基于当时“私人 macOS Electron App”假设形成的历史决策记录。最新 `PRODUCT-POSITIONING.md` 已冻结 Askora v1 正式产品形态为：

```text
Browser
→ loopback Local Server
→ local SQLite/files/jobs
→ External AI Provider (BYOK)
```

并明确 macOS / Windows 原生客户端、Electron/Desktop shell 不属于 v1 产品范围。

因此以下 **Desktop-specific mechanics 已被上位产品定位 supersede，不再是当前实现要求**：

- Electron main-process encrypted vault 作为必需 credential source；
- Electron `safeStorage` 作为唯一/必需 secret adapter；
- main/preload narrow IPC 作为 v1 Settings 写入口；
- `DESKTOP_VAULT` source precedence；
- Electron child-backend port/control-token handshake；
- Desktop launcher 注入环境变量；
- macOS App E2E 作为模型设置唯一 release path。

以下**架构原则继续有效并已迁移到当前 Local Web contract**：

1. SYS08 是 `ModelRouteProfileV1` 的唯一 routing semantic owner；
2. routing metadata 与 API Key/secret material 分离；
3. Secret 必须安全地只保存在本机，不允许 plaintext fallback；
4. Browser/UI/普通 API 不得获得已保存 Key；
5. candidate 配置在激活前需要真实、无私人资料的 provider probe；
6. 配置使用 version/revision + optimistic concurrency；
7. activation failure 必须 rollback/fail closed，不能产生 runtime/profile split-brain；
8. clear 后旧 `.env` / cache / inherited process state 不得静默复活配置；
9. 关键任务不得不可追踪地 silent failover；
10. secret 不进入日志、默认 backup/export/diagnostic、Prompt metadata 或学习 truth。

后续实现只能服从 `PRODUCT-POSITIONING.md` 与最新 `MODEL-CONFIG-*`，不得再根据本 ADR 的 Desktop mechanics 新增 Electron-specific v1 依赖。

## Historical Context

当时 Askora 被假定为私人 macOS Electron App。模型 Key 只来自后端环境配置，Settings 只展示任意 Key 是否非空，`ModelRouter` 又在启动时缓存 provider/model/Key。用户无法在 App 内安全配置、验证、恢复或清除模型，错误的 Key 也可能被显示成“已配置”。

该目标涉及跨会话 control state、secret persistence、IPC/API schema、provider error、backend restart 和 fallback semantics，因此当时形成了本 ADR。

## Historical Decision

1. SYS08 唯一拥有版本化 `ModelRouteProfileV1` 的 provider/model/source/activation 语义。
2. packaged/private desktop 使用 Electron main-process encrypted vault 作为 profile/credential source；backend runtime 只是 exact revision projection。
3. Key 使用 Electron asynchronous `safeStorage` 加密；macOS encryption key 由 Keychain 管理。不可用时 fail closed，不允许 plaintext fallback。
4. renderer 只通过 narrow、sender-validated、versioned preload IPC 提交临时 Key；不得读取旧 Key、ciphertext 或内部路径。
5. candidate 配置必须先通过不含私人资料的真实 provider probe。probe 通过后才加密落盘并重启后端；启动或 revision health 失败必须恢复 prior encrypted revision。
6. clear 写入 versioned `DISABLED` tombstone，确保 inherited/.env Key 不会在 desktop restart 后意外复活。
7. 首版只允许一个 active external provider/model，不自动跨 provider failover。local fallback 仅在 workflow 明确允许时使用并显式标记。
8. source/Docker environment configuration 保留为没有 desktop vault 时的 read-only compatibility source；App 不编辑或删除 `.env`。

这些 mechanics 仅保留为历史实现依据；其中与 Desktop/Electron 绑定的部分不得继续约束 v1。

## Alternatives Considered at the Time

### App 内直接编辑 `.env`

拒绝。它会把 Key 明文持久化，缺少原子启用、版本冲突、回滚和安全存储，而且修改后仍需重启才能刷新 router。

该拒绝理由在 Local Web v1 仍成立：Settings 不应编辑 `.env`。

### 使用现有 KEK 加密后写数据库

拒绝作为当时 desktop canonical source。当前 v1 仍保留原则：普通 SQLite routing/profile payload 不应持有明文 API Key；具体 SecretStore adapter 由最新 Spec 决定。

### 引入 keytar 或云端 secret service

当时拒绝。当前 v1 仍禁止 Askora 官方云 secret service 成为 BYOK 必经路径。具体本地 OS-backed secure storage adapter MAY 按平台实现演进，不再被 Electron 限定。

### Electron main 直接实现各 provider HTTP probe

拒绝。该原则继续有效：provider protocol/probe 只应在统一 backend/SYS08 provider adapter 中实现，Browser/launcher 不建立第二 model gateway。

## Retained Ownership and Invariants

- SYS08：`ModelRouteProfileV1` semantic owner；provider probe/runtime execution owner。
- Local SecretStore：只托管 secret，不取得 provider/model routing semantic ownership。
- Browser/API health：read projection/transport，不是 writer。
- secret 不进入 Prompt metadata、日志、普通 API response、browser persistence、普通导出、默认 backup 或 diagnostic package。
- configuration error 不得产生 learner failure、AssessmentResult、MasteryEstimate、activity completion 或 accepted transcript truth。
- probe 不发送私人资料；真实学习请求继续遵守 workflow/data-minimization contract。

## Current Migration Direction

```text
Historical Desktop model configuration
→ preserve existing verified routing metadata where safely migratable
→ migrate credential material to Local SecretStore contract
→ Browser Settings + loopback API
→ SYS08 ModelRouteProfile exact revision
→ retire Electron IPC / desktop vault / launcher dependencies
```

Migration MUST NOT：

- expose/decrypt Key into Browser；
- copy `.env` silently into production user config；
- create two active routing truths；
- lose explicit DISABLED/UNCONFIGURED intent；
- require Desktop shell to start Local Web runtime。

## Security and Privacy Consequences

当前 v1 安全边界由 loopback Local Web + LocalOwnerContext + SecretStore 构成，而不是 Electron IPC。API Key 在用户输入、本地 loopback request、provider adapter memory 中短暂存在是完成调用所需的最小明文面；持久化必须通过安全本地 SecretStore，失败时不得 plaintext fallback。

## Current Validation

后续模型设置验证应覆盖：

- Local Web Settings → loopback API；
- no Electron/Desktop production dependency；
- SecretStore unavailable fail closed；
- Browser/localStorage/API/log/backup/export/diagnostic secret leakage scan；
- real provider probe；
- revision conflict；
- activation/rollback；
- clear + restart no resurrection；
- no silent failover；
- actual provider/model route trace；
- BYOK real-provider E2E when release requires it。

历史 Electron-specific unit/E2E 可作为 legacy regression 保留，但不再是 v1 release requirement。

## Supersedes / Superseded By

本 ADR 当时 additive 扩展 ADR-0005 的 configured-provider 来源与激活语义。

从 2026-08-10 起：

- **Desktop/Electron mechanics**：由 `PRODUCT-POSITIONING.md` 与最新 `docs/specs/systems/08-model-configuration.md` supersede；
- **routing ownership / secret separation / probe / revision / rollback / no silent failover / no leakage 原则**：继续有效。

本 ADR 保留作为历史决策记录，不得用来反向覆盖当前 Product Positioning。
