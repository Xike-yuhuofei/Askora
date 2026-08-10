# Askora Execution Plans

> 状态：既有 UI-02C、P1-01～05、P1-07 等基线已完成；当前存在独立 active/blocked 队列  
> Active / Frozen Queue：EXEC-042、EXEC-043～046
> UI-03 implementation chain：`EXEC-1062 DONE → EXEC-043 → EXEC-044 → EXEC-045 → EXEC-046`

本目录保存可直接交给 Codex 执行的工程任务合同，以及完成后的不可变归档。EXEC 只能拆解已经冻结的 Spec/Vertical Slice，不能修改 Design、ADR 或 Spec 语义。

```text
Accepted ADR / Canonical Design
→ Spec
→ Vertical Slice
→ EXEC
→ Code / Test
→ Release Evidence
```

## 1. Active / Frozen Queue

| EXEC | Task | Status | Dependency / Concurrency |
|---|---|---|---|
| [EXEC-042](active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md) | v0.3 Production Sequential Teaching Policy Closure | FROZEN / ACTIVE | backend/policy 独立任务域 |
| [EXEC-043](active/EXEC-043-ui-03a-shell-routes-learning-domain.md) | UI-03A Shell, Routes and Learning Domain | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-1062 DONE |
| [EXEC-044](active/EXEC-044-ui-03b-today-primary-hierarchy.md) | UI-03B Today Primary Hierarchy | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-043 DONE |
| [EXEC-045](active/EXEC-045-ui-03c-library-progressive-disclosure.md) | UI-03C Library Progressive Disclosure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-044 DONE |
| [EXEC-046](active/EXEC-046-ui-03d-settings-legacy-release-closure.md) | UI-03D Settings / Legacy / Release Closure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-045 DONE |

### Concurrency Rule

`EXEC-042` 只处理 backend Teaching Policy production closure，可与 P1-06/UI 文档治理并行，但不得扩大到 frontend Interaction Architecture。

UI-03 四个 EXEC 必须严格串行：

```text
EXEC-1062 DONE
    ↓
EXEC-043 Shell / Routes / Learning
    ↓
EXEC-044 Today
    ↓
EXEC-045 Library
    ↓
EXEC-046 Settings / Cleanup / Release
```

原因：EXEC-1062 与 UI-03 在 `App.jsx`、Settings、route tests 和 UI Specs 上存在文件重叠；并行实现会产生不可审计覆盖。

## 2. Current Baseline

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 Adaptive Teaching Loop historical implementation | EXEC-007～013 | DONE / historical snapshot |
| v0.3 Production Sequential Teaching Policy Closure | EXEC-042 | FROZEN / ACTIVE |
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
| P1-04A/B/C Library Management | EXEC-031～033 | DONE |
| P1-05 Identity / Recovery / Deletion | EXEC-034～036 + integration EXEC-037 | DONE |
| P1-07 Error Recovery Center | historical EXEC-037 task-domain file | DONE |
| P1-01 Goal Management | EXEC-038～039 | DONE |
| P1-02 Model Settings | EXEC-040～041 | DONE |
| P1-03 Data Control and Recovery | EXEC-1031～1034 | DONE |
| P1-06 Onboarding Readiness Foundation | EXEC-1061 | DONE |
| P1-06 Onboarding Product Closure | EXEC-1062 | DONE |
| UI-03 Interactive Element System Refactor | EXEC-043～046 | FROZEN / BLOCKED |

## 3. UI-03 Governance Chain

```text
Interactive Element System Canonical Design Delta
→ ADR-0014 accepted
→ UI-IES / UI-IA / UI-SCREEN / UI-VIS / UI-QUAL frozen
→ UI-03 Vertical Slice frozen
→ EXEC-043 → 044 → 045 → 046
→ UI-03 Release Evidence
```

UI-03 只改变 information architecture、interaction hierarchy、presentation exposure 与 route organization。不得改变 SYS01～SYS08 ownership、TeachingAction、LearningPlan、LearnerState、ReviewSchedule 或 P1-02/03/05/07 security/data semantics。

## 4. v0.3 Current Conformance Closure

当前 v0.3 production conformance 仍由 EXEC-042 独立管理。UI-03 不得借 Interaction Architecture 任务修复或改写 Teaching Policy。

Engineering、Policy Correctness 与 Learning Evidence 必须继续独立报告；UI 改善不得改变 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 5. Book-to-Learning Historical Chain

```text
EXEC-016 DONE
→ EXEC-017
→ EXEC-018
→ EXEC-019
   ├→ EXEC-020 ─┐
   └→ EXEC-021 → EXEC-022
                 ↓
              EXEC-023
                 ↓
              EXEC-024
```

EXEC-017～024 均已完成并归档，保持历史原貌。

## 6. P1-06 → UI-03 Boundary

P1-06B 只完成首次用户 journey、default entry、deep-link preservation、Settings reopen 与真实 owner capability integration。

执行 EXEC-1062 时必须使用最新 ADR-0014 UI contracts，但不得提前实施完整 UI-03。P1-06B 完成并归档后，EXEC-043 才能开始全局 IA migration。

## 7. Queue Contract

- 每个 EXEC 只能在自身 dependency gate 满足后执行；
- 后序依赖未 DONE 时返回 `BLOCKED_BY_DEPENDENCY`；
- active EXEC 不得互相扩大 Allowed Files 或混合 commit；
- 公共语义、owner、schema、生产依赖出现未冻结选择时按 `AGENTS.md` 报告 `BLOCKED_BY_SPEC_GAP`；
- 每个 EXEC 完成后先满足自身 AC / Required Tests / DoD，再移入 `completed/`；
- completed EXEC 保持不可变历史证据。

## 8. New EXEC Requirements

每份新 EXEC 必须包含：Objective、Dependencies、Required Specs、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests、Completion Report Format。

执行前必须读取根 `AGENTS.md`、本 EXEC 引用的全部 Spec，并核对当前代码和 Git 状态。不得通过删除测试、弱化断言、frontend-only state 或 legacy shortcut 伪造完成。
