# SYS02 — Retrieval & Knowledge Supply

> Spec ID：`SYS02-*`  
> 对应设计：4.2 检索与知识供给  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + v1 Workspace Scope Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. Responsibility

### SYS02-001

SYS02 的唯一职责是在 SYS05 已确定 TeachingAction、来源范围与暴露 envelope 后，从 SYS01 知识基础设施中选择本轮可使用的最小高质量 `EvidenceBundle`。

### SYS02-002

SYS02 独占 EvidenceBundle 的最终选择、压缩、组合、引用验证和 RetrievalTrace；MUST NOT 选择 TeachingAction、修改 LearnerState、判分 Attempt、修改 LearningPlan/ReviewSchedule、修改 Workspace membership 或生成最终用户表达。

### SYS02-003 — RAG Is Infrastructure, Not Product Core

RAG / BM25 / Embedding / Vector Index / Graph route 是知识供给基础设施，不是 Askora 的产品本体。正确依赖方向：

```text
Learning Goal / LearningActivity
→ Teaching Policy
→ Knowledge Need / TeachingAction
→ RetrievalScope
→ Retrieval
→ EvidenceBundle
→ SYS08 execution
```

MUST NOT 把 `Document → Chunk → Embedding → Chat` 建成默认产品主链。

## 2. Inputs / Outputs

允许读取 TeachingAction/TeachingContext subset、KnowledgeUnit/Concept、SourceSpan/Chunk、published relations、RetrievalScope、index versions、SYS04 rubric evidence request。

输出 MUST 是结构化 EvidenceBundle，至少包含 selected evidence、SourceSpan anchors、pedagogical roles、`answer_exposure`、allowed use、index versions、missing/conflict signal、RetrievalTrace id。

### SYS02-100 — RetrievalScope

v1 production RetrievalScope MUST 显式包含：

```yaml
retrieval_scope:
  workspace_id: uuid            # REQUIRED
  project_ids: [uuid]           # optional narrowing
  material_ids: [uuid]          # optional narrowing
  knowledge_unit_ids: [uuid]    # optional narrowing
  session_context: object|null  # optional narrowing/context
```

规则：

- `workspace_id` 是 hard scope，不得省略或用 LocalOwner 替代；
- `project_ids` 只能引用同一 Workspace 内的 LearningProject；
- `material_ids` 只能引用同一 Workspace 内的 Material；
- 默认不得跨 Workspace 搜索；
- v1 不存在独立 Global Material Library retrieval scope；
- 若调用方无法确定 workspace，MUST fail closed，而不是扩大到全部本地数据。

### SYS02-101 — Scope Intersection

若 TeachingAction、LearningActivity、Project、Material 或 explicit request 同时提供 scope，SYS02 MUST 取安全交集/明确允许范围，不得通过 union 自动扩大可见资料。

任何跨 Workspace ref MUST 返回稳定 scope violation / invalid ref，而不是静默忽略 workspace filter。

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

v1 baseline：

```text
workspace/material hard scope
→ BM25/lexical + dense retrieval (when available)
→ RRF fusion
→ hard policy/exposure filter
→ high-precision rerank（可用时）
→ coverage + budget selection
→ dedup/MMR
→ extractive compression 优先
→ citation validation
```

Embedding/provider unavailable 时 SHOULD 保留 lexical/local fallback，不得把“没有 embedding”解释为资料不可用。

### SYS02-021

排序 SHOULD 同时考虑 relevance、coverage、pedagogical_role_fit、只读 learner/context fit、source/citation quality、leakage risk、redundancy、token cost；MUST NOT 只有 semantic relevance。

### SYS02-022

异构分数量纲未校准时 SHOULD 使用 RRF，MUST NOT 直接线性相加原始分数。

### SYS02-023

Graph/hierarchy route MAY 按问题类型启用；MUST NOT 默认所有请求使用 GraphRAG，也 MUST NOT 因有图关系强制引入专用图数据库。

### SYS02-024 — Source-grounded vs External Model Knowledge

EvidenceBundle 只代表可验证来源供给。若 SYS08/教学动作允许使用模型自身知识补充解释，该内容 MUST 在执行/展示层与 Source-grounded claim 区分；SYS02 MUST NOT 为模型常识伪造 SourceSpan/citation。

## 4. Persistence / Cache

### SYS02-030

index/cache 是可重建 projection，MUST NOT 成为 knowledge truth。

### SYS02-031

Cache key 至少包含：

```text
workspace_id
project/material/KU scope fingerprint
material/source revision
segmentation/index/embedding/reranker version
request semantics
canonical answer_exposure
allowed-use/grader boundary
```

不同 Workspace、scope、exposure 或 allowed-use MUST NOT 不安全复用 cache。

### SYS02-032

EvidenceBundle SHOULD immutable；新检索生成新 bundle。

### SYS02-033 — Local Index Rebuildability

Vector/Lexical/Graph projection 被删除后 MUST 可从 durable Material/SourceSpan/KnowledgeUnit + exact version configuration 重建。

Index rebuild failure MUST 标记 STALE/PARTIAL/MISSING，不得损坏 SourceFile、KnowledgeUnit 或 LearningEvidence。

## 5. Failure Semantics

必须区分：

- no result；
- low confidence；
- required role missing；
- source conflict；
- invalid citation；
- stale/missing index；
- reranker unavailable；
- embedding/provider unavailable；
- workspace/scope violation；
- exposure classification uncertain。

### SYS02-040

缺失必需证据时 MUST NOT 让 SYS08 用模型常识冒充用户资料答案；若需改变 TeachingAction，返回 SYS05 下一轮重新决策。

### SYS02-041 — Partial Availability

Material 已 SourceStored/Parsed/Structured 但尚未完成全部 embedding/KnowledgeModeling 时，SYS02 MAY 使用当前可靠的 SourceSpan/lexical projection 提供受限学习能力，并 MUST 在 trace 中记录 missing/stale derived stages。

不得因为某个 Derived Data 阶段失败而把 durable Material 整体标记为不可恢复失败。

## 6. Idempotency / Replay

相同 request + exact workspace/scope + fixed indexes/config SHOULD 产生稳定排序；非确定组件需固定版本与 stable tie-break。RetrievalTrace/bundle 创建 MUST 有 request id/idempotency strategy。

Replay MUST NOT 为恢复历史引用而调用在线 LLM 重写 source evidence。

## 7. Observability

必须记录：candidate rank、fusion/rerank score、workspace/scope fingerprint、hard filter reason、pedagogical role、exposure filtering、source/index versions、citation validation、latency/cache、degradation mode。

关键指标 MAY 包含 Recall@K、MRR、nDCG、role coverage、citation precision、answer leakage rate、context redundancy、token efficiency、p95 latency；这些属于 retrieval quality/process metrics，不是学习效果 KPI。

## 8. Security / Privacy

### SYS02-050

Workspace/RetrievalScope 是 hard filter，MUST 在 candidate search 和最终 bundle 前执行且 cache 不得绕过。

### SYS02-051

不可信文档指令 MUST NOT 提升 tool/model 权限或突破 TeachingAction exposure policy。

### SYS02-052

Grader-only 与 learner-visible evidence MUST 明确分离，参考答案不得错误进入 learner-visible context。

### SYS02-053

默认日志/诊断 MUST NOT 保存整本原文、完整 retrieval context 或完整用户资料正文；只记录必要 metadata/ref/hash/reason。

## 9. Tests

必须覆盖：

- workspace required / missing workspace fail closed；
- cross-workspace material/project/KU ref rejection；
- lexical+dense、RRF deterministic fixture；
- no-embedding lexical degradation；
- `NONE/PARTIAL/COMPLETE` exposure filter；
- tightening-only property；
- workspace/scope/cache isolation；
- revision/index invalidation；
- derived index delete/rebuild；
- duplicate/MMR；
- invalid anchor；
- reranker/embedding degradation；
- partial material availability；
- missing role；
- grader-only isolation；
- prompt injection。

## 10. Acceptance Criteria

- `SYS02-AC-001`：每个 EvidenceBundle item 可回溯 SourceSpan。
- `SYS02-AC-002`：独立评估时不允许的 COMPLETE answer 无法进入 learner-visible bundle。
- `SYS02-AC-003`：reranker/embedding 故障可降级，不改变 TeachingAction 或 durable Material。
- `SYS02-AC-004`：Workspace/scope/exposure 不同请求不会命中不安全 cache。
- `SYS02-AC-005`：缺必需证据返回 missing signal，不伪造证据。
- `SYS02-AC-006`：RetrievalTrace 可解释纳入/排除原因。
- `SYS02-AC-007`：索引重建不改变 canonical knowledge facts。
- `SYS02-AC-201`：SYS02 只能收紧，不能扩大 SYS05 answer exposure envelope。
- `SYS02-AC-202`：任何 production RetrievalScope 都有 workspace_id，默认无 cross-workspace retrieval。
- `SYS02-AC-203`：删除全部 Derived Index 后可从 durable facts 重建检索 projection。
- `SYS02-AC-204`：Material 部分处理成功时仍可在可靠证据边界内提供降级检索。

## 11. Legacy / Superseded Mapping

- v0.2 `SYS02-010 answer_exposure_max` 与 L0-L4 exposure 被 `SYS02-200/201` supersede。
- 旧 owner-only / global-library retrieval scope 必须迁移为 explicit workspace scope；在完成 migration 前只能作为 bounded compatibility path，MUST NOT 创建新 global cache/index truth。
- v0.2 advanced ranking/Bandit 演进属于历史研究方向。Contextual Bandit/RL MUST NOT 成为当前 canonical retrieval policy；未来启用需新的 Design/ADR/Spec。

## 12. Forbidden Implementations

禁止：

- 单一 embedding top-k 作为全部检索；
- Agent 自由搜索后无 trace 直接回答；
- SYS02 自行决定 TeachingAction；
- LLM 摘要充当原始来源；
- 无 citation anchor 的资料型回答当已验证证据；
- cache 忽略 workspace/scope/exposure/version；
- 检索失败后模型常识冒充资料；
- GraphRAG 默认所有请求；
- owner_id 代替 workspace_id 做资料隔离；
- 建立 v1 Global Material Library / cross-workspace default search；
- Vector/Embedding Index 成为不可重建 truth。
