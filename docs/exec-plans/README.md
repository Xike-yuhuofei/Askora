# Askora Execution Plans

> 本目录保存可直接交给 Codex 执行的工程任务合同，以及已完成任务的不可变归档。

## 1. 权威性

EXEC Plan 不能修改 Design/Spec 语义，只能把已冻结规范拆成实现步骤。

```text
Spec > ADR > EXEC > Code
```

若 EXEC 与 Spec 冲突，以 Spec 为准并报告 `SPEC GAP`。

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

执行完成后按 `docs/specs/quality/definition-of-done.md` 返回 `DONE | PARTIAL | BLOCKED_BY_SPEC_GAP`。

## 5. v0.2 状态

`EXEC-001` ～ `EXEC-006` 已于 2026-08-07 完成并归档，v0.2 First Vertical Learning Loop 已冻结为基线。

权威收口记录：

- `docs/exec-plans/completed/README.md`
- `docs/releases/v0.2-first-vertical-learning-loop.md`

当前 `active/` 无 v0.2 EXEC。下一阶段必须先完成 v0.3 顶层设计与 Spec 增量，再生成新的 EXEC；不得由 Codex 直接从 v0.2 实现自行推导新架构。
