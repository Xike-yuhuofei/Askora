# Askora 决策索引（Decision Log）

> 状态：**Index — 决策索引，不是现行合同**
> 定位：Nygard ADR 的可变索引。ADR 原文不可变，保留在 `docs/archive/adr/`。现行行为一律以 `docs/specs/**` 与 Experience Design 为准。
> 最近校准：2026-08-13
> 上位的不可变原文：`docs/archive/adr/ADR-XXXX-*.md`（32 份）

## 如何使用

1. 想知道“为什么当年这样选、被什么替代” → 在 **Part A / Part B** 按主题查；
2. 想知道软件现在必须怎样表现 → 打开对应 Spec，不要把本页结论当 MUST；
3. 需要决策原文 / 备选方案与后果 → 点 `原文` 链接到 `docs/archive/adr/`；
4. 本页与 Spec 冲突时，**以 Spec 为准**；若决策结论已变，写新 ADR 并更新 Spec。

---

# Part A — 仍被现行 Spec / Experience Design 承接的决策

## 主题 1：Learning Core（教学内核，SYS01-SYS08）

### ADR-0001 — Teaching Strategy Ontology
- Status: `accepted`（2026-08-07）
- 结论：v0.3 顶层 Strategy Family 收敛为 6 族（EXPLICIT_INSTRUCTION / GUIDED_PRACTICE / FADING_PRACTICE 等），`TeachingAction` 采用 immutable strategy family + action/move/modifier/envelope 语义；scaffold/hint/exposure/assistance 正交化。
- 规范：[`specs/systems/05-teaching-policy.md`](../specs/systems/05-teaching-policy.md) + [`specs/domain/domain.md`](../specs/domain.md)
- 原文：[`ADR-0001`](../archive/adr/ADR-0001-teaching-strategy-ontology.md)

### ADR-0002 — Constrained Deterministic Teaching Policy Architecture
- Status: `accepted`（2026-08-07）
- 结论：SYS05 canonical 决策路径固定为 `TeachingContext Snapshot → Typed Hard Constraints → Derived TeachingStage → Candidate Generation → Feature Builder → Normalized Weighted Scoring`；`DecisionTrace` 固定 replayability、assignment probability 与 action propensity 分离、deterministic propensity=null。
- 规范：[`specs/systems/05-teaching-policy.md`](../specs/systems/05-teaching-policy.md) + [`specs/domain/domain.md`](../specs/domain.md)
- 原文：[`ADR-0002`](../archive/adr/ADR-0002-constrained-deterministic-teaching-policy-architecture.md)

### ADR-0003 — Policy Runtime Profile Source and Activation Resolution
- Status: `accepted`（2026-08-08）
- 结论：生产 `PolicyRuntimeProfile` 是仓库内不可变 JSON artifact（`askora-v03-default-1`）；digest = 去 content_digest 后 key 升序 SHA-256；resolver 按 `activated_at DESC, activation_id DESC` fail-closed 解析，缺失/不一致不得回退测试 fixture、最新文件或 LLM；replay 使用已固定的 exact bundle/profile。
- 规范：[`specs/systems/05-teaching-policy.md`](../specs/systems/05-teaching-policy.md)
- 原文：[`ADR-0003`](../archive/adr/ADR-0003-policy-runtime-profile-source-and-activation.md)

### ADR-0004 — Guided Book Learning and Durable Transcript
- Status: `accepted`（2026-08-08）
- 结论：用户只负责不可替代的意图/证据动作；book-learning façade 协调 SYS06/SYS04/SYS08 不复制算法；`GoalKnowledgeMapping.selected_target_ids` 排序具有 rank 语义（rank 1 = 首轮诊断 primary target）；SYS08 新增 append-only transcript projection，不是新学习 truth。
- 规范：[`specs/systems/06-learning-planner.md`](../specs/systems/06-learning-planner.md) + [`specs/systems/08-ai-orchestration.md`](../specs/systems/08-ai-orchestration.md)
- 原文：[`ADR-0004`](../archive/adr/ADR-0004-guided-book-learning-and-durable-transcript.md)

### ADR-0005 — Policy-bound Real-model Rendering
- Status: `accepted`（2026-08-08）
- 结论：`PolicyBoundModelRenderer` 只在已确定 TeachingAction + learner-visible EvidenceBundle 内渲染；模型只负责语言表达，不选策略/动作/状态；prompt 固定版本、最小数据、untrusted evidence 边界；`mode=real_model` 才算真实成功，mock 不得冒充。
- 规范：[`specs/systems/08-ai-orchestration.md`](../specs/systems/08-ai-orchestration.md) + [`specs/interfaces/content.md`](../specs/interfaces/content.md)
- 原文：[`ADR-0005`](../archive/adr/ADR-0005-policy-bound-real-model-rendering.md)

### ADR-0007 — SYS06 Activity Lifecycle and Completion
- Status: `accepted`（2026-08-09）
- 结论：SYS06-owned append-only versioned `LearningActivityStateV1` 是活动状态唯一 canonical source；`SelectNextLearningActivity` 只做 planned→available；`Start/CompleteLearningActivityV1` 校验 owner/版本/幂等/type-specific 前置；完成活动 ≠ objective satisfied / goal achieved / mastery changed。
- 规范：[`specs/systems/06-learning-planner.md`](../specs/systems/06-learning-planner.md) + [`specs/domain/domain.md`](../specs/domain.md)
- 原文：[`ADR-0007`](../archive/adr/ADR-0007-sys06-activity-lifecycle-and-completion.md)

### ADR-0010 — Goal Definition, State, Draft and Safe Replan
- Status: `accepted`（2026-08-09）
- 结论：SYS06 分离 `LearningGoalDefinitionV2` 与 append-only `LearningGoalStateV1`；用户输入先写 `LearningGoalDraftV1` 并通过三重建模门禁；`GoalChangePreviewV1` 固定 refs/fields/target 影响；所有 command 带 expected version / idempotency key / correlation id；意图/能力/成功标准变化建新版本，仅预算/期限变化复用 exact target evidence。
- 规范：[`specs/systems/06-learning-planner.md`](../specs/systems/06-learning-planner.md)
- 原文：[`ADR-0010`](../archive/adr/ADR-0010-goal-definition-state-draft-and-replan.md)

### ADR-0011 — Goal Achievement Measurement and Evidence Gate
- Status: `accepted`（2026-08-09）
- 结论：`LearningObjectiveV1` 结构化 criterion/认知类型/target/evidence requirements；versioned `GoalAchievementPolicyV1` 冻结 delay/novelty/rubric/confidence/reviewer 参数（产品参数，非普适科学常数）；低置信/分歧/provider failure/Prompt Injection 风险进 `needs_review/scoring_failed`；SYS03 只接纳 accepted result。
- 规范：[`specs/systems/06-learning-planner.md`](../specs/systems/06-learning-planner.md) + [`specs/systems/04-assessment.md`](../specs/systems/04-assessment.md) + [`specs/systems/03-learner-model.md`](../specs/systems/03-learner-model.md)
- 原文：[`ADR-0011`](../archive/adr/ADR-0011-goal-achievement-measurement-and-evidence-gate.md)

## 主题 2：Workspace / Identity / 数据控制

### ADR-0015 — Local Single-User Identity Without Authentication
- Status: `accepted`（2026-08-10）
- 结论：**Askora 不再提供 Account/Login/Register/Logout/Password/Recovery/AuthSession**；唯一长期身份为 `LocalOwnerContext (owner_id: UUID)`；`LocalOwner` 是本地数据归属主体，不是 credential principal；所有业务入口解析唯一 LocalOwnerContext。
- 规范：[`specs/platform/platform.md`](../specs/platform.md)（Identity & Privacy Lifecycle）
- 原文：[`ADR-0015`](../archive/adr/ADR-0015-local-single-user-identity-without-authentication.md)

### ADR-0016 — Workspace, LearningProject and LearningSession Scope Ownership
- Status: `accepted`（2026-08-10）
- 结论：Workspace → Platform Workspace Registry；LearningProject/ProjectMaterial → Platform Workspace/Product Organization；LearningSession → Platform Learning Session Registry（非 DialogSession，不拥有 transcript/TeachingAction/Assessment/Mastery truth）；existing `user_documents.id` 保持稳定 Material identity；LearnerEvidence/Mastery/LearnerState/Review 变 Workspace-specific；cross-workspace refs fail closed。
- 规范：[`specs/platform/platform.md`](../specs/platform.md)（Workspace/Project/Session Scope）
- 原文：[`ADR-0016`](../archive/adr/ADR-0016-workspace-project-and-learning-session-scope-ownership.md)

### ADR-0006 — Workspace Read-model Scope and Missing Objective Metadata
- Status: `accepted`（2026-08-09）
- 结论：UI read 层是 additive read-only composition：`/workspace/goals|path|evidence` 按 current identity/workspace 读最新 immutable version；无 `goal_id` 时仅一个 eligible plan 可自动返回，多个返回 scoped-selection 而非任意 winner；缺失 owner 元数据返回 null + `OBJECTIVE_METADATA_UNAVAILABLE`；mastery label 在 SYS03 发布前保持 null。
- 规范：[`specs/ui.md`](../specs/ui.md)（UI Read Model）
- 原文：[`ADR-0006`](../archive/adr/ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md)

### ADR-0103 — Local Data Recovery, Portability and Erasure
- Status: `accepted`（2026-08-09）
- 结论：P1-03 产品范围 = macOS 私人桌面 SQLite（PG/Docker 走独立运维 adapter）；versioned encrypted recovery package + Recovery Key（设备副本 secure storage 保护，跨设备由用户提供）；restore 在 staging 校验/迁移后原子切换；pre-migration verified snapshot 是 destructive migration 硬前置；`DataErasureWorkflowV1` 只协调 owner commands（范围 DOCUMENT / LEARNING_RECORDS / MODEL_EXECUTION / ALL_PERSONAL_DATA），删除写 ErasureCheckpoint/Receipt，projection rebuild 不得重新生成已删事实。
- 规范：[`specs/interfaces/recovery-and-onboarding.md`](../specs/interfaces/recovery-and-onboarding.md) + [`specs/interfaces/persistence-and-data-control.md`](../specs/interfaces/persistence-and-data-control.md)
- 原文：[`ADR-0103`](../archive/adr/ADR-0103-local-data-recovery-portability-erasure.md)

### ADR-0107 — Account Deletion Uses the Canonical Data Erasure Workflow
- Status: `partially superseded by ADR-0015`（Account 语义已退休）；其 owner-erasure 原则承接于 ADR-0103 / P1-03。
- 当前有效结论：P1-05 删除必须调用 P1-03 固定 `ALL_PERSONAL_DATA` scope，P1-03 是唯一 erasure truth；禁止第二套 receipt 流；`PrivacyTombstone` 只是 projection/adapter。
- 规范：[`specs/interfaces/persistence-and-data-control.md`](../specs/interfaces/persistence-and-data-control.md)
- 原文：[`ADR-0107`](../archive/adr/ADR-0107-account-deletion-erasure-workflow-integration.md)

### ADR-0009 — Local-first Identity and Privacy Lifecycle
- Status: `partially superseded by ADR-0015`（Account/AuthSession/Recovery 产品语义退休）。
- 当前有效：Platform Identity & Privacy 是横切边界，不拥有学习 truth；Argon2id、offline 恢复套件、删除 `ACTIVE → DELETION_PENDING → PURGING → DELETED` 状态机、subject manifest 零残留等有独立数据治理价值的**原则**继续承接于 LID 契约。
- 规范：[`specs/platform/platform.md`](../specs/platform.md)
- 原文：[`ADR-0009`](../archive/adr/ADR-0009-local-first-identity-privacy-lifecycle.md)

## 主题 3：Experience / UI / 交互边界

### ADR-0029 — Local and Hybrid Material Parse
- Status: `accepted`（2026-08-13）
- 结论：本地确定性解析始终先跑；LLM 增强解析由设置开关 + 模型就绪共同决定。无 key 强制本机解析；打开开关不自动重跑旧资料；「用模型再解析」是同一 Material 的增强 run。开关不管教学是否用模型。
- 规范：[`specs/systems/01-content-knowledge.md`](../specs/systems/01-content-knowledge.md) + [`specs/systems/08-ai-orchestration.md`](../specs/systems/08-ai-orchestration.md) + Experience
- 原文：[`ADR-0029`](../archive/adr/ADR-0029-local-and-hybrid-material-parse.md)

### ADR-0028 — Assign Unassigned Material to a Workspace
- Status: `accepted`（2026-08-13）
- 结论：默认上传只创建未归属资料；`AssignMaterialToWorkspaceV1` 是唯一归属 command。
- 规范：[`specs/interfaces/content.md`](../specs/interfaces/content.md) + [`specs/interfaces/persistence-and-data-control.md`](../specs/interfaces/persistence-and-data-control.md)
- 原文：[`ADR-0028`](../archive/adr/ADR-0028-assign-material-to-workspace.md)

### ADR-0027 — Welcome Is the Home Destination, Not a First-use Wizard
- Status: `accepted`（2026-08-13）
- 结论：Welcome 是每次打开 App 的回家页；first-use 只保留薄提示。Onboarding 不再把用户送去 `/today` 或确认目标向导。
- 规范：[`specs/ui.md`](../specs/ui.md) + [`specs/interfaces/recovery-and-onboarding.md`](../specs/interfaces/recovery-and-onboarding.md)
- 原文：[`ADR-0027`](../archive/adr/ADR-0027-welcome-home-not-first-use-wizard.md)

### ADR-0026 — Close Core Journey Goal and Unassigned-Material Gaps
- Status: `accepted`（2026-08-13）
- 结论：开始学习不以确认目标为前置（`PD-RULE-004`）；上传允许未归属 Workspace 的 Material（`WSP-021`）。关掉 ADR-0025 留下的两条 GAP。
- 规范：[`product/PRODUCT-DEFINITION.md`](../product/PRODUCT-DEFINITION.md) + [`specs/platform.md`](../specs/platform.md) + Experience
- 原文：[`ADR-0026`](../archive/adr/ADR-0026-close-journey-goal-and-unassigned-material-gaps.md)

### ADR-0025 — Space / Conversation User-facing IA and Core Journeys
- Status: `accepted`（2026-08-13）；两条 GAP 由 ADR-0026 关闭
- 结论：用户侧词汇改为「空间 / 对话」；Core Journey 为「用资料开始」「回来继续」「在对话里学习」「建立或扩充空间」。打开 App 先 Welcome；点已有对话恢复，对空间「继续学习」新开对话。
- 规范：[`design/experience/EXPERIENCE-ARCHITECTURE.md`](../design/experience/EXPERIENCE-ARCHITECTURE.md) + [`specs/ui.md`](../specs/ui.md)
- 原文：[`ADR-0025`](../archive/adr/ADR-0025-space-conversation-core-journeys.md)

### ADR-0022 — Course-centric Information Architecture
- Status: `partially superseded by ADR-0025`（2026-08-11）
- 结论：用户侧 Workspace vocabulary 曾统一为「课程」，canonical Workspace identity 不变；`＋ 新课程` 曾是 Primary Action。现行用户文案与 Core Journey 以 ADR-0025 / current Experience 为准；Workspace identity、三栏、Chat 非 Product Domain 仍有效。
- 规范：[`specs/ui.md`](../specs/ui.md) + [`specs/platform.md`](../specs/platform.md)（Course Workspace Selection）
- 原文：[`ADR-0022`](../archive/adr/ADR-0022-course-centric-information-architecture.md)

### ADR-0023 — Course Workspace Selection and Activity Projection
- Status: `accepted`（2026-08-11）
- 结论：Platform Workspace Registry 拥有 durable versioned `WorkspaceSelection`（与 `Workspace.is_default` 区分）；fresh owner 可零 Workspace；用户侧创建入口现为 `＋ 新建空间` / 「马上开始学习」，command 仍是 atomic create-and-select；switch 使用 expected version + idempotency + typed recovery guard；deep links/GET 无副作用；Course Activity index 是只读 exact SYS06 composition；Activity-scoped LearningSession 不取 SYS06 ownership。
- 规范：[`specs/platform/platform.md`](../specs/platform.md)（CWSP）
- 原文：[`ADR-0023`](../archive/adr/ADR-0023-course-workspace-selection-and-activity-projection.md)

### ADR-0024 — Adopt TraeWork Light as Askora Visual Foundation
- Status: `accepted`（2026-08-13）
- 结论：Askora Light foundation 采用 TraeWork Light 值，保留 Askora semantic roles；accent = `--bg-brand` `#4B3FE3`；v1 不采用 Dark；`shell-replica` 只当构图证据；本轮不实现组件替换。
- 规范：[`specs/ui.md`](../specs/ui.md)（`UI-DS-TOK-*` / `UI-DS-COMP-090`）
- 原文：[`ADR-0024`](../archive/adr/ADR-0024-traework-light-foundation.md)

### ADR-0018 — UX Workspace Context and Three-Column Learning Architecture
- Status: `partially superseded by ADR-0022`（旧 L0 变更）；retained 语义已 consolidation 进 Experience Design。
- 当前有效：left rail = Where（产品导航 + canonical Workspace），center = Learn（唯一 Primary Canvas），right rail = hideable Reference/Notes；Learning Context Drawer 默认折叠；Library v1 UI 不暴露 OCR。
- 规范：[`design/experience/EXPERIENCE-ARCHITECTURE.md`](../design/experience/EXPERIENCE-ARCHITECTURE.md) + [`specs/ui.md`](../specs/ui.md)
- 原文：[`ADR-0018`](../archive/adr/ADR-0018-ux-workspace-context-architecture.md)

### ADR-0019 — UI Workspace Context and Learning Context Read Projections
- Status: `accepted`；single-default query 限制被 ADR-0023 superseded。
- 结论：canonical current Workspace 来自 Platform Workspace Registry（非 route/frontend state）；Drawer stage 来自 exact SYS05 TeachingAction；next 1..3 directions 来自 exact SYS06 LearningActivity refs；stage-goal copy 是 versioned server-side presentation catalog；query assembly 只读、current-Workspace scoped、无副作用、诚实 MISSING/PARTIAL/STALE。
- 规范：[`specs/ui.md`](../specs/ui.md)（UI Read Model）
- 原文：[`ADR-0019`](../archive/adr/ADR-0019-ui-workspace-read-projections.md)

### ADR-0020 — Learning Conversation Message Presentation and Interaction Boundary
- Status: `accepted`（2026-08-11）
- 结论：canonical target = LearningActivity-scoped、SYS08-owned presentation/transcript artifact；Conversation/Message/Block 不成为 LearningEvidence 或第九 owner；`LearningMessageV1` 与不变的非交互 `RenderPayloadV1` 分离；six typed blocks 用 exact owner/provenance/trace refs；frontend 只渲染 server-issued capabilities；legacy Dialog/RenderPayload 是带退休条件的 bounded adapter。
- 规范：[`specs/interfaces/message-and-note.md`](../specs/interfaces/message-and-note.md)（LCMS）
- 原文：[`ADR-0020`](../archive/adr/ADR-0020-learning-conversation-message-presentation-and-interaction-boundary.md)

### ADR-0021 — UserNote Ownership and Source Inspection Boundary
- Status: `accepted`（2026-08-11）
- 结论：`UserNote` 唯一 writer = **Platform Workspace Notes**（Workspace 下 durable personal-artifact owner，非第九 Learning Core）；拥有 identity/scope/anchor/content/version chain/idempotency/conflict recovery/erasure；不得写 Material/SourceSpan/TeachingAction/Assessment/LearnerState/Review/Message/Retrieval truth。
- 规范：[`specs/interfaces/message-and-note.md`](../specs/interfaces/message-and-note.md)（UserNote & Source Inspection）
- 原文：[`ADR-0021`](../archive/adr/ADR-0021-user-note-and-source-inspection-boundary.md)

### ADR-0014 — User-job-driven Information and Interaction Architecture
- Status: `partially superseded by ADR-0018 / ADR-0022`；retained principles 已 consolidation 进 Experience Design。
- 当前有效：交互原语层级、progressive disclosure、component boundary 语义由 Interaction Model 承接。
- 规范：[`design/experience/INTERACTION-MODEL.md`](../design/experience/INTERACTION-MODEL.md)
- 原文：[`ADR-0014`](../archive/adr/ADR-0014-user-job-driven-interaction-architecture.md)

## 主题 4：Local Web / BYOK / 安全

### ADR-0017 — OS-backed LocalSecretStore and Crash-consistent Model Activation
- Status: `accepted`（2026-08-10）
- 结论：生产后端 allowlist（macOS keyring / Windows WinVault），无 third-party/Null/file fallback；opaque random secret refs；SQLite 只存非密 profile/ref/activation journal；durable phase journal 协调 SQLite + OS credential-store 崩溃一致性；restore 缺失 secret → degraded/re-enter，绝不 `.env` resurrection。
- 规范：[`specs/platform.md`](../specs/platform.md)（LSS）+ [`specs/systems/08-ai-orchestration.md`](../specs/systems/08-ai-orchestration.md) + [`specs/quality.md`](../specs/quality.md)
- 原文：[`ADR-0017`](../archive/adr/ADR-0017-os-backed-local-secret-store-and-crash-consistent-model-activation.md)

### ADR-0013 — Desktop Model Credential and Atomic Activation
- Status: `partially superseded`（Desktop/Electron mechanics 退休）；current 语义 = ADR-0017 + Local Web BYOK。
- 当前有效：SYS08 拥有 `ModelRouteProfileV1` semantic owner；secret 不进入 Prompt metadata/日志/API response/browser/导出/backup/diagnostic；config error 不得产生 learner failure / AssessmentResult / Mastery / completion / transcript truth；probe 不发送私人资料。
- 规范：[`specs/systems/08-ai-orchestration.md`](../specs/systems/08-ai-orchestration.md) + [`specs/platform/platform.md`](../specs/platform.md)
- 原文：[`ADR-0013`](../archive/adr/ADR-0013-desktop-model-credential-and-activation.md)

## 主题 5：内容 / 恢复 / 引导

### ADR-0008 — Library Management, Deduplication and OCR Governance
- Status: `partially superseded by Product Positioning / Product Definition`（OCR-as-core / global library / archive-restore 语义退休）。
- 当前有效：SYS01 拥有 Material metadata/content/dedupe 决定权；`original_filename` + checksum 不可变、`display_title/subject/author/language` 可编辑（versioned + optimistic concurrency）；search projection 可重建、workspace-scoped、非第二 truth；重复建议不自动合并；可选 OCR 候选安全。
- 规范：[`specs/systems/01-content-knowledge.md`](../specs/systems/01-content-knowledge.md) + [`specs/interfaces/content.md`](../specs/interfaces/content.md) + [`specs/interfaces/persistence-and-data-control.md`](../specs/interfaces/persistence-and-data-control.md)
- 原文：[`ADR-0008`](../archive/adr/ADR-0008-library-management-deduplication-and-ocr.md)

### ADR-0012 — Unified Recovery Control Plane
- Status: `accepted`（2026-08-09）
- 结论：双入口单合同：运行期 `/settings/recovery` + Electron bootstrap recovery shell（后者仅当后端不可达）；`RecoveryIssueViewV1` 是 SYS08 只读投影；`RecoveryActionV1` 闭集，command router 只分派给原 owner。
- 规范：[`specs/interfaces/recovery-and-onboarding.md`](../specs/interfaces/recovery-and-onboarding.md)
- 原文：[`ADR-0012`](../archive/adr/ADR-0012-unified-recovery-control-plane.md)

### ADR-0106 — Fact-driven Onboarding Readiness and Presentation Preferences
- Status: `accepted`；default-entry 假设部分被 ADR-0022 superseded。
- 结论：事实驱动、可恢复的 journey，非一次性 wizard；`OnboardingPreferenceV1` 只存 presentation-only 偏好；`OnboardingJourneyViewV1` 是只读投影；第一节完成只由 SYS06 `FirstActivityCompletionProjectionV1` 的 exact evidence 决定；一个 response 只返回一个 server-selected `next_action`。
- 规范：[`specs/interfaces/recovery-and-onboarding.md`](../specs/interfaces/recovery-and-onboarding.md)
- 原文：[`ADR-0106`](../archive/adr/ADR-0106-fact-driven-onboarding-readiness-and-preferences.md)

---

# Part B — 历史废止索引

| ADR | 当前状态 | 被什么替代 | 当前语义承接 |
|---|---|---|---|
| ADR-0008 | partially superseded | Product Positioning / Definition（OCR-as-core、global library、archive-restore 退休） | SYS01 LIB/MATLIFE contracts |
| ADR-0009 | partially superseded | ADR-0015 | LID 原则（Argon2id、offline recovery、删除状态机） |
| ADR-0013 | partially superseded | ADR-0017 + Local Web BYOK | MODEL-CONFIG / LSS / SEC |
| ADR-0014 | partially superseded | ADR-0018 / ADR-0022 | Experience Design + Interaction Model |
| ADR-0018 | partially superseded | ADR-0022（旧 L0） | Experience Design + UI contracts |
| ADR-0019 | 部分（single-default） | ADR-0023 | CWSP + UI Read Model |
| ADR-0022 | 部分（课程词汇 / 五条 Journey / 启动直达） | ADR-0025 | Experience Design + UI contracts |
| ADR-0106 | 部分（default-entry / 用户可见 GOAL / OPEN_TODAY） | ADR-0025 / ADR-0027 | Onboarding + Welcome home |
| ADR-0027 | 现行 | — | Welcome destination + onboarding thin notice |
| ADR-0028 | 现行 | — | Unassigned upload + AssignMaterial command |
| ADR-0029 | 现行 | — | Local / hybrid material parse + Settings toggle |
| ADR-0107 | partially superseded | ADR-0015（Account 语义退休） | P1-03 erasure workflow |

> 规则：历史 ADR 原文保留在 `docs/archive/adr/`。若未来新决策 supersede 某 ADR，更新本索引的 Status 与指向，并同步修改对应 Spec；不得只改本页而让 Spec 落后。
