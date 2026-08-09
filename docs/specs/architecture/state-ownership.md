# Askora State Ownership Specification

> Spec ID 范围：`STATE-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3

## 1. Existing Ownership Principles Retained

### STATE-001 — One State, One Writer

任何跨会话、可影响后续教学决策的 canonical state MUST 有唯一写入 owner。其他系统 MAY 读取、缓存、投影或托管 ledger，但 MUST NOT 形成第二 truth。

### STATE-002 — Read Permission != Write Permission

系统读取另一 owner 的 exact-version state 用于决策，并不获得更新该 state 的权限。

### STATE-003 — Suggestion / Evidence != State Update

LLM、grader、retriever、experiment 或用户反馈产生的建议/evidence/candidate 必须先由对应 owner 按 contract 接纳，才能形成新的 canonical state/version。

### STATE-004 — Core State Is Versioned

已发布 KnowledgeUnit/Relation revision、AssessmentResult、MasteryEstimate、TeachingAction、LearningPlan、ReviewSchedule、LearningEvent、DecisionTrace MUST 使用 append/version/immutable semantics；v0.3 TeachingContext、PolicyBundle、OutcomeObservation、ExperimentAssignment 也 MUST immutable/versioned。MUST NOT 静默覆盖历史。

## 2. v0.3 Ownership Matrix

| Canonical truth / decision | Owner | Other systems may |
|---|---|---|
| Knowledge truth / relations / Misconception definition | SYS01 | read / retrieve / reference |
| EvidenceBundle / RetrievalTrace | SYS02 | consume |
| LearnerEvidence acceptance / MasteryEstimate / LearnerState / MisconceptionHypothesis | SYS03 | read |
| AssessmentItem / Attempt / AssessmentResult / MisconceptionEvidence / actual assistance | SYS04 | consume |
| TeachingAction / TeachingContext decision-snapshot semantics / TeachingStage derivation / PolicyBundle governance / validation obligation | SYS05 | execute / read |
| LearningGoal / Objective / LearningActivity / LearningPlan | SYS06 | read |
| ReviewSchedule / memory scheduling state / next_due_at | SYS07 | read / plan from |
| WorkflowRun / ModelRouteProfile / ModelInference / Tool execution / execution validation | SYS08 | execute / host ledgers |

## 3. Existing Boundary Requirements Retained

### STATE-010 — AssessmentResult != MasteryEstimate

AssessmentResult 只描述一次 Attempt/measurement；只有 SYS03 可把一个或多个 accepted evidence 融合为 MasteryEstimate。SYS04/Assessment MUST NOT 直接写 mastery。

### STATE-011 — ReviewSchedule != MasteryEstimate

SYS07 MAY 维护 stability/difficulty/retrievability/next_due_at，但 MUST NOT 宣布 stable/transfer mastery。

### STATE-012 — LearningPlan != TeachingAction

SYS06 决定 learning objective/activity/priority/sequence；SYS05 决定当前教学动作、支架/提示/答案暴露 envelope 与 policy-control semantics。两者 MUST 独立 versioned。

### STATE-013 — SourceChunk != KnowledgeUnit

SourceChunk 是可重建 retrieval projection；KnowledgeUnit 是 canonical knowledge identity。重新分块 MUST NOT 自动重建全部 KnowledgeUnit identity。

### STATE-014 — Misconception Definition != Learner Hypothesis

SYS01 定义 misconception；SYS04 产生 MisconceptionEvidence；SYS03 维护 MisconceptionHypothesis；SYS05 决定 remediation。

## 4. Existing Update / Replay Requirements Retained

### STATE-020 — Provenance

关键 state 新版本 MUST 至少追溯 input/event refs、algorithm/policy/model version、time、reason codes、trace/correlation id。

### STATE-021 — No Direct State Update From Chat

Chat MAY 触发 command/self-report/feedback，但 MUST 经结构化 owner contract 才能影响 state；“我已经会了”等 MUST NOT 直接设置 mastery。

### STATE-022 — Dispute / Review

用户争议系统判断时 MUST 进入 FeedbackSignal → dispute/retest/evidence correction/replay → new state version；MUST NOT 通用直接编辑概率。

### STATE-023 — Correction / Deletion

普通纠错追加 correction/invalidation；明确删除/法律删除按 privacy contract 删除并重建受影响 projection，保留允许范围 audit tombstone。

### STATE-030 — Monotonic Version

同一 aggregate canonical version MUST 单调递增，并有唯一性约束。

### STATE-031 — Command Idempotency

重复 command MUST NOT 生成第二份等价 evidence/state update。

### STATE-032 — Projection Idempotency

重放相同 event/evidence set + exact projection version MUST 得到相同 semantic state。

### STATE-033 — Replay No Online LLM

Replay MUST NOT 调用在线 LLM 重新理解历史；使用当时持久化结构化 result/inference 或显式新 reassessment/recompute。

## 5. Existing Legacy Governance Retained

### STATE-040 — Migration Starts With Owner

任何 legacy table/model 重构前 MUST 标注 target owner、current writers、multi-writer risk、migration strategy、retirement condition。

### STATE-041 — Dual-write Only Temporarily

若 migration 必须短期 dual-write，必须指定 canonical truth、reconciliation、停止条件；MUST NOT 形成永久架构。

### STATE-042 — KT/DKT Convergence

SYS03 MUST 只有一个 canonical learner-state projector。DKT/Deep KT MAY challenger/feature provider，MUST NOT 成为第二 mastery truth。

## 6. v0.3 Derived / Control Objects

### STATE-200 — TeachingContext

TeachingContext 是 SYS05 immutable decision-input snapshot，引用 exact owner versions；MUST NOT 成为第二 LearnerState/AssessmentResult/LearningPlan truth。

### STATE-201 — TeachingStage

TeachingStage = SYS05 从 `TeachingContext + PolicyBundle` 派生的当前 control stage；MUST NOT 持久化为 SYS03 learner/mastery stage truth。

### STATE-202 — PolicyBundle

PolicyBundle 是 SYS05 immutable/versioned policy configuration artifact；activation 只影响新 TeachingAction，MUST NOT 重解释历史 action。

### STATE-203 — Independent Validation Obligation

Validation obligation 属 SYS05 policy-control semantics。SYS04 产生 fresh Attempt/AssessmentResult facts；SYS03 仅判断 evidence eligibility，MUST NOT 创建/提前完成 obligation。

## 7. v0.3 Outcome / Experiment Contracts

### STATE-210 — OutcomeObservation

OutcomeObservation 是 immutable measurement/analytics record，必须引用既有 measurement/evidence owner facts；MUST NOT 替代 AssessmentResult、MasteryEstimate 或 TeachingAction truth。

### STATE-211 — ExperimentAssignment

ExperimentAssignment 是 experiment control/analytics record，MAY 被 SYS05 read-only 消费；MUST NOT 成为第二 TeachingAction/LearnerState owner。

### STATE-212 — Ledger Hosting

SYS08 MAY 托管 LearningEvent、DecisionTrace、OutcomeObservation、ExperimentAssignment durable ledger/outbox；hosting = storage/transport responsibility，MUST NOT 修改 payload/domain semantics。

## 8. v0.3 LLM / Policy Boundaries

### STATE-220

LLM/Agent MAY 生成 explanation、worked example、hint、diagnostic candidate、feedback、self-explanation prompt、language realization、tool result；MUST NOT 成为 LearnerState、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule owner 或 hard-rule/answer-exposure override。

### STATE-221

SYS08/SYS02 MAY 收紧 TeachingAction envelope；MUST NOT 扩大 scaffold、hint specificity、answer exposure 或 action semantics。

### STATE-222 — ModelRouteProfile

`ModelRouteProfileV1` 是 SYS08 拥有的版本化执行配置 truth。Electron desktop adapter MAY 加密保存并激活该对象，但 MUST NOT 把密钥或 provider 选择复制成 renderer、普通 API、`.env` 或第二持久化 truth。

### STATE-223 — Disabled Tombstone

桌面用户清除配置时 MUST 写入版本化 `DISABLED` tombstone；该状态优先于外部环境变量，防止旧 `.env` 在重启后静默恢复已清除的 provider。外部环境变量仅在不存在 desktop revision 时作为只读兼容输入。

### STATE-230 — Misconception Four-way Ownership

`Misconception definition → SYS01`；`MisconceptionEvidence → SYS04`；`MisconceptionHypothesis → SYS03`；`Remediation decision → SYS05`。MUST NOT 合并为跨系统可写对象。

## 9. v0.3 Ownership Sweep

### STATE-240

新增公共对象必须明确：state/derived/control/measurement/ledger 分类、唯一 writer、read/execute roles、duplicate-truth risk、replay exact version source。

### STATE-241

Architecture tests MUST 证明不存在第二 LearnerState、第二 TeachingAction、第二 Experiment truth、第二 Outcome truth。

### STATE-250 — Legacy Compatibility

Legacy dialog mastery、Socratic selector/state graph、old policy config、integer support/exposure MAY 暂作 read projection/adapter/audit，必须有 canonical source 与 retirement condition，MUST NOT permanent dual-write。

## 10. Acceptance Criteria

原有 AC 保留：

- `STATE-AC-001`：AssessmentResult 后只有 SYS03 owner path 可创建 MasteryEstimate。
- `STATE-AC-002`：LLM 返回 mastery/next_review_at/plan/action 等字段不能越权写 canonical state。
- `STATE-AC-003`：Planner 消费 ReviewDue 不能修改 ReviewSchedule memory state。
- `STATE-AC-004`：Assessment misconception evidence 由 SYS03 决定是否形成 learner hypothesis。
- `STATE-AC-005`：相同 event/evidence + exact projector replay deterministic。
- `STATE-AC-006`：SourceChunk 重分块不无条件重建 KnowledgeUnit identity。

新增 v0.3 AC：

- `STATE-AC-201`：SYS01～SYS08 canonical truth single-writer。
- `STATE-AC-202`：TeachingContext/TeachingStage 不形成第二 LearnerState。
- `STATE-AC-203`：validation obligation 由 SYS05 控制，fresh Attempt 前不能被 SYS03 完成。
- `STATE-AC-204`：Outcome/Experiment ledger records 不覆盖八系统 domain truth。
- `STATE-AC-205`：LLM/SYS08/legacy Socratic 无 final TeachingAction ownership。
- `STATE-AC-206`：desktop ModelRouteProfile 只有 SYS08 语义 owner，renderer 与普通 API 无 secret truth。
- `STATE-AC-207`：清除配置后的重启保持 DISABLED，不被 `.env` 静默重新激活。

## 11. Forbidden Implementations

禁止：共享大状态表多模块任意写；conversation JSON 混 mastery/plan/review/teaching；多个 mastery/next_due writers；点赞直接转 mastery；LLM confidence 直接变 MasteryEstimate confidence；历史 AssessmentResult 静默覆盖；replay 调在线模型；TeachingStage 进入 learner truth；Outcome/Experiment analytics table 反向成为独立业务 truth；renderer/普通 API 持有模型密钥 truth；desktop vault 与 `.env` permanent dual-write；legacy/v0.3 permanent dual-write。

## 12. P1-06 Onboarding Presentation Boundary

### STATE-300 — OnboardingPreferenceV1

`OnboardingPreferenceV1` 是 Platform Experience Preference 拥有的 presentation-only state，只可保存
journey/version、active/dismissed、boundary notice acknowledgment 与 dismiss metadata。它 MUST NOT 保存
step completion 或 model/document/goal/plan/activity/transcript/recovery truth/ref 副本。

### STATE-301 — Onboarding Read Projection

`OnboardingJourneyViewV1` 和 SYS06 `FirstActivityCompletionProjectionV1` 均为只读投影。Query hosting、
API serialization 或 UI presentation MUST NOT 取得 SYS01～SYS08 写入权；投影失效只能重查 owner，
不得回写或修补 owner state。

### STATE-AC-300

Architecture tests MUST 证明 onboarding 只有 presentation preference writer，且 activity completion 仍只由
SYS06 lifecycle transition 产生。
