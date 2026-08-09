# Askora Execution Plans

> 状态：UI-02C EXEC-030 FROZEN / BLOCKED_BY_DEPENDENCY；P1-03 DONE
> Active：EXEC-030
> 已完成：EXEC-001～EXEC-025、EXEC-029、EXEC-1031～1034

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
| `active/` | [EXEC-030](active/EXEC-030-ui-02c-canonical-activity-lifecycle.md) | EXEC-030 blocked |
| [`completed/`](completed/README.md) | EXEC-001～025、EXEC-029、EXEC-1031～1034 | 保留执行任务合同及其显式决策记录 |

归档 EXEC 文件头中的 `READY_*` 是历史入口条件，不代表当前状态。最终状态、实现提交和验证证据以 [completed 索引](completed/README.md) 与 [Release Evidence](../releases/README.md) 为准。

## 2. 当前冻结基线

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 Adaptive Teaching Loop | EXEC-007～013 | DONE |
| v0.3.1 Rich Response Rendering | EXEC-014 | DONE |
| UI-01 Learning Shell and Compatibility Tutor Workspace | EXEC-015 | DONE |
| UI-02A Canonical Library and Scoped Knowledge Map | EXEC-016 | DONE |
| Book-to-Learning SPEC-D01～D06 | EXEC-017～024 | DONE |
| UI-02B1 Material-to-Learning Launch | EXEC-025 | DONE |
| UI-02B Goals, Learning Path and Evidence | EXEC-029 | DONE |
| UI-02C Canonical Activity Lifecycle | EXEC-030 | FROZEN / BLOCKED_BY_DEPENDENCY |
| P1-03 Data Control and Recovery | EXEC-1031～1034 | DONE |

## 2A. P1-03 Execution Chain

```text
ADR-0103 + DATA-* + P1-03 Vertical Slice
→ EXEC-1031 Recovery Foundation
→ EXEC-1032 Verified Restore
→ EXEC-1033 User Data Export
→ EXEC-1034 Erasure / UX / Release Gate
```

P1-03 使用任务域保留编号，避免与并行 P1 工作流的普通连续编号碰撞。四个 EXEC 已按依赖顺序完成并使用独立本地 commit；验证证据见 [P1-03 Release Report](../releases/p1-03-data-control-recovery.md)。

v0.3 最终状态：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

这表示实现与 policy correctness 达到当次冻结要求，不表示 Adaptive Teaching Loop 已被证明改善真人学习效果。

## 3. Book-to-Learning EXEC Completion

| EXEC | Contract | Depends on | Status |
|---|---|---|---|
| EXEC-017 | [Structure-Preserving EPUB Ingestion & Source Replay](completed/EXEC-017-structure-preserving-epub-ingestion.md) | EXEC-016 DONE | DONE |
| EXEC-018 | [Multi-Granularity Content Model & Rebuildable Projections](completed/EXEC-018-multi-granularity-content-projections.md) | EXEC-017 DONE | DONE |
| EXEC-019 | [Canonical Knowledge Verification & Publication](completed/EXEC-019-knowledge-verification-publication.md) | EXEC-018 DONE | DONE |
| EXEC-020 | [Published Knowledge → Retrieval Projection & SYS02 Binding](completed/EXEC-020-retrieval-projection-sys02-binding.md) | EXEC-019 DONE | DONE |
| EXEC-021 | [LearningGoal Formation & Goal-to-Knowledge Mapping](completed/EXEC-021-learning-goal-knowledge-mapping.md) | EXEC-019 DONE | DONE |
| EXEC-022 | [Prerequisite Diagnostic Bootstrap & LearningPlan Handoff](completed/EXEC-022-prerequisite-diagnostic-planner-bootstrap.md) | EXEC-021 DONE | DONE |
| EXEC-023 | [Book-to-Adaptive Orchestration, Readiness & Additive API](completed/EXEC-023-book-learning-orchestration-api.md) | EXEC-020 + EXEC-022 DONE | DONE |
| EXEC-024 | [Book-to-Learning E2E, Replay, Security & Release Gate](completed/EXEC-024-book-to-learning-e2e-release-gate.md) | EXEC-023 DONE | DONE |

Dependency graph：

```text
EXEC-016 DONE
    ↓
EXEC-017
    ↓
EXEC-018
    ↓
EXEC-019
   ├────────→ EXEC-020 ────────┐
   └────────→ EXEC-021 → EXEC-022
                               │
EXEC-020 ──────────────────────┤
                               ↓
                           EXEC-023
                               ↓
                           EXEC-024
```

EXEC-020 与 EXEC-021 在 EXEC-019 DONE 后并行完成；其余任务按 dependency gate 串行完成。当前没有 active Book-to-Learning EXEC。

## 4. Queue Contract

- Book-to-Learning 本轮从 EXEC-017 连续编号至 EXEC-024，符合 SPEC-D06 编号治理。
- EXEC-017～024 只实现 SPEC-D01～D06；不得重新设计 v0.3 Adaptive Teaching Loop。
- 每个 EXEC 完成后必须先满足自身 Acceptance Criteria / Required Tests / DoD，再归档到 `completed/`。
- 后序 EXEC 在依赖未 DONE 时应报告 `BLOCKED_BY_DEPENDENCY`，不得越序实现。
- 遇到公共语义、owner、schema、生产依赖等未冻结选择，按 `AGENTS.md` 报告 `BLOCKED_BY_SPEC_GAP`。
- Active EXEC 的文档生命周期由本索引治理；归档后进入 `completed/README.md` 与 release evidence 历史清单。

## 5. 新 EXEC 要求

每份新 EXEC 必须包含：Objective、Dependencies、Required Specs、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests 和 Completion Report Format。

执行前必须读取根 `AGENTS.md`、本 EXEC 引用的全部 Spec，并核对当前代码和 Git 状态。遇到无法在现有 Spec 内无歧义实现的公共语义，必须报告 `BLOCKED_BY_SPEC_GAP`；不得由执行代理自行重设计。

只有满足前一任务的 DONE gate 才能进入后续依赖任务。完成后按 [Definition of Done](../specs/quality/definition-of-done.md) 返回状态，并将任务移入 `completed/`。
