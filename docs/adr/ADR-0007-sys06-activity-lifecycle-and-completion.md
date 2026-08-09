# ADR-0007 — SYS06 Activity Lifecycle and Completion

Status: accepted
Date: 2026-08-09
Decision owner: Codex under the user's explicit authorization to execute the accepted product-completion plan
Decision authority: user-delegated Codex
Affected specs: `docs/specs/domain/lifecycle-state-machines.md`, `docs/specs/systems/06-activity-lifecycle.md`, `docs/specs/ui/data-contracts.md`, `docs/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md`

## Context

Askora 已能生成、选择和执行 `LearningActivity`，并能恢复 exact activity transcript，但当前 `LearningActivity.payload.status` 只是计划生成时的快照；`ActivitySelected` 与 transcript 也都不拥有 plan progression 或 activity completion。前端因此无法可靠回答三个基础问题：活动是否已经开始、能否恢复、何时真正完成并推进下一项。

直接根据“存在对话”“最后一条回复成功”或前端 local state 推断完成，会让 SYS08 transcript 或 UI 变成第二个 SYS06 truth。原地覆盖 activity payload 又会丢失状态历史、破坏并发控制和 replay。

## Decision

建立 SYS06-owned、append-only、versioned `LearningActivityStateV1` 生命周期流，作为活动当前状态的唯一 canonical source：

- `LearningActivity` 继续是 immutable plan definition；其 payload 中的 `status` 只表示创建时 initial/legacy snapshot，cutover 后不得原地更新；
- 每个 activity 在创建 plan 时同事务创建 lifecycle state v1；最新 lifecycle version 决定 current status；
- `SelectNextLearningActivity` 只可把 canonical plan order 中 eligible activity 从 `planned` 转为 `available`；
- `StartLearningActivityV1` 由 SYS06 执行 `available → active`，要求 expected lifecycle version 与 idempotency key；成功后 UI 通过 stable `/learn/{activity_id}` 路由进入或恢复 SYS08 execution projection；
- `CompleteLearningActivityV1` 由用户显式触发，但由 SYS06 验证 owner、版本、activity type 与 type-specific completion precondition 后执行 `active → completed`；
- UI-02C 第一版只允许 transcript-backed `learn_new`、`prerequisite_remediation`、`practice`、`metacognitive_review` 使用 `learner_finished`，并要求至少一个 accepted transcript turn；diagnostic、delayed review 与 transfer check 必须由未来冻结的 evaluator-owned evidence ref 完成，客户端不得绕过；
- 完成 activity 只表示该计划任务的执行结束，不表示 objective satisfied、goal achieved 或 mastery changed；
- 完成后 SYS06 在同一事务中按 immutable plan order 将下一 eligible `planned` activity 置为 `available`；没有剩余非终态 activity 时可把 plan 置为 `completed`，但不得自动把 goal 置为 `achieved`；
- 每次转换同时写 canonical state version 与 SYS06-owned durable `ActivityAvailable|ActivityStarted|ActivityCompleted` event/outbox；重复幂等键返回原结果，expected version 不符返回稳定 conflict；
- API/Query/UI 只读 latest lifecycle state，不从 transcript、legacy payload 或 event recency重新推导 current status。

## Alternatives

### 原地修改 `LearningActivity.payload.status`

拒绝。它没有 activity-level version、optimistic concurrency 或历史状态链，无法可靠审计与恢复。

### 只把 `LearningEvent` ledger 当作 current state

拒绝。ledger 可托管事件，但无明确 current projection、迁移与并发语义；每个读方自行折叠事件会形成多套状态解释。事件保留审计，SYS06 lifecycle stream 是 current truth。

### 把 transcript 存在视为 active，把最后回复视为 completed

拒绝。SYS08 transcript 是执行投影，不拥有 plan progression；模型/基础设施成功也不等于用户完成活动。

### 完成活动时同时更新 mastery 或 goal achievement

拒绝。MasteryEstimate 属 SYS03；goal achievement 需要独立 SYS06 目标达成合同。Activity completion 不能偷渡学习效果结论。

## Invariants

- lifecycle state 与 transition command 只有 SYS06 可写；SYS08/UI 只能提交受限 command 或 source ref。
- `completed != mastered != objective satisfied != goal achieved`。
- system/provider failure 不得完成活动，也不得形成负向 learner evidence。
- current-user ownership必须经 goal→plan→activity owner chain 验证；未授权与不存在保持不可枚举。
- 同一 activity/version/idempotency 只产生一个 state transition、event 与 next-availability side effect。
- transcript 只作 completion precondition ref，不被复制成 SYS06 内容事实。

## Migration and Rollback

新增 lifecycle table 与唯一约束 `(activity_id, version)`。代表性 backfill 规则固定为：

1. 有 accepted transcript turn → `active`；
2. 无 transcript 但有 owner-valid `ActivitySelected` → `available`；
3. 否则使用 immutable activity payload 的 initial status；
4. 历史 `completed` 不从对话或模型结果推断；只有已有 owner-valid completion event 才可 backfill completed。

迁移期间 read adapter 先读 lifecycle，缺失才返回 `LEGACY_ACTIVITY_STATE_UNMIGRATED`，不得静默写回。所有新 plan 必须原子创建 lifecycle v1；旧 payload writer 在 cutover 后停止更新 status。回滚保留 append-only lifecycle/event 数据，旧版本可继续读取 initial payload，但不得声称能看到最新 progression；优先 forward-fix。

## Validation

- schema/transition/property tests 覆盖所有允许与禁止转换；
- SQLite/PostgreSQL migration、代表性 backfill、rollback/forward-fix 与 reconciliation；
- duplicate idempotency、optimistic conflict、并发 start/complete、事务 outbox 与 restart recovery；
- cross-user、stale plan、superseded activity、missing transcript、provider failure 与 evaluator-required activity fail closed；
- real browser 验证 Today/Path → start/resume → complete → next activity；刷新和重启后状态一致；
- Engineering 与 Policy/Ownership Gate 单独报告；Learning Evidence 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`。
