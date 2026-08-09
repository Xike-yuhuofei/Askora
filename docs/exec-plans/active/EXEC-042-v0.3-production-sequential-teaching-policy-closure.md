# EXEC-042 — v0.3 Production Sequential Teaching Policy Closure

> Status：**FROZEN / READY_FOR_EXECUTION**  
> Priority：**P0 Policy Correctness Closure**  
> Frozen：2026-08-10  
> Baseline：`93667cd93a1e88659cab56e3bfa697f8e3c21741`  
> Governing Gap：`GAP-V03-001` + `GAP-V03-002`  
> Governing Audit：[`../../design/v0.3-Current-Main-Conformance-Gap-Analysis.md`](../../design/v0.3-Current-Main-Conformance-Gap-Analysis.md)

## Objective

关闭当前 `main` 相对 frozen v0.3 Adaptive Teaching Loop 的两个 production conformance gap：

```text
GAP-V03-001
Production adaptive path bypasses SequentialTeachingPolicy

+

GAP-V03-002
Production TeachingContext / sequential evidence hydration is incomplete
```

本 EXEC 不重新研究或重写 Teaching Policy 算法。目标是把已经实现并冻结的：

```text
TeachingPolicyKernel
= pure single-decision evaluator

SequentialTeachingPolicy
= sequential transition / anti-oscillation wrapper
```

正确接入唯一 production canonical adaptive path，并使用现有 immutable canonical records 重建可 replay 的 sequential input projection。

完成后必须能够证明：

```text
first decision
→ deterministic bootstrap kernel

second+ decision
→ exact previous action / trace
→ material evidence projection
→ SequentialTeachingPolicy
→ anti-oscillation decision
→ final TeachingAction + DecisionTrace
→ SYS02 / SYS08 tightening-only execution
```

## Dependencies

必须满足：

- v0.3 Canonical Design / Delta 已冻结；
- ADR-0001、ADR-0002、ADR-0003 已 accepted；
- v0.3 Specs / Vertical Slice 已冻结；
- EXEC-009、EXEC-010、EXEC-011 已历史完成；
- `GAP-V03-001`、`GAP-V03-002` 已由 current-main conformance audit 冻结为 OPEN；
- 当前实现已有 `TeachingPolicyKernel`、`SequentialTeachingPolicy`、immutable TeachingAction / DecisionTrace / TeachingContext / PolicyBundle records。

本 EXEC 与 `EXEC-1062` 无依赖关系，可独立执行；禁止把 P1-06 onboarding 工作并入本 EXEC。

当前仓库另有与本任务无关的 Black baseline failure：

```text
apps/backend/app/data_control/__init__.py
apps/backend/app/data_control/recovery.py
apps/backend/tests/contracts/test_data_control_contract.py
```

这些文件不属于 EXEC-042 scope，不得为了让本 EXEC 看起来“全绿”而混入修改。最终 current-main Engineering Gate 重新宣告需另行确认所有仓库级 CI 已恢复绿色。

## Required Specs

Codex MUST 按 `AGENTS.md` 顺序读取，并至少读取：

- `docs/specs/README.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/architecture/system-architecture.md`
- `docs/specs/architecture/dependency-rules.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/domain/event-contract.md`
- `docs/specs/interfaces/persistence-contract.md`
- `docs/specs/systems/02-retrieval.md`
- `docs/specs/systems/03-learner-model.md`
- `docs/specs/systems/04-assessment.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/systems/06-learning-planner.md`
- `docs/specs/systems/07-review-scheduler.md`
- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/observability-standard.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

设计理由只在需要时读取：

- `docs/design/v0.3-Canonical-Design-Delta.md`
- `docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md`

历史 EXEC-010 / EXEC-011 用于理解已实现意图，不得覆盖当前 Spec。

## Current Reality

当前 Book-to-Learning production path 为：

```text
BookLearningApplication.start_teaching_round
→ ActivePolicyRuntimeResolver
→ BookLearningApplication._teaching_context
→ LearningOrchestrationFacade.run_turn
→ LearningOrchestrationFacade._execute_adaptive_turn
→ TeachingPolicyKernel.decide
→ SYS02 retrieval
→ SYS08 execution
→ persistence
```

当前问题：

1. `_execute_adaptive_turn()` 直接调用 `TeachingPolicyKernel.decide()`；
2. `SequentialTeachingPolicy.decide()` 不在 production canonical adaptive path；
3. `BookLearningApplication._teaching_context()` 主要 hydrate Goal / Plan / Activity / LearnerState / MasteryEstimate；
4. previous TeachingAction、recent assessment、actual assistance、material evidence、sequential dwell/observed evidence 等输入没有完整进入下一轮 decision；
5. 当前 architecture regression test 反而固定了 facade 必须出现一次 direct kernel call；
6. Book E2E 验证了 first/second TeachingAction 和 mastery update，但未验证真实 production HOLD / SWITCH / hysteresis / dwell / anti-oscillation trace。

已有正确组件不得重建：

- `TeachingPolicyKernel` pure deterministic evaluator；
- `SequentialTeachingPolicy` material-evidence / dwell / hysteresis / failure override；
- `FixedTimeSource`；
- `advance_validation_obligation()`；
- SYS08 tightening-only execution；
- `AdaptiveContractRepository` / `DecisionTraceV03Repository` immutable persistence；
- existing canonical Assessment / LearnerModel records。

## Frozen Implementation Boundary

### B1 — No New Canonical Truth

默认实现必须从现有 immutable records **重建 sequential projection**，不得新增：

- `TutorState`；
- `TeachingSessionState`；
- 新 LearnerState；
- 新 policy-state 数据库表；
- 第二套 action/assessment/assistance history truth；
- 为方便 transition 而长期双写的 mutable cache truth。

若现有 canonical records 无法无歧义重建 `SequentialPolicyState` 所需语义，必须返回：

```text
BLOCKED_BY_SPEC_GAP
```

并指出缺失的 owner/schema/version/recovery semantics。不得自行新增公共 durable state。

### B2 — Production Decision Composition

生产语义冻结为：

```text
if no previous_teaching_action_ref:
    deterministic bootstrap via TeachingPolicyKernel
else:
    require exact previous TeachingAction + DecisionTrace
    require reconstructible SequentialPolicyState
    project typed material EvidenceSignal(s)
    decide via SequentialTeachingPolicy
```

只有最终 `PolicyDecision.action + PolicyDecision.trace` 可进入 SYS02 / SYS08。

存在 `previous_teaching_action_ref` 但 sequential state / exact trace / required refs 无法重建时，MUST fail closed；不得静默 fallback 到 single-decision kernel。

### B3 — Private Composition, No Public Schema Change

MAY 在 orchestration/application 层增加私有 production policy composition helper/service，MAY 为 `CanonicalTurnRequest` 增加非 API 序列化的内部 typed input；但：

- MUST NOT 新增或修改公共 HTTP API semantics；
- MUST NOT 修改 canonical v0.3 public schema；
- MUST NOT 新增数据库 migration；
- MUST NOT 创建第二 final TeachingAction owner；
- kernel 只能作为 bootstrap / sequential wrapper 内部 evaluator。

### B4 — Fixed Decision Time

production sequential evaluation 必须使用当前 immutable `TeachingContext.decision_time` 作为固定 policy time source。

Replay：

```text
same exact context
+ same exact PolicyBundle/profile
+ same exact previous action/trace
+ same material evidence refs
+ same experiment assignment
→ same semantic TeachingAction / DecisionTrace
```

不得在 replay 时读取新的 wall clock 或调用 online LLM。

### B5 — Sequential Projection Scope

当 canonical evidence 存在且与当前 learner/session/activity/knowledge scope 可证明关联时，projection 至少应覆盖：

```text
previous TeachingAction + DecisionTrace
recent accepted AssessmentResult / Attempt
actual assistance / answer exposure event
LearnerState / MasteryEstimate update
independent vs assisted success evidence
ErrorType / diagnostic confidence / needs_probe
previous action outcome refs
meaningful review/delay evidence（存在时）
transfer evidence（存在时）
explicit structured user-request flags（存在时）
```

缺失信息必须继续使用 canonical `MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE` semantics；禁止 missing=0。

不得从 learner free-form text 用未经冻结的 LLM/heuristic 猜测 direct-answer intent。只有已有 structured canonical flag/command 时，才生成 `EXPLICIT_USER_REQUEST` signal。

### B6 — Material Evidence Identity

Evidence opportunity 必须由 stable exact-version evidence identity 去重，而不是：

- chat turn number；
- wording variation；
- re-render；
- retry invocation；
- few-second wall clock drift。

重复读取同一个 AssessmentResult / LearnerState update / assistance event 不得制造第二个 dwell opportunity。

## Allowed Files

仅允许在实际需要时修改：

```text
# Production composition / hydration
apps/backend/app/application/book_learning.py
apps/backend/app/orchestration/learning_facade.py
apps/backend/app/orchestration/**                 # 仅新增/修改 private sequential composition helper

# Existing policy implementation: integration-only changes, no algorithm redesign
apps/backend/app/domains/teaching_policy/**

# Existing canonical read/reconstruction support
apps/backend/app/infrastructure/adaptive_records.py
apps/backend/app/infrastructure/book_learning_transcript.py
apps/backend/app/infrastructure/learning_records.py
apps/backend/app/queries/**                       # 仅 owner-safe sequential projection query

# Tests / fixtures
apps/backend/tests/architecture/test_v03_adaptive_owner_cutover.py
apps/backend/tests/integration/test_v03_policy_sequential.py
apps/backend/tests/evals/test_v03_policy_anti_oscillation.py
apps/backend/tests/e2e/test_book_to_adaptive_learning.py
apps/backend/tests/integration/**                 # 仅 EXEC-042 新增 production composition tests
apps/backend/tests/fixtures/**                    # 仅 EXEC-042 deterministic fixtures

# Task lifecycle / evidence index
apps/backend/README.md                            # 仅必要 current architecture note
docs/exec-plans/README.md
docs/exec-plans/active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md
docs/exec-plans/completed/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md
docs/exec-plans/completed/README.md
docs/releases/v0.3-production-sequential-policy-closure.md
docs/releases/README.md
docs/document-inventory.md
docs/README.md
```

如实现需要修改以下任一范围，默认视为 scope violation，除非先报告 `BLOCKED_BY_SPEC_GAP`：

```text
apps/backend/app/contracts/**
apps/backend/app/models/**
apps/backend/alembic/**
docs/specs/**
docs/adr/**
docs/design/**
apps/frontend/**
```

## Forbidden Changes

- 不重写 `TeachingPolicyKernel` 的算法语义；
- 不删除或内联掉 `SequentialTeachingPolicy`；
- 不把 anti-oscillation 强塞回 single-decision kernel；
- 不创建新的 StrategyFamily / TeachingStage / ErrorType；
- 不改变 scaffold / hint / answer-exposure / assistance 四轴语义；
- 不让 LLM / renderer / retrieval 拥有 final TeachingAction；
- 不把 legacy Socratic selector 接回 v0.3 final decision；
- 不引入 Bandit / RL / stochastic runtime tie-break；
- 不持久化新的 generic sequential/tutor state truth；
- 不以 turn count 作为 evidence opportunity；
- 不从自由文本猜测 mastery、diagnosis 或 material evidence；
- 不把 planned assistance 当 actual assistance；
- 不把 validation scheduled 当 validation satisfied；
- 不让 repeated evaluation of same evidence 增加 dwell count；
- 不弱化 SYS08 tightening-only；
- 不修改 P1-06 / Desktop / DMG / model-settings / data-control unrelated product scope；
- 不修改上述 3 个 unrelated Black-baseline 文件；
- 不修改 Design / ADR / Spec 来迁就现有 direct-kernel implementation。

## Implementation Tasks

### T1 — Build One Production SYS05 Decision Composition

将 production adaptive decision 收敛到一个私有 composition boundary：

```text
bootstrap decision
OR
sequential decision
→ one PolicyDecision
```

要求：

- facade 不再把 direct kernel call 当作 production final-path architecture contract；
- ordinary / streaming 使用同一个 `_execute_turn()` / same decision composition；
- Book-to-Learning 通过同一 facade；
- 不出现第二个 production selector。

### T2 — Bootstrap vs Sequential Fail-Closed Gate

实现明确分支：

```text
previous_teaching_action_ref is None
→ bootstrap kernel

previous_teaching_action_ref exists
→ exact sequential state/signals required
→ SequentialTeachingPolicy
```

以下必须报 typed deterministic error，不能 fallback kernel：

- previous ref 存在但 action missing；
- previous DecisionTrace missing/mismatch；
- previous trace 未精确选择 previous action；
- previous action scope 不属于当前 activity/objective；
- sequential reconstruction ambiguity。

### T3 — Reconstruct Previous Action / Trace Chain

优先从 canonical TeachingAction / DecisionTrace immutable records 重建：

- exact previous action；
- exact previous trace；
- latest transition state；
- evidence opportunities since last switch；
- observed material evidence identities；
- open validation obligation（若已有 canonical evidence 可重建）。

MAY 使用 durable transcript / activity linkage **定位 canonical ref**，但 transcript copy 不得替代 SYS05 canonical action/trace truth。

不得新增 policy-state table。

### T4 — Hydrate TeachingContext From Existing Owner Facts

扩展 Book production `TeachingContext` projection，使当前已存在且与 scope 可证明关联的 canonical facts 进入 exact snapshot。

至少优先补齐：

```text
previous_teaching_action_ref
previous_action_outcome_refs
recent_assessment_result_ref
correctness_score
assessment_confidence
error_type
diagnostic_confidence
needs_probe
assistance_history_summary
scaffold_history
hint_history
answer_exposure_history
independent_success_history
assisted_success_history
```

若某项没有 canonical fact，保留 explicit missing/empty semantics，不伪造。

所有新加入 snapshot 的 owner facts 必须进入 `source_refs` 或相应 field-level refs，并参与 deterministic fingerprint。

### T5 — Project Typed EvidenceSignal

从 exact canonical refs 产生 `EvidenceSignal`，至少支持当前真实路径可获得的：

```text
ASSESSMENT_RESULT
INDEPENDENT_ATTEMPT
DIAGNOSTIC_PROBE
LEARNER_STATE_UPDATE
ASSISTANCE_EVENT
EXPLICIT_USER_REQUEST   # 仅 structured flag 已存在时
REVIEW_DELAY_TRANSITION # 仅 canonical review/delay evidence 已存在时
```

同一 exact evidence ref 只能算一次 material opportunity。

不得把 chat turn / free-text change / re-render 伪装成 material signal。

### T6 — Use Context Decision Time For Sequential Policy

调用 `SequentialTeachingPolicy` 时使用 fixed `TeachingContext.decision_time`。

禁止 production sequential transition 隐式读取当前 wall clock。

### T7 — Persist Final Sequential Decision Trace

production second+ decision 的 persisted `DecisionTraceV03` 必须真实包含：

```text
previous_teaching_action_ref
transition_reason_codes
material_evidence_refs
anti_oscillation_decision
behavior_policy_type = DETERMINISTIC
action_propensity = null
replayability_status
```

HOLD 仍产生新的 immutable TeachingAction / DecisionTrace，语义 envelope 可继承 previous legal action，但 exact current context/bundle/ref 必须更新。

### T8 — Replace Architecture Regression

更新 `test_v03_adaptive_owner_cutover.py`：

旧断言：

```text
facade must contain exactly one self._policy_kernel.decide(
```

必须删除。

新断言必须证明：

- production adaptive path 只有一个 SYS05 production composition；
- second+ decision 不允许 direct-kernel bypass；
- legacy selector 仍不能 emit `TeachingActionV03`；
- ordinary / streaming 仍共享同一 adaptive execution method。

不得用脆弱的“字符串出现次数”替代关键 runtime behavior test；静态 architecture test 只能作为补充。

### T9 — Production HOLD E2E

扩展真实 Book-to-Learning E2E：

```text
first canonical action
→ next teaching decision with no new material evidence
→ sequential path
→ HOLD_NO_MATERIAL_EVIDENCE
```

必须断言：

- exact previous action ref；
- `anti_oscillation_decision.decision = HOLD`；
- `material_evidence_refs` 正确为空或仅含真正 material refs；
- final action/trace 已持久化；
- SYS02/SYS08 仍使用 held final action。

### T10 — Production Legal SWITCH E2E

在同一 Book-to-Learning production fixture 中注入真实 canonical evidence，例如：

```text
accepted independent AssessmentResult
+ resulting LearnerState/MasteryEstimate update
```

并证明：

- evidence ref 进入 next TeachingContext / signal projection；
- duplicate evidence 不重复计数；
- minimum dwell 生效；
-达到 frozen transition condition 后出现合法 SWITCH；
- transition reason stable；
- anti-oscillation trace 完整；
- replay deterministic。

不得通过直接构造测试专用 `SequentialPolicyState` 绕过 production reconstruction 来满足此 AC。

### T11 — Production Hysteresis / Repeated Failure Regression

至少增加 production-composition integration tests，证明：

- score delta 小于 switch margin → HOLD；
- repeated failure ceiling 可 override sticky/dwell/hysteresis；
- hard constraint 始终优先；
- UNKNOWN / low diagnostic confidence 保持 conservative path。

这些可复用已有 policy fixtures，但必须穿过新的 production decision composition，而不仅直接调用 `SequentialTeachingPolicy` unit API。

### T12 — Replay From Persisted Exact Records

建立 persisted-record replay test：

```text
TeachingContextRecord
+ PolicyBundle exact version/profile
+ previous TeachingActionRecord
+ previous DecisionTraceRecord
+ material evidence refs
→ reconstructed sequential decision
```

在线模型入口必须 patch 为 fail；replay 仍必须成功且语义一致。

### T13 — Preserve Cross-System Boundaries

回归验证：

- SYS02/SYS08 tightening-only；
- actual assistance remains SYS08/SYS04 fact；
- SYS03 alone owns LearnerState/MasteryEstimate；
- validation obligation create/satisfy semantics unchanged；
- DKT challenger remains non-canonical writer；
- legacy v0.2 compatibility path cannot emit canonical v0.3 TeachingAction。

### T14 — Task Lifecycle / Evidence

只有所有 EXEC-042 AC 满足后：

1. 将本文件从 `active/` 迁入 `completed/`；
2. 更新 `docs/exec-plans/README.md` / completed index；
3. 新建 `docs/releases/v0.3-production-sequential-policy-closure.md`；
4. release report 必须区分：
   - EXEC-042 Policy Correctness closure；
   - targeted Engineering verification；
   - repository-wide current CI status；
   - Learning Evidence 仍为 `LEARNING_EVIDENCE_INSUFFICIENT`；
5. 不得修改历史 v0.3 release snapshot 伪装成当时已经运行了新的 production sequential path。

## Acceptance Criteria

- `EXEC042-AC-001`：first canonical adaptive decision 无 previous action 时仍通过 deterministic bootstrap kernel，same exact input 得到 same semantic action/trace。
- `EXEC042-AC-002`：second+ canonical adaptive decision 只要存在 previous action ref，就必须进入 `SequentialTeachingPolicy`；无法重建时 fail closed，不得 direct-kernel fallback。
- `EXEC042-AC-003`：previous TeachingAction 与 DecisionTrace exact match；scope mismatch / trace mismatch 有稳定错误并阻断执行。
- `EXEC042-AC-004`：production Book TeachingContext hydrate 当前可获得的 previous action、assessment、actual assistance、learner update 等 owner facts；missing 仍显式，不使用默认 0。
- `EXEC042-AC-005`：material evidence 使用 stable exact-version identity；重复 evidence 不制造第二 dwell opportunity。
- `EXEC042-AC-006`：无新 material evidence 的 production next decision 返回 `HOLD_NO_MATERIAL_EVIDENCE`，且 DecisionTrace 有真实 anti-oscillation payload。
- `EXEC042-AC-007`：minimum dwell 基于 evidence opportunity 生效，不基于 chat turn。
- `EXEC042-AC-008`：switch-margin hysteresis 在 production composition 生效，且 hard constraint 可覆盖 hysteresis。
- `EXEC042-AC-009`：repeated failure ceiling 可合法突破 sticky/dwell/hysteresis 并进入 frozen remediation/support path。
- `EXEC042-AC-010`：structured explicit user request 在存在 canonical flag 时形成 typed material signal；不得用新 LLM/free-text heuristic 猜测该 flag。
- `EXEC042-AC-011`：actual assistance / answer exposure / accepted assessment / learner update 能按 frozen semantics进入 context/signals；planned assistance 不替代 actual facts。
- `EXEC042-AC-012`：production second+ DecisionTrace 包含 exact previous ref、transition reason、material evidence refs、anti-oscillation decision；B3 `action_propensity = null`。
- `EXEC042-AC-013`：sequential evaluation 使用 `TeachingContext.decision_time`；persisted replay 不依赖当前 wall clock，不调用 online LLM。
- `EXEC042-AC-014`：Book-to-Learning production E2E 至少覆盖一个真实 HOLD 和一个合法 SWITCH，并验证 persistence + replay。
- `EXEC042-AC-015`：architecture regression 阻止 second+ production direct-kernel bypass；ordinary/streaming/book adaptive paths 不产生第二 final policy path。
- `EXEC042-AC-016`：SYS08 tightening-only、validation obligation、SYS03/SYS04/SYS05 ownership、legacy/DKT boundary 全部保持通过。
- `EXEC042-AC-017`：不新增 DB migration、public contract/schema 或 canonical state owner；如确实需要则任务返回 `BLOCKED_BY_SPEC_GAP`。
- `EXEC042-AC-018`：EXEC-042 targeted/applicable tests、Ruff、mypy、docs checker、diff check 通过；若 repository-wide CI 仍仅因明确记录的 scope 外既有问题失败，release report 必须单独标记，不得宣称 current Engineering Gate PASS。
- `EXEC042-AC-019`：无未声明 blocking SPEC GAP；没有 TODO/pass/mock-only shortcut 伪完成。

## Required Tests

必须新增/更新测试覆盖：

```text
bootstrap deterministic path
second+ sequential routing
missing/mismatched previous action/trace fail closed
production no-material HOLD
production material evidence dwell
production duplicate-evidence dedup
production hysteresis HOLD
production hard-rule precedence
production repeated-failure override
structured explicit-request signal
actual assistance / assessment / learner-update projection
UNKNOWN / low-confidence conservative behavior
DecisionTrace anti-oscillation completeness
fixed-decision-time persisted replay
ordinary/streaming composition equivalence
legacy selector / DKT no-owner regression
SYS08 tightening-only regression
validation-obligation regression
Book-to-Learning HOLD + SWITCH E2E
```

最低 targeted gate：

```bash
cd apps/backend
uv run pytest \
  tests/architecture/test_v03_adaptive_owner_cutover.py \
  tests/integration/test_v03_policy_sequential.py \
  tests/evals/test_v03_policy_anti_oscillation.py \
  tests/e2e/test_book_to_adaptive_learning.py

uv run pytest tests/integration tests/e2e tests/architecture tests/evals
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

如仓库级 Black baseline 仍因 EXEC-042 scope 外文件失败，必须在 Completion Report 精确列出文件和基线证据；不得修改这些文件绕过 scope，也不得把 targeted PASS 写成 current repository Engineering Gate PASS。

## Completion Report Format

```text
Status: DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Baseline:
- start commit
- end commit

Gap closure:
- GAP-V03-001 -> CLOSED / OPEN
- GAP-V03-002 -> CLOSED / OPEN

Production decision composition:
- bootstrap path
- second+ sequential path
- fail-closed cases

Sequential reconstruction:
- previous action / trace source
- evidence-opportunity reconstruction
- observed material evidence dedup
- validation obligation reconstruction

TeachingContext hydration:
- field -> owner fact -> exact ref -> availability

Material Evidence projection:
- signal kind -> canonical source -> dedup identity

Production traces:
- HOLD example
- SWITCH example
- anti-oscillation payload
- action_propensity

Replay:
- persisted inputs
- fixed decision time
- expected == actual
- online model call count = 0

Ownership / integrity:
- SYS05
- SYS02/SYS08 tightening-only
- SYS04 actual assistance
- SYS03 learner truth
- legacy/DKT boundary

AC Matrix:
- EXEC042-AC-001 ... EXEC042-AC-019

Tests:
- command -> result

Repository-wide CI:
- current status
- unrelated pre-existing failures, if any

Release Gate after EXEC-042:
- Policy Correctness: PASS / FAILED
- Engineering: PASS / FAILED / NOT RECLASSIFIED
- Learning Evidence: LEARNING_EVIDENCE_INSUFFICIENT

SPEC GAP:
- none / details
```

## Completion Rule

只有同时满足以下条件才可将 EXEC-042 标 `DONE`：

```text
GAP-V03-001 CLOSED
+
GAP-V03-002 CLOSED
+
production HOLD verified
+
production legal SWITCH verified
+
sequential persisted replay verified
+
no direct-kernel second+ bypass
+
no new canonical truth
+
all EXEC042 AC satisfied
```

如果 sequential state 无法从现有 frozen owner facts / immutable records 无歧义重建：

```text
Status: BLOCKED_BY_SPEC_GAP
```

此时必须停止产品代码扩展，报告所需 Design/ADR/Spec delta，不得创建临时 durable tutor state。

**Freeze Result：READY_FOR_EXECUTION**
