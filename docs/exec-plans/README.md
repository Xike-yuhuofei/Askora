# Askora Execution Plans

> 状态：UI-02C、P1-01、P1-02、P1-03、P1-04、P1-05、P1-07 DONE；v0.3 sequential policy closure 与 P1-06B 按独立冻结队列推进  
> Active：EXEC-042（v0.3 Policy Correctness Closure）、EXEC-1062（P1-06B）  
> 已完成：EXEC-001～EXEC-041、EXEC-1031～1034、EXEC-1061（其中 EXEC-037 有两个历史任务域文件）

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
| `active/` | [EXEC-042](active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md)、[EXEC-1062](active/EXEC-1062-p1-06b-onboarding-product-closure.md) | 两个独立任务域；不得越过冻结 owner/spec 边界或混合 scope |
| [`completed/`](completed/README.md) | EXEC-001～041、EXEC-1031～1034、EXEC-1061（EXEC-037 含两个历史任务域文件） | 保留执行任务合同及其显式决策记录 |

归档 EXEC 文件头中的 `READY_*` 是历史入口条件，不代表当前状态。最终状态、实现提交和验证证据以 [completed 索引](completed/README.md) 与 [Release Evidence](../releases/README.md) 为准。

## 2. 当前冻结基线

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 Adaptive Teaching Loop historical implementation | EXEC-007～013 | DONE / historical snapshot |
| v0.3 Production Sequential Teaching Policy Closure | [EXEC-042](active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md) | FROZEN / ACTIVE |
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
| P1-05 Identity Credential and Durable Sessions | EXEC-034 | DONE |
| P1-05 Local Account Recovery | EXEC-035 | DONE |
| P1-05 Account Deletion and Erasure | EXEC-036 | DONE |
| P1-05 / P1-03 Canonical Erasure Integration | [EXEC-037](completed/EXEC-037-p1-05-p1-03-erasure-integration.md) | DONE |
| P1-07 Error Recovery Center | [EXEC-037](completed/EXEC-037-p1-07-error-recovery-center.md) | DONE |
| P1-01A Goal Definition, Draft and Safe Replan | [EXEC-038](completed/EXEC-038-p1-01a-goal-definition-draft-replan.md) | DONE |
| P1-01B Goal Lifecycle and Evidence-gated Achievement | [EXEC-039](completed/EXEC-039-p1-01b-goal-lifecycle-achievement.md) | DONE |
| P1-02A Secure Model Configuration Foundation | [EXEC-040](completed/EXEC-040-p1-02a-model-configuration-foundation.md) | DONE |
| P1-02B Model Settings Product Closure | [EXEC-041](completed/EXEC-041-p1-02b-model-settings-product-closure.md) | DONE |
| P1-03 Data Control and Recovery | EXEC-1031～1034 | DONE |
| P1-06 Onboarding Readiness Foundation | [EXEC-1061](completed/EXEC-1061-p1-06a-onboarding-readiness-foundation.md) | DONE |
| P1-06 Onboarding Product Closure | [EXEC-1062](active/EXEC-1062-p1-06b-onboarding-product-closure.md) | FROZEN / ACTIVE |

## 2A. v0.3 Current Conformance Closure

历史 v0.3 release snapshot 曾记录：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

该状态仅代表当时 release evidence。2026-08-10 的 current-main conformance audit 已重新判定：

```text
Engineering Gate: ENGINEERING_GATE_FAILED
Policy Correctness Gate: POLICY_CORRECTNESS_GATE_FAILED
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

冻结缺口：

```text
GAP-V03-001 — Production adaptive path bypasses SequentialTeachingPolicy
GAP-V03-002 — Production TeachingContext / sequential evidence hydration incomplete
```

对应唯一 P0 实现闭包为 [EXEC-042](active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md)。EXEC-042 不重写 Teaching Policy 算法，不修改 Canonical Design / ADR / Spec，不引入新的 durable TutorState；若现有 immutable owner facts 无法无歧义重建 sequential state，则必须返回 `BLOCKED_BY_SPEC_GAP`。

current Engineering Gate 还必须在 EXEC-042 之外重新获得 repository-wide 绿色 CI；EXEC-042 不允许混入审计中已识别的 scope 外 Black formatting 文件。

## 2B. P1-03 Execution Chain

```text
ADR-0103 + DATA-* + P1-03 Vertical Slice
→ EXEC-1031 Recovery Foundation
→ EXEC-1032 Verified Restore
→ EXEC-1033 User Data Export
→ EXEC-1034 Erasure / UX / Release Gate
```

P1-03 使用任务域保留编号，避免与并行 P1 工作流的普通连续编号碰撞。四个 EXEC 已按依赖顺序完成并使用独立本地 commit；验证证据见 [P1-03 Release Report](../releases/p1-03-data-control-recovery.md)。

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

EXEC-020 与 EXEC-021 在 EXEC-019 DONE 后并行完成；其余任务按 dependency gate 串行完成。当前没有新的 Book-to-Learning feature EXEC；EXEC-042 只修复 frozen v0.3 policy production composition，不重新设计 Book-to-Learning pipeline。

P1-05 dependency graph：

```text
ADR-0009 + IDP Spec
        ↓
    EXEC-034
        ↓
    EXEC-035
        ↓
    EXEC-036 → P1-05 DONE
```

用户于 2026-08-09 显式采纳 P1-05 推荐方案并授权完成实现。EXEC-034～036 已在冻结的 Allowed Files/owner 边界内串行完成；EXEC-037 已将账号删除收敛到 P1-03 canonical erasure single truth 并通过 PR CI。P1-05 当前为 DONE，证据见 `docs/releases/p1-05-account-lifecycle.md`。

P1-05/P1-03 integration 与 P1-07 在并行历史中都使用了 `EXEC-037`；两份已归档合同以完整文件路径区分，禁止据此重写已接受的合同或提交历史。

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

用户于 2026-08-09 显式采纳事实驱动 onboarding，并授权真正关闭 P1-06。EXEC-1061 可独立实现 preference/readiness foundation；EXEC-1062 必须等待真实依赖，不能用 placeholder 或 mock 绕过。

## 4. Queue Contract

- EXEC-042 与 EXEC-1062 属于两个独立任务域；不得互相扩大 Allowed Files 或借对方任务修改冻结语义。
- EXEC-042 只关闭 `GAP-V03-001` + `GAP-V03-002` 及对应 production-path tests/replay，不得混入 P1-06、Desktop/DMG、data-control Black formatting 或新教学算法。
- Book-to-Learning 历史实现从 EXEC-017 连续编号至 EXEC-024；这些 completed EXEC 保持历史原貌。
- 每个 EXEC 完成后必须先满足自身 Acceptance Criteria / Required Tests / DoD，再归档到 `completed/`。
- 后序依赖未 DONE 时应报告 `BLOCKED_BY_DEPENDENCY`，不得越序实现。
- 遇到公共语义、owner、schema、生产依赖等未冻结选择，按 `AGENTS.md` 报告 `BLOCKED_BY_SPEC_GAP`。
- Active EXEC 的文档生命周期由本索引治理；归档后进入 `completed/README.md` 与 release evidence 历史清单。

## 5. 新 EXEC 要求

每份新 EXEC 必须包含：Objective、Dependencies、Required Specs、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests 和 Completion Report Format。

执行前必须读取根 `AGENTS.md`、本 EXEC 引用的全部 Spec，并核对当前代码和 Git 状态。遇到无法在现有 Spec 内无歧义实现的公共语义，必须报告 `BLOCKED_BY_SPEC_GAP`；不得由执行代理自行重设计。

只有满足任务自己的 dependency gate 才能执行。完成后按 [Definition of Done](../specs/quality/definition-of-done.md) 返回状态，并将任务移入 `completed/`。
