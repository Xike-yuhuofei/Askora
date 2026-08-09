# P1-01A Goal Definition, Draft and Safe Replan Completion Report

> Date: 2026-08-09
> Scope: EXEC-037
> Governing: ADR-0010, SYS06 Goal Management, P1-01A Vertical Slice

## 1. Final gate

```text
Engineering Gate: PASS
Contract / Ownership / Security Gate: PASS
Real Browser / Responsive / Accessibility Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

P1-01A 已关闭。该结论证明目标定义、草稿、预览、Focus 与安全 Replan 的工程闭环成立，
不证明真人学习效果，也不代表 P1-01B 生命周期和 evidence-gated achievement 已完成。

## 2. Delivered behavior

- `LearningGoalDefinitionV2`、`LearningGoalStateV1`、`LearningPlanStateV1`、`LearningGoalDraftV1`、`GoalChangePreviewV1` 与 `FocusedLearningGoalStateV1` append-only/current projection 合同；
- `/goals/new`、`/goals/drafts/:draftId`、`/goals/:goalId`、`/goals/:goalId/edit` 的统一草稿与编辑体验；
- 多资料 current-user scope、可测成功标准候选、带来源和证据的显式 target 选择；
- expected version、idempotency key、correlation id、stale preview、不可执行资料和未确认 target 的稳定拒绝语义；
- 无 active activity 时原子立即应用；存在 active activity 时等待正常边界，或显式 `superseded` 后切换；
- preview/input 过期和新计划准备失败时保留旧 activity/plan，不产生两个 current plan；
- 第一个激活目标可显式设为 Focus；Book Learning 快捷入口迁移至同一 SYS06 draft/apply 服务。

## 3. Automated gates

```text
Backend full pytest: 407 passed, 4 skipped
Backend ruff app/tests: PASS
Backend mypy app: PASS (179 source files)
Alembic: single head; migration compatibility and alembic check PASS
Frontend tests: 60 passed
Frontend production build: PASS
Frontend npm audit --omit=dev: 0 vulnerabilities
Documentation checker: 162 files, 0 broken local links
```

覆盖包括多资料、不可测标准、不可执行资料、显式 target、幂等重放、expected-version conflict、
stale preview、立即/边界/显式 supersede、旧计划故障保护、Focus、cross-user、private no-store、
SQLite representative migration fixture 与 legacy-compatible read。

## 4. Real browser evidence

在隔离 SQLite 数据库和本地 FastAPI/Vite 服务上注册临时私人用户，真实浏览器进入
`/goals/new`，填写目标、主题与能力，并由 API 生成 recall/understand/apply/transfer 四类可测候选。
首次请求在服务尚未就绪时显示可恢复错误，重试后 `POST /api/v1/goals/criteria/suggest` 返回 200，
页面完整呈现候选及 evidence requirements。

360、768、1024、1440 px 四档视口均保留目标标题和成功标准操作；200% 浏览器缩放后核心内容仍可访问；
键盘 Enter 可触发候选生成。隔离服务随后正常关闭，未修改现有私人资料。

## 5. Ownership and evidence boundary

- SYS06 唯一写入 Goal Definition/State/Draft/Preview/Focus 与当前 Plan State；
- SYS01 继续唯一判定资料 current-user executable scope；target evidence 必须绑定 exact source/revision；
- activity boundary 由 canonical SYS06 lifecycle progression 触发，不由前端或 LLM 直接改写计划；
- P1-01A 不写 LearnerState、AssessmentResult、TeachingAction 或 ReviewSchedule；
- `LEARNING_EVIDENCE_INSUFFICIENT` 保持不变，目标达成测量属于 P1-01B。
