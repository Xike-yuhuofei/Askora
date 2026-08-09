# P1-02 安全模型设置体验设计

> 状态：Canonical Design / Accepted for P1-02
> 日期：2026-08-09
> 授权：用户明确采纳推荐方案，并要求最终真正关闭 P1-02、通过相关测试
> 关联决策：ADR-0013

## 1. 目标

让第一次使用 Askora 的私人 macOS 用户不离开 App 即可：

```text
选择 provider / model
→ 安全输入 API Key
→ 用不含私人资料的固定请求验证连接
→ 验证成功后原子启用
→ 后端重启后继续使用 exact configuration revision
→ 失败时保留并恢复上一份可用配置
```

完成后，用户能够理解模型是否真实可用、失败原因、是否可重试、可能产生的费用、哪些数据会发送给外部 provider，以及本地 fallback 与真实模型的区别。

## 2. 当前问题

当前 `/settings` 只读取 `/health/config` 的 `llm_ready` 布尔值。该值只证明某个环境变量非空，不证明：

- 当前默认 provider 对应 Key 已配置；
- Key 有效；
- model 存在或账号有权访问；
- 连接未超时或被限流；
- 当前路由器已经加载新配置；
- canonical learning 实际会得到 real-model response。

`ModelRouter` 在进程启动时读取配置并缓存 provider。只在 UI 写 `.env` 无法形成即时、可恢复、可审计的产品闭环。

## 3. 产品边界

### 3.1 本轮包含

- macOS Electron 桌面 App 内的 generative chat provider 配置；
- provider/model 选择；
- Key 新增、更新、清除；
- 无私人资料的真实连接测试；
- 验证成功后启用、重启 readiness 与失败 rollback；
- 稳定错误码和恢复动作；
- 数据发送、fallback、超时、限流与费用边界说明；
- source/Docker 环境变量兼容，只读显示其来源；
- 真实 macOS App + 真实 provider E2E。

### 3.2 本轮不包含

- provider 账户注册、充值、余额或账单读取；
- 价格抓取或费用预测；
- 任意 OpenAI-compatible base URL；
- 未实现的 provider/model；
- embedding provider 凭据管理；
- 自动跨 provider failover；
- 云端 secret service、多设备同步或公网多租户 secret 管理；
- 把模型连通性当作真人学习效果。

## 4. 核心模型

### 4.1 ModelRouteProfileV1

`ModelRouteProfileV1` 是 SYS08-owned、版本化、跨会话影响后续 execution 的 control artifact：

```yaml
schema_version: "1.0"
revision: integer
state: ACTIVE|DISABLED
provider: qwen|deepseek|doubao|zhipu|null
model: string|null
source: DESKTOP_VAULT|EXTERNAL_ENVIRONMENT
verified_at: datetime|null
verification_provider: string|null
verification_model: string|null
```

它不包含明文 Key。凭据由桌面 secret adapter 保存为 OS-protected ciphertext；后端只在当前进程内接收完成 provider 调用所需的明文。

### 4.2 唯一事实与投影

- packaged/private desktop 的配置 truth：Electron `userData` 下的 encrypted profile revision；
- credential encryption key：macOS Keychain，由 Electron `safeStorage` 管理；
- backend `settings`/`ModelRouter`：当前 active revision 的运行投影，不是第二 truth；
- `/health/config`：非敏感 readiness 投影，不是凭据或配置 writer；
- React form/local state：临时输入，不是持久化 truth。

### 4.3 配置来源优先级

```text
valid DESKTOP_VAULT ACTIVE revision
→ exact desktop runtime projection

DESKTOP_VAULT DISABLED revision
→ explicitly unconfigured; must override inherited/.env LLM keys

no DESKTOP_VAULT revision
→ EXTERNAL_ENVIRONMENT compatibility read
```

App 不自动编辑、删除或导入 `.env`。用户从环境变量切换到 App 配置后，desktop vault 成为 packaged desktop 的唯一 active source。

## 5. 安全存储与 IPC

Electron main process 使用异步 `safeStorage`：

- `isAsyncEncryptionAvailable=false` 时 fail closed；
- ciphertext 使用原子临时文件 + rename 写入，权限 `0600`；
- decrypt 返回 `shouldReEncrypt=true` 时在成功解密后重新加密；
- 不使用 plaintext fallback；
- 不向 renderer 返回明文、Key 尾号、ciphertext 或内部路径。

preload 只暴露三个窄接口：

```text
getModelSettings()
applyModelSettings({schema_version, provider, model, api_key})
clearModelSettings({schema_version, expected_revision})
```

main process 必须验证 sender、schema、provider/model、输入长度和 expected revision。不得暴露通用 `ipcRenderer.invoke`。

## 6. 验证与原子启用

### 6.1 连接探测

Electron main 通过仅本地启用的 desktop control adapter 调用当前后端。该 adapter：

- 只监听当前 `127.0.0.1` 后端；
- 要求每次后端启动生成的高熵 control token；
- 不进入 OpenAPI；
- 使用 candidate provider/model/Key 构造一次独立 provider instance；
- 发送固定合成 Prompt，不包含用户文档、聊天、学习状态或 grader data；
- `temperature=0`、极小 output budget、bounded timeout、无自动 fallback；
- 不记录 request body、Key、Authorization header 或 provider raw error body。

### 6.2 Apply transaction

```text
validate candidate
→ probe current backend
→ probe failed: no write/no restart/old config unchanged
→ probe passed: encrypt candidate
→ atomic replace encrypted revision
→ graceful backend restart
→ /ready + active revision health check
→ success: return VERIFIED_ACTIVE
→ failure: restore prior ciphertext/tombstone
→ restart prior configuration
→ report rollback result
```

清除配置写入 `DISABLED` tombstone revision，而不是简单删除文件；否则旧 `.env` 可能在重启后重新激活。

## 7. 路由与 fallback

首版 desktop vault 只有一个 active provider/model。数学或成本路由不得静默改用另一外部 provider。若 execution 无法使用 active provider：

- canonical real-model-required flow 返回稳定依赖错误；
- 只有上游 workflow 明确允许时，才可使用版本化 `local_fallback`；
- local fallback 必须明确标记，不能满足 real-model gate；
- provider failure 不得记录为 learner failure、错误答案或负向 evidence。

## 8. 用户体验

Settings 使用以下状态：

```text
LOADING
UNCONFIGURED
EXTERNAL_READ_ONLY
READY
VALIDATING
APPLYING
ROLLING_BACK
DEGRADED
ERROR
```

主要交互：

- 当前模型：provider、model、来源、最近验证时间；
- 配置表单：provider/model 组合、空白密码输入；
- `验证并使用`：一次完成真实 probe 与启用；
- `重新验证`：对当前配置发起无私人资料 probe；
- `更新密钥`：不回显旧值；
- `清除配置`：inline scope confirmation + expected revision；
- 失败卡片：发生了什么、数据是否安全、可否重试、旧配置是否已保留。

## 9. 数据与费用说明

设置页必须明确：

- 连接测试只发送固定合成文本，但仍可能产生极小 provider 费用；
- canonical Book Learning 当前发送本轮输入、目标摘要和一个 learner-visible evidence item；
- compatibility quick learning 当前可能发送最近最多 20 条 learner/assistant history；
- Key、grader-only evidence、内部 Prompt 和无关完整 learner history 不得发送；
- 费用由 provider 账户结算；Askora 不读取余额、不保证价格、不实施月度预算；
- token/latency 只属于 execution audit/process metrics。

## 10. 错误与恢复

必须区分：

```text
MODEL_CONFIG_STORAGE_UNAVAILABLE
MODEL_CONFIG_SCHEMA_UNSUPPORTED
MODEL_CONFIG_REVISION_CONFLICT
MODEL_CREDENTIAL_REJECTED
MODEL_NOT_AVAILABLE
MODEL_RATE_LIMITED
MODEL_PROVIDER_TIMEOUT
MODEL_PROVIDER_UNAVAILABLE
MODEL_CONFIG_APPLY_FAILED
MODEL_CONFIG_ROLLBACK_FAILED
```

401/403 不可自动重试；429/timeout/5xx 可在 bounded 条件下由用户重试。任何错误详情不得包含 secret/provider raw body/stack/path。

## 11. 交付拆分

### P1-02A / EXEC-040

冻结并实现 SYS08 control contract、desktop encrypted vault、narrow IPC、probe、runtime projection、restart/rollback 和 security/recovery tests。

### P1-02B / EXEC-041

实现 Settings 状态机、数据/费用边界、错误恢复、responsive/accessibility、真实 macOS App/provider E2E、release report 与 gap closure。

## 12. 完成声明边界

P1-02 DONE 只证明模型设置 Engineering、Security/Ownership、真实连接和产品恢复闭环完成。它不证明 provider 永久在线、模型回答质量、人类学习效果或费用节省。Learning Evidence 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
