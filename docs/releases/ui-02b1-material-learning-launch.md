# Askora UI-02B1 Material-to-Learning Launch Completion Report

> Status：DONE
>
> 日期：2026-08-08
>
> 实现合同：`EXEC-025` / `UI02B1-AC-001..012`
>
> Implementation commit：本报告与实现同一原子提交，hash 见 Git 历史与交付回执

## 1. Release 结论

```text
Engineering Gate: PASS
UI Contract / Ownership / Accessibility Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02B1 已交付 `/library → /book-learning/:documentId` 的单资料学习启动路径：用户可形成并确认 Goal、执行单 target mapping 与 prerequisite diagnostic、生成/选择 LearningActivity，并进入现有 canonical teaching façade。它不创建第二 tutor、第二 owner truth 或 legacy quick-session 伪装路径。

## 2. Contract 与安全交付

- readiness 与 exact owner refs 决定页面步骤；刷新不从前端状态推导 canonical truth，也不重放 activity selection。
- learner-visible diagnostic 只公开 item ref、need ref/version、type、prompt、options；answer、rubric、explanation 与 grader metadata 为零泄漏。
- 多 target mapping 以 `UI02B1_SINGLE_TARGET_REQUIRED` fail closed；unknown state、missing ref、blocked/partial/auth/version conflict 不绕过 owner command。
- 历史本地非 UUID 用户主键使用 deterministic canonical identity projection，不改写原 `User.id`。
- query response 使用 private `no-store`；当前页面消息明确不具备 durable history/resume 合同。

## 3. UI 与真实验收

- Library 对未失败/拒绝/隔离的资料显示“从这份资料开始学习”，最终可用性仍由 backend readiness 判断。
- Goal、确认、mapping、diagnostic、plan、activity selection 与 teaching 均通过真实 command 后刷新 owner 状态。
- component tests 覆盖完整 mocked canonical flow、多 target 与 unknown readiness fail closed、protected route 和 CTA 边界。
- 使用现有真实 EPUB 页面完成只读验收：readiness 返回 `READY_FOR_GOAL`；1280px 与 360×800 均无水平溢出，浏览器 console 0 error。验收未提交表单或写入个人学习数据。
- 真实验收发现旧 dev user key 不能直接解析 UUID，已用共享 deterministic projection 修复并加入 integration/unit 回归。

## 4. Verification Evidence

| Gate | 结果 |
|---|---|
| backend full pytest | 344 passed, 1 skipped, 28 warnings |
| targeted Book Learning regression | 7 passed |
| Ruff | PASS |
| mypy | PASS；仅既有 untyped-body notes |
| Alembic check | PASS；No new upgrade operations detected |
| frontend Vitest | 11 files / 43 tests PASS |
| frontend production build | PASS |
| npm audit `--audit-level=high` | PASS；0 vulnerabilities |
| real local page path | PASS；真实资料进入 `READY_FOR_GOAL` |
| desktop / narrow / console | 1280px PASS；360×800 无溢出；0 error |
| `git diff --check` | PASS |

## 5. 残余边界

Blocking SPEC GAP：none。

多 target 用户选择、完整 `/goals`/`/path`/`/evidence`、durable activity↔dialog-session/history、Focus 与真人学习效果评估仍不属于 UI-02B1。UI 连通性、自动化测试和真实页面验收不能证明真人学习效果。
