# Askora Book-to-Adaptive-Learning Completion Report

> Status：DONE
> 日期：2026-08-08
> 实现合同：`SPEC-D01～D06` / `EXEC-017～024`
> Implementation commit：本报告与 EXEC-024 release gate 同一原子提交，hash 见 Git 历史与交付回执

## 1. Release 结论

```text
Engineering / Contract Gate: PASS
Policy / Ownership Regression Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

Book-to-Adaptive-Learning 已用一个合法、固定 EPUB fixture 走通真实代码路径：

```text
upload / durable process
→ DocumentIR / SourceSpan replay
→ SemanticUnit / published KnowledgeUnit / hard prerequisite relation
→ SYS02 retrieval projection
→ natural-language Goal / confirm / mapping / subgraph
→ diagnostic Attempt / AssessmentResult / SYS03 projection
→ existing LearningPlanner / Activity
→ existing TeachingContext / PolicyBundle / TeachingAction
→ EvidenceBundle / SYS08 actual assistance event
→ fresh formative Attempt / AssessmentResult / SYS03 MasteryEstimate
→ second canonical TeachingAction
```

本报告证明冻结合同的工程实现、ownership、policy regression、replay、恢复与安全门禁通过；它不证明 Askora 改善了真人学习效果。没有新增 RL、Deep KT truth、GraphRAG default、第二 Planner、第二 Teaching Loop 或 book-specific tutor。

## 2. 固定 E2E Fixture

`tests.fixtures.minimal_epub.book_to_learning_epub()` 固定以下内容：

- 合法 EPUB3 container / OPF / manifest / spine / nav；
- `BOOK / CHAPTER / SECTION / PARAGRAPH / LIST / FOOTNOTE / FIGURE` 结构；
- `Foundations`、`Application`、`Replay` 三个 published KnowledgeUnit；
- source-explicit `Foundations → Replay` hard prerequisite；
- 可定位/回放 SourceSpan、内部链接、footnote 与 figure；
- deterministic diagnostic/formative exact assessment 内容。

基础 `minimal_structured_epub()` 保持无 relation，用于证明“章节顺序不自动产生 prerequisite”；EXEC-024 fixture 通过独立入口显式加入 relation，不弱化 EXEC-019 断言。

## 3. Gate Matrix

| Gate | 结果 | 关键证据 |
|---|---|---|
| G0 Contract | PASS | public contract、architecture dependency、SYS01～SYS08 owner tests；无 second truth/tutor |
| G1 Content | PASS | fixed EPUB structure、granularity、exact SourceSpan replay、publish/relation/cycle/projection tests |
| G2 Goal / Diagnostic | PASS | natural-language Goal、confirm、exact mapping/subgraph、unknown prerequisite、deterministic Assessment→SYS03 |
| G3 Planning | PASS | published eligible KU/relation + exact learner/graph versions 进入 existing LearningPlanner / Activity |
| G4 Teaching | PASS | Activity 进入 existing SYS05/SYS02/SYS08；first/second immutable TeachingAction；actual assistance event durable |
| G5 Recovery / Security | PASS | duplicate process/idempotency、restart/retry、quarantine、prompt injection、grader-only、auth/scope、system failure boundary |
| G6 Product Contract | PASS | `test_book_to_adaptive_learning.py` 从 EPUB upload 闭合到 second canonical TeachingAction |

## 4. E2E Audit Evidence

主 E2E 明确验证：

- plan/activity 的 KnowledgeUnit 全部属于同一资料范围内 published 且带 evidence span 的集合；
- hard prerequisite 使用 published SYS01 relation revision，不由章节顺序或 LLM 猜测；
- Goal 输入仅为自然语言，不要求用户提供 UUID；
- diagnostic result 由 SYS04 创建，MasteryEstimate/LearnerState 仅由 SYS03 owner path 写入；
- first teaching 返回真实 EvidenceBundle，learner-visible items 不含 grader-only；
- SYS08 `ActualAssistanceRecorded` 作为 append-only v0.3 event 持久化，重复 teaching request 复用同一 immutable event；
- fresh no-hint formative Attempt 形成新的 SYS03 MasteryEstimate；
- second TeachingContext exact source refs 包含该新 MasteryEstimate，随后产生第二个 immutable TeachingAction；
- online `ModelRouter` 在 E2E 中被设为“调用即失败”，证明 deterministic bootstrap/replay 不依赖在线 LLM。

## 5. Replay / Idempotency / Migration

- 相同 EPUB parser input 产生相同结构；重复 `process_document` 不创建第二 revision。
- SourceSpan exact replay 校验 locator/content hash；publication replay 只消费 persisted exact refs。
- Goal mapping 重复 idempotency key 返回同一 mapping/subgraph。
- DiagnosticNeed 按 exact version replay，不调用模型。
- first TeachingContext + exact production PolicyBundle/profile 重放产生相同 semantic TeachingAction。
- actual assistance event 使用 deterministic identity；重复 teaching request 不产生第二 event。
- production PolicyRuntimeProfile digest、active activation exact resolution、缺失/不匹配 fail-closed 均有测试。
- Alembic 新库完成 `upgrade head → check → downgrade base → upgrade head`；被 TeachingAction 引用的默认 bundle 回滚会 fail closed 并要求 forward-fix。

## 6. Security / Failure Evidence

完整回归覆盖：

- current-user auth、source scope 与 private/no-store transport；
- quarantine / review-required / unauthorized 内容不能推进 readiness 或进入教学；
- prompt injection / unsafe EPUB archive path / path traversal / secret leakage；
- grader-only solution 不进入 learner-visible EvidenceBundle；
- SYS02/SYS08 只能 tighten TeachingAction exposure envelope；
- missing evidence 显式返回，不让 LLM 补造资料事实；
- model timeout/invalid structured output/system failure 不产生 learner failure evidence；
- outbox retry/dead-letter/restart recovery 与 immutable ledger idempotency。

## 7. Acceptance Criteria Matrix

| AC | 结果 | 证据摘要 |
|---|---|---|
| D06-AC-001 | PASS | fixed EPUB 走 structure-preserving parser/IR，不走 flat-chunk shortcut |
| D06-AC-002 | PASS | plan 仅消费 published eligible KU/relation + replayable source evidence |
| D06-AC-003 | PASS | natural-language Goal→confirm→exact target mapping，无 UUID 用户输入 |
| D06-AC-004 | PASS | unknown prerequisite→真实 diagnostic→SYS03 LearnerState |
| D06-AC-005 | PASS | 复用 existing LearningPlanner 生成 Activity |
| D06-AC-006 | PASS | Activity 进入 existing v0.3 Teaching Policy；无 book tutor |
| D06-AC-007 | PASS | fresh Assessment/SYS03 material evidence 进入 second TeachingContext/Action |
| D06-AC-008 | PASS | content/goal/diagnostic/plan/policy/event correlation 与 exact refs 可审计 |
| D06-AC-009 | PASS | fixed replay 期间在线 ModelRouter 调用会令测试失败 |
| D06-AC-010 | PASS | quarantine/auth/grader-only/security gates PASS |
| D06-AC-011 | PASS | 无 blocking ownership/ADR/Spec conflict |
| D06-AC-012 | PASS | Learning Evidence 诚实保持 insufficient |

`EXEC024-AC-001～010` 均由上述真实 E2E、全量回归、迁移与发布证据覆盖。

## 8. Verification Evidence

| Gate | 结果 |
|---|---|
| backend pytest + coverage | 330 passed, 1 skipped；coverage 71.63%（required 45%） |
| `test_document_service.py` | PASS |
| `test_optimizations.py` | PASS |
| Ruff | PASS |
| Black hash-locked baseline | PASS；270 files unchanged |
| mypy | PASS；仅 untyped-body notes |
| Alembic current DB check | PASS；No new upgrade operations detected |
| Alembic fresh SQLite roundtrip | PASS；upgrade/check/downgrade/upgrade |
| Python dependency audit | PASS；No known vulnerabilities found |
| frontend Vitest | 10 files / 39 tests PASS |
| frontend production build | PASS |
| npm audit `--audit-level=high` | PASS；0 vulnerabilities |
| docs lifecycle/link gate | PASS on candidate Git tree；用户未跟踪 `docs/CODE_WIKI.md` 不属于 release candidate |
| `git diff --check` | PASS（提交前执行） |

真实模型 gate 不属于 EXEC-024 Acceptance Criteria；本次 replay/E2E 主动禁止在线模型调用。既有 real-model test 在无密钥本地环境保持 1 skipped，不能解释为模型能力或学习效果证据。

## 9. Black Baseline 收敛

当前 CI 的 hash-locked Black 检查发现 `evidence_service.py`、`planning_records.py`、`models/planning.py` 已在 EXEC-020/021/023 合法修改后脱离旧 hash。按检查器明确协议：

- `evidence_service.py` 仅执行 Black mechanical formatting；
- `planning_records.py`、`models/planning.py` 已符合 Black，无内容格式变化；
- 删除这 3 个已失效 baseline entries；
- 未新增或扩大任何 ignore，最终 baseline gate PASS。

## 10. Residual Risks / Claim Boundary

- `LEARNING_EVIDENCE_INSUFFICIENT`：只有 synthetic fixture / deterministic policy / engineering replay，无真实 human delayed-retention / transfer outcome evidence。
- 本次没有宣称 causal learning improvement、真人学习增益或模型教学质量。
- 用户工作区存在未跟踪 `docs/CODE_WIKI.md`，其 `file://` 链接会令直接在脏工作区运行 docs checker 失败；该文件未被读取为合同、未修改、未暂存，也不进入候选 Git tree。

Blocking `SPEC GAP`：none。
