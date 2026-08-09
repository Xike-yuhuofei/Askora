# Askora Completed Execution Plans

> v0.2 收口日期：2026-08-07
> v0.3 收口日期：2026-08-07
> v0.3.1 收口日期：2026-08-08
> UI-01 收口日期：2026-08-08
> UI-02A 收口日期：2026-08-08
> UI-02B1 收口日期：2026-08-08
> UI-02B Goals/Path/Evidence 收口日期：2026-08-09
> Book-to-Learning 执行日期：2026-08-08
> 状态：v0.2 + v0.3 + v0.3.1 + UI-01 + UI-02A + UI-02B1 + UI-02B Goals/Path/Evidence FROZEN BASELINES；Book-to-Learning EXEC-017～024 DONE

## Completion Matrix

| EXEC | Final Status | Primary implementation commit |
|---|---|---|
| EXEC-001 — Contracts + Event/Outbox Foundation | DONE | `5d6682ee69e4fa16b039b5100c3eb916bb26e1d0` |
| EXEC-002 — Canonical Teaching Entry | DONE | `7d6012a1b3230f2af92c8dd2fc7eb278a76e58ab` |
| EXEC-003 — Content + EvidenceBundle | DONE | `020107dee53b5e9674591afcecaef7f7f725763c` |
| EXEC-004 — Assessment → Evidence → Learner Projection | DONE | `290d6a5bc23d717701acd7c2f8b66b2012a68dd3` |
| EXEC-005 — Review Scheduler + Planner Integration | DONE | `d18ef3331f78cccdfde9147037127247629414d2` |
| EXEC-006 — v0.2 E2E / Recovery / Security Gate | DONE | `bc5d8bb184ef7f49ac631729d4a8739482562a23` |
| EXEC-007 — v0.3 Governance Preconditions | DONE | `c97e8ba` / CI evidence `eaa0883` |
| EXEC-008 — v0.3 Contracts + Schema Migration | DONE | `2ecc662` |
| EXEC-009 — Deterministic Teaching Policy Kernel | DONE | `67e3ef9` |
| EXEC-010 — Adaptive Transition + Anti-Oscillation | DONE | `82bb5b1` |
| EXEC-011 — Cross-System Adaptive Execution | DONE | `d95e0a4` |
| EXEC-012 — Outcome / Experiment / OPVE Foundation | DONE | `71d05a2` |
| EXEC-013 — v0.3 E2E / Release Gate | DONE | `530322e` |
| EXEC-014 — Rich Response Rendering | DONE | local implementation (not committed) |
| EXEC-015 — UI-01 Learning Shell and Compatibility Tutor Workspace | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-016 — UI-02A Canonical Library and Scoped Knowledge Map | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-017 — Structure-Preserving EPUB Ingestion & Source Replay | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-018 — Multi-Granularity Content Model & Rebuildable Projections | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-019 — Canonical Knowledge Verification & Publication Pipeline | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-020 — Published Knowledge → Retrieval Projection & SYS02 Binding | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-021 — LearningGoal Formation & Goal-to-Knowledge Mapping | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-022 — Prerequisite Diagnostic Bootstrap & LearningPlan Handoff | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-023 — Book-to-Adaptive Orchestration, Readiness & Additive API | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-024 — Book-to-Learning E2E, Replay, Security & Release Gate | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-025 — UI-02B1 Material-to-Learning Launch | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-029 — UI-02B Goals, Learning Path and Evidence | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |

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

## v0.3 Release Gates

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

v0.3 冻结的是 engineering/policy vertical slice，不是 human learning efficacy 结论。OPVE、G0/G1、synthetic learner 与真实模型连通性不得被解释为“adaptive teaching 已证明更有效”。

真实模型 v0.3 gate：

```text
provider: deepseek
model: deepseek-chat
prompt_version: v03-policy-bound-render/1.0
policy_bundle_version: policy-1
result: success
```

详细 DoD/AC、测试、迁移、恢复、安全、OPVE 和 evidence boundary 见：`docs/releases/v0.3-adaptive-teaching-loop.md`。

## UI-01 Release Gates

```text
Engineering Gate: PASS
Policy Correctness / Ownership Regression Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-01 交付 learning-loop-first Shell、Today Workspace Query、明确标记的兼容导师工作台、History 与 Settings；未实现或伪造 canonical Goal/Plan/Activity link。详细证据见 `docs/releases/ui-01-learning-shell-workspace.md`。

## UI-02A Release Gates

```text
Engineering Gate: PASS
Contract / Ownership / Security Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02A 交付 current-user Canonical 资料库、durable document processing、source-bound KnowledgeUnit candidates、范围化 Knowledge Map 与 SourceSpan Inspector；无证据时关系保持为空。详细证据见 `docs/releases/ui-02a-library-knowledge-map.md`。

## UI-02B Goals, Learning Path and Evidence Release Gates

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02B 交付 current-user Goals、canonical plan order、owner-safe Evidence 与诚实 Today 计划摘要；未冻结的 activity/session link 不以 UI 状态伪造。详细证据见 `docs/releases/ui-02b-goals-path-evidence.md`。

## Historical Contract Rule

归档后的 EXEC 文件保持执行前任务合同原貌，因此文件头中的 `READY_*` 字段属于历史元数据，不再代表当前状态。当前最终状态以本文件为权威记录。
