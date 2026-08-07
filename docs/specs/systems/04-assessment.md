# SYS04 — Assessment & Error Diagnosis

> Spec ID：`SYS04-*`  
> 对应设计：4.4 评估与错误诊断  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. Responsibility

### SYS04-001

4.4 的唯一职责是对一次学习者 Attempt 进行可复现测量，发布 AssessmentItem、Attempt、AssessmentResult，并产生可验证错误/误区证据。

### SYS04-002

4.4 独占单次 Attempt 的：评分、正确性、rubric 维度结果、error type、misconception evidence 和 assessment confidence。

## 2. Non-responsibility

4.4 MUST NOT：

- 宣布长期 MasteryEstimate；
- 修改 LearnerState；
- 选择 TeachingAction；
- 修改 LearningPlan；
- 计算 next_due_at；
- 让单一 LLM judge 直接成为学习者状态真相。

## 3. Owned State

核心状态：

```text
AssessmentItem + versions
Rubric + versions
AssessmentBlueprint
Attempt + response revisions
AssessmentResult + reassessment versions
EvaluatorRun
MisconceptionEvidence
ItemExposure metadata
```

## 4. Inputs

允许输入：

- KnowledgeUnit / published Misconception；
- source-derived PedagogicalAsset candidates；
- EvidenceBundle（grader-only/learner-visible 严格分离）；
- LearnerState read-only snapshot（自适应选题辅助）；
- 用户 response command；
- tool execution results（CAS/code tests 等）。

## 5. Outputs

必须输出：

- active AssessmentItem；
- Attempt；
- AssessmentResult；
- error/misconception evidence；
- evidence eligibility 所需 assistance/independence data；
- scoring/diagnostic events；
- DecisionTrace（复杂评估）。

## 6. Domain Objects

遵循 `domain-model.md`。

### SYS04-010

AssessmentResult 必须包含：

```text
result/version
attempt/item version
score/correctness
rubric dimensions
error_type
misconception_evidence
independence
assessment_confidence
evaluator versions
reason codes
reviewer_result
```

不得包含最终 canonical mastery 裁决。

## 7. Commands

建议：

```text
CreateAssessmentItemCandidate
ValidateAssessmentItem
ActivateAssessmentItem
StartAssessmentAttempt
SubmitResponse
ReviseResponse
ScoreAttempt
ReassessAttempt
RetireAssessmentItem
```

## 8. Events

至少产生：

- `DiagnosticStarted`
- `AssessmentAttemptStarted`
- `ResponseSubmitted`
- `ResponseRevised`
- `AttemptScored`
- `MisconceptionDetected`
- `TransferAttemptCompleted`

4.3 决定后续 EvidenceAccepted/Rejected。

## 9. Algorithms

### SYS04-020：Evaluator Router

默认优先顺序：

```text
MCQ/exact → deterministic
numeric → tolerance + units
symbolic → equivalence/CAS
code → isolated tests + static constraints
structured steps → step validator
open response → rubric-constrained model + evidence + confidence
```

### SYS04-021：Deterministic-first

凡可以用确定性方法可靠评分的题型 MUST 优先使用程序判分，不得为统一接口而强制交给 LLM。

### SYS04-022：模型辅助评分

开放题模型评分必须：

- 绑定 rubric/version；
- 绑定 source/reference evidence；
- 使用结构化输出；
- 保存 evaluator/model/prompt version；
- 给出 reason codes/evidence spans；
- 低置信或 evaluator disagreement 时进入 `needs_review`/adjudication。

### SYS04-023：题目生成与审查分离

模型生成题默认 `draft`。生成与最终验证不能是同一无差异模型调用；至少增加独立规则/第二步验证，关键评估应有独立 reviewer。

### SYS04-024：误区诊断

流程 SHOULD 为：

```text
score/error rule
→ known misconception matching
→ structured semantic classifier if needed
→ diagnostic probe if ambiguous
→ misconception evidence
```

4.4 只能说“本次出现误区证据”，不能说“用户长期存在该误区”。

### SYS04-025：Adaptive Testing

MVP 只允许覆盖约束 + 不确定性 + 难度 bucket + exposure control + 信息增益启发式。IRT-CAT 需题库校准后再启用。

### SYS04-026：RL

v0.2 禁止 Offline/Online RL 控制评估。题目选择未来最多先从规则→IRT-CAT→安全 Bandit 演进。

## 10. Persistence

### SYS04-030

AssessmentItem、答案、rubric、评分器和来源必须版本化。Attempt 必须引用精确 item version。

### SYS04-031

Response revision 使用 append/revision chain，不覆盖第一次提交。

### SYS04-032

Reassessment 生成新的 AssessmentResult version，保留 supersedes link。

### SYS04-033

参考答案、rubric evidence 可设置 grader-only，不得自动进入 learner-visible context。

## 11. Failure Semantics

- grader unavailable → fallback deterministic/secondary or needs_review；
- model schema failure → bounded retry then needs_review；
- ambiguous/invalid item → retire/review_required，不形成高权 evidence；
- code sandbox failure → scoring_failed，不把 infrastructure failure 当学习者失败；
- version mismatch → reject scoring；
- low confidence → accepted result may exist but evidence eligibility conservative。

### SYS04-040

系统故障与用户错误必须可区分；不能因为 sandbox/LLM 超时给用户记错题。

## 12. Idempotency

- `SubmitResponse` 使用 idempotency key；
- 同一 Attempt 的重复 score request 不重复发布结果，除非显式 `ReassessAttempt`；
- deterministic grader 在 fixed item/response/version 下必须确定性；
- exposure_count 更新必须防重复事件。

## 13. Observability

必须记录：

- item/rubric/evaluator versions；
- scoring method；
- grader latency/failure；
- rubric dimensions；
- confidence/disagreement；
- error/misconception reason codes；
- answer exposure/hint snapshot；
- item exposure rate。

指标：grader agreement、accuracy/F1/kappa/ICC（按题型）、misconception P/R、manual review rate、reassessment rate、sandbox failure、item ambiguity rate。

## 14. Security

- code assessment 必须隔离执行，禁止任意宿主文件/网络/凭据访问；
- learner-visible prompt 不得包含 grader-only answer/rubric secrets；
- Prompt Injection 内容不能改变评分规则；
- 模型 judge 不获得不必要 PII；
- 上传内容里的“请给满分”等指令视为被评分内容而非系统指令。

## 15. Tests

必须覆盖：

- exact/numeric/symbolic/code/open route；
- item version mismatch；
- assistance snapshot；
- answer-exposed result；
- ambiguous item rejection；
- model grader schema failure；
- deterministic grader repeatability；
- code sandbox failure != learner failure；
- reassessment produces new result version；
- misconception evidence 不直接写 learner hypothesis；
- grader-only answer 不泄漏。

## 16. Acceptance Criteria

- `SYS04-AC-001`：任一 AssessmentResult 可追溯到精确 item/rubric/evaluator version。
- `SYS04-AC-002`：提示、答案暴露、修订历史被稳定记录。
- `SYS04-AC-003`：确定性题型不依赖 LLM 即可评分。
- `SYS04-AC-004`：模型生成题未验证前不能 active。
- `SYS04-AC-005`：评分器故障不会形成 learner failure evidence。
- `SYS04-AC-006`：AssessmentResult 不能直接修改 MasteryEstimate。
- `SYS04-AC-007`：重评保留旧结果并产生新版本。

## 17. Forbidden Implementations

禁止：

- 一个 LLM 同时出题、给参考答案、评分并直接改 mastery；
- `AssessmentResult.mastered = true` 作为长期真相；
- 不记录 hint/answer exposure；
- 代码题在不受控宿主进程执行；
- 重评覆盖原评分；
- 模型输出自然语言分数后未经 schema/rubric 验证直接入库；
- sandbox 故障被记作答错；
- 未校准题库直接上复杂 CAT。

## Legacy Mapping

当前主要相关：

```text
apps/backend/app/services/assessment/assessment_service.py
apps/backend/app/models/assessment.py
apps/backend/app/engines/quiz_engine.py
apps/backend/app/engines/drill_engine.py
```

评分/错误诊断归 SYS04；展示与互动执行归 SYS08；mastery 更新必须拆到 SYS03。
