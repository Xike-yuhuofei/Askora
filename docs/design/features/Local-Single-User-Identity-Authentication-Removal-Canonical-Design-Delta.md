# Askora Local Single-User Identity & Authentication Removal — Canonical Design Delta

> 状态：FROZEN  
> 日期：2026-08-10  
> 目标：将 Askora 从“本地优先账号系统”收敛为“本地单用户学习 App”，彻底移除登录与账号认证，同时保留稳定的数据归属、学习者身份与数据治理能力。

## 1. Canonical Product Decision

Askora 的目标产品形态是本地单机、个人长期使用的 AI 学习 App。

因此，从本 Delta 起，Askora **不再存在以下产品概念**：

- Account / 账号；
- Login / Register / Logout；
- Password / Password Recovery；
- Access Token / Refresh Token / JWT；
- Auth Session / Device Session；
- Recovery Credential / Recovery Kit；
- Account Deletion Lifecycle；
- 以“是否已登录”决定业务访问权限的 Protected Route。

Askora 仍然必须存在一个稳定、长期、可迁移的数据归属主体，但该主体是 **Local Owner / Learner Identity**，不是认证账号。

## 2. First-Principles Boundary

单用户并不意味着可以删除身份概念。

Askora 的学习记录、资料、目标、计划、对话、评估、Learner State、DecisionTrace 与数据删除流程仍需要回答：

> 这些数据属于哪个长期学习者？

Canonical answer：

```text
LocalDataStore
└── LocalOwner
    └── Learner
        ├── Profile
        ├── Documents
        ├── Goals
        ├── Learning Records
        ├── Dialogs
        └── Model / Decision / Outcome Records
```

`LocalOwner` 是本地数据所有权事实；`Learner` 是学习领域主体。两者可在首版使用同一 canonical UUID，但语义必须明确：它不是 credential subject，也不产生登录会话。

## 3. LocalOwnerContext

### 3.1 Canonical State

每个 Askora 本地数据存储最多有一个 canonical `LocalOwner`：

```yaml
local_owner:
  owner_id: uuid
  schema_version: "1.0"
  created_at: datetime
```

约束：

- `owner_id` 在该数据存储生命周期内稳定；
- App 启动时直接加载，不需要用户证明身份；
- 不保存密码、手机号、邮箱、微信 OpenID、token、设备指纹等认证材料；
- 安装实例 ID、浏览器指纹、机器 ID 不能成为学习数据归属 truth；
- nickname、偏好等属于 LearnerProfile / Settings，不属于 LocalOwner credential。

### 3.2 Runtime Context

业务入口统一解析：

```text
Request / App Command
→ LocalOwnerContext
→ Learner-owned Service / Query
```

不得再存在：

```text
Request
→ Bearer Token
→ AuthSession
→ CurrentUser
→ Business Service
```

## 4. Security Boundary After Authentication Removal

移除认证后，Askora 的安全边界从“应用层登录认证”切换为“本机进程 / loopback 边界”。

只要当前仍采用 Web-first 前后端开发形态，就必须满足：

- backend MUST 只监听 loopback：`127.0.0.1` 或 `::1`；
- MUST NOT 默认监听 `0.0.0.0`、LAN IP 或公网接口；
- CORS MUST 只允许明确的 loopback frontend origins；
- WebSocket MUST 使用同样的 local-origin 边界；
- `/auth/*`、`/account/*` 不得作为“额外保护层”残留；
- 如果未来重新支持 LAN / remote / multi-device service，必须通过新的 Canonical Design + ADR 重新引入 authentication，而不能静默放宽 host 配置。

**无认证部署与非 loopback 网络暴露互斥。**

## 5. User / Learner Semantic Split

当前 `User` 同时混合了：

1. credential/account state；
2. product identity；
3. learner/data ownership。

新的 canonical split：

### 删除

- phone / email / wechat identity；
- password hash / credential version；
- last login；
- auth role/status；
- auth sessions；
- recovery credentials / throttles；
- account deletion state；
- identity command receipts that exist only for authentication/account lifecycle。

### 保留或迁移

- learner-owned stable UUID；
- nickname → LearnerProfile；
- learning/data ownership references；
- profile/dialog/document/goal/assessment/planning ownership；
- privacy/data-erasure subject references where仍需要确定数据归属。

历史字段名 `user_id` / `pseudonym_id` MAY 在迁移窗口作为 storage compatibility 保留，但不得继续被解释为登录账号，也不得形成第二身份 truth。

## 6. Data Control Is Not Account Management

认证退役不得删除真正有价值的数据治理能力。

继续保留：

- 数据导出；
- 删除单份资料；
- 删除学习记录；
- 删除模型执行记录；
- 错误恢复中心；
- durable erasure / no-resurrection 机制中与本地数据安全真正相关的部分。

删除：

- “删除账号”；
- re-auth password confirmation；
- 24h account deletion grace period；
- deletion-control token；
- account tombstone / ACTIVE→DELETION_PENDING 等账号状态机。

产品语义改为：

```text
Erase Selected Local Data
Reset Local Learning Data
Reset Local Workspace   # 若未来产品提供完整重置
```

危险操作仍必须使用 preview + explicit typed confirmation，但确认的目的属于 destructive-action safety，不属于身份认证。

## 7. Settings Information Architecture Delta

Settings 删除：

- 账号信息；
- 手机号；
- 修改密码；
- 登录设备 / 会话；
- 退出登录；
- 恢复套件；
- 删除账号；
- JWT / 会话安全事实文案。

Settings 保留并重新组织为：

```text
Settings
├── AI 与模型
├── 本地数据
│   ├── 数据导出
│   ├── 清除资料 / 学习记录
│   └── 本地工作区重置（若实现）
├── 存储与运行状态
├── 错误恢复中心
├── 隐私
└── 关于
```

“昵称”如果继续存在，应放入 Profile / Personalization，而不是 Account。

## 8. First-use Journey Delta

首次启动：

```text
App start
→ ensure LocalOwner exists
→ onboarding readiness
→ configure model / add material / define goal
→ learning
```

不得出现：

```text
register → login → save recovery kit → onboarding
```

如果 LocalOwner 尚不存在，系统必须在本地原子初始化；这不是注册流程，也不要求联网。

## 9. API and WebSocket Delta

- business API 不再要求 `Authorization: Bearer ...`；
- frontend 不再保存 `access_token` / `refresh_token` / auth `user` cache；
- request interceptor 不再附加 token / auth device fingerprint；
- 401 不再触发 refresh / redirect `/login`；
- WebSocket 不再接受 token 作为身份凭证；
- business endpoint 通过 `LocalOwnerContext` 获取唯一 learner subject；
- `/auth/*`、开发自动登录、账号删除 API 必须退役并停止注册。

## 10. Migration Invariants

### 10.1 Existing Single-user Data

若旧数据存储可以唯一确定一个真实 learner subject：

- MUST 无损采用其 stable identity 作为 LocalOwner；
- MUST 保持 documents/goals/dialogs/learning records/DecisionTrace 等归属；
- MUST NOT 因移除 auth 而生成新的空学习者并遗失旧历史。

### 10.2 Ambiguous Legacy Data

若存在多个无法安全归并的真实 learner subject：

- MUST fail closed；
- MUST 报告 `LOCAL_OWNER_AMBIGUOUS` 或等价稳定 migration issue；
- MUST NOT 静默选择、合并或删除其他 subject；
- auth tables 的物理删除必须发生在 owner migration 成功之后。

### 10.3 Compatibility

旧 token、session、password、recovery data 不需要 runtime backward compatibility。

历史 migration 只需保证：

- 学习数据不丢失；
- ownership 不错配；
- auth secret material 最终被删除；
- replay / decision history 不因身份迁移失去引用完整性。

## 11. Supersession

本 Delta 在“账号 / 登录 / 认证 / session / recovery / account deletion”语义上 supersede：

- `docs/archive/design/账号与隐私生命周期设计.md` 中的账号认证部分；
- ADR-0009 中的 Account/AuthSession/Recovery 决策；
- ADR-0107 中的 Account Deletion orchestration；
- `docs/specs/platform/identity-privacy-lifecycle.md` v1.0；
- `docs/archive/specs/vertical-slices/p1-05-account-lifecycle.md` 的当前产品目标。

P1-03 Data Control / Erasure 中与本地数据治理无关账号认证的部分需按后续 Spec Delta 删除；真正的数据导出、owner-safe erasure、recovery safety 继续有效。

## 12. Frozen Decisions

| ID | Decision |
|---|---|
| `LSI-CD-001` | Askora 为 local single-user product；无 Account/Login 产品概念 |
| `LSI-CD-002` | LocalOwner 是唯一 durable local data ownership subject |
| `LSI-CD-003` | Learner identity 与 credential identity 永久分离；当前不需要 credential identity |
| `LSI-CD-004` | 无认证运行必须强制 loopback network boundary |
| `LSI-CD-005` | 认证数据可删除，学习数据 ownership 必须无损迁移 |
| `LSI-CD-006` | Data export/erasure/recovery safety 保留，但去账号化 |
| `LSI-CD-007` | Settings 与 onboarding 不再出现 login/account/session/recovery-kit |
| `LSI-CD-008` | 未来 remote/multi-user 必须通过新 ADR 显式重新引入 authentication |

## 13. Formation Chain

```text
This Canonical Design Delta
→ ADR-0015 Local Single-User Identity Without Authentication
→ IDP v2 Implementation Spec
→ Authentication Removal Vertical Slice / EXEC
→ Code + Migration + Tests
→ Release Evidence
```

在 ADR-0015 与 IDP v2 冻结前，禁止直接通过只删 Login 页面来实现本目标。
