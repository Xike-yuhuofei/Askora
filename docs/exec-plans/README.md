# Askora Execution Plans

> 状态：EXEC-016 active
> 已完成：EXEC-001～EXEC-015

本目录保存可直接交给 Codex 执行的工程任务合同，以及完成后的不可变归档。EXEC 只能拆解已经冻结的 Spec/Vertical Slice，不能修改 Design、ADR 或 Spec 语义。

```text
Accepted ADR / Canonical Design
→ Spec
→ Vertical Slice
→ EXEC
→ Code / Test
→ Release Evidence
```

## 1. 目录状态

| 目录 | 当前状态 | 规则 |
|---|---|---|
| `active/` | EXEC-016 | UI-02A Canonical Library and Scoped Knowledge Map |
| [`completed/`](completed/README.md) | EXEC-001～015 | 保留执行前任务合同原貌，不回写其 READY 字段 |

归档 EXEC 文件头中的 `READY_*` 是历史入口条件，不代表当前状态。最终状态、实现提交和验证证据以 [completed 索引](completed/README.md) 与 [Release Evidence](../releases/README.md) 为准。

## 2. 当前冻结基线

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 Adaptive Teaching Loop | EXEC-007～013 | DONE |
| v0.3.1 Rich Response Rendering | EXEC-014 | DONE |
| UI-01 Learning Shell and Compatibility Tutor Workspace | EXEC-015 | DONE |
| UI-02A Canonical Library and Scoped Knowledge Map | EXEC-016 | ACTIVE |

v0.3 最终状态：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

这表示实现与 policy correctness 达到当次冻结要求，不表示 Adaptive Teaching Loop 已被证明改善真人学习效果。

## 3. 新 EXEC 要求

每份新 EXEC 必须包含：Objective、Dependencies、Required Specs、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests 和 Completion Report Format。

执行前必须读取根 `AGENTS.md`、本 EXEC 引用的全部 Spec，并核对当前代码和 Git 状态。遇到无法在现有 Spec 内无歧义实现的公共语义，必须报告 `BLOCKED_BY_SPEC_GAP`；不得由执行代理自行重设计。

只有满足前一任务的 DONE gate 才能进入后续依赖任务。完成后按 [Definition of Done](../specs/quality/definition-of-done.md) 返回状态，并将任务移入 `completed/`。
