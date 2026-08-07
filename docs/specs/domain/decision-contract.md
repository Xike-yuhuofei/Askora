# Askora Decision Trace Contract

> Spec ID 范围：`DECISION-*`  
> 状态：Canonical Implementation Contract  
> 版本：v1.0

## 1. 目的

Askora 的关键决策必须可以回答：**当时看到了什么、有哪些候选、受什么约束、为什么选择这个结果、由哪个算法/策略/模型版本产生。**

`DecisionTrace` 是审计记录，不是新的业务状态 owner。

## 2. 所有权

### DECISION-001

做出业务决策的领域系统负责产生 DecisionTrace payload；4.8 的 Decision Ledger 负责 append-only 持久化、索引和查询。

### DECISION-002

4.8 不得修改 `selected_action`、`reason_codes` 或其他领域决策语义来“修复”记录。

## 3. `DecisionTrace v1`

```yaml
decision_trace:
  decision_id: uuid
  decision_type: string
  schema_version: "1.0"

  owner_system: content_knowledge|retrieval|learner_model|assessment|teaching_policy|learning_planner|review_scheduler|ai_orchestration

  inputs:
    - entity_type: string
      entity_id: uuid|string
      version: string|integer|null

  candidates: [object]
  selected: object
  constraints: [object]
  reason_codes: [string]
  confidence: float|null

  algorithm:
    algorithm_id: string
    algorithm_version: string
    model_inference_ids: [uuid]
    prompt_versions: [string]

  experiment:
    experiment_id: string|null
    variant_id: string|null
    propensity: float|null

  created_at: datetime
  correlation_id: uuid
  trace_id: string
```

## 4. 必须记录的决策

### DECISION-010：4.1 高影响知识发布

至少记录：

- KnowledgeUnit 合并/拆分；
- hard prerequisite 发布/拒绝；
- 无法自动确定而进入人工审核的高影响关系。

### DECISION-011：4.2 EvidenceBundle 选择

必须记录：

- 检索请求；
- 主要候选/排名来源；
- 硬过滤原因；
- 最终 selected evidence；
- exposure 过滤；
- missing/conflict。

### DECISION-012：4.3 MasteryEstimate 更新

必须记录：

- 使用的 evidence ids；
- evidence weights；
- prior state version；
- new estimate version；
- algorithm version；
- reason codes。

### DECISION-013：4.4 非平凡评估

开放题、模型辅助评分、评估器冲突或误区判断必须记录：

- evaluator candidates/results；
- rubric/version；
- adjudication constraints；
- selected AssessmentResult。

纯确定性 exact grader MAY 以精简 trace 记录。

### DECISION-014：4.5 TeachingAction

必须记录全部可行动作候选、硬约束过滤、评分、最终动作和 reason codes。

### DECISION-015：4.6 Plan / Replan

必须记录：

- feasible candidates；
- prerequisite/deadline/time constraints；
- priority factors；
- selected activities；
- replan trigger。

### DECISION-016：4.7 ReviewSchedule 更新

必须记录：

- prior memory state；
- valid retrieval evidence；
- desired retention；
- new next_due_at；
- scheduler/model version。

### DECISION-017：4.8 高影响模型路由与降级

以下情况必须记录：

- 隐私等级导致的本地/云模型选择；
- 主模型失败后 fallback；
- 工具权限拒绝；
- 输出验证导致重试/降级；
- 影响任务质量/成本的重要 route。

## 5. Reason Codes

### DECISION-020

每个关键决策 MUST 至少有一个稳定、机器可查询的 `reason_code`。自然语言解释只能作为附加显示，不得替代 reason code。

建议格式：

```text
<DOMAIN>_<CAUSE>
```

例如：

```text
TEACH_HIGH_HINT_DEPENDENCY
TEACH_PREREQUISITE_GAP
RETRIEVAL_EXPOSURE_LIMIT
RETRIEVAL_CITATION_INVALID
ASSESS_LOW_GRADER_CONFIDENCE
MASTERY_NO_DELAYED_EVIDENCE
PLAN_HARD_PREREQUISITE
PLAN_REVIEW_OVERDUE
REVIEW_RECALL_FAILURE
ROUTE_PROVIDER_UNAVAILABLE
```

### DECISION-021

Reason code 语义一旦发布，不得改变含义复用同一个 code。语义变化需要新 code 或新主版本。

## 6. Candidate 与约束

### DECISION-030

对存在真实候选选择的决策，trace MUST 保存足够候选摘要以支持离线 replay/counterfactual comparison。

不要求保存巨量 raw context，但必须能重建核心 feature/score/eligibility。

### DECISION-031

硬约束与软评分必须分开记录。

例如 Teaching Policy：

```text
hard constraint: assessment_no_answer_exposure
soft score: expected_learning_value = 0.74
```

不得把硬安全规则仅表示成一个可被高分抵消的 penalty。

## 7. Confidence

### DECISION-040

`confidence` 只在有明确定义/校准方法时使用。若没有校准依据，字段应为 null 或使用离散 reason code，不得让 LLM 自报 0.93 作为系统置信度。

## 8. 模型参与

### DECISION-050

模型参与关键决策时必须通过 `model_inference_ids` 关联 `ModelInference`，而不是只记录模型名字。

### DECISION-051

最终领域决策与模型输出必须分开：

```text
ModelInference = 模型产生了什么
DecisionTrace = 领域系统最终接受了什么、为什么
```

## 9. 实验与策略学习

### DECISION-060

任何 A/B、Bandit 或策略实验必须记录：

- experiment_id；
- variant_id；
- 可选动作集合；
- behavior policy/propensity（需要 OPE 时）。

### DECISION-061

没有 propensity/action availability 日志，不得声称可以可靠进行 IPS/SNIPS/DR 等 off-policy evaluation。

### DECISION-062

实验 reward 的主目标不得使用聊天时长、点击率或点赞替代学习结果。它们只能作为体验 guardrail/辅助指标。

## 10. Replay 与 Counterfactual

### DECISION-070

DecisionTrace 必须支持至少以下用途：

```text
历史解释
→ 同版本 replay
→ 新旧算法 shadow compare
→ counterfactual candidate compare
→ 回滚定位
```

### DECISION-071

重放旧决策时，若输入实体的历史版本不可取得，则该决策不能标记为“可完整重放”；必须显式标记 replayability 缺口。

## 11. 用户可解释性

### DECISION-080

面向用户的解释 SHOULD 从稳定 reason codes 和真实 evidence 生成，不得让 LLM 凭空编造“为什么系统这样安排”。

例：

```text
系统安排复习
→ PLAN_REVIEW_OVERDUE + ReviewSchedule v12
→ 用户解释：“该知识点已超过建议复习时间。”
```

## 12. 持久化

### DECISION-090

DecisionTrace MUST append-only。更正通过新 trace/关联 correction record 完成。

### DECISION-091

Decision Ledger SHOULD 支持按以下字段索引：

- decision_id；
- decision_type；
- owner_system；
- correlation_id；
- trace_id；
- input entity id；
- algorithm version；
- experiment id；
- created_at。

## 13. Acceptance Criteria

- `DECISION-AC-001`：任一 TeachingAction 可追溯到 LearnerState/AssessmentResult/Plan 输入版本。
- `DECISION-AC-002`：任一 MasteryEstimate 更新可列出 source evidence 和算法版本。
- `DECISION-AC-003`：EvidenceBundle 中被排除的高暴露候选可通过 reason code 解释。
- `DECISION-AC-004`：Plan replan 可说明触发原因和前后版本。
- `DECISION-AC-005`：模型 fallback 有 ModelInference 与 route trace。
- `DECISION-AC-006`：用户看到的“为什么”解释能映射到真实 reason codes，而非模型自由生成原因。

## 14. Forbidden Implementations

禁止：

- 只保存最终动作，不保存关键输入版本；
- 只保存自然语言“因为用户需要帮助”而无 reason code；
- 将 ModelInference 与 DecisionTrace 合成一个对象；
- Decision Ledger 反向修改领域业务状态；
- 没有实验分配/propensity 日志却训练或评估策略并宣称无偏；
- 用点赞、会话时长作为教学策略主要 reward；
- LLM 为历史决策事后编造理由。
