# Askora UI-02B2 Guided Book Learning Completion Report

> Status：DONE
>
> 日期：2026-08-08
>
> 实现合同：`EXEC-026` / `UI02B2-AC-001..012`
>
> Decision authority：user-delegated Codex

## 1. Release 结论

```text
Engineering Gate: PASS
UI / Contract / Ownership / Security Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
Current Local Database Activation: PENDING MIGRATION
```

UI-02B2 已把 Goal 确认后的内部 pipeline 按钮收敛为 bounded safe auto-advance，并交付
rank-1 primary diagnostic target、system-start 首轮教学、按 exact LearningActivity 持久化的
append-only transcript、刷新恢复与 learner-visible 资料依据。它没有新增第二 tutor、第二状态 owner、
legacy dialog 双写，亦不把 system-start 伪装成 learner evidence。

## 2. Contract、迁移与安全交付

- `POST /api/v1/book-learning/{document_id}/advance` 每次只执行一个 readiness 授权的 allowlist command；
  Goal 创建/确认、diagnostic 作答与 teaching start 仍要求明确用户动作。
- SYS06 persisted stable rank 的第一个 target 是首轮诊断目标；UI/SYS08 不重排。
- `book_learning_advance_records` 保存 exact advance receipt；重复 key 重放已接受响应。
- `book_learning_transcript_turns` 按 current user + plan + activity + deterministic session append-only；
  learner/system-start 参数边界、turn number、idempotency 与 exact response 都有数据库约束和回归测试。
- system-start prompt 由服务端 versioned bounded intent 生成，不接受客户端 system prompt，不产生
  Attempt、AssessmentResult 或 MasteryEstimate。
- transcript 仅呈现 `allowed_use=learner_visible` 的 SourceSpan 引用；grader/internal/unknown evidence fail closed。
- migration 以现有 `9b4c2d7e1a60` 为 parent，SQLite 临时库完成 upgrade → check，并由 migration test 覆盖
  downgrade/forward-fix。当前用户 PostgreSQL 未被自动迁移，因此运行新代码前仍需显式执行
  `cd apps/backend && uv run alembic upgrade head`。

## 3. UI 与真实浏览器验收

- 主流程收敛为“目标 / 起点 / 本次学习”三段；内部 command、readiness、SYS/version 默认只在技术详情显示。
- READY 页面只有一个“开始本次学习”主动作；系统发起第一问，后续输入恢复 durable next turn。
- 资料依据随 accepted assistant turn 展示，刷新后从服务端 transcript 恢复，不依赖 sessionStorage。
- 使用当前本地真实 EPUB `张一鸣管理日志.epub` 进入 `READY_TO_LEARN`，默认桌面视口与 360×800
  均完成视觉检查，console 0 error；发现并修复桌面主按钮偏左问题。
- 验收使用显式开发自动登录，没有提交 diagnostic/teaching 表单，也没有创建个人学习作答记录；
  未触发可能产生外部模型费用的真实教学回合。

## 4. Verification Evidence

| Gate | 结果 |
|---|---|
| targeted backend Book Learning suite | 11 passed |
| backend full pytest | 351 passed, 2 skipped, 28 warnings |
| Ruff | PASS |
| mypy | PASS；仅既有 untyped-body notes |
| migration temporary SQLite upgrade/check | PASS；No new upgrade operations detected |
| migration upgrade/downgrade/forward-fix test | PASS |
| frontend Vitest | 11 files / 45 tests PASS |
| frontend production build | PASS |
| real local page / console | READY_TO_LEARN；0 error |
| desktop / 360×800 visual QA | PASS |
| targeted docs validation | PASS |
| `git diff --check` | PASS |

仓库级 `check_docs.py` 仍会报告本任务开始前已存在、未跟踪的 `docs/engineering/README.md` 中 `file://`
链接与 inventory 缺项；目标治理/Spec/EXEC/Release 文件通过定向校验，本任务未改该用户文件。

## 5. AC 与残余边界

`UI02B2-AC-001..012` 与 `EXEC026-AC-001..004` 均有实现和当前自动化/浏览器证据。
Blocking SPEC GAP：none。

并发去重锁覆盖当前 Askora 私人本地单进程运行模型；数据库 unique constraint 继续保护最终 accepted
turn。完整 activity completion、下一活动推进、Goals/Path/Evidence 顶层页面及真人学习效果评估仍不在
本 Slice。Engineering、UI、真实页面与模型连通性均不能证明真人学习效果。
