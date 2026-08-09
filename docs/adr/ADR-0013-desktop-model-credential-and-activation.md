# ADR-0013 — Desktop Model Credential and Atomic Activation

Status: accepted
Date: 2026-08-09
Decision authority: user-delegated Codex
Authorized objective: 真正关闭 P1-02 模型设置体验并通过相关测试
Affected specs: `STATE-*`、`SYS08-*`、`MODEL-CONFIG-*`、`API-*`、`ERROR-*`、`SCHEMA-*`、`SEC-*`、`OBS-*`、`TEST-*`、`DOD-*`、`UI-SCREEN-*`、`UI-DATA-*`、P1-02 Vertical Slice

## Context

Askora 是私人 macOS Electron App。当前模型 Key 只来自后端环境配置，Settings 只展示任意 Key 是否非空，`ModelRouter` 又在启动时缓存 provider/model/Key。用户无法在 App 内安全配置、验证、恢复或清除模型，错误的 Key 也可能被显示成“已配置”。

该目标涉及跨会话 control state、secret persistence、IPC/API schema、provider error、backend restart 和 fallback semantics，属于必须先治理的 SPEC GAP。

## Decision

1. SYS08 唯一拥有版本化 `ModelRouteProfileV1` 的 provider/model/source/activation 语义。
2. packaged/private desktop 使用 Electron main-process encrypted vault 作为 profile/credential source；backend runtime 只是 exact revision projection。
3. Key 使用 Electron asynchronous `safeStorage` 加密；macOS encryption key 由 Keychain 管理。不可用时 fail closed，不允许 plaintext fallback。
4. renderer 只通过 narrow、sender-validated、versioned preload IPC 提交临时 Key；不得读取旧 Key、ciphertext 或内部路径。
5. candidate 配置必须先通过不含私人资料的真实 provider probe。probe 通过后才加密落盘并重启后端；启动或 revision health 失败必须恢复 prior encrypted revision。
6. clear 写入 versioned `DISABLED` tombstone，确保 inherited/.env Key 不会在 desktop restart 后意外复活。
7. 首版只允许一个 active external provider/model，不自动跨 provider failover。local fallback 仅在 workflow 明确允许时使用并显式标记。
8. source/Docker environment configuration 保留为没有 desktop vault 时的 read-only compatibility source；App 不编辑或删除 `.env`。

## Alternatives Considered

### App 内直接编辑 `.env`

拒绝。它会把 Key 明文持久化，缺少原子启用、版本冲突、回滚和 Keychain 保护，而且修改后仍需重启才能刷新 router。

### 使用现有 KEK 加密后写数据库

拒绝作为 desktop canonical source。当前 KEK 自身来自本地 secret file；用它保护用户输入的 provider Key 会形成 root-key portability/backup coupling，也让 backend database 取得不必要的 credential persistence 职责。

### 引入 keytar 或云端 secret service

拒绝。keytar 增加 native production dependency，而 Electron 已提供 OS-backed `safeStorage`；云端 secret service 引入外部服务、付费、网络和新隐私边界，不符合私人单机目标。

### Electron main 直接实现各 provider HTTP probe

拒绝。它会复制 backend provider protocol、错误映射和模型 adapter，形成第二 model gateway。

## Ownership and Invariants

- SYS08：`ModelRouteProfileV1` semantic owner；provider probe/runtime execution owner。
- Electron vault：SYS08 desktop infrastructure adapter，托管 credential ciphertext/profile revision。
- React/API health：read projection/transport，不是 writer。
- secret 不进入 Prompt、日志、普通 API response、frontend persistence、普通导出或 crash report。
- configuration error 不得产生 learner failure、AssessmentResult、MasteryEstimate、activity completion 或 accepted transcript。
- probe 不发送私人资料；真实学习请求继续遵守各 workflow 的既有 data-minimization contract。

## Migration / Rollback

- 没有 desktop vault 时继续读取环境变量，不自动迁移或删除 `.env`。
- 第一份 App 配置创建 revision 1；成功后 desktop vault 优先。
- clear 追加 `DISABLED` revision，而不是退回环境变量。
- apply failure 恢复 prior ciphertext/revision 并验证 prior backend ready。
- vault schema unknown/corrupt 时不猜测、不回传 ciphertext，显示恢复错误；用户可显式清除并重新配置。
- 不新增数据库 migration；encrypted profile 位于 Electron `userData`，属于桌面 infrastructure artifact。

## Security and Privacy Consequences

- Key 在用户输入、IPC、local control probe 和 backend process memory 中短暂存在，这是完成调用所需的最小明文面。
- control adapter 仅 local/private 注册，并由每次启动的高熵 token 鉴权；token 与 Key 不记录。
- safeStorage 不可用时用户不能保存新 Key，但 App 其他本地能力可继续运行。
- connection probe 会产生一次真实外部请求，UI 必须在动作前说明可能产生极小费用。

## Validation

- contract：profile/IPC schema、unknown major、revision conflict、error taxonomy；
- unit：safeStorage availability、encrypt/decrypt/re-encrypt、atomic write、disabled tombstone；
- integration：probe auth、401/403/429/timeout/5xx/model invalid mapping、no secret echo；
- recovery：apply restart failure rollback、prior config recovery、corrupt vault、clear restart；
- security：IPC sender、renderer/localStorage/API/log/export leakage scan；
- real E2E：macOS App 内配置真实 provider、启用、完成真实 inference、退出重开后仍可用；
- UI：360/768/1024/1440、keyboard、status/error live announcement、clear confirmation。

## Supersedes / Superseded By

本 ADR additive 扩展 ADR-0005 的 configured-provider 来源与激活语义，不改变 TeachingAction、EvidenceBundle、model rendering、transcript 或 Learning Evidence 边界。
