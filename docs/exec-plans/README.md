# Askora Execution Plans

> 本目录保存可直接交给 Codex 执行的工程任务合同，以及已完成任务的不可变归档。

## 1. 权威性

EXEC Plan 不能修改 Design/Spec 语义，只能把已冻结规范拆成实现步骤。

```text
Accepted ADR / Canonical Design
→ Spec
→ Vertical Slice
→ EXEC
→ Code
```

实现执行时以当前已冻结 Spec 为直接合同；若 EXEC 与 Spec/Accepted ADR 冲突，MUST 停止并报告 `SPEC GAP` / upstream conflict，不得由 Codex 自行重设计。

## 2. 目录

```text
active/      尚未完成或正在执行
completed/   已满足完成条件的历史任务合同与完成记录
```

任务进入 `completed/` 后，原 EXEC 文件作为历史执行合同保留，不回写或改写其执行前状态字段；最终状态、实现 commit、验证证据和遗留债务以 `completed/README.md` 与对应 Release Completion Report 为准。

## 3. 每份 EXEC 必须包含

- Objective；
- Dependencies；
- Required Specs；
- Current Reality；
- Allowed Files；
- Forbidden Changes；
- Implementation Tasks；
- Acceptance Criteria；
- Required Tests；
- Completion Report Format。

## 4. Codex 规则

Codex 开始任务前必须读取根 `AGENTS.md`、本 EXEC 引用的全部 Spec，并核对当前代码。不得只根据 EXEC 标题开始改代码。

通用约束：

- Codex 是执行者，不拥有 Canonical Design / ADR / Spec 决策权；
- 不允许以 legacy implementation 反向覆盖已冻结语义；
- 遇到无法在当前 Spec 内无歧义实现的公共语义，停止并报告 `BLOCKED_BY_SPEC_GAP`；
- 每个 EXEC 只能在其 Allowed Files / scope 内工作；
- 必须执行 Required Tests，并返回可核验 evidence；
- 未满足前一 EXEC 的 DONE gate，不得宣布后一 EXEC 完成。

执行完成后按 `docs/specs/quality/definition-of-done.md` 返回对应状态。

## 5. v0.2 Frozen Baseline

`EXEC-001` ～ `EXEC-006` 已于 2026-08-07 完成并归档，v0.2 First Vertical Learning Loop 已冻结为基线。

权威收口记录：

- `docs/exec-plans/completed/README.md`
- `docs/releases/v0.2-first-vertical-learning-loop.md`

v0.3 implementation MUST 复用 v0.2 已建立的 canonical learning facade、event/outbox/replay/recovery、assessment→learner projection、review/planner 与真实模型 gateway，不得创建第二套 canonical learning loop。

## 6. v0.3 Active Execution Sequence

上游已冻结：

```text
v0.3 Research Synthesis
→ v0.3 Canonical Design Delta
→ ADR-0001 / ADR-0002 Accepted
→ v0.3 Spec Delta PASS
→ v0.3 Adaptive Teaching Loop Vertical Slice PASS
→ 【active EXEC-007～013】
```

当前 active contracts：

| EXEC | Task | Entry Gate |
|---|---|---|
| `EXEC-007` | v0.3 Governance Preconditions | READY |
| `EXEC-008` | v0.3 Contracts + Schema Migration | after EXEC-007 DONE |
| `EXEC-009` | Deterministic Teaching Policy Kernel | after EXEC-008 DONE |
| `EXEC-010` | Adaptive Transition + Anti-Oscillation | after EXEC-009 DONE |
| `EXEC-011` | Cross-System Adaptive Execution Integration | after EXEC-010 DONE |
| `EXEC-012` | Outcome / Experiment / OPVE Foundation | after EXEC-011 DONE |
| `EXEC-013` | v0.3 E2E / Migration / Recovery / Security / Release Gate | after EXEC-012 DONE |

文件：

- `active/EXEC-007-v0.3-governance-preconditions.md`
- `active/EXEC-008-v0.3-contracts-schema-migration.md`
- `active/EXEC-009-deterministic-teaching-policy-kernel.md`
- `active/EXEC-010-adaptive-transition-anti-oscillation.md`
- `active/EXEC-011-cross-system-adaptive-execution.md`
- `active/EXEC-012-outcome-experiment-opve-foundation.md`
- `active/EXEC-013-v0.3-e2e-release-gate.md`

## 7. v0.3 Dependency Order

必须严格按：

```text
EXEC-007 governance preconditions
→ EXEC-008 contracts/schema/migration
→ EXEC-009 single-decision deterministic policy kernel
→ EXEC-010 sequential transition/anti-oscillation
→ EXEC-011 cross-system execution/actual assistance
→ EXEC-012 outcome/experiment/OPVE
→ EXEC-013 final system/release gate
```

禁止：

- 跳过 EXEC-007 的 `/users/profile` boundary 与 durable CI evidence；
- 跳过 EXEC-008 在旧 `strategy_id/scaffold_level/hint_level` contract 上直接堆 v0.3 policy；
- 把 EXEC-009 单次决策与 EXEC-010 sequential transition 混为不可测试模块；
- 让 SYS02/SYS08/LLM/legacy Socratic 在 EXEC-011 获得 final TeachingAction ownership；
- 在 EXEC-012/013 将 OPVE 或 synthetic learner 解释为真实学习效果证据。

## 8. v0.3 Completion Gate

`EXEC-013` 最终必须独立输出：

```text
Engineering Gate: PASS | FAIL
Policy Correctness Gate: PASS | FAIL
Learning Evidence Gate: PASS | FAIL | LEARNING_EVIDENCE_INSUFFICIENT
```

以下状态是合法且预期的首个 v0.3 engineering/policy slice 结果：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

它表示实现与 policy correctness 已达到冻结要求，但尚无充分真实 human learning efficacy evidence。不得据此声明 Adaptive Teaching Loop 已被证明优于 fixed strategy 或自由 LLM tutor。

只有 `EXEC-013` 满足其归档条件后，才将 `EXEC-007`～`EXEC-013` 移入 `completed/` 并创建 v0.3 release completion report。