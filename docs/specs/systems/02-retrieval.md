# SYS02 — Retrieval & Knowledge Supply

> Spec ID：`SYS02-*`  
> 对应设计：4.2 检索与知识供给  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS02-001

4.2 的唯一职责是在 4.5 已确定教学动作、来源范围与答案暴露约束后，从 4.1 的知识基础设施中选择本轮可使用的最小高质量证据集合 `EvidenceBundle`。

### SYS02-002

4.2 独占：检索候选进入本轮 EvidenceBundle 的最终选择、压缩、组合、引用验证和 RetrievalTrace。

## 2. Non-responsibility

4.2 MUST NOT：

- 选择 TeachingAction；
- 修改 LearnerState/MasteryEstimate；
- 对 Attempt 判分；
- 决定 LearningPlan/ReviewSchedule；
- 生成最终用户表达；
- 把自动摘要/图社区摘要提升为无来源事实。

## 3. Owned State

4.2 可拥有：

- TeachingRetrievalRequest；
- RetrievalPlan；
- RetrievalCandidate；
- RetrievalTrace；
- EvidenceBundle；
- 可重建检索 cache/projection 状态。

不得保存可写 LearnerState 副本。

## 4. Inputs

允许读取：

- TeachingAction / TeachingContext subset；
- target KnowledgeUnit/Concept；
- SourceChunk/SourceSpan；
- published knowledge relations；
- source scope / ACL；
- index versions；
- 4.4 grader/rubric 证据请求。

### SYS02-010

教学策略给出的 `answer_exposure_max` 是硬上限，检索层可以进一步收紧但 MUST NOT 放宽。

## 5. Outputs

输出必须是结构化 `EvidenceBundle`，而不是仅返回拼接字符串。

至少包括：

- selected evidence；
- SourceSpan anchors；
- pedagogical roles；
- exposure level / allowed use；
- retrieval/index versions；
- conflict/missing role signal；
- RetrievalTrace id。

## 6. Domain Objects

公共 `EvidenceBundle` 遵循 `domain-model.md`。

内部对象：

```text
TeachingRetrievalRequest
RetrievalPlan
RetrievalCandidate
RetrievalTrace
```

暴露等级固定：

```text
L0 条件/已知事实
L1 方向性线索
L2 局部下一步
L3 关键结构
L4 完整解答
```

## 7. Commands

建议：

```text
BuildEvidenceBundle
RetrieveForAssessment
ValidateCitation
InvalidateRetrievalCache
```

请求必须绑定 source scope、教学动作/用途、允许暴露级别、上下文预算和 index version policy。

## 8. Events

至少产生：

- `ContentRetrieved`
- `RetrievalFailed`

关键 EvidenceBundle 选择 MUST 写 DecisionTrace。

## 9. Algorithms

### SYS02-020：MVP Baseline

MVP 默认：

```text
BM25/lexical
+ dense retrieval
→ RRF fusion
→ hard policy filter
→ cross-encoder/高精度 rerank（可用时）
→ coverage + budget selection
→ MMR/dedup
→ extractive compression优先
→ citation validation
```

### SYS02-021：教学适用性

排序目标不能只有 semantic relevance，至少应考虑：

```text
relevance
coverage
pedagogical_role_fit
learner_stage_fit（来自只读 context）
source_quality
citation_quality
- leakage_risk
- redundancy
- token_cost
```

### SYS02-022：RRF

多路分数量纲未校准时，MVP SHOULD 使用 RRF 作为稳定融合基线，不应直接线性相加异构原始分数。

### SYS02-023：Graph/Hierarchy Route

GraphRAG/层级检索 MAY 按问题类型启用：

- 前置/跨章节关系 → graph；
- 长文档论证范围 → hierarchy/page tree；
- 局部事实/定义 → lexical+dense。

不得所有请求默认 GraphRAG。

### SYS02-024：高级排序

Learning-to-Rank 只有在具有标注/真实 outcome 数据且稳定优于 RRF+rerank baseline 后才能成为主排序。Bandit 只可用于安全 route/reranker variant，并需 propensity logging；当前 v0.2 不实施。

## 10. Persistence

### SYS02-030

检索 index/cache 是可重建 projection，不得成为知识事实源。

### SYS02-031

Cache key 至少需要考虑：

- source/document revision；
- segmentation/index/embedding/reranker version；
- retrieval request semantics；
- answer exposure level；
- source scope/ACL。

不得跨不同 exposure/ACL 复用导致泄漏。

### SYS02-032

EvidenceBundle 是一次决策结果，SHOULD 不原地修改；新的检索生成新 bundle。

## 11. Failure Semantics

必须区分：

- no result；
- low confidence；
- required pedagogical role missing；
- source conflict；
- invalid citation anchor；
- stale index；
- reranker unavailable；
- ACL denied。

降级顺序可为：

```text
reranker unavailable → RRF score
vector unavailable → lexical-only
optional graph unavailable → skip graph
citation invalid → drop evidence
required evidence absent → fail/return MissingEvidence
```

### SYS02-040

缺失证据时 MUST NOT 让 4.8 用模型常识假装用户资料有答案。需要改变教学动作时返回 4.5 下一轮重新决策。

## 12. Idempotency

相同 request + fixed indexes/config SHOULD 可重复得到稳定排序（模型非确定部分需保存版本与必要 tie-break）。

RetrievalTrace 与 bundle 创建需有 request id/idempotency strategy，避免一次教学动作重复创建语义重复的副作用记录。

## 13. Observability

必须记录：

- 每路 candidate rank；
- RRF/重排分；
- hard filter reason；
- selected pedagogical role；
- exposure filtering；
- source/index versions；
- citation validation；
- latency/caching。

关键指标：Recall@K、MRR、nDCG、role coverage、citation precision、answer leakage rate、context redundancy、token efficiency、p95 latency。

## 14. Security

### SYS02-050

ACL/source_scope 是 hard filter，必须在最终 bundle 前执行，且缓存不得绕过。

### SYS02-051

不可信文档里的指令不能提升 tool/model 权限，也不能突破 exposure policy。

### SYS02-052

Grader-only evidence 与 learner-visible evidence 必须有明确可见性分离，防止参考答案进入学习者生成上下文。

## 15. Tests

必须覆盖：

- lexical+dense 混合召回；
- RRF deterministic fixture；
- exposure L0-L4 filter；
- ACL filter；
- source revision/cache invalidation；
- duplicate/MMR；
- invalid anchor 被剔除；
- reranker/embedding 故障降级；
- missing role 返回结构化 signal；
- grader-only evidence 不进入 learner-visible output；
- prompt injection 文本不改变 retrieval policy。

## 16. Acceptance Criteria

- `SYS02-AC-001`：每个 EvidenceBundle item 可回溯 SourceSpan。
- `SYS02-AC-002`：无提示评估时 L4 完整答案无法进入 learner-visible bundle。
- `SYS02-AC-003`：reranker 故障可降级，不改变 TeachingAction。
- `SYS02-AC-004`：ACL 不同的请求不会命中不安全缓存。
- `SYS02-AC-005`：缺必需证据时返回 missing signal，不伪造证据。
- `SYS02-AC-006`：RetrievalTrace 可解释候选被纳入/排除原因。
- `SYS02-AC-007`：图/向量索引重建不会改变 canonical knowledge facts。

## 17. Forbidden Implementations

禁止：

- 单一 embedding top-k 作为全部检索；
- 让 Agent 自由搜索后直接回答且无 RetrievalTrace；
- 让检索层自行决定教学动作；
- 把 LLM 摘要当原始来源；
- 无 citation anchor 的资料型回答当已验证证据；
- 缓存忽略 exposure/ACL/version；
- 检索失败后用模型常识冒充资料内容；
- GraphRAG 成为所有请求默认路径。

## Legacy Mapping

当前：

```text
apps/backend/app/services/documents/rag_service.py
apps/backend/app/services/documents/embedding_service.py
apps/backend/app/services/knowledge_graph/kg_service.py
```

应逐步把 retrieval/ranking/EvidenceBundle 职责从 `documents/` 拆到 SYS02；知识事实与 graph canonicalization 仍归 SYS01。
