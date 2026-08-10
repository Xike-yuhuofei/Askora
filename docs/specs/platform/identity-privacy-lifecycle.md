# Askora Local Identity and Privacy Lifecycle Specification

> Spec ID：`LID-*`  
> 状态：FROZEN  
> 版本：v2.0  
> Governing decision：ADR-0015  
> Supersedes：本文件 v1.0 `IDP-*` account/authentication contract

## 1. Scope

### LID-001 — Product Boundary

Askora 当前是 local single-user product。

Runtime MUST NOT require：

- login / register / logout；
- password / password recovery；
- JWT access/refresh token；
- AuthSession / token family；
- authentication device fingerprint；
- recovery credential / recovery kit；
- account deletion lifecycle。

Identity & Privacy 仍是平台横切边界，不是第九学习系统。

### LID-002 — Canonical Identity Truth

唯一 durable local identity truth 是：

```yaml
local_owner:
  owner_id: uuid
  schema_version: "1.0"
  created_at: datetime
```

`owner_id` 表示本地数据归属主体，不表示 credential principal。

### LID-003 — Learner Boundary

Learner/Profile/learning state MAY 使用 `owner_id` 作为 canonical subject key。

nickname、presentation preference、学习偏好属于 LearnerProfile / Settings，不属于 LocalOwner。

`LocalOwner` MUST NOT 保存 phone、email、password、token、recovery secret、wechat id、device fingerprint 等认证材料。

## 2. LocalOwner Lifecycle

### LID-010 — Bootstrap

App 启动 MUST 在任何 learner-owned query/command 前完成：

```text
load LocalOwner
OR
atomically create LocalOwner
→ expose LocalOwnerContext
```

首次创建不是 registration，不要求联网，不产生 token/session。

### LID-011 — Cardinality

一个 canonical local data store MUST 最多存在一个 active LocalOwner。

新空数据存储不存在 owner 时 MAY 原子创建一个 UUID。

### LID-012 — Stability

LocalOwner `owner_id` 在正常使用、App 重启、版本升级和普通数据导出期间 MUST 稳定。

browser fingerprint、machine id、process id、frontend storage key MUST NOT 替代 `owner_id`。

### LID-013 — Runtime Dependency

Canonical dependency：

```text
get_local_owner_context()
→ LocalOwnerContext(owner_id)
```

所有原 `get_current_user` business dependencies MUST 迁移到 LocalOwnerContext 或由它生成的 learner context。

兼容层 MAY 临时返回旧 `User` ORM projection，但：

- 不得验证 token；
- 不得创建 auth session；
- projection 必须唯一映射到同一个 LocalOwner；
- compatibility layer 必须有明确退役点。

## 3. Network Security Boundary

### LID-020 — Loopback Only

无认证 runtime MUST 只监听 loopback：

```text
127.0.0.1
::1
localhost-resolved loopback
```

`0.0.0.0`、LAN address、public interface MUST fail startup。

### LID-021 — Frontend Origins

CORS MUST explicit allowlist local frontend origins only。

不得因 single-user 模式使用 `*`。

### LID-022 — WebSocket Boundary

WebSocket MUST 使用与 HTTP 相同的 loopback/origin trust boundary，不得要求或接受 auth token 作为 owner identity。

### LID-023 — Remote Mode Prohibited

当前 no-auth profile MUST NOT 被宣称支持：

- LAN sharing；
- remote browser access；
- multi-device service；
- multi-user deployment。

未来新增上述能力 MUST 先通过新的 Canonical Design + ADR 重新定义 authentication。

## 4. Frontend Contract

### LID-030 — No Auth Shell

Frontend MUST 删除：

- `/login`；
- Login/Register/Recover UI；
- ProtectedRoute；
- AuthProvider / auth-only hooks；
- auth redirect；
- logout action。

App root MUST 直接进入 local bootstrap / product routing。

### LID-031 — No Token Storage

Frontend MUST NOT 持久化：

```text
access_token
refresh_token
auth session
current authenticated user cache
auth device fingerprint
```

普通非认证 UI preference 不受本条限制。

### LID-032 — API Client

Request interceptor MUST NOT 附加 `Authorization: Bearer ...`。

Response interceptor MUST NOT：

- refresh token；
- retry using rotated token；
- clear auth storage；
- redirect `/login`。

401 不再属于“session expired”产品语义。

## 5. Backend Contract

### LID-040 — Retired Routes

Production application MUST NOT register：

```text
/auth/*
account-login/recovery/session routes
dev auto-login
account deletion lifecycle routes
```

旧路径 MAY 返回 normal 404；不得保留隐藏自动登录 compatibility service。

### LID-041 — Retired Runtime Services

以下服务不得存在于 production request path：

- AuthService；
- TokenService；
- password verifier/hasher solely for account auth；
- auth session repository；
- recovery credential service；
- auth throttle service；
- account deletion runtime。

### LID-042 — Retired Configuration

认证退役后 production config MUST 删除或停止要求：

- JWT secret/algorithm/expiry；
- auth session timeout；
- dev auto-login flag；
- account deletion grace/polling config；
- auth-only secret validation。

### LID-043 — Business APIs

Documents、Goals、Workspace、Dialog、Onboarding、Data Control、Profile、Assessment/Planning 等 learner-owned APIs MUST 在无 Authorization header 下工作，并通过 LocalOwnerContext 确定唯一 subject。

## 6. Persistence and Migration

### LID-050 — Migration Order

认证移除 migration MUST 严格遵循：

```text
1. inventory existing learner subjects
2. resolve one LocalOwner
3. verify owner reference integrity
4. cut runtime to LocalOwnerContext
5. remove auth runtime/routes/config
6. remove auth-only schema/columns
7. validate replay/data-control integrity
```

MUST NOT 先 drop auth/user tables 再尝试恢复 ownership。

### LID-051 — Unique Legacy Subject

若 legacy datastore 可以唯一确定一个真实 learner subject：

- MUST 复用其稳定 UUID；或使用有记录、确定性的 canonical mapping；
- MUST 保留 documents/goals/dialogs/profiles/learning records/DecisionTrace ownership；
- MUST NOT 创建新的空 learner 取代旧数据。

### LID-052 — Ambiguous Legacy Subject

若存在多个无法安全区分/合并的真实 learner subjects：

- migration MUST fail closed；
- stable issue code：`LOCAL_OWNER_AMBIGUOUS`；
- MUST NOT 依据“最后登录”“最大数据量”或随机顺序静默选择；
- MUST NOT 删除未解析 subject 数据。

测试/demo fixture 可通过明确 fixture metadata 排除，不能靠名字猜测。

### LID-053 — Compatibility Columns

历史列名 `user_id` / `pseudonym_id` MAY 暂时保留以降低一次性 schema 风险，但它们的 canonical semantics MUST 是 LocalOwner/Learner ownership。

新实现不得再次引入 Account credential semantics。

### LID-054 — Auth Secret Erasure

LocalOwner migration 成功后，以下数据 SHOULD 被物理删除：

- password hashes；
- phone/email/wechat auth identifiers；
- access/refresh/session state；
- recovery secret digests；
- auth throttle state；
- authentication command receipts；
- account lifecycle-only state。

日志和 migration report MUST NOT 输出 secret material。

## 7. Data Control and Privacy

### LID-060 — Preserve Useful Data Governance

认证退役 MUST NOT 删除：

- user-readable/local data export；
- document erasure；
- learning-record erasure；
- model-execution erasure；
- owner-safe erasure workflow；
- recovery center；
- durable receipt/checkpoint/no-resurrection safety where applicable。

### LID-061 — No Account Deletion

产品/API MUST 不再使用 `DeleteAccount` 语义。

如果提供全量本地清除，canonical command 应是 `ResetLocalWorkspace` 或等价明确本地数据语义。

### LID-062 — Destructive Confirmation

危险数据删除仍 MUST：

1. 读取真实影响 preview；
2. 使用短时/版本化 preview；
3. 要求精确 typed confirmation；
4. 使用 idempotency key；
5. durable report/receipt；
6. fail closed on partial failure。

不得要求 current password，因为不存在 credential identity。

### LID-063 — Owner Preservation During Partial Erasure

普通 scoped erasure MUST 保留 LocalOwner identity，以保证剩余数据仍有稳定归属。

完整 workspace reset 若选择 rotate owner_id，必须在旧 owner 全量 erasure + no-resurrection checkpoint 完成之后创建新 owner，禁止两个 canonical owner 并存。

## 8. Settings and Onboarding

### LID-070 — Settings

Settings MUST 删除：

- 账号信息/状态；
- 手机号；
- 修改密码；
- session/device management；
- recovery kit；
- logout；
- delete account；
- JWT/session 安全说明。

Settings SHOULD 组织为：AI/模型、本地数据、存储与运行状态、错误恢复中心、隐私、关于。

### LID-071 — Onboarding

First-use journey：

```text
LocalOwner bootstrap
→ readiness
→ model/material/goal
→ first learning activity
```

不得依赖 register/login/recovery kit。

## 9. Error Contract

### LID-080 — Stable Local Identity Errors

至少冻结：

```text
LOCAL_OWNER_MISSING
LOCAL_OWNER_AMBIGUOUS
LOCAL_OWNER_MIGRATION_FAILED
LOCAL_NETWORK_BOUNDARY_VIOLATION
LOCAL_DATA_RESET_PARTIAL
```

正常新空 datastore 的 `LOCAL_OWNER_MISSING` 应由 bootstrap 原子创建解决，不应成为普通用户错误页。

## 10. Observability and Privacy

### LID-090

日志 MAY 记录最小必要 owner UUID/request id/operation id，但不得重新引入 phone/email/device fingerprint/token 等认证遥测。

### LID-091

移除 authentication 不得改变：

- TeachingAction；
- DecisionTrace policy inputs；
- learner mastery semantics；
- OutcomeObservation；
- experiment assignment；
- learning evidence hierarchy。

身份迁移只改变 ownership resolution，不改变教学决策 truth。

## 11. Acceptance Criteria

- `LID-AC-001`：冷启动无 Login，直接进入 local bootstrap/product flow。
- `LID-AC-002`：frontend bundle/runtime 不读写 access/refresh token。
- `LID-AC-003`：主要 learner-owned API 无 Authorization header 全部正常。
- `LID-AC-004`：`/auth/*`、dev auto-login、account deletion routes 未注册。
- `LID-AC-005`：backend 配置为 `0.0.0.0` 或非 loopback 地址时 startup fail closed。
- `LID-AC-006`：WebSocket 在合法 local origin 无 token 工作；非法 origin 被拒绝。
- `LID-AC-007`：legacy 单 learner migration 后关键 owner-owned records 数量/引用保持一致。
- `LID-AC-008`：multiple-real-subject fixture 返回 `LOCAL_OWNER_AMBIGUOUS` 且不执行 destructive cleanup。
- `LID-AC-009`：auth-only secret/session/recovery persistence 被删除或确认无 production references。
- `LID-AC-010`：Settings 无账号/密码/session/recovery/delete-account UI。
- `LID-AC-011`：data export、scoped erasure、Recovery Center 回归通过。
- `LID-AC-012`：DecisionTrace/replay/learning evidence 回归无语义变化。
- `LID-AC-013`：frontend test/build、backend pytest/ruff/mypy、migration tests、browser E2E 全部通过。

## 12. Release Gate

不得以以下方式声明完成：

- 只隐藏 Login 页面；
- 保留 AuthProvider 自动注入 demo token；
- 保留 JWT/session 但称为“本地身份”；
- 硬编码固定 demo user；
- 删除 `user_id` 导致历史学习数据脱离 owner；
- backend 可从 LAN/public interface 访问；
- 删除 data export/erasure/recovery safety 以简化实现。

Engineering 与 Policy/Ownership gate 必须 PASS。Learning Evidence 对本变更为 `NOT_APPLICABLE`；不得借本变更提高学习效果声明。
