# Askora Execution Plans

> 本目录保存可直接交给 Codex 执行的工程任务合同。

## 1. 权威性

EXEC Plan 不能修改 Design/Spec 语义，只能把已冻结规范拆成实现步骤。

```text
Spec > ADR > EXEC > Code
```

若 EXEC 与 Spec 冲突，以 Spec 为准并报告 `SPEC GAP`。

## 2. 目录

```text
active/      尚未完成或正在执行
completed/   已全部满足 AC，并保留最终 commit/验证记录
```

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

## 5. v0.2 执行顺序

```text
EXEC-001 contracts + event/outbox foundation
→ EXEC-002 canonical teaching entry
→ EXEC-003 content + EvidenceBundle
→ EXEC-004 assessment + learner projection
→ EXEC-005 review + planner integration
→ EXEC-006 E2E/recovery/security gate
```

前一任务未达到其阻断性 AC 时，后续任务不得通过临时绕过方式继续。
