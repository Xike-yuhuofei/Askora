# SPEC-D05 — Prerequisite Diagnostic Bootstrap Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D05`  
> 冻结日期：2026-08-08  
> Owners：SYS06（诊断需求/活动规划）、SYS04（Assessment/Diagnosis）、SYS03（LearnerState projection）  
> 上游：`SPEC-D04`、`systems/03-learner-model.md`、`systems/04-assessment.md`、`systems/06-learning-planner.md`  
> 目的：冻结 Goal-specific subgraph 进入第一版 LearnerState / LearningPlan 之前的 prerequisite diagnosis，不重建第二套 assessment 或 mastery engine。

## 1. Boundary

本合同严格保持：

```text
哪些 prerequisite 需要测      → SYS06
AssessmentItem / Attempt / Result → SYS04
长期 evidence / MasteryEstimate  → SYS03
下一步 LearningPlan             → SYS06
```

SYS04 MUST NOT 修改 LearningPlan/Mastery；SYS06 MUST NOT 自行判分；SYS03 MUST NOT 自行创建 AssessmentResult。

## 2. Diagnostic Need

### D05-010

SYS06 根据：

```text
confirmed GoalKnowledgeMapping
+ GoalSpecificKnowledgeSubgraph
+ exact LearnerState/MasteryEstimate
+ time/diagnostic budget
```

构建 `DiagnosticNeed` decision record：

```yaml
diagnostic_need:
  need_id: uuid
  goal_mapping_ref: versioned_ref
  target_knowledge_unit_id: uuid
  prerequisite_knowledge_unit_ids: [uuid]
  unknown_ids: [uuid]
  unmet_ids: [uuid]
  reason_codes: [string]
  planner_version: string
  created_from_learner_state_version: integer
```

它是 SYS06 决策记录，不是 learner truth。

## 3. Unknown Semantics

### D05-020

`UNKNOWN/MISSING/LOW_CONFIDENCE` mastery MUST NOT 当 0 或 1。

若 hard prerequisite 状态未知且会改变 target feasibility，SYS06 MUST 优先创建 `DIAGNOSTIC` activity 或明确 blocked state。

若 prerequisite 已有足够 current independent evidence，则不得为固定流程强制重复测量。

## 4. Adaptive Diagnostic Baseline

MVP 采用 deterministic、可解释的 graph-adaptive diagnostic：

```text
Goal target
→ immediate/high-value prerequisite unknowns
→ choose diagnostic item
→ Attempt / AssessmentResult
→ SYS03 projection update
→ re-evaluate prerequisite feasibility
→ if failure: descend toward prerequisite causes
→ if success: continue only with unresolved decision-relevant unknowns
→ stop on sufficient feasibility or budget limit
```

### D05-030

成功测得较高层 prerequisite 不得自动把其所有祖先 MasteryEstimate 改为 mastered；是否接受何种推断证据仍由 SYS03 projector contract 决定。

SYS06 仅可因为“当前直接 prerequisite 已有足够 evidence”减少无必要测试。

## 5. Selection Objective

### D05-040

诊断 item/knowledge-unit selection SHOULD 最大化：

```text
decision relevance
prerequisite coverage
uncertainty reduction
centrality/value
expected time efficiency
```

并受：

```text
source/goal scope
assessment availability
exposure history
security
user time budget
```

约束。

Complex IRT-CAT 不属于本 bootstrap；使用现有 SYS04 information-gain heuristic 范围。

## 6. Assessment Asset Contract

### D05-050

SYS04 优先复用已 active、可稳定判分的 AssessmentItem。

若缺 item：

- SYS08 MAY 在 SYS04 约束下生成 draft candidate；
- SYS04 MUST 完成 schema/scoring/reference validation 后才可 active；
- 能 deterministic 评分的题型优先 exact/MCQ/numeric；
- grader-only solution/rubric 不得泄漏 learner-visible context。

不得为了完成诊断直接使用未验证 LLM question+answer。

## 7. Diagnostic Run

SYS04 MAY 维护 assessment workflow/run ref，但 canonical facts 仍是已有：

```text
AssessmentItem
Attempt
AssessmentResult
Diagnosis
```

`DiagnosticStarted` 等事件继续使用现有 Event Contract；不新增第二 assessment result schema。

## 8. LearnerState Update

### D05-060

每个 AssessmentResult 由 SYS03 通过现有 evidence eligibility/projector 消费。

必须保留：

```text
actual assistance
independence
assessment confidence
diagnostic confidence
delay/transfer semantics
source evidence refs
```

系统/模型/工具失败不得形成 learner failure evidence。

## 9. Stop Conditions

诊断停止条件 MUST versioned，至少允许：

```text
ALL_DECISION_RELEVANT_PREREQUISITES_RESOLVED
TARGET_READY
REMEDIATION_REQUIRED
DIAGNOSTIC_BUDGET_EXHAUSTED
NO_VALID_ASSESSMENT_ITEM
LOW_CONFIDENCE_REQUIRES_REVIEW
USER_STOPPED
SYSTEM_BLOCKED
```

固定题数/固定阈值不得被描述为普适科学常数。

### D05-070

Budget exhausted 时：

- 保留 unknown；
- Planner 使用 uncertainty-aware conservative planning；
- MUST NOT 把未测状态默认 mastered/failed。

## 10. Replanning

诊断产生 material LearnerState change 后，SYS06 MUST 使用现有 replan contract，而不是维护独立“诊断课程表”。

典型结果：

```text
unknown prerequisite → DIAGNOSTIC
unmet prerequisite   → PREREQUISITE_REMEDIATION
prerequisite ready   → LEARN_NEW / PRACTICE
already mastered     → TRANSFER_CHECK as needed
```

## 11. Idempotency / Replay

固定：

```text
Goal mapping version
+ subgraph relation refs
+ learner state version
+ diagnostic planner version
+ assessment item/version
```

必须能重放诊断决策。Replay 不调用在线 LLM；若历史 item 是模型生成，使用持久化 exact item/version。

重复 SubmitResponse/idempotency key 不得生成第二 AssessmentResult/evidence。

## 12. Failure Semantics

至少：

```text
DIAGNOSTIC_ITEM_UNAVAILABLE
DIAGNOSTIC_ITEM_INVALID
ASSESSMENT_SYSTEM_FAILURE
DIAGNOSTIC_LOW_CONFIDENCE
PREREQUISITE_GRAPH_STALE
DIAGNOSTIC_BUDGET_EXHAUSTED
LEARNER_STATE_STALE
```

任何 system failure MUST 与 learner error 分离。

## 13. Tests

MUST 覆盖：

1. unknown prerequisite → DIAGNOSTIC；
2. success 后减少无决策价值的下钻；
3. failure 后向更基础 prerequisite 下钻；
4. assessment result 经 SYS03 才影响 mastery；
5. budget exhausted 保留 unknown；
6. grader/model failure != learner failure；
7. answer-exposed success 不满足 independent evidence；
8. deterministic item route；
9. replay 不调用 LLM；
10. diagnosis 后触发现有 Planner replan。

## 14. Acceptance Criteria

- `D05-AC-001`：Goal-specific hard prerequisite 未知时可形成真实 DIAGNOSTIC activity。
- `D05-AC-002`：一次诊断 AssessmentResult 只经 SYS03 owner path 更新 LearnerState。
- `D05-AC-003`：诊断过程不会把 unknown 默认为 failed/mastered。
- `D05-AC-004`：失败可触发更基础 prerequisite 检查或 remediation，而不是重复同题无限循环。
- `D05-AC-005`：诊断预算、停止原因、输入版本均可审计。
- `D05-AC-006`：不存在第二 Assessment/Mastery/Planner truth。
- `D05-AC-007`：最终输出可直接进入现有 LearningPlanner / Adaptive Teaching Loop。

## 15. Forbidden Implementations

禁止：

- SYS06 内实现 grader；
- SYS04 直接写 mastery/plan；
- LLM 判断“用户应该会了”后直接设置 prerequisite satisfied；
- 一个失败结果永久标记 misconception/mastery；
- complex CAT/RL 作为 bootstrap 必需条件；
- 固定诊断题数作为普适教学规律。

## 16. Freeze Decision

`SPEC-D05`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。若实现需要新的 canonical assessment type、改变 SYS03 evidence semantics 或引入 complex CAT，必须先报告 `SPEC GAP`。