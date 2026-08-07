# Askora Security Standard

> Spec ID：`SEC-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Trust Boundaries

### SEC-001

以下输入一律视为不可信：用户上传文件、网页内容、检索结果、模型输出、Tool output、用户自由文本、第三方 API 数据。

不可信数据 MUST NOT 覆盖 system policy、TeachingAction、tool permissions、state ownership 或 grader rules。

## 2. Prompt Injection

### SEC-010

上传材料中的“忽略此前指令”“调用某工具”“输出答案”等文本只能作为学习材料内容处理。

### SEC-011

防御必须同时存在于：

```text
content boundary
→ retrieval visibility/exposure
→ prompt construction
→ tool authorization
→ output validation
```

仅靠 system prompt 提醒“不要听文档指令”不合格。

## 3. Tool Security

### SEC-020

模型可用工具必须：registry + typed schema + allowlist + least privilege + audit。

### SEC-021

默认禁止模型任意 shell、宿主文件写入、任意网络访问、凭据读取。

### SEC-022

有副作用工具必须要求幂等/确认机制，并记录 ToolCall/ToolResult。

## 4. Model/Data Boundary

### SEC-030

外部模型仅接收完成任务所需最小数据。密钥、认证 token 和与任务无关的完整 learner history MUST NOT 进入 Prompt。

### SEC-031

隐私分类为 sensitive 的数据是否允许 external_processing 必须由产品配置/用户授权决定，不能由模型路由自行放宽。

## 5. Answer Leakage

### SEC-040

`TeachingAction.answer_exposure_max` 是硬边界；retrieval 与 generation 都必须执行。

### SEC-041

grader-only reference answer/rubric/evidence 必须与 learner-visible context 隔离。

## 6. Citation / Grounding

### SEC-050

资料型输出不得用未检索到的模型常识伪装成资料事实。引用必须映射到 EvidenceBundle/SourceSpan。

## 7. Upload Security

至少防御：

- 文件类型伪造；
- 超大文件/压缩炸弹；
- path traversal；
- 恶意嵌入/外部引用；
- parser resource exhaustion；
- quarantined content 进入索引。

阈值可配置，但默认应保守。

## 8. Code Execution

### SEC-060

代码评估必须在隔离环境运行，默认无宿主文件、凭据和开放网络权限，并限制 CPU/memory/time/process。

## 9. Authorization

即使 v0.2 单用户本地优先，也要保持资源 owner 边界。服务模式必须验证 user/resource ownership，不允许仅凭 object id 访问其他用户数据。

## 10. Secrets

- 只从受控配置/secret store/environment 读取；
- 不提交仓库；
- 不输出日志；
- 不发送给 LLM；
- 前端 bundle 不含服务端 secret。

## 11. Logging & Retention

### SEC-070

日志默认保存 metadata/reason/reference，不保存完整敏感上下文。需要 debug capture 时必须显式开启、限定期限并可删除。

## 12. Dependencies

### SEC-080

新增生产依赖需要明确目的、维护性和安全评估；Codex 不得自行加入大型 Agent/security framework 解决局部问题。

## 13. Tests

必须有固定回归样本：

- document prompt injection；
- retrieval injection；
- tool-call injection；
- answer leakage；
- grader answer leakage；
- path traversal；
- unauthorized resource access；
- secret/log leakage；
- malicious model structured output；
- tool parameter validation。

## 14. Acceptance Criteria

- `SEC-AC-001`：恶意文档不能改变 TeachingAction/工具权限。
- `SEC-AC-002`：模型不能调用未注册工具。
- `SEC-AC-003`：grader-only 答案不进入学习者输出。
- `SEC-AC-004`：外部模型请求不包含测试密钥/认证 token。
- `SEC-AC-005`：quarantined 内容不进入检索。
- `SEC-AC-006`：代码评估无法访问宿主敏感资源。
- `SEC-AC-007`：引用声明可追踪真实 SourceSpan。

## 15. Forbidden Implementations

禁止：

- “Prompt 足够强所以无需权限层”；
- 给 autonomous agent 任意 shell/network；
- 把 reference answer 与 learner prompt 放在同一未隔离 context；
- 外部模型默认接收全部个人资料；
- 在日志打印 API key/token/完整敏感 Prompt；
- parser 直接信任上传文件扩展名；
- 检索到恶意指令后把它提升为 system instruction。
