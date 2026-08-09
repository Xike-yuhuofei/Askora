# Askora Security Standard

> Spec ID：`SEC-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

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

v0.2 `TeachingAction.answer_exposure_max` 曾作为 answer leakage hard boundary。该**字段语义**在 v0.3 被 `SEC-200` 的正交 TeachingAction envelope supersede；`SEC-040` 仅保留历史审计线索，MUST NOT 作为 v0.3 canonical writer contract。

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

## 9. Authorization

本地单用户模式仍需保持 owner boundary；服务模式必须验证 user/resource ownership，不允许仅凭 object id 访问其他用户数据。

## 10. Secrets / Logging

Secrets 只从受控配置读取，不提交仓库、不输出日志、不发送 LLM、不进入前端 bundle。

### SEC-071 — Desktop Model Credential

macOS desktop credential MUST 由 Electron main 使用 `safeStorage` 加密保存，密钥保护委托给 OS Keychain；禁止明文 fallback。renderer 只能获得 `configured/provider/model/source/revision/verified_at` 等脱敏状态，MUST NOT 获得 decrypt/file/env/control-token 能力。IPC handler MUST 验证 sender/origin，并使用固定 allowlist channel。

候选 credential probe 只可发送固定 synthetic text，不发送个人资料、学习历史、EvidenceBundle 或用户文档；provider 返回只用于连通性/模型有效性判定，不进入学习事实。probe、日志、错误、telemetry 均不得包含 credential、ciphertext、control token 或原始 provider response。

### SEC-070

日志默认保存 metadata/reason/reference，不保存完整敏感上下文；debug capture 必须显式、限期、可删除。

## 11. Dependencies

### SEC-080

新增生产依赖需要目的/维护/安全评估；执行代理 MUST NOT 自行加入大型 autonomous-agent/security framework 解决局部问题。

### SEC-081 — Rich Response Renderer

模型/检索/工具产生的 Markdown、公式和结构化 block 一律 untrusted。前端 MUST 使用 typed component allowlist；MUST NOT 执行 raw HTML、MDX、script、模型指定组件、代码块或 arbitrary card command。链接协议只允许 `http`/`https`；v1.0 remote image/file/data URL MUST blocked。公式 renderer MUST 禁止 trusted external-resource commands，并限制 expansion/size。

### SEC-082 — Recovery and Export

Recovery Package MUST authenticated encrypt，并使用独立 Recovery Key；明文 key 不得进入 package/catalog/log/argv/localStorage。设备副本须由 platform secure storage 保护。恢复解压必须阻止 traversal、symlink/special file、duplicate entry、size/compression abuse；激活前在 staging 完整校验。

User Data Export 使用显式 allowlist，MUST NOT 包含 password/hash、JWT/refresh token、KEK/Recovery Key/provider key、内部 Prompt/system instructions、grader-only answer/rubric、其他用户数据或本地绝对路径。

### SEC-083 — Destructive Data Control

Erasure 必须 current-user、影响预览、expiring confirmation、显式用户动作、幂等与最小 audit receipt。外部模型、资料内容、renderer 或普通 retry 无权触发/扩大删除范围。

## 12. Policy Override Protection

### SEC-210

LLM/Agent、retrieved content、SYS08 fallback、experiment variant MUST NOT override SYS05 typed hard constraint 或恢复 hard-filtered action。

### SEC-211

Legacy Socratic selector/state graph MUST NOT 成为 final TeachingAction owner 或 exposure override；迁移期只允许 bounded adapter/move provider/execution role。

## 13. Tests

必须覆盖：document/retrieval/tool injection；grader/answer leakage；attempted scaffold/hint/exposure expansion；direct-answer assessment integrity；actual exposure capture；path traversal；unauthorized access；secret/log leakage；malicious structured output；tool parameter validation；legacy Socratic no override；safeStorage 不可用；renderer/IPC 越权；control token 错误；probe payload 私密数据缺席；clear/rollback 后 secret 不泄漏。

P1-03 还必须覆盖 recovery wrong-key/tamper/truncation/path/limits、platform key boundary、export zero-secret leakage、erasure confirmation/authorization、managed old-backup no-resurrection。

P1-03 还必须覆盖 recovery wrong-key/tamper/truncation/path/limits、platform key boundary、export zero-secret leakage、erasure confirmation/authorization、managed old-backup no-resurrection。

## 14. Acceptance Criteria

- `SEC-AC-001`：恶意文档不能改变 TeachingAction/PolicyBundle/tool permission。
- `SEC-AC-002`：模型不能调用未注册工具。
- `SEC-AC-003`：grader-only answer 不进入 learner output。
- `SEC-AC-004`：外部模型请求不包含测试密钥/token。
- `SEC-AC-005`：quarantined 内容不进入 retrieval。
- `SEC-AC-006`：代码评估无法访问宿主敏感资源。
- `SEC-AC-007`：引用声明可追踪 SourceSpan。
- `SEC-AC-201`：SYS02/SYS08 无扩大 SYS05 support/exposure envelope 的路径。
- `SEC-AC-202`：hard rule 无 LLM/experiment/legacy bypass。
- `SEC-AC-203`：renderer、普通 API、日志、Prompt、telemetry 无模型明文 credential。
- `SEC-AC-204`：desktop vault 无 OS encryption 时拒绝写入，不降级为明文。

## 15. Legacy Mapping

历史整数/L0-L4 exposure MAY read-only/audit；canonical writer MUST 只写 `answer_exposure`，不得 permanent dual-write。旧 `SEC-040` 的保护意图仍由 `SEC-200` 承接；旧 `SEC-041` 保留原 grader-only isolation 语义。

## 16. Forbidden Implementations

禁止：Prompt 作为唯一权限层；autonomous agent 任意 shell/network；reference answer 与 learner prompt 无隔离混放；外部模型默认接收全部个人资料；日志打印 secret/完整敏感 Prompt；renderer 获取明文 credential/decrypt/file/control token；safeStorage 不可用时明文落盘；probe 携带个人资料；parser 信任扩展名；恶意 retrieval content 提升为 system instruction；继续写 `answer_exposure_max` 为 canonical security truth；SYS08/LLM 自动扩大 TeachingAction envelope。

## 17. Identity and Privacy Security

### SEC-300

Password/recovery/deletion secret MUST 使用适用的 slow hash 或 keyed digest，MUST NOT 明文持久化、日志记录、进入 Prompt、普通 export 或 frontend user cache。新密码使用 Argon2id；历史 bcrypt 只作兼容读取/rehash。

### SEC-301

access/refresh token MUST 绑定 durable AuthSession/token family；refresh replay 必须 revoke family。Redis outage、进程重启或前端 localStorage 清理不得恢复 revoked session。

### SEC-302

修改密码、恢复和账号删除必须重新认证并 server-side rate limit。unknown/existing identifier response 不得泄漏账号存在性。

### SEC-303

账号删除必须 cross-user fail closed、manifest scoped、reconciliation zero-residual。tombstone/receipt 不得保存 PII/content/secret；restore barrier 必须在普通认证和后台处理前生效。

## 18. P1-06 Onboarding Security

### SEC-320

Onboarding view/preference/log MUST NOT 包含 Key/fragment、Prompt、grader-only、raw provider body、
absolute path 或其他用户 ref。Boundary copy 只能引用 P1-02/P1-03 已验证事实，不得承诺完全离线或
绝对隐私。

### SEC-321

Onboarding MUST NOT 自动 probe provider、加载未经选择的私人文档、创建样例/Goal/Activity 或执行
recovery command。所有导航后的副作用仍由原 owner command 的 auth/idempotency/security gate 控制。
