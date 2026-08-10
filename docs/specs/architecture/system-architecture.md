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
