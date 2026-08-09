# Askora Execution Plans

> 状态：EXEC-030 DONE；P1-04 已完成；P1-06 按独立冻结队列推进
> Active：EXEC-038（P1-01B）；EXEC-1062 等待自身依赖 gate
> 已完成：EXEC-001～EXEC-033

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
| `active/` | [EXEC-038](active/EXEC-038-p1-01b-goal-lifecycle-achievement.md)、[EXEC-1062](active/EXEC-1062-p1-06b-onboarding-product-closure.md) | P1-01 为 037→038；P1-06 为 1061→1062；不得越过依赖或已冻结 owner 边界 |
| [`completed/`](completed/README.md) | EXEC-001～033 | 保留执行任务合同及其显式决策记录 |

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
| UI-02B2 Guided Book Learning | EXEC-026 | DONE |
| UI-02B3 Real-model Guided Learning | EXEC-027 | DONE |
| Zhipu Development Model Integration | EXEC-028 | DONE |
| UI-02B Goals, Learning Path and Evidence | EXEC-029 | DONE |
| UI-02C Canonical Activity Lifecycle | EXEC-030 | DONE |
| P1-04A Library Search and Organization | [EXEC-031](completed/EXEC-031-p1-04a-library-organization.md) | DONE |
| P1-04B Library Deduplication | [EXEC-032](completed/EXEC-032-p1-04b-library-deduplication.md) | DONE |
| P1-04C Scanned PDF OCR Review | [EXEC-033](completed/EXEC-033-p1-04c-library-ocr-review.md) | DONE |
| P1-01A Goal Definition, Draft and Safe Replan | [EXEC-037](completed/EXEC-037-p1-01a-goal-definition-draft-replan.md) | DONE |
| P1-01B Goal Lifecycle and Evidence-gated Achievement | EXEC-038 | FROZEN / ACTIVE |
| P1-06 Onboarding Readiness Foundation | [EXEC-1061](completed/EXEC-1061-p1-06a-onboarding-readiness-foundation.md) | DONE |
| P1-06 Onboarding Product Closure | EXEC-1062 | FROZEN / BLOCKED_BY_DEPENDENCY_GATE |

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

P1-06 dependency graph：

```text
ADR-0106 + ONBOARD Spec + UI-02C DONE
        ↓
    EXEC-1061
        ↓
P1-02/P1-03/P1-07 integration gate
        ↓
    EXEC-1062 → P1-06 DONE
```

用户于 2026-08-09 显式采纳事实驱动 onboarding，并授权真正关闭 P1-06。EXEC-1061 可独立实现
preference/readiness foundation；EXEC-1062 必须等待真实依赖，不能用 placeholder 或 mock 绕过。

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
