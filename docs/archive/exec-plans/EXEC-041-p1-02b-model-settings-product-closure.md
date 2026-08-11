# EXEC-041 — P1-02B Model Settings Product Closure

> Status：DONE
> Priority：P1 Product Reliability
> Governing：ADR-0013、`MODEL-CONFIG-*`、P1-02 Vertical Slice

## Objective

在 EXEC-040 安全基础之上完成 Settings 产品体验、真实 macOS App/provider/relaunch 验收、release evidence 与 P1-02 gap closure。

## Dependency Gate

EXEC-040 已归档，所有 foundation AC PASS，并形成独立集成提交 `d59837d`。

## Allowed Files

```text
docs/archive/audits/product-gap-register-p1-p2.md
docs/governance/document-inventory.md
docs/specs/README.md
docs/archive/design/p1-02-model-settings.md
docs/architecture/decisions/ADR-0012-desktop-model-credential-and-activation.md
docs/specs/systems/08-model-configuration.md
docs/specs/interfaces/api-contract.md
docs/specs/ui/README.md
docs/archive/specs/ui/screen-contracts.md
docs/specs/frontend/ui-read-model-contracts.md
docs/archive/specs/ui/quality-and-migration.md
docs/archive/specs/vertical-slices/p1-02-model-settings.md
docs/planning/README.md
docs/planning/execs/EXEC-041-p1-02b-model-settings-product-closure.md
docs/archive/exec-plans/EXEC-041-p1-02b-model-settings-product-closure.md
docs/archive/exec-plans/README.md
docs/archive/releases/p1-02-model-settings.md
docs/archive/releases/README.md
apps/backend/app/main.py
apps/backend/tests/contracts/test_model_configuration_contract.py
apps/backend/tests/security/test_model_configuration_security.py
apps/frontend/src/api/users.js
apps/frontend/src/App.jsx
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/Settings.test.jsx
apps/frontend/src/test/ModelSettingsSecurity.test.jsx
apps/frontend/electron/main.cjs
apps/frontend/electron/model-settings.cjs
apps/frontend/electron/model-settings.test.cjs
apps/frontend/package.json
```

`/settings/models` 已由 P1-07 owner recovery navigation 与 UI screen contract 冻结为模型恢复入口；
因此本 EXEC 显式允许最小路由注册及其测试，不授权新增第二个 Settings 实现或改变其他路由语义。

## Tasks

1. EXEC-040 dependency audit。
2. 实现 Settings 状态机、provider/model form、apply/reverify/update/clear。
3. 实现 data/cost/fallback/error/recovery copy 和 accessible status。
4. 覆盖 component/security/responsive/keyboard tests。
5. 以独立 loopback port 与当前 backend start token 的私有 readiness 握手隔离并发 App 实例。
6. packaged macOS App 完成真实 provider configure→canonical learning→relaunch。
7. 运行 full gates，形成 release report。
8. 仅在全部 AC 有证据后把 P1-02 标 DONE，归档并独立 commit。

## Acceptance Criteria

- `EXEC041-AC-001`：`P102-AC-001..013` 全部满足。
- `EXEC041-AC-002`：首次用户不离开 App 完成配置与真实验证。
- `EXEC041-AC-003`：每个失败状态都有数据安全说明和下一动作。
- `EXEC041-AC-004`：真实 provider、backend revision、canonical inference 与 relaunch recovery 一致。
- `EXEC041-AC-005`：full backend/frontend/electron/security/docs gates PASS。
- `EXEC041-AC-006`：P1-02 register=DONE；Engineering/Security/Real Provider PASS；Learning Evidence 仍 insufficient。
- `EXEC041-AC-007`：并发 Askora App 不共享 backend；公共 `/ready`、已占用 port 或其他实例均不能满足本实例 identity/readiness。

## Required Tests

```bash
cd apps/backend
pytest
ruff check app tests
mypy app
alembic check

cd apps/frontend
npm run test:electron
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

真实门禁另需：packaged macOS App、真实 provider、Settings apply、canonical learning response、App restart exact configuration recovery。Mock-only 不得满足。

## Completion Report

完成日期：2026-08-09。

```text
Engineering Gate: PASS
Security / Ownership Gate: PASS
Real Provider Product Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

packaged macOS App 已使用智谱 `glm-4.7-flash` 完成 Settings real probe、encrypted vault
revision 1、authenticated backend restart、canonical `real_model` response 与同一 revision 的
quit/relaunch recovery。后端 378 passed / 2 skipped，Electron 41/41，frontend 70/70，构建、
npm audit、Ruff、mypy、PostgreSQL `alembic check`、docs checker 与 diff check 全部通过。

`P102-AC-001..013` 与 `EXEC041-AC-001..007` 均有当前证据；P1-02 register 已标 DONE。
Blocking SPEC GAP：none。完整证据与范围外发现见
[P1-02 Completion Report](../releases/p1-02-model-settings.md)。
