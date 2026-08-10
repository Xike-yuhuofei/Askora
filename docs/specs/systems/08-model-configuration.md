# SYS08 Model Configuration and Local Secret Boundary Contract

> Spec ID：`MODEL-CONFIG-*`  
> 状态：Canonical Implementation Contract / FROZEN  
> 版本：v1 Local Web / BYOK Alignment  
> Historical governing decision：ADR-0013（desktop-specific mechanics superseded）  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. Responsibility and Ownership

### MODEL-CONFIG-001

SYS08 MUST 是 `ModelRouteProfileV1` 的唯一 semantic writer，负责 provider/model/task route/revision/verification/activation。

Local SecretStore MAY 作为 infrastructure adapter 托管 API Key，但 MUST NOT 产生第二 routing truth。

### MODEL-CONFIG-002

Browser Settings、provider instances、health/readiness response 与 UI state 都只是 active exact revision 的运行/展示投影。它们 MUST NOT 独立修改或推断另一个 active profile。

### MODEL-CONFIG-003

配置、probe、activation 或 provider failure MUST NOT 写入 learner、assessment、policy、plan、activity、review、knowledge 或 accepted transcript truth。

### MODEL-CONFIG-004 — Local Web Boundary

v1 model settings interaction：

```text
Browser Settings
→ loopback API
→ Model Configuration Application Service
├── validate / probe
├── SYS08 ModelRouteProfile
└── Local SecretStore
        ↓
    External AI Provider
```

MUST NOT 依赖 Electron main/preload IPC、desktop vault 或 native desktop shell 才能完成 v1 model configuration。

## 2. Public Profile Contract

### MODEL-CONFIG-010

非敏感 profile summary SHOULD 至少表达：

```yaml
schema_version: "1.0"
revision: integer|null
state: ACTIVE|DISABLED|UNCONFIGURED|DEGRADED
provider: string|null
model: string|null
embedding_provider: string|null
embedding_model: string|null
task_routes: object
source: LOCAL_USER_CONFIG|DEVELOPMENT_ENVIRONMENT|NONE
verified_at: datetime|null
runtime_ready: boolean
runtime_revision: integer|null
reason_codes: [string]
```

summary MUST NOT 包含：

- API Key；
- Key fragment/fingerprint；
- ciphertext；
- OS credential identifier that can expose secret material；
- Authorization header；
- internal absolute path；
- provider raw error/body。

### MODEL-CONFIG-011

apply/clear command MUST 显式 schema version、expected revision 与 idempotency key。已有 revision 时若 expected revision 不匹配，返回 `MODEL_CONFIG_REVISION_CONFLICT`，不得 last-write-wins。

### MODEL-CONFIG-012 — Task Routes

v1 MAY 为不同任务配置不同 provider/model，例如：

```text
KnowledgeExtraction
TeachingDialogue
Assessment
Embedding
```

route 选择 MUST 来自用户配置或确定性 versioned routing policy；不得由 LLM 自由决定或静默跨 provider 切换。

## 3. Configuration Source Precedence

### MODEL-CONFIG-020 — Production Local

Production Local canonical precedence：

```text
explicit LOCAL_USER_CONFIG ACTIVE
→ exact configured route

explicit DISABLED / UNCONFIGURED
→ no configured external route
```

Development/testing environment variables MAY 作为非生产 compatibility source，但 MUST NOT：

- 成为 v1 用户必须配置方式；
- 在 production clear 后静默复活 provider；
- 覆盖用户明确保存的 revision；
- 被自动复制进 SecretStore。

### MODEL-CONFIG-021

Askora MUST NOT 编辑或删除用户开发环境 `.env`；也 MUST NOT 把 `.env` secret 自动迁移为正式用户配置。

## 4. Secret Storage

### MODEL-CONFIG-030 — Local SecretStore

API Key 仅保存在本机，并通过 `LocalSecretStore` port 隔离具体存储机制。

Production target SHOULD 优先使用 OS-backed secure credential storage。无论具体 adapter 为何：

- MUST NOT plaintext persist；
- MUST NOT 存入 Workspace/Project普通文件；
- MUST NOT 存入 browser localStorage/sessionStorage/IndexedDB；
- MUST NOT 进入普通 SQLite profile payload；
- MUST NOT 进入默认 Backup / Export / Diagnostics / Logs。

若安全持久化不可用，系统 MUST fail closed for persistence；不得自动降级明文保存。实现 MAY 允许用户重新输入临时 session credential，但不得把该行为伪装为“已安全保存”。

### MODEL-CONFIG-031 — Secret/Profile Separation

`ModelRouteProfileV1` 只保存非敏感 routing metadata 与 exact secret reference/status；SecretStore 保存 secret material。二者必须通过 revision/idempotency application transaction 协调，但 SecretStore 不拥有 provider/model语义。

### MODEL-CONFIG-032 — Browser Exposure

Browser MAY 在用户输入时短暂持有候选 API Key，并通过 loopback HTTPS-equivalent local trust boundary/HTTP loopback request 提交给 Local Server；提交完成、失败或离开表单后 SHOULD 清除内存中的敏感值。

Browser MUST NOT 提供“显示已保存 Key”能力。

### MODEL-CONFIG-033 — Logs and Diagnostics

任何 log、telemetry、error response、diagnostic bundle MUST redact：

- Key；
- Authorization；
- request body containing secret；
- provider raw body that may echo secret。

## 5. Candidate Validation / Connection Probe

### MODEL-CONFIG-050

candidate 在激活前 MUST 通过真实 provider probe 或等价的明确验证步骤。probe 只能发送 fixed synthetic content，不得包含 user document、conversation、learner state、goal、grader data 或 stored Prompt。

### MODEL-CONFIG-051

probe MUST 使用 candidate provider/model/Key 的 isolated provider instance、fixed prompt/version、bounded timeout、small output budget、no fallback。

成功至少要求：

- provider 可认证；
- model 可用；
- response 非 mock；
- returned route 与 candidate 一致（若 provider API 可验证）。

### MODEL-CONFIG-052 — Loopback Control Boundary

Model settings write/probe API MUST 只暴露在 Local Web loopback application boundary，并服从 LocalOwnerContext/origin/security contract。

MUST NOT 为此建立公网 secret-control endpoint、remote credential service 或 Askora 官方 proxy。

### MODEL-CONFIG-053

probe request/response/log MUST NOT 保存或返回 Key、Authorization header、私人学习资料、完整 raw provider response 或 stack trace。只允许 provider/model、prompt version、latency、stable result/error code、retryable、tested_at、correlation id。

## 6. Activation and Rollback

### MODEL-CONFIG-060

apply canonical sequence：

```text
validate command/revision
→ probe candidate
→ persist secret through LocalSecretStore
→ persist/activate ModelRouteProfile revision
→ refresh runtime route
→ verify runtime revision/readiness
```

用户不应手工重启 Local Server 才能完成配置生效。

实现 MAY 使用 hot reload 或由 Askora 自己协调的受控 Local Server restart，但 restart 属内部实现，不得要求 Desktop/Electron launcher。

### MODEL-CONFIG-061

activation/readiness verify 失败 MUST 恢复 prior profile/secret association 或进入明确 degraded/recovery state；不得留下“UI 显示新配置，runtime 仍使用旧配置”的 split-brain。

### MODEL-CONFIG-062

clear MUST 使用 expected revision + confirmation，创建明确 `DISABLED` / `UNCONFIGURED` profile revision，并删除/retire 对应 secret。重启后不得被 legacy `.env`、browser cache 或旧 process state 静默恢复。

### MODEL-CONFIG-063

同一 expected revision 的并发 apply/clear 只有一个可提交；后续请求返回 conflict。重复 idempotency key/command fingerprint MUST 返回已提交 summary，不重复 probe/side effect。

## 7. Routing and Fallback

### MODEL-CONFIG-070

SYS08 可以支持多个 provider/model adapter，但 v1 不建设通用插件 marketplace/runtime plugin ecosystem。

每个任务实际使用 provider/model MUST 可追踪。

### MODEL-CONFIG-071

关键任务禁止不可追踪的 silent failover。以下至少必须记录 route + fallback reason：

- Assessment；
- Knowledge Extraction；
- Learner State 相关关键推导；
- Teaching Dialogue when route change affects behavior；
- Embedding/index rebuild when model/version changes derived artifacts。

如果 workflow contract 不允许 fallback，则 provider failure MUST 返回稳定 dependency/transient error。

### MODEL-CONFIG-072

所有 provider adapter 在显式或默认 output budget 下 MUST 有 bounded semantics；不得因某 provider 忽略 omitted `max_tokens` 而形成无声明费用边界。

## 8. Cost Governance

### MODEL-CONFIG-075

BYOK 不等于无成本治理。Askora SHOULD 记录或估计：

```text
request count
input tokens
output tokens
provider
model
estimated cost
```

高成本/批量操作 MAY 有本地 limit/confirmation，但 cost estimate 不是计费事实，不得伪装为 provider 账单。

## 9. Error Contract

### MODEL-CONFIG-080

至少支持：

| Code | Category | Retryable | Required action |
|---|---|---:|---|
| `MODEL_CONFIG_STORAGE_UNAVAILABLE` | security/dependency | false | 恢复安全凭据存储或重新输入临时凭据 |
| `MODEL_CONFIG_SCHEMA_UNSUPPORTED` | validation | false | 升级 Askora 或按迁移流程重建 |
| `MODEL_CONFIG_REVISION_CONFLICT` | conflict | false | 刷新后重试 |
| `MODEL_CREDENTIAL_REJECTED` | authorization/dependency | false | 更新 Key |
| `MODEL_NOT_AVAILABLE` | dependency | false | 选择受支持模型/开通权限 |
| `MODEL_RATE_LIMITED` | transient | true | 按 retry-after 等待 |
| `MODEL_PROVIDER_TIMEOUT` | transient | true | bounded retry / 稍后再试 |
| `MODEL_PROVIDER_UNAVAILABLE` | dependency/transient | true | bounded retry / 稍后再试 |
| `MODEL_CONFIG_APPLY_FAILED` | internal | true | prior profile restored 时可重试 |
| `MODEL_CONFIG_ROLLBACK_FAILED` | internal | false | 进入本地恢复流程 |

## 10. Data and Cost Disclosure

### MODEL-CONFIG-090

Settings MUST 在 probe 动作前说明该动作只发送固定合成文本、可能产生极小 provider 费用。

### MODEL-CONFIG-091

设置页 MUST 明确 Askora 是 BYOK，真实学习时会将完成任务所需的最小资料/上下文发送给用户选择的外部 AI Provider。不得使用“全部数据永不离开本机”等与产品实际网络依赖冲突的绝对文案。

## 11. Observability

### MODEL-CONFIG-100

至少记录 sanitized：command id/fingerprint、prior/new revision、provider/model/task route、probe status/latency/error code、activation/runtime verify/rollback result、token usage/cost metadata、correlation id。

MUST NOT 记录 Key/secret reference internals/request body/raw provider error。

## 12. Tests

必须覆盖：

- schema/enum/revision；
- no Electron/Desktop dependency in production-local path；
- Local SecretStore unavailable/no plaintext fallback；
- browser no secret persistence；
- probe 401/403/404/429/timeout/5xx/empty/mock；
- probe contains no user material；
- apply no-write-on-probe-fail；
- activation/runtime revision verify；
- rollback/degraded handling；
- disabled/unconfigured state survives restart；
- development env does not resurrect cleared production config；
- secret leakage scan for API/log/backup/export/diagnostic；
- multi-task route deterministic resolution；
- no silent cross-provider failover；
- one real provider integration/E2E with BYOK in Local Web flow when release evidence requires it。

## 13. Acceptance Criteria

- `MODEL-CONFIG-AC-001`：用户在 Local Web Settings 内完成 provider/model/Key 配置和真实验证，无 Desktop/Electron prerequisite。
- `MODEL-CONFIG-AC-002`：Key 不进入 browser persistence/API response/log/Prompt metadata/export/default backup/diagnostic。
- `MODEL-CONFIG-AC-003`：probe 失败无 active config switch；activation 失败可恢复 prior revision 或明确 fail closed。
- `MODEL-CONFIG-AC-004`：clear 后重启仍是 DISABLED/UNCONFIGURED，不被 `.env` 复活。
- `MODEL-CONFIG-AC-005`：runtime provider/model/revision 与 canonical active summary 一致。
- `MODEL-CONFIG-AC-006`：provider errors 稳定分类并产生正确恢复动作。
- `MODEL-CONFIG-AC-007`：无 silent external failover/mock-as-ready/learner failure evidence。
- `MODEL-CONFIG-AC-008`：退出并重开 Askora Local Server 后 exact verified config 可恢复，前提是安全 SecretStore 可用。
- `MODEL-CONFIG-AC-009`：真实 provider、自动化、安全和 Local Web UI 门禁有当前证据。
- `MODEL-CONFIG-AC-010`：不同 task route 实际使用的 provider/model/fallback reason 可审计。

## 14. Legacy / Supersession

ADR-0013 与旧版 `MODEL-CONFIG-*` 中以下 Desktop-specific mechanics 对 v1 已 superseded：

```text
Electron safeStorage as required adapter
main/preload IPC
DESKTOP_VAULT source
Desktop child-backend port/control-token handshake
Desktop launcher environment injection
macOS App E2E as only release path
```

仍保留的原则：

- SYS08 owns routing semantics；
- secret 与 routing metadata 分离；
- safe local secret persistence；
- real candidate probe before activation；
- exact revision / optimistic concurrency；
- activation/rollback verification；
- no silent failover；
- no secret leakage。

## 15. Forbidden Implementations

禁止：

- UI 编辑 `.env`；
- Key/Key fragment 回显；
- plaintext fallback；
- browser localStorage/sessionStorage/IndexedDB 保存 Key；
- ordinary SQLite profile payload 保存明文 Key；
- Electron IPC 成为 v1 必需 model settings 路径；
- probe 携带用户资料；
- probe 失败仍激活；
- activation 失败不处理 split-brain；
- clear 后回落旧环境 Key；
- silent cross-provider failover；
- mock 显示为已连接；
- provider failure 记 learner error；
- 模型连通性宣称学习有效；
- Askora 官方云 proxy 成为 BYOK 必经路径。
