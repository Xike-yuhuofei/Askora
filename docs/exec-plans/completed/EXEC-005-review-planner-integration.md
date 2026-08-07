# EXEC-005 — Review Scheduler + Planner Integration

> Priority：P1  
> Status：READY_AFTER_EXEC-004  
> Depends on：EXEC-001～004

## Objective

建立 SYS07 单一 ReviewSchedule owner，并让 SYS06 只消费 due/overdue 候选纳入 LearningPlan；消除 mastery、memory、plan 对 `next_review_at` 的重复所有权。

## Required Specs

- `systems/06-learning-planner.md`
- `systems/07-review-scheduler.md`
- `domain/domain-model.md`
- `architecture/state-ownership.md`
- `interfaces/persistence-contract.md`
- `vertical-slices/v0.2-learning-loop.md`

## Current Reality

当前仓库没有清晰独立的 Planner/Review bounded context；相关字段/逻辑可能散落在 profile、KT、session 或服务代码中。本任务开始前 Codex 必须搜索：

```text
next_review_at
review
memory_strength
retention
schedule
study_plan
learning_plan
```

并生成一份迁移清单，标记所有现有写入者。

## Allowed Files

```text
app/domains/review_scheduler/**        # 新建
app/domains/learning_planner/**        # 新建
app/contracts/**
app/infrastructure/**
app/models/**                           # 仅必要迁移/兼容
app/services/kt/**                      # 仅移除/适配越权 review 写入
app/services/dkt/**                     # 不得新增 ownership
app/orchestration/**                    # 调用接口
app/workers/**                          # due/recovery task
tests/**review**
tests/**planner**
tests/**schedule**
tests/**replay**
```

## Forbidden Changes

- 不把 ReviewSchedule 写进 LearnerState 作为同一字段；
- 不让 Planner 重新计算 memory model；
- 不让 Review Scheduler 修改 LearningPlan；
- 不用 LLM 决定复习日期；
- 不引入 RL；
- 不把固定 1/3/7/14 天作为唯一长期算法。

## Implementation Tasks

### T1 — Ownership Audit

先扫描所有 review/memory/plan 相关字段与写入路径，确定：

- current owner；
- target owner；
- duplicate truth；
- migration/delete strategy。

若发现无法安全确定语义，报告 SPEC GAP，不猜。

### T2 — ReviewSchedule Repository

实现 learner × KnowledgeUnit versioned ReviewSchedule。

### T3 — Memory Baseline

实现 FSRS-compatible 或现有依赖条件下的等价可解释 baseline，并保留简单 baseline 可测试。不得为了本任务新增大型第三方依赖；若必须新增，先 SPEC GAP。

### T4 — Valid Review Observation

从 EXEC-004 的 LearnerEvidence/AssessmentResult 映射：

- independent recall；
- hinted/assisted；
- answer exposed；
- failure；
- delay。

### T5 — Due Projection

`due/overdue` 基于时间 + latest schedule 派生，不通过无意义写 row 表示时间流逝。

### T6 — Minimal Planner

建立首期 SYS06：confirmed goal/objective + prerequisite feasibility + mastery gap + review urgency + time budget → LearningActivity plan。

只需满足首个 vertical slice，不建设复杂 curriculum optimizer。

### T7 — Integration

SYS07 发布 due candidate；SYS06 将其转换成 `DELAYED_REVIEW` LearningActivity。SYS06 不修改 memory state。

### T8 — Persistence/Restart

应用重启后 ReviewSchedule 与 plan version 可恢复，pending due task 不丢。

## Acceptance Criteria

- `EXEC005-AC-001`：`SYS07-AC-001～007` 全部通过。
- `EXEC005-AC-002`：`SYS06-AC-001～007` 中首期适用项通过。
- `EXEC005-AC-003`：代码库 canonical `next_due_at` 只有 SYS07 一个写入者。
- `EXEC005-AC-004`：Planner 纳入 due review 不改变 ReviewSchedule。
- `EXEC005-AC-005`：independent recall 与 answer-exposed 对 schedule 更新不同。
- `EXEC005-AC-006`：重启后 schedule/plan 仍可查询且 pending work 恢复。
- `EXEC005-AC-007`：固定 input/version 的 scheduler/planner 可 deterministic replay。

## Required Tests

```bash
cd apps/backend
pytest tests -k "review or planner or schedule or replay or recovery"
pytest
ruff check app tests
mypy app
```

必须新增 ownership test，扫描/断言 `next_due_at` 不存在多个 canonical write path。

## Completion Report

额外报告：

- 搜索到的旧 review/memory/plan 写入点；
- 已迁移与仍待迁移列表；
- scheduler baseline/model version；
- planner scoring factors/version。
