# EXEC-046 — UI-03D Settings Hierarchy, Legacy Cleanup and Release Closure

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Priority: P0/P1 Product Closure  
> Governing: `docs/product/PRODUCT-POSITIONING.md`, ADR-0014, ADR-0015, `UI-IES-*`, `UI-SCREEN-100..110`, `UI-VIS-100..101`, `UI-QUAL-*`, UI-03 Vertical Slice  
> Depends on: `EXEC-045 DONE` + `EXEC-051 DONE`

## Objective

完成 UI-03 最终闭环：把 Settings 从 giant control grid 重构为 hierarchical category navigation + secondary task destinations，保持 **模型/BYOK、本地数据治理、Backup/Export、Recovery Center、诊断与本地运行安全** 的真实语义；证明并清理无使用者的 legacy chat-first UI；执行完整 responsive/accessibility/security/E2E gate 并形成 UI-03 release evidence。

本 EXEC 必须以 EXEC-047～051 已完成的 no-auth LocalOwner baseline 为前提。账号、密码、AuthSession、Recovery Kit、Logout、Delete Account 等旧 SaaS/账号语义已被 PRODUCT-POSITIONING 与 ADR-0015 supersede，**不得作为需要保留的功能或回归目标重新引入**。

## Dependency Gate

- EXEC-045 DONE；
- EXEC-051 DONE，Authentication Removal release evidence PASS；
- EXEC-043/044/045 commits 均已归档并保持 frontend gates 绿色；
- Settings P1-02/P1-03/P1-07 relevant regression tests 绿色；
- 无其他 active EXEC 修改 Settings/App/route finalization files。

未满足返回 `BLOCKED_BY_DEPENDENCY`。

## Required Product Positioning

必须读取 `docs/product/PRODUCT-POSITIONING.md`，至少核对：

- v1 单用户、无注册、无登录、无账号体系、无 AuthSession；
- Local Web Application + LocalOwner + loopback-only；
- 用户自行配置 AI Provider / Model / API Key；
- API Key 仅保存在本机，优先 OS secure credential storage，不进入默认 Backup/diagnostic/log；
- 核心学习数据本地保存；Backup 与 Export 是不同能力；
- 数据删除遵守 Trash → Permanent Delete 两阶段语义，不以“删除账号”包装本地数据删除；
- v1 默认不依赖远程 Analytics / Sentry / PostHog / Mixpanel / Segment；
- Settings 不得恢复任何 Account / Organization / Tenant / multi-device/cloud-sync 产品语义。

如现有 UI/P1 文档仍要求保留账号生命周期能力，必须按 PRODUCT-POSITIONING + ADR-0015 认定为 superseded，或返回 `BLOCKED_BY_SPEC_GAP`；不得执行旧账号要求。

## Required Specs

- `AGENTS.md`
- `docs/product/PRODUCT-POSITIONING.md`
- ADR-0014
- ADR-0015
- `UI-IES-*`
- `UI-IA-*`
- `UI-SCREEN-100..110`
- `UI-VIS-100..101`
- `UI-QUAL-*`
- UI-03 Vertical Slice
- P1-02 model configuration / credential specs（仅保留与 BYOK/本地 secret 仍有效的部分）
- P1-03 data control / backup / export / restore / erasure specs
- P1-07 recovery contract / slice
- Authentication Removal / LocalOwner release contracts

历史 P1-05 Account Lifecycle 仅可作为 superseded/historical migration 参考，不得作为当前 v1 Required behavior。

## Current Reality

在本 EXEC 开始时，EXEC-049/050/051 应已经完成：frontend/backend production path 无 Login/AuthProvider/ProtectedRoute/JWT/AuthSession，Settings 中账号信息、密码、会话、Recovery Kit、Logout、Delete Account 等能力应已删除。

如果实际 main 中仍存在这些 account semantics，应把它们视为 Authentication Removal residue 并删除/阻断，而不是“保持回归”。Settings 当前真正需要重构的是仍有效的本地能力层级，例如：AI/模型、本地数据、Backup/Export/Restore、Recovery Center、隐私、诊断与运行状态。

`Chat.jsx` 仍可能存在旧 chat-first component；当前 canonical routes 主要使用 `TutorWorkspace`。删除必须基于 route/import/static evidence，而非仅凭命名判断。

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
apps/frontend/src/pages/Unavailable.jsx                  # only if route/recovery presentation needs final adjustment
apps/frontend/src/pages/Unavailable.css                  # same restriction
apps/frontend/src/pages/settings/**                      # new category/task components if chosen
apps/frontend/src/components/settings/**                 # new reusable settings components if chosen
apps/frontend/src/test/**Settings**
apps/frontend/src/test/**settings**
apps/frontend/src/test/**Chat**
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/**accessibility**
apps/frontend/src/test/**navigation**
docs/releases/ui-03-interactive-element-system.md       # new
docs/releases/README.md
docs/exec-plans/active/EXEC-046-ui-03d-settings-legacy-release-closure.md
docs/exec-plans/completed/EXEC-046-ui-03d-settings-legacy-release-closure.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
```

若当前仓库测试文件名不同，可修改本 scope 对应 frontend tests。禁止以通配理由修改 backend/domain。

## Forbidden Changes

- 修改 credential storage/secret lifetime/provider probe semantics；
- 修改 backup/restore/export/erasure owner truth；
- 修改 RecoveryAction contract；
- 删除或弱化 destructive confirmation；
- 创建第二套 settings business state；
- 删除 `TutorWorkspace` 或 `/quick/:sessionId`；
- 删除 `Chat.jsx` 前没有静态/route proof；
- 新增 global search/backend；
- 把 UI cleanup 扩大成 backend refactor；
- 恢复 Login / Register / Account / Password / AuthSession / Recovery Kit / Logout / Delete Account；
- 把本地 scoped erasure / permanent delete 改名或建模成 account deletion；
- 新增 Organization / Tenant / cloud sync / multi-device / remote account settings；
- 把远程 Analytics / Telemetry 设为 v1 正常运行必需；
- 将 API Key 写入普通配置文件、Workspace/Project 文件、日志、默认 Backup 或默认诊断包。

## Implementation Tasks

1. 记录 Settings/route/security tests baseline、Authentication Removal release evidence 与 Chat import/route graph。
2. 先写 RED tests：Settings utility placement、category landing、secondary destinations、BYOK/local-data/recovery flow preservation、account-semantics absence、legacy Chat route absence。
3. 建立 Settings categories，只为已有真实 capability 建 route/component；不得创建空占位设置项。
4. 推荐当前 v1 category 至少按真实能力组织为：
   - AI / Models / Provider / API Key；
   - Local Data（Backup / Restore / Export / Trash / Permanent Delete where applicable）；
   - Recovery / Diagnostics；
   - Application / Advanced / System。
   不得创建 Account / Security Account / Sessions / Devices / Cloud 等旧类别。
5. normal runtime status 降低主层级；degraded/action-required 仍可见。
6. 保留 Recovery global indicator + Settings fallback entry。
7. 明确 Backup ≠ Export：UI 不得把两者混成一个“导出/备份”动作；恢复 Backup 后 API Key 仍需重新配置。
8. API Key / provider secret 相关界面继续服从本地 secret 规则，不显示完整 secret，不进入日志/诊断 copy。
9. 对 `Chat.jsx`/`Chat.css` 执行 route/import/static search；无使用者时删除并补防回归 test；仍有合法依赖时记录 retirement blocker，不强删。
10. 清理只服务旧 7-item IA 或旧 account shell 的 dead CSS/组件，但不得大范围视觉重写。
11. 跑全 UI-03 E2E：Today→Learning facets、Library contextual actions、Settings categories、legacy deep links、Welcome/default entry。
12. 完成 1440/1024/768/360、200% zoom、keyboard/focus/live region、contextual touch-equivalent、security regression。
13. 验证 repo/frontend production path 无 account/password/session/recovery-kit/logout/delete-account UI residue；存在时不得宣告 DONE。
14. 运行 full frontend/build/audit/docs/diff gates，形成 UI-03 release report。
15. 全部 AC PASS 后归档 EXEC-046，并将 UI-03 标记 DONE；独立 commit。

## Acceptance Criteria

- `EXEC046-AC-001`：适用的 `UI03-AC-010..016` PASS；任何仍要求 Account Lifecycle 的旧 UI03 条款必须先 reconciliation，不得覆盖 Product Positioning/ADR-0015。
- `EXEC046-AC-002`：Settings landing 以 category navigation 为主，不同复杂 flow 不再同屏全部展开。
- `EXEC046-AC-003`：P1-02 中仍有效的 BYOK credential 完整性/保密性无回归；不存在账号 credential 要求。
- `EXEC046-AC-004`：P1-03 Backup/Export/Restore/scoped erasure truth 与 confirmation 无回归，且 Backup 与 Export 在 UI/语义上明确区分。
- `EXEC046-AC-005`：P1-07 Recovery Center issue/action semantics 无回归。
- `EXEC046-AC-006`：Settings / routes / production frontend 不存在 Login/Account/Password/AuthSession/RecoveryKit/Logout/DeleteAccount 产品语义。
- `EXEC046-AC-007`：API Key 不进入默认 Backup、默认 diagnostics 或日志；恢复后可重新配置。
- `EXEC046-AC-008`：legacy Chat 仅在无使用者证明后删除；compatibility TutorWorkspace 保留。
- `EXEC046-AC-009`：完整 UI-03 route/navigation/accessibility/security E2E PASS。
- `EXEC046-AC-010`：UI Engineering / Contract / Accessibility-Security PASS；Learning Evidence claim unchanged。
- `EXEC046-AC-011`：Settings 不新增官方云、多设备同步、Tenant/Organization、远程 Analytics 必需依赖等 v1 Non-goals。

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

另外必须提供 P1-02/P1-03/P1-07 relevant frontend/integration/security regression evidence、ADR-0015 / no-account regression evidence；若其测试位于 backend，可运行 targeted tests，但不得修改 backend。

禁止要求 P1-05 password/session/recovery-kit/account-deletion flow PASS；这些是 superseded behavior。历史 migration tests 如仍有价值，只能作为 Historical/Optional evidence，不能恢复产品能力。

## Completion Report Format

分别报告：

- Engineering Gate；
- UI Contract Correctness；
- Accessibility/Security；
- PRODUCT-POSITIONING / ADR-0015 reconciliation；
- P1-02/03/07 regression matrix；
- account-semantics absence evidence；
- Backup vs Export / API-key exclusion evidence；
- UI03 applicable AC final matrix；
- legacy Chat proof/decision；
- responsive/zoom/keyboard evidence；
- tests/build/audit/docs；
- commits；
- release report；
- Learning Evidence unchanged；
- remaining SPEC GAP / retirement items。
