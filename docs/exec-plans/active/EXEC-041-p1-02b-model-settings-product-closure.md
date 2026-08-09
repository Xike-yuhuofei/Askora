# EXEC-041 — P1-02B Model Settings Product Closure

> Status：FROZEN / ACTIVE
> Priority：P1 Product Reliability
> Governing：ADR-0013、`MODEL-CONFIG-*`、P1-02 Vertical Slice

## Objective

在 EXEC-040 安全基础之上完成 Settings 产品体验、真实 macOS App/provider/relaunch 验收、release evidence 与 P1-02 gap closure。

## Dependency Gate

EXEC-040 已归档，所有 foundation AC PASS，并形成独立集成提交 `d59837d`。

## Allowed Files

```text
docs/product-gap-register-p1-p2.md
docs/document-inventory.md
docs/specs/README.md
docs/specs/ui/README.md
docs/specs/ui/screen-contracts.md
docs/specs/ui/data-contracts.md
docs/specs/ui/quality-and-migration.md
docs/specs/vertical-slices/p1-02-model-settings.md
docs/exec-plans/README.md
docs/exec-plans/active/EXEC-041-p1-02b-model-settings-product-closure.md
docs/exec-plans/completed/EXEC-041-p1-02b-model-settings-product-closure.md
docs/exec-plans/completed/README.md
docs/releases/p1-02-model-settings.md
docs/releases/README.md
apps/backend/app/main.py
apps/backend/tests/contracts/test_model_configuration_contract.py
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
5. packaged macOS App 完成真实 provider configure→canonical learning→relaunch。
6. 运行 full gates，形成 release report。
7. 仅在全部 AC 有证据后把 P1-02 标 DONE，归档并独立 commit。

## Acceptance Criteria

- `EXEC041-AC-001`：`P102-AC-001..010` 全部满足。
- `EXEC041-AC-002`：首次用户不离开 App 完成配置与真实验证。
- `EXEC041-AC-003`：每个失败状态都有数据安全说明和下一动作。
- `EXEC041-AC-004`：真实 provider、backend revision、canonical inference 与 relaunch recovery 一致。
- `EXEC041-AC-005`：full backend/frontend/electron/security/docs gates PASS。
- `EXEC041-AC-006`：P1-02 register=DONE；Engineering/Security/Real Provider PASS；Learning Evidence 仍 insufficient。

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

分别报告 Engineering、Security/Ownership、Real Provider Product Gate、Learning Evidence；逐项列 P1-02 AC、测试、真实页面/App/relaunch、commit、未完成项和 SPEC GAP。
