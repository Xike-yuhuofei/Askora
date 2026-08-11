# Askora State Ownership Specification

> Spec ID 范围：`STATE-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + v1 Product Positioning Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. Ownership Principles

### STATE-001 — One State, One Writer

任何跨会话、可影响后续业务或教学决策的 canonical state MUST 有唯一写入 owner。其他系统 MAY 读取、缓存、投影或托管 ledger，但 MUST NOT 形成第二 truth。

### STATE-002 — Read Permission != Write Permission

系统读取另一 owner 的 exact-version state 用于决策，并不获得更新该 state 的权限。

### STATE-003 — Suggestion / Evidence != State Update

LLM、grader、retriever、experiment、用户反馈或 UI action 产生的建议/evidence/candidate 必须先由对应 owner 按 contract 接纳，才能形成新的 canonical state/version。

### STATE-004 — Core State Is Versioned

已发布 KnowledgeUnit/Relation revision、AssessmentResult、MasteryEstimate、TeachingAction、LearningPlan、ReviewSchedule、LearningEvent、DecisionTrace MUST 使用 append/version/immutable semantics；TeachingContext、PolicyBundle、OutcomeObservation、ExperimentAssignment 也 MUST immutable/versioned。MUST NOT 静默覆盖历史。

明确的 Trash / Permanent Delete / data erasure 属数据生命周期，不与 immutable/versioned 原则冲突；删除后相关 projection MUST invalidated/rebuilt，MUST NOT resurrect deleted facts。

### STATE-005 — Platform State Is Not a Ninth Learning System

以下 platform state 可以存在于 SYS01～SYS08 之外，但仍必须有唯一 owner：

| State | Owner |
|---|---|
| LocalOwner | Platform Local Identity (`LID-*`) |
| Workspace | Platform Workspace Registry |
| LearningProject / ProjectMaterial membership | Platform Workspace / Product Organization boundary |
| Application/Workspace/Project configuration | owning configuration service, subject to explicit override contract |
| Backup manifest / data-directory compatibility metadata | Platform Data Lifecycle |
| Local background job runtime state | Platform Job Runtime |

Platform owner MUST NOT 因此取得 SYS01～SYS08 学习 truth 的写权限。

### STATE-006 — Workspace Scope Is Part of State Identity

v1 中 Material、LearningProject、LearningGoal、LearningSession、LearningEvidence、LearnerState、LearningHistory、UserNote、Search/Retrieval scope MUST 能解析到唯一 `workspace_id`。

不同 Workspace 的学习状态与资料关系默认互相隔离。没有显式上位产品决策时，MUST NOT 建立 cross-workspace global material/search/learner-state truth。

### STATE-007 — Durable Fact vs Rebuildable Projection

必须区分：

- **Durable facts**：SourceFile、Workspace、LearningProject、LearningGoal、UserNote、Attempt、AssessmentResult、LearningEvidence、LearningHistory、用户配置与删除事实等；
- **Canonical rebuildable projections**：MasteryEstimate、LearnerState 等当前权威派生状态；
- **Infrastructure-derived data**：SourceChunk、Embedding、Vector/Lexical Index、retrieval cache、可重新生成的 AI Summary 等。

“rebuildable”不意味着无 owner：MasteryEstimate / LearnerState 仍只有 SYS03 可写，但 MUST 能从 durable evidence + exact projector/version 重新生成。

## 2. v0.3 Learning Core Ownership Matrix

| Canonical truth / decision | Owner | Other systems may |
|---|---|---|
| Material content semantics / SourceFile refs / Knowledge truth / relations / Misconception definition | SYS01 | read / retrieve / reference |
| EvidenceBundle / RetrievalTrace | SYS02 | consume |
| LearnerEvidence acceptance / MasteryEstimate / LearnerState / MisconceptionHypothesis | SYS03 | read |
| AssessmentItem / Attempt / AssessmentResult / MisconceptionEvidence / actual assistance | SYS04 | consume |
| TeachingAction / TeachingContext decision-snapshot semantics / TeachingStage derivation / PolicyBundle governance / validation obligation | SYS05 | execute / read |
| LearningGoal / Objective / LearningActivity / LearningPlan | SYS06 | read |
| ReviewSchedule / memory scheduling state / next_due_at | SYS07 | read / plan from |
| WorkflowRun / ModelRouteProfile / ModelInference / Tool execution / execution validation | SYS08 | execute / host ledgers |

`LearningProject` 的组织关系不把 Material ownership 转移给 SYS06，也不把 LearningGoal ownership转移给 SYS01；Project 只保存对 canonical refs 的组织关系。

## 3. Boundary Requirements

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

### STATE-015 — Material != SourceFile != SourceDocument Compatibility Record

Material 是 Workspace-scoped 用户资料领域对象；SourceFile 是 Askora managed local raw asset；历史 `SourceDocument` MAY 作为 SYS01 content/compatibility record 存在，但不得替代 Material 的 workspace membership、Project relation 或用户资料生命周期语义。

## 4. Update / Replay Requirements

### STATE-020 — Provenance

关键 state 新版本 MUST 至少追溯 input/event refs、algorithm/policy/model version、time、reason codes、trace/correlation id；Workspace-scoped state 还 MUST 可追溯 workspace scope。

### STATE-021 — No Direct State Update From Chat

Chat MAY 触发 command/self-report/feedback，但 MUST 经结构化 owner contract 才能影响 state；“我已经会了”等 MUST NOT 直接设置 mastery。

### STATE-022 — Dispute / Review

用户争议系统判断时 MUST 进入 FeedbackSignal → dispute/retest/evidence correction/replay → new state version；MUST NOT 通用直接编辑概率。

### STATE-023 — Correction / Deletion

普通纠错追加 correction/invalidation；明确删除按 Trash/Permanent Delete/data-control contract 删除或标记 durable fact，并重建受影响 projection。若删除 LearningEvidence 曾影响 LearnerState，SYS03 MUST 重新投影，不得继续保留旧掌握状态。

### STATE-030 — Monotonic Version

同一 aggregate canonical version MUST 单调递增，并有唯一性约束。

### STATE-031 — Command Idempotency

重复 command MUST NOT 生成第二份等价 evidence/state update。

### STATE-032 — Projection Idempotency

重放相同 durable event/evidence set + exact projection version MUST 得到相同 semantic state。

### STATE-033 — Replay No Online LLM

Replay MUST NOT 调用在线 LLM 重新理解历史；使用当时持久化结构化 result/inference 或显式新 reassessment/recompute。

## 5. Legacy Governance

### STATE-040 — Migration Starts With Owner

任何 legacy table/model 重构前 MUST 标注 target owner、current writers、multi-writer risk、migration strategy、retirement condition。

### STATE-041 — Dual-write Only Temporarily

若 migration 必须短期 dual-write，必须指定 canonical truth、reconciliation、停止条件；MUST NOT 形成永久架构。

### STATE-042 — KT/DKT Convergence

SYS03 MUST 只有一个 canonical learner-state projector。DKT/Deep KT MAY challenger/feature provider，MUST NOT 成为第二 mastery truth。

### STATE-043 — Legacy User/Auth Semantics

历史 `user_id` / `pseudonym_id` MAY 在迁移窗口保留作为 LocalOwner/Learner ownership compatibility key，但 MUST NOT 再解释为 Account/AuthSession principal。Account/Login/Token/Recovery identity truth 由 ADR-0015/LID-* 退役。

### STATE-044 — Desktop/Global-library Legacy

Desktop vault、Electron IPC、全局资料库、跨 Workspace 默认检索、Redis-only state 等旧实现 MAY 作为待迁移 compatibility asset，但 MUST NOT 再成为 v1 Canonical State 来源。

## 6. Derived / Control Objects

### STATE-200 — TeachingContext

TeachingContext 是 SYS05 immutable decision-input snapshot，引用 exact owner versions；MUST NOT 成为第二 LearnerState/AssessmentResult/LearningPlan truth。

### STATE-201 — TeachingStage

TeachingStage = SYS05 从 `TeachingContext + PolicyBundle` 派生的当前 control stage；MUST NOT 持久化为 SYS03 learner/mastery stage truth。

### STATE-202 — PolicyBundle

PolicyBundle 是 SYS05 immutable/versioned policy configuration artifact；activation 只影响新 TeachingAction，MUST NOT 重解释历史 action。

### STATE-203 — Independent Validation Obligation

Validation obligation 属 SYS05 policy-control semantics。SYS04 产生 fresh Attempt/AssessmentResult facts；SYS03 仅判断 evidence eligibility，MUST NOT 创建/提前完成 obligation。

### STATE-204 — LearnerState Is a Canonical Derived Projection

LearnerState / MasteryEstimate 的当前版本 MAY 被其他系统作为 authoritative read projection 使用，但其 source of reconstruction MUST 是 accepted durable LearningEvidence / Assessment-related facts + exact projector version。

删除或修正输入 evidence 后，旧 projection MUST 被 supersede/invalidated 并重建。

## 7. Outcome / Experiment Contracts

### STATE-210 — OutcomeObservation

OutcomeObservation 是 immutable measurement/analytics record，必须引用既有 measurement/evidence owner facts；MUST NOT 替代 AssessmentResult、MasteryEstimate 或 TeachingAction truth。

### STATE-211 — ExperimentAssignment

ExperimentAssignment 是 experiment control/analytics record，MAY 被 SYS05 read-only 消费；MUST NOT 成为第二 TeachingAction/LearnerState owner。

### STATE-212 — Ledger Hosting

SYS08 MAY 托管 LearningEvent、DecisionTrace、OutcomeObservation、ExperimentAssignment durable ledger/outbox；hosting = storage/transport responsibility，MUST NOT 修改 payload/domain semantics。

## 8. LLM / Policy / Model Configuration Boundaries

### STATE-220

LLM/Agent MAY 生成 explanation、worked example、hint、diagnostic candidate、feedback、self-explanation prompt、language realization、tool result；MUST NOT 成为 LearnerState、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule、Workspace、Material membership 或 deletion owner。

### STATE-221

SYS08/SYS02 MAY 收紧 TeachingAction envelope；MUST NOT 扩大 scaffold、hint specificity、answer exposure 或 action semantics。

### STATE-222 — ModelRouteProfile

`ModelRouteProfileV1` 是 SYS08 拥有的版本化执行配置 truth。Local SecretStore / OS-backed credential adapter 只托管 API Key；MUST NOT 把 provider/model/routing selection 复制成 browser storage、普通 API、`.env` 或第二持久化 truth。

Production Local MAY 读取明确的 app-owned configuration metadata；开发/测试环境变量只能是非生产 compatibility input，不得覆盖用户已明确保存或禁用的配置。

### STATE-223 — Disabled / Cleared Configuration

用户清除模型配置后 MUST 形成明确的 disabled/unconfigured canonical profile state，并清除相应 secret。重启后 MUST 保持该语义；不得被旧 `.env`、browser cache 或进程继承变量静默重新激活。

### STATE-230 — Misconception Four-way Ownership

`Misconception definition → SYS01`；`MisconceptionEvidence → SYS04`；`MisconceptionHypothesis → SYS03`；`Remediation decision → SYS05`。MUST NOT 合并为跨系统可写对象。

## 9. Ownership Sweep

### STATE-240

新增公共对象必须明确：state/derived/control/measurement/ledger 分类、唯一 writer、workspace scope、read/execute roles、duplicate-truth risk、replay exact version source。

### STATE-241

Architecture tests MUST 证明不存在第二 LearnerState、第二 TeachingAction、第二 Experiment truth、第二 Outcome truth、第二 LocalOwner 或跨 Workspace 混写。

### STATE-250 — Legacy Compatibility

Legacy dialog mastery、Socratic selector/state graph、old policy config、integer support/exposure MAY 暂作 read projection/adapter/audit，必须有 canonical source 与 retirement condition，MUST NOT permanent dual-write。

## 10. Acceptance Criteria

原有 AC：

- `STATE-AC-001`：AssessmentResult 后只有 SYS03 owner path 可创建 MasteryEstimate。
- `STATE-AC-002`：LLM 返回 mastery/next_review_at/plan/action 等字段不能越权写 canonical state。
- `STATE-AC-003`：Planner 消费 ReviewDue 不能修改 ReviewSchedule memory state。
- `STATE-AC-004`：Assessment misconception evidence 由 SYS03 决定是否形成 learner hypothesis。
- `STATE-AC-005`：相同 event/evidence + exact projector replay deterministic。
- `STATE-AC-006`：SourceChunk 重分块不无条件重建 KnowledgeUnit identity。

v0.3 AC：

- `STATE-AC-201`：SYS01～SYS08 canonical truth single-writer。
- `STATE-AC-202`：TeachingContext/TeachingStage 不形成第二 LearnerState。
- `STATE-AC-203`：validation obligation 由 SYS05 控制，fresh Attempt 前不能被 SYS03 完成。
- `STATE-AC-204`：Outcome/Experiment ledger records 不覆盖八系统 domain truth。
- `STATE-AC-205`：LLM/SYS08/legacy Socratic 无 final TeachingAction ownership。
- `STATE-AC-206`：ModelRouteProfile 只有 SYS08 语义 owner；SecretStore/browser/API 无第二 routing truth。
- `STATE-AC-207`：清除配置后的重启保持 disabled/unconfigured，不被环境变量静默重新激活。

v1 alignment AC：

- `STATE-AC-208`：每个 local datastore 最多一个 LocalOwner，业务不依赖 Account/AuthSession。
- `STATE-AC-209`：Workspace 是强隔离 scope，不被建模为 Tenant/Organization。
- `STATE-AC-210`：Material/Goal/LearnerState/Session/Evidence 可解析到 workspace，默认无 cross-workspace truth mixing。
- `STATE-AC-211`：LearnerState 删除后可由 durable LearningEvidence + projector 重建；删除 evidence 会触发 reprojection。
- `STATE-AC-212`：SourceFile/Material 与 SourceChunk/Embedding/Index 的 durable/derived 分类无歧义。

## 11. Forbidden Implementations

禁止：

- 共享大状态表多模块任意写；
- conversation JSON 混 mastery/plan/review/teaching；
- 多个 mastery/next_due writers；
- 点赞或“我懂了”直接转 mastery；
- LLM confidence 直接变 MasteryEstimate confidence；
- 历史 AssessmentResult 静默覆盖；
- replay 调在线模型；
- TeachingStage 进入 learner truth；
- Outcome/Experiment analytics table 反向成为独立业务 truth；
- browser/普通 API 持有模型密钥 truth；
- `.env` 与用户配置 permanent dual-write；
- Workspace 当 Tenant/Organization；
- 全局 Material Library 作为 v1 canonical scope；
- 删除 LearningEvidence 后继续保留受其影响的旧 LearnerState；
- legacy/v0.3 permanent dual-write。

## 12. P1-06 Onboarding Presentation Boundary

### STATE-300 — OnboardingPreferenceV1

`OnboardingPreferenceV1` 是 Platform Experience Preference 拥有的 presentation-only state，只可保存 journey/version、active/dismissed、boundary notice acknowledgment 与 dismiss metadata。它 MUST NOT 保存 step completion 或 model/material/goal/plan/activity/transcript/recovery truth/ref 副本。

其 owner key canonical semantics MUST 是 LocalOwner；历史 `user_id` 列 MAY 作为迁移兼容字段存在。

### STATE-301 — Onboarding Read Projection

`OnboardingJourneyViewV1` 和 SYS06 `FirstActivityCompletionProjectionV1` 均为只读投影。Query hosting、API serialization 或 UI presentation MUST NOT 取得 SYS01～SYS08 写入权；投影失效只能重查 owner，不得回写或修补 owner state。

### STATE-310 — UI Workspace Read Projections

`WorkspaceContextResponseV1` 与 `LearningContextResponseV1` 是 ADR-0019 冻结的只读 UI 聚合投影：

- Workspace identity/name/version 只读 Platform Workspace Registry；
- Drawer stage 只读 exact SYS05 TeachingAction；
- Drawer next directions 只读 ordered exact SYS06 LearningActivity；
- stage-goal presentation catalog 必须版本化，且不得成为 LearningGoal、LearningObjective、TeachingStage mapper 或 TeachingAction 的 writer/truth；
- query assembler 只拥有 composition/serialization，不拥有任何被读取状态。

任何 frontend cache、route、chat text、LLM output 或 read-model row MUST NOT 成为第二 Workspace/Stage/Plan truth。

### STATE-AC-310

Architecture/contract tests MUST 证明两个 projection 无 write path、无新持久化表、无 frontend inference，并保留 exact owner source refs。

### STATE-AC-300

Architecture tests MUST 证明 onboarding 只有 presentation preference writer，且 activity completion 仍只由 SYS06 lifecycle transition 产生。
