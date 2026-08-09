# Askora UI-02B Goals, Learning Path and Evidence Completion Report

> Status：DONE
>
> 日期：2026-08-09
>
> 实现合同：`EXEC-029` / `UI02B-VSLICE-AC-001..010`
>
> Implementation commit：本报告与实现同一原子提交，hash 见 Git 历史与交付回执

## 1. Release 结论

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02B 已把 `/goals`、`/path`、`/evidence` 从占位入口交付为真实、只读、current-user scoped 的产品页面，并让 `/today` 复用同一 canonical current-plan 选择。活动启动/恢复关联尚无冻结合同，因此产品只展示真实计划，不提供虚假的“继续学习”。

## 2. 产品与合同交付

- Goals 只展示当前用户每个 `goal_id` 的最新 owner 版本，不提供未冻结的编辑动作。
- Path 按 `LearningPlan.activity_ids` 原顺序展示活动；多 current plan 要求显式 goal scope，不按时间猜选。
- durable Objective metadata 尚未发布时保留 exact ref，以 null 与稳定 reason 呈现，不从活动或资料反推事实。
- Evidence 只读取 SYS03 canonical estimate；概率明确标记为估计，缺失值不变成 0，也不由前端阈值生成“已掌握”。
- SYS01 标签仅在当前用户 current revision exact knowledge-unit id 命中时附加；legacy profile 默认不进入主视图。
- 三个 endpoint 均为 strict v1.0、current-user scoped、private/no-store；API 层只做 transport mapping。

## 3. UI 与真实验收

- 真实本地 FastAPI、SQLite 与 Vite 页面完成 Today、Goals、Path、Evidence 全链路验收。
- Today 显示唯一 canonical 目标与活动，并明确活动启动/恢复 link 尚未冻结。
- Path 保留规划顺序并显示 Objective metadata 缺失说明；Evidence 显示能力估计、置信度和命名证据计数。
- 360×800 下四个核心页面均无水平溢出；关键状态有文字表达，浏览器 console 为 0 warning / 0 error。
- 页面与自动化测试覆盖 loading、empty、ready/partial、error、unauthorized、多计划显式选择和空证据语义。

## 4. Verification Evidence

| Gate | 结果 |
|---|---|
| backend targeted workspace suite | 10 passed；2 warnings |
| backend full pytest（当前集成工作区） | 363 passed；2 skipped；4 warnings |
| backend full pytest（clean candidate） | 336 passed；1 skipped；1 inherited baseline failure；该失败已在父提交独立复现 |
| Ruff | PASS |
| mypy | PASS；仅既有 untyped-body notes |
| Alembic check | PASS；No new upgrade operations detected |
| frontend Vitest（clean candidate） | 14 files / 50 tests PASS |
| frontend production build | PASS |
| npm audit `--audit-level=high` | PASS；0 vulnerabilities |
| real local browser | Today / Goals / Path / Evidence PASS |
| narrow viewport / console | 360×800 无水平溢出；0 warning / 0 error |
| clean candidate worktree | UI-02B targeted、Ruff、mypy、migration、frontend、docs 与 diff PASS；不依赖未提交 UI-02B2 / UI-02B3 / EXEC-028 改动 |
| docs / diff checks | PASS |

## 5. Ownership 与安全结论

- SYS06 仍是 Goal、Plan、Activity 唯一写入者；本 Slice 只增加 query projection。
- SYS03 仍是 MasteryEstimate 唯一写入者；UI 不写 mastery，不把 probability 解释为最终掌握标签。
- SYS01 只提供 owner-safe exact label；缺少可靠关联时返回空值，不回退到其他用户或 legacy 数据。
- 未增加数据库迁移、生产依赖、外部服务、第二 truth 或跨系统写入。

## 6. 残余边界

Blocking SPEC GAP：none。

durable LearningObjective metadata、canonical Activity start/resume/session link、Activity completion、Goal 编辑、计划重排与真人学习效果评估仍不属于 UI-02B。UI 连通性、自动化测试、synthetic data 和真实浏览器验收均不能证明真人学习效果，因此 Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

clean candidate 的全量后端门禁继承一个父提交既有失败：`test_exec025_legacy_local_user_id_uses_stable_canonical_owner` 在 `DocumentService` 中直接执行 `UUID(user.id)`。当前集成工作区的后续未提交改动已使全量 363 tests 通过；该修复属于既有 Book Learning / 后续切片文件，不纳入 EXEC-029，也未被本提交覆盖或偷带。
