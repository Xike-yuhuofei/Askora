# Askora Completed Execution Plans

> v0.2 收口日期：2026-08-07
> v0.3 收口日期：2026-08-07
> v0.3.1 收口日期：2026-08-08
> UI-01 收口日期：2026-08-08
> UI-02A 收口日期：2026-08-08
> UI-02B1 收口日期：2026-08-08
> UI-02B2 收口日期：2026-08-08
> UI-02B3 收口日期：2026-08-08
> UI-02B Goals/Path/Evidence 收口日期：2026-08-09
> UI-02C 收口日期：2026-08-09
> P1-04 Library Management 收口日期：2026-08-09
> P1-01A Goal Definition, Draft and Safe Replan 收口日期：2026-08-09
> P1-01B Goal Lifecycle and Evidence-gated Achievement 收口日期：2026-08-09
> P1-05 Account Lifecycle 收口日期：2026-08-09
> P1-05 / P1-03 Canonical Erasure Integration 收口日期：2026-08-09
> P1-02A Secure Model Configuration Foundation 收口日期：2026-08-09
> P1-07 Error Recovery Center 收口日期：2026-08-09
> P1-03 收口日期：2026-08-09
> P1-06A Onboarding Readiness Foundation 收口日期：2026-08-09
> Book-to-Learning 执行日期：2026-08-08
> P1-02B 模型设置产品闭环收口日期：2026-08-09
> UI-03B Today Primary Hierarchy 收口日期：2026-08-11
> UI-04A Workspace Context / Shell / Route Migration 收口日期：2026-08-11
> PostgreSQL Membership Constraint Reconciliation 收口日期：2026-08-11
> 状态：v0.2 + v0.3 + v0.3.1 + UI-01 + UI-02A + UI-02B1 + UI-02B2 + UI-02B3 + UI-02B Goals/Path/Evidence + UI-02C FROZEN BASELINES；Book-to-Learning EXEC-017～024、P1-03 EXEC-1031～1034、P1-04 EXEC-031～033、P1-05 EXEC-034～037、P1-01 EXEC-038～039、P1-02 EXEC-040～041、P1-06A EXEC-1061、P1-07 EXEC-037、EXEC-042 DONE

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
| EXEC-026 — UI-02B2 Guided Book Learning | DONE | local atomic implementation；commit pending |
| EXEC-027 — UI-02B3 Real-model Guided Learning E2E | DONE | Zhipu UI E2E + DeepSeek real-model gate PASS；local implementation |
| EXEC-028 — Zhipu Development Model Integration | DONE | `zhipu/glm-4.7-flash` unit + real-model canonical gate PASS；local configuration only |
| EXEC-029 — UI-02B Goals, Learning Path and Evidence | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-030 — UI-02C Canonical Activity Lifecycle | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-031 — P1-04A Library Search and Organization | DONE | canonical P1-04 dependency baseline |
| EXEC-032 — P1-04B Library Deduplication | DONE | canonical P1-04 dependency baseline |
| EXEC-033 — P1-04C Scanned PDF OCR Review | DONE | canonical P1-04 dependency baseline |
| EXEC-034 — Identity Credential and Durable Sessions | DONE | 独立 implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-035 — Local Account Recovery Kit | DONE | 独立 implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-036 — Account Deletion, Owner Erasure and Restore Barrier | DONE | 独立 implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-037 — P1-05 / P1-03 Canonical Erasure Integration | DONE | `aea603e0e77afcbbd855330e4c1e715fb25c9aab`；PR #5 CI run `31302663091` PASS |
| EXEC-037 — P1-07 Error Recovery Center | DONE | `c4a5928` / integration and release fixes through candidate HEAD |
| EXEC-038 — P1-01A Goal Definition, Draft and Safe Replan | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-039 — P1-01B Goal Lifecycle and Evidence-gated Achievement | DONE | local atomic implementation commit；hash 见 Git 历史/交付回执 |
| EXEC-040 — P1-02A Secure Model Configuration Foundation | DONE | `0da63a7` / `7964ebd` / `d59837d` |
| EXEC-041 — P1-02B Model Settings Product Closure | DONE | `feat(model-settings): close P1-02 product gate`；hash 见 Git 历史 |
| EXEC-1031 — P1-03 Recovery Foundation | DONE | `23e2c51` |
| EXEC-1032 — P1-03 Verified Offline Restore | DONE | `cfed3e6` |
| EXEC-1033 — P1-03 User Data Export | DONE | `4588543` |
| EXEC-1034 — P1-03 Erasure, Settings UX and Release Gate | DONE | `d0cff3a` |
| EXEC-1061 — P1-06 Onboarding Readiness Foundation | DONE | `4747000` |
| EXEC-047 — LocalOwner Foundation & Migration | DONE | 2026-08-10 archived；commit SHA 见 Git 历史/交付回执 |
| EXEC-042 — v0.3 Production Sequential Teaching Policy Closure | DONE | 2026-08-10 archived；commit SHA 见 Git 历史/交付回执 |
| EXEC-043 — UI-03A Shell, Routes and Learning Domain | DONE | 2026-08-10 archived；commit SHA 见 Git 历史/交付回执 |
| EXEC-044 — UI-03B Today Primary Hierarchy | DONE | 2026-08-11 archived；implementation/verification commit SHA 见 Git 历史/交付回执 |
| EXEC-068 — UI-04A Workspace Context / Shell / Route Migration | DONE | 2026-08-11 archived；ADR-0019 canonical Workspace query + frontend shell closure |
| EXEC-069 — UI-04B Learning Context Drawer Query and UI | DONE | 2026-08-11 archived；canonical SYS05/SYS06 query + accessible presentation-only disclosure |
| EXEC-074 — PostgreSQL Membership Constraint Reconciliation | DONE | `ea78ada`；revision `w171r0e0a002`；SQLite/PostgreSQL migration checks PASS |

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

## UI-02B2 Release Gates

```text
Engineering Gate: PASS
UI / Contract / Ownership / Security Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02B2 交付 system-guided safe auto-advance、rank-1 primary diagnostic target、system-start 与 durable activity transcript；其当次报告记录的本地数据库状态为 pending migration。详细证据见 `docs/releases/ui-02b2-guided-book-learning.md`。

## UI-02B3 Release Gates

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Real Browser + Provider + PostgreSQL E2E Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02B3 交付 production policy-bound real-model renderer、model execution/transcript/event
可追踪性、千级 EPUB retrieval 放大修复，并完成 Zhipu 真实 UI、PostgreSQL、刷新和 duplicate audit。
当前本地数据库已迁移至 `a80d4f9c2b61 (head)`；UI-02B2 报告中的 pending migration 是其生成时快照。
详细证据见 `docs/releases/ui-02b3-real-model-guided-learning.md`。

## UI-02B Goals, Learning Path and Evidence Release Gates

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

UI-02B 交付 current-user Goals、canonical plan order、owner-safe Evidence 与诚实 Today 计划摘要；未冻结的 activity/session link 不以 UI 状态伪造。详细证据见 `docs/releases/ui-02b-goals-path-evidence.md`。

## P1-03 Release Gates

```text
Engineering Gate: PASS
Policy / Ownership / Security Gate: PASS
Desktop Recovery E2E Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

P1-03 交付 macOS 私人桌面 SQLite 的加密恢复、可验证离线恢复、current-user 可读导出和 owner-coordinated 四范围删除；详细 AC、测试、打包桌面恢复证据与既有仓库门禁债务见 `docs/releases/p1-03-data-control-recovery.md`。

## Historical Contract Rule

归档后的 EXEC 文件保持执行前任务合同原貌，因此文件头中的 `READY_*` 字段属于历史元数据，不再代表当前状态。当前最终状态以本文件为权威记录。
