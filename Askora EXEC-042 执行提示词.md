# Askora EXEC-042 执行提示词

你现在是 Askora 项目的工程执行代理。

你的唯一任务是：

> **完整执行并关闭 `EXEC-042 — v0.3 Production Sequential Teaching Policy Closure`。**

不得重新设计 Askora，不得扩大任务范围。

---

## 一、第一步：读取当前 main

必须先拉取并检查最新 `main`，禁止基于历史摘要直接修改代码。

首先读取：

1. `AGENTS.md`
2. `docs/specs/README.md`
3. `docs/exec-plans/active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md`
4. `docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md`

然后严格按 EXEC-042 的 `Required Specs` 继续读取相关：

- architecture
- domain
- SYS02
- SYS03
- SYS04
- SYS05
- SYS06
- SYS07
- SYS08
- persistence
- testing
- observability
- Definition of Done
- v0.3 Adaptive Teaching Loop Vertical Slice
- Book-to-Adaptive-Learning Vertical Slice

实现权威顺序必须遵循：

```text
docs/specs/**
→ Accepted ADR
→ Canonical Design
→ EXEC-042
→ current code
```

当前代码若与 Spec 冲突，默认属于 implementation drift。

禁止为了迁就现有实现而修改冻结设计。

---

# 二、任务目标

关闭：

```text
GAP-V03-001
Production adaptive path bypasses SequentialTeachingPolicy

+

GAP-V03-002
Production TeachingContext / sequential evidence hydration is incomplete
```

必须把当前：

```text
LearningOrchestrationFacade
→ TeachingPolicyKernel.decide()
→ SYS02 / SYS08
```

修正为完整 production policy composition：

```text
First canonical decision
→ TeachingPolicyKernel bootstrap

Second+ canonical decision
→ exact previous TeachingAction
→ exact previous DecisionTrace
→ reconstruct SequentialPolicyState
→ project typed material EvidenceSignals
→ SequentialTeachingPolicy
→ anti-oscillation
→ final TeachingAction + DecisionTrace
→ SYS02 / SYS08
```

---

# 三、核心架构约束

## 1. 不得重写算法

已有：

```text
TeachingPolicyKernel
= pure deterministic single-decision evaluator

SequentialTeachingPolicy
= sequential transition / anti-oscillation wrapper
```

必须复用。

禁止重新实现：

- Strategy selector
- anti-oscillation algorithm
- hysteresis algorithm
- minimum dwell algorithm
- failure override algorithm
- TeachingStage derivation
- candidate scoring
- tie-break

除非发现明确 implementation bug，且修复不改变冻结语义。

---

## 2. 禁止新增第二 Truth

默认必须利用现有 immutable canonical records 重建 sequential projection。

禁止新增：

```text
TutorState
TeachingSessionState
AdaptiveTutorState
PolicySessionState
第二 LearnerState
第二 TeachingAction history
第二 Assessment history
第二 assistance history
新的 mutable policy truth
新的 policy-state DB table
```

禁止因为实现方便新增数据库 migration。

如果当前 canonical records **确实无法无歧义重建 `SequentialPolicyState`**：

立即停止相关部分，并输出：

```text
BLOCKED_BY_SPEC_GAP
```

必须准确说明：

- 缺少什么语义；
- 当前 owner 是谁；
- 为什么现有 records 无法重建；
- 需要什么 schema / owner / persistence decision。

不得自行发明 durable tutor state。

---

# 四、Production Composition 必须满足

## Case A — First Decision

若：

```text
previous_teaching_action_ref == None
```

允许：

```text
TeachingPolicyKernel.decide()
```

作为 bootstrap。

要求保持：

```text
DETERMINISTIC
action_propensity = null
fixed TeachingContext.decision_time
exact PolicyBundle/profile pinning
```

---

## Case B — Second+ Decision

如果存在：

```text
previous_teaching_action_ref
```

则：

**禁止直接调用 single-decision kernel 作为最终 production policy。**

必须获得：

```text
previous TeachingAction
previous DecisionTrace
SequentialPolicyState
material EvidenceSignals
```

并执行：

```text
SequentialTeachingPolicy.decide(...)
```

如果 previous ref 存在，但 previous action / trace / required sequential evidence 无法重建：

必须 fail closed。

禁止：

```text
except:
    return TeachingPolicyKernel.decide(...)
```

这种 silent fallback。

---

# 五、Sequential Evidence Projection

优先从现有 canonical records 投影。

当数据真实存在且可以证明属于当前：

```text
user
session
learning activity
objective / knowledge scope
```

时，至少考虑：

```text
previous TeachingAction
previous DecisionTrace

recent accepted AssessmentResult
corresponding Attempt
actual assistance snapshot
answer exposure

LearnerState update
MasteryEstimate update

independent success
assisted success

ErrorType
diagnostic confidence
needs_probe

previous action outcome refs

meaningful review/delay evidence
transfer evidence

explicit user request
```

必须遵守：

```text
missing ≠ 0
missing ≠ false
unknown assistance ≠ independent
chat turn ≠ evidence opportunity
wording change ≠ material evidence
rerender ≠ material evidence
```

不得从 LLM 文本猜测 learner outcome。

---

# 六、SequentialPolicyState

优先从 immutable records **deterministically reconstruct**：

```text
SequentialPolicyState(
    previous_action,
    previous_trace,
    evidence_opportunities_since_transition,
    observed_material_evidence_keys,
    validation_obligation
)
```

重点审查：

```text
evidence_opportunities_since_transition
observed_material_evidence_keys
```

必须能够从已有历史记录或 DecisionTrace semantics 稳定恢复。

禁止引入依赖 process memory 的临时计数器作为 canonical behavior。

重启应用后，相同 canonical evidence 必须仍能得到相同 sequential decision。

---

# 七、Time / Replay

Production sequential policy 必须使用：

```text
TeachingContext.decision_time
```

作为 fixed policy time。

不得直接：

```python
datetime.now()
time.time()
```

驱动 policy decision。

必须满足：

```text
same exact TeachingContext
+ same PolicyBundle/profile
+ same previous TeachingAction
+ same previous DecisionTrace
+ same material evidence refs
+ same ExperimentAssignment
=
same semantic TeachingAction
+ same DecisionTrace
```

Replay 期间：

- 不调用 online LLM；
- 不读取新的 wall clock；
- 不使用随机 tie-break。

---

# 八、TeachingContext Hydration

必须修复 current Book-to-Learning path，使已有 canonical evidence 不再无理由保持 `MISSING`。

重点检查并在有真实 evidence 时 hydrate：

```text
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

previous_teaching_action_ref
previous_action_outcome_refs

delayed_independent_evidence
review_context

transfer_evidence
transfer_distance_novelty
```

但：

> 没有 evidence 时必须保持 explicit MISSING，而不是制造默认值。

---

# 九、Architecture Regression

当前 architecture test 若要求：

```text
LearningOrchestrationFacade
contains direct self._policy_kernel.decide(...)
```

必须修改该测试。

新的 architecture invariant 应验证：

```text
production adaptive entry
→ one SYS05 production policy composition path
```

而不是：

```text
production adaptive entry
→ direct TeachingPolicyKernel
```

必须禁止以后再次出现：

```text
facade
→ kernel directly
→ SYS02/SYS08
```

的 production bypass。

Kernel 可以继续存在，但只能作为：

```text
bootstrap evaluator
或 SequentialTeachingPolicy 内部 evaluator
```

---

# 十、必须覆盖的真实 Production Tests

不能只增加 `sequential.py` unit tests。

必须测试真正的 production composition。

至少覆盖：

## T1 First Decision

```text
no previous action
→ deterministic bootstrap
```

## T2 No Material Evidence

```text
previous action
+ no material evidence
→ HOLD_NO_MATERIAL_EVIDENCE
```

不得发生 StrategyFamily oscillation。

## T3 Minimum Dwell

```text
material evidence opportunity #1
→ HOLD_MINIMUM_DWELL_EVIDENCE_OPPORTUNITY

next valid evidence opportunity
→ transition eligibility
```

## T4 Hysteresis

阈值附近 repeated evidence：

```text
→ stable family
→ no oscillation
```

## T5 Repeated Failure Override

重复失败达到 versioned ceiling：

```text
→ may break sticky continuity
→ remediation/support escalation
```

## T6 Independent Success

新的 fresh independent success：

```text
→ may legally fade support
```

## T7 Assisted / Answer Exposed

实际 learner experience：

```text
ASSISTED success
or
ANSWER_EXPOSED success
→ independent validation obligation
```

不能直接算 independent mastery success。

## T8 UNKNOWN Diagnosis

```text
UNKNOWN / low diagnostic confidence
→ conservative path / probe
```

不得猜具体 misconception。

## T9 DecisionTrace

Second+ production decision 必须有：

```text
previous_teaching_action_ref
transition_reason_codes
material_evidence_refs
anti_oscillation_decision != null
```

B3 保持：

```text
action_propensity = null
```

## T10 Replay

固定时间与相同 immutable refs：

```text
decision A == replay decision B
```

## T11 Book-to-Learning E2E

至少实际经过：

```text
first decision
→ assessment/evidence update
→ second decision HOLD

以及

previous decision
→ material evidence
→ legitimate SWITCH
```

必须是 production Book-to-Learning path，而不是直接调用 policy unit fixture。

---

# 十一、必须保持不变

不得破坏：

```text
SYS02 tightening-only
SYS08 tightening-only
actual assistance semantics
validation obligation semantics
ErrorType 7 + UNKNOWN
six StrategyFamily
TeachingStage derived-only ownership
PolicyBundle exact versioning
DecisionTrace probability semantics
legacy Socratic no final TeachingAction ownership
DKT challenger no canonical write
```

禁止引入：

```text
Contextual Bandit
RL
new LLM strategy selector
always-on Socratic controller
executable policy DSL
```

---

# 十二、Allowed Scope

严格遵循 EXEC-042 中的 Allowed Files。

若某个文件未列入 Allowed Files，但为了完成现有 frozen semantics 确实必须修改：

先判断：

### 私有机械 integration

若：

- 不改变公共 schema；
- 不改变 owner；
- 不改变 API；
- 不改变 domain semantics；

可按 AGENTS.md 局部实现自治处理，并在 Completion Report 明确说明。

### 公共语义变化

若涉及：

```text
owner
schema
database model
API
public contract
persistent truth
policy semantics
```

必须：

```text
BLOCKED_BY_SPEC_GAP
```

不得偷偷扩大范围。

---

# 十三、明确禁止处理的无关问题

当前 CI 已知有 3 个与 EXEC-042 无关的 Black formatting failures：

```text
apps/backend/app/data_control/__init__.py
apps/backend/app/data_control/recovery.py
apps/backend/tests/contracts/test_data_control_contract.py
```

这些文件不属于 EXEC-042。

**禁止在本 EXEC 中顺手修复。**

执行结果必须区分：

```text
EXEC-042 scoped verification

vs

repository-wide existing CI failure
```

不得为了获得绿色 CI 扩大任务范围。

---

# 十四、验证

至少运行 EXEC-042 指定的全部测试。

并至少执行：

```bash
cd apps/backend

uv run pytest tests/evals
uv run pytest tests/integration
uv run pytest tests/e2e
uv run pytest tests/architecture

uv run pytest

uv run ruff check app tests
uv run mypy app --no-error-summary
```

如适用同时运行：

```bash
cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

如果 repository-wide Black baseline 因已知 3 个 scope 外文件失败：

必须原样报告，不得修改它们。

---

# 十五、完成条件

只有以下全部满足，才能声明：

```text
Status: DONE
```

必须证明：

```text
1. first decision deterministic bootstrap
2. second+ production decision cannot bypass SequentialTeachingPolicy
3. exact previous TeachingAction / DecisionTrace reconstructed
4. material evidence projection uses canonical facts
5. no material evidence → HOLD
6. minimum dwell works
7. hysteresis works
8. repeated failure override works
9. actual assistance participates correctly
10. independent success can produce legal fading
11. UNKNOWN remains conservative
12. DecisionTrace includes real anti-oscillation information
13. deterministic replay passes
14. Book-to-Learning production HOLD test passes
15. Book-to-Learning production SWITCH test passes
16. architecture regression prevents direct-kernel bypass
17. SYS02/SYS08 tightening-only remains passing
18. no second canonical truth introduced
19. no unresolved SPEC GAP
```

如果任一关键 semantic requirement 不能在 frozen Spec 内安全实现：

输出：

```text
Status: BLOCKED_BY_SPEC_GAP
```

不得称为 DONE。

---

# 十六、完成后治理

若 `Status: DONE`：

1. 更新 EXEC-042 文件中的 Completion Report；
2. 将：

```text
docs/exec-plans/active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md
```

归档为：

```text
docs/exec-plans/completed/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md
```

3. 更新：
   - `docs/exec-plans/README.md`
   - `docs/exec-plans/completed/README.md`
   - `docs/document-inventory.md`

4. 创建新的 current-head verification / release evidence，明确区分：

```text
Engineering Gate
Policy Correctness Gate
Learning Evidence Gate
```

不得修改历史 release report 来伪装当前重新验证。

5. 只有证据充分时才能关闭：

```text
GAP-V03-001
GAP-V03-002
```

6. 最终提交应保持任务边界清晰。

---

# 十七、最终报告格式

最终必须输出：

```text
EXEC-042 Status:
DONE | PARTIAL | BLOCKED_BY_SPEC_GAP

Baseline:
- starting commit
- final commit

Production policy path:
- before
- after

Sequential reconstruction:
- previous action source
- previous trace source
- dwell reconstruction
- observed evidence reconstruction
- validation obligation source

TeachingContext hydration:
- field
- canonical source
- availability semantics

Production scenarios:
- bootstrap
- HOLD
- dwell
- hysteresis
- repeated failure
- independent success
- assisted/answer-exposed
- UNKNOWN
- SWITCH

DecisionTrace:
- previous action ref
- material evidence refs
- transition reason
- anti-oscillation decision
- action propensity

Architecture:
- direct bypass removed
- regression test

AC Matrix:
- EXEC042-AC-* → PASS / FAIL + evidence

Tests:
- exact command
- result

Repository-wide unrelated failures:
- exact failure
- confirmed outside EXEC-042 scope

Files changed:
- path
- purpose

SPEC GAP:
- none
or
- exact blocking issue
```

不要只给文字总结。

必须实际修改代码、执行测试、完成治理收口并提交到仓库。

开始执行。