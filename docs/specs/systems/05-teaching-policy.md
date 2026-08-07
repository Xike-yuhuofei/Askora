# SYS05 — Teaching Policy

> Spec ID：`SYS05-*`  
> 对应设计：4.5 教学策略选择  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS05-001

4.5 的唯一职责是在当前 LearningObjective/LearningActivity 已确定的前提下，根据 LearnerState、最近 AssessmentResult、Review context 和用户约束选择下一步具体 `TeachingAction`。

一句话：**决定当前怎么教。**

## 2. Non-responsibility

4.5 MUST NOT：

- 选择长期学习目标或重排 LearningPlan；
- 修改 LearnerState/MasteryEstimate；
- 对 Attempt 重新评分；
- 计算 next_due_at；
- 自己执行模型/工具；
- 自己重选 EvidenceBundle；
- 把策略逻辑交给 LLM 自由决定。

## 3. Owned State

4.5 独占：

- TeachingStrategy definition/version；
- TeachingAction；
- scaffold/hint level；
- answer_exposure_max；
- evidence requirements；
- current action success/failure/exit conditions；
- policy parameters/version。

TeachingAction 是不可变决策；执行状态归 4.8。

## 4. Inputs

允许读取：

- LearningObjective；
- current LearningActivity；
- LearnerState/MasteryEstimate snapshot；
- recent AssessmentResult；
- active misconception hypothesis；
- ReviewSchedule/retrievability read-only context；
- user request/constraints：直接讲解、时间预算、无障碍等；
- prior TeachingAction outcome。

### SYS05-010

用户明确要求“直接告诉我”可以改变候选动作，但不自动取消安全、评估有效性或资料边界约束。

## 5. Outputs

输出必须为结构化：

- TeachingAction；
- TeachingContext snapshot/reference；
- EvidenceRequest requirements；
- DecisionTrace payload；
- 必要的 PolicyDecisionMade event。

## 6. Domain Objects

遵循 `domain-model.md`。

默认策略族：

```text
DIRECT_INSTRUCTION
WORKED_EXAMPLE_FADING
SOCRATIC_PROBING
GUIDED_PRACTICE
ERROR_REMEDIATION
RETRIEVAL_PRACTICE
PRODUCTIVE_FAILURE
TRANSFER_CHALLENGE
METACOGNITIVE_REFLECTION
```

### SYS05-020

TeachingAction 至少包含：action type、strategy version、scaffold/hint、answer exposure、evidence requirements、success/failure conditions、reason codes、policy version。

## 7. Commands

建议：

```text
SelectTeachingAction
ReevaluateTeachingAction
ActivateTeachingStrategyVersion
RetireTeachingStrategyVersion
```

不得暴露 `SetMastery`、`ReplanCourse`、`SetNextReviewAt`。

## 8. Events

消费：

- AssessmentResult available；
- LearnerState changed；
- Activity selected；
- review context/due；
- execution failure/feedback。

产生：

- `PolicyDecisionMade`

若改变教学语义，必须新建 TeachingAction，不得修改旧 action。

## 9. Algorithms

### SYS05-030：MVP Baseline

固定演进顺序：

```text
hard constraints
→ strategy state machine
→ candidate generation
→ weighted action scoring
→ deterministic tie-break
→ TeachingAction
```

### SYS05-031：Hard constraints

至少包含：

- 无提示评估禁止高答案暴露；
- 先备知识严重缺失时不得持续高难独立任务；
- 连续失败存在上限，需增加支架/切换讲解；
- 用户已经稳定独立成功时应降低不必要支架；
- 低 LearnerState confidence 时优先安全诊断/低风险动作；
- 4.6 已固定 objective，不得偷偷切目标。

硬约束不得通过软评分被抵消。

### SYS05-032：State machine baseline

```text
UNKNOWN → DIAGNOSE
NOVICE → EXPLAIN / WORKED_EXAMPLE
EMERGING → SOCRATIC / GUIDED_PRACTICE
PRACTICING → FADED_EXAMPLE / PRACTICE
INDEPENDENT → NO_HINT_RETRIEVAL
RETAINED → DELAYED_RETRIEVAL
TRANSFER → TRANSFER_TASK
```

该状态机是策略控制映射，不是新的 LearnerState truth。

### SYS05-033：Weighted score

可采用：

```text
expected_learning_value
+ diagnostic_value
+ stage_fit
- hint_dependency_risk
- cognitive_load_penalty
- time_cost
```

权重必须版本化、可回放、可离线比较。

### SYS05-034：策略演进

必须按：

```text
规则
→ 启发式评分
→ 监督 outcome model
→ Contextual Bandit
→ Offline RL
→ 受约束在线 RL
```

逐级证明收益。

v0.2 MUST 停在规则/状态机/启发式评分，不实施 RL。

### SYS05-035：Bandit/RL future guard

未来若实验：

- 只能在 hard constraint 过滤后的安全动作集合探索；
- reward 以之后无提示成功、延迟保持、迁移为主；
- 必须记录 action availability 和 propensity；
- 不能用聊天时长/点赞作为主 reward。

## 10. Persistence

- TeachingStrategy 使用 semantic version；
- TeachingAction append-only；
- policy weights/config versioned；
- DecisionTrace 关联 input snapshot versions；
- 当前策略运行不得依赖不可审计的自由 Prompt 状态。

### SYS05-040

正在执行的 TeachingAction 固定 policy/strategy version；策略配置热更新只影响新 action。

## 11. Failure Semantics

- LearnerState missing/stale → conservative diagnostic/default policy；
- AssessmentResult low confidence → 降低该信号权重，不自行重评；
- no eligible actions → explicit policy failure + safe fallback action；
- conflicting hard rules → SPEC/config error，不由 LLM仲裁；
- 4.8 execution failure → 可原动作重试或返回 4.5 新决策；
- policy config unavailable → previous stable/default version。

### SYS05-050

策略执行失败与策略业务失败必须分开。模型供应商超时不自动等于“应换教学策略”。

## 12. Idempotency

相同 TeachingContext snapshot + fixed policy version + fixed experiment assignment SHOULD 得到同一 TeachingAction。

同一 decision request 重试不得创建多个语义相同 action，除非明确需要新决策轮次。

## 13. Observability

必须记录：

- TeachingContext input versions；
- feasible candidates；
- hard-filter reason codes；
- scores/weights；
- selected action；
- policy/strategy version；
- scaffold changes；
- answer exposure；
- experiment variant（如有）。

指标：constraint violation=0、expert agreement、decision p95、fallback rate、strategy switch frequency、hint dependency、scaffold fading、下一次无提示成功、延迟保持、迁移。

## 14. Security

- 4.8/LLM 不能篡改 action/exposure；
- user content/prompt injection 不得改变 policy config；
- user override 只能在产品允许范围内形成约束输入；
- 评估期间的 answer exposure 是高影响安全/有效性边界。

## 15. Tests

必须覆盖：

- novice → explain/worked example；
- high hint dependency → scaffold reduction/独立检验合理行为；
- prerequisite gap；
- repeated failure escalation；
- explicit user direct explanation request；
- assessment no-answer hard constraint；
- low-confidence learner state；
- deterministic tie-break；
- stale/missing state fallback；
- 4.8 不能修改 TeachingAction；
- policy version replay。

## 16. Acceptance Criteria

- `SYS05-AC-001`：每个 TeachingAction 可追溯到输入状态版本、候选和 reason codes。
- `SYS05-AC-002`：无提示 assessment 不能选择/执行超过暴露上限的动作。
- `SYS05-AC-003`：策略层不能修改 LearningPlan 或 ReviewSchedule。
- `SYS05-AC-004`：同输入+同 policy version 可重复产生相同决策。
- `SYS05-AC-005`：连续失败存在显式退出/支架升级机制，不会无限苏格拉底追问。
- `SYS05-AC-006`：连续独立成功后能减少不必要支架。
- `SYS05-AC-007`：模型/工具故障不会被误解释为 learner state 改变。

## 17. Forbidden Implementations

禁止：

- `LLM.choose_strategy()` 直接成为最终策略 owner；
- 把全部策略写在自由 Prompt 里而无版本化 policy；
- Teaching Policy 自行切换 LearningObjective；
- 用点赞/会话长度优化教学动作；
- 在线 RL 自由探索答案泄漏或高风险动作；
- 同一个 TeachingAction 在执行中被原地改语义；
- 4.8 因生成方便而提高 exposure level；
- 永久默认苏格拉底式提问，无新手讲解/支架退出机制。

## Legacy Mapping

当前主要相关：

```text
apps/backend/app/engines/socratic/strategy_selector.py
apps/backend/app/engines/socratic/strategy_library.py
apps/backend/app/data/strategies/
apps/backend/app/engines/state_graph.py
```

选择策略的业务逻辑应从具体 Socratic engine 中抽出；response generation、guardrail 与引擎执行归 SYS08。
