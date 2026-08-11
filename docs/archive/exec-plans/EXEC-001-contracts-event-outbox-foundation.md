# EXEC-001 — Contracts + Event/Outbox Foundation

> Priority：P0  
> Status：READY_FOR_CODEX  
> Depends on：none

## Objective

建立 v0.2 后续所有实现共同依赖的公共合同、LearningEvent ledger、Transactional Outbox、幂等和基础架构测试；不改变现有用户可见教学行为。

## Required Specs

必须读取：

- `AGENTS.md`
- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/interfaces/schema-versioning.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/definition-of-done.md`

## Current Reality

仓库已有 SQLAlchemy/Alembic、SQLite/PostgreSQL 支持、Redis、Kafka/worker 等历史基础设施，但 v0.2 本地闭环不能依赖 Redis/Kafka 才可工作。当前公共事件/DecisionTrace/owner repository 合同尚未形成统一实现。

## Allowed Files

优先允许：

```text
apps/backend/app/contracts/**                 # 新建
apps/backend/app/infrastructure/**            # 新建或按现有结构适配
apps/backend/app/models/**                    # 仅新增必要 persistence models
apps/backend/app/workers/**                   # durable task/outbox adapter
apps/backend/alembic/**                       # 实际路径以仓库为准
apps/backend/tests/contracts/**               # 新建
apps/backend/tests/infrastructure/**          # 新建
apps/backend/tests/architecture/**            # 新建
```

如仓库迁移目录名称不同，可使用真实等价路径。不得借本任务重构八类系统业务逻辑。

## Forbidden Changes

- 不修改教学策略；
- 不修改 mastery 算法；
- 不改变 dialog/orchestrator 行为；
- 不引入微服务/Kafka 作为本地必需依赖；
- 不新增生产依赖，除非出现 SPEC GAP 并获得新 Spec/ADR；
- 不建立一个八类系统都可以随意 patch 的共享 JSON state。

## Implementation Tasks

### T1 — Public Contracts

使用 Pydantic/domain models 实现至少：

```text
LearningEventEnvelope v1
DecisionTrace v1
AssessmentResult v1
LearnerEvidence v1
MasteryEstimate v1
TeachingAction v1
EvidenceBundle v1
LearningPlan/Activity minimal v1
ReviewSchedule v1
```

跨模块字段语义必须与 Spec 一致。

### T2 — Event Ledger

实现 append-only event repository：

- unique event_id；
- aggregate id/version unique；
- sequence/version；
- idempotency key；
- schema/provenance/trace/privacy metadata；
- query/replay API。

### T3 — Decision Ledger

实现 append-only DecisionTrace repository/index；业务系统只能提交 payload，ledger 不修改 selected decision。

### T4 — Transactional Outbox

实现 durable outbox/task table：

```text
id
type
schema_version
payload
status
idempotency_key
attempt_count
next_attempt_at
last_error
created_at
updated_at
```

提供 producer + worker/recovery skeleton。

### T5 — SQLite Baseline

确保没有 Redis/Kafka 时 event/outbox 核心功能可运行。

### T6 — Architecture Tests

至少使用 Python AST/import inspection 建立以下规则回归：

- API 不直接 import learner/mastery repository；
- Assessment 不允许直接写 learner repository（允许未来 public command/evidence contract）；
- Orchestration 不允许直接写 learner/plan/review repository；
- domain/contracts 不依赖 FastAPI/Redis/Kafka/provider SDK。

初期可对当前 legacy 做 allowlist，但 allowlist 必须逐项写清 TODO owner/EXEC 删除任务，不能 `**/*` 全放行。

### T7 — Migration Tests

建立 representative SQLite fixture：upgrade → 写 event/outbox → reopen/restart → pending task 仍存在。

## Acceptance Criteria

- `EXEC001-AC-001`：`EVENT-AC-001/002/005/007` 通过。
- `EXEC001-AC-002`：同 idempotency key 重试不创建第二事件/任务。
- `EXEC001-AC-003`：状态+outbox 同事务原子性有 integration test。
- `EXEC001-AC-004`：关闭 Redis/Kafka 后 SQLite event/outbox tests 仍通过。
- `EXEC001-AC-005`：DecisionTrace append-only 且可按 trace/entity/version 查询。
- `EXEC001-AC-006`：architecture tests 已建立并能对一个故意违规 fixture 报错。
- `EXEC001-AC-007`：迁移后重启可恢复 pending task。
- `EXEC001-AC-008`：没有改变现有产品教学行为。

## Required Tests

至少运行：

```bash
cd apps/backend
pytest tests/contracts tests/infrastructure tests/architecture
pytest
ruff check app tests
mypy app
```

若全量存在既有失败，按 TEST-060 报告。

## Completion Report

严格使用 `definition-of-done.md` 模板，并额外列出：

- 新增数据库表/索引；
- architecture allowlist 中仍存在的 legacy 违规；
- 下一任务 EXEC-002 是否可开始。
