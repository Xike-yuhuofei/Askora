# Askora Implementation Specifications

> 状态：Canonical Implementation Contract Index  
> 当前版本：v0.3 Adaptive Teaching Loop Frozen / Implemented Baseline + Book-to-Learning Bootstrap Frozen / Implemented Baseline

## 1. Purpose

`docs/specs/**` 将已冻结 Canonical Design 与 Accepted ADR 转换为可直接约束实现、测试、迁移、replay 与 release 的合同。

v0.3 authoritative formation chain：

```text
Research Synthesis
→ Canonical Design
→ Accepted ADR-0001 / ADR-0002
→ Updated v0.3 Specs
→ v0.3 Vertical Slice
→ EXEC-007+
→ Implementation
```

Book-to-Learning Bootstrap formation chain：

```text
Canonical Design + v0.3 implemented baseline + UI-02A implemented baseline
→ Gap Analysis
→ SPEC-D01～D06
→ Spec Freeze
→ EXEC-017～024
→ Implemented Baseline
```

当前 Book-to-Learning 状态：**SPEC FROZEN / IMPLEMENTED BASELINE**。EXEC-017～024 已完成并归档；Engineering/Contract 与 Policy/Ownership Gate PASS，Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。实现证据见 [Book-to-Adaptive-Learning Completion Report](../releases/book-to-adaptive-learning.md)。

实现必须服从 updated Spec + frozen Vertical Slice；发现 Vertical Slice / Spec 与 Accepted ADR/Canonical Design 冲突时，MUST 先做 SPEC GAP/upstream conflict closure，MUST NOT 让代码或旧 Spec 反向修改 ADR 语义。用户已委托架构自治时，Codex MAY 代表该目标接受新的 superseding/additive ADR，并在同步更新 Spec/EXEC 后继续实现；不得用代码事实反向追认设计。

## 2. Spec Index

### Domain

- [Domain Model](domain/domain-model.md) — canonical objects、ontology、TeachingContext、PolicyBundle、Outcome/Experiment、migration
- [Decision Contract](domain/decision-contract.md) — DecisionTrace v0.3、probability、replay
- [Event Contract](domain/event-contract.md) — LearningEvent、assistance/outcome/experiment event semantics
- [Lifecycle State Machines](domain/lifecycle-state-machines.md) — lifecycle contracts

### Architecture

- [State Ownership](architecture/state-ownership.md) — SYS01～SYS08 single-writer ownership
- [System Architecture](architecture/system-architecture.md)
- [Dependency Rules](architecture/dependency-rules.md)

### Systems

- [SYS01 Content & Knowledge](systems/01-content-knowledge.md)
- [SYS01 Library Management, Deduplication and OCR](systems/01-library-management.md) — P1-04 metadata/search/organization/dedup/OCR additive contract
- [SYS02 Retrieval](systems/02-retrieval.md)
- [SYS03 Learner Model](systems/03-learner-model.md)
- [SYS04 Assessment](systems/04-assessment.md)
- [SYS05 Teaching Policy](systems/05-teaching-policy.md)
- [SYS06 Learning Planner](systems/06-learning-planner.md)
- [SYS06 Goal Management](systems/06-goal-management.md) — versioned definition/state/draft/replan 与 evidence-gated achievement
- [SYS06 Activity Lifecycle and Completion](systems/06-activity-lifecycle.md) — versioned start/resume/completion 与 next-activity progression
- [SYS07 Review Scheduler](systems/07-review-scheduler.md)
- [SYS08 AI Orchestration](systems/08-ai-orchestration.md)

### Interfaces

- [API Contract](interfaces/api-contract.md)
- [Error Contract](interfaces/error-contract.md)
- [Persistence Contract](interfaces/persistence-contract.md)
- [Data Control and Recovery](interfaces/data-control-contract.md) — P1-03 加密恢复、导出与 owner 协调删除合同
- [First-use Onboarding Contract](interfaces/onboarding-contract.md) — P1-06 presentation preference、owner-fact readiness、single next action 与 deep-link contract
- [Rich Response Rendering](interfaces/render-content-contract.md) — RenderPayloadV1、Markdown/math/cards/citations、安全降级
- [Schema Versioning](interfaces/schema-versioning.md)

### Quality

- [Testing Standard](quality/testing-standard.md) — L0～L6 + OPVE/G0/G1/G2
- [Observability Standard](quality/observability-standard.md) — decision/outcome observability + learning outcome hierarchy
- [Definition of Done](quality/definition-of-done.md) — Engineering/Policy/Learning Evidence release gates
- [Security Standard](quality/security-standard.md) — hard-rule / answer-exposure / grader-only security boundary

### Vertical Slices

- [P1-03 Data Control and Recovery](vertical-slices/p1-03-data-control-recovery.md) — macOS 私人桌面备份、恢复、导出与删除闭环；EXEC-1031～1034
- [P1-01B Goal Lifecycle and Evidence-gated Achievement](vertical-slices/p1-01b-goal-lifecycle-achievement.md) — pause/resume/archive/copy/measurement/achievement；EXEC-038 frozen
- [P1-01A Goal Definition, Draft and Safe Replan](vertical-slices/p1-01a-goal-definition-draft-replan.md) — multi-source/explicit target/preview/boundary apply；EXEC-037 DONE
- [P1-06 Fact-driven First-use Onboarding](vertical-slices/p1-06-first-use-onboarding.md) — 首次 model→material→goal→activity→Today 可恢复闭环；EXEC-1061～1062 frozen
- [P1-04C Scanned PDF OCR Review](vertical-slices/p1-04c-library-ocr-review.md) — local OCR candidate/review/publish；EXEC-033 已完成
- [P1-04B Library Deduplication](vertical-slices/p1-04b-library-deduplication.md) — evidence-bound duplicate suggestions；EXEC-032 已完成
- [P1-04A Library Search and Organization](vertical-slices/p1-04a-library-organization.md) — search/metadata/tag/collection/batch/archive；EXEC-031 已完成
- [UI-02C Canonical Activity Lifecycle](vertical-slices/ui-02c-canonical-activity-lifecycle.md) — start/resume/complete/next 闭环；EXEC-030 已完成
- [UI-02B Goals, Learning Path and Evidence](vertical-slices/ui-02b-goals-path-evidence.md) — Goals/Path/Evidence 只读产品闭环；EXEC-029 已完成
- [UI-02B3 Real-model Guided Learning](vertical-slices/ui-02b3-real-model-guided-learning.md) — production configured-model rendering 与真实浏览器/DB E2E；EXEC-027 已完成
- [UI-02B2 Guided Book Learning](vertical-slices/ui-02b2-guided-book-learning.md) — 系统自动准备→第一节可恢复 canonical 教学；EXEC-026 已完成
- [UI-02B1 Material-to-Learning Launch](vertical-slices/ui-02b1-material-learning-launch.md) — 单份资料→Goal→诊断→计划→canonical 教学启动；EXEC-025 已完成
- [UI-02A Canonical Library and Scoped Knowledge Map](vertical-slices/ui-02a-library-knowledge-map.md) — frozen library slice；EXEC-016 已完成
- [UI-01 Learning Shell and Compatibility Tutor Workspace](vertical-slices/ui-01-learning-shell-workspace.md) — frozen UI implementation slice；EXEC-015 已完成
- [v0.3.1 Rich Response Rendering](vertical-slices/v0.3.1-rich-response-rendering.md) — additive presentation slice；EXEC-014 已完成
- [v0.3 Adaptive Teaching Loop](vertical-slices/v0.3-adaptive-teaching-loop.md) — **current frozen v0.3 implementation slice**；EXEC-007～013 已按此完成
- [v0.2 Learning Loop](vertical-slices/v0.2-learning-loop.md) — historical v0.2 slice；与 v0.3 ontology/support/probability contracts 冲突时由 v0.3 canonical specs supersede

### Book-to-Learning Bootstrap（Frozen / Implemented Baseline）

- [SPEC-D01 Content Ingestion & Source Locator](interfaces/content-ingestion-contract.md) — structure-preserving ingestion、DocumentIR/DocumentNode、source locator/replay
- [SPEC-D02 Multi-Granularity Content Model](systems/01-content-granularity.md) — EvidenceSpan/SemanticUnit/RetrievalChunk/HierarchyNode 边界
- [SPEC-D03 Knowledge Candidate Verification & Publish](systems/01-knowledge-publish-pipeline.md) — candidate→verify→publish、hard prerequisite gate
- [SPEC-D04 LearningGoal → Knowledge Mapping](systems/06-goal-knowledge-mapping.md) — natural-language goal、target KU mapping、goal subgraph
- [SPEC-D05 Prerequisite Diagnostic Bootstrap](systems/06-prerequisite-diagnostic-bootstrap.md) — SYS06/SYS04/SYS03 diagnostic bootstrap 边界
- [SPEC-D06 Book-to-Adaptive-Learning Vertical Slice](vertical-slices/book-to-adaptive-learning.md) — EPUB upload → first/next canonical TeachingAction E2E

### UI Experience（Frozen）

- [UI Redesign Spec Index](ui/README.md) — 学习闭环优先的 UI 重设计 Canonical Contract
- [Information Architecture](ui/information-architecture.md) — 导航、路由、页面层级与响应式信息架构
- [Screen Contracts](ui/screen-contracts.md) — 页面状态、内容优先级、交互边界与验收条件
- [Data Contracts](ui/data-contracts.md) — 只读 Query/API、来源标记与系统所有权边界
- [Visual System](ui/visual-system.md) — macOS-first 视觉语言、tokens、组件与无障碍约束
- [Quality and Migration](ui/quality-and-migration.md) — 三阶段执行、测试门禁、迁移与延后决策登记

## 3. v0.3 Canonical Decisions → ADR → Spec Traceability

| Canonical Decision | ADR | Canonical Spec Requirements |
|---|---|---|
| `V03-CD-002` six Strategy Families | ADR-0001 | `DOMAIN-083/086`, `SYS05-201` |
| `V03-CD-003` four-layer ontology | ADR-0001 | `DOMAIN-083..085`, `SYS05-202/203` |
| `V03-CD-005` TeachingContext | ADR-0002 | `DOMAIN-088`, `SYS05-210..212` |
| `V03-CD-006` ErrorType | — | `DOMAIN-072..074`, `SYS04-220..224` |
| `V03-CD-007` hard/soft/experiment | ADR-0002 | `SYS05-240..242`, `DECISION-240` |
| `V03-CD-008` support/exposure | ADR-0001 | `DOMAIN-061..063`, `SYS05-220/221`, `SYS04-210/211` |
| `V03-CD-009` validation obligation | — | `DOMAIN-091`, `SYS05-222`, `SYS03-230/231`, `SYS04-230..232` |
| `V03-CD-010` deterministic policy | ADR-0002 | `SYS05-230/231`, `SYS05-290/291`, `DECISION-210` |
| `V03-CD-011` anti-oscillation | ADR-0002 | `SYS05-280..285`, `TEST-240..242` |
| `V03-CD-012` PolicyBundle | ADR-0002 | `DOMAIN-089`, `SYS05-300..303` |
| `V03-CD-013` DecisionTrace probability/replay | ADR-0002 | `DECISION-200..222`, `SYS05-310..312` |
| `V03-CD-014` Outcome data model | — | `DOMAIN-111..113`, `OBS-200..221` |
| `V03-CD-015` OPVE / outcome hierarchy | — | `TEST-200..281`, `OBS-210..213` |
| `V03-CD-017` release gate | — | `DOD-200..260` |

## 4. SD-01～SD-11 Resolution Matrix

| SD | Status | Primary Specs |
|---|---|---|
| SD-01 Strategy Ontology | RESOLVED | domain-model, SYS05 |
| SD-02 TeachingContext | RESOLVED | domain-model, SYS05, DecisionTrace |
| SD-03 Assessment | RESOLVED | domain-model, SYS04 |
| SD-04 Error Diagnosis | RESOLVED | domain-model, SYS04, SYS03/SYS05 boundary |
| SD-05 Support/Hint/Exposure/Assistance | RESOLVED | domain-model, SYS02/03/04/05/08, events |
| SD-06 Anti-Oscillation | RESOLVED | SYS05, testing |
| SD-07 PolicyBundle / Policy Stack | RESOLVED | domain-model, SYS05 |
| SD-08 DecisionTrace v0.3 | RESOLVED | decision-contract, SYS05 |
| SD-09 Outcome / Experiment | RESOLVED | domain-model, event, ownership, observability |
| SD-10 Testing / OPVE | RESOLVED | testing-standard |
| SD-11 Observability / DoD / Release Gate | RESOLVED | observability-standard, definition-of-done |

## 5. Breaking Change Register — Spec Resolution

| BC | Resolution |
|---|---|
| BC-001 Strategy enum | six StrategyFamily is only v0.3 canonical top-level enum; old nine values read-only/audit |
| BC-002 TeachingAction semantics | immutable four-layer action contract + exact context/bundle pinning |
| BC-003 Support / exposure | canonical orthogonal scaffold/hint/exposure/assistance model |
| BC-004 Policy configuration | immutable/versioned PolicyBundle; no executable/free-form rules |
| BC-005 DecisionTrace probability / replay | deterministic `action_propensity=null`; assignment probability separated; explicit replayability |
| BC-006 Legacy Socratic selector | bounded InteractionMove provider/legacy adapter only; SYS05 owns final TeachingAction |

All six are **RESOLVED IN SPEC**。Implementation migration MUST follow `vertical-slices/v0.3-adaptive-teaching-loop.md`。

## 6. Migration Candidate Register — Contract Resolution

| Candidate | Canonical target | Compatibility read | Classification / ambiguity | Replayability | Retirement condition |
|---|---|---|---|---|---|
| historical strategy records | six StrategyFamily | legacy audit allowed | ambiguous mapping must be explicit | FULL/PARTIAL by refs | supported history migrated/archived |
| historical TeachingAction | v0.3 immutable action | read adapter | non-lossless semantics marked | usually PARTIAL when fields absent | no active v0.2 workflow |
| old `scaffold_level` | `scaffold_control` | read adapter | lossy/unknown marked | PARTIAL if inference required | no active writer + migrated history |
| old `hint_level` | `hint_specificity` | read adapter | lossy/unknown marked | PARTIAL if inference required | no active writer + migrated history |
| old answer exposure scale | `answer_exposure` | read adapter | lossy mapping marked | PARTIAL if inference required | no active writer + migrated history |
| legacy Socratic selector/state machine | bounded InteractionMove provider/legacy adapter | bounded compatibility | never final owner | replay only behind fixed SYS05 contract | canonical path covers supported flows |
| old policy config | immutable PolicyBundle | audit/import only | executable config never executed | exact bundle required for FULL | migrated/retired configs |
| old DecisionTrace propensity | separated assignment/action probability | raw audit allowed | ambiguous → null/unknown + reason | PARTIAL | historical migrator complete |
| historical replay | exact historical refs | best effort | missing versions never guessed | FULL/PARTIAL/NON_REPLAYABLE | explicit status retained |

All nine migration candidates have canonical target、compatibility read、ambiguity、replayability 与 retirement semantics。Permanent dual truth is forbidden。

## 7. Spec-ID Governance

Existing requirement IDs MUST NOT be reused to change meaning. Superseded v0.2 IDs remain visible in each affected Spec's superseded/legacy register; v0.3 additions use new unused ranges (principally `*-2xx/3xx`)。v0.3 Vertical Slice 使用 `VSLICE-3xx`。

`SPEC-D01～D06` 是 Book-to-Learning additive contract pack；内部要求使用 `D01-*`～`D06-*`，不得复用现有 SYS/DOMAIN/ADR requirement ID 改变原语义。

## 8. v0.3 Canonical Invariants

```text
Knowledge truth / relations     → SYS01
EvidenceBundle                  → SYS02
LearnerState / MasteryEstimate  → SYS03
AssessmentResult                → SYS04
TeachingAction                  → SYS05
LearningPlan / Activity         → SYS06
ReviewSchedule / next_due       → SYS07
Model / Tool execution          → SYS08
```

And:

```text
TeachingStage != LearnerState
DecisionTrace != OutcomeObservation
Experiment assignment probability != action selection propensity
SYS08/SYS02 may tighten but may not expand TeachingAction envelope
LLM/Agent never owns final TeachingAction or canonical learner/assessment/plan/review truth
```

Book-to-Learning additionally freezes：

```text
SourceChunk != KnowledgeUnit
GoalSpecificKnowledgeSubgraph != KnowledgeGraph truth
DiagnosticNeed != LearnerState
Book bootstrap != second Teaching Loop
```

## 9. Versioned Parameters

mastery threshold、failure ceiling、minimum dwell、switch margin、hint sequence、scaffold fade amount、diagnostic confidence cutoff、transfer novelty threshold、delay windows、policy weights、practical harm margin MUST remain versioned/traceable configurable parameters. No Spec may claim arbitrary fixed values are universal learning-science constants.

Book-to-Learning 的 extraction/publication/mapping/diagnostic thresholds 与 budgets 同样 MUST versioned；不得写成普适常数。

## 10. v0.3 Out of Scope

Contextual Bandit、Offline RL、Online RL、Deep KT canonical truth、complex IRT-CAT、open-world misconception discovery、school-level population A/B、multi-agent teaching control、automatic learned reward、synthetic learner as learning evidence、free-form LLM TeachingAction ownership、generic Productive Failure strategy、always-on Socratic tutor、generic executable policy DSL。

B2 LLM selector MAY only be experiment baseline behind the same hard shield/action vocabulary.

## 11. Vertical Slice Gate

v0.3 Vertical Slice is frozen when：

```text
Scope is narrow and end-to-end
No new Canonical Design decision introduced
No ADR conflict
No Spec conflict
All six breaking changes have implementation path
All nine migration candidates have executable verification path
Single-writer ownership remains intact
Engineering / Policy / Learning Evidence claims remain separated
```

Vertical Slice Gate：**PASS**。EXEC-007～013 已完成并归档；当前实现证据见 [v0.3 Release Report](../releases/v0.3-adaptive-teaching-loop.md)。

## 12. Book-to-Learning Spec Freeze

| Spec | Status | Primary Boundary |
|---|---|---|
| SPEC-D01 | FROZEN | structure-preserving ingestion / source replay |
| SPEC-D02 | FROZEN | multi-granularity content model |
| SPEC-D03 | FROZEN | knowledge verification / publication |
| SPEC-D04 | FROZEN | LearningGoal → Knowledge mapping |
| SPEC-D05 | FROZEN | prerequisite diagnostic bootstrap |
| SPEC-D06 | FROZEN | Book-to-Adaptive-Learning E2E slice |

Consistency check：

```text
Accepted ADR conflict                     PASS
Canonical Design conflict                 PASS
UI-02A baseline compatibility             PASS
v0.3 Teaching Loop compatibility          PASS
SYS01～SYS08 single-writer ownership       PASS
Second truth / second Teaching Loop       NONE
New learning efficacy claim               NONE
EXEC number pre-allocation                NONE
```

**Book-to-Learning Spec Freeze Gate：PASS**。

Implementation Gate：**PASS**（EXEC-017～024）。这不改变 Spec 的 Frozen 状态，也不构成真人学习效果结论。

后续变化仍只能先生成新的 EXEC Plan 再实现。未获用户架构自治委托时，Codex 不得从
D01～D06 自行扩大范围；已获委托时，Codex MAY 先接受所需 ADR、更新并冻结新增 Spec/
Vertical Slice/EXEC，再在新边界内实现，且不得静默改写 D01～D06 的历史冻结语义。
