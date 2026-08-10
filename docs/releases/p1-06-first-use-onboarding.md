# P1-06 First-Use Onboarding Completion Report

> Date: 2026-08-10
> Scope: EXEC-1061 (readiness foundation) + EXEC-1062 (product closure)
> Governing: ADR-0106, ADR-0014 (routing / interaction hierarchy), `ONBOARD-*`, `UI-IA-*` / `UI-SCREEN-*`, P1-06 Vertical Slice

## 1. Final gate

```text
Engineering Gate: PASS
Security / Ownership Gate: PASS
Product Usability Gate: PASS
Real Provider Product Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

P1-06 首次使用引导已关闭：clean profile 可在无开发者入口的情况下完成真实四步主链并进入 Today
下一步。本结论证明 onboarding 的工程/安全/产品闭环成立，不改变 `LEARNING_EVIDENCE_INSUFFICIENT`
（不声称改善真人学习效果）。

## 2. Delivered behavior

- `/welcome` protected route、default-entry guard、explicit deep-link preservation；Settings 内固定
  "First Guide" reopen 入口；Welcome 完成进入 `/today`，不恢复旧 7-item L0；
- 四步主链（MODEL / MATERIAL / GOAL / FIRST_ACTIVITY）由 current-user scoped read model 聚合
  SYS08 模型配置、SYS01 资料、SYS06 Goal/activity/transcript owner facts；
- 服务端返回确定性 single `next_action`/route/resource ref；UI 不做完成推断、不猜选业务对象；
- 首次完成只接纳 SYS06 exact `active -> completed` + `LEARNER_FINISHED_TRANSCRIPT_BACKED_ACTIVITY`
  + accepted `BookLearningTranscriptTurn`；
- API current-user scoped、strict v1、`private, no-store`；preference 仅 presentation-only；
- ADR-0014 兼容：`L0 = Today / Learning / Library`，Settings = App Utility，`/welcome` = supporting route。

## 3. Automated gates

- 后端完整套件：`pytest` → **486 passed / 6 skipped**；`ruff check app tests` PASS；`alembic check`
  = No new upgrade operations detected；`alembic heads` 单 head；
- 前端完整套件：`npm test` → **121 passed**；`npm run build` PASS；
- 关闭前补齐 EXEC-1061 定义的 security/architecture 边界回归：真实 SYS08 模型配置查询从
  `app/queries/onboarding.py` 迁至 `app/services/llm/model_configuration.py`（onboarding 查询模块不再
  引用 `model_router`/`api_key`），`test_onboarding_boundary.py` / `test_onboarding_security.py`
  重新通过；
- docs check 与 `git diff --check` 通过。

## 4. Claim boundary

P1-06 证明 onboarding 的工程/安全/产品可用性闭环；不证明自适应教学改善真人学习效果。完整 UI-03
（Today hierarchy、Library progressive disclosure、Settings full hierarchy）属 EXEC-043→046，按
`EXEC-1062 DONE → EXEC-043 → … → EXEC-046` 串行执行。
