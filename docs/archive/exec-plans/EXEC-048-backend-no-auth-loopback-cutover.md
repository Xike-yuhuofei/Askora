# EXEC-048 — Backend No-Auth & Loopback Cutover

> Status：**DONE**（2026-08-10）  
> Governing：ADR-0015、`LID-*`、Authentication Removal Vertical Slice  
> Dependency：EXEC-047 DONE（satisfied 2026-08-10）  
> Next：EXEC-049

## Objective

把 production backend 从 Bearer Token/AuthSession/current-user 解析切换到 LocalOwnerContext，并同时冻结 no-auth 所必须的 loopback-only 网络安全边界。

## Dependencies

- EXEC-047 DONE；
- LocalOwner bootstrap/migration tests PASS；
- 当前 branch 无 frontend/UI 混合改动。

## Required Specs

- ADR-0015
- `LID-020..043`
- API / WebSocket / Error / Data Control contracts
- Authentication Removal Vertical Slice

## Current Reality

- 多个 API 通过 `Depends(get_current_user)`；
- WebSocket 需要 token；
- `app.main` 注册 auth/account/recovery/dev-auth routes；
- API client/backend 仍存在 JWT/session runtime；
- 当前默认 host 已是 `127.0.0.1`，但尚未把非 loopback 配置定义为 startup violation。

## Allowed Files

```text
apps/backend/app/api/v1/**
apps/backend/app/main.py
apps/backend/app/core/config.py
apps/backend/app/core/exceptions.py
apps/backend/app/services/auth/**
apps/backend/app/services/websocket/**
apps/backend/app/gateway/**
apps/backend/tests/contracts/**
apps/backend/tests/integration/**
apps/backend/tests/security/**
apps/backend/tests/unit/**
docs/planning/**
```

只允许与 owner resolution/auth runtime/network boundary 直接相关的改动。

## Forbidden Changes

- 不 drop auth tables/columns（留给 EXEC-050）；
- 不修改 frontend；
- 不重构 UI-03；
- 不扩大 host 到 LAN；
- 不用 CORS 代替 bind-address fail closed；
- 不用硬编码 demo user 代替 LocalOwner。

## Implementation Tasks

1. 将 learner-owned endpoints 的 `get_current_user` 切换为 LocalOwnerContext/compat learner projection；
2. 确保 Documents/Goals/Workspace/Dialog/Onboarding/Data Control/Profile 等无 Authorization header 正常；
3. WebSocket 移除 token identity，使用 local origin + LocalOwner；
4. `app.main` 停止注册 auth、dev-auth、account deletion auth routes；
5. auth/session service 不得再位于 production request path；
6. startup validator 强制 host 仅 loopback；
7. CORS/WebSocket allowlist 仅明确 loopback origins；
8. 停止 JWT key runtime health requirement；
9. 为旧 auth paths 固定 normal 404 行为；
10. 保证 data export/scoped erasure/recovery center API 不因 auth removal 失效。

## Acceptance Criteria

- `E048-AC-001`：production API code 无 `Depends(get_current_user)`；
- `E048-AC-002`：主要 learner-owned API 无 Authorization header PASS；
- `E048-AC-003`：`/auth/*`、dev auto-login、account auth/deletion routes 未注册；
- `E048-AC-004`：合法 local WebSocket 无 token 可连接；
- `E048-AC-005`：非法 origin WebSocket 拒绝；
- `E048-AC-006`：host=`0.0.0.0`、LAN/public address startup fail closed=`LOCAL_NETWORK_BOUNDARY_VIOLATION` 或等价稳定错误；
- `E048-AC-007`：仅 loopback origins 生效；
- `E048-AC-008`：P1-03/P1-07 backend regression PASS；
- `E048-AC-009`：TeachingAction/DecisionTrace 输出不因 cutover 改变。

## Required Tests

- API integration no-auth tests；
- WebSocket origin/no-token tests；
- config/startup loopback boundary tests；
- auth-route absence tests；
- data-control/recovery regression；
- backend pytest targeted + ruff + mypy。

## Completion Report Format

必须报告：cutover endpoints、remaining auth code（仅 dormant/persistence）、network-boundary evidence、tests、commit SHA、`E048 DONE` 或 blocker。
