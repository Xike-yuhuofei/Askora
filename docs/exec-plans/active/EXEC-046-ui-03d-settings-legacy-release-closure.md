# EXEC-046 — Settings / Legacy UI Closure

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P1 UI Product Closure  
> Product Traceability: `CAP-08`、`PD-REQ-0801..0804`、`PD-RULE-008/010/011`  
> Governing: `docs/product/PRODUCT-DEFINITION.md`, `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`, `docs/design/experience/INTERACTION-MODEL.md`, `docs/specs/ui/screen-and-navigation-contracts.md`, `docs/specs/ui/design-system.md`, `docs/specs/ui/quality-and-regression.md`, ADR-0015/0018  
> Depends on: **EXEC-073 DONE**

## Objective

完成仍有效的 Settings / Legacy UI 收口：

- Settings 保持 App Utility，不成为 Product Domain；
- 用 hierarchical category navigation 组织当前真实能力；
- 保持 BYOK、本地数据、Backup/Export/Restore、Recovery/Diagnostics 的 owner/security truth；
- 清理已证明无使用者的 chat-first / Account/Auth UI residue；
- 不再承担旧 UI-03 four-facet / Library / Workspace 的全局 release acceptance——这些由 current UI-04 与 `UI-QR-*` 管理。

本 EXEC 是 Settings/Legacy 的 bounded implementation closure，不重新设计 Product Scope 或 Experience Architecture。

## Dependency Gate

- `EXEC-073 DONE`，避免与 UI-04 全前端 responsive/a11y release 修复重叠；
- LocalOwner/no-auth baseline 已在 current `main`；
- 当前 BYOK / Data Control / Recovery contracts 可执行；
- 无其他 active EXEC 修改 Settings/App/router/Sidebar overlap files。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Sources

- `AGENTS.md`
- `docs/product/PRODUCT-DEFINITION.md`
- `docs/product/PRODUCT-POSITIONING.md`
- `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`
- `docs/design/experience/INTERACTION-MODEL.md`
- `docs/specs/ui/screen-and-navigation-contracts.md`（`UI-SET-*`、`UI-NAV-002`）
- `docs/specs/ui/design-system.md`
- `docs/specs/ui/quality-and-regression.md`
- current Model Configuration / LocalSecretStore / Data Control / Recovery / Security specs
- ADR-0015 / ADR-0017 / ADR-0018

历史 UI-03、P1-05 Account Lifecycle、Desktop/Electron UI contract 只作 migration evidence，不是 current behavior source。

## Current Reality

开始前必须读取 current `main`，验证：

- Settings 当前 category / route structure；
- Login/Account/Password/AuthSession/RecoveryKit/Logout/DeleteAccount residue 是否仍可达；
- legacy `Chat.jsx` 是否仍有 route/import/runtime 使用者；
- current BYOK / Data Control / Recovery flows 实际入口；
- 与已完成 UI-04 shell/sidebar 的 overlap。

不得根据本 EXEC 的旧版本描述假设当前代码仍处于历史 UI-03 状态。

## Allowed Files

```text
apps/frontend/src/App.jsx
apps/frontend/src/router.jsx
apps/frontend/src/components/Sidebar.jsx
apps/frontend/src/components/Sidebar.css
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/pages/Chat.jsx                         # delete only after proof
apps/frontend/src/pages/Chat.css                         # delete only after proof
apps/frontend/src/pages/Unavailable.jsx                  # only if utility/recovery presentation needs adjustment
apps/frontend/src/pages/Unavailable.css
apps/frontend/src/pages/settings/**
apps/frontend/src/components/settings/**
apps/frontend/src/test/**Settings**
apps/frontend/src/test/**settings**
apps/frontend/src/test/**Chat**
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/**accessibility**
apps/frontend/src/test/**navigation**
docs/releases/ui-settings-legacy-closure.md             # new bounded release evidence
docs/releases/README.md
docs/exec-plans/active/EXEC-046-ui-03d-settings-legacy-release-closure.md
docs/exec-plans/completed/EXEC-046-ui-03d-settings-legacy-release-closure.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

## Forbidden Changes

- 修改 credential storage / secret lifetime / provider probe semantics；
- 修改 Backup/Restore/Export/Erasure owner truth；
- 修改 RecoveryAction contract；
- 创建第二套 settings business state；
- 恢复 Account/Login/Register/Password/AuthSession/RecoveryKit/Logout/DeleteAccount；
- 新增 Organization/Tenant/cloud-sync/multi-device/remote account；
- 把 API Key 写入普通配置、DOM/web storage、日志、默认 Backup/Export/diagnostics；
- 删除 `TutorWorkspace` / canonical learning path；
- 无使用者证据前删除 compatibility code；
- 借 Settings closure 修改 Learning IA / Teaching Policy / backend schema；
- 重做 UI-04 已验收的 Workspace/Library/Learning surfaces。

## Implementation Tasks

1. 记录 current Settings/routes/legacy UI inventory 与 frontend baseline。
2. 写 RED tests：Utility placement、category navigation、真实 capability destinations、no Account/Auth residue、legacy Chat reachability、security/data-control invariants。
3. Settings landing 只展示当前真实 category；推荐按实际能力组织：
   - AI / Models；
   - Local Data；
   - Recovery / Diagnostics；
   - Application / Advanced（仅真实能力存在时）。
4. 不建立 Account / Sessions / Devices / Cloud 等 category。
5. 正常 runtime status 保持低视觉层级；degraded/action-required state 可提升。
6. 保持 Backup ≠ Export，Restore 后 secret 仍服从 current SecretStore contract。
7. 保留 Recovery current issue/action semantics。
8. 对 `Chat.jsx` / `Chat.css` 做 static import + route + runtime evidence；无使用者才删除，否则记录 retirement blocker。
9. 清理只服务已退役 account/chat-first shell 的 dead CSS/route residue；不做无关视觉重写。
10. 验证 Settings / Recovery 的 keyboard/focus/360/200% zoom/security paths。
11. 运行 gates，形成 bounded release evidence；全部 AC PASS 后归档。

## Acceptance Criteria

- `EXEC046-AC-001`：`UI-SN-AC-001/007/009/010` 与适用 `UI-QR-*` PASS；
- `EXEC046-AC-002`：Settings 是 Utility + hierarchical category navigation，不是 giant control grid；
- `EXEC046-AC-003`：只暴露 Product Definition 当前真实 capability，无 placeholder category；
- `EXEC046-AC-004`：BYOK / secret confidentiality / revision behavior 无回归；
- `EXEC046-AC-005`：Backup/Export/Restore/scoped data operations 语义无回归，Backup ≠ Export；
- `EXEC046-AC-006`：Recovery issue/action semantics 无回归；
- `EXEC046-AC-007`：生产可达 UI 不存在 Account/Login/Password/AuthSession/RecoveryKit/Logout/DeleteAccount 语义；
- `EXEC046-AC-008`：legacy Chat 只在无使用者证明后删除；canonical Learning/Tutor 路径保留；
- `EXEC046-AC-009`：没有重开已被 UI-04 current contracts 收口的 Learning/Library/Workspace 设计；
- `EXEC046-AC-010`：Product Acceptance / UX / Engineering / Security / Learning Evidence 分开报告。

## Required Tests

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

至少提供：Settings category matrix、legacy route/import evidence、BYOK/data/recovery regression、360/200% zoom、keyboard/focus、安全证据。

## Completion Report Format

报告：base/final commit、Settings category before/after、legacy cleanup proof、security/data-control evidence、tests/build/audit/docs/diff、AC matrix、remaining blockers。