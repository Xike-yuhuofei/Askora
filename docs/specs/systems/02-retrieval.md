# SYS02 — Retrieval & Knowledge Supply

> Spec ID：`SYS02-*`  
> 对应设计：4.2 检索与知识供给  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS02-001

SYS02 的唯一职责是在 SYS05 已确定 TeachingAction、来源范围与暴露 envelope 后，从 SYS01 知识基础设施中选择本轮可使用的最小高质量 `EvidenceBundle`。

### SYS02-002

SYS02 独占 EvidenceBundle 的最终选择、压缩、组合、引用验证和 RetrievalTrace；MUST NOT 选择 TeachingAction、修改 LearnerState、判分 Attempt、修改 LearningPlan/ReviewSchedule 或生成最终用户表达。

## 2. Inputs / Outputs

允许读取 TeachingAction/TeachingContext subset、KnowledgeUnit/Concept、SourceSpan/Chunk、published relations、source scope/ACL、index versions、SYS04 rubric evidence request。

输出 MUST 是结构化 EvidenceBundle，至少包含 selected evidence、SourceSpan anchors、pedagogical roles、`answer_exposure`、allowed use、index versions、missing/conflict signal、RetrievalTrace id。

### SYS02-200 — v0.3 Exposure Envelope

SYS02 MUST 使用 canonical：

```text
answer_exposure = NONE | PARTIAL | COMPLETE
```

TeachingAction 的 `answer_exposure` 是硬上限。SYS02 MAY 进一步收紧，MUST NOT 放宽。历史 `answer_exposure_max` 与 L0-L4 exposure 只允许兼容读取/audit，MUST NOT 继续作为 v0.3 writer contract。

### SYS02-201 — Tightening Only

Evidence item 的 exposure classification MUST 可映射到 TeachingAction envelope；任何无法可靠分类的 candidate SHOULD 按更严格等级处理或剔除，不能因“不确定”放宽可见性。

## 3. Retrieval Baseline

### SYS02-020

MVP baseline：

```text
BM25/lexical + dense retrieval
→ RRF fusion
→ hard policy/ACL/exposure filter
→ high-precision rerank（可用时）
→ coverage + budget selection
→ dedup/MMR
→ extractive compression 优先
→ citation validation
```

### SYS02-021

排序 SHOULD 同时考虑 relevance、coverage、pedagogical_role_fit、只读 learner/context fit、source/citation quality、leakage risk、redundancy、token cost；MUST NOT 只有 semantic relevance。

### SYS02-022

异构分数量纲未校准时 SHOULD 使用 RRF，MUST NOT 直接线性相加原始分数。

### SYS02-023

Graph/hierarchy route MAY 按问题类型启用；MUST NOT 默认所有请求使用 GraphRAG。

## 4. Persistence / Cache

### SYS02-030

index/cache 是可重建 projection，MUST NOT 成为 knowledge truth。

### SYS02-031

Cache key 至少包含 document revision、segmentation/index/embedding/reranker version、request semantics、canonical `answer_exposure`、source scope/ACL。不同 exposure/ACL MUST NOT 不安全复用。

### SYS02-032

EvidenceBundle SHOULD immutable；新检索生成新 bundle。

## 5. Failure Semantics

必须区分 no result、low confidence、required role missing、source conflict、invalid citation、stale index、reranker unavailable、ACL denied、exposure classification uncertain。

### SYS02-040

缺失必需证据时 MUST NOT 让 SYS08 用模型常识冒充用户资料答案；若需改变 TeachingAction，返回 SYS05 下一轮重新决策。

## 6. Idempotency / Replay

相同 request + fixed indexes/config SHOULD 产生稳定排序；非确定组件需固定版本与 stable tie-break。RetrievalTrace/bundle 创建 MUST 有 request id/idempotency strategy。

## 7. Observability

必须记录 candidate rank、fusion/rerank score、hard filter reason、pedagogical role、exposure filtering、source/index versions、citation validation、latency/cache。关键指标 MAY 包含 Recall@K、MRR、nDCG、role coverage、citation precision、answer leakage rate、context redundancy、token efficiency、p95 latency。

## 8. Security

### SYS02-050

ACL/source_scope 是 hard filter，MUST 在最终 bundle 前执行且 cache 不得绕过。

### SYS02-051

不可信文档指令 MUST NOT 提升 tool/model 权限或突破 TeachingAction exposure policy。

### SYS02-052

Grader-only 与 learner-visible evidence MUST 明确分离，参考答案不得错误进入 learner-visible context。

## 9. Tests

必须覆盖：lexical+dense、RRF deterministic fixture、`NONE/PARTIAL/COMPLETE` exposure filter、tightening-only property、ACL/cache、revision invalidation、duplicate/MMR、invalid anchor、reranker/embedding degradation、missing role、grader-only isolation、prompt injection。

## 10. Acceptance Criteria

- `SYS02-AC-001`：每个 EvidenceBundle item 可回溯 SourceSpan。
- `SYS02-AC-002`：独立评估时不允许的 COMPLETE answer 无法进入 learner-visible bundle。
- `SYS02-AC-003`：reranker 故障可降级，不改变 TeachingAction。
- `SYS02-AC-004`：ACL/exposure 不同请求不会命中不安全 cache。
- `SYS02-AC-005`：缺必需证据返回 missing signal，不伪造证据。
- `SYS02-AC-006`：RetrievalTrace 可解释纳入/排除原因。
- `SYS02-AC-007`：索引重建不改变 canonical knowledge facts。
- `SYS02-AC-201`：SYS02 只能收紧，不能扩大 SYS05 answer exposure envelope。

## 11. Legacy Mapping

v0.2 `SYS02-010 answer_exposure_max` 与 L0-L4 exposure 被 `SYS02-200/201` supersede。旧值 MAY 由 read adapter 映射为 `NONE|PARTIAL|COMPLETE`；lossy/ambiguous mapping MUST 标记 migration reason。所有 active writers 切换且历史兼容完成后旧字段 SHOULD retirement。

## 12. Forbidden Implementations

禁止：单一 embedding top-k 作为全部检索；Agent 自由搜索后无 trace 直接回答；SYS02 自行决定 TeachingAction；LLM 摘要充当原始来源；无 citation anchor 的资料型回答当已验证证据；cache 忽略 exposure/ACL/version；检索失败后模型常识冒充资料；GraphRAG 默认所有请求；继续写 L0-L4/`answer_exposure_max` 为 canonical truth。