# Askora Completed Execution Plans

> v0.2 收口日期：2026-08-07  
> 状态：FROZEN BASELINE

## Completion Matrix

| EXEC | Final Status | Primary implementation commit |
|---|---|---|
| EXEC-001 — Contracts + Event/Outbox Foundation | DONE | `5d6682ee69e4fa16b039b5100c3eb916bb26e1d0` |
| EXEC-002 — Canonical Teaching Entry | DONE | `7d6012a1b3230f2af92c8dd2fc7eb278a76e58ab` |
| EXEC-003 — Content + EvidenceBundle | DONE | `020107dee53b5e9674591afcecaef7f7f725763c` |
| EXEC-004 — Assessment → Evidence → Learner Projection | DONE | `290d6a5bc23d717701acd7c2f8b66b2012a68dd3` |
| EXEC-005 — Review Scheduler + Planner Integration | DONE | `d18ef3331f78cccdfde9147037127247629414d2` |
| EXEC-006 — v0.2 E2E / Recovery / Security Gate | DONE | `bc5d8bb184ef7f49ac631729d4a8739482562a23` |

## Release Gate

`Release Gate: PASS`

最终 gate 提交新增/收敛了：

- v0.2 canonical E2E；
- independent / assisted / answer-exposed evidence 语义；
- deterministic learner replay；
- restart / outbox recovery；
- migration / rollback-forward-fix 回归；
- prompt injection、answer leakage、unauthorized tool、path traversal、secret leakage 安全回归；
- citation / missing evidence 防伪造；
- real-model gate result。

真实模型记录：

```text
provider: deepseek
model: deepseek-chat
prompt_version: explain-evidence/1.0
result: success
```

详细审计与遗留债务见：`docs/releases/v0.2-first-vertical-learning-loop.md`。

## Historical Contract Rule

归档后的 EXEC 文件保持执行前任务合同原貌，因此文件头中的 `READY_*` 字段属于历史元数据，不再代表当前状态。当前最终状态以本文件为权威记录。
