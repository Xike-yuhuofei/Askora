# SPEC-D04 — LearningGoal → Knowledge Mapping Contract

> 状态：**FROZEN**  
> Spec ID：`SPEC-D04`  
> 冻结日期：2026-08-08  
> Owner：SYS06 Learning Planner  
> 上游：`systems/06-learning-planner.md`、`domain/domain-model.md`、`SPEC-D03`  
> 目的：冻结从用户自然语言学习目标到可执行 target KnowledgeUnit 的映射，使现有 LearningPlanner 获得真实输入，而不是让 LLM 直接生成不可审计课程路径。

## 1. Ownership

LearningGoal / LearningObjective / LearningPlan / LearningActivity 继续由 SYS06 独占。

本合同新增的 `GoalKnowledgeMapping` 与 `GoalSpecificKnowledgeSubgraph` 是 SYS06-owned versioned decision/projection records，不获得 SYS01 知识事实写权限。

## 2. Goal Formation

### D04-010

用户可用自然语言创建 `LearningGoal` candidate。候选至少应结构化：

```yaml
title: string
topic: string
target_capabilities: [string]
application_context: string|null
success_criteria: [string]
source_document_ids: [uuid]
deadline_at: datetime|null
weekly_time_budget_minutes: integer|null
```

`confirmed|active` 仍服从 DOMAIN-010：必须经过用户确认或已冻结的显式产品规则。

### D04-011

Goal success criteria MUST 尽量可由一个或多个 AssessmentItem 测量。仅“了解、熟悉、看完”等不可验证表述必须被转换为更可测量的 capability candidate，不能直接成为唯一 success criterion。

## 3. GoalKnowledgeMapping

### D04-020

SYS06 MUST 创建 versioned mapping record：

```yaml
goal_knowledge_mapping:
  mapping_id: uuid
  mapping_version: integer
  goal_id: uuid
  goal_version: integer
  source_document_ids: [uuid]
  knowledge_graph_versions: [string]
  candidate_target_ids: [uuid]
  selected_target_ids: [uuid]
  excluded_target_ids: [uuid]
  evidence_refs: [object]
  confidence: float|null
  reason_codes: [string]
  mapper_version: string
  model_inference_refs: [uuid]
  status: candidate|confirmed|blocked|superseded
```

该 record 不是 KnowledgeUnit truth，只说明“为什么这个目标映射到这些已存在的知识对象”。

## 4. Mapping Inputs

允许读取：

- confirmed/candidate LearningGoal；
- published/verified KnowledgeUnit / Concept；
- hierarchy scope；
- published KnowledgeRelation；
- source_document scope；
- user explicit inclusion/exclusion；
- existing LearnerState 仅用于优先级/诊断规划，不得改变“目标语义本身”。

### D04-030

默认 executable mapping MUST 只选择 downstream policy 明确允许消费的 published/verified KnowledgeUnit。Candidate-only KU 可作为 `CONTENT_MODEL_INCOMPLETE` evidence/reason，但不得静默进入正式 LearningPlan。

## 5. Mapping Algorithm Baseline

MVP MUST 使用可解释、多阶段映射：

```text
normalize target capability
→ hard source scope filter
→ lexical/concept candidate recall
→ semantic candidate recall（可用时）
→ hierarchy/context fit
→ capability/knowledge-type fit
→ deterministic fusion/ranking
→ coverage + redundancy repair
→ ambiguity check
→ mapping record
```

相异打分尺度未校准时 SHOULD 使用 rank fusion，而不是直接相加原始分数。

## 6. LLM Boundary

### D04-040

LLM MAY：

- 解析自然语言目标为 capability candidate；
- 提议 search terms / concept aliases；
- 对候选 KU 做 schema-constrained relevance explanation；
- 在低置信时生成 bounded clarification question。

LLM MUST NOT：

- 新建/修改 published KnowledgeUnit；
- 绕过 source scope；
- 直接确认用户目标；
- 直接生成最终 LearningPlan；
- 用模型常识补造材料中不存在的知识节点。

模型参与时必须持久化 inference/version，replay 不重新调用当前模型。

## 7. User Confirmation Semantics

### D04-050

用户确认的是 LearningGoal 意图和必要时的 scope/重点，不要求逐个确认全部 KU。

若 mapping 存在会产生显著不同学习路径的 blocking ambiguity，SYS06 MUST：

- 标记 mapping `blocked/candidate`；
- 提供最小 bounded clarification；
- 不猜测最终 target set。

非 blocking 低风险排序差异 MAY 由 deterministic mapper 选择，并保留 reason/evidence。

## 8. Goal-specific Knowledge Subgraph

### D04-060

SYS06 可构建 versioned read-only subgraph snapshot：

```yaml
goal_subgraph:
  subgraph_id: uuid
  goal_mapping_ref: versioned_ref
  target_knowledge_unit_ids: [uuid]
  included_prerequisite_ids: [uuid]
  relation_refs: [versioned_ref]
  knowledge_graph_versions: [string]
  closure_policy_version: string
  reason_codes: [string]
```

它是规划 projection，不是第二知识图。所有 edge 必须引用 SYS01 published relation revision。

### D04-061

Goal subgraph MUST 限于 confirmed source scope + required prerequisite closure；不得默认把整本书全部 KU 加入目标。

## 9. Determinism / Versioning

相同：

```text
Goal version
+ exact knowledge revisions
+ mapper version
+ fixed persisted model inference（如有）
```

MUST 得到相同 selected target set/stable ordering。

Goal materially changed、knowledge revision changed、scope changed 时 MUST 新建 mapping version；不得覆盖历史。

## 10. Failure Semantics

至少区分：

```text
NO_PUBLISHED_TARGET_MATCH
AMBIGUOUS_GOAL_MAPPING
CONTENT_MODEL_INCOMPLETE
SOURCE_SCOPE_EMPTY
STALE_KNOWLEDGE_GRAPH
MAPPING_MODEL_UNAVAILABLE
SUCCESS_CRITERIA_UNMEASURABLE
```

模型不可用时 SHOULD 降级到 deterministic lexical/hierarchy path；不得扩展 source scope。

## 11. Tests

MUST 覆盖：

1. goal source scope hard filter；
2. 一般“理解全书核心思想”映射为有限 target set；
3. 明确专题目标只映射相关 KU；
4. candidate-only KU 不进入 executable mapping；
5. blocking ambiguity 触发 clarification；
6. model unavailable deterministic fallback；
7. fixed input/version deterministic mapping；
8. goal change creates new mapping version；
9. mapping 不修改 SYS01 knowledge truth。

## 12. Acceptance Criteria

- `D04-AC-001`：每个 selected target KU 有 mapping reason/evidence 和 exact knowledge version。
- `D04-AC-002`：用户 Goal 不再要求人工预填 target KU id 才能进入主流程。
- `D04-AC-003`：LLM mapping proposal 不具有知识发布或 Goal confirmation 权限。
- `D04-AC-004`：source scope 不能被 mapper/LLM 静默扩大。
- `D04-AC-005`：Goal-specific subgraph 只引用 SYS01 canonical relation，不复制第二 graph truth。
- `D04-AC-006`：mapping blocking ambiguity 不被静默猜测。
- `D04-AC-007`：现有 LearningPlanner contract 无需重写即可消费 selected target ids。

## 13. Forbidden Implementations

禁止：

- `LLM(goal) → full course JSON → directly persist LearningPlan`；
- 用目录章节作为唯一 target mapping；
- candidate KU 当 published truth；
- mapper 修改 prerequisite graph；
- learner mastery 反向改变用户目标语义；
- 未保存模型推断结果的在线 LLM replay。

## 14. Freeze Decision

`SPEC-D04`：**FROZEN / UI-02B2 ADDITIVE**。`selected_target_ids` 的稳定顺序按 deterministic
fusion rank 降序；第一个 target 是首轮 prerequisite diagnostic 的
`primary_diagnostic_target_id`。该规则只选择首轮诊断入口，不删除其余目标，也不改变完整
Goal subgraph/plan scope。若实现必须新增跨系统公共 Goal 类型、改变 LearningGoal owner 或改变
用户确认语义，必须先报告 `SPEC GAP`。
