# Askora Lifecycle State Machines

> Spec ID 范围：`LIFE-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 通用规则

### LIFE-001

公共领域对象的 `status` MUST 具有显式允许转换；Codex 不得自行增加可改变业务语义的新状态。

### LIFE-002

已发布/已完成结论需要修改时，优先创建新 revision/version 并把旧版本标记 superseded，而不是回退并覆盖旧数据。

### LIFE-003

状态转换 MUST 由对象 owner 执行，并记录产生转换的 command/event、reason code 与 trace id。

## 2. SourceDocument

Owner：4.1。

```text
imported
  → parsed
  → modeled
  → published
  → superseded

imported/parsed/modeled
  → failed
  → imported/parsed       # 明确 retry/reprocess 后产生新 processing run

任意预发布状态
  → quarantined           # 安全风险
```

### LIFE-010

只有 `published` revision 可以作为默认教学/评估事实来源。

### LIFE-011

`quarantined` 内容不得进入检索索引或 LLM learner-visible context。

## 3. KnowledgeUnit / Relation

Owner：4.1。

```text
candidate
  → verified
  → published
  → superseded

candidate/verified
  → rejected
```

### LIFE-020

低证据 `candidate` 不得被 4.2/4.6 当作正式 hard prerequisite。

### LIFE-021

published relation 的纠正生成新 revision 或 superseding relation，不直接改旧 edge。

## 4. LearningGoal

Owner：4.6。

```text
candidate
  → confirmed
  → active
  → achieved

active ↔ paused
confirmed/active/paused → archived
```

### LIFE-030

未确认的 candidate goal 不得触发长期自动规划，除非产品有显式“快速开始”规则并留下等价确认记录。

## 5. LearningObjective

Owner：4.6。

```text
planned
  → active
  → satisfied

satisfied → reopened      # 新证据显示能力退化/目标提高
planned/active/reopened → superseded
```

`reopened` 不意味着旧完成记录被删除。

## 6. LearningActivity

Owner：4.6。

```text
planned
  → available
  → active
  → completed

planned/available → skipped
planned/available/active → superseded
```

### LIFE-040

4.8 可以执行 `active` activity，但不能把另一个 activity 自行设为 active；选择权仍属于 4.6。

## 7. LearningPlan

Owner：4.6。

```text
active
  → completed
active ↔ paused
active/paused → superseded
```

### LIFE-050

Replan MUST 创建新 plan version；旧 active version 转为 superseded。不得原地重排历史 activity 后假装仍是同一版本。

## 8. AssessmentItem

Owner：4.4。

```text
draft
  → reviewed
  → active
  → retired

draft/reviewed → retired
```

### LIFE-060

模型生成 item MUST 从 `draft` 开始。

### LIFE-061

`active` item 的 answer/rubric/claim 发生语义修改时 MUST 创建新 item version。

## 9. Attempt

Owner：4.4。

Attempt 的生命周期状态建议：

```text
started
  → submitted
  → scored

started → abandoned
submitted → scoring_failed
scoring_failed → scored      # 明确 retry 后
```

### LIFE-070

提交后的回答修订不得覆盖旧提交；使用 response revision chain 并保留 assistance snapshot。

### LIFE-071

`scoring_failed` 不得产生高权 EvidenceAccepted。

## 10. AssessmentResult

Owner：4.4。

AssessmentResult 结论采用版本化而非可变 status：

```text
result v1 accepted/rejected/needs_review
→ reassessment
→ result v2 supersedes v1
```

### LIFE-080

重新评分不得静默覆盖 v1。

## 11. Learner Evidence

Owner：4.3 对 evidence eligibility 的最终接纳。

```text
candidate
  → accepted
candidate → rejected
accepted → invalidated       # 后续发现题目/评分/数据损坏
```

### LIFE-090

`invalidated` evidence 必须触发相关 MasteryEstimate 的 replay/recompute。

## 12. MasteryEstimate / LearnerState

Owner：4.3。

它们采用 immutable version stream，不使用 mutable workflow status：

```text
v1 → v2 → v3 ...
```

UI 派生标签 MAY 为：

```text
insufficient_evidence
forming
basic_mastery
stable_mastery
transfer_capable
```

### LIFE-100

标签是投影结果，不是用户可直接写状态。

### LIFE-101

`stable_mastery` 不得仅由一次即时正确或单一 probability threshold 触发。

## 13. TeachingStrategy

Owner：4.5。

```text
draft → active → retired
```

策略内容语义改变时创建新 semantic version。

## 14. TeachingAction

Owner：4.5。

TeachingAction 是单轮不可变决策。执行状态属于 4.8，二者必须区分：

```text
TeachingAction created (4.5)
  ↓
WorkflowStep pending/running/succeeded/failed (4.8)
```

### LIFE-110

执行失败不得修改原 TeachingAction；若教学语义需要变化，4.5 创建新 action。

## 15. ReviewSchedule

Owner：4.7。

采用 version stream：

```text
schedule v1
→ valid retrieval evidence
→ schedule v2
→ ...
```

可派生：

```text
not_due | due | overdue
```

### LIFE-120

`due/overdue` 是时间投影，不需要修改 schedule row 才成立。

### LIFE-121

实际复习执行时间与推荐 `next_due_at` 必须分别记录。

## 16. WorkflowRun

Owner：4.8。

```text
pending
  → running
  → succeeded
running → failed_retriable → running
running → failed_terminal
running → cancelled
```

### LIFE-130

有副作用的 tool step 重试必须带幂等键或 side-effect reconciliation；不得因自动 retry 重复创建外部副作用。

### LIFE-131

恢复运行必须固定 workflow/prompt/policy 版本，除非显式启动新的 run。

## 17. Feedback Dispute

当用户争议 learner state / assessment / content 时：

```text
FeedbackSignal
→ open dispute/review
→ validate evidence or retest
→ accepted_correction | rejected_dispute | unresolved
→ new domain version if needed
```

### LIFE-140

用户纠错不能跳过对应 owner，直接修改 canonical state。

## 18. Acceptance Criteria

- `LIFE-AC-001`：quarantined SourceDocument 无法进入 learner-visible retrieval。
- `LIFE-AC-002`：模型生成 AssessmentItem 未 review/validate 前不能 active。
- `LIFE-AC-003`：replan 后旧 LearningPlan 可查询且标记 superseded。
- `LIFE-AC-004`：AssessmentResult 重评产生新版本而非覆盖。
- `LIFE-AC-005`：invalidated evidence 会触发 mastery recompute。
- `LIFE-AC-006`：TeachingAction 执行失败不会原地改变教学策略。
- `LIFE-AC-007`：WorkflowRun 重试不会重复不可逆副作用。

## 19. Forbidden Implementations

禁止：

- 任意字符串 status 且无转换校验；
- 修改 `published` KnowledgeUnit 内容但保留相同 revision；
- 原地编辑已完成 LearningPlan；
- 模型生成题直接 `active`；
- 重评分数覆盖旧 AssessmentResult；
- 把 WorkflowRun failure 当成 TeachingAction failure 并自动改教学策略；
- 用户点击“我会了”直接把 mastery label 改成 stable_mastery。
