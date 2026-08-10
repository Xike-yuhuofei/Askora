# Askora Security Standard

> Spec ID：`SEC-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 Learning Core + v1 Local Web / BYOK Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`  
> Local Secret governing：ADR-0017 + `docs/specs/platform/local-secret-store.md`

## 1. Trust Boundaries

### SEC-001

用户上传文件、网页、retrieval result、model/tool output、用户自由文本、第三方 API 数据一律 untrusted。Untrusted data MUST NOT 覆盖 system policy、TeachingAction、PolicyBundle hard rules、tool permissions、state ownership 或 grader rules。

## 2. Prompt Injection

### SEC-010

材料中的“忽略指令”“调用工具”“直接给答案”等只能作为内容数据处理。

### SEC-011

防御 MUST 组合：content boundary → retrieval visibility/exposure → prompt construction → tool authorization → output validation。仅依赖 system prompt 不合格。

## 3. Tool Security

### SEC-020

模型工具 MUST registry + typed schema + allowlist + least privilege + audit。

### SEC-021

默认禁止模型任意 shell、宿主文件写入、开放网络、凭据读取。

### SEC-022

有副作用工具 MUST 有 idempotency/confirmation/reconciliation，并记录 ToolCall/ToolResult。

## 4. Model / Data Boundary

### SEC-030

外部模型只接收完成任务所需最小数据；密钥/token/无关完整 learner history MUST NOT 进入 Prompt。

### SEC-031

Sensitive data external processing 必须服从产品配置/用户授权；model router/LLM MUST NOT 自行放宽。

## 5. Answer / Support Leakage

### SEC-040 — Superseded v0.2 Exposure Field

v0.2 `TeachingAction.answer_exposure_max` 曾作为 answer leakage hard boundary。该字段语义在 v0.3 被 `SEC-200` 的正交 TeachingAction envelope supersede；`SEC-040` 仅保留历史审计线索，MUST NOT 作为 v0.3 canonical writer contract。

### SEC-041 — Grader-only Isolation

grader-only reference answer/rubric/evidence MUST 与 learner-visible context 隔离。

### SEC-200 — v0.3 TeachingAction Envelope

SYS05 TeachingAction 定义 canonical hard envelope：

```text
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

SYS02 与 SYS08 MAY 因证据/安全收紧，MUST NOT 扩大。任何无法可靠判断 exposure/support 的内容 MUST conservative block/tighten。

### SEC-201 — Assessment Integrity

独立 assessment/retrieval 场景 MUST 执行 SYS05 hard constraints；`SEC-041` 的 grader-only isolation 同时适用。Explicit user direct-answer request MUST NOT 自动绕过 assessment integrity。

### SEC-202 — Actual Exposure

实际呈现的 support/hint/exposure MUST 可记录到 SYS04 Attempt/event chain；MUST NOT 仅假设计划 envelope 等于实际经历。

## 6. Citation / Grounding

### SEC-050

资料型输出 MUST NOT 用未检索到的模型常识伪装资料事实。引用必须映射 EvidenceBundle/SourceSpan。

## 7. Upload Security

至少防御文件类型伪造、超大文件/压缩炸弹、path traversal、恶意外部引用、parser resource exhaustion、quarantined content 进入索引。阈值可配置且默认保守。

## 8. Code Execution

### SEC-060

代码评估必须隔离运行，默认无宿主敏感文件/凭据/开放网络，并限制 CPU/memory/time/process。

## 9. LocalOwner / Workspace Boundary

### SEC-065

v1 无 Account/Login/Tenant/RBAC。无认证不等于无安全边界：Local Server MUST 仅绑定 loopback，并验证受支持 browser origin；资源 query/write 仍必须解析唯一 LocalOwner 并执行 Workspace scope。

### SEC-066

Workspace 是单机数据隔离边界，不是权限角色。跨 Workspace object ref、retrieval scope、ProjectMaterial、Goal/Session binding MUST fail closed，并不得泄漏不相关 Workspace 的 object metadata。

## 10. Secrets / Logging

### SEC-070 — Logging

日志默认保存 metadata/reason/reference，不保存完整敏感上下文；debug capture 必须显式、限期、可删除。

任何 API key、Authorization、secret material、secret-bearing request body 或可恢复 credential representation MUST NOT 进入普通 log、trace、diagnostic、Prompt、frontend cache、export 或默认 backup。

### SEC-071 — Historical Desktop Model Credential

旧版 `SEC-071` 规定 Electron main + `safeStorage` + preload IPC。该 **Desktop-specific mechanism 已由 Product Positioning、ADR-0017 与 `LSS-*` supersede**。

其仍有效的保护意图仅包括：

- OS-backed secure persistence；
- no plaintext fallback；
- browser/renderer 无 saved-key readback；
- probe 不携带私人资料；
- credential 不进入日志/Prompt/export。

Electron/safeStorage/IPC/control-token 不得再作为 v1 production Local Web 的 Required 安全机制。

### SEC-072 — Local Web BYOK Credential

Production v1 provider credential MUST 服从 ADR-0017 + `LSS-*`：

```text
macOS   → exact keyring.backends.macOS.Keyring
Windows → exact keyring.backends.Windows.WinVaultKeyring
```

并要求：

- production explicit backend allowlist；
- automatic/third-party/Null/file backend rejected；
- Windows credential 使用 local-machine persistence；
- no plaintext persistent fallback；
- browser/public API 无 secret read/enumerate capability；
- ordinary SQLite 只保存 non-secret profile/ref/journal metadata；
- apply/clear 使用 durable non-secret activation journal 解决 SQLite + OS store crash consistency；
- restore 缺 secret 时进入 degraded/reconfigure，不允许 `.env` fallback。

### SEC-073 — Local Secret Threat Claim Boundary

OS credential storage 保护的是 Askora 普通数据文件、browser、日志、诊断和 backup/export 泄漏面。Askora MUST NOT 宣称它能抵御同一 OS 用户权限下的任意代码执行、完整机器 compromise 或提供 native app sandbox/hardware-backed isolation。

未来更强 native credential ACL MAY 通过新的 ADR 引入，但 MUST NOT 让 Desktop shell 成为 v1 prerequisite。

## 11. Dependencies

### SEC-080

新增生产依赖需要目的/维护/安全评估；执行代理 MUST NOT 自行加入大型 autonomous-agent/security framework 解决局部问题。

`keyring` 作为 ADR-0017 已批准的窄 production dependency；版本必须 lock，升级必须重新运行 `LSS-*` backend allowlist/leakage/crash tests。

### SEC-081 — Rich Response Renderer

模型/检索/工具产生的 Markdown、公式和结构化 block 一律 untrusted。前端 MUST 使用 typed component allowlist；MUST NOT 执行 raw HTML、MDX、script、模型指定组件、代码块或 arbitrary card command。链接协议只允许 `http`/`https`；v1.0 remote image/file/data URL MUST blocked。公式 renderer MUST 禁止 trusted external-resource commands，并限制 expansion/size。

### SEC-082 — Recovery and Export

Recovery/backup/export 必须服从当前 v1 Data Control contract。任何 package/export MUST NOT 包含 provider API key、recoverable model credential、内部 Prompt/system instructions、grader-only answer/rubric、其他 Workspace 数据或本地绝对路径。

User Data Export 使用显式 allowlist，MUST NOT 包含 KEK/Recovery Key/provider key、内部 Prompt/system instructions、grader-only answer/rubric、其他 owner 数据或本地绝对路径。若历史 recovery package 仍使用加密恢复密钥，其机制只作为对应 historical/current data-control contract 的实现证据，不得重新引入 Account credential semantics。

### SEC-083 — Destructive Data Control

Erasure/Permanent Delete 必须固定 scope、影响预览、显式用户动作、幂等与最小 audit receipt。外部模型、资料内容、renderer 或普通 retry 无权触发/扩大删除范围。

## 12. Policy Override Protection

### SEC-210

LLM/Agent、retrieved content、SYS08 fallback、experiment variant MUST NOT override SYS05 typed hard constraint 或恢复 hard-filtered action。

### SEC-211

Legacy Socratic selector/state graph MUST NOT 成为 final TeachingAction owner 或 exposure override；迁移期只允许 bounded adapter/move provider/execution role。

## 13. Tests

必须覆盖：

- document/retrieval/tool injection；
- grader/answer leakage；
- attempted scaffold/hint/exposure expansion；
- direct-answer assessment integrity；
- actual exposure capture；
- path traversal；
- LocalOwner/Workspace cross-scope isolation；
- secret/log leakage；
- malicious structured output；
- tool parameter validation；
- legacy Socratic no override；
- LocalSecretStore exact backend allowlist；
- Null/third-party/override backend rejection；
- Windows local-machine credential persistence；
- probe payload excludes private data；
- browser/API/SQLite/log/export/backup zero-secret leakage；
- activation crash/restart matrix；
- clear remains disabled even if orphan-secret cleanup fails；
- restore missing secret requires reconfiguration and no env resurrection。

Data lifecycle 还必须覆盖 recovery wrong-key/tamper/truncation/path/limits（如当前 recovery format 适用）、export zero-secret leakage、erasure confirmation/scope、managed old-backup no-resurrection。

## 14. Acceptance Criteria

- `SEC-AC-001`：恶意文档不能改变 TeachingAction/PolicyBundle/tool permission。
- `SEC-AC-002`：模型不能调用未注册工具。
- `SEC-AC-003`：grader-only answer 不进入 learner output。
- `SEC-AC-004`：外部模型请求不包含测试密钥/token 或无关个人数据。
- `SEC-AC-005`：quarantined 内容不进入 retrieval。
- `SEC-AC-006`：代码评估无法访问宿主敏感资源。
- `SEC-AC-007`：引用声明可追踪 SourceSpan。
- `SEC-AC-201`：SYS02/SYS08 无扩大 SYS05 support/exposure envelope 的路径。
- `SEC-AC-202`：hard rule 无 LLM/experiment/legacy bypass。
- `SEC-AC-203`：browser、普通 API、SQLite profile、日志、Prompt、telemetry、export/default backup 无模型明文 credential。
- `SEC-AC-204`：production LocalSecretStore 只接受 ADR-0017/LSS 指定 OS-backed backend；安全存储不可用时拒绝持久化，不降级明文。
- `SEC-AC-205`：clear 后 canonical routing 保持 disabled，即使旧 secret 删除失败或开发 `.env` 仍存在。
- `SEC-AC-206`：模型配置任一 crash phase 不产生 silent profile/runtime split-brain。

## 15. Legacy Mapping

历史整数/L0-L4 exposure MAY read-only/audit；canonical writer MUST 只写 `answer_exposure`，不得 permanent dual-write。旧 `SEC-040` 的保护意图仍由 `SEC-200` 承接；旧 `SEC-041` 保留 grader-only isolation。

旧 Desktop credential security 只保留安全意图，具体 Electron mechanics 由 `SEC-071` 明确 superseded。

## 16. Forbidden Implementations

禁止：

- Prompt 作为唯一权限层；
- autonomous agent 任意 shell/network；
- reference answer 与 learner prompt 无隔离混放；
- 外部模型默认接收全部个人资料；
- 日志打印 secret/完整敏感 Prompt；
- browser 获取 saved credential/decrypt/file control capability；
- LocalSecretStore 不可用时明文落盘；
- automatic/unknown keyring backend 作为 production security decision；
- probe 携带个人资料；
- parser 信任扩展名；
- 恶意 retrieval content 提升为 system instruction；
- 继续写 `answer_exposure_max` 为 canonical security truth；
- SYS08/LLM 自动扩大 TeachingAction envelope；
- Account/JWT/AuthSession 重新成为 v1 security prerequisite。

## 17. Historical Identity / Account Security

旧 `SEC-300..303` 关于 Password、JWT、AuthSession、Account Deletion 的要求属于 P1-05 历史实现合同，已由 `PRODUCT-POSITIONING.md` + ADR-0015 / `LID-*` supersede，不得作为 v1 active runtime requirement。其仍有价值的通用原则（secret 不明文、rate-limit destructive/recovery operations、删除 no-resurrection、最小 audit）由当前 LocalOwner/Data Control/LocalSecretStore 合同承接。以下为 v1 生效的无认证 active requirements：

Askora 为本地单用户 App，无注册/登录/登出、无密码、无 JWT/会话、无 recovery credential、无账号删除。`LocalOwner` 是唯一本地数据归属主体，MUST NOT 保存 phone/email/password/token/recovery secret/device fingerprint 等认证材料（见 `identity-privacy-lifecycle.md` LID-003）。

### SEC-301

无认证 runtime MUST 只监听 loopback（`127.0.0.1` / `::1`）；`0.0.0.0`、LAN 或公网接口 MUST fail startup。CORS/WebSocket MUST 仅 allowlist loopback origins（LID-020..022）。`/auth/*`、dev auto-login、account deletion routes MUST 停止注册（LID-040）。

### SEC-302

危险本地数据清除（Erase Selected Local Data / Reset Local Workspace）MUST 使用 preview + expiring confirmation + typed phrase + idempotency + durable receipt，且不得重新引入 password 或 account-deletion 语义（LID-061/062）。

### SEC-303

数据清除必须 owner-scoped、reconciliation zero-residual；tombstone/receipt 不得保存 PII/content/secret；restore barrier 必须在本地数据恢复与后台处理前生效。

## 18. P1-06 Onboarding Security

### SEC-320

Onboarding view/preference/log MUST NOT 包含 Key/fragment、Prompt、grader-only、raw provider body、absolute path 或其他 Workspace ref。Boundary copy 只能引用当前 MODEL-CONFIG/P1-03 已验证事实，不得承诺完全离线或绝对隐私。

### SEC-321

Onboarding MUST NOT 自动 probe provider、加载未经选择的私人文档、创建样例/Goal/Activity 或执行 recovery command。所有导航后的副作用仍由原 owner command 的 idempotency/security gate 控制。
