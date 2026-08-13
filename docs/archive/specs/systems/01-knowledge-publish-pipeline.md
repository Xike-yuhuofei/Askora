# SPEC-D03 — Knowledge Candidate Verification & Publish Pipeline

> 状态：**FROZEN**  
> Spec ID：`SPEC-D03`  
> 冻结日期：2026-08-08  
> Owner：SYS01 Content & Knowledge  
> 上游：`SPEC-D01`、`SPEC-D02`、`systems/01-content-knowledge.md`、UI-02A Frozen Baseline  
> 目的：把 UI-02A 的 source-bound structural candidates 扩展为可验证、可发布、可审计的真实 Knowledge Model，而不允许 LLM 输出直接成为 canonical truth。

## 1. Baseline

UI-02A 已冻结：

```text
deterministic-structure-v2
→ SourceSpan-bound KnowledgeUnit candidate
```

并明确：无可靠 relation 时 edges 保持为空；`minimal-binding-v1` 只能兼容读取。

本合同 MUST 在该基线上扩展，不得回退为“一文档一个高置信 published KnowledgeUnit”。

## 2. Candidate Families

SYS01 内部至少支持：

```text
ConceptCandidate
KnowledgeUnitCandidate
RelationCandidate
PedagogicalAssetCandidate
```

每个 candidate MUST 保存：

```yaml
candidate_id: uuid
revision_id: uuid
candidate_type: string
source_span_ids: [uuid]
semantic_unit_ids: [uuid]
extraction_run_id: uuid
proposed_payload: object
provenance_type: deterministic|source_explicit|model_inferred|human_curated
confidence: float|null
status: candidate|verified|published|rejected|review_required|superseded
reason_codes: [string]
```

Model confidence MUST NOT 被解释为已校准事实概率。

## 3. ExtractionRun

### D03-010

每次 extraction run MUST 固定并保存：

```text
parser version
semantic segmentation version
extractor version
model/provider/snapshot（如有）
prompt/schema version（如有）
publication policy version
input revision
```

Replay MUST 使用持久化 candidate/result；不得调用当前在线 LLM 重构历史 extraction。

## 4. Pipeline

```text
SemanticUnit
→ schema-constrained extraction
→ evidence binding
→ entity resolution
→ candidate normalization
→ relation validation
→ reverse evidence check
→ duplicate/conflict/cycle checks
→ publication policy
→ published | review_required | rejected
```

任何步骤失败都必须显式保留状态/reason code；不得静默丢弃后把剩余结果宣称完整。

## 5. KnowledgeUnit Publication

### D03-020

KnowledgeUnit MAY 自动 publish，仅当 versioned `KnowledgePublicationPolicy` 明确允许且同时满足：

- 至少一个 current-revision replayable SourceSpan；
- schema/business validation pass；
- identity/entity resolution 无 blocking ambiguity；
- 无未解决 source conflict；
- provenance 和 extraction versions 完整；
- confidence/quality rule 达到 policy 要求。

阈值 MUST versioned/configured，MUST NOT 写成普适学习科学常数。

### D03-021

source-explicit / deterministic structural evidence 可以与 model inference 组合，但 model inference 单独不足以绕过证据要求。

## 6. Concept Resolution

### D03-030

Concept merge MUST conservative。别名、同义词或相似 embedding 不足以静默合并 canonical Concept。

实体消歧至少考虑：

```text
source scope
local definition/context
hierarchy
existing aliases
relation neighborhood
```

Blocking ambiguity → `review_required` 或保持多个 candidate。

## 7. Relation Publication

### D03-040

Relation 至少支持既有 canonical relation semantics；`PrerequisiteRelation` 的约束最严格。

### D03-041 — Hard Prerequisite

`hard prerequisite` 自动发布必须满足以下之一：

1. 原文明确陈述且证据可回放；
2. versioned deterministic domain rule 且规则适用条件可审计；
3. 人工 ReviewDecision 接纳。

以下信息单独存在 MUST NOT 发布 hard prerequisite：

- 章节先后顺序；
- embedding 相似度；
- LLM 单次判断；
- “一般常识”；
- learner 当前错误表现。

### D03-042

soft/contextual relation MAY 使用 model-assisted candidate，但仍需 evidence binding + reverse validation + versioned publication policy。

## 8. Reverse Verification

每个 model-inferred KnowledgeUnit/Relation 在 publish 前 MUST 执行独立于初始自由生成文本的验证步骤。实现 MAY 使用：

- deterministic evidence entailment rules；
- schema/rule validator；
- separate constrained model inference；
- human review。

若使用第二模型步骤，必须保存独立 inference/version，不得把“同一回答自我声称正确”当验证。

## 9. Graph Quality Checks

至少：

```text
duplicate identity
self-loop
hard prerequisite cycle
orphan evidence
invalid SourceSpan
conflicting relation
superseded revision reference
```

Hard prerequisite cycle MUST block affected edge publication；SYS06 发现的规划冲突只能回报 evidence，不得直接修改 graph。

## 10. PedagogicalAsset

来源材料中的 definition/example/exercise/solution 等 MAY 形成 source-derived asset candidate。

LLM 生成的 explanation/example/hint/exercise MUST 明确 `generated` provenance；未经对应验证规则不得伪装为 source fact。AssessmentItem 是否 active 仍由 SYS04 决定。

## 11. Publication / Review Semantics

`ReviewDecision` 是 SYS01-owned 领域决定，但本 Spec 不要求本轮实现完整人工审核 UI。

若无审核 UI：

- 可安全机器发布的对象按 policy publish；
- 其余保持 `review_required/candidate`；
- downstream executable LearningPlan MUST 只消费允许的 published/verified KnowledgeUnit；
- UI 可展示 candidate，但不得当成熟 truth。

## 12. Events

继续使用现有事件家族：

```text
ContentImported
ContentPublished
KnowledgeRelationPublished
processing failed / review-required events
```

事件 payload MUST 引用 exact revision、candidate/published refs、ExtractionRun、reason codes；不得复制整本材料。

## 13. Tests

MUST 覆盖：

1. deterministic structural candidate 兼容；
2. source-bound KU publish；
3. unsupported candidate rejection；
4. ambiguous entity 保持未合并；
5. model-only hard prerequisite 不发布；
6. explicit hard prerequisite 可验证发布；
7. cycle rejection；
8. reverse verification failure；
9. invalid SourceSpan blocks publish；
10. fixed extraction result replay 不调用 LLM；
11. projection rebuild 不改变 published knowledge。

## 14. Acceptance Criteria

- `D03-AC-001`：任一 published KnowledgeUnit/Relation 可追溯 exact MaterialRevision + SourceSpan + ExtractionRun/policy version。
- `D03-AC-002`：LLM JSON 不能直接成为 published truth。
- `D03-AC-003`：章节顺序不能自动产生 hard prerequisite。
- `D03-AC-004`：blocking entity ambiguity 不会被静默 merge。
- `D03-AC-005`：hard prerequisite cycle 不可进入 published graph。
- `D03-AC-006`：`minimal-binding-v1` 不重新成为成熟知识 truth。
- `D03-AC-007`：SYS04/SYS06/SYS08 不获得知识发布写权限。

## 15. Forbidden Implementations

禁止：

- 一次 LLM 调用同时抽取、验证、发布；
- model self-confidence 直接控制 truth；
- 用 user mastery/error 反向修改 canonical prerequisite；
- SourceChunk 直接升级成 KnowledgeUnit；
- 没有 evidence anchor 的自动知识发布；
- 为“图看起来完整”生成无证据 edges。

## 16. Freeze Decision

`SPEC-D03`：**FROZEN / READY_FOR_EXEC_DECOMPOSITION**。若实现需要改变 relation ontology、引入新的 canonical relation type 或外部人工审核服务，必须先报告 `SPEC GAP`。