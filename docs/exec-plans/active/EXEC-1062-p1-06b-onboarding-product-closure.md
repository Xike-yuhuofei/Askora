# EXEC-1062 — P1-06B Onboarding Product Closure

> Status：FROZEN / BLOCKED_BY_DEPENDENCY_GATE
> Priority：P1 Reliable Private Product
> Governing：ADR-0106、`ONBOARD-*`、P1-06 Vertical Slice

## Objective

在 EXEC-1061 与真实 P1-02/P1-03/P1-07 依赖之上完成 `/welcome`、路由/恢复、四步真实主链、
App restart 与首次用户验收，并关闭 P1-06。

## Dependency Gate

- EXEC-1061 已归档、所有 AC PASS、独立 commit；
- P1-02 已完成真实 App 内模型验证和 relaunch；
- P1-03 已发布数据控制 capability/route；
- P1-07 已发布本路径稳定 recovery actions；
- UI-02C completion commit `44ed11a` 保持通过；
- P1-02/P1-07 ADR-0012 编号冲突完成历史消歧。

未满足任一项时，本 EXEC 不授权以 placeholder、disabled action 或 mock 完成产品代码。

## Allowed Files

```text
docs/product-gap-register-p1-p2.md
docs/document-inventory.md
docs/specs/README.md
docs/specs/interfaces/onboarding-contract.md
docs/specs/ui/information-architecture.md
docs/specs/ui/screen-contracts.md
docs/specs/ui/data-contracts.md
docs/specs/ui/quality-and-migration.md
docs/specs/vertical-slices/p1-06-first-use-onboarding.md
docs/exec-plans/README.md
docs/exec-plans/active/EXEC-1062-p1-06b-onboarding-product-closure.md
docs/exec-plans/completed/EXEC-1062-p1-06b-onboarding-product-closure.md
docs/exec-plans/completed/README.md
docs/releases/p1-06-first-use-onboarding.md
docs/releases/README.md
apps/backend/app/contracts/onboarding.py
apps/backend/app/queries/onboarding.py
apps/backend/app/services/onboarding.py
apps/backend/tests/contracts/test_onboarding_contract.py
apps/backend/tests/integration/test_onboarding_journey.py
apps/backend/tests/security/test_onboarding_security.py
apps/frontend/src/App.jsx
apps/frontend/src/api/onboarding.js
apps/frontend/src/pages/Welcome.jsx
apps/frontend/src/pages/Welcome.css
apps/frontend/src/pages/Settings.jsx
apps/frontend/src/pages/Settings.css
apps/frontend/src/test/AppRoutes.test.jsx
apps/frontend/src/test/Welcome.test.jsx
apps/frontend/src/test/OnboardingSecurity.test.jsx
apps/frontend/package.json
```

## Forbidden Changes

- frontend-only completion/next-action inference；
- 强制重定向 explicit deep link；
- 复制 P1-02/03/07 设置、备份或恢复 UI/logic；
- 自动创建样例、Goal、Activity 或完成 transition；
- 用 mock/连接成功冒充第一节完成；
- 改写 SYS01～SYS08 owner semantics；
- 混入 shared worktree 其他任务文件。

## Tasks

1. 审计全部 dependency commits/contracts/真实证据并解除 gate。
2. 先写 route/component/accessibility/security RED tests。
3. 实现 protected `/welcome`、default entry 与 deep-link preservation。
4. 实现四步状态、单一主动作、boundary copy、dismiss/reopen/finish。
5. 集成 P1-02 summary、P1-03 route/capability、P1-07 actions 和真实 Book Learning/UI-02C。
6. 验证回退、partial/stale/error、reload/relogin/App restart 与无重复副作用。
7. 完成 deterministic browser、真实 provider、macOS App、responsive/accessibility 和首次用户验收。
8. 运行 full gates、形成 release report；全部 AC 后更新 register、归档并独立 commit。

## Acceptance Criteria

- `EXEC1062-AC-001`：`P106-AC-001..009` 全部满足。
- `EXEC1062-AC-002`：clean profile 无开发者入口完成真实四步与 Today next action。
- `EXEC1062-AC-003`：dismiss/reopen/deep link/restart/回退/恢复状态有机器和真实体验证据。
- `EXEC1062-AC-004`：数据/模型说明与实际 P1-02/P1-03 行为一致，无样例/secret/path 泄漏。
- `EXEC1062-AC-005`：full backend/frontend/security/docs/migration gates PASS。
- `EXEC1062-AC-006`：P1-06 register=DONE；Engineering/Security/Product PASS；Learning Evidence
  仍 insufficient。

## Required Tests

```bash
cd apps/backend
pytest
ruff check app tests
mypy app
alembic check

cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

真实门禁另需：clean Web App、真实 provider 配置/验证、私人资料处理、Goal/diagnostic/plan、activity
start/resume/complete、360px/200%/keyboard，以及无内部知识首次用户。

## Completion Report

分别报告 Engineering、Security/Privacy、Product Usability、Real Provider Product Gate、Learning
Evidence；逐项列 P1-06 AC、dependency commits、测试、真实页面/App/restart、人工验收、commit、未完成项
和 SPEC GAP。
