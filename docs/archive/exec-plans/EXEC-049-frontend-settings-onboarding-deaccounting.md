# EXEC-049 — Frontend / Settings / Onboarding De-accounting

> Status：**DONE**（2026-08-10）  
> Governing：ADR-0015、`LID-*`、ADR-0014（仅保持既有 IA 边界，不实施完整 UI-03）  
> Dependency：EXEC-048 DONE  
> Next：EXEC-050

## Objective

彻底删除 frontend authentication shell 和账号产品语义，让 Askora 启动后直接进入 local product flow，同时保留 Settings 中真正属于本地数据治理与恢复的能力。

## Dependencies

- EXEC-048 DONE；
- backend no-auth APIs / WebSocket 已可用；
- EXEC-1062 已完成并形成可修改 baseline；
- UI-03 EXEC-043～046 尚未开始。

## Required Specs

- `LID-030..032`
- `LID-070..071`
- ADR-0014 UI-IA/UI-SCREEN 当前 contracts
- onboarding / data-control / recovery contracts

## Current Reality

- App 存在 AuthProvider / ProtectedRoute / `/login`；
- API client 保存 token、refresh、device fingerprint 并处理 401 refresh；
- Settings 含账号信息、密码、会话、恢复套件、logout、delete-account；
- data export、scoped erasure、Recovery Center 与账号 UI 混在同页。

## Allowed Files

```text
apps/frontend/src/App.jsx
apps/frontend/src/router/**
apps/frontend/src/api/**
apps/frontend/src/context/**
apps/frontend/src/hooks/**
apps/frontend/src/pages/Login*
apps/frontend/src/pages/Settings*
apps/frontend/src/pages/Welcome*
apps/frontend/src/components/**auth*
apps/frontend/src/test/**
apps/frontend/package.json
docs/specs/ui/**
docs/planning/**
```

若真实文件名不同，只允许删除/修改 authentication、Settings、onboarding、routing 直接依赖。

## Forbidden Changes

- 不实施完整 UI-03 Today/Library/Learning redesign；
- 不改 backend schema；
- 不删除 data export/scoped erasure/Recovery Center；
- 不保留 hidden auto-login；
- 不把固定 token/demo user 写入 localStorage；
- 不新增 account/security 页面替代 Login。

## Implementation Tasks

1. 删除 `/login`、Login/Register/Recover 页面与 route；
2. 删除 ProtectedRoute、AuthProvider、auth-only hooks/context；
3. App root 直接进入 local bootstrap / canonical default route；
4. API client 删除 access/refresh token、Authorization header、refresh retry、auth device fingerprint、401→login redirect；
5. 删除 frontend auth API modules 与 dead imports；
6. Settings 删除账号信息、手机号、密码、session/device、recovery kit、logout、delete-account；
7. Settings 保留并明确：AI/模型、本地数据导出、局部永久删除、运行状态、Recovery Center、隐私；
8. nickname 若保留，改为 learner/profile personalization，不标“账号”；
9. onboarding/default-entry 不再检查认证状态；
10. 更新 route/security/accessibility tests，保持 ADR-0014 三域 IA，不提前实施 UI-03 全量视觉重构。

## Acceptance Criteria

- `E049-AC-001`：冷启动不会渲染或 redirect Login；
- `E049-AC-002`：frontend source/runtime 无 access_token/refresh_token auth flow；
- `E049-AC-003`：无 ProtectedRoute/AuthProvider production dependency；
- `E049-AC-004`：Settings 无账号/密码/session/recovery-kit/logout/delete-account 文案与操作；
- `E049-AC-005`：数据导出、scoped erasure、Recovery Center 仍可完成；
- `E049-AC-006`：Welcome/onboarding 可无 auth 进入并结束到 canonical route；
- `E049-AC-007`：360px、keyboard、200% zoom、focus/status/error 基线不退化；
- `E049-AC-008`：不恢复旧七项 L0 IA，不提前实施 UI-03。

## Required Tests

- App route tests；
- no-login cold-start test；
- API client no-token test；
- Settings tests；
- onboarding tests；
- data-control/recovery UI regression；
- `npm test`；
- `npm run build`。

## Completion Report Format

必须报告：deleted auth UI/modules、Settings preserved capabilities、route behavior、tests/build、remaining frontend auth references、commit SHA、`E049 DONE` 或 blocker。
