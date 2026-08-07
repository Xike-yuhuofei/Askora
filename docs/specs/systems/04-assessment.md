# SYS04 — Assessment

> Spec ID：`SYS04-*`  
> 对应设计：4.4 评估与形成性诊断  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS04-001

SYS04 是 `AssessmentItem`、`Attempt`、`AssessmentResult`、`MisconceptionEvidence` 与实际经历 assistance/exposure snapshot 的唯一 domain owner。

### SYS04-002

SYS04 负责判定“这次作答发生了什么、得分如何、可观察错误证据是什么”；MUST NOT 将 AssessmentResult 直接升级为 MasteryEstimate，也 MUST NOT 选择 TeachingAction。

## 2. Ownership Boundary

```text
Misconception definition      → SYS01
MisconceptionEvidence         → SYS04
MisconceptionHypothesis       → SYS03
Remediation decision          → SYS05
```

### SYS04-003

`AssessmentResult ≠ MasteryEstimate`。SYS03 MAY 消费结果形成 LearnerEvidence；SYS04 MUST NOT 写 mastery truth。

## 3. AssessmentItem / Attempt

### SYS04-010

AssessmentItem MUST 固定 item/version、claims、scoring method/rubric version、provenance 与 exposure metadata。模型生成 item 默认 MUST 为 draft，经可解性/答案一致性/安全检查后才 MAY active。

### SYS04-011

Attempt MUST 固定 item/version、response、timestamps、assessment type 与实际 assistance snapshot，保证之后 eligibility/replay 不依赖聊天文本推断。

### SYS04-200 — Canonical Assistance Snapshot

每个 Attempt MUST 记录：

```text
scaffold_control = NONE | LOW | MEDIUM | HIGH
hint_specificity = NONE | ORIENTATION | CONCEPTUAL_STRATEGIC | SUBGOAL | PARTIAL_STEP | BOTTOM_OUT
answer_exposure = NONE | PARTIAL | COMPLETE
assistance_state = INDEPENDENT | ASSISTED | ANSWER_EXPOSED
```

SYS04 记录的是**实际经历**，而非 SYS05 的 allowed envelope。历史 `max_hint_level`、整数 `hint_level/scaffold_level`、0..4 exposure 只允许兼容读取。

### SYS04-201 — Assistance Integrity

若执行过程中实际 exposure/support 与 TeachingAction envelope 不一致，SYS04 MUST 保存实际经历并产生 integrity reason/event；MUST NOT 为“符合计划”而篡改 Attempt snapshot。

## 4. AssessmentResult & Diagnosis

### SYS04-210 — Canonical ErrorType

v0.3 ErrorType 仅允许：

```text
KNOWLEDGE_GAP
CONCEPTUAL_MISCONCEPTION
METHOD_SELECTION
EXECUTION
RETRIEVAL_FAILURE
TRANSFER_FAILURE
EXPRESSION_FORMAT
UNKNOWN
```

### SYS04-211 — Diagnosis Contract

AssessmentResult MUST 能表达：

```text
error_type
diagnostic_confidence
diagnostic_evidence_refs
misconception_evidence_refs
alternative_hypotheses
needs_probe
reason_codes
```

并单独表达 `assessment_confidence`。

### SYS04-212 — Confidence Separation

`assessment_confidence != diagnostic_confidence`。高评分可信度 MUST NOT 被实现为高错因归因可信度的隐式默认值。

### SYS04-213 — UNKNOWN Is Valid

证据不足或假设不可区分时，SYS04 MUST 允许 `UNKNOWN`；MUST NOT 为满足 enum 完整性强制猜测一个具体 ErrorType。`needs_probe=true` MAY 与 UNKNOWN 或低置信诊断同时存在。

### SYS04-214 — Legacy Error Mapping

兼容读取历史数据时：

```text
condition_omission     → reason code / subcategory
metacognitive          → behavioral/policy signal、ActionModifier 或 reason code
expression_incomplete  → EXPRESSION_FORMAT
```

若历史记录无法无歧义映射，canonical diagnosis MUST 为 `UNKNOWN` 并保存 `migration_reason`；不得伪造 diagnostic confidence。

## 5. Scoring & Evaluation

### SYS04-020

可确定性评分任务 SHOULD 优先使用 exact/equivalence/tests/rubric deterministic path；LLM judge MAY 用于适合的开放任务，但 MUST 固定 model/prompt/rubric/schema versions，并允许 `unscorable|needs_review`。

### SYS04-021

评分系统 MUST 区分：score/correctness、assessment confidence、diagnosis、diagnostic confidence。任何单一 LLM 输出 MUST NOT 同时无验证地产生四者并被视为 truth。

### SYS04-022

评估失败、模型/工具失败或系统异常 MUST NOT 被记录为 learner failure evidence。

## 6. Independent Validation Semantics

### SYS04-220

SYS04 MUST 忠实记录 `ASSISTED` 与 `ANSWER_EXPOSED` success，并将其提供给 SYS05/SYS03；它 MUST NOT 自行把这些 success 标记为 independent。

### SYS04-221

`ANSWER_EXPOSED` 当前结果 MUST NOT 被标记为 independent mastery evidence。独立验证只有在后续 fresh Attempt 实际发生且满足 independent criteria 后才能形成新的 AssessmentResult/LearnerEvidence。

### SYS04-222

SYS05 的 `INDEPENDENT_VALIDATION_REQUIRED` 是 policy-control obligation，不属于 AssessmentResult/MasteryState；SYS04 只产生能够满足或未满足该 obligation 的新事实。

## 7. Persistence / Versioning

### SYS04-030

AssessmentItem、Attempt、AssessmentResult MUST 有稳定 identity/version/provenance。重新评分产生新 Result revision 或 superseding result；MUST NOT 原地改写历史评分理由。

### SYS04-031

Evaluator/rubric/model/prompt/normalization/migration versions MUST 可追踪。历史 raw diagnosis MAY 保留为 audit metadata，但 canonical field MUST 服从 v0.3 enum。

## 8. Idempotency

### SYS04-040

同一 submit command/idempotency key MUST NOT 产生多个语义重复 Attempt；同一 Attempt + exact evaluator bundle SHOULD 得到 deterministic result，非确定组件必须保存足够版本与输出引用。

## 9. Events / Observability

### SYS04-050

至少发布/记录：

- AssessmentItemPresented；
- ResponseSubmitted；
- AssessmentResultProduced；
- DiagnosisProduced/DiagnosisUncertain；
- AssistanceExperienced/AnswerExposed（发生时）；
- AssessmentEvaluationFailed。

### SYS04-051

观测 MUST 包含 item/result/evaluator versions、assessment confidence、diagnostic confidence、ErrorType、alternative hypotheses、needs_probe、actual assistance/exposure、migration reason 与 source refs。

## 10. Failure Semantics

必须区分：invalid item/version、unscorable response、rubric/evaluator unavailable、low assessment confidence、low diagnostic confidence、UNKNOWN diagnosis、assistance snapshot missing、integrity mismatch、persistence failure。

### SYS04-060

缺失 assistance snapshot 时，系统 MUST 标记 evidence eligibility 不完整/保守，MUST NOT 默认 `INDEPENDENT`。

## 11. Tests

### SYS04-230

测试 MUST 覆盖：

- canonical 7 + UNKNOWN ErrorType；
- `UNKNOWN` 合法且不会被强制分类；
- assessment/diagnostic confidence 独立；
- alternative hypotheses/needs_probe；
- legacy `condition_omission`/`metacognitive`/`expression_incomplete` mapping；
- four-axis assistance snapshot；
- answer-exposed success 不等于 independent；
- execution/system failure 不生成 learner failure evidence；
- MisconceptionEvidence 不直接变成 LearnerState hypothesis；
- deterministic scoring replay / versioned LLM judge；
- missing assistance fail conservative。

## 12. Acceptance Criteria

- `SYS04-AC-201`：AssessmentResult 可完整表达 v0.3 diagnosis contract。
- `SYS04-AC-202`：ErrorType 只能是 7 类 + UNKNOWN，历史旧值不能作为 canonical 写入。
- `SYS04-AC-203`：`assessment_confidence` 与 `diagnostic_confidence` 可独立变化。
- `SYS04-AC-204`：实际 assistance/exposure 可由 Attempt 直接审计，不依赖聊天内容推断。
- `SYS04-AC-205`：ANSWER_EXPOSED result 不能被标记为 independent evidence。
- `SYS04-AC-206`：SYS04 不写 MasteryEstimate、MisconceptionHypothesis 或 TeachingAction。

## 13. Legacy Mapping

v0.2 ErrorType 与整数帮助/暴露字段只允许 read adapter/audit。迁移后 canonical writer MUST 只写 v0.3 schema；当所有活跃记录/工作流不再依赖旧字段且历史 migrator 可提供明确 replayability status 后，旧 writer/adapter SHOULD retirement。

## 14. Forbidden Implementations

禁止：

- 把 AssessmentResult 当 MasteryEstimate；
- 强制猜 ErrorType；
- `assessment_confidence = diagnostic_confidence` 的硬绑定；
- 用 `missing=0`；
- 继续写 `condition_omission`、`metacognitive`、`expression_incomplete` 为 canonical ErrorType；
- 继续用一个整数 hint/scaffold/exposure 表示全部帮助语义；
- LLM judge 直接写 LearnerState；
- 系统故障算作 learner failure。