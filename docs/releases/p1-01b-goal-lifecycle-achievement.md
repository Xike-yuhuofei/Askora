# P1-01B Goal Lifecycle and Evidence-gated Achievement Completion Report

> Date: 2026-08-09
> Scope: EXEC-039
> Governing: ADR-0011, SYS06 Goal Management, P1-01B Vertical Slice

## 1. Final gate

```text
Engineering Gate: PASS
Contract / Ownership / Security Gate: PASS
Real Configured-model Gate: PASS
Real Browser / Responsive / Accessibility Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

P1-01B 已关闭。该结论证明目标生命周期、成功标准测量和证据门禁达成的工程闭环成立；
`goal achieved` 仅表示该私人目标在对应 policy 版本下满足，不等于一般化 mastery、产品学习效果或真人因果证据。

## 2. Delivered behavior

- SYS06 append-only `active ↔ paused`、`active → achieved`、`confirmed|active|paused → archived` Goal/Plan state；终态不可原地恢复；
- 暂停保留 exact activity/transcript 并阻止继续选择或启动活动；恢复仅在 definition/mapping/source refs 仍有效时恢复 exact plan；
- 归档 supersede 当前 activity/plan、清空 Focus，并可复制为新 goal id 的草稿；达成也结束遗留 active activity；
- versioned `LearningObjectiveV1`、`GoalAchievementPolicyV1`、criterion-specific AssessmentActivity 和 exact-evidence evaluation；
- recall 优先确定性评分；开放题绑定 rubric、来源证据、严格 schema 和独立 reviewer；
- Prompt Injection、provider/schema failure、低置信或 grader 分歧均 fail closed，不形成 learner failure；
- 只有 accepted canonical AssessmentResult 进入 SYS03 LearnerEvidence，且只有用户可最终确认达成。

## 3. Automated gates

```text
Backend full pytest on latest main integration: 488 passed, 7 skipped
Backend ruff app/tests: PASS
Backend mypy app: PASS (202 source files)
Alembic: single head; SQLite fresh upgrade, representative migration and alembic check PASS
Frontend tests: 83 passed
Frontend production build: PASS
Frontend npm audit --omit=dev: 0 vulnerabilities
Documentation checker: 183 files, 0 broken local links
```

PR 集成时已将 P1-01A migration 串行到 `main` 上 P1-05 account lifecycle head
`f36c91b807d3` 之后，避免形成第二个 Alembic head；20 项代表性迁移/恢复回归通过，
另 1 项 PostgreSQL 环境条件测试跳过。
P1-01 新增表也已显式加入 P1-05 账号删除 subject registry：10 张用户目标表按 SYS06
可擦除数据处理，achievement policy 表保持全局规则，grader payload 纳入删除扫描。

覆盖包括 lifecycle expected-version/idempotency、Focus、exact resume、输入过期 replan、归档复制、
暂停调度门禁、四类成功标准、确定性评分、开放题双重评分、相关活跃误解门禁、owner 隔离、
Prompt Injection、provider/低置信失败、restart/outbox/replay、grader-only payload 隔离和 legacy migration。

## 4. Real configured-model evidence

真实配置 DeepSeek `deepseek-chat` 完成 rubric/source/schema-bound 开放题独立评分与复核。最终候选树复验得到安全复核结果：

```text
evaluator_versions: goal-open-grader/1.0, goal-open-reviewer/1.0
assessment_confidence: 0.8
result: needs_review
```

同一实现的前序候选复验曾得到 `assessment_confidence: 0.85 / accepted`；也观察到真实 provider
限流进入 `scoring_failed`。这些结果共同证明正常接纳与分歧/失败 fail-closed 路径，不产生错误的
learner failure 或未接纳证据。

## 5. Real browser evidence

隔离 SQLite 数据库和本地 FastAPI/Vite 服务上，真实浏览器以临时私人用户完成：目标详情 → 暂停 →
恢复 exact plan → 安排 recall 验证 → 确定性评分 accepted → 检查证据门禁 → 用户确认 achieved。
页面逐步呈现状态恢复、fail-closed 解释和“达成不等于 mastery/真人学习效果”的终态文案；浏览器控制台无 warning/error。

360、768、1024、1440 px 四档视口均无横向溢出并保留核心控件；360 px 也覆盖 768 px 在 200%
缩放下更窄的等效 CSS 布局边界。原生 button 保持键盘焦点语义，真实浏览器验证焦点可达；内置浏览器
不响应系统缩放/激活快捷键，因此不把快捷键发送本身作为额外产品证据。隔离服务正常关闭，临时数据库与资料已移入废纸篓。

## 6. Ownership and evidence boundary

- SYS06 唯一写 Goal/Plan lifecycle、Focus、Objective/Assessment scheduling 与 achievement evaluation；
- SYS04 唯一写 canonical AssessmentResult 和单次评分诊断；grader-only payload 不返回前端；
- SYS03 仅通过 canonical projector 接纳 accepted AssessmentResult，不接纳 `needs_review/scoring_failed`；
- model/provider 不直接改写 Goal、Plan、LearnerState、TeachingAction 或 ReviewSchedule；
- Learning Evidence Gate 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
