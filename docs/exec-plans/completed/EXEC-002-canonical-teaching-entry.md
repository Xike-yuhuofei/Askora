# EXEC-002 — Canonical Teaching Entry

> Priority：P0  
> Status：READY_AFTER_EXEC-001  
> Depends on：EXEC-001

## Objective

让 `DialogService` 的普通/流式请求统一经过 canonical Orchestrator，并停止 Dialog/Engine/SharedContext 对 canonical mastery 的直接写入。

## Required Specs

- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/interfaces/api-contract.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/vertical-slices/v0.2-learning-loop.md`

## Current Reality

已核对当前代码：

1. `app/services/dialog/dialog_service.py::_send_message_unlocked` 通过 `_should_use_orchestrator()` 在 direct Socratic 与 Orchestrator 两条路径间切换；
2. direct path 用 `engine_output.mastery_delta` 直接修改 `session.mastery_estimate`；
3. Orchestrator path 从 `shared_ctx_snapshot.mastery_vector` 回写 `session.mastery_estimate`；
4. `_stream_message_unlocked` 当前直接调用 `SocraticEngine.stream_response()`，绕过 Orchestrator；
5. `api/v1/orchestrator.py` 目前是 debug/demo endpoint，并明确提示生产应经 DialogService 接入。

## Allowed Files

```text
apps/backend/app/services/dialog/**
apps/backend/app/engines/orchestrator.py
apps/backend/app/engines/base.py
apps/backend/app/engines/**                 # 仅必要 adapter/interface 改动
apps/backend/app/api/v1/dialog.py
apps/backend/app/api/v1/orchestrator.py     # 仅 debug/compat 调整
apps/backend/app/contracts/**
apps/backend/app/orchestration/**           # 如 EXEC-001 后建立
apps/backend/tests/**dialog**
apps/backend/tests/**orchestrator**
apps/backend/tests/**stream**
apps/backend/tests/architecture/**
```

## Forbidden Changes

- 不在本任务实现新 mastery 算法；
- 不把 `DialogSession.mastery_estimate` 改成另一个独立 truth；
- 不让 streaming 保留 direct Socratic 特例；
- 不把 engine switching 逻辑继续扩展成新的 Teaching Policy owner；
- 不改变 4.6 Planner/4.7 Review 语义。

## Implementation Tasks

### T1 — Canonical Facade

建立/确认一个 production application facade，例如：

```text
LearningOrchestrationFacade.run_turn(...)
LearningOrchestrationFacade.stream_turn(...)
```

名字可调整，但普通/流式必须共享同一领域决策入口。

### T2 — Dialog Adapter

`DialogService.send_message/stream_message` 只承担 session/message transport compatibility，并调用 canonical facade。

移除 `_should_use_orchestrator` 对生产业务路径的二选一意义。若 feature flag 暂时保留，只能用于 emergency rollback，并明确到期删除条件。

### T3 — Remove Direct Mastery Writes

移除：

```text
engine_output.mastery_delta → session.mastery_estimate
shared_ctx.mastery_vector → session.mastery_estimate
```

及等价路径。

若前端暂时读取 `DialogSession.mastery_estimate`，只能从 SYS03 canonical projection 同步只读值；若 EXEC-004 尚未实现，可明确返回 unavailable/legacy_readonly，不能继续计算新值。

### T4 — Streaming

流式必须执行与非流式同一 TeachingAction/engine selection，只有 response transport 不同。

### T5 — Orchestrator Session Persistence Boundary

当前 `get_orchestrator()` 内 `_sessions` 可暂保留运行时执行状态，但不得作为 learner truth。为应用重启持久化做好 port/interface，不要求本任务完成全部 session recovery。

### T6 — Legacy Socratic Adapter

现有 SocraticEngine 可作为 SYS08 execution adapter；其 `mastery_delta`/内部策略状态不能再成为跨会话 canonical state。

### T7 — Error Contract

普通/流式统一稳定 error code 与 correlation id；stream catch-all 不得把所有异常都压成固定 `STREAM-ERR` 而丢失领域 error code。

## Acceptance Criteria

- `EXEC002-AC-001`：`API-AC-001` 普通/流式同业务链通过。
- `EXEC002-AC-002`：`SYS08-AC-001/003` 通过。
- `EXEC002-AC-003`：代码中不存在 Dialog/Orchestrator 对 canonical mastery 的直接写入。
- `EXEC002-AC-004`：direct Socratic 不再是默认生产路径。
- `EXEC002-AC-005`：流式断开/重连不重复持久化用户消息/assistant completion。
- `EXEC002-AC-006`：模型执行失败不会修改 learner mastery。
- `EXEC002-AC-007`：现有前端会话接口保持兼容，任何字段降级有明确契约/test。

## Required Tests

```bash
cd apps/backend
pytest tests -k "dialog or orchestrator or stream or state_consistency"
pytest
ruff check app tests
mypy app
```

必须新增一个 architecture/behavior test，证明给 EngineOutput 注入巨大 `mastery_delta` 也不能改 canonical mastery。

## Completion Report

额外报告：

- 删除/保留的 legacy direct path；
- `DialogSession.mastery_estimate` 当前语义与删除计划；
- streaming/non-streaming canonical facade 的具体路径。
