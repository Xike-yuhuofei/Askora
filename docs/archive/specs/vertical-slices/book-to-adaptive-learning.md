# SPEC-D06 — Book-to-Adaptive-Learning Vertical Slice

> 状态：**FROZEN**  
> Spec ID：`SPEC-D06`  
> 冻结日期：2026-08-08  
> 范围：Book-to-Learning Bootstrap  
> Product Traceability：`CAP-01`、`CAP-02`、`CAP-03`、`CAP-04`、`CAP-05`、`CAP-07`；`PD-REQ-0101..0103`、`PD-REQ-0201..0203`、`PD-REQ-0301..0303`、`PD-REQ-0401..0402`、`PD-REQ-0501..0503`、`PD-REQ-0701`；`PD-RULE-002/005/006/007/010/011`  
> 上游：`PRODUCT-DEFINITION.md`、`SPEC-D01`～`SPEC-D05`、UI-02A Frozen Baseline、v0.3 Adaptive Teaching Loop Frozen Baseline  
> 目的：冻结“上传一本 EPUB → 第一轮真实 Adaptive Teaching”端到端技术切片；复用现有教学内核，不创建第二 Teaching Loop。

## 0. Acceptance Ownership

本 Vertical Slice 聚合多个 Product Requirement 并冻结一条可实现、可验证的端到端技术闭环，但它**不是新的 Product Scope 或 Product Acceptance 来源**。

规则：

- Product Capability / Product Requirement / Product Rule 以 `docs/product/PRODUCT-DEFINITION.md` 为上游 authority；
- 本文件 `IN / OUT` 只表示 `SPEC-D06` 的 implementation-slice scope，不等同 v1 Product inclusion / exclusion；
- 本文件 `D06-AC-*` 是 **Vertical Slice Technical Acceptance**，证明该 E2E 合同按当前 Specs 成立；
- 若需要新增/删除 Product Capability、改变 v1 Feature inclusion、改变 Product Requirement 或 Product Acceptance，必须先报告 `PRODUCT DEFINITION GAP`；
- Engineering / Vertical Slice PASS 不等同真人 Learning Evidence PASS。

## 1. Phase Position

当前形成链：

```text
PRODUCT-DEFINITION
→ Canonical Design / v0.3 Adaptive Teaching Loop
→ UI-02A Canonical Library Baseline
→ SPEC-D01～D05
→ 【SPEC-D06 Book-to-Adaptive-Learning Vertical Slice】
→ Linear Issue / EXEC decomposition
→ implementation
→ Book-to-Learning release gate
```

本 Spec Freeze 不预占 EXEC 编号。实时任务编号、状态与依赖属于 Linear / current EXEC index，不在本文件维护第二套 backlog。

## 2. Preconditions

必须复用且不得重建：

- UI-02A durable upload / processing / quarantine / reinspection；
- MaterialRevision / SourceSpan / scoped Library & Knowledge Map；
- event/outbox/idempotency/recovery；
- SYS02 EvidenceBundle；
- SYS03 LearnerState/MasteryEstimate；
- SYS04 AssessmentResult/Error Diagnosis；
- SYS05 deterministic Teaching Policy / TeachingStage / anti-oscillation；
- SYS06 LearningPlanner；
- SYS07 ReviewSchedule；
- SYS08 real-model bounded execution；
- v0.3 Outcome / OPVE / release claim separation。

## 3. Primary End-to-End Scenario

使用一个固定、可合法纳入仓库测试的 EPUB fixture，完成：

```text
Upload EPUB
→ durable processing
→ MaterialRevision
→ structure-preserving DocumentIR / DocumentNode
→ replayable SourceSpan
→ SemanticUnit
→ source-bound Knowledge candidates
→ verify / publish KnowledgeUnit + minimal relations
→ rebuildable retrieval projection
→ LearningGoal candidate
→ user-confirmed LearningGoal
→ GoalKnowledgeMapping
→ GoalSpecificKnowledgeSubgraph
→ prerequisite DiagnosticNeed
→ DIAGNOSTIC Activity / Assessment
→ LearnerState update
→ LearningPlan / LearningActivity
→ existing TeachingContext
→ existing deterministic Teaching Policy
→ TeachingAction
→ existing SYS02 EvidenceBundle
→ existing SYS08 execution
→ Attempt / AssessmentResult
→ LearnerState update
→ next policy decision
```

该链路必须至少闭合到“第二次 TeachingAction 可由第一次真实 material evidence 触发”。

## 4. Scope

本节只冻结 `SPEC-D06` 技术切片范围；不得用本节 OUT 项反向修改 Product Definition。

IN：

1. SPEC-D01 structure-preserving ingestion；
2. SPEC-D02 multi-granularity content model；
3. SPEC-D03 canonical knowledge candidate/verification/publication；
4. retrieval projection 与当前 SYS02 绑定；
5. SPEC-D04 natural-language Goal → KU mapping；
6. Goal-specific prerequisite closure；
7. SPEC-D05 prerequisite diagnostic bootstrap；
8. current LearningPlanner bootstrap/replan；
9. application/orchestration linking bootstrap to existing canonical teaching facade；
10. minimal additive API/query needed to operate/test the bootstrap；
11. E2E replay/idempotency/security/observability gate。

OUT：

- 重做 Teaching Policy / StrategyFamily / TeachingStage；
- Contextual Bandit / Offline/Online RL；
- Deep KT canonical truth；
- complex IRT-CAT；
- GraphRAG default；
- 自动 open-world misconception discovery；
- 全量人工 knowledge review UI；
- UI-02B 完整 Goal/Path/Evidence 视觉交付；
- 跨设备/cloud object storage；
- 外部图数据库/向量数据库作为必需条件；
- 用 synthetic learner 证明真实学习效果。

## 5. Bootstrap Readiness

### D06-010

产品/应用层 MAY 暴露 `BookLearningReadiness` read model，但它必须是派生状态，不是新的 canonical truth。

建议状态：

```text
PROCESSING
CONTENT_PARTIAL
READY_FOR_GOAL
GOAL_CONFIRMATION_REQUIRED
DIAGNOSIS_REQUIRED
DIAGNOSING
PLAN_READY
READY_TO_LEARN
BLOCKED
```

每个状态必须由 exact owner refs 派生，并返回 reason codes；不得由 UI 手工推进。

## 6. Minimal Application Commands / Queries

Vertical Slice MUST 至少存在等价能力：

```text
CreateLearningGoalCandidate
ConfirmLearningGoal
MapGoalToKnowledge
BuildGoalKnowledgeSubgraph
Generate/ContinuePrerequisiteDiagnosis
GenerateLearningPlan
SelectNextLearningActivity
StartCanonicalTeachingRound
```

Query 至少：

```text
GetBookLearningReadiness
GetLearningGoalCandidate/ConfirmedGoal
GetGoalKnowledgeMapping
GetCurrentDiagnosticState
GetCurrentLearningPlan/Activity
```

Transport endpoint 名称 MAY 由后续 EXEC 在 `API-*` 非破坏性 v1 additive 约束下选择，但不得让 API adapter 承担算法。

## 7. Orchestration Boundary

### D06-020

Book bootstrap orchestration 可以由 SYS08/application facade 编排，但每个领域写入必须回到对应 owner command：

```text
SYS01 → knowledge/content
SYS03 → learner projection
SYS04 → assessment
SYS06 → goal/plan/activity
SYS05 → TeachingAction
SYS07 → review
```

Orchestrator MUST NOT 持久化一个包含这些状态副本的“all-in-one learning session truth”。

## 8. Existing Teaching Loop Handoff

### D06-030

当 SYS06 产生可执行 `LearningActivity` 后，后续教学必须进入现有 canonical teaching entry：

```text
LearningActivity
→ TeachingContext Snapshot
→ PolicyBundle
→ deterministic Teaching Policy
→ TeachingAction
→ SYS02/SYS08 tightening-only execution
```

MUST NOT 新建 `book_tutor` / `epub_tutor` 自由 LLM 主链绕过 SYS05。

Book bootstrap 的 production handoff MUST 按 `ADR-0003` / `SYS05-304～306` 从 atomic active activation 解析 exact PolicyBundle 与 immutable runtime profile。缺失或不一致时必须停在 SYS05 unsupported-configuration boundary，MUST NOT 使用测试 fixture 或临时默认参数绕过。

## 9. Content-to-Plan Integrity

### D06-040

任一进入正式 LearningPlan 的 target/prerequisite KnowledgeUnit MUST：

- 属于 Goal confirmed scope；
- 有 exact canonical knowledge version；
- 有 replayable source evidence；
- 满足 SPEC-D03 downstream publish eligibility；
- relation 如为 prerequisite，引用 published SYS01 relation revision。

Candidate-only / stale / invalid-anchor KU 不能静默进入 executable plan。

## 10. Failure & Recovery

至少覆盖：

```text
CONTENT_PROCESSING_FAILED
CONTENT_MODEL_PARTIAL
SOURCE_ANCHOR_FAILED
KNOWLEDGE_PUBLICATION_BLOCKED
NO_PUBLISHED_TARGET_MATCH
AMBIGUOUS_GOAL_MAPPING
DIAGNOSTIC_ITEM_UNAVAILABLE
DIAGNOSTIC_BUDGET_EXHAUSTED
LEARNER_STATE_STALE
PLAN_BLOCKED
EVIDENCE_MISSING
MODEL_EXECUTION_FAILED
```

失败必须停在正确 owner 边界；不得通过让 LLM“先聊起来”掩盖 bootstrap 未完成。

Durable async content tasks 与同步 teaching round 必须分离：上传建模可异步，教学决策/Assessment 主路径需遵守现有低延迟/幂等 contract。

## 11. Replay / Idempotency

固定 fixture 必须证明：

- duplicate upload/process 不制造重复 revision/truth；
- parser/extraction version 可准确定位；
- fixed extraction result replay 不调用 LLM；
- fixed Goal + knowledge versions + mapper version 得到稳定 mapping；
- fixed diagnostic inputs 得到稳定 DiagnosticNeed；
- existing Teaching Policy replay 保持现有 FULL/PARTIAL/NON_REPLAYABLE 语义；
- 重复 command/idempotency key 不生成第二事实。

## 12. Security

必须继续验证：

- EPUB archive/path traversal/bomb 防线；
- prompt injection 内容不能成为 system instruction；
- quarantined 内容不进入 modeling/retrieval/learning；
- grader-only solution 不泄漏；
- source scope / current-owner authorization；
- LLM 不获得 owner write 权限；
- model failure 不转换为 learner failure。

## 13. Observability

一次 E2E correlation 至少可追踪：

```text
RawAsset / MaterialRevision
parser / extraction versions
KnowledgeUnit / Relation refs
Goal + mapping version
Goal subgraph version
DiagnosticNeed / Assessment refs
LearnerState version
LearningPlan / Activity version
TeachingContext / PolicyBundle
TeachingAction / DecisionTrace
EvidenceBundle / ModelInference
Attempt / AssessmentResult
next LearnerState / next decision
```

不得通过复制完整领域对象到一个 trace JSON 建立第二 truth。

## 14. Quality Gates

### G0 — Contract Correct

SPEC-D01～D05 schema/owner/forbidden rules 全部通过。

### G1 — Content Model Correct

EPUB structure、anchor replay、KU evidence binding、relation publication/cycle rules 通过。

### G2 — Goal / Diagnostic Correct

Goal mapping、scope、unknown prerequisite、diagnostic budget、Assessment→SYS03 boundary 通过。

### G3 — Planning Correct

真实 Goal/subgraph/LearnerState 可生成并重放 LearningPlan/Activity。

### G4 — Teaching Integration Correct

第一项 Activity 进入现有 v0.3 TeachingContext/Policy/Action，不存在第二教学主链。

### G5 — Recovery / Security Correct

outbox recovery、idempotency、quarantine、prompt injection、grader-only、scope authorization 通过。

### G6 — E2E Vertical Slice Contract Correct

固定 EPUB fixture 从 upload 闭合到下一次 TeachingAction。

G0～G6 是 technical / vertical-slice gates；它们可以支撑对应 Product Requirement 的实现证据，但不自行定义新的 Product Acceptance。

## 15. Vertical Slice Technical Acceptance Criteria

以下 `D06-AC-*` 是 `SPEC-D06` 的技术/E2E验收，不是新的 `PD-AC-*`：

- `D06-AC-001`：真实 EPUB 不经 flat-chunk shortcut 即可进入 canonical content model。
- `D06-AC-002`：正式 LearningPlan 只消费可审计 published/eligible KnowledgeUnit 与 relation。
- `D06-AC-003`：自然语言 Goal 可经确认映射到可审计 target KU，无需用户输入 UUID。
- `D06-AC-004`：未知 prerequisite 可进入真实 diagnostic assessment 并通过 SYS03 更新 LearnerState。
- `D06-AC-005`：现有 LearningPlanner 基于真实 inputs 生成第一版 Activity，不重写 planner。
- `D06-AC-006`：Activity 进入现有 v0.3 Teaching Policy，不存在 book-specific free-LLM TeachingAction owner。
- `D06-AC-007`：第一轮 Assessment 后的新 material evidence 能触发现有下一轮 policy decision。
- `D06-AC-008`：全链 exact versions/reason refs/correlation 可审计。
- `D06-AC-009`：replay 不调用在线 LLM 重构历史判断。
- `D06-AC-010`：quarantine/unauthorized/grader-only 内容无法进入 learner-visible teaching evidence。
- `D06-AC-011`：无 blocking ownership/ADR/Spec conflict。
- `D06-AC-012`：Learning Evidence Gate 继续为 `LEARNING_EVIDENCE_INSUFFICIENT`，直到有真实 human outcome evidence。

对应 Product Acceptance 是否成立，应由适用 `PD-REQ-* / PD-AC-*` 的产品行为证据单独判定。

## 16. Spec Consistency Invariants

本切片冻结以下不可变式：

```text
Content/Knowledge truth → SYS01
Goal/Plan/Activity       → SYS06
Assessment truth         → SYS04
Learner truth            → SYS03
TeachingAction           → SYS05
EvidenceBundle           → SYS02
ReviewSchedule           → SYS07
Execution/Model          → SYS08
```

以及：

```text
SourceChunk != KnowledgeUnit
GoalSubgraph != KnowledgeGraph truth
DiagnosticNeed != LearnerState
LearningPlan != TeachingAction
LLM inference != canonical truth
Book bootstrap != second Teaching Loop
```

## 17. Freeze Decision

`SPEC-D06`：**FROZEN**。

Spec Freeze Gate：**PASS**，条件为：

- 上游 Product Definition trace 明确；
- D01～D05 已 Frozen；
- 与 Accepted ADR-0001/0002 无冲突；
- 与 UI-02A/v0.3 frozen baseline 无冲突；
- single-writer ownership 不变；
- 未引入新的 Product Scope 或学习效果宣称；
- 后续实现只通过 Linear Issue / frozen EXEC（需要时）进入实现。

任何实现阶段发现必须违反 Product Definition 时，必须报告 `PRODUCT DEFINITION GAP`；发现必须违反本合同或其他 canonical Spec 时，报告 `SPEC GAP`。不得先修改产品代码，再用 Product Definition / ADR / Spec 追认既成事实。
