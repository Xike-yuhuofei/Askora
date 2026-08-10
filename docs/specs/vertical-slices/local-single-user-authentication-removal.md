# Local Single-User Authentication Removal Vertical Slice

> Status：FROZEN  
> Governing：Local Single-User Identity Canonical Design Delta、ADR-0015、`LID-*` v2  
> Execution：EXEC-047 → EXEC-048 → EXEC-049 → EXEC-050 → EXEC-051

## 1. Objective

把当前 production path 从：

```text
Frontend Auth Shell
→ JWT/AuthSession
→ get_current_user
→ User
→ learner-owned services
```

完整迁移为：

```text
Local bootstrap
→ LocalOwnerContext
→ learner-owned services
```

并在不丢失历史学习数据、不破坏 DecisionTrace/replay、不删除 P1-03 有效数据治理能力的前提下，物理退役认证子系统。

## 2. Dependency Gate

必须满足：

- ADR-0015 accepted；
- `LID-*` v2 FROZEN；
- EXEC-1062 DONE，因为它与本 slice 在 App/Settings/onboarding/routes 有文件重叠；
- 当前数据库 migration heads 可确定；
- 工作树无未归属的身份/认证改动。

本 slice 完成前，UI-03 EXEC-043～046 MUST NOT 开始；否则 shell/routes/Settings 会形成双重迁移。

## 3. Scope

### Phase A — LocalOwner Foundation

- inventory 现有 learner subjects / owner references；
- 建立 durable LocalOwner truth；
- 旧单 learner identity 无损映射；
- ambiguous legacy subject fail closed；
- 建立 `get_local_owner_context()`；
- 暂不删除 auth runtime/schema。

### Phase B — Backend No-Auth Cutover

- learner-owned HTTP APIs 切换 LocalOwnerContext；
- WebSocket 切换 local-origin/LocalOwner；
- 停止注册 auth/dev-auth/account-deletion routes；
- 删除 JWT/session runtime dependency；
- 强制 loopback-only host/origin boundary；
- 保持 data-control/recovery center 正常。

### Phase C — Frontend De-accounting

- 删除 Login / ProtectedRoute / AuthProvider / auth hooks；
- 删除 token/device-fingerprint auth storage/interceptors；
- App 直接进入 local bootstrap/product route；
- Settings 删除账号/密码/session/recovery-kit/logout/delete-account；
- Onboarding 不再依赖认证；
- 数据导出、局部删除、恢复中心继续可用。

### Phase D — Persistence Cleanup

- 删除 auth-only tables/columns/config/secrets；
- 保留必要 owner key compatibility，避免一次性大规模 FK churn；
- 删除 account deletion runtime/schema 中仅服务账号生命周期的部分；
- owner-safe erasure/no-resurrection 仍由 P1-03 当前合同承接；
- migration on existing single-user database 可重复、可验证。

### Phase E — Release Closure

- 删除 auth-only tests/fixtures/docs residue；
- 增加 no-auth / loopback / migration / ownership gates；
- full frontend/backend quality gates；
- release evidence；
- 更新 EXEC / Spec / CODE_WIKI / inventory 状态。

## 4. Explicit Non-goals

本 slice 不负责：

- PostgreSQL → SQLite 总体数据库迁移；
- UI-03 三域 IA 全量重构；
- 修改 Teaching Policy / Assessment / Learner Model 算法；
- 重命名所有历史 `user_id` 列；
- 引入 LAN/remote/multi-user；
- 增加新的账号、passkey、MFA 或系统账户登录；
- 删除 P1-03 数据导出/erasure/recovery safety；
- 声称学习效果提升。

## 5. Ownership Invariants

```text
LocalOwner = local data ownership truth
Learner = learning domain subject
LocalOwner != Account
browser/device fingerprint != owner truth
AuthSession != compatibility identity
```

旧 `User` ORM MAY 在 Phase A/B 暂作 compatibility projection，但不得再承担 credential/session truth，并必须在 Phase D 收敛。

## 6. Migration Invariants

- auth schema cleanup 必须晚于 owner mapping；
- single real learner 数据数量和引用保持；
- multiple ambiguous real subjects fail closed；
- migration 不输出旧 secret；
- DecisionTrace/event/replay owner refs 不失效；
- data deletion receipts/checkpoints 不因账号退役失去可解释性。

## 7. Network Invariant

No-auth runtime 与非 loopback 网络暴露互斥。

验收必须证明：

```text
127.0.0.1 / ::1 → allowed
0.0.0.0 / LAN / public IP → startup failure
```

仅做 CORS 限制而仍监听所有接口不算通过。

## 8. Acceptance Summary

- `LSI-VS-AC-001`：`LID-AC-001..013` 全部通过；
- `LSI-VS-AC-002`：旧单 learner 数据迁移前后 owner-owned canonical records 对齐；
- `LSI-VS-AC-003`：auth routes/services/token/session/recovery production references 为零；
- `LSI-VS-AC-004`：Settings/Onboarding 无 account semantics；
- `LSI-VS-AC-005`：P1-03 export/scoped erasure/recovery center 回归通过；
- `LSI-VS-AC-006`：UI-03 后续可在无 Auth shell 基线继续执行；
- `LSI-VS-AC-007`：Engineering / Policy-Ownership PASS，Learning Evidence=`NOT_APPLICABLE`。

## 9. Execution Order

```text
EXEC-1062 DONE
    ↓
EXEC-047 LocalOwner Foundation & Migration
    ↓
EXEC-048 Backend No-Auth + Loopback Cutover
    ↓
EXEC-049 Frontend / Settings / Onboarding De-accounting
    ↓
EXEC-050 Auth Persistence & Configuration Cleanup
    ↓
EXEC-051 Acceptance / Release Closure
    ↓
EXEC-043 → EXEC-044 → EXEC-045 → EXEC-046
```

不得并行执行 EXEC-047～051。
