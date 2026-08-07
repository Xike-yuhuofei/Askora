# Askora Definition of Done

> Spec ID：`DOD-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 通用完成定义

Codex 只有在以下全部满足时才能报告任务 `DONE`：

### DOD-001 — Scope

- EXEC Plan 指定的 Acceptance Criteria 全部满足；
- 只修改允许范围，额外修改有必要性说明；
- 无未声明的公共 API/Schema/数据库语义变化。

### DOD-002 — Architecture

- 未违反 `ARCH-*`、`DEP-*`、`STATE-*`；
- 没有新增第二事实源；
- 没有新增绕过 canonical orchestrator 的教学路径；
- legacy adapter 有明确迁移目的，不成为永久新架构。

### DOD-003 — Data

- 新状态有明确 owner；
- 关键更新可追溯 event/evidence/decision；
- 幂等、并发、版本和 migration 语义已实现；
- durable task/outbox 对需要恢复的工作有效。

### DOD-004 — AI

- 模型/Prompt/schema/version 可追踪；
- fallback 不改变领域语义；
- Prompt Injection / answer leakage / tool authorization 防线未被绕过；
- Mock 未被当成真实模型连接证据。

### DOD-005 — Tests

- 新增关键行为有自动化测试；
- targeted tests 通过；
- 全量适用测试已运行或明确报告既有失败；
- lint/type/build 按任务范围执行；
- 不通过 skip/delete/weaken tests 伪造完成。

### DOD-006 — Failure

- timeout、invalid input、dependency failure、retry exhausted 等适用失败路径有定义和测试；
- 系统故障不会被记录为学习者错误；
- retry 对 side effects 幂等。

### DOD-007 — Observability

- 新关键决策/事件/模型调用有 trace；
- 新 error 使用稳定 code；
- 日志不泄漏 secret/不必要敏感内容。

### DOD-008 — Documentation

如果实现改变已冻结的公共行为，Codex MUST 停止并报告 SPEC GAP；不得先改代码后补文档。

## 2. Codex 结果格式

每个 EXEC 完成后必须返回：

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Implemented:
- ...

Spec/AC coverage:
- RULE-ID → test/file

Files changed:
- ...

Migrations:
- ... / none

Tests run:
- command → result

Existing unrelated failures:
- ... / none

SPEC GAP:
- ... / none

Remaining risks:
- ... / none
```

## 3. PARTIAL

### DOD-020

如果大部分工作完成但存在无法在当前 Spec 下安全实现的缺口，必须标 `PARTIAL` 或 `BLOCKED_BY_SPEC_GAP`，不能称 DONE。

## 4. 真实 E2E

### DOD-030

涉及 LLM gateway/orchestrator “已接通”的任务，至少一次真实已配置模型调用成功才可完成对应 AC。普通 unit/integration 测试仍应主要使用 Mock。

## 5. Migration Done

数据库/状态迁移只有在以下满足后才完成：

- migration 可执行；
- representative fixture backfill 正确；
- owner truth 明确；
- reconciliation test 通过；
- legacy write path 关闭或有明确关闭条件；
- rollback/forward-fix 明确。

## 6. Forbidden Completion Claims

禁止把以下情况称 DONE：

- 留下关键 `TODO/pass/NotImplemented`；
- 只有 Mock 但声称真实模型可用；
- 测试未运行却说“应该通过”；
- 删除失败测试；
- 发现 Spec 冲突后自行选方案；
- 新旧两套 truth 双写但无 reconciliation/删除条件；
- 仅 UI 看起来正常但事件/证据/状态链未接通。
