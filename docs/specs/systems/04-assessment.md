# SYS04 — Assessment & Error Diagnosis

> Spec ID：`SYS04-*`  
> 对应设计：4.4 评估与错误诊断  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Responsibility

### SYS04-001

SYS04 的唯一职责是对一次学习者 Attempt 进行可复现测量，发布 AssessmentItem、Attempt、AssessmentResult，并产生可验证 error/misconception evidence。

### SYS04-002

SYS04 独占单次 Attempt 的评分、correctness、rubric dimension result、canonical ErrorType、MisconceptionEvidence、assessment confidence、diagnostic confidence 与实际经历 assistance/exposure snapshot。

SYS04 MUST NOT 宣布长期 MasteryEstimate、修改 LearnerState、选择 TeachingAction、修改 LearningPlan/ReviewSchedule，或让单一 LLM judge 成为学习者状态真相。

## 2. Ownership Boundary

### SYS04-200 — Misconception Boundary

```text
Misconception definition      → SYS01
MisconceptionEvidence         → SYS04
MisconceptionHypothesis       → SYS03
Remediation decision          → SYS05
```

`AssessmentResult != MasteryEstimate`。SYS03 MAY 消费结果形成 LearnerEvidence；SYS04 MUST NOT 写 mastery truth。

## 3. Existing v0.2 Contracts Retained

### SYS04-010 — AssessmentResult Contract

AssessmentResult MUST 包含/引用：result/version、attempt/item version、score/correctness、rubric dimensions、canonical diagnosis、actual assistance/independence snapshot、assessment confidence、evaluator versions、reason codes 与 reviewer_result。MUST NOT 包含最终 canonical mastery 裁决。

### SYS04-020 — Evaluator Router

默认优先：exact/MCQ → deterministic；numeric → tolerance + units；symbolic → equivalence/CAS；code → isolated tests + static constraints；structured steps → step validator；open response → rubric-constrained model + evidence + confidence。

### SYS04-021 — Deterministic-first

凡可用确定性方法可靠评分的题型 MUST 优先程序判分，不得为统一接口而强制交给 LLM。

### SYS04-022 — Model-assisted Scoring

开放题模型评分 MUST 绑定 rubric/version、source/reference evidence、structured output、evaluator/model/prompt version，并提供 reason/evidence。低置信或 evaluator disagreement MUST 进入 `needs_review`/adjudication；模型调用失败 MUST NOT 被解释为 learner failure。

### SYS04-023 — Generation / Validation Separation

模型生成题默认 `draft`。生成与最终验证 MUST 分离；至少有独立规则/第二步验证，关键评估 SHOULD 有独立 reviewer。

### SYS04-024 — Misconception Diagnosis

诊断 SHOULD 按：score/error rule → known misconception matching → structured classifier（如需）→ diagnostic probe（如 ambiguity）→ MisconceptionEvidence。SYS04 只能断言“本次出现证据”，MUST NOT 直接断言长期 learner misconception。

### SYS04-025 — Adaptive Testing Scope

MVP 只允许 coverage constraints + uncertainty + difficulty bucket + exposure control + information-gain heuristic。Complex IRT-CAT MUST NOT 成为 v0.3 canonical runtime，除非未来新的 Design/ADR/Spec 冻结。

### SYS04-026 — RL Scope

Offline/Online RL MUST NOT 控制 v0.3 canonical assessment runtime。

### SYS04-030 — Versioned Assessment Assets

AssessmentItem、答案、rubric、scoring/evaluator 与来源 MUST versioned；Attempt MUST 引用 exact item version。

### SYS04-031 — Response Revision

Response revision MUST 使用 append/revision chain，MUST NOT 覆盖首次提交。

### SYS04-032 — Reassessment

Reassessment MUST 产生新的 AssessmentResult version 并保留 supersedes link。

### SYS04-033 — Grader-only Isolation

reference answer/rubric evidence MAY 为 grader-only，MUST NOT 自动进入 learner-visible context。

### SYS04-040 — System Failure != Learner Error

系统/工具/模型故障与 learner error MUST 可区分；sandbox/LLM timeout 等 MUST NOT 形成 learner failure evidence。

## 4. v0.3 Assistance / Exposure Contract

### SYS04-210 — Canonical Assistance Snapshot

每个 Attempt MUST 记录实际经历：

```text
scaffold_control = NONE | LOW | MEDIUM | HIGH
hint_specificity = NONE | ORIENTATION | CONCEPTUAL_STRATEGIC | SUBGOAL | PARTIAL_STEP | BOTTOM_OUT
answer_exposure = NONE | PARTIAL | COMPLETE
assistance_state = INDEPENDENT | ASSISTED | ANSWER_EXPOSED
```

SYS04 记录的是**实际经历**，不是 SYS05 allowed envelope。历史 `max_hint_level`、整数 `hint_level/scaffold_level` 与 0..4 exposure 只允许兼容读取/audit。

### SYS04-211 — Assistance Integrity

若实际 support/exposure 与 TeachingAction envelope 不一致，SYS04 MUST 保存实际经历并产生 integrity reason/event；MUST NOT 为符合计划而篡改 Attempt snapshot。

## 5. v0.3 Error Diagnosis

### SYS04-220 — Canonical ErrorType

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

### SYS04-221 — Diagnosis Contract

AssessmentResult/Diagnosis MUST 能表达：`error_type`、`diagnostic_confidence`、`diagnostic_evidence_refs`、`misconception_evidence_refs`、`alternative_hypotheses`、`needs_probe`、`reason_codes`，并单独表达 `assessment_confidence`。

### SYS04-222 — Confidence Separation

`assessment_confidence != diagnostic_confidence`。高评分可信度 MUST NOT 隐式等于高错因归因可信度。

### SYS04-223 — UNKNOWN Is Valid

证据不足或假设不可区分时 MUST 允许 `UNKNOWN`；MUST NOT 为 enum 完整性强制猜具体 ErrorType。`needs_probe=true` MAY 与 UNKNOWN/低置信诊断并存。

### SYS04-224 — Legacy Error Mapping

兼容读取历史数据：

```text
condition_omission     → reason code / subcategory
metacognitive          → behavioral/policy signal、ActionModifier 或 reason code
expression_incomplete  → EXPRESSION_FORMAT
```

无法无歧义映射时 canonical diagnosis MUST 为 `UNKNOWN` 并保存 migration reason；不得伪造 diagnostic confidence。

## 6. Independent Validation Semantics

### SYS04-230

SYS04 MUST 忠实记录 `ASSISTED` 与 `ANSWER_EXPOSED` success，并提供给 SYS05/SYS03；MUST NOT 自行标记为 independent。

### SYS04-231

`ANSWER_EXPOSED` 当前结果 MUST NOT 被标记为 independent mastery evidence。独立验证只有后续 fresh Attempt 实际发生并满足 independent criteria 时才能形成新事实。

### SYS04-232

SYS05 `INDEPENDENT_VALIDATION_REQUIRED` 是 policy-control obligation，不属于 AssessmentResult/MasteryState；SYS04 只产生能满足或未满足 obligation 的事实。

## 7. Idempotency / Replay

`SubmitResponse` MUST 使用 idempotency key；同一 Attempt 重复 score request MUST NOT 产生重复结果，除非显式 ReassessAttempt；deterministic grader 在 fixed item/response/version 下 MUST deterministic；exposure_count/event consumption MUST 防重复。

Canonical replay MUST 固定 item/rubric/evaluator/model/prompt/schema versions。

## 8. Failure Semantics

必须区分：invalid item/version、unscorable response、grader unavailable、rubric/evaluator unavailable、model schema failure、sandbox failure、low assessment confidence、low diagnostic confidence、UNKNOWN diagnosis、assistance snapshot missing、integrity mismatch、persistence failure。

### SYS04-240 — Missing Assistance

缺失 assistance snapshot 时 MUST conservative 标记 evidence eligibility 不完整，MUST NOT 默认 `INDEPENDENT`。

## 9. Observability

至少记录 item/rubric/evaluator versions、scoring method、grader latency/failure、rubric dimensions、assessment confidence、diagnostic confidence、ErrorType、alternative hypotheses、needs_probe、actual assistance/exposure、migration reason 与 evidence/source refs。

## 10. Security

Code assessment MUST isolated；learner-visible prompt MUST NOT 包含 grader-only answer/rubric secrets；prompt injection MUST NOT 修改评分规则；model judge 不获得不必要 PII。

## 11. Tests

### SYS04-250

测试 MUST 覆盖：exact/numeric/symbolic/code/open route；item version mismatch；canonical 7+UNKNOWN ErrorType；UNKNOWN 不被强制分类；assessment/diagnostic confidence 独立；alternative hypotheses/needs_probe；legacy error mapping；four-axis assistance snapshot；answer-exposed success != independent；ambiguous item rejection；model grader schema failure；deterministic repeatability；sandbox failure != learner failure；reassessment new version；MisconceptionEvidence 不直接写 learner hypothesis；grader-only isolation；missing assistance fail conservative。

## 12. Acceptance Criteria

原有 AC 保留并更新 v0.3 字段语义：

- `SYS04-AC-001`：任一 AssessmentResult 可追溯 exact item/rubric/evaluator version。
- `SYS04-AC-002`：support、answer exposure 与 revision history 被稳定记录。
- `SYS04-AC-003`：确定性题型不依赖 LLM 即可评分。
- `SYS04-AC-004`：模型生成题未验证前不能 active。
- `SYS04-AC-005`：评分器/系统故障不会形成 learner failure evidence。
- `SYS04-AC-006`：AssessmentResult 不能直接修改 MasteryEstimate。
- `SYS04-AC-007`：reassessment 保留旧结果并产生新版本。

新增 v0.3 AC：

- `SYS04-AC-201`：ErrorType 只能是 7 类 + UNKNOWN，历史旧值不能 canonical 写入。
- `SYS04-AC-202`：`assessment_confidence` 与 `diagnostic_confidence` 可独立变化。
- `SYS04-AC-203`：actual assistance/exposure 可由 Attempt 直接审计。
- `SYS04-AC-204`：ANSWER_EXPOSED result 不能被标记为 independent evidence。
- `SYS04-AC-205`：SYS04 不写 MisconceptionHypothesis 或 TeachingAction。

## 13. Legacy Mapping

v0.2 ErrorType 与整数帮助/暴露字段只允许 read adapter/audit。Canonical writer MUST 只写 v0.3 schema；active workflows 全部切换且 historical migrator 能给出明确 replayability 后，旧 writer/adapter SHOULD retirement。

## 14. Forbidden Implementations

禁止：

- 一个 LLM 同时出题、给参考答案、评分并直接改 mastery；
- `AssessmentResult.mastered=true` 作为长期 truth；
- 强制猜 ErrorType；
- `assessment_confidence = diagnostic_confidence` 硬绑定；
- `missing=0`；
- 继续写 `condition_omission`、`metacognitive`、`expression_incomplete` 为 canonical ErrorType；
- 继续用单一 integer hint/scaffold/exposure 表示全部帮助语义；
- code 在不受控宿主执行；
- reassessment 覆盖原结果；
- system failure 算作 learner failure；
- 未校准题库直接上 complex CAT；
- v0.3 Offline/Online RL assessment control。

## P1-01 Criterion Measurement

SYS04 对 exact/numeric/structured criterion 优先确定性评分；开放回答必须使用 versioned rubric、
exact source evidence、strict schema grader 与独立复核。grader-only input 不得泄漏 learner-visible。
低置信、分歧、provider failure 或 Prompt Injection 标记 `needs_review/scoring_failed`，不得记 0 分。
