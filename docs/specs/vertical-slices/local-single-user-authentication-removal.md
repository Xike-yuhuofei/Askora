# Local Single-User Authentication Removal Vertical Slice

> Status：FROZEN  
> Product Traceability：`CAP-08`；`PD-REQ-0801..0802`；`PD-RULE-008/010/011`  
> Governing：`PRODUCT-DEFINITION.md`、Local Single-User Identity Canonical Design Delta、ADR-0015、`LID-*` v2  
> Historical execution refs：EXEC-047 → EXEC-048 → EXEC-049 → EXEC-050 → EXEC-051；实时状态以 Linear 与 current `main` 为准

## 0. Acceptance Ownership

本 Slice 负责把已冻结的 **no-auth / LocalOwner / loopback local-product** 定义转化为身份、迁移与运行时技术合同。

- no Account/Login/AuthSession/Tenant/RBAC 的 Product Rule 由 `PRODUCT-DEFINITION.md` / Product Positioning 拥有；
- 本文件 Scope / Non-goals 仅是该 migration slice 的 implementation scope，不定义新的 v1 Product Scope；
- `LSI-VS-AC-*` 属于 **Technical / Migration Vertical Slice Acceptance**，不自动成为 `PD-AC-*`；
- 若未来需要重新引入 Account、remote identity、multi-user 或改变 LocalOwner 产品意义，必须先报告 `POSITIONING GAP` / `PRODUCT DEFINITION GAP`；
- Engineering / migration PASS 不自动证明整个 `CAP-08` 已完整 Product Accepted。

## 1. Objective

把历史 production path 从：

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

执行或修复本 Slice 时必须按 current truth 重新确认：

- ADR-0015 仍为 accepted applicable decision；
- `LID-*` v2 仍为 current identity contract；
- 当前数据库 migration heads 可确定；
- current `main` 不存在未归属的身份/认证漂移；
- Linear 中不存在 blocking dependency 或重叠 migration。

历史 EXEC 与 UI migration 顺序仅作为完成证据和设计背景保留，不在本 frozen Slice 维护实时状态。

## 3. Scope

本节只定义 authentication-removal migration slice scope。

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
- 更新 current Spec / CODE_WIKI / inventory；实时 Issue/EXEC 状态回写 Linear / EXEC index。

## 4. Explicit Non-goals

本节只约束本 Slice，不定义 Askora 总体 Product Scope：

- PostgreSQL → SQLite 总体数据库迁移；
- UI 三域/三栏 IA 全量重构；
- 修改 Teaching Policy / Assessment / Learner Model 算法；
- 重命名所有历史 `user_id` 列；
- 引入 LAN/remote/multi-user；
- 增加新的账号、passkey、MFA 或系统账户登录；
- 删除 P1-03 数据导出/erasure/recovery safety；
- 声称学习效果提升。

其中 Account/multi-user 等产品边界同时受 Product Positioning / Product Definition 更高 authority 约束。

## 5. Ownership Invariants

```text
LocalOwner = local data ownership truth
Learner = learning domain subject
LocalOwner != Account
browser/device fingerprint != owner truth
AuthSession != compatibility identity
```

旧 `User` ORM MAY 在 migration compatibility 阶段暂作 projection，但不得再承担 credential/session truth，并必须有明确 retirement path。

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

## 8. Technical / Migration Acceptance Summary

以下 AC 不创建新的 Product Acceptance：

- `LSI-VS-AC-001`：`LID-AC-001..013` 全部通过；
- `LSI-VS-AC-002`：旧单 learner 数据迁移前后 owner-owned canonical records 对齐；
- `LSI-VS-AC-003`：auth routes/services/token/session/recovery production references 为零；
- `LSI-VS-AC-004`：Settings/Onboarding 无 account semantics；
- `LSI-VS-AC-005`：P1-03 export/scoped erasure/recovery center 回归通过；
- `LSI-VS-AC-006`：后续 UI 工作可在无 Auth shell 基线继续执行；
- `LSI-VS-AC-007`：Engineering / Policy-Ownership PASS，Learning Evidence=`NOT_APPLICABLE`。

对应 `CAP-08 / PD-REQ-0801..0802` 的 Product Acceptance 必须按 Product Definition 单独判断。

## 9. Historical Execution Order

```text
EXEC-047 LocalOwner Foundation & Migration
    ↓
EXEC-048 Backend No-Auth + Loopback Cutover
    ↓
EXEC-049 Frontend / Settings / Onboarding De-accounting
    ↓
EXEC-050 Auth Persistence & Configuration Cleanup
    ↓
EXEC-051 Acceptance / Release Closure
```

以上仅保留为历史 implementation decomposition。若未来发生身份回归修复或新 migration，必须从 current Product Definition / ADR / Spec / Linear 重新生成实施任务，不得机械重放历史 EXEC 序列。
