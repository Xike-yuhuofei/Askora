# EXEC-013 — v0.3 E2E / Migration / Recovery / Security / Release Gate

> Priority：P0 Release Gate  
> Status：READY_AFTER_EXEC-012  
> Depends on：EXEC-007～012

## Objective

不再新增横向功能，只对 v0.3 Adaptive Teaching Loop 做最终系统级验证：真实 canonical path、migration/replay/recovery/security、真实模型执行、OPVE G0/G1，以及 Engineering / Policy / Learning Evidence 三类 gate 独立判定。

失败必须回到对应 EXEC 修复；禁止降低规范标准来让 gate 通过。

## Required Specs

Codex MUST 读取根 `AGENTS.md` 与全部 `docs/specs/**`，重点：

- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/observability-standard.md`
- `docs/specs/quality/definition-of-done.md`

同时读取 `EXEC-007`～`EXEC-012` 的 completion evidence。

## Allowed Files

优先只允许测试、fixture、release evidence 与真实缺陷修复：

```text
apps/backend/tests/e2e/**
apps/backend/tests/integration/**
apps/backend/tests/security/**
apps/backend/tests/recovery/**
apps/backend/tests/migrations/**
apps/backend/tests/evals/**
apps/backend/tests/fixtures/**
apps/backend/tests/architecture/**
.github/workflows/**
docs/archive/releases/**
docs/archive/exec-plans/**           # 仅 gate PASS 后归档
```

若测试暴露实现缺陷，可修改对应实现文件，但 completion report MUST 映射回责任 EXEC/SYS requirement。不得借最终 gate 增加新功能或改设计。

## Forbidden Changes

- 不修改 Design/ADR/Spec 以迁就实现；
- 不跳过 critical test 后宣布 PASS；
- 不以 mock 替代唯一真实模型 AC；
- 不伪造 CI status/check；
- 不把 synthetic learner/OPVE 当 human learning efficacy proof；
- 不把 Engineering PASS 推导为 Learning Evidence PASS；
- 不把 engagement/turns/likes 当 primary learning outcome；
- 不允许 LLM/legacy Socratic 获得 final TeachingAction ownership；
- 不允许 hard-rule violation 通过 soft score/fallback；
- 不允许 historical replay 使用当前 state/config 猜补 exact refs。

## Canonical E2E Scenario

使用一份固定小型 PDF/Markdown + 一个主 KnowledgeUnit + 少量 prerequisites + deterministic assessment item family。

至少执行并可追踪：

```text
1. fresh/repaired database
2. import material / SourceSpan
3. create/activate LearningGoal + LearningActivity
4. build exact TeachingContext
5. pin exact PolicyBundle
6. SYS05 hard constraints -> stage -> candidates -> features -> scoring -> anti-oscillation -> tie-break
7. persist TeachingAction + DecisionTrace
8. SYS02 EvidenceBundle tightening-only
9. SYS08 real-model render within action envelope
10. record actual assistance/exposure
11. learner submits deterministic response
12. SYS04 Attempt + AssessmentResult + ErrorType/diagnostic confidence
13. SYS03 LearnerEvidence + MasteryEstimate
14. create/satisfy independent-validation obligation where applicable
15. SYS07 ReviewSchedule / deterministic time transition
16. next exact TeachingContext + SYS05 decision
17. TeachingEpisode / LearningTrajectory linkage
18. OutcomeObservation
19. restart/recover pending work
20. fixed-version replay without online LLM
```

## Required Scenario Variants

### V1 — Low/Insufficient Evidence

应产生合法 `EXPLICIT_INSTRUCTION` 或 `GUIDED_PRACTICE` candidate/selection，不允许 free-form LLM strategy selection。

### V2 — Assisted Success

记录 `ASSISTED` actual assistance，创建 `INDEPENDENT_VALIDATION_REQUIRED`，不能直接完成 independent mastery validation。

### V3 — Answer Exposed

记录 `ANSWER_EXPOSED`，正确回答不得成为 independent mastery evidence，并创建 validation obligation。

### V4 — Fresh Independent Success

满足支持降低/validation completion 的合法证据条件；FADING/RETRIEVAL eligibility 按 PolicyBundle/Spec 判定。

### V5 — Delayed Retrieval

使用 injected/fixed time，不真实等待；验证 ReviewSchedule/outcome delay/retrieval semantics。

### V6 — Transfer

使用 novel variant，验证 `TRANSFER_CHALLENGE` candidate/Outcome transfer fields。

### V7 — Repeated Failure / Remediation

达到 versioned failure ceiling 后，验证 continuity override、support escalation/re-diagnosis/prerequisite/ERROR_REMEDIATION 合法路径。

### V8 — UNKNOWN / Low Diagnostic Confidence

验证 conservative probe/remediation，不强制猜测 misconception。

### V9 — No Material Evidence Repeat

重复 policy evaluation 不发生非法 strategy oscillation。

### V10 — Model Failure / Invalid Output

模型 timeout/unavailable/invalid structured output；fallback 只能保持或收紧 envelope，不产生 learner failure evidence。

### V11 — Retrieval Missing

missing evidence 显式失败/降级，不允许模型伪造来源事实。

### V12 — Prompt Injection / Override Attempt

资料或模型尝试覆盖 hard rule、TeachingAction、tool permission、answer exposure；必须失败。

### V13 — Restart During Pending Work

outbox/workflow pending 时重启；恢复或进入明确 terminal failure，不得重复 canonical evidence/write。

### V14 — Historical Migration / Replay

覆盖 9 migration candidates；缺 exact version 时只能 PARTIAL/NON_REPLAYABLE，不得伪造 FULL replay。

### V15 — Experiment Probability Separation

若有 ExperimentAssignment fixture，验证 assignment probability 与 deterministic action propensity 完全分离。

## Migration Gate

必须验证：

- v0.2 representative database -> v0.3 schema；
- 9 migration candidate fixtures；
- no permanent dual-write；
- legacy strategy/assistance/policy/trace 只做 compatibility read/audit；
- migration/upcaster 幂等；
- historical replay status 显式；
- new PolicyBundle activation 不重解释历史 decision。

## Security Gate

至少固定回归：

```text
document/retrieval prompt injection
hard-rule override attempt
answer/grader leakage
SYS02/SYS08 envelope expansion attempt
unauthorized tool
secret/prompt/log leakage
legacy Socratic override attempt
```

## Observability Gate

选取一个 E2E correlation/trace，必须可串联：

```text
API / LearningActivity
→ TeachingContext
→ PolicyBundle
→ DecisionTrace
→ TeachingAction
→ RetrievalTrace / EvidenceBundle
→ ModelInference / execution validation
→ actual assistance event
→ Attempt
→ AssessmentResult
→ LearnerEvidence / MasteryEstimate
→ ReviewSchedule
→ next policy decision
→ TeachingEpisode / LearningTrajectory
→ OutcomeObservation
```

Decision-time data 与 outcome data 必须可区分。

## OPVE Gate

必须自动执行：

- L1 Contract Verification；
- L2 Scenario Replay；
- L3 Sequential Transition Replay；
- L4 Property/Metamorphic；
- L5 Baseline Differential Replay；
- L6 Synthetic Learner Stress。

Gate rules：

```text
G0 hard constraints = 100% pass
forbidden action = 0
G1 selected action in acceptable_actions
G2 = research/calibration evidence, not hard release gate unless explicitly configured
```

## Real-Model Gate

至少一次使用实际配置模型执行：

```text
fixed TeachingAction
→ EvidenceBundle
→ model-generated explanation/hint/feedback within envelope
→ output validation
→ actual assistance recording
→ deterministic AssessmentResult
→ next SYS05 decision
```

保存非敏感：provider、model、prompt/version、policy bundle version、result、latency/trace refs。不得提交密钥。

## Release Acceptance Criteria

### Engineering Gate

- `EXEC013-AC-001`：v0.2 canonical learning loop 未被破坏；single-writer ownership 仍成立。
- `EXEC013-AC-002`：EXEC-007 profile boundary debt 已关闭且 candidate commit 有 durable CI evidence。
- `EXEC013-AC-003`：v0.3 canonical schema 是唯一 active writer；9 migration candidates 可执行验证。
- `EXEC013-AC-004`：restart/outbox/recovery/migration/replay tests 通过。
- `EXEC013-AC-005`：真实模型 E2E 至少一次成功且无 secret 泄漏。
- `EXEC013-AC-006`：全量 backend quality/tests、migration、frontend build、dependency audit 均有 candidate CI 结果。

### Policy Correctness Gate

- `EXEC013-AC-007`：six StrategyFamily/four-layer ontology runtime/test 一致。
- `EXEC013-AC-008`：same exact context + PolicyBundle + assignment deterministic。
- `EXEC013-AC-009`：G0 = 100%，forbidden action = 0。
- `EXEC013-AC-010`：G1 selected action 属于 acceptable set。
- `EXEC013-AC-011`：hard constraints > score/LLM/experiment/fallback。
- `EXEC013-AC-012`：anti-oscillation/repeated failure/UNKNOWN/validation obligation sequential behavior 全部通过。
- `EXEC013-AC-013`：SYS02/SYS08 tightening-only，actual assistance 被 SYS04/SYS03 正确消费。
- `EXEC013-AC-014`：legacy Socratic 无 final TeachingAction ownership。
- `EXEC013-AC-015`：B3 `behavior_policy_type=DETERMINISTIC` 且 `action_propensity=null`；assignment probability 独立。

### Learning Evidence Gate

- `EXEC013-AC-016`：OutcomeObservation 与 DecisionTrace 分离，delayed attribution 不 last-touch 伪因果。
- `EXEC013-AC-017`：primary learning outcomes 与 process metrics 分离。
- `EXEC013-AC-018`：若无充分真实 human efficacy experiment evidence，状态明确为 `LEARNING_EVIDENCE_INSUFFICIENT`，不得宣称 adaptive policy superior。

### Global

- `EXEC013-AC-019`：Vertical Slice Definition of Done 23 项逐项映射并满足 Engineering/Policy 所需项。
- `EXEC013-AC-020`：无 blocking `SPEC GAP`。

## Required Commands

最低：

```bash
cd apps/backend
uv run pytest tests/e2e tests/integration tests/security tests/recovery tests/migrations tests/evals tests/architecture
uv run pytest
uv run ruff check app tests scripts test_document_service.py test_optimizations.py
uv run black --check app tests scripts test_document_service.py test_optimizations.py
uv run mypy app --no-error-summary
uv run alembic upgrade head
uv run alembic check

cd ../frontend
npm ci
npm run build
```

并检查对应 candidate commit 的 GitHub CI checks。真实模型测试可通过受控 marker/workflow 单独运行，但 Release Gate 必须实际执行一次并留下非敏感 evidence。

## Final Release Status

最终必须分别输出：

```text
Engineering Gate: PASS | FAIL
Policy Correctness Gate: PASS | FAIL
Learning Evidence Gate: PASS | FAIL | LEARNING_EVIDENCE_INSUFFICIENT
```

允许：

```text
Engineering Gate: PASS
Policy Correctness Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

此时 v0.3 engineering/policy vertical slice 可完成，但产品/研究文档不得声称“adaptive teaching 已被证明更有效”。

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP | FAIL

Engineering Gate: PASS | FAIL
Policy Correctness Gate: PASS | FAIL
Learning Evidence Gate: PASS | FAIL | LEARNING_EVIDENCE_INSUFFICIENT

Candidate commit / CI:
- sha
- checks/results

Vertical Slice DoD Matrix:
- 1..23 -> evidence/result

AC Matrix:
- EXEC013-AC-001 ... EXEC013-AC-020

OPVE:
- L1..L6
- G0 pass rate / forbidden action count
- G1 pass rate
- G2 scope

Real model:
- provider/model/prompt version/policy bundle/result/latency（无密钥）

Migration/replay:
- 9 candidates
- FULL/PARTIAL/NON_REPLAYABLE

Recovery:
- scenarios/results

Security:
- cases/results

Ownership:
- canonical writers/final TeachingAction owner

Known legacy debt:
- path/rule/next action

SPEC GAP:
- none / details
```

只有 Engineering Gate 与 Policy Correctness Gate 都 PASS，且 AC-018 诚实判定，才可：

1. 将 `EXEC-007`～`EXEC-013` 移入 `docs/archive/exec-plans/`；
2. 更新 `docs/archive/exec-plans/README.md`；
3. 创建 v0.3 release completion report；
4. 宣布 **v0.3 Adaptive Teaching Loop engineering/policy vertical slice frozen**。