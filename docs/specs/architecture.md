# Askora System Architecture Specification

> Spec ID 范围：`ARCH-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 Learning Core + v1 Product Positioning Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

## 1. Goal

Askora MUST 以**单用户、单设备、Local Web Application、模块化单体**为 v1 正式产品架构，并在该运行边界内实现个人长期学习闭环。

未经新的 Product Positioning Delta + Canonical Design + ADR + Spec：

- MUST NOT 将八类学习系统拆成独立微服务；
- MUST NOT 让 LLM/Agent 成为跨域超级 owner；
- MUST NOT 把公网 SaaS、Desktop/Electron、Redis、PostgreSQL、Docker、Kafka、Kubernetes 或 Elasticsearch 集群变成 v1 最终用户运行前提；
- MUST NOT 为未来多用户、多设备或云同步预付分布式复杂度。

## 2. Top-level Principles

### ARCH-001 — Learning Loop, Not Chat-first

canonical 主链：

```text
LearningGoal / LearningPlan
→ LearningActivity
→ TeachingContext Snapshot
→ SYS05 TeachingAction
→ SYS02 EvidenceBundle
→ SYS08 Execution
→ SYS04 Attempt / AssessmentResult
→ SYS03 LearnerEvidence / LearnerState
→ SYS07 ReviewSchedule
→ SYS06 Replan when triggered
→ next TeachingContext
```

普通、流式、浏览器教学请求 MUST 汇入同一 canonical teaching/orchestration boundary；direct chat/Socratic path MUST NOT 长期并存为第二生产主链。

Conversation / Message / Prompt MAY 是交互或执行对象，但 MUST NOT 成为 Askora 核心领域模型或学习事实源。

### ARCH-002 — Decision vs Generation

LLM MAY 生成候选、讲解、worked example、hint、feedback、self-explanation prompt、language realization、tool output；MUST NOT 成为 mastery、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule、knowledge publication、Workspace membership 或数据删除决定的权威 writer，也 MUST NOT override hard rules/exposure envelope。

### ARCH-003 — Single Writer

每类 canonical truth MUST 有唯一 owner。其他系统只可读取 exact-version snapshot、发送 command/event/evidence 或执行已决定动作；MUST NOT 跨系统直接 ORM 写入。

Platform domain（例如 LocalOwner / Workspace Registry）可以拥有学习核心之外的平台状态，但不得因此取得 SYS01～SYS08 的学习状态写权限。

### ARCH-004 — Fact / Measurement / Inference / Decision / Execution / Outcome

Source fact、user fact、Measurement、Learner inference、Policy/planning decision、Execution 与 Later Outcome MUST 分层。Outcome MUST NOT 回写历史 DecisionTrace reasoning。

### ARCH-005 — Immutable History + Replayable Projection

关键 event、TeachingAction、TeachingContext、DecisionTrace、PolicyBundle refs 与 OutcomeObservation SHOULD immutable/versioned。正常纠错使用 new version/supersede/reprojection，MUST NOT 静默覆盖历史。

“immutable”不等于“用户永远不可删除”：明确的 Trash / Permanent Delete / owner-safe erasure 可删除 durable fact，并 MUST invalidate/rebuild 受影响 projection，防止已删除事实通过重放复活。

### ARCH-006 — v1 Local Web Application Is the Product Runtime

Askora v1 正式运行拓扑固定为：

```text
Browser (Chrome / Edge prioritized)
        ↓ loopback HTTP/WebSocket
http://127.0.0.1:<port>
        ↓
Askora Local Server
├── Application Layer
├── Learning Core (SYS01～SYS08)
├── Content Pipeline
├── Retrieval
├── Local Background Job Runtime
├── SQLite
├── Managed Local Files
├── Local Derived Indexes / Cache
└── AI Provider Adapter
        ↓ Internet when needed
External AI APIs (BYOK)
```

`Web` 在 Askora 中指 Local Web Application，不等于公网 SaaS。

v1：

- UI MUST 通过浏览器访问本机 Local Server；
- Local Server MUST 默认仅绑定 `127.0.0.1` / `::1`；
- MUST NOT 默认作为 LAN Server 或公网服务；
- macOS/Windows 原生客户端、Electron/Desktop shell 不属于 v1 Canonical Runtime；
- Desktop-specific adapter 不得继续出现在 v1 必须实现合同中。

### ARCH-007 — Baseline Before Advanced Algorithms

高级算法必须有透明 baseline。v0.3 Teaching Policy canonical runtime 是 ADR-0002 B3 constrained deterministic architecture；Contextual Bandit、Offline/Online RL、Deep KT canonical truth、autonomous multi-agent 均不在当前 canonical runtime scope。

### ARCH-008 — LocalOwner and Workspace Are Mandatory Scope Boundaries

每个 LocalDataStore 最多有一个 canonical `LocalOwner`。业务请求通过 `LocalOwnerContext` 解析长期 learner/data ownership，不通过 Account/AuthSession。

Workspace 是 LocalOwner 下的高层数据隔离边界，不是 Tenant / Organization，也不是第九学习系统。

以下对象/行为 MUST 能确定其 Workspace scope：

- Material / SourceFile / knowledge publication；
- LearningProject / LearningGoal / LearningSession；
- LearnerState / LearningEvidence / Assessment history；
- UserNote；
- Retrieval / Search；
- background rebuild jobs。

不同 Workspace 默认 MUST NOT 共享 LearnerState、资料关系或检索结果。跨 Workspace 行为若未来引入，必须是显式的新产品决策。

### ARCH-009 — SQLite Is the v1 Production Persistence Baseline

Askora v1 production-local structured data baseline MUST 是 SQLite；原始资料与其他文件资产使用 Askora 管理的本地文件系统；检索索引是本地可重建 projection；进程内内存只用于临时 cache/runtime state。

PostgreSQL MAY 用于 CI、测试或未来可选模式，但 MUST NOT 是 v1 最终用户运行要求。Redis/Kafka 等不得成为 production-local correctness dependency。

### ARCH-010 — Durable Facts vs Rebuildable Projections

架构 MUST 显式区分：

```text
Durable / Canonical Facts
- LocalOwner / Workspace / LearningProject
- Material / SourceFile
- LearningGoal / UserNote
- Attempt / AssessmentResult / LearningEvidence
- Learning history / configuration / deletion facts

Canonical Rebuildable Projections
- MasteryEstimate / LearnerState
- other derived learner projections

Infrastructure-derived Data
- SourceChunk
- Embedding
- Vector / lexical index
- cached retrieval
- rebuildable AI summaries
```

LearnerState 可以是当前 canonical projection，但 MUST 尽可能能够由 durable LearningEvidence + exact projector/version 重建；不得把它当作不可替代的原始事实。

### ARCH-011 — Local Background Jobs Are Durable and Restart-safe

Parsing、Embedding、Knowledge Extraction、Indexing、Rebuild 等后台任务 MUST 使用本地持久化任务状态，不得只存在于内存。

最少支持：

```text
pending | running | succeeded | failed | interrupted
```

任务 MUST bounded concurrency、尽可能幂等、可去重/互斥、可从安全边界 resume/retry/restart。App 关闭不得破坏 Durable Data。

### ARCH-012 — Backup, Restore and Schema Migration Are Platform Capabilities

v1 MUST 把 Schema Migration、数据目录兼容性检查、Backup/Restore 作为 Platform Architecture，而不是临时运维脚本。

```text
Startup
→ resolve data directory
→ verify reader/writer/schema compatibility
→ create safety backup when required
→ migrate
→ validate
→ start services/jobs
→ open browser
```

Backup 用于恢复 Askora；Export 用于让数据离开 Askora 后继续可用。二者 MUST 分离。

### ARCH-013 — BYOK and Secret Boundary

用户自行配置 AI Provider / Model / API Key。Secret 只保存在本机，MUST NOT 上传 Askora 官方服务器、进入默认 backup/diagnostic/log、Workspace/Project 普通文件或浏览器持久化存储。

Secret storage MUST 通过本地 platform adapter 隔离；优先使用 OS-backed secure credential storage。SYS08 仍拥有 `ModelRouteProfile` 的语义，SecretStore 只负责凭据托管，不成为第二 routing truth。

### ARCH-014 — External AI Is Unreliable, Local Data Is Authoritative

Askora 是 Local-first，不是 Offline-only。外部 AI Provider failure MUST NOT 损坏 Durable Data。离线时 SHOULD 仍可启动、查看本地资料/历史/项目/目标/状态并管理本地数据。

AI 调用、fallback、provider/model/version 与关键原因 MUST 可追踪；关键任务不得静默跨模型切换。

### ARCH-015 — User-visible Startup Must Not Require Developer Infrastructure

最终用户启动体验 MUST 收敛为“启动 Askora → Local Server 自检/恢复 → 自动打开浏览器”。用户不得被要求手工启动 Docker、Redis、PostgreSQL 或开发者命令。

## 3. v0.3 Eight Systems & Ownership

> 八系统是 Learning Core，不包含 LocalOwner/Workspace/Backup 等平台横切能力。

### ARCH-300 — SYS01 Content & Knowledge

Owner：Material content semantics、SourceFile/MaterialRevision content refs、KnowledgeUnit、Concept、PrerequisiteRelation、Misconception definition。MUST NOT own mastery/action/plan/review/EvidenceBundle final selection。

Material MUST 属于一个 Workspace。`SourceDocument` 若保留，应解释为 Material 内部 content record / compatibility object，不得替代 Workspace-scoped Material 产品语义。

### ARCH-301 — SYS02 Retrieval

Owner：EvidenceBundle、RetrievalTrace。读取 TeachingAction envelope 并 MAY 收紧 `answer_exposure`；MUST NOT 扩大或自行改变 TeachingAction。

每个 production RetrievalScope MUST 至少包含 `workspace_id`；默认不得跨 Workspace 搜索。

### ARCH-302 — SYS03 Learner Model

Owner：LearnerEvidence acceptance、MasteryEstimate、LearnerState、MisconceptionHypothesis。TeachingStage MUST NOT 成为 SYS03 persistent truth。

MasteryEstimate / LearnerState 属 canonical derived projection；其唯一 writer 仍是 SYS03，但必须能够基于 durable evidence/versioned algorithm 重建。

### ARCH-303 — SYS04 Assessment

Owner：AssessmentItem、Attempt、AssessmentResult、MisconceptionEvidence、actual assistance/exposure。`assessment_confidence != diagnostic_confidence`。

### ARCH-304 — SYS05 Teaching Policy

唯一 owner：TeachingAction；同时负责 TeachingContext snapshot/evaluation semantics、TeachingStage derivation、PolicyBundle governance、independent validation obligation。

Canonical StrategyFamily 仅：

```text
EXPLICIT_INSTRUCTION
GUIDED_PRACTICE
FADING_PRACTICE
RETRIEVAL_PRACTICE
ERROR_REMEDIATION
TRANSFER_CHALLENGE
```

Allowed envelope：

```text
scaffold_control = NONE|LOW|MEDIUM|HIGH
hint_specificity = NONE|ORIENTATION|CONCEPTUAL_STRATEGIC|SUBGOAL|PARTIAL_STEP|BOTTOM_OUT
answer_exposure = NONE|PARTIAL|COMPLETE
```

`StrategyFamily != TeachingAction != InteractionMove`。Socratic/worked example/direct instruction/self-explanation/metacognition 属 bounded move/modifier；generic Productive Failure MUST NOT selectable。

### ARCH-305 — SYS06 Learning Planner

Owner：LearningGoal controlled version、LearningObjective、LearningActivity、LearningPlan、replan/day priority。MUST NOT 决定 hint/explanation 或 `next_due_at` truth。

LearningGoal MUST 在 Workspace scope 内。LearningProject membership 由 Workspace/Product Organization boundary 管理，SYS06 只保存/消费明确 project ref，不接管 Material membership truth。

### ARCH-306 — SYS07 Review Scheduler

Owner：ReviewSchedule、memory scheduling state、retrievability estimate、`next_due_at`。MUST NOT own daily plan、TeachingAction、mastery truth。

### ARCH-307 — SYS08 AI Orchestration & Trust

Owner：Session/Workflow execution state、`ModelRouteProfile`/ModelRoute/Inference、ToolCall/Result、PromptVersion、execution validation/telemetry。

Local SecretStore / OS credential adapter MAY 托管 API Key，但不得成为第二 ModelRouteProfile owner。Browser UI、普通 API、renderer MUST NOT 持有持久化 secret truth。

SYS08 MAY host LearningEvent/DecisionTrace/Outcome/Experiment ledger persistence，但 hosting MUST NOT 成为 payload/domain ownership。SYS08 MAY tighten action envelope；MUST NOT expand semantics。

## 4. v0.3 Canonical Policy Architecture

### ARCH-320

SYS05 B3 runtime MUST 实现：

```text
TeachingContext Snapshot
→ Typed Hard Constraints
→ Derived TeachingStage
→ Typed Candidate Generation / Decision Table
→ Feature Builder
→ Normalized Weighted Scoring
→ Anti-Oscillation Gate
→ Deterministic Tie-break
→ Immutable TeachingAction
→ DecisionTrace
```

Hard Constraint MUST NOT 被 soft score、LLM、experiment 恢复。

### ARCH-321

TeachingContext MUST exact-version/immutable，并显式处理 `AVAILABLE|MISSING|STALE|LOW_CONFIDENCE|NOT_APPLICABLE`；replay MUST NOT 读当前 mutable state 或重新调用在线 LLM。

### ARCH-322

Anti-oscillation MUST 覆盖 Material Evidence Gate、Sticky Continuity、Minimum Dwell by Evidence Opportunity、Hysteresis、Transition Priority、Repeated Failure Override。

### ARCH-323

PolicyBundle MUST immutable/versioned/atomic activate/exact pin/historical retain；MUST NOT 包含 executable DSL、embedded Python、free-form runtime policy code 或 LLM-generated rules。

### ARCH-324

B3 trace MUST 写 `behavior_policy_type=DETERMINISTIC`、`action_propensity=null`；ExperimentAssignment probability MUST 与 action propensity 分离。

## 5. Cross-system Data Flow

### ARCH-020 — Standard Teaching Round

```text
SYS06 selects LearningActivity
→ SYS05 snapshots TeachingContext + creates TeachingAction
→ SYS02 creates EvidenceBundle if required
→ SYS08 executes within/tighter envelope
→ SYS04 records Attempt / AssessmentResult / actual assistance
→ SYS03 accepts evidence and rebuilds/updates learner projection
→ SYS07 updates ReviewSchedule from valid retrieval evidence
→ SYS06 replans only on trigger
```

### ARCH-021 — No Synchronous Multi-owner Mutation

循环 MUST 通过 new events/versions/commands 形成；MUST NOT 在一个 transaction/call stack 直接修改多个 owner tables。

### ARCH-022 — Failure Return

SYS02/SYS08 MAY 返回 missing evidence、conflict、low confidence、model/tool unavailable、validation failure；MUST NOT 自行改变 TeachingAction semantics。需要改变教学策略时 MUST 回 SYS05 创建新 action。

## 6. Legacy Architecture Governance

### ARCH-030 — Legacy Freeze

对应 migration 完成前，legacy 模块 MAY 修复，但 MUST NOT 继续向错误边界增加长期 state ownership。

Desktop/Electron、Account/AuthSession、global-library、Redis-required、PostgreSQL-required 等与 v1 Product Positioning 冲突的 legacy 代码只能作为待退役实现，不得反向进入新的 Canonical Spec。

### ARCH-031 — No Dual Truth Source

状态迁移后，旧路径 MUST 进入 read-only/adapter/removal 阶段；MUST NOT 新旧两套 truth 持续 dual-write 且无 reconciliation/retirement contract。

## 7. v0.3 Misconception / Validation Boundaries

### ARCH-330

`Misconception definition → SYS01`；`MisconceptionEvidence → SYS04`；`MisconceptionHypothesis → SYS03`；`Remediation decision → SYS05`。

### ARCH-331

ASSISTED/ANSWER_EXPOSED success → SYS05 `INDEPENDENT_VALIDATION_REQUIRED`。Obligation 不是 MasteryState；只有 fresh independent Attempt/result 才能提供满足事实。

## 8. v0.3 Outcome / Experiment Architecture

### ARCH-340

TeachingEpisode、LearningTrajectory、OutcomeObservation、ExperimentAssignment 是 additive domain/analytics/experiment contracts，不建立第九 learning state owner。

### ARCH-341

Delayed outcome MUST NOT 自动 last-touch；attribution 使用 ACTION_DIRECT / EPISODE_ASSOCIATED / TRAJECTORY_ASSOCIATED / EXPERIMENTALLY_CAUSAL / UNATTRIBUTABLE。

## 9. v1 Platform Architecture

推荐模块边界：

```text
apps/backend/app/
├── platform/
│   ├── local_identity/
│   ├── workspace/
│   ├── configuration/
│   ├── secrets/
│   ├── jobs/
│   ├── backup_restore/
│   ├── schema_migration/
│   └── observability/
├── domains/
│   ├── content_knowledge/
│   ├── retrieval/
│   ├── learner_model/
│   ├── assessment/
│   ├── teaching_policy/
│   ├── learning_planner/
│   └── review_scheduler/
├── orchestration/
├── ai/
├── contracts/
├── infrastructure/
├── api/
└── legacy/ or adapters/
```

这是目标依赖边界，不要求大爆炸重写；后续 Vertical Slice/EXEC 渐进迁移。

Local Web runtime 允许 frontend 作为 transport/presentation adapter，但 UI state MUST NOT 取代 backend canonical state。

## 10. Legacy Mapping Direction

### ARCH-350

`services/documents/` → SYS01+SYS02；`services/kt/` → SYS03 baseline；`services/dkt/` → challenger；`services/assessment/` → SYS04；legacy Socratic selector/state graph → bounded provider/adapter but not final owner；`engines/*_engine.py` → SYS08 execution adapters；dialog/session mastery → read-only migration projection。

Desktop/Electron-specific code → retirement/compatibility only；不得承载 v1 production-only secret、launch、routing 或 state ownership。

### ARCH-351 — No Permanent Dual Truth

Old nine-family strategy、integer scaffold/hint/exposure、legacy Socratic selector、old policy config、ambiguous propensity、Account/AuthSession、desktop vault、global material scope MAY only read/audit compatibility with retirement conditions；MUST NOT dual-write canonical truth。

## 11. Quality / Release Architecture

### ARCH-360

Testing MUST include L0～L6 + OPVE；G0 hard constraints MUST 100% pass、forbidden action=0；G1 selected action MUST belong to acceptable set。

Production-local tests MUST additionally cover SQLite, loopback-only binding, restart-safe jobs, data-directory compatibility, backup/restore, migration and derived-data rebuild without Redis/PostgreSQL/Docker runtime dependencies。

### ARCH-361

Release MUST distinguish Engineering Gate、Policy Correctness Gate、Learning Evidence Gate。Engineering/Policy Correct MUST NOT be claimed learning efficacy。Primary learning outcomes：no-hint independent success、delayed independent performance、independent transfer、unit-time capability gain；engagement/turns/likes/hints/tokens/session duration 仅 process diagnostics。

## 12. Acceptance Criteria

原有 AC：

- `ARCH-AC-001`：任一核心业务 state 可指出唯一 owner，且不存在无合同第二 writer。
- `ARCH-AC-002`：普通/流式教学请求经过同一 canonical orchestrator 主链。
- `ARCH-AC-003`：AssessmentResult 不直接等于 MasteryEstimate，存在 explicit evidence → learner model boundary。
- `ARCH-AC-004`：TeachingAction 与 LearningPlan 分离，SYS05 不重排长期目标。
- `ARCH-AC-005`：ReviewSchedule 与 LearnerState 分离，Planner 不重复计算 forgetting model。
- `ARCH-AC-006`：LLM/Agent 无直接写 SYS01/SYS03/SYS04/SYS05/SYS06/SYS07 canonical state 通道。
- `ARCH-AC-007`：关键 decisions/model calls 可用 version + trace id 追踪。
- `ARCH-AC-008`：固定 projection/algorithm 的 event replay 不依赖在线 LLM。

v0.3 AC：

- `ARCH-AC-201`：SYS01～SYS08 canonical truth single-writer，无第二 learning truth。
- `ARCH-AC-202`：SYS05 only six StrategyFamily，four-layer ontology 可审计。
- `ARCH-AC-203`：SYS02/SYS08 only tighten action envelope。
- `ARCH-AC-204`：TeachingStage 不进入 LearnerState truth。
- `ARCH-AC-205`：Policy replay 无 online LLM/current mutable reads。
- `ARCH-AC-206`：Outcome/Experiment records 不形成第九 learning owner。
- `ARCH-AC-207`：legacy Socratic 无 final TeachingAction ownership。

v1 Product Positioning Alignment AC：

- `ARCH-AC-208`：正式产品路径为 Browser → loopback Local Server；无 Desktop/Electron 必需运行链。
- `ARCH-AC-209`：production-local 在没有 Docker/Redis/PostgreSQL/Kafka 时仍能完成启动与核心本地数据访问。
- `ARCH-AC-210`：LocalOwner 唯一，Workspace scope 可贯穿 Material/Goal/LearnerState/Session/Retrieval。
- `ARCH-AC-211`：跨 Workspace 默认检索与 learner projection 隔离。
- `ARCH-AC-212`：删除 Derived Data 后可从 Durable Data 重建正确 projection；LearnerState 可由 LearningEvidence 重投影。
- `ARCH-AC-213`：后台任务在 App 中断/重启后可安全恢复或重试，不损坏 Durable Data。
- `ARCH-AC-214`：Backup/Restore 与 Export 分离，Schema mismatch 会 fail closed 或进入 versioned migration。
- `ARCH-AC-215`：API Key 不进入普通 DB/export/backup/log/diagnostic/browser persistence，ModelRouteProfile 与 SecretStore 无第二 truth。

## 13. Spec-ID Governance

`ARCH-001..015`、`ARCH-020..022`、`ARCH-030/031`、`ARCH-AC-001..008` 保留平台/通用职责；v0.3 ontology/policy/outcome/migration/quality requirements 使用 `ARCH-300+`；v1 产品对齐使用新增 `ARCH-008..015` 与 `ARCH-AC-208..215`。MUST NOT 复用既有 ID 改成无关语义。

## 14. Forbidden Architecture

禁止：

- TutorAgent 同时拥有八类决策；
- direct chat 与 canonical teaching 两条默认主链；
- cross-owner writes；
- SYS08/SYS02 envelope expansion；
- old strategy/support fields canonical writing；
- TeachingStage persistent learner truth；
- DecisionTrace/Outcome 混写；
- deterministic `action_propensity=1.0`；
- Contextual Bandit/RL/Deep KT 自动成为当前 canonical runtime；
- ledger hosting = domain ownership；
- 为架构美观大爆炸重写；
- 把 Local Web 当临时开发壳、把 Electron/Desktop 当 v1 目标；
- 把 Workspace 建模为 Tenant/Organization；
- 建立跨 Workspace 默认全局资料库/全局检索；
- Redis/PostgreSQL/Docker/Kafka 作为 v1 最终用户启动前提；
- SourceChunk/Embedding/Index 成为不可重建 truth；
- LLM 直接写 SQLite/canonical state；
- 未经版本检查直接打开未知数据目录并写入。

---

## Askora State Ownership Specification

> Spec ID 范围：`STATE-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + v1 Product Positioning Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

### 1. Ownership Principles

#### STATE-001 — One State, One Writer

任何跨会话、可影响后续业务或教学决策的 canonical state MUST 有唯一写入 owner。其他系统 MAY 读取、缓存、投影或托管 ledger，但 MUST NOT 形成第二 truth。

#### STATE-002 — Read Permission != Write Permission

系统读取另一 owner 的 exact-version state 用于决策，并不获得更新该 state 的权限。

#### STATE-003 — Suggestion / Evidence != State Update

LLM、grader、retriever、experiment、用户反馈或 UI action 产生的建议/evidence/candidate 必须先由对应 owner 按 contract 接纳，才能形成新的 canonical state/version。

#### STATE-004 — Core State Is Versioned

已发布 KnowledgeUnit/Relation revision、AssessmentResult、MasteryEstimate、TeachingAction、LearningPlan、ReviewSchedule、LearningEvent、DecisionTrace MUST 使用 append/version/immutable semantics；TeachingContext、PolicyBundle、OutcomeObservation、ExperimentAssignment 也 MUST immutable/versioned。MUST NOT 静默覆盖历史。

明确的 Trash / Permanent Delete / data erasure 属数据生命周期，不与 immutable/versioned 原则冲突；删除后相关 projection MUST invalidated/rebuilt，MUST NOT resurrect deleted facts。

#### STATE-005 — Platform State Is Not a Ninth Learning System

以下 platform state 可以存在于 SYS01～SYS08 之外，但仍必须有唯一 owner：

| State | Owner |
|---|---|
| LocalOwner | Platform Local Identity (`LID-*`) |
| Workspace | Platform Workspace Registry |
| WorkspaceSelection / current Workspace preference | Platform Workspace Registry (`CWSP-*`) |
| LearningProject / ProjectMaterial membership | Platform Workspace / Product Organization boundary |
| Application/Workspace/Project configuration | owning configuration service, subject to explicit override contract |
| Backup manifest / data-directory compatibility metadata | Platform Data Lifecycle |
| Local background job runtime state | Platform Job Runtime |

Platform owner MUST NOT 因此取得 SYS01～SYS08 学习 truth 的写权限。

#### STATE-006 — Workspace Scope Is Part of State Identity

v1 中 Material、LearningProject、LearningGoal、LearningSession、LearningEvidence、LearnerState、LearningHistory、UserNote、Search/Retrieval scope MUST 能解析到唯一 `workspace_id`。

不同 Workspace 的学习状态与资料关系默认互相隔离。没有显式上位产品决策时，MUST NOT 建立 cross-workspace global material/search/learner-state truth。

#### STATE-007 — Durable Fact vs Rebuildable Projection

必须区分：

- **Durable facts**：SourceFile、Workspace、LearningProject、LearningGoal、UserNote、Attempt、AssessmentResult、LearningEvidence、LearningHistory、用户配置与删除事实等；
- **Canonical rebuildable projections**：MasteryEstimate、LearnerState 等当前权威派生状态；
- **Infrastructure-derived data**：SourceChunk、Embedding、Vector/Lexical Index、retrieval cache、可重新生成的 AI Summary 等。

“rebuildable”不意味着无 owner：MasteryEstimate / LearnerState 仍只有 SYS03 可写，但 MUST 能从 durable evidence + exact projector/version 重新生成。

### 2. v0.3 Learning Core Ownership Matrix

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

### 3. Boundary Requirements

#### STATE-010 — AssessmentResult != MasteryEstimate

AssessmentResult 只描述一次 Attempt/measurement；只有 SYS03 可把一个或多个 accepted evidence 融合为 MasteryEstimate。SYS04/Assessment MUST NOT 直接写 mastery。

#### STATE-011 — ReviewSchedule != MasteryEstimate

SYS07 MAY 维护 stability/difficulty/retrievability/next_due_at，但 MUST NOT 宣布 stable/transfer mastery。

#### STATE-012 — LearningPlan != TeachingAction

SYS06 决定 learning objective/activity/priority/sequence；SYS05 决定当前教学动作、支架/提示/答案暴露 envelope 与 policy-control semantics。两者 MUST 独立 versioned。

#### STATE-013 — SourceChunk != KnowledgeUnit

SourceChunk 是可重建 retrieval projection；KnowledgeUnit 是 canonical knowledge identity。重新分块 MUST NOT 自动重建全部 KnowledgeUnit identity。

#### STATE-014 — Misconception Definition != Learner Hypothesis

SYS01 定义 misconception；SYS04 产生 MisconceptionEvidence；SYS03 维护 MisconceptionHypothesis；SYS05 决定 remediation。

#### STATE-015 — Material != SourceFile != SourceDocument Compatibility Record

Material 是 Workspace-scoped 用户资料领域对象；SourceFile 是 Askora managed local raw asset；历史 `SourceDocument` MAY 作为 SYS01 content/compatibility record 存在，但不得替代 Material 的 workspace membership、Project relation 或用户资料生命周期语义。

### 4. Update / Replay Requirements

#### STATE-020 — Provenance

关键 state 新版本 MUST 至少追溯 input/event refs、algorithm/policy/model version、time、reason codes、trace/correlation id；Workspace-scoped state 还 MUST 可追溯 workspace scope。

#### STATE-021 — No Direct State Update From Chat

Chat MAY 触发 command/self-report/feedback，但 MUST 经结构化 owner contract 才能影响 state；“我已经会了”等 MUST NOT 直接设置 mastery。

#### STATE-022 — Dispute / Review

用户争议系统判断时 MUST 进入 FeedbackSignal → dispute/retest/evidence correction/replay → new state version；MUST NOT 通用直接编辑概率。

#### STATE-023 — Correction / Deletion

普通纠错追加 correction/invalidation；明确删除按 Trash/Permanent Delete/data-control contract 删除或标记 durable fact，并重建受影响 projection。若删除 LearningEvidence 曾影响 LearnerState，SYS03 MUST 重新投影，不得继续保留旧掌握状态。

#### STATE-030 — Monotonic Version

同一 aggregate canonical version MUST 单调递增，并有唯一性约束。

#### STATE-031 — Command Idempotency

重复 command MUST NOT 生成第二份等价 evidence/state update。

#### STATE-032 — Projection Idempotency

重放相同 durable event/evidence set + exact projection version MUST 得到相同 semantic state。

#### STATE-033 — Replay No Online LLM

Replay MUST NOT 调用在线 LLM 重新理解历史；使用当时持久化结构化 result/inference 或显式新 reassessment/recompute。

### 5. Legacy Governance

#### STATE-040 — Migration Starts With Owner

任何 legacy table/model 重构前 MUST 标注 target owner、current writers、multi-writer risk、migration strategy、retirement condition。

#### STATE-041 — Dual-write Only Temporarily

若 migration 必须短期 dual-write，必须指定 canonical truth、reconciliation、停止条件；MUST NOT 形成永久架构。

#### STATE-042 — KT/DKT Convergence

SYS03 MUST 只有一个 canonical learner-state projector。DKT/Deep KT MAY challenger/feature provider，MUST NOT 成为第二 mastery truth。

#### STATE-043 — Legacy User/Auth Semantics

历史 `user_id` / `pseudonym_id` MAY 在迁移窗口保留作为 LocalOwner/Learner ownership compatibility key，但 MUST NOT 再解释为 Account/AuthSession principal。Account/Login/Token/Recovery identity truth 由 ADR-0015/LID-* 退役。

#### STATE-044 — Desktop/Global-library Legacy

Desktop vault、Electron IPC、全局资料库、跨 Workspace 默认检索、Redis-only state 等旧实现 MAY 作为待迁移 compatibility asset，但 MUST NOT 再成为 v1 Canonical State 来源。

### 6. Derived / Control Objects

#### STATE-200 — TeachingContext

TeachingContext 是 SYS05 immutable decision-input snapshot，引用 exact owner versions；MUST NOT 成为第二 LearnerState/AssessmentResult/LearningPlan truth。

#### STATE-201 — TeachingStage

TeachingStage = SYS05 从 `TeachingContext + PolicyBundle` 派生的当前 control stage；MUST NOT 持久化为 SYS03 learner/mastery stage truth。

#### STATE-202 — PolicyBundle

PolicyBundle 是 SYS05 immutable/versioned policy configuration artifact；activation 只影响新 TeachingAction，MUST NOT 重解释历史 action。

#### STATE-203 — Independent Validation Obligation

Validation obligation 属 SYS05 policy-control semantics。SYS04 产生 fresh Attempt/AssessmentResult facts；SYS03 仅判断 evidence eligibility，MUST NOT 创建/提前完成 obligation。

#### STATE-204 — LearnerState Is a Canonical Derived Projection

LearnerState / MasteryEstimate 的当前版本 MAY 被其他系统作为 authoritative read projection 使用，但其 source of reconstruction MUST 是 accepted durable LearningEvidence / Assessment-related facts + exact projector version。

删除或修正输入 evidence 后，旧 projection MUST 被 supersede/invalidated 并重建。

### 7. Outcome / Experiment Contracts

#### STATE-210 — OutcomeObservation

OutcomeObservation 是 immutable measurement/analytics record，必须引用既有 measurement/evidence owner facts；MUST NOT 替代 AssessmentResult、MasteryEstimate 或 TeachingAction truth。

#### STATE-211 — ExperimentAssignment

ExperimentAssignment 是 experiment control/analytics record，MAY 被 SYS05 read-only 消费；MUST NOT 成为第二 TeachingAction/LearnerState owner。

#### STATE-212 — Ledger Hosting

SYS08 MAY 托管 LearningEvent、DecisionTrace、OutcomeObservation、ExperimentAssignment durable ledger/outbox；hosting = storage/transport responsibility，MUST NOT 修改 payload/domain semantics。

### 8. LLM / Policy / Model Configuration Boundaries

#### STATE-220

LLM/Agent MAY 生成 explanation、worked example、hint、diagnostic candidate、feedback、self-explanation prompt、language realization、tool result；MUST NOT 成为 LearnerState、Assessment truth、TeachingAction、LearningPlan、ReviewSchedule、Workspace、Material membership 或 deletion owner。

#### STATE-221

SYS08/SYS02 MAY 收紧 TeachingAction envelope；MUST NOT 扩大 scaffold、hint specificity、answer exposure 或 action semantics。

#### STATE-222 — ModelRouteProfile

`ModelRouteProfileV1` 是 SYS08 拥有的版本化执行配置 truth。Local SecretStore / OS-backed credential adapter 只托管 API Key；MUST NOT 把 provider/model/routing selection 复制成 browser storage、普通 API、`.env` 或第二持久化 truth。

Production Local MAY 读取明确的 app-owned configuration metadata；开发/测试环境变量只能是非生产 compatibility input，不得覆盖用户已明确保存或禁用的配置。

#### STATE-223 — Disabled / Cleared Configuration

用户清除模型配置后 MUST 形成明确的 disabled/unconfigured canonical profile state，并清除相应 secret。重启后 MUST 保持该语义；不得被旧 `.env`、browser cache 或进程继承变量静默重新激活。

#### STATE-224 — Learning Conversation Message Artifact

`LearningConversationViewV1` / `LearningMessageV1` / `MessageBlockV1` 是 ADR-0020 / `LCMS-*` 冻结的 SYS08 presentation/transcript projection/artifact：

- Conversation view only owns scope/order/cursor/availability；
- Message owns accepted learner-visible content/blocks/exact refs；
- capability descriptor owns no business result and is revalidated by target owner；
- Message/Block MUST NOT become LearningActivity、Attempt、AssessmentResult、LearnerEvidence、MasteryEstimate、TeachingAction、ReviewSchedule or LearningSession truth；
- presented/opened/copy/hover/turn count are not LearningEvidence；
- frontend invocation success requires owner receipt/re-query and MUST NOT persist as second owner truth。

#### STATE-230 — Misconception Four-way Ownership

`Misconception definition → SYS01`；`MisconceptionEvidence → SYS04`；`MisconceptionHypothesis → SYS03`；`Remediation decision → SYS05`。MUST NOT 合并为跨系统可写对象。

### 9. Ownership Sweep

#### STATE-240

新增公共对象必须明确：state/derived/control/measurement/ledger 分类、唯一 writer、workspace scope、read/execute roles、duplicate-truth risk、replay exact version source。

#### STATE-241

Architecture tests MUST 证明不存在第二 LearnerState、第二 TeachingAction、第二 Experiment truth、第二 Outcome truth、第二 LocalOwner 或跨 Workspace 混写。

#### STATE-250 — Legacy Compatibility

Legacy dialog mastery、Socratic selector/state graph、old policy config、integer support/exposure MAY 暂作 read projection/adapter/audit，必须有 canonical source 与 retirement condition，MUST NOT permanent dual-write。

### 10. Acceptance Criteria

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

### 11. Forbidden Implementations

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

### 12. P1-06 Onboarding Presentation Boundary

#### STATE-300 — OnboardingPreferenceV1

`OnboardingPreferenceV1` 是 Platform Experience Preference 拥有的 presentation-only state，只可保存 journey/version、active/dismissed、boundary notice acknowledgment 与 dismiss metadata。它 MUST NOT 保存 step completion 或 model/material/goal/plan/activity/transcript/recovery truth/ref 副本。

其 owner key canonical semantics MUST 是 LocalOwner；历史 `user_id` 列 MAY 作为迁移兼容字段存在。

#### STATE-301 — Onboarding Read Projection

`OnboardingJourneyViewV1` 和 SYS06 `FirstActivityCompletionProjectionV1` 均为只读投影。Query hosting、API serialization 或 UI presentation MUST NOT 取得 SYS01～SYS08 写入权；投影失效只能重查 owner，不得回写或修补 owner state。

#### STATE-310 — UI Workspace Read Projections

`WorkspaceContextResponseV1` 与 `LearningContextResponseV1` 是 ADR-0019 冻结的只读 UI 聚合投影：

- Workspace identity/name/version 只读 Platform Workspace Registry；
- Drawer stage 只读 exact SYS05 TeachingAction；
- Drawer next directions 只读 ordered exact SYS06 LearningActivity；
- stage-goal presentation catalog 必须版本化，且不得成为 LearningGoal、LearningObjective、TeachingStage mapper 或 TeachingAction 的 writer/truth；
- query assembler 只拥有 composition/serialization，不拥有任何被读取状态。

任何 frontend cache、route、chat text、LLM output 或 read-model row MUST NOT 成为第二 Workspace/Stage/Plan truth。

ADR-0023 supersedes the single-default target limitation：current Workspace now reads versioned `WorkspaceSelection` from Platform Workspace Registry；`Workspace.is_default` remains migration/fallback metadata。The additive Course Activity index only composes exact SYS06 Activity definition/latest lifecycle refs and owns no Activity state。

#### STATE-311 — WorkspaceSelection

`WorkspaceSelection` is durable, owner-scoped, monotonic-version Platform preference。Only Platform Workspace Registry may create/update it；route、browser storage、Workspace default marker、LearningSession、Activity、query assembler and LLM are read-only consumers。Create/switch receipts are idempotency records, not a second current-state writer。

#### STATE-AC-310

Architecture/contract tests MUST 证明两个 projection 无 write path、无新持久化表、无 frontend inference，并保留 exact owner source refs。

#### STATE-AC-311

Architecture/contract tests MUST prove current selection has one Platform writer；default marker/browser/route cannot mutate it；Course Activity projection is read-only and exact SYS06-derived。

#### STATE-AC-300

Architecture tests MUST 证明 onboarding 只有 presentation preference writer，且 activity completion 仍只由 SYS06 lifecycle transition 产生。

---

## Askora Dependency Rules

> Spec ID 范围：`DEP-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.3 + v1 Product Positioning Alignment  
> 上位约束：`docs/product/PRODUCT-POSITIONING.md`

### 1. Purpose

本规范定义各系统允许的依赖方向、跨边界调用方式以及 legacy 迁移限制。违反本文件的实现必须先通过 Product Positioning / Design / ADR / Spec 治理，MUST NOT 由执行代理在产品代码中临场或隐式重定义架构。

### 2. Core Dependency Rules

#### DEP-001 — No Cross-owner ORM Writes

领域模块 MUST NOT 通过 ORM/repository 直接写其他领域状态。跨领域变更只能通过 public command、append-only event/evidence、read-only query 或 owner application service。

#### DEP-002 — One Public Schema

`LearningEvent`、`AssessmentResult`、`MasteryEstimate`、`TeachingContext`、`TeachingAction`、`PolicyBundle`、`LearningPlan`、`ReviewSchedule`、`EvidenceBundle`、`OutcomeObservation`、`ExperimentAssignment` 等跨系统对象 MUST 有唯一 canonical contract；MUST NOT 复制长期本地副本作为第二协议。

LocalOwner / Workspace / Material / LearningProject 等 platform/product objects 同样 MUST 有唯一公共语义。

#### DEP-003 — Domain / Infrastructure Separation

Domain logic MUST NOT 依赖 FastAPI transport、browser runtime、Redis/Kafka client、具体 model SDK、OS secret API 或隐式 global SQLAlchemy Session；这些能力 SHOULD 通过 port/adapter 注入。

Electron/Desktop 不属于 v1 Canonical Runtime，新 domain code MUST NOT 依赖 Electron IPC/safeStorage。

#### DEP-004 — API Is a Local Transport Adapter

API 只负责 loopback transport validation、LocalOwnerContext resolution、command/query、HTTP/WebSocket/streaming mapping 与 error mapping；MUST NOT 持有 mastery、Teaching Policy、assessment、plan、review 算法。

v1 API MUST NOT 以 Account/JWT/AuthSession 作为业务 owner resolution。网络安全边界由 loopback/origin + LocalOwnerContext 共同承担。

#### DEP-005 — SYS08 Executes, Does Not Own SYS01～SYS07 Rules

SYS08 MAY 决定 workflow/retry/model/tool route，但 MUST NOT 复制/覆盖领域规则。例如 support/hint transition 属 SYS05、evidence eligibility 属 SYS03、next_due 属 SYS07；SYS08 只能在 TeachingAction envelope 内执行并 MAY 收紧、MUST NOT 扩大。

#### DEP-006 — Sync Query, Explicit Feedback

读取 snapshot MAY 同步；跨系统产生新 state SHOULD 通过 command/event 形成新版本。MUST NOT 用一个巨大 service method 在单调用栈修改所有系统表。

#### DEP-007 — Platform Scope Before Learning Domain

learner-owned command/query 进入 Learning Core 前 MUST 已解析：

```text
LocalOwnerContext
→ WorkspaceContext (when object is workspace-scoped)
→ owner application/domain service
```

平台 scope resolution 不得越权修改领域状态。

#### DEP-008 — Workspace Scope Is a Hard Filter

Workspace scope MUST 在 search/retrieval、material access、goal/session access、learner projection query 与 background rebuild task 中先于 soft ranking/LLM logic 生效。

跨 Workspace 数据不得因为“同一 LocalOwner”而自动可见或自动融合。

### 3. Allowed Logical Dependency Matrix

符号：`Q` read-only query；`C` public command；`E` event；`X` execute decided action；`-` no direct business dependency。

| From \ To | SYS01 | SYS02 | SYS03 | SYS04 | SYS05 | SYS06 | SYS07 | SYS08 |
|---|---|---|---|---|---|---|---|---|
| SYS01 | - | E/Q | E/Q | E/Q | - | E/Q | - | E |
| SYS02 | Q | - | - | Q | E | - | - | E/X |
| SYS03 | Q | - | - | Q | E/Q | E/Q | E/Q | E |
| SYS04 | Q | Q | Q/E | - | E | - | E | C/E |
| SYS05 | Q | C | Q | Q | - | Q | Q | C |
| SYS06 | Q | - | Q | - | E | - | Q | C/E |
| SYS07 | - | - | Q/E | Q | E | E | - | E |
| SYS08 | Q | C | E | C | C | C | C | - |

矩阵表示 logical collaboration，不授权 import 对方内部 implementation 或越权写入。

LocalOwner/Workspace/Product Organization 属 platform boundary，不进入八系统矩阵。Learning Core MAY 只读其 exact scope refs；不得回写 Workspace membership。

### 4. Package / Transaction Rules

```text
contracts  ← domains can depend
    ↑
domains/*  ← own domain + contracts + ports
    ↑
application/orchestration ← public application ports/contracts
    ↑
api/local_workers ← application facade

platform/* → identity/workspace/jobs/backup/config lifecycle
infrastructure → implements ports (SQLite/files/index/secret/provider)
```

#### DEP-020

`domains/<A>/` MUST NOT import `domains/<B>/internal_*`、repository implementation 或 ORM model。

#### DEP-021

跨 domain 只允许依赖 public contract/query/command/event schema。

#### DEP-022

Infrastructure MAY 依赖 SQLite driver、file APIs、index libraries、model SDK；domain MUST NOT 反向依赖 infrastructure implementation。

Redis/PostgreSQL MAY 存在于开发/CI adapter，但 production-local domain semantics MUST NOT 假设它们存在。

#### DEP-023

API MUST NOT 直接调用 repository；LocalOwner/Workspace resolver 是 transport/application prerequisite，不是 repository bypass 许可。

#### DEP-024 — Browser Is Presentation, Not State Owner

Browser/localStorage/sessionStorage MAY 保存短期 UI preference/cache，但 MUST NOT 成为 LocalOwner、Workspace、Material membership、LearningGoal、LearnerState、TeachingAction、ModelRouteProfile、API Key 或 background job truth。

Current Workspace selection is specifically a Platform Workspace Registry preference governed by `CWSP-*`。Browser MAY preserve per-Workspace draft/tab position for recovery, but MUST NOT claim switch success before the owner command receipt。

#### DEP-025 — Workspace Selection Before Scoped Command

Application startup MAY read canonical WorkspaceSelection；explicit deep links MAY supply a validated Workspace scope without mutating selection。Every workspace-scoped write still carries/resolves exact route/body scope and MUST NOT depend only on ambient current selection。Course Activity query may read SYS06 exact refs；it MUST NOT import/write SYS06 private persistence as a second owner。

#### DEP-030 — Single-owner Transaction

一个 domain transaction SHOULD 只修改该 owner 的业务状态，并写同一事务的 outbox/event record。

#### DEP-031 — Transactional Outbox

关键跨系统事件 MUST 与 owner state update 可靠写入 outbox/等价本地 durable mechanism。

#### DEP-032 — At-least-once Consumers

Consumers MUST 假设 at-least-once delivery，因此必须 idempotent。

#### DEP-033 — No Default 2PC

采用 local transaction → outbox → idempotent consumer/projection → eventual convergence；MUST NOT 为 v1 默认引入 2PC/distributed transaction。

#### DEP-034 — Local Job Runtime

Background jobs MUST 通过 Platform Job Runtime 读取持久化 job state，并调用对应 owner application service。Worker MAY 与 Local Server 同进程或受控子进程运行，但 MUST NOT 要求 Redis/Celery/Kafka 等独立服务才能保证正确性。

### 5. Legacy Governance

#### DEP-040

现有 `services/*`、`engines/*` MAY 在迁移期保留，但新增能力 SHOULD 朝 canonical owner/adapter 边界收敛；legacy path MUST NOT 扩大越权。

#### DEP-041 — Socratic Split Direction

Legacy Socratic 的教学动作选择逻辑最终归 SYS05；语言生成/表达/guardrail execution 归 SYS08。`strategy_selector.py` / state graph MUST NOT 成为 final TeachingAction owner，迁移期 MAY bounded InteractionMove provider/adapter/stage-definition source/execution component。

#### DEP-042 — Documents Split Direction

`services/documents/` 中 parser/model/provenance → SYS01；retrieval/ranking/EvidenceBundle → SYS02；storage → infrastructure；security scan → trust/security adapter，不得改变知识业务语义。

Material/SourceFile/Workspace membership 必须按最新 Domain/Workspace contract 分离，旧 `Document.user_id` 不能继续充当全局资料 scope。

#### DEP-043 — KT/DKT

SYS03 MUST 只有一个 canonical state projector。DKT/Deep KT MAY challenger/auxiliary predictor，MUST NOT 独立持有 learner truth。

#### DEP-044 — Desktop/Auth/Distributed Infrastructure Retirement

Electron main/preload、desktop vault、JWT/AuthSession、Redis-required worker、PostgreSQL-required runtime MAY 作为 legacy implementation 存在于迁移期；新 canonical code MUST NOT 依赖它们。每条 compatibility path 必须有 target owner 与 retirement condition。

### 6. Prohibited Dependencies

#### DEP-050

SYS04 Assessment MUST NOT 调用 SYS03 repository 直接更新 mastery。

#### DEP-051

SYS08 Orchestrator/LLM MUST NOT 调用 SYS03/SYS05/SYS06/SYS07 repository 直接更新 canonical state/action。

#### DEP-052

SYS06 Planner MUST NOT 调用 SYS05 private implementation 决定 hint/explanation/TeachingAction。

#### DEP-053

SYS02 Retrieval MUST NOT 调用 SYS03 write interface，也不得生成长期 LearnerState 副本。

#### DEP-054

SYS07 Review MUST NOT 修改 LearningPlan；它只能发布 due/risk，SYS06 决定是否进入实际计划。

#### DEP-055

任一 domain MUST NOT 从聊天文本解析结果直接更新关键业务状态；必须先形成对应 command/evidence/result。

#### DEP-056

任何 domain MUST NOT 绕过 WorkspaceContext 执行 cross-workspace query/retrieval，因为 owner_id 相同并不等于 workspace scope 相同。

#### DEP-057

LLM/provider adapter MUST NOT 直接写 SQLite、Workspace membership、LearningEvidence、LearnerState、Goal、Plan 或 TeachingAction；structured output 必须经过 schema/application/domain rules。

### 7. Adaptive Teaching Dependencies

#### DEP-200 — TeachingContext Assembly

SYS05 MAY 读取 SYS03/SYS04/SYS06/SYS07 exact versioned refs 与用户请求/experiment refs 构造 TeachingContext；MUST NOT 将 source snapshots 变成 SYS05 可写副本。

TeachingContext 所引用的 workspace-scoped facts MUST 属于同一 Workspace，除非未来显式合同允许跨 Workspace。

#### DEP-201 — Policy Execution Boundary

```text
SYS05 TeachingAction
→ SYS02 evidence supply (tighten only)
→ SYS08 execution (tighten only)
→ SYS04 actual assistance/Attempt/AssessmentResult
→ SYS03 evidence/state update
→ new material evidence
→ SYS05 next decision
```

任何环节需要改变 StrategyFamily/InteractionMove/envelope semantics 时 MUST 回到 SYS05 创建新 TeachingAction。

#### DEP-202 — Validation Obligation

SYS05 owns validation obligation；SYS04 creates fresh independent evidence；SYS03 evaluates evidence eligibility。SYS03/SYS08 MUST NOT clear/complete obligation without fresh evidence。

#### DEP-203 — Decision / Outcome

DecisionTrace payload 由 decision owner 定义并 MAY 由 SYS08 ledger 托管；OutcomeObservation/ExperimentAssignment MAY 由 analytics ledger 托管，但 MUST NOT 回写 DecisionTrace 或取得 TeachingAction/LearnerState ownership。

#### DEP-204 — No Legacy Dual Truth

旧 strategy enum、integer scaffold/hint/exposure、old policy config/propensity MAY read-only compatibility/audit；MUST NOT 与 v0.3 canonical fields permanent dual-write。

#### DEP-205 — Hard-rule / Envelope Integrity

SYS02/SYS08 MUST NOT expand TeachingAction envelope；experiment layer MUST NOT restore hard-filtered action；LLM/legacy adapters MUST NOT bypass SYS05 hard constraints。

#### DEP-206 — Local Model Configuration Adapter

Browser Settings MAY 通过 loopback API 提交一次性 candidate provider/model/API Key。API/application layer MUST 把 secret 交给 local SecretStore adapter、把 routing metadata 交给 SYS08 `ModelRouteProfile` owner；Browser MUST NOT 读取已保存 Key。

SecretStore MAY 使用 OS-backed credential storage；domain/SYS08 routing logic MUST NOT 依赖具体 OS API。Development/test environment variables MAY 作为非生产 compatibility input，但不得成为 production Local 的第二配置 truth或在 clear 后静默复活配置。

### 8. Architecture Tests

代码库 SHOULD 验证：

- domains 不 import api/infrastructure implementation；
- cross-owner writes 不可达；
- SYS04 no SYS03 persistence write；
- SYS08 no mastery/plan/review/action write；
- SYS02/SYS08 tightening-only；
- legacy Socratic no final owner；
- Outcome/Experiment ledger hosting no domain takeover；
- LocalOwner/Workspace scope 无第二 writer；
- production retrieval 无 cross-workspace leak；
- browser 无 persistent secret truth；
- Local Server 不依赖 Redis/PostgreSQL/Docker 才能启动；
- local job restart/duplicate execution 仍幂等。

### 9. Acceptance Criteria

- `DEP-AC-201`：TeachingContext assembly 只读 exact owner refs。
- `DEP-AC-202`：SYS02/SYS08 无扩大 scaffold/hint/exposure 路径。
- `DEP-AC-203`：validation obligation 由 SYS05 policy-control 管理，并由 fresh SYS04 evidence 满足。
- `DEP-AC-204`：legacy Socratic 无 final TeachingAction ownership。
- `DEP-AC-205`：无 legacy/v0.3 permanent dual truth。
- `DEP-AC-206`：existing `DEP-050..057` prohibited dependencies 可由 architecture tests 强制。
- `DEP-AC-207`：browser/普通 API 无持久化 secret truth；SecretStore 与 SYS08 profile owner 分离。
- `DEP-AC-208`：learner-owned request 解析 LocalOwnerContext；workspace-scoped request 解析 WorkspaceContext。
- `DEP-AC-209`：SYS02/cache/background rebuild 默认严格 workspace scoped。
- `DEP-AC-210`：production-local dependency graph 不要求 Redis/PostgreSQL/Docker/Kafka/Electron。

### 10. Forbidden Implementations

禁止 cross-owner repository writes；SYS08/LLM direct canonical writes；SYS06 private-policy dependency；SYS02 learner-state writer；SYS07 plan writer；chat-text direct state update；SYS02/SYS08 envelope expansion；experiment hard-rule restoration；browser 获取已保存明文模型密钥；公网/普通 API 暴露 secret；permanent legacy dual truth；Workspace 被当作 Tenant；owner_id 代替 workspace filter；production-local worker 必须依赖 Redis/Kafka；Electron IPC 成为 v1 model configuration requirement。

### 11. P1-06 Onboarding Dependencies

#### DEP-300 — Read-only Composition

Onboarding query MAY 读取 Platform Experience Preference、public model summary、SYS01 material eligibility、SYS06 Goal/Activity projections、Data Control capability route 与 RecoveryAction。它 MUST NOT import 或调用这些 owner 的 private repository/write implementation。

#### DEP-301 — Command Direction

Onboarding preference command 只能写 presentation preference。模型、资料、Goal、diagnostic、plan、activity 和 recovery side effect 必须继续通过对应现有页面/application command；Onboarding 不得提供跨 owner generic command router。

#### DEP-302 — Completion Source

First activity completion dependency 固定为 SYS06 exact lifecycle state + accepted transcript completion source。message/model result/UI state → onboarding completion 的直接依赖 MUST 由 architecture tests 禁止。
