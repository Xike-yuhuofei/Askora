# Askora EXEC-042 剩余收口执行提示词

你现在是 Askora 项目的工程执行代理。

GitHub 仓库：

`https://github.com/Xike-yuhuofei/Askora.git`

当前任务不是创建新的 EXEC，也不是重新设计 Teaching Policy。

你的唯一任务是：

> **继续并正式完成 `EXEC-042 — v0.3 Production Sequential Teaching Policy Closure`。**

当前 EXEC-042 已有部分实现进入 `main`，但仍未满足自身冻结的 Completion Rule。你必须基于最新 `main` 重新核验并关闭剩余缺口。

---

# 一、先读取最新 main

必须先拉取最新 `main`，禁止依赖旧分支或历史摘要。

首先读取：

- `AGENTS.md`
- `docs/exec-plans/active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md`
- `docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md`
- `docs/specs/systems/05-teaching-policy.md`
- `docs/specs/domain/decision-contract.md`
- `docs/specs/domain/domain-model.md`
- `docs/specs/architecture/state-ownership.md`
- `docs/specs/quality/definition-of-done.md`
- `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md`
- `docs/specs/vertical-slices/book-to-adaptive-learning.md`

然后检查当前真实实现：

```text
apps/backend/app/orchestration/learning_facade.py
apps/backend/app/application/book_learning.py
apps/backend/app/domains/teaching_policy/**
apps/backend/app/infrastructure/adaptive_records.py
apps/backend/tests/architecture/test_v03_adaptive_owner_cutover.py
apps/backend/tests/integration/test_v03_policy_sequential.py
apps/backend/tests/evals/test_v03_policy_anti_oscillation.py
apps/backend/tests/e2e/test_book_to_adaptive_learning.py
apps/backend/tests/e2e/test_v03_adaptive_loop.py
```

权威顺序：

```text
Frozen Specs
→ Accepted ADR
→ Canonical Design
→ EXEC-042
→ current code
```

代码与冻结 Spec 冲突时，修代码，不反向修改 Spec。

---

# 二、当前已知状态

当前实现已经完成部分工作：

```text
LearningOrchestrationFacade
→ bootstrap TeachingPolicyKernel
OR
→ SequentialTeachingPolicy
```

并已具备：

- previous TeachingAction 传递；
- previous DecisionTrace 查询；
- `FixedTimeSource(context.decision_time)`；
- SequentialPolicyState reconstruction helper；
- 部分 evidence signal projection；
- 部分 TeachingContext history hydration；
- architecture regression 初步更新。

这些已有成果必须保留。

但 **EXEC-042 目前仍不得标记 DONE**。

---

# 三、必须关闭的剩余问题

## P0-1 — 消除所有 sequential → bootstrap silent fallback

这是最高优先级。

冻结规则：

```text
if TeachingContext.previous_teaching_action_ref is None:
    bootstrap TeachingPolicyKernel
else:
    SequentialTeachingPolicy REQUIRED
```

当前任何类似逻辑都必须修正：

```python
if previous_trace is None:
    previous_action = None
```

这是错误的 silent downgrade。

如果上一 canonical TeachingAction 已存在，但：

- previous action record missing；
- previous DecisionTrace missing；
- DecisionTrace 与 previous action 不匹配；
- previous action scope mismatch；
- sequential state reconstruction ambiguous；

必须：

```text
FAIL CLOSED
```

使用稳定 typed deterministic error。

禁止：

```text
previous action exists
→ trace missing
→ pretend first turn
→ TeachingPolicyKernel
```

### 必须增加测试

至少覆盖：

```text
context.previous_teaching_action_ref exists
+ request previous action missing
→ fail closed

previous action exists
+ previous trace missing
→ fail closed

previous action exists
+ trace selects different action
→ fail closed

previous action scope mismatch
→ fail closed
```

并证明：

> second+ production decision 不存在任何 direct-kernel fallback。

---

# 四、完成 TeachingContext owner-fact hydration

当前 `_teaching_context()` 不能只装载 MasteryEstimate 和少量 history。

必须从现有 canonical owner records 中，在证据真实存在且 scope 匹配时，补齐：

```text
recent_assessment_result_ref
correctness_score
assessment_confidence

error_type
diagnostic_confidence
needs_probe

actual assistance history
scaffold history
hint history
answer exposure history

independent_success_history
assisted_success_history

previous_teaching_action_ref
previous_action_outcome_refs
```

如现有数据支持，还应装载：

```text
delayed_independent_evidence
review_context
transfer_evidence
transfer_distance_novelty
```

但必须遵守：

```text
不存在 canonical fact
→ explicit MISSING

禁止：
MISSING → 0
MISSING → false
MISSING → independent
```

所有 hydration 必须满足：

```text
canonical owner fact
→ exact VersionedRef
→ field-level provenance/source_refs
→ deterministic context fingerprint
```

不得从：

- learner free text；
- LLM response；
- UI state；
- transcript copy；

猜测 learner truth。

Transcript 只能用于定位 canonical refs，不得成为第二 truth。

---

# 五、修正 Material Evidence Signal Projection

检查 `_build_evidence_signals()`。

必须保证真正 material evidence 来自 canonical exact-version refs。

允许的 typed signal 根据现有 frozen vocabulary处理，例如：

```text
ASSESSMENT_RESULT
INDEPENDENT_ATTEMPT
ASSISTANCE_EVENT
DIAGNOSTIC_PROBE
LEARNER_STATE_UPDATE
EXPLICIT_USER_REQUEST
REVIEW_DELAY_TRANSITION
```

必须满足：

```text
same exact evidence ref
→ counted once
```

禁止：

```text
CHAT_TURN
text changed
new rendering
new LLM answer
turn count
```

被视为 material evidence opportunity。

如果当前代码在没有 material evidence 时创建：

```text
CHAT_TURN
```

可以保留它作为 non-material observation，但必须证明 SequentialTeachingPolicy 不会因此增加 material dwell opportunity。

---

# 六、完成 SequentialPolicyState deterministic reconstruction

必须证明：

```text
SequentialPolicyState(
    previous_action,
    previous_trace,
    evidence_opportunities_since_transition,
    observed_material_evidence_keys,
    validation_obligation
)
```

可以从现有 immutable records 确定性重建。

重点检查：

```text
evidence_opportunities_since_transition
observed_material_evidence_keys
```

要求：

```text
process restart
+ same persisted records
→ same reconstructed state
```

禁止引入：

- in-memory turn counter；
- mutable session-only counter；
- 新 policy_state 表；
- 新 TutorState；
- 新第二 truth。

如果现有冻结合同确实不足以无歧义恢复某个 required field：

```text
BLOCKED_BY_SPEC_GAP
```

不要自行发明持久化状态。

---

# 七、必须补齐 Production HOLD E2E

必须通过真实：

```text
BookLearningApplication
→ LearningOrchestrationFacade
→ SequentialTeachingPolicy
→ SYS02
→ SYS08
```

执行。

场景：

```text
first canonical TeachingAction
→ no new material evidence
→ second teaching decision
```

必须断言：

```text
transition_reason = HOLD_NO_MATERIAL_EVIDENCE

DecisionTrace.previous_teaching_action_ref
== first TeachingAction exact ref

anti_oscillation_decision.decision
== HOLD

material_evidence_refs
没有伪造新 evidence

second TeachingAction
仍为新的 immutable decision envelope

second action / trace persisted

SYS02 / SYS08
使用 second final held action
```

不能直接调用 `SequentialTeachingPolicy` unit API 伪造这个验收。

---

# 八、必须补齐 Production Legal SWITCH E2E

构造真实 canonical evidence，例如：

```text
accepted independent Attempt
→ AssessmentResult
→ SYS03 learner projection
→ MasteryEstimate / LearnerState update
→ next TeachingContext
```

然后通过真实 production path：

```text
BookLearningApplication
→ facade
→ SequentialTeachingPolicy
```

验证：

```text
material evidence enters TeachingContext
material evidence becomes typed EvidenceSignal
duplicate evidence not counted twice
minimum dwell works
hysteresis works
legal transition eventually SWITCHes
transition reason stable
anti_oscillation_decision complete
DecisionTrace persisted
```

不得直接手工构造最终 `SequentialPolicyState` 绕过 production reconstruction。

---

# 九、必须增加以下 production regression

至少证明：

### Minimum dwell

```text
first material opportunity
→ HOLD due minimum dwell

next distinct material opportunity
→ transition becomes eligible
```

### Hysteresis

```text
score delta below switch margin
→ HOLD
```

### Hard constraint precedence

```text
previous action becomes hard-forbidden
→ SWITCH regardless of hysteresis
```

### Repeated failure

```text
consecutive failure reaches versioned ceiling
→ legal override sticky/dwell/hysteresis
→ remediation/support transition
```

### UNKNOWN / low confidence

```text
UNKNOWN diagnosis
or low diagnostic confidence
→ conservative/probe behavior
```

---

# 十、完成 persisted sequential replay

必须增加真实 persisted-record replay。

输入：

```text
TeachingContextRecord
PolicyBundle exact version
PolicyRuntimeProfile
previous TeachingAction record
previous DecisionTrace record
material evidence refs
ExperimentAssignment if applicable
```

然后重新运行 sequential decision。

必须证明：

```text
same immutable inputs
+ same TeachingContext.decision_time
→ same semantic TeachingAction
→ same DecisionTrace semantics
```

Replay 期间：

```text
online LLM calls = 0
wall-clock dependency = 0
random tie-break = 0
```

禁止 replay 时使用 `datetime.now()` 决定 policy transition。

---

# 十一、修正 E2E 中仍直接使用 kernel 的错误验收

检查：

```text
apps/backend/tests/e2e/test_v03_adaptive_loop.py
apps/backend/tests/e2e/test_book_to_adaptive_learning.py
```

如果测试中的“next decision”仍直接：

```python
TeachingPolicyKernel().decide(...)
```

来代表 second+ canonical production decision：

必须调整。

Kernel 单元 replay 可继续测试 bootstrap。

但 second+ production policy 验收必须通过：

```text
production composition
→ SequentialTeachingPolicy
```

---

# 十二、保持以下语义不变

禁止修改：

```text
six StrategyFamily
TeachingStage ownership
ErrorType vocabulary
scaffold / hint / answer_exposure / assistance axes
PolicyBundle semantics
DecisionTrace probability semantics
SYS02 tightening-only
SYS08 tightening-only
validation obligation semantics
SYS03 Mastery/LearnerState ownership
SYS04 AssessmentResult ownership
legacy Socratic compatibility-only boundary
DKT challenger-only boundary
```

禁止新增：

```text
RL
Bandit
stochastic tie-break
LLM TeachingAction selector
policy DSL
TutorState
generic mutable policy session truth
```

---

# 十三、当前仓库 CI 问题处理原则

当前 `main` 还有其他并行开发变更。

因此首先重新运行最新 CI，区分：

```text
EXEC-042 semantic failures
vs
other task failures
```

如果出现明显机械 CI 问题，且属于当前 `main` 新引入、修复不会改变任何公共语义，例如：

```text
import sorting
document inventory registration
format-only change
```

可以单独、最小化修复，但必须：

- 不与 EXEC-042 semantic patch 混为一谈；
- 在最终报告中单独列出；
- 不借此扩大架构范围。

如果问题属于其他 active EXEC 的业务语义：

不要修改，只报告。

---

# 十四、必须运行的测试

至少：

```bash
cd apps/backend

uv run pytest \
  tests/architecture/test_v03_adaptive_owner_cutover.py \
  tests/integration/test_v03_policy_sequential.py \
  tests/evals/test_v03_policy_anti_oscillation.py \
  tests/e2e/test_book_to_adaptive_learning.py \
  tests/e2e/test_v03_adaptive_loop.py
```

然后：

```bash
uv run pytest tests/integration tests/e2e tests/architecture tests/evals
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
```

仓库根目录：

```bash
python3 .github/workflows/check_docs.py
git diff --check
```

最后检查 GitHub Actions 最新 `main` run。

---

# 十五、重新执行 EXEC042 AC Matrix

必须逐项重新判断：

```text
EXEC042-AC-001
...
EXEC042-AC-019
```

不得使用：

```text
probably pass
implemented
looks correct
```

每一项必须对应：

```text
PASS
+ code evidence
+ test evidence
```

否则：

```text
FAIL
```

---

# 十六、只有满足 Completion Rule 才允许归档

只有同时满足：

```text
GAP-V03-001 CLOSED
GAP-V03-002 CLOSED

production HOLD verified
production legal SWITCH verified
minimum dwell verified
hysteresis verified
repeated-failure override verified

sequential persisted replay verified

second+ direct-kernel bypass impossible

no new canonical truth

all EXEC042 AC-001..019 PASS
```

才允许：

```text
Status: DONE
```

然后必须执行治理收口。

---

# 十七、正式治理收口

将：

```text
docs/exec-plans/active/
EXEC-042-v0.3-production-sequential-teaching-policy-closure.md
```

归档为：

```text
docs/exec-plans/completed/
EXEC-042-v0.3-production-sequential-teaching-policy-closure.md
```

并在文件中写入完整 Completion Report。

更新：

```text
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
docs/document-inventory.md
docs/README.md
docs/releases/README.md
```

新建：

```text
docs/releases/v0.3-production-sequential-policy-closure.md
```

Release evidence 必须明确区分：

```text
Policy Correctness Gate
Engineering Gate
Learning Evidence Gate
```

其中：

```text
Learning Evidence Gate
= LEARNING_EVIDENCE_INSUFFICIENT
```

除非存在新的真实用户学习效果证据，否则不得修改。

---

# 十八、关闭 Gap 的方式

不要篡改历史审计内容。

`docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md`
是历史 current-main snapshot。

应通过新的 current-head verification / release evidence 记录：

```text
GAP-V03-001 → CLOSED
GAP-V03-002 → CLOSED
```

并注明：

```text
verified against commit: <final SHA>
```

禁止把历史审计改写成“当时就是 CLOSED”。

---

# 十九、最终输出格式

最终报告必须严格包含：

```text
EXEC-042 Status:
DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Baseline:
- start SHA
- final SHA

GAP closure:
- GAP-V03-001
- GAP-V03-002

Production composition:
- bootstrap path
- second+ sequential path
- fail-closed behavior

TeachingContext hydration:
- field
- canonical owner/source
- availability semantics

Sequential reconstruction:
- previous action
- previous trace
- evidence opportunity count
- observed evidence dedup
- validation obligation

Production HOLD:
- test
- transition reason
- trace evidence

Production SWITCH:
- canonical evidence
- dwell
- hysteresis
- transition reason

Replay:
- persisted refs
- fixed time
- model call count
- deterministic equality

AC Matrix:
- AC-001 ... AC-019
- PASS / FAIL
- exact test evidence

Tests:
- command
- result

GitHub Actions:
- run number
- final result
- failing jobs if any

Unrelated failures:
- path
- reason
- owning task if known

Governance:
- EXEC-042 archived?
- release evidence created?
- indexes updated?
- Gap closure recorded?

SPEC GAP:
- none
or
- exact blocker
```

---

# 二十、执行原则

不要生成方案后停止。

不要新建 EXEC-043 来解决 EXEC-042 的遗留问题。

不要重新研究 Teaching Policy。

不要修改冻结 Canonical Design / ADR / Spec。

直接：

```text
inspect latest main
→ implement remaining EXEC-042 gaps
→ add production tests
→ run verification
→ close AC matrix
→ archive EXEC-042
→ create release evidence
→ commit
```

开始执行。