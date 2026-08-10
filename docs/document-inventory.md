# Askora 文档处置清单

> 状态：Current  
> 校准日期：2026-08-10
> 基线提交：`241dce1ba91f422f13bd07d224e34f48cf6cc098`  
> 范围：受 Git 跟踪或本次新增的 Markdown/RST 文件；生成产物中的复制文件不作为独立权威来源。

处置代码：

- `CURRENT-UPDATED`：当前说明，已按稳定代码基线更新；
- `CANONICAL-RETAIN`：冻结合同或正式设计，保留语义；
- `HISTORICAL-RETAIN`：保留为历史、研究或发布证据，不作为当前状态；
- `SUPPORT-RETAIN`：工具、构建或设计辅助资产；
- `EXCLUDED`：测试夹具，不属于项目说明；
- `DELETED`：已确认无持续维护价值并删除。

## 1. 根目录与应用说明

| 文件 | 处置 | 说明 |
|---|---|---|
| `AGENTS.md` | CANONICAL-RETAIN | Codex 强制执行合同 |
| `README.md` | CURRENT-UPDATED | 当前产品、实现、运行和验证入口 |
| `Askora EXEC-042 执行提示词.md` | SUPPORT-RETAIN | EXEC-042 执行代理提示词 |
| `Askora EXEC-1062 执行提示词.md` | SUPPORT-RETAIN | EXEC-1062 执行代理提示词 |
| `Askora EXEC-047 执行提示词.md` | SUPPORT-RETAIN | EXEC-047 执行代理提示词 |
| `apps/backend/README.md` | CURRENT-UPDATED | 后端模块与命令已对齐 v0.3/CI |
| `apps/frontend/README.md` | CURRENT-UPDATED | 当前前端说明；Desktop/Electron 历史内容不得覆盖 v1 Local Web 产品定位 |
| `apps/frontend/resources/backend/README.md` | SUPPORT-RETAIN | Electron 历史后端资源目录说明；非 v1 canonical runtime |
| `apps/backend/.trae/documents/seed_data_plan.md` | DELETED | 一次性计划已实现；旧策略分类会误导当前语义 |
| `apps/backend/tests/fixtures/malicious_document.md` | EXCLUDED | 安全测试输入，不是说明文档 |
| `apps/backend/data/documents/user_pseudo_001/6dcb2a02-322a-4e35-b33a-54708b8d5904_3673b0a7.md` | EXCLUDED | 测试种子数据，不是项目说明 |
| `.design_library/Askora/README.md` | SUPPORT-RETAIN | UI 设计资产，不是 Canonical Design |
| `.design_library/Askora/SKILL.md` | SUPPORT-RETAIN | 设计工具指令，不是项目实现合同 |

## 2. 文档索引、Product、ADR 与 Release

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/README.md` | CURRENT-UPDATED | Product→Design→ADR→Spec→EXEC 权威层级与 v1 Local Web 架构入口 |
| `docs/CODE_WIKI.md` | CURRENT-UPDATED | 当前代码架构、模块职责与本地源码导航参考 |
| `docs/document-inventory.md` | CURRENT-UPDATED | 本清单 |
| `docs/product/PRODUCT-POSITIONING.md` | CANONICAL-RETAIN | **Askora v1 最高 Frozen Product Baseline**；Local Web、LocalOwner、Workspace、SQLite/local-first、BYOK、Non-goals 与 Hard Constraints |
| `docs/product-gap-register-p1-p2.md` | CURRENT-UPDATED | 当前 P1/P2 产品缺口登记；历史状态不得突破 PRODUCT-POSITIONING |
| `docs/adr/README.md` | CANONICAL-RETAIN | ADR 治理、Product Positioning 上位约束、supersession 与索引 |
| `docs/adr/ADR-0001-teaching-strategy-ontology.md` | CANONICAL-RETAIN | Accepted decision record |
| `docs/adr/ADR-0002-constrained-deterministic-teaching-policy-architecture.md` | CANONICAL-RETAIN | Accepted decision record |
| `docs/adr/ADR-0003-policy-runtime-profile-source-and-activation.md` | CANONICAL-RETAIN | Accepted production profile source / activation resolution decision |
| `docs/adr/ADR-0004-guided-book-learning-and-durable-transcript.md` | CANONICAL-RETAIN | User-delegated guided flow and SYS08 transcript decision |
| `docs/adr/ADR-0005-policy-bound-real-model-rendering.md` | CANONICAL-RETAIN | User-delegated production real-model rendering and E2E decision |
| `docs/adr/ADR-0006-workspace-read-model-scope-and-missing-objective-metadata.md` | CANONICAL-RETAIN | UI-02B read scope、objective missing semantics；Workspace current semantics 服从 Product Positioning |
| `docs/adr/ADR-0007-sys06-activity-lifecycle-and-completion.md` | CANONICAL-RETAIN | SYS06 activity lifecycle、completion 与迁移决策 |
| `docs/adr/ADR-0008-library-management-deduplication-and-ocr.md` | CANONICAL-RETAIN | **Partially superseded**；metadata/provenance/dedup invariant 保留，OCR-as-core/global-library/archive mechanics 已退役 |
| `docs/adr/ADR-0009-local-first-identity-privacy-lifecycle.md` | CANONICAL-RETAIN | P1-05 历史 identity/privacy 决策；Account/Auth semantics 由 ADR-0015 supersede |
| `docs/adr/ADR-0010-goal-definition-state-draft-and-replan.md` | CANONICAL-RETAIN | P1-01A Definition/State/Draft/Replan 决策 |
| `docs/adr/ADR-0011-goal-achievement-measurement-and-evidence-gate.md` | CANONICAL-RETAIN | P1-01B evidence-gated achievement 决策 |
| `docs/adr/ADR-0012-unified-recovery-control-plane.md` | CANONICAL-RETAIN | P1-07 统一恢复控制面与 bootstrap diagnostics 决策 |
| `docs/adr/ADR-0013-desktop-model-credential-and-activation.md` | CANONICAL-RETAIN | **Partially superseded**；routing/secret/probe/rollback invariant 保留，Desktop/Electron mechanics 已退役 |
| `docs/adr/ADR-0014-user-job-driven-interaction-architecture.md` | CANONICAL-RETAIN | Accepted user-job-driven IA、3-domain navigation 与 Interactive Element System 决策 |
| `docs/adr/ADR-0015-local-single-user-identity-without-authentication.md` | CANONICAL-RETAIN | Accepted LocalOwner/no-auth/loopback identity decision |
| `docs/adr/ADR-0103-local-data-recovery-portability-erasure.md` | CANONICAL-RETAIN | P1-03 local recovery、portability 与 owner erasure decision |
| `docs/adr/ADR-0106-fact-driven-onboarding-readiness-and-preferences.md` | CANONICAL-RETAIN | P1-06 presentation preference、owner-fact readiness 与首次完成/路由决策 |
| `docs/adr/ADR-0107-account-deletion-erasure-workflow-integration.md` | CANONICAL-RETAIN | 历史 account deletion integration；Account semantics 由 ADR-0015 supersede，owner-safe erasure invariant 保留 |
| `docs/releases/README.md` | CURRENT-UPDATED | 历史证据索引；历史结果不等于 current checkout verification |
| `docs/releases/v0.2-first-vertical-learning-loop.md` | HISTORICAL-RETAIN | v0.2 release evidence snapshot |
| `docs/releases/v0.3-governance-preconditions.md` | HISTORICAL-RETAIN | EXEC-007 durable evidence snapshot |
| `docs/releases/v0.3-adaptive-teaching-loop.md` | HISTORICAL-RETAIN | v0.3 release evidence；指定历史快照边界 |
| `docs/releases/ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN | UI-01 completion evidence snapshot |
| `docs/releases/ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN | UI-02A completion evidence snapshot |
| `docs/releases/p1-03-data-control-recovery.md` | CURRENT-UPDATED | P1-03 历史/当前本地恢复证据；Desktop-specific evidence 不定义 v1 runtime |
| `docs/releases/ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN | UI-02B2 guided learning completion evidence snapshot |
| `docs/releases/p1-04-library-management.md` | HISTORICAL-RETAIN | P1-04 search/organization/dedup/local OCR 历史 completion evidence；OCR 非 v1 core |
| `docs/releases/p1-01a-goal-definition-draft-replan.md` | HISTORICAL-RETAIN | P1-01A Definition/Draft/Replan completion evidence |
| `docs/releases/p1-01b-goal-lifecycle-achievement.md` | HISTORICAL-RETAIN | P1-01B Lifecycle/Achievement completion evidence |

## 3. Canonical Design 与 Research

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/design/README.md` | CURRENT-UPDATED | Design 层索引；明确 Product Positioning 为上位约束 |
| `docs/design/个人AI辅助学习平台设计方案.md` | CURRENT-UPDATED | Canonical Design 语义保留；与 Product Positioning 冲突处由上位基线 supersede |
| `docs/design/AI学习系统算法与教学内核设计.md` | CURRENT-UPDATED | 学习内核 Canonical Design；Teaching Policy 等 v0.3 核心继续有效 |
| `docs/design/Interactive-Element-System-Canonical-Design-Delta.md` | CANONICAL-RETAIN | ADR-0014 上游 Interactive Element Taxonomy 与页面级 IA 设计输入 |
| `docs/design/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md` | CANONICAL-RETAIN | ADR-0015 上游 LocalOwner/no-auth/loopback 设计冻结输入 |
| `docs/design/v0.3-Canonical-Design-Delta.md` | CANONICAL-RETAIN | v0.3 Research Synthesis → Canonical Design 冻结变更记录 |
| `docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md` | CURRENT-UPDATED | 指定 main snapshot 对 frozen v0.3 Design/Spec 的实现一致性审计；不是新合同 |
| `docs/design/CI-Test-Infrastructure-Gap-Analysis.md` | CURRENT-UPDATED | 当前 CI/Test Infrastructure 与 v1 Local Web/Product Positioning 对齐 Gap Analysis |
| `docs/design/账号与隐私生命周期设计.md` | CANONICAL-RETAIN | 历史设计基线；Account/Login/AuthSession/Recovery/Account Deletion 语义已 superseded |
| `docs/design/p1-03-data-control-and-recovery.md` | CURRENT-UPDATED | P1-03 data protection additive Canonical Design；保留 owner-safe data lifecycle |
| `docs/design/p1-02-model-settings.md` | CANONICAL-RETAIN | P1-02 历史模型配置设计；Desktop mechanics 由当前 Local Web model config contract supersede |
| `docs/design/p1-06-fact-driven-first-use-journey.md` | CANONICAL-RETAIN | P1-06 事实驱动、可恢复的首次学习旅程设计 |
| `docs/design/research/README.md` | CURRENT-UPDATED | Research Delta 改为已完成历史输入 |
| `docs/design/research/evidence/八类技术系统-教育科学证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-ITS与学习者建模证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-检索与知识架构证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-教学策略与序列决策证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-记忆与复习调度证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-LLM-Agent与可信治理证据.md` | HISTORICAL-RETAIN | 独立研究证据 |
| `docs/design/research/evidence/八类技术系统-参考资料索引.md` | HISTORICAL-RETAIN | 外部证据索引；未重新验证外部网页存续 |
| `docs/design/research/synthesis/4.1-内容解析与知识建模-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.2-检索与知识供给-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.3-学习者建模-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.4-评估与错误诊断-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.5-教学策略选择-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.6-学习路径与任务调度-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.7-记忆保持与复习调度-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/4.8-LLM生成Agent编排与可信控制-系统设计研究.md` | HISTORICAL-RETAIN | 分系统研究设计 |
| `docs/design/research/synthesis/DR-03-01-教学策略与支架转换研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/DR-03-02-错误诊断到教学补救研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/DR-03-03-Teaching-Policy-决策算法与数据契约研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/DR-03-04-学习效果验证与产品实验研究.md` | HISTORICAL-RETAIN | v0.3 Research Delta evidence |
| `docs/design/research/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md` | HISTORICAL-RETAIN | v0.3 frozen research input |
| `docs/design/research/synthesis/v0.3-候选范围分析.md` | HISTORICAL-RETAIN | completed pre-design input |
| `docs/design/research/synthesis/v0.3-深度研究议程.md` | HISTORICAL-RETAIN | completed research agenda |
| `docs/design/research/synthesis/八类技术系统-公共架构冻结稿.md` | HISTORICAL-RETAIN | 已由 Canonical Design/Specs 吸收 |
| `docs/design/research/synthesis/八类技术系统-现状诊断.md` | HISTORICAL-RETAIN | pre-v0.2 snapshot |
| `docs/design/research/synthesis/八类技术系统-系统设计研究综合与溯源.md` | HISTORICAL-RETAIN | 研究拆分与溯源入口 |

## 4. Implementation Specs

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/specs/README.md` | CURRENT-UPDATED | Product→Design→ADR→Spec authority；v0.3 Learning Core + v1 Local Web alignment index |
| `docs/specs/architecture/state-ownership.md` | CANONICAL-RETAIN | Learning Core single-writer + LocalOwner/Workspace + Durable/Derived ownership contract |
| `docs/specs/architecture/system-architecture.md` | CANONICAL-RETAIN | Browser→loopback Local Server、SQLite/local files/jobs、SYS01～SYS08 canonical architecture |
| `docs/specs/architecture/dependency-rules.md` | CANONICAL-RETAIN | LocalOwner/Workspace scope、no cross-owner writes、no production Electron/Redis/Postgres dependency |
| `docs/specs/domain/domain-model.md` | CANONICAL-RETAIN | v0.3 objects + v1 LocalOwner/Workspace/Material/Project/Session/Durable-Derived alignment |
| `docs/specs/domain/decision-contract.md` | CANONICAL-RETAIN | v0.3 DecisionTrace/replay contract |
| `docs/specs/domain/event-contract.md` | CANONICAL-RETAIN | v0.3 event contract |
| `docs/specs/domain/lifecycle-state-machines.md` | CANONICAL-RETAIN | lifecycle contract；删除/账号语义冲突时服从最新 Product/Data Control contracts |
| `docs/specs/interfaces/api-contract.md` | CANONICAL-RETAIN | API contract；身份与网络边界服从 LID/loopback Product Positioning |
| `docs/specs/interfaces/content-ingestion-contract.md` | CANONICAL-RETAIN | SPEC-D01；managed copy、Workspace scope、阶段化 local jobs、v1 core formats/source replay |
| `docs/specs/interfaces/recovery-contract.md` | CANONICAL-RETAIN | P1-07 strict recovery issue/action/result contract |
| `docs/specs/interfaces/data-control-contract.md` | CANONICAL-RETAIN | P1-03 recovery/export/erasure；Account-specific semantics superseded |
| `docs/specs/interfaces/error-contract.md` | CANONICAL-RETAIN | stable error contract |
| `docs/specs/interfaces/persistence-contract.md` | CANONICAL-RETAIN | SQLite production baseline、local files/jobs、Backup/Restore/Migration、Trash/no-resurrection |
| `docs/specs/interfaces/onboarding-contract.md` | CANONICAL-RETAIN | P1-06 LocalOwner/no-auth readiness/single next action/route contract |
| `docs/specs/interfaces/render-content-contract.md` | CANONICAL-RETAIN | v0.3.1 rich response rendering contract |
| `docs/specs/interfaces/schema-versioning.md` | CANONICAL-RETAIN | versioning contract；须服从 v1 datastore compatibility gate |
| `docs/specs/quality/testing-standard.md` | CANONICAL-RETAIN | v0.3 quality contract |
| `docs/specs/quality/observability-standard.md` | CANONICAL-RETAIN | v0.3 observability contract；remote analytics 非 runtime prerequisite |
| `docs/specs/quality/definition-of-done.md` | CANONICAL-RETAIN | Engineering/Policy/Learning Evidence release gates |
| `docs/specs/quality/security-standard.md` | CANONICAL-RETAIN | security contract |
| `docs/specs/quality/ci-infrastructure-standard.md` | CANONICAL-RETAIN | 当前 CI/Test Infrastructure 标准；必须服从 v1 Local Web/Product Positioning |
| `docs/specs/quality/v1-local-web-quality-reconciliation.md` | CANONICAL-RETAIN | v1 Local Web quality gate 与历史 Desktop/服务化测试基线 reconciliation contract |
| `docs/specs/systems/01-content-knowledge.md` | CANONICAL-RETAIN | SYS01 content/knowledge contract |
| `docs/specs/systems/01-content-granularity.md` | CANONICAL-RETAIN | SPEC-D02；多粒度内容模型冻结合同 |
| `docs/specs/systems/01-knowledge-publish-pipeline.md` | CANONICAL-RETAIN | SPEC-D03；知识候选验证/发布冻结合同 |
| `docs/specs/systems/01-library-management.md` | CANONICAL-RETAIN | Workspace Material/search/dedup/Trash/Project relation；OCR legacy/optional 非 v1 core |
| `docs/specs/systems/02-retrieval.md` | CANONICAL-RETAIN | workspace-required RetrievalScope、rebuildable local indexes、tightening-only |
| `docs/specs/systems/03-learner-model.md` | CANONICAL-RETAIN | workspace-scoped LearningEvidence → rebuildable LearnerState/Mastery projection |
| `docs/specs/systems/04-assessment.md` | CANONICAL-RETAIN | SYS04 contract |
| `docs/specs/systems/05-teaching-policy.md` | CANONICAL-RETAIN | SYS05 deterministic Teaching Policy contract；v0.3 semantics 保留 |
| `docs/specs/systems/06-learning-planner.md` | CANONICAL-RETAIN | SYS06 contract |
| `docs/specs/systems/06-activity-lifecycle.md` | CANONICAL-RETAIN | SYS06 versioned activity lifecycle |
| `docs/specs/systems/06-goal-management.md` | CANONICAL-RETAIN | P1-01 goal definition/lifecycle/achievement contract |
| `docs/specs/systems/06-goal-knowledge-mapping.md` | CANONICAL-RETAIN | SPEC-D04；LearningGoal→Knowledge mapping |
| `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md` | CANONICAL-RETAIN | SPEC-D05；prerequisite diagnostic bootstrap |
| `docs/specs/systems/07-review-scheduler.md` | CANONICAL-RETAIN | SYS07 contract |
| `docs/specs/systems/08-ai-orchestration.md` | CANONICAL-RETAIN | SYS08 execution/model/tool orchestration contract |
| `docs/specs/systems/08-model-configuration.md` | CANONICAL-RETAIN | Local Web BYOK、loopback API、LocalSecretStore、probe/activation/rollback；Desktop mechanics superseded |
| `docs/specs/vertical-slices/v0.2-learning-loop.md` | HISTORICAL-RETAIN | v0.2 frozen historical baseline |
| `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md` | CURRENT-UPDATED | v0.3 Learning Core frozen slice；实时实现状态由 EXEC/release evidence 决定 |
| `docs/specs/vertical-slices/v0.3.1-rich-response-rendering.md` | CANONICAL-RETAIN | v0.3.1 additive presentation slice |
| `docs/specs/vertical-slices/book-to-adaptive-learning.md` | CANONICAL-RETAIN | SPEC-D06；Book-to-Adaptive-Learning E2E；runtime/material scope 服从 v1 current contracts |
| `docs/specs/ui/README.md` | CANONICAL-RETAIN | ADR-0014 UI Interaction Architecture 合同入口 |
| `docs/specs/ui/interactive-element-system.md` | CANONICAL-RETAIN | semantic primitives/L0～L5/pattern qualification |
| `docs/specs/ui/information-architecture.md` | CANONICAL-RETAIN | Today/Learning/Library navigation/routes/Shell |
| `docs/specs/ui/screen-contracts.md` | CANONICAL-RETAIN | 页面状态、任务层级与交互合同 |
| `docs/specs/ui/data-contracts.md` | CANONICAL-RETAIN | UI 只读查询接口与来源语义 |
| `docs/specs/ui/visual-system.md` | CANONICAL-RETAIN | visual/accessibility contract |
| `docs/specs/ui/quality-and-migration.md` | CANONICAL-RETAIN | UI quality/migration contract |
| `docs/specs/vertical-slices/ui-01-learning-shell-workspace.md` | CANONICAL-RETAIN | UI-01 historical implemented slice |
| `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md` | CANONICAL-RETAIN | UI-02A historical implemented slice；global-library semantics 服从 v1 workspace scope |
| `docs/specs/vertical-slices/ui-02b1-material-learning-launch.md` | CANONICAL-RETAIN | UI-02B1 material→learning launch historical slice |
| `docs/specs/vertical-slices/ui-02b2-guided-book-learning.md` | CANONICAL-RETAIN | UI-02B2 guided learning/durable transcript historical slice |
| `docs/specs/vertical-slices/ui-02b3-real-model-guided-learning.md` | CANONICAL-RETAIN | UI-02B3 real-model historical slice；model settings runtime 服从 Local Web current contract |
| `docs/specs/vertical-slices/ui-02b-goals-path-evidence.md` | CANONICAL-RETAIN | UI-02B Goals/Path/Evidence historical slice |
| `docs/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md` | CANONICAL-RETAIN | UI-02C activity lifecycle slice |
| `docs/specs/vertical-slices/ui-03-interactive-element-system-refactor.md` | CANONICAL-RETAIN | ADR-0014 UI-03 Vertical Slice；不得突破 Product Positioning |
| `docs/specs/platform/identity-privacy-lifecycle.md` | CANONICAL-RETAIN | ADR-0015 LID v2 LocalOwner/no-auth/loopback current platform contract |
| `docs/specs/vertical-slices/p1-05-account-lifecycle.md` | HISTORICAL-RETAIN | **SUPERSEDED account lifecycle historical implementation slice** |
| `docs/specs/vertical-slices/p1-04a-library-organization.md` | HISTORICAL-RETAIN | P1-04A historical search/metadata/organization slice；current scope=Workspace |
| `docs/specs/vertical-slices/p1-04b-library-deduplication.md` | HISTORICAL-RETAIN | P1-04B historical duplicate governance slice |
| `docs/specs/vertical-slices/p1-04c-library-ocr-review.md` | HISTORICAL-RETAIN | **Historical optional OCR slice；OCR 非 v1 core/release prerequisite** |
| `docs/specs/vertical-slices/p1-07-error-recovery-center.md` | CANONICAL-RETAIN | P1-07 unified recovery slice |
| `docs/specs/vertical-slices/p1-03-data-control-recovery.md` | CANONICAL-RETAIN | P1-03 backup/restore/export/erasure slice；account semantics superseded |
| `docs/specs/vertical-slices/p1-02-model-settings.md` | HISTORICAL-RETAIN | **Historical Desktop model-settings slice；current runtime 由 MODEL-CONFIG Local Web contract supersede** |
| `docs/specs/vertical-slices/p1-06-first-use-onboarding.md` | CANONICAL-RETAIN | P1-06 LocalOwner/no-auth onboarding slice |
| `docs/specs/vertical-slices/local-single-user-authentication-removal.md` | CANONICAL-RETAIN | Local Single-User Authentication Removal migration slice |
| `docs/specs/vertical-slices/p1-01a-goal-definition-draft-replan.md` | CANONICAL-RETAIN | P1-01A Goal Definition/Draft/Replan slice |
| `docs/specs/vertical-slices/p1-01b-goal-lifecycle-achievement.md` | CANONICAL-RETAIN | P1-01B Goal Lifecycle/Achievement slice |

## 5. EXEC 历史合同

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/exec-plans/README.md` | CURRENT-UPDATED | 当前 active/completed EXEC 队列索引；实时状态以该文件为准 |
| `docs/exec-plans/completed/README.md` | CURRENT-UPDATED | 已完成 EXEC 的统一索引 |
| `docs/exec-plans/active/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md` | CANONICAL-RETAIN | v0.3 production sequential policy closure contract；实时完成状态以文件与 release evidence 为准 |
| `docs/exec-plans/completed/EXEC-001-contracts-event-outbox-foundation.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-002-canonical-teaching-entry.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-003-content-evidence-bundle.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-004-assessment-learner-projection.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-005-review-planner-integration.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-006-v0.2-e2e-quality-gate.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-007-v0.3-governance-preconditions.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-008-v0.3-contracts-schema-migration.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-009-deterministic-teaching-policy-kernel.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-010-adaptive-transition-anti-oscillation.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-011-cross-system-adaptive-execution.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-012-outcome-experiment-opve-foundation.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-013-v0.3-e2e-release-gate.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-014-rich-response-rendering.md` | HISTORICAL-RETAIN | 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-015-ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN | UI-01 不可变任务合同 |
| `docs/exec-plans/completed/EXEC-016-ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN | UI-02A 任务合同 |
| `docs/exec-plans/completed/EXEC-017-structure-preserving-epub-ingestion.md` | HISTORICAL-RETAIN | Book-to-Learning EPUB ingestion 历史任务合同 |
| `docs/exec-plans/completed/EXEC-018-multi-granularity-content-projections.md` | HISTORICAL-RETAIN | 多粒度内容模型历史任务合同 |
| `docs/exec-plans/completed/EXEC-019-knowledge-verification-publication.md` | HISTORICAL-RETAIN | 知识候选验证/发布历史任务合同 |
| `docs/exec-plans/completed/EXEC-020-retrieval-projection-sys02-binding.md` | HISTORICAL-RETAIN | SYS02 retrieval projection binding 历史任务合同 |
| `docs/exec-plans/completed/EXEC-021-learning-goal-knowledge-mapping.md` | HISTORICAL-RETAIN | Goal→Knowledge mapping 历史任务合同 |
| `docs/exec-plans/completed/EXEC-022-prerequisite-diagnostic-planner-bootstrap.md` | HISTORICAL-RETAIN | prerequisite diagnostic/planner bootstrap 历史任务合同 |
| `docs/exec-plans/completed/EXEC-023-book-learning-orchestration-api.md` | HISTORICAL-RETAIN | Book learning orchestration API 历史任务合同 |
| `docs/exec-plans/completed/EXEC-024-book-to-learning-e2e-release-gate.md` | HISTORICAL-RETAIN | Book-to-Learning E2E 历史任务合同 |
| `docs/exec-plans/completed/EXEC-025-ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN | 单份资料到 canonical teaching 启动 UI 历史任务合同 |
| `docs/exec-plans/completed/EXEC-026-ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN | 系统带领 Book Learning/durable transcript 历史任务合同 |
| `docs/exec-plans/completed/EXEC-027-ui-02b3-real-model-e2e.md` | HISTORICAL-RETAIN | production real-model rendering/真实 E2E 历史合同 |
| `docs/exec-plans/completed/EXEC-028-zhipu-development-model.md` | HISTORICAL-RETAIN | 智谱开发模型接入历史任务合同 |
| `docs/exec-plans/completed/EXEC-029-ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN | Goals/Path/Evidence UI 历史任务合同 |
| `docs/exec-plans/completed/EXEC-030-ui-02c-canonical-activity-lifecycle.md` | HISTORICAL-RETAIN | UI-02C lifecycle 历史任务合同 |
| `docs/exec-plans/completed/EXEC-031-p1-04a-library-organization.md` | HISTORICAL-RETAIN | P1-04A completed execution contract |
| `docs/exec-plans/completed/EXEC-032-p1-04b-library-deduplication.md` | HISTORICAL-RETAIN | P1-04B completed execution contract |
| `docs/exec-plans/completed/EXEC-033-p1-04c-library-ocr-review.md` | HISTORICAL-RETAIN | P1-04C OCR historical completed execution contract |
| `docs/exec-plans/completed/EXEC-034-identity-session-foundation.md` | HISTORICAL-RETAIN | P1-05 durable session/password historical EXEC |
| `docs/exec-plans/completed/EXEC-035-local-account-recovery.md` | HISTORICAL-RETAIN | P1-05 local recovery historical EXEC |
| `docs/exec-plans/completed/EXEC-036-account-deletion-erasure.md` | HISTORICAL-RETAIN | P1-05 account deletion/erasure historical EXEC |
| `docs/exec-plans/completed/EXEC-038-p1-01a-goal-definition-draft-replan.md` | HISTORICAL-RETAIN | P1-01A completed execution contract |
| `docs/exec-plans/completed/EXEC-039-p1-01b-goal-lifecycle-achievement.md` | HISTORICAL-RETAIN | P1-01B completed execution contract |
| `docs/exec-plans/completed/EXEC-040-p1-02a-model-configuration-foundation.md` | HISTORICAL-RETAIN | P1-02A historical model configuration foundation contract |
| `docs/exec-plans/completed/EXEC-037-p1-07-error-recovery-center.md` | HISTORICAL-RETAIN | P1-07 completed execution contract |
| `docs/exec-plans/completed/EXEC-1031-p1-03-recovery-foundation.md` | HISTORICAL-RETAIN | P1-03 recovery foundation completed EXEC |
| `docs/exec-plans/completed/EXEC-1032-p1-03-verified-restore.md` | HISTORICAL-RETAIN | P1-03 verified restore completed EXEC |
| `docs/exec-plans/completed/EXEC-1033-p1-03-user-data-export.md` | HISTORICAL-RETAIN | P1-03 user export completed EXEC |
| `docs/exec-plans/completed/EXEC-1034-p1-03-erasure-ui-release.md` | HISTORICAL-RETAIN | P1-03 erasure/release completed EXEC |
| `docs/exec-plans/completed/EXEC-041-p1-02b-model-settings-product-closure.md` | HISTORICAL-RETAIN | P1-02 historical Desktop model settings closure；current runtime 服从 Local Web MODEL-CONFIG |
| `docs/exec-plans/completed/EXEC-1061-p1-06a-onboarding-readiness-foundation.md` | HISTORICAL-RETAIN | P1-06 preference/readiness completed EXEC |
| `docs/exec-plans/completed/EXEC-1062-p1-06b-onboarding-product-closure.md` | HISTORICAL-RETAIN | P1-06 product closure historical EXEC |
| `docs/exec-plans/completed/EXEC-047-local-owner-foundation-migration.md` | HISTORICAL-RETAIN | LocalOwner Foundation & Migration completed historical contract |
| `docs/exec-plans/completed/EXEC-037-p1-05-p1-03-erasure-integration.md` | HISTORICAL-RETAIN | P1-05/P1-03 erasure integration historical contract |

## 6. Release Evidence

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/releases/README.md` | CURRENT-UPDATED | 历史发布与验收证据索引 |
| `docs/releases/book-to-adaptive-learning.md` | CURRENT-UPDATED | Book-to-Learning Engineering/Contract、Policy/Ownership 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02b1-material-learning-launch.md` | CURRENT-UPDATED | UI-02B1 Engineering/UI Contract/Accessibility 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02b2-guided-book-learning.md` | CURRENT-UPDATED | UI-02B2 Engineering/UI/Contract/Ownership/Security 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02b3-real-model-guided-learning.md` | CURRENT-UPDATED | UI-02B3 历史真实浏览器/provider/PostgreSQL evidence；PostgreSQL 不定义 v1 runtime prerequisite |
| `docs/releases/ui-02b-goals-path-evidence.md` | CURRENT-UPDATED | UI-02B Goals/Path/Evidence Engineering、Ownership 与 Learning Evidence 分离报告 |
| `docs/releases/ui-02c-canonical-activity-lifecycle.md` | CURRENT-UPDATED | UI-02C Engineering、Ownership、浏览器 lifecycle 与 Learning Evidence 分离报告 |
| `docs/releases/p1-07-error-recovery-center.md` | CURRENT-UPDATED | P1-07 历史 Engineering/Ownership/Security evidence；Desktop-specific evidence 不定义 v1 runtime |
| `docs/releases/p1-05-account-lifecycle.md` | HISTORICAL-RETAIN | **Account Lifecycle historical release evidence；current product semantics superseded** |
| `docs/releases/p1-02-model-settings.md` | HISTORICAL-RETAIN | **Desktop model-settings historical release evidence；current Local Web contract supersedes runtime mechanics** |
| `docs/releases/p1-06-first-use-onboarding.md` | CURRENT-UPDATED | P1-06 首次使用 Engineering/Security/Product 与 Learning Evidence 分离报告 |

## 7. 后续维护规则

1. `PRODUCT-POSITIONING.md` 是最高产品约束；所有下位文档必须服从。
2. 当前说明必须随稳定代码和可执行命令更新；未提交实验不得写成已交付能力。
3. Canonical Spec/ADR 的语义变化不能借“文档整理”偷偷突破 Product Positioning。
4. 历史文件保留当时语境；上级索引负责说明其 supersession/lifecycle。
5. 只有完全重复、没有独立证据/设计/审计价值的临时说明才删除。
6. 删除前记录替代来源；删除后运行文档链接/生命周期门禁。
7. 历史 Desktop/OCR/Account/PostgreSQL evidence 可以保留，但不得被解释为 v1 仍要求这些运行形态。
