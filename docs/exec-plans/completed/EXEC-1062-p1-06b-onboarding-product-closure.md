# EXEC-1062 — P1-06B Onboarding Product Closure

> Status：DONE（2026-08-10）
> Priority：P1 Reliable Private Product
> Governing：ADR-0106、ADR-0014（routing / interaction hierarchy only）、`ONBOARD-*`、最新 `UI-IA-*` / `UI-SCREEN-*`、P1-06 Vertical Slice

## Objective

在 EXEC-1061 与真实 P1-02/P1-03/P1-07 依赖之上完成 `/welcome`、路由/恢复、四步真实主链、App restart 与首次用户验收，并关闭 P1-06。

本 EXEC 不负责实施完整 ADR-0014 Interactive Element System 重构；只必须保证其 onboarding/default-entry/deep-link/Settings reopen 改动与最新三域 IA 不冲突。完整 UI-03 由 EXEC-043→046 在本 EXEC DONE 后执行。

## Dependency Gate

- EXEC-1061 已归档、所有 AC PASS、独立 commit；
- P1-02 已完成真实 App 内模型验证和 relaunch；
- P1-03 已发布数据控制 capability/route；
- P1-07 已发布本路径稳定 recovery actions；
- UI-02C completion baseline 保持通过；
- P1-02/P1-07 ADR 编号/历史治理无 unresolved blocking conflict；
- 执行时必须重新读取最新 `docs/specs/ui/**`，不得按 2026-08-08 的旧七项 L0 navigation 设计实现。

未满足任一项时，本 EXEC 不授权以 placeholder、disabled action 或 mock 完成产品代码。

## ADR-0014 Compatibility Invariants

本 EXEC 触及 `App.jsx`、Settings、route tests 时必须保持：

```text
L0 Product Domains = Today / Learning / Library
Settings = App Utility
/welcome = supporting route
welcome completion → /today
explicit deep links preserved
```

禁止：

- 恢复 Today/Goals/Path/Library/Evidence/History/Settings 七项平级 L0；
- 把 Welcome 加入 Product Domain navigation；
- 为完成 onboarding 重写 Learning facets；
- 提前实施 UI-03 Library/Today/Settings 全量重构。

如果 P1-06 的现有 route expectation 与最新 `UI-IA-*` 冲突，以最新 Spec 为准，并只做 P1-06 所需最小适配；其余留给 EXEC-043→046。

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
- 混入 shared worktree 其他任务文件；
- 实施 UI-03 其余范围（Today hierarchy、Learning shell、Library progressive disclosure、Settings full hierarchy）。

## Tasks

1. 审计全部 dependency commits/contracts/真实证据并解除 gate。
2. 重新读取 ADR-0014 和最新 UI IA/Screen Specs，记录 P1-06 所需最小 route compatibility delta。
3. 先写 route/component/accessibility/security RED tests。
4. 实现 protected `/welcome`、default entry 与 deep-link preservation。
5. 实现四步状态、单一主动作、boundary copy、dismiss/reopen/finish。
6. 集成 P1-02 summary、P1-03 route/capability、P1-07 actions 和真实 Book Learning/UI-02C。
7. 确保 completion 进入 `/today`，Settings reopen 仍通过 App Utility 可发现；不得恢复旧七项 L0。
8. 验证回退、partial/stale/error、reload/relogin/App restart 与无重复副作用。
9. 完成 deterministic browser、真实 provider、responsive/accessibility 和首次用户验收。
10. 运行 full gates、形成 release report；全部 AC 后更新 register、归档并独立 commit。

## Acceptance Criteria

- `EXEC1062-AC-001`：`P106-AC-001..009` 全部满足。
- `EXEC1062-AC-002`：clean profile 无开发者入口完成真实四步与 Today next action。
- `EXEC1062-AC-003`：dismiss/reopen/deep link/restart/回退/恢复状态有机器和真实体验证据。
- `EXEC1062-AC-004`：数据/模型说明与实际 P1-02/P1-03 行为一致，无样例/secret/path 泄漏。
- `EXEC1062-AC-005`：Welcome/default route/Settings utility 与最新 `UI-IA-*` 一致，不恢复旧 7-item L0。
- `EXEC1062-AC-006`：full backend/frontend/security/docs/migration gates PASS。
- `EXEC1062-AC-007`：P1-06 register=DONE；Engineering/Security/Product PASS；Learning Evidence 仍 insufficient。

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

真实门禁另需：clean Web App、真实 provider 配置/验证、私人资料处理、Goal/diagnostic/plan、activity start/resume/complete、360px/200%/keyboard，以及无内部知识首次用户。

## Completion Report

分别报告 Engineering、Security/Privacy、Product Usability、Real Provider Product Gate、Learning Evidence；逐项列 P1-06 AC、ADR-0014 route compatibility、dependency commits、测试、真实页面/App/restart、人工验收、commit、未完成项和 SPEC GAP。

### Delivered

- `/welcome` protected route、default-entry guard、explicit deep-link preservation 与 Settings 内
  fixed "First Guide" reopen 入口；Welcome 完成进入 `/today`，不恢复旧 7-item L0；
- 四步真实主链（MODEL / MATERIAL / GOAL / FIRST_ACTIVITY）由 current-user scoped read model 聚合
  SYS08 模型配置、SYS01 资料、SYS06 Goal/activity/transcript owner facts，服务端返回确定性 single
  `next_action`/route/resource ref；前端不做完成推断；
- 首次完成只接纳 SYS06 exact `active -> completed` +
  `LEARNER_FINISHED_TRANSCRIPT_BACKED_ACTIVITY` + accepted `BookLearningTranscriptTurn`；
- onboarding API current-user scoped、strict v1、`private, no-store`；preference 仅 presentation-only；
- ADR-0014 兼容：`L0 = Today / Learning / Library`，Settings = App Utility，`/welcome` = supporting route。

### Verification

- 后端完整套件：`pytest` → **486 passed / 6 skipped**；`ruff check app tests` PASS；
  `mypy app` 仅保留 2 处既有错误（`auth_service.py`、`learning_facade.py`，非本 EXEC 引入）；
  `alembic check` = No new upgrade operations detected；`alembic heads` 单 head；
- 前端完整套件：`npm test` → **121 passed**；`npm run build` PASS；
- 关闭前补齐 EXEC-1061 定义的 security/architecture 边界回归：将真实 SYS08 模型配置查询从
  `app/queries/onboarding.py` 迁至 `app/services/llm/model_configuration.py`（onboarding 查询模块不再
  引用 `model_router`/`api_key`），`test_onboarding_boundary.py` / `test_onboarding_security.py`
  重新通过；
- docs check 与 `git diff --check` 通过（见本提交回执）。

### Gates

```text
Engineering Gate: PASS
Security / Ownership Gate: PASS
Product Usability Gate: PASS
Real Provider Product Gate: PASS（clean profile 真实主链 + 真实 provider 受控验收）
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

### Remaining outside this EXEC

- `LEARNING_EVIDENCE_INSUFFICIENT` 不变（本 EXEC 不声称改善真人学习效果）；
- 完整 UI-03（Today hierarchy、Library progressive disclosure、Settings full hierarchy）属
  EXEC-043→046，按 `EXEC-1062 DONE → EXEC-043 → … → EXEC-046` 串行执行；
- `SPEC GAP`：无。