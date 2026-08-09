# SYS08 Model Configuration and Desktop Credential Contract

> Spec ID：`MODEL-CONFIG-*`
> 状态：Canonical Implementation Contract / FROZEN
> 版本：v1.0
> Governing decision：ADR-0013

## 1. Responsibility and Ownership

### MODEL-CONFIG-001

SYS08 MUST 是 `ModelRouteProfileV1` 的唯一 semantic writer，负责 provider/model/source/revision/verification/activation。Electron desktop vault MAY 作为 SYS08 infrastructure adapter 托管 profile 与 credential ciphertext，但 MUST NOT 产生第二 routing truth。

### MODEL-CONFIG-002

Backend `Settings`、provider instances、health response 与 UI state 均为 active exact revision 的运行/展示投影。它们 MUST NOT 独立修改或推断另一个 active profile。

### MODEL-CONFIG-003

配置、probe 或 restart failure MUST NOT 写入 learner、assessment、policy、plan、activity、review、knowledge 或 accepted transcript truth。

## 2. Public Profile Contract

### MODEL-CONFIG-010

非敏感 profile summary：

```yaml
schema_version: "1.0"
revision: integer|null
state: ACTIVE|DISABLED|EXTERNAL_READ_ONLY|UNCONFIGURED|DEGRADED
provider: qwen|deepseek|doubao|zhipu|null
model: string|null
source: DESKTOP_VAULT|EXTERNAL_ENVIRONMENT|NONE
verified_at: datetime|null
runtime_ready: boolean
runtime_revision: integer|null
reason_codes: [string]
```

summary MUST NOT 包含 Key、Key fragment/fingerprint、ciphertext、base URL、control token、内部路径或 provider raw error。

### MODEL-CONFIG-011

desktop write command 必须显式 `schema_version=1.0`。clear MUST 携带 `expected_revision`；apply 在已有 revision 时也 MUST 携带 expected revision，冲突返回 `MODEL_CONFIG_REVISION_CONFLICT`，不得 last-write-wins。

## 3. Source Precedence

### MODEL-CONFIG-020

packaged/private desktop precedence：

```text
DESKTOP_VAULT ACTIVE → exact vault profile
DESKTOP_VAULT DISABLED → explicit no-model projection
no vault revision → EXTERNAL_ENVIRONMENT compatibility read
```

### MODEL-CONFIG-021

App MUST NOT 自动读取并复制 `.env` Key 到 vault，也 MUST NOT 编辑/删除 `.env`。External source MAY read-only 显示 provider/model/configured fact；切换到 App configuration 必须由用户提交新 Key。

### MODEL-CONFIG-022

vault source 激活时 desktop launcher MUST 清除/覆盖所有 inherited generative provider Key，再只注入 active provider Key、provider/model、source 和 exact revision。DISABLED revision MUST 注入显式空 Key，防止 `.env` 复活。

## 4. Secret Storage

### MODEL-CONFIG-030

macOS desktop credential MUST 使用 Electron asynchronous `safeStorage` OS-backed encryption。`isAsyncEncryptionAvailable=false`、encrypt/decrypt failure 或 unknown schema MUST fail closed；MUST NOT 使用 plaintext fallback。

### MODEL-CONFIG-031

ciphertext wrapper MUST versioned，写入使用 same-directory temporary ciphertext + fsync/close where available + atomic rename，文件/目录权限分别不宽于 `0600/0700`。Crash 不得产生半个 active plaintext/config。

### MODEL-CONFIG-032

decrypt 返回 key rotation/re-encrypt signal 时 MUST 在成功解析 old payload 后写入新 ciphertext；旧 ciphertext 只在 new atomic write 成功后退休。

### MODEL-CONFIG-033

renderer MUST NOT 获得 stored Key、ciphertext 或 decrypted profile payload。表单 Key 只能存在于当前 renderer memory，提交完成/失败/离开页面后清空；不得进入 local/session storage、URL、analytics、普通 export 或 error detail。

## 5. Desktop IPC

### MODEL-CONFIG-040

preload 只允许暴露：

```text
getModelSettings()
applyModelSettings(ModelConfigApplyCommandV1)
clearModelSettings(ModelConfigClearCommandV1)
```

不得暴露 raw `ipcRenderer`、任意 channel、filesystem、process environment 或 decrypt API。

### MODEL-CONFIG-041

main process MUST 验证 sender frame、top-level origin/path、schema major、provider/model allowlist、Key 类型/长度和 expected revision。Invalid input 返回稳定 sanitized error，不得回显 input。

## 6. Connection Probe

### MODEL-CONFIG-050

candidate 在持久化前 MUST 通过真实 provider probe。probe 只能发送 fixed synthetic content，不得包含 user document、conversation、learner state、goal、grader data 或 stored Prompt。

### MODEL-CONFIG-051

probe MUST 使用 candidate provider/model/Key 的 isolated provider instance、fixed prompt version、`temperature=0`、bounded timeout、small output budget、no fallback。成功至少要求 non-empty、non-mock response 且 returned provider/model 与 candidate 一致。

### MODEL-CONFIG-052

desktop control adapter 仅在 `APP_ENV=local + PRIVATE_APP=true + loopback host + non-empty high-entropy control token` 时注册。每次 backend start 使用新 token；comparison constant-time；endpoint 不进入 OpenAPI。

Electron 每个 App process MUST 选择一个未占用的 loopback port（MAY 优先兼容端口），并在该 App process 的 backend restart 间保持稳定。每次 start 的当前 token MUST 同时保护私有 readiness handshake 与 probe；只有该 authenticated private readiness response 才能证明当前 child backend identity。公共 `/ready`、仅有 listener、端口被占用或其他 Askora backend 的成功响应均不得满足本实例 readiness。无法取得或重新绑定已选 port 时 MUST fail closed，不得 attach 到其他实例的数据库、API 或 runtime。

### MODEL-CONFIG-053

probe request/response/log MUST NOT 保存或返回 Key、Authorization header、request body、provider raw response body 或 stack。只允许 provider/model、prompt version、latency、stable result/error code、retryable、tested_at、correlation id。

## 7. Activation and Rollback

### MODEL-CONFIG-060

apply 顺序 MUST 为：validate → probe → encrypt → atomic revision replace → graceful backend restart → readiness + runtime revision verify。probe 未通过时 MUST NOT 写 vault 或重启。

### MODEL-CONFIG-061

vault replace 后 restart/readiness/revision verify 失败 MUST 恢复 prior ciphertext/revision 并重启 prior profile。返回必须区分 `rollback_succeeded=true|false`；rollback 失败为 blocking recovery error。

### MODEL-CONFIG-062

clear MUST 经过 scope confirmation 与 expected revision，创建 `DISABLED` tombstone revision并完成相同 restart/revision verify。不得只删除文件后回落到环境变量。

### MODEL-CONFIG-063

同一 expected revision 的并发 apply/clear 只有一个可提交；后续请求返回 conflict。重复 idempotency key/command fingerprint MUST 返回已提交 summary，不重复 probe/restart。

## 8. Routing and Fallback

### MODEL-CONFIG-070

v1 desktop vault 只激活一个 provider/model。subject/cost route MUST resolve to this exact active route；MUST NOT 静默调用另一个外部 provider 或 unconfigured provider mock。

### MODEL-CONFIG-071

canonical real-model-required flow 在 unconfigured/degraded 时返回 stable dependency error。`local_fallback` 只在 workflow contract 已允许时使用，必须标记 mode/version/reason，且不得满足 real-model gate。

### MODEL-CONFIG-072

所有 provider adapter 在显式或默认 output budget 下 MUST 有相同 bounded semantics；不得因某 provider 忽略 omitted `max_tokens` 而形成无声明费用边界。

## 9. Error Contract

### MODEL-CONFIG-080

至少支持：

| Code | Category | Retryable | Required action |
|---|---|---:|---|
| `MODEL_CONFIG_STORAGE_UNAVAILABLE` | security/dependency | false | 恢复 Keychain 或重新配置环境 |
| `MODEL_CONFIG_SCHEMA_UNSUPPORTED` | validation | false | 升级 App 或显式清除重建 |
| `MODEL_CONFIG_REVISION_CONFLICT` | conflict | false | 刷新后重试 |
| `MODEL_CREDENTIAL_REJECTED` | authorization/dependency | false | 更新 Key |
| `MODEL_NOT_AVAILABLE` | dependency | false | 选择受支持模型/开通权限 |
| `MODEL_RATE_LIMITED` | transient | true | 按 retry-after 等待 |
| `MODEL_PROVIDER_TIMEOUT` | transient | true | 重试或稍后再试 |
| `MODEL_PROVIDER_UNAVAILABLE` | dependency/transient | true | 稍后重试 |
| `MODEL_CONFIG_APPLY_FAILED` | internal | true | 已恢复旧配置时重试 |
| `MODEL_CONFIG_ROLLBACK_FAILED` | internal | false | 进入本地恢复流程 |

## 10. Data and Cost Disclosure

### MODEL-CONFIG-090

Settings MUST 在 probe 动作前说明该动作只发送固定合成文本、可能产生极小 provider 费用。不得展示未经实时来源支持的价格、余额或月度预算承诺。

### MODEL-CONFIG-091

Settings MUST 区分当前产品路径：canonical Book Learning 的最小本轮 input/evidence 与 compatibility quick history window。不得使用“绝不发送历史/全部数据都本地”等不符合实际的绝对文案。

## 11. Observability

### MODEL-CONFIG-100

至少记录 sanitized：command id/fingerprint、prior/new revision、provider/model、probe status/latency/error code、restart/ready/rollback result、correlation id。MUST NOT 记录 Key/ciphertext/control token/request body/raw provider error。

## 12. Tests

必须覆盖：schema/enum/revision、safeStorage unavailable/encrypt/decrypt/rotation、atomic write/crash artifact、IPC sender/invalid input、probe auth、401/403/404/429/timeout/5xx/empty/mock、output budget、apply no-write-on-probe-fail、restart rollback、rollback failure、disabled tombstone、external precedence、secret leakage、frontend no persistence、responsive/keyboard/live status，以及一个真实 macOS App/provider E2E。

## 13. Acceptance Criteria

- `MODEL-CONFIG-AC-001`：首次用户仅在 App 内完成 provider/model/Key 配置和真实验证。
- `MODEL-CONFIG-AC-002`：Key 不进入 renderer persistence/API response/log/Prompt/export。
- `MODEL-CONFIG-AC-003`：probe 失败无配置写入，apply 失败恢复 exact prior revision。
- `MODEL-CONFIG-AC-004`：clear 后重启仍是 DISABLED，不被 `.env` 复活。
- `MODEL-CONFIG-AC-005`：runtime provider/model/revision 与 vault active summary 一致。
- `MODEL-CONFIG-AC-006`：provider errors 稳定分类并产生正确恢复动作。
- `MODEL-CONFIG-AC-007`：无 silent external failover/mock-as-ready/learner failure evidence。
- `MODEL-CONFIG-AC-008`：退出并重开 App 后 exact verified config 可恢复。
- `MODEL-CONFIG-AC-009`：真实 provider E2E、自动化、安全和 UI 门禁有当前证据。

## 14. Forbidden Implementations

禁止：UI 编辑 `.env`；Key/Key fragment 回显；plaintext fallback；数据库成为 desktop credential truth；renderer decrypt；任意 IPC；probe 携带用户资料；probe 失败仍保存；restart 失败不 rollback；clear 后回落旧环境 Key；silent cross-provider failover；mock 显示为已连接；provider failure 记 learner error；模型连通性宣称学习有效。
