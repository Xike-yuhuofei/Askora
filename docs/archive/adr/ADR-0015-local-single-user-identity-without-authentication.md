# ADR-0015 — Local Single-User Identity Without Authentication

Status: accepted  
Date: 2026-08-10  
Decision owners: user  
Decision authority: explicit user confirmation  
Affected specs: `docs/specs/platform/identity-privacy-lifecycle.md`, `docs/archive/specs/vertical-slices/p1-05-account-lifecycle.md`, UI Settings/Onboarding/API contracts

## Context

Askora 已明确收敛为本地单机、个人长期学习 App。当前实现仍保留完整账号系统：Login/Register、JWT access/refresh token、durable AuthSession、设备指纹、password/recovery kit、account deletion lifecycle，以及大量 `get_current_user` 依赖。

这些机制主要解决多用户、远程访问、跨设备 session 与账号恢复问题。对单机单用户产品而言，它们引入了额外状态、错误路径、安全配置、迁移负担和 UI 复杂度，却没有提供与当前产品目标相匹配的用户价值。

但学习数据仍需要稳定 ownership subject，因此“移除认证”不能等于“删除 learner identity”。

## Decision

### 1. Product identity

Askora 不再提供 Account/Login/Register/Logout/Password/Recovery/AuthSession 产品能力。

唯一长期身份改为：

```text
LocalOwnerContext
└── owner_id: UUID
```

`LocalOwner` 是本地数据归属主体，不是 credential principal。

### 2. Runtime resolution

所有原本使用 `get_current_user` 的业务入口改为解析唯一 `LocalOwnerContext`。

不再通过 Bearer token、session、device fingerprint 或 browser storage 证明身份。

### 3. Security boundary

无认证 profile MUST 只允许本机 loopback 访问：

- backend bind 仅 `127.0.0.1` / `::1`；
- CORS / WebSocket origin 仅允许明确 loopback origins；
- 非 loopback host 配置 MUST fail startup；
- remote/LAN/multi-user service mode 与本 ADR 不兼容。

未来若要支持远程访问，必须由新的 Canonical Design + ADR 重新引入 authentication。

### 4. Authentication state retirement

以下 runtime truth 退役：

- password/hash/credential version；
- JWT configuration and token families；
- AuthSession；
- recovery credential / throttle；
- auth-only identity command receipt；
- login timestamp / auth role/status；
- account deletion lifecycle and deletion-control token。

物理 schema cleanup 必须晚于 learner ownership migration。

### 5. Learner ownership preservation

现有 documents/goals/dialogs/learning state/assessment/planning/DecisionTrace 等 owner references必须保留语义完整性。

历史 `user_id` 或 `pseudonym_id` MAY 暂作为 compatibility storage key，但不得继续表示认证账号。

### 6. Data control

保留数据导出、局部数据删除、owner-safe erasure、错误恢复与必要的 no-resurrection safety。

“删除账号”改为本地数据删除/工作区重置语义；危险操作继续需要 preview + typed confirmation，但不进行 password re-auth。

### 7. UI

删除 Login、ProtectedRoute、账号安全、密码、会话、恢复套件、退出登录、删除账号等 UI。

Settings 只保留本地数据、AI/模型、存储/运行状态、恢复中心、隐私和关于等单机工具。

## Alternatives Considered

### A. 保留账号系统但自动登录

未采用。它仍保留 JWT/session/password/recovery/account state，只是隐藏 Login UI；复杂度和失败路径没有真正消失。

### B. 固定一个硬编码 demo user

未采用。硬编码身份会污染数据迁移、测试、导出和 owner-safe erasure，也容易形成隐式第二 truth。

### C. 完全删除所有 user/owner 标识

未采用。学习历史、资料、目标、对话和 DecisionTrace 仍需要稳定数据归属；没有 owner subject 会破坏领域完整性和未来迁移。

### D. LocalOwner + loopback-only

采用。它保留最小必要 identity truth，同时删除认证复杂度，并把安全边界与真实单机部署模型对齐。

## Consequences

### Positive

- 启动直接进入本地工作区；
- 删除 login/token/session/recovery 失败路径；
- Settings 与 onboarding 显著简化；
- 减少安全 secret、配置、测试和 migration surface；
- learner ownership 与 authentication 解耦；
- 与本地单用户产品边界一致。

### Negative / Constraints

- 当前无认证 profile 不能安全暴露给 LAN/公网；
- 旧账号相关 feature/test/contract 将成为历史实现，需要系统性退役；
- 旧数据库必须先完成 owner migration，再删除 auth schema；
- 多真实用户 legacy 数据不能自动猜测归并。

## State Ownership and Duplicate Truth

- `LocalOwner` 是唯一 local ownership identity truth；
- LearnerProfile 不拥有 credential truth；
- browser localStorage、device fingerprint、AuthSession 不得充当 owner truth；
- compatibility `user_id/pseudonym_id` 只能投影到同一个 LocalOwner，不得产生第二 canonical identity。

## Migration / Rollback

### Forward migration

1. 建立/解析 LocalOwner；
2. 将唯一旧 learner subject 映射为 LocalOwner；
3. 验证所有 owner references 和 replay integrity；
4. 切换 API/WS/Frontend 到 LocalOwnerContext；
5. 删除 auth routes/runtime/config；
6. 删除 auth-only tables/columns；
7. 更新 Settings/Onboarding；
8. 运行 migration + E2E gates。

若 legacy 数据存在多个无法安全判断的真实 subject，migration MUST fail closed，禁止静默合并。

### Rollback

一旦 auth secret/schema 被物理删除，不提供 runtime rollback 到旧登录系统。需要恢复认证时采用新的 forward design/ADR/migration，而不是重新启用旧代码。

## Security / Privacy / Replay / Idempotency

- 无认证模式必须 fail closed 到 loopback；
- destructive data commands 仍需幂等键、preview、typed confirmation 与 durable receipt；
- migration 不得记录旧 password/token/recovery secret；
- DecisionTrace / historical replay 的 owner reference 必须保持稳定；
- auth state 删除不能改变教学决策结果或学习证据语义。

## Validation

至少需要：

1. frontend 无 `/login`、ProtectedRoute、auth token storage；
2. backend 不注册 `/auth/*`、account deletion、dev auto-login；
3. 所有主要业务 API 在无 Authorization header 下工作；
4. backend 非 loopback host 启动失败；
5. WebSocket 无 token 仍可在合法 local origin 工作；
6. 旧单用户数据库迁移后资料、目标、对话、进度、DecisionTrace 数量与 ownership 对齐；
7. 多真实 legacy subject fixture fail closed；
8. data export / scoped erasure / recovery center 继续工作；
9. 全量测试不再依赖 auth fixture；
10. Engineering / Policy-Ownership gate PASS；Learning Evidence 声明不因本 ADR改变。

## Supersedes / Superseded By

本 ADR 在 Account/AuthSession/Recovery/Account Deletion 产品语义上 supersede：

- ADR-0009 `Local-first Identity and Privacy Lifecycle` 的认证部分；
- ADR-0107 `Account Deletion Uses the Canonical Data Erasure Workflow` 的账号 orchestration 部分。

ADR-0009/0107 中与 owner-safe data erasure、privacy/no-resurrection 仍有独立价值的原则，由 IDP v2 重新吸收后继续有效。
