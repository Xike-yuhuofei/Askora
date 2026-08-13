# Askora v1 Local Web Quality Reconciliation

> Spec ID：`QUAL-V1-*`  
> 状态：Canonical Superseding Quality Delta  
> 版本：v1 Local Web Baseline  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`  
> 配套规范：`docs/specs/quality/ci-infrastructure-standard.md`

---

## 1. Purpose

本文件用于消解 Askora 历史 v0.3 / P1 质量规范与当前冻结产品定位之间的冲突。

它不重写已经有效的教学正确性、replay、assessment、security、recovery、observability 合同；只对已经失效的产品形态假设做 supersession。

发生冲突时，权威顺序为：

```text
PRODUCT-POSITIONING.md
        ↓
Accepted current ADR / Canonical Design
        ↓
v1 Local Web Quality Reconciliation
        ↓
CI Infrastructure Standard
        ↓
Testing / Security / Observability / Definition of Done historical clauses
        ↓
Workflow / Tests / Code
```

---

## 2. Global Reconciliation Rules

### QUAL-V1-001 — Current Product Truth

Askora v1 的质量合同必须以以下产品事实为前提：

- 单用户；
- Local Web Application；
- Browser → loopback Local Server；
- SQLite + Local Files 为核心本地权威存储；
- 无注册、无登录、无账号体系；
- 无 Tenant / Organization / RBAC / 多用户服务模式；
- Docker / Redis / PostgreSQL 不得成为最终用户 runtime requirement；
- BYOK 外部 AI Provider 是不可靠外部依赖；
- Chrome / Edge / Chromium 为 v1 正式浏览器基线；
- macOS / Windows 原生客户端不是 v1 release prerequisite。

### QUAL-V1-002 — Preserve Learning-core Contracts

以下合同继续有效，不因 Local Web 产品形态变化而弱化：

- Teaching Policy deterministic / explainable；
- Assessment integrity；
- Learning Evidence → Learner State；
- replay / trace / version pinning；
- G0 / G1 policy correctness；
- no forbidden TeachingAction；
- answer / rubric leakage protection；
- prompt injection / tool authorization；
- Derived Data rebuildability；
- migration / restart / recovery / idempotency；
- Source-grounded provenance；
- LLM 不直接成为 Canonical State writer。

### QUAL-V1-003 — Historical Test Oracle Must Not Restore Removed Product Features

历史测试仍然可以作为迁移证据或历史回归样本，但如果其预期行为要求恢复以下能力，则不得继续作为 v1 Required truth：

```text
Login / Register
Password lifecycle
AuthSession / JWT
Account recovery
multi-user / cross-user service mode
PostgreSQL production persistence
Redis production runtime
packaged native macOS application
Electron-only credential semantics
```

---

## 3. Testing Standard Reconciliation

### QUAL-V1-100 — Retained Testing Layers

`testing-standard.md` 的 L0～L6 分层继续有效：

```text
L0 Static / Architecture
L1 Unit
L2 Contract
L3 Integration
L4 End-to-End
L5 Replay / Migration / Recovery
L6 AI Quality / Security Evaluation
```

其中 L3 Required persistence baseline 必须以真实 SQLite 为主；PostgreSQL 只能作为 Optional compatibility，除非未来产品定位重新纳入。

### QUAL-V1-101 — Current Required Integration Truth

Required integration tests SHOULD 优先使用：

```text
isolated AskoraData
+ SQLite
+ Local Files
+ local background jobs
+ deterministic model fixtures
```

不得要求 Redis / PostgreSQL / Docker 才能建立有效 integration environment。

### QUAL-V1-102 — Browser E2E

v1 Required L4 的产品级入口改为：

```text
Chromium
→ 127.0.0.1:<port>
→ Askora Local Server
→ SQLite / Local Files
```

历史 packaged macOS / Electron E2E 只能作为 historical/optional evidence，不得继续作为 v1 Required release prerequisite。

### QUAL-V1-103 — Real Model Evidence

保留“Mock 不得伪装真实 Provider 当前可用”的原则。

但普通 PR Required CI 不要求真实 BYOK Key。真实 Provider connectivity、actual structured output、configured-model canonical learning turn 应放在：

- manual validation；
- scheduled provider smoke；
- release evidence；
- 明确声称 Provider 当前可用的任务验收。

### QUAL-V1-104 — Cross-user Tests

历史 `cross-user` / service-mode authorization tests 的 Required 语义被 supersede。

当前必须重写为适用的边界测试：

- LocalOwnerContext 唯一 owner；
- Workspace isolation；
- RetrievalScope isolation；
- 禁止跨 Workspace 非授权批量状态修改；
- legacy owner migration fail-closed。

### QUAL-V1-105 — Database Compatibility

历史 SQLite/PostgreSQL 双数据库 Required matrix 被 supersede。

当前 Required：

- fresh SQLite → head；
- representative legacy SQLite → head；
- migration failure preserves durable data；
- schema/minimum reader/writer compatibility；
- rebuild / restart recovery。

PostgreSQL migration/adapter verification MAY 保留在 Optional workflow。

### QUAL-V1-106 — Desktop Model Configuration Tests

历史 `Desktop model configuration L1～L4` 中与模型安全和原子配置相关的意图继续有效，但 native desktop-specific transport/packaging 要求被 supersede。

当前应验证：

- API Key 由本机安全凭据抽象保存；
- frontend 永不获得 secret；
- provider probe 使用最小 synthetic payload；
- candidate config 不在验证前错误成为 active truth；
- activation / rollback / clear / revision 可验证；
- Local Server restart 后配置状态正确恢复；
- 真实 Provider evidence 与 deterministic Required CI 分离。

---

## 4. Definition of Done Reconciliation

### QUAL-V1-200 — Retained DoD

`DOD-001`～`DOD-030`、Engineering Gate、Policy Correctness Gate、Learning Evidence Gate 的核心语义继续有效。

Engineering Correct 仍不得被描述为 Learning Effective。

### QUAL-V1-201 — DOD-031 Supersession

历史 `DOD-031 Desktop Model Settings Closure` 中以下要求不再是 v1 产品 DoD：

- packaged macOS app；
- Electron renderer/main IPC 作为唯一验收路径；
- macOS relaunch 作为 v1 release prerequisite。

当前对应 closure 改为：

```text
Local Web Settings
→ local credential storage abstraction
→ provider probe
→ atomic activation / rollback
→ Local Server restart
→ browser reconnect
→ configured state preserved
```

若声明某真实 Provider 当前可用，仍必须提供当前真实 Provider 证据。

### QUAL-V1-202 — Product DoD

任何功能声称 v1 Engineering DONE 时，不得新增以下隐式运行前提：

- Docker daemon；
- Redis server；
- PostgreSQL server；
- Askora cloud；
- Authentication service；
- native desktop shell。

---

## 5. Security Standard Reconciliation

### QUAL-V1-300 — Current Authorization Boundary

`security-standard.md` 中“服务模式 cross-user authorization”不再是 v1 产品合同。

当前安全边界为：

```text
loopback process boundary
+ LocalOwnerContext
+ Workspace / object scope
+ typed domain authorization
+ explicit destructive-operation confirmation
```

单用户不等于无安全边界；路径、Workspace、工具、LLM 写入权限、secret 与 destructive action 仍必须 fail closed。

### QUAL-V1-301 — Desktop Credential Clause Supersession

历史 `SEC-071 Desktop Model Credential` 的安全意图保留，但 Electron/macOS `safeStorage` 不是 v1 唯一 canonical implementation。

当前 canonical contract：

- secret 仅在本机保存；
-优先使用操作系统安全凭据存储；
- browser/frontend 不接触明文 API Key；
- secret 不进入日志、backup、diagnostics、export、Prompt；
- credential backend 必须可替换，不能绑定 native desktop UI 架构。

### QUAL-V1-302 — Historical Auth Security

`SEC-300`～`SEC-303` 中 password/access token/refresh token/AuthSession/account recovery 等认证合同对 v1 runtime 已 superseded。

它们 MAY 保留为 historical migration / deletion evidence，但不得：

- 成为 Required test oracle；
- 迫使 runtime 继续保留 JWT/password/session tables 或 write path；
- 通过 hidden login / auto-login 继续存在。

### QUAL-V1-303 — Erasure Semantics

历史 `current-user` / account deletion wording 应重解释为当前 LocalOwner 数据控制语义。

删除仍必须满足：

- impact preview；
- explicit confirmation；
- idempotency；
- canonical durable data scope；
- derived data cleanup/rebuild semantics；
- backup/restore resurrection protection where applicable。

---

## 6. Observability Standard Reconciliation

### QUAL-V1-400 — Local Observability First

保留 DecisionTrace / OutcomeObservation / ModelInference / retrieval / job / recovery observability。

v1 默认目标是本地诊断，不要求远程 telemetry backend。

Logs / traces / metrics 不得成为业务事实源。

### QUAL-V1-401 — Model Configuration Observability

历史 desktop-specific model configuration observability 应重解释为 Local Web model configuration lifecycle：

```text
candidate
→ probe
→ activate / reject
→ revision
→ rollback / clear
→ Local Server restart verification
```

记录 provider/model/revision/outcome/latency/stable error code；不得记录 credential、完整 Prompt 或原始敏感 provider body。

### QUAL-V1-402 — Ownership Alerts

历史 `cross-owner write violation` 应在 v1 Required Gate 中解释为：

- invalid LocalOwner mutation；
- cross-Workspace scope violation；
- retrieval scope leakage；
- canonical owner bypass。

---

## 7. CI Classification Contract

### QUAL-V1-500 — Required

以下属于 v1 Required quality truth：

- Product Boundary；
- backend architecture / unit / contract / SQLite integration；
- Teaching Policy / Assessment / Learner State correctness；
- migration / restart / recovery / rebuild；
- Local Web Chromium E2E；
- static quality；
- secret/data boundary；
- Workspace / RetrievalScope isolation。

### QUAL-V1-501 — Optional / Manual / Scheduled

以下默认不作为 `Askora CI / Required`：

- PostgreSQL compatibility；
- Docker image build；
- Redis legacy adapter tests；
- secondary Python compatibility；
- real-provider uptime smoke；
- expensive multi-model eval；
- native desktop historical validation；
- service-mode multi-user tests。

### QUAL-V1-502 — Delete vs Historical

没有未来迁移、审计或兼容价值的 stale tests SHOULD 删除。

仍有价值的旧测试必须明确：

```text
HISTORICAL
or
OPTIONAL_COMPATIBILITY
```

禁止让未分类 legacy tests 混在 Required suite 中。

---

## 8. Acceptance Criteria

- `QUAL-V1-AC-001`：Testing / Security / Observability / DoD 的当前解释不再要求 native desktop、multi-user、Auth、PostgreSQL production 或 Redis production。
- `QUAL-V1-AC-002`：历史教学内核 deterministic / replay / policy / assessment / evidence contracts 未被弱化。
- `QUAL-V1-AC-003`：Required integration baseline 明确为 SQLite Production Local。
- `QUAL-V1-AC-004`：Required E2E 明确为 Chromium + loopback Local Server。
- `QUAL-V1-AC-005`：真实 Provider evidence 与普通 deterministic PR CI 分离。
- `QUAL-V1-AC-006`：cross-user tests 已重写为 LocalOwner / Workspace / RetrievalScope 边界，或降级为 historical。
- `QUAL-V1-AC-007`：password/JWT/AuthSession security clauses 不再成为 v1 Required runtime truth。
- `QUAL-V1-AC-008`：credential security 不绑定 Electron/macOS implementation。
- `QUAL-V1-AC-009`：PostgreSQL/Docker compatibility failure 默认不阻断 v1 Required Gate。

---

## 9. Forbidden Interpretations

禁止：

- 因旧测试仍存在而恢复 Login/JWT/AuthSession；
- 因旧 DOD 写有 packaged macOS app 而把原生客户端重新纳入 v1；
- 因旧 security 文档写有 cross-user 而建立多租户授权层；
- 因 PostgreSQL contract test 存在而将其重新变成 production persistence；
- 因 Electron `safeStorage` 历史实现存在而让浏览器依赖 Electron；
- 删除 Teaching Policy / Assessment / Evidence / replay 等仍有效核心测试来“简化”CI；
- 把真实 Provider outage 解释为 deterministic product logic failure。

---

## 10. Final Rule

质量基础设施只保护**当前产品真值**和**仍有效的学习系统合同**。

历史技术栈、历史客户端形态和历史账号系统可以保留为证据，但不得继续拥有 v1 release veto 权。