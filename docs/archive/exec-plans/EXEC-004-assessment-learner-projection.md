# EXEC-004 — Assessment → Evidence → Learner Projection

> Priority：P0  
> Status：READY_AFTER_EXEC-003  
> Depends on：EXEC-001, EXEC-002, EXEC-003

## Objective

建立首个可确定性评分的评估闭环，将 Attempt 与帮助状态转成 AssessmentResult，再由 SYS03 独立接纳 LearnerEvidence 并生成 canonical MasteryEstimate；停止任何“评分=掌握”的旧捷径。

## Required Specs

- `systems/03-learner-model.md`
- `systems/04-assessment.md`
- `domain/domain-model.md`
- `domain/event-contract.md`
- `architecture/state-ownership.md`
- `quality/testing-standard.md`
- `vertical-slices/v0.2-learning-loop.md`

## Current Reality

仓库已有：

```text
app/services/assessment/**
app/services/kt/**
app/services/dkt/**
app/models/assessment.py
app/models/profile.py
app/engines/quiz_engine.py
app/engines/drill_engine.py
```

这些历史模块必须收敛到：SYS04 单次测量 + SYS03 canonical learner projector；DKT 不得成为第二 truth。

## Allowed Files

```text
app/services/assessment/**
app/services/kt/**
app/services/dkt/**                 # 仅 challenger/adapter 降级
app/domains/assessment/**
app/domains/learner_model/**
app/contracts/**
app/models/assessment.py
app/models/profile.py               # 仅兼容迁移
app/infrastructure/**
app/engines/quiz_engine.py
app/engines/drill_engine.py
tests/**assessment**
tests/**knowledge**tracking**
tests/**mastery**
tests/**state_consistency**
tests/**replay**
```

## Forbidden Changes

- 不让 AssessmentService 直接更新 mastery；
- 不保留 KT/DKT 两套 canonical mastery；
- 不把 LLM confidence 直接当 mastery confidence；
- 不在本任务实现开放题复杂 judge；
- 不计算 ReviewSchedule。

## Implementation Tasks

### T1 — Deterministic Assessment Item

选择一个首期题型（优先 existing multiple_choice/numeric/exact）并实现版本化 AssessmentItem + deterministic grader。

### T2 — Attempt Assistance Snapshot

提交时冻结：hint level、assistance class、source visible、answer visible、response revision、response time。

### T3 — AssessmentResult

SYS04 生成结构化结果：score/correctness/error/independence/confidence/evaluator version/reason codes。

### T4 — Evidence Eligibility

SYS03 独立实现：

```text
AssessmentResult
→ accepted/rejected evidence
→ weight/dimension/novelty/delay
→ LearnerEvidence
```

完整答案已暴露/不可审计/版本错/重复结果必须拒绝或不给高权 mastery evidence。

### T5 — Canonical Projector

建立一个 baseline canonical learner projector。优先复用/重构现有 KT/BKT 能力；参数和算法版本化。

### T6 — DKT Demotion

明确 `services/dkt/` 只能 challenger/auxiliary；任何输出必须经 SYS03 接纳，不能直接写 canonical state。

### T7 — Compatibility Projection

若前端仍需 `DialogSession.mastery_estimate`，只能从 canonical MasteryEstimate 投影同步，不作为独立计算路径，并建立删除/迁移测试。

### T8 — Replay

固定 events/evidence + fixed algorithm version 重放，禁止在线 LLM。

### T9 — Dispute/Invalidation Skeleton

用户状态 dispute 或 invalidated evidence 能触发重算，而非直接 patch probability。

## Acceptance Criteria

- `EXEC004-AC-001`：`SYS04-AC-001/002/003/005/006/007` 通过。
- `EXEC004-AC-002`：`SYS03-AC-001/002/003/004/005/007` 通过。
- `EXEC004-AC-003`：独立、提示、答案暴露三类相同正确回答产生不同 evidence 结果。
- `EXEC004-AC-004`：任一 MasteryEstimate 完整追踪 item/Attempt/result/evidence/algorithm。
- `EXEC004-AC-005`：重放确定性且不发模型请求。
- `EXEC004-AC-006`：DKT 停止作为 canonical truth source。
- `EXEC004-AC-007`：基础设施评分故障不会记成用户答错。

## Required Tests

```bash
cd apps/backend
pytest tests -k "assessment or mastery or knowledge_tracing or state_consistency or replay"
pytest
ruff check app tests
mypy app
```

必须新增 table-driven evidence eligibility tests。

## Completion Report

额外报告：

- canonical mastery repository/projector 路径；
- BKT/KT baseline 参数版本；
- DKT 当前剩余用途；
- legacy `DialogSession.mastery_estimate` 是否仍存在及其只读语义。
