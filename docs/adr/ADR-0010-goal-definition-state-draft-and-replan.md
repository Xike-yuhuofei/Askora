# ADR-0010 — Goal Definition, State, Draft and Safe Replan

> Status: Accepted
> Date: 2026-08-09
> Decision authority: user-delegated Codex
> Authorized objective: P1-01 目标管理完整闭环

## Context

现有 `LearningGoalV1` 把不可变目标内容与当前状态放在同一 payload，并且 Book Learning 只支持
单资料快捷创建。目标修订、跨资料选择、显式 target、焦点目标和活动边界切换没有公共合同。

## Decision

1. SYS06 分离 `LearningGoalDefinitionV2` 与 append-only `LearningGoalStateV1`；旧
   `LearningGoalV1.status` 只保留 legacy initial snapshot。
2. 用户输入先写 `LearningGoalDraftV1`；确认前必须通过资料可执行性、成功标准可测性和显式
   target 确认门禁。
3. `GoalChangePreviewV1` 固定 exact Goal/Mapping/Plan/Activity/Source/Learner refs、字段 diff、
   target 与计划影响。所有 command 使用 expected version、idempotency key、correlation id。
4. 意图、能力、成功标准、资料或 target 变化创建新 mapping/subgraph/plan versions；仅预算或
   deadline 变化复用 exact target evidence，不重新让模型猜 target。
5. 无 active activity 时原子切换 definition/mapping/plan/state；存在 active activity 时进入
   `approved_pending_boundary`。完成活动后在同一 SYS06 progression 优先应用；显式“结束并切换”
   把旧 activity 标 `superseded`，保留 transcript 且不产生学习证据。
6. SYS06 维护 `FocusedLearningGoalStateV1`。重点目标终止或暂停时清空，不自动猜选下一个。
7. 单资料 Book Learning 只作为 canonical draft/apply service 的兼容 adapter；退休条件是前端调用
   全部迁移且 adapter equivalence tests 通过。

## Alternatives

- 原地 PATCH `LearningGoalV1`：拒绝，会把历史定义和当前状态混成 last-write-wins。
- 活动进行中立即替换计划：拒绝，会破坏 transcript/activity exact refs。
- 自动选择最高分 target 或下一个 focus：拒绝，会把模型/排序建议冒充用户意图。

## Migration and rollback

按 semantic fingerprint 回填 Definition；candidate-only 变 draft；其余状态回填 State；旧 payload
只读兼容。新写只走 Definition/State/Draft。迁移可 downgrade 新表而保留全部 legacy goal、mapping、
plan、activity/event 历史；已应用新版本使用 forward-fix，不回写历史。

## Invariants

- 一个 goal 只有一个 effective definition、mapping 和 current plan。
- stale preview 不终止旧活动/计划。
- SYS06 是唯一 writer；LLM 只能给候选。
- cross-user source/goal/preview 不可枚举。
