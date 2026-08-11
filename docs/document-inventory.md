# Askora 文档处置清单

> 状态：Current
> 校准日期：2026-08-11
> 基线提交：`db963d75adade6e8fe3c52d828ac1c4c27bc2dda`
> 目的：为当前受跟踪 Markdown/RST 文档声明 lifecycle/disposition；实时执行状态以 Linear 和 current `main` 为准。

处置代码：

- `CURRENT-UPDATED`：当前说明/索引；
- `CANONICAL-RETAIN`：当前冻结产品/设计/ADR/Spec 合同；
- `HISTORICAL-RETAIN`：历史 EXEC/Release/Research/已 supersede 基线或带 SHA 的审计快照；
- `SUPPORT-RETAIN`：研究、提示词、工具、设计辅助说明；
- `EXCLUDED`：测试夹具/数据，不是项目说明；
- `DELETED`：历史清理记录，文件本身不应继续作为当前说明。

## 1. Root / Application / Support

| 文件 | 处置 | 说明 |
|---|---|---|
| `AGENTS.md` | CANONICAL-RETAIN | Codex 强制执行合同 |
| `README.md` | CURRENT-UPDATED | 当前产品、实现、运行和验证入口 |
| `.github/PULL_REQUEST_TEMPLATE.md` | SUPPORT-RETAIN | Pull Request delivery/review contract；要求 Problem、authority、risk、Required CI、review findings 与 evidence classification |
| `Askora EXEC-042 执行提示词.md` | SUPPORT-RETAIN | EXEC-042 执行代理提示词 |
| `Askora EXEC-1062 执行提示词.md` | SUPPORT-RETAIN | EXEC-1062 执行代理提示词 |
| `Askora EXEC-047 执行提示词.md` | SUPPORT-RETAIN | EXEC-047 执行代理提示词 |
| `Askora EXEC-042 剩余收口执行提示词.md` | SUPPORT-RETAIN | EXEC-042 剩余收口执行提示词 |
| `Askora CI v2 + Local Web Baseline 全链路自主执行提示词.md` | SUPPORT-RETAIN | CI v2 + Local Web Baseline 全链路自主执行提示词 |
| `Professional App Development Framework.md` | SUPPORT-RETAIN | 本地产品开发方法工作稿；不构成 Askora Product/ADR/Spec 权威合同 |
| `askora-learning-conversation-message-system-canonical-design.md` | SUPPORT-RETAIN | 本地消息系统设计工作稿；未进入治理链，不构成 Canonical Design |
| `design-recommendations.md` | SUPPORT-RETAIN | 本地 UI 设计建议工作稿；不覆盖已冻结 UI Specs |
| `exec-report-XIK-174-EXEC-065.md` | HISTORICAL-RETAIN | XIK-174 / EXEC-065 历史执行证据快照 |
| `exec-report-XIK-176-v1-product-positioning-conformance.md` | HISTORICAL-RETAIN | XIK-176 v1 Product Positioning 验收证据快照 |
| `apps/backend/README.md` | CURRENT-UPDATED | 后端模块与命令已对齐 v0.3/CI |
| `apps/frontend/README.md` | CURRENT-UPDATED | 当前前端说明；Desktop/Electron 历史内容不得覆盖 v1 Local Web 产品定位 |
| `apps/frontend/resources/backend/README.md` | SUPPORT-RETAIN | Electron 历史后端资源目录说明；非 v1 canonical runtime |
| `apps/backend/.trae/documents/seed_data_plan.md` | DELETED | 一次性计划已实现；旧策略分类会误导当前语义 |
| `apps/backend/tests/fixtures/malicious_document.md` | EXCLUDED | 安全测试输入，不是说明文档 |
| `apps/backend/data/documents/user_pseudo_001/6dcb2a02-322a-4e35-b33a-54708b8d5904_3673b0a7.md` | EXCLUDED | 测试种子数据，不是项目说明 |
| `.design_library/Askora/README.md` | SUPPORT-RETAIN | UI 设计资产，不是 Canonical Design |
| `.design_library/Askora/SKILL.md` | SUPPORT-RETAIN | 设计工具指令，不是项目实现合同 |

## 2. Product / ADR / Release Index

| 文件 | 处置 | 说明 |
|---|---|---|
| `docs/README.md` | CURRENT-UPDATED | Strategy→Positioning→Product Definition→Design→ADR→Spec→EXEC 权威层级与文档职责边界 |
| `docs/CODE_WIKI.md` | CURRENT-UPDATED | 当前代码架构、模块职责与本地源码导航参考 |
| `docs/document-inventory.md` | CURRENT-UPDATED | 本清单 |
| `docs/product-development-process.md` | CURRENT-UPDATED | Research→Strategy→Positioning→Product Definition→Design/Spec→Linear/EXEC→PR→Evidence 的端到端流程 |
| `docs/product/README.md` | CURRENT-UPDATED | Product Strategy / Positioning / Definition 职责、authority 与 change-control 索引 |
| `docs/product/PRODUCT-STRATEGY.md` | CANONICAL-RETAIN | **最高产品战略意图来源**；Problem、Primary User、JTBD、Vision、Value、Principles、Assumptions、Risks、Success Definition |
| `docs/product/PRODUCT-POSITIONING.md` | CANONICAL-RETAIN | **最高可执行产品边界**；Category、v1 Product Shape、Strategic Constraints、Non-goals、AI/Learning authority |
| `docs/product/PRODUCT-DEFINITION.md` | CANONICAL-RETAIN | **Canonical Product WHAT**；Product Actors、Core Product Objects、CAP-*、PD-RULE-*、PD-REQ-*、Product Acceptance、v1 Scope semantics |
| `docs/product-gap-register-p1-p2.md` | HISTORICAL-RETAIN | 历史 P1/P2 产品缺口快照；实时 backlog / status 迁移至 Linear，不得作为 current work truth |
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
| `docs/adr/ADR-0016-workspace-project-and-learning-session-scope-ownership.md` | CANONICAL-RETAIN | Accepted Workspace/Project/Session scope、ownership 与 migration decision |
| `docs/adr/ADR-0017-os-backed-local-secret-store-and-crash-consistent-model-activation.md` | CANONICAL-RETAIN | Accepted OS-backed LocalSecretStore 与 crash-consistent activation decision |
| `docs/adr/ADR-0018-ux-workspace-context-architecture.md` | CANONICAL-RETAIN | Accepted Workspace Context UX architecture decision；保留 Today single-primary invariant |
| `docs/adr/ADR-0019-ui-workspace-read-projections.md` | CANONICAL-RETAIN | Accepted UI-04 current Workspace / Drawer read-projection ownership and versioning decision |
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

## 3. Canonical Design / Research

| 文件 | 处置 |
|---|---|
| `docs/design/README.md` | CURRENT-UPDATED |
| `docs/design/个人AI辅助学习平台设计方案.md` | CURRENT-UPDATED |
| `docs/design/AI学习系统算法与教学内核设计.md` | CURRENT-UPDATED |
| `docs/design/UX-Architecture-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/Interactive-Element-System-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/Local-Single-User-Identity-Authentication-Removal-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/v0.3-Canonical-Design-Delta.md` | CANONICAL-RETAIN |
| `docs/design/v0.3-Current-Main-Conformance-Gap-Analysis.md` | HISTORICAL-RETAIN |
| `docs/design/v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md` | HISTORICAL-RETAIN |
| `docs/design/CI-Test-Infrastructure-Gap-Analysis.md` | HISTORICAL-RETAIN |
| `docs/design/账号与隐私生命周期设计.md` | HISTORICAL-RETAIN |
| `docs/design/p1-03-data-control-and-recovery.md` | CANONICAL-RETAIN |
| `docs/design/p1-02-model-settings.md` | HISTORICAL-RETAIN |
| `docs/design/p1-06-fact-driven-first-use-journey.md` | CANONICAL-RETAIN |
| `docs/research/README.md` | CURRENT-UPDATED |
| `docs/research/product-strategy/USER-PROBLEM-JTBD-RESEARCH.md` | SUPPORT-RETAIN |
| `docs/research/product-strategy/ALTERNATIVES-OPPORTUNITY-RESEARCH.md` | SUPPORT-RETAIN |
| `docs/design/research/README.md` | CURRENT-UPDATED |
| `docs/design/research/evidence/八类技术系统-教育科学证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-ITS与学习者建模证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-检索与知识架构证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-教学策略与序列决策证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-记忆与复习调度证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-LLM-Agent与可信治理证据.md` | HISTORICAL-RETAIN |
| `docs/design/research/evidence/八类技术系统-参考资料索引.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.1-内容解析与知识建模-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.2-检索与知识供给-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.3-学习者建模-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.4-评估与错误诊断-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.5-教学策略选择-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.6-学习路径与任务调度-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.7-记忆保持与复习调度-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/4.8-LLM生成Agent编排与可信控制-系统设计研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-01-教学策略与支架转换研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-02-错误诊断到教学补救研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-03-Teaching-Policy-决策算法与数据契约研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/DR-03-04-学习效果验证与产品实验研究.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/v0.3-Research-Synthesis-Adaptive-Teaching-Loop.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/v0.3-候选范围分析.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/v0.3-深度研究议程.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/八类技术系统-公共架构冻结稿.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/八类技术系统-现状诊断.md` | HISTORICAL-RETAIN |
| `docs/design/research/synthesis/八类技术系统-系统设计研究综合与溯源.md` | HISTORICAL-RETAIN |

## 4. Implementation Specs

| 文件 | 处置 |
|---|---|
| `docs/specs/README.md` | CURRENT-UPDATED |
| `docs/specs/architecture/state-ownership.md` | CANONICAL-RETAIN |
| `docs/specs/architecture/system-architecture.md` | CANONICAL-RETAIN |
| `docs/specs/architecture/dependency-rules.md` | CANONICAL-RETAIN |
| `docs/specs/domain/domain-model.md` | CANONICAL-RETAIN |
| `docs/specs/domain/decision-contract.md` | CANONICAL-RETAIN |
| `docs/specs/domain/event-contract.md` | CANONICAL-RETAIN |
| `docs/specs/domain/lifecycle-state-machines.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/api-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/content-ingestion-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/recovery-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/data-control-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/error-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/persistence-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/material-lifecycle-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/onboarding-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/render-content-contract.md` | CANONICAL-RETAIN |
| `docs/specs/interfaces/schema-versioning.md` | CANONICAL-RETAIN |
| `docs/specs/platform/identity-privacy-lifecycle.md` | CANONICAL-RETAIN |
| `docs/specs/platform/workspace-project-session-scope.md` | CANONICAL-RETAIN |
| `docs/specs/platform/local-secret-store.md` | CANONICAL-RETAIN |
| `docs/specs/quality/testing-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/test-oracle-classification.md` | CANONICAL-RETAIN |
| `docs/specs/quality/observability-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/definition-of-done.md` | CANONICAL-RETAIN |
| `docs/specs/quality/security-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/ci-infrastructure-standard.md` | CANONICAL-RETAIN |
| `docs/specs/quality/v1-local-web-quality-reconciliation.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-content-knowledge.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-content-granularity.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-knowledge-publish-pipeline.md` | CANONICAL-RETAIN |
| `docs/specs/systems/01-library-management.md` | CANONICAL-RETAIN |
| `docs/specs/systems/02-retrieval.md` | CANONICAL-RETAIN |
| `docs/specs/systems/03-learner-model.md` | CANONICAL-RETAIN |
| `docs/specs/systems/04-assessment.md` | CANONICAL-RETAIN |
| `docs/specs/systems/05-teaching-policy.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-learning-planner.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-activity-lifecycle.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-goal-management.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-goal-knowledge-mapping.md` | CANONICAL-RETAIN |
| `docs/specs/systems/06-prerequisite-diagnostic-bootstrap.md` | CANONICAL-RETAIN |
| `docs/specs/systems/07-review-scheduler.md` | CANONICAL-RETAIN |
| `docs/specs/systems/08-ai-orchestration.md` | CANONICAL-RETAIN |
| `docs/specs/systems/08-model-configuration.md` | CANONICAL-RETAIN |
| `docs/specs/ui/README.md` | CANONICAL-RETAIN |
| `docs/specs/ui/interactive-element-system.md` | CANONICAL-RETAIN |
| `docs/specs/ui/information-architecture.md` | CANONICAL-RETAIN |
| `docs/specs/ui/screen-contracts.md` | CANONICAL-RETAIN |
| `docs/specs/ui/data-contracts.md` | CANONICAL-RETAIN |
| `docs/specs/ui/visual-system.md` | CANONICAL-RETAIN |
| `docs/specs/ui/quality-and-migration.md` | CANONICAL-RETAIN |
| `docs/specs/ui/component-state-contracts.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/v0.2-learning-loop.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/v0.3.1-rich-response-rendering.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/book-to-adaptive-learning.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b3-real-model-guided-learning.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-02c-canonical-activity-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/ui-03-interactive-element-system-refactor.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/ui-04-ux-workspace-context.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-05-account-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-04a-library-organization.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-04b-library-deduplication.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-04c-library-ocr-review.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-07-error-recovery-center.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-03-data-control-recovery.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-02-model-settings.md` | HISTORICAL-RETAIN |
| `docs/specs/vertical-slices/p1-06-first-use-onboarding.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/local-single-user-authentication-removal.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-01a-goal-definition-draft-replan.md` | CANONICAL-RETAIN |
| `docs/specs/vertical-slices/p1-01b-goal-lifecycle-achievement.md` | CANONICAL-RETAIN |

## 5. Execution Plans

Active EXEC contracts are additionally governed by `docs/exec-plans/README.md`; entries below are lifecycle inventory，**不是实时工作状态源**。实时状态属于 Linear 与 EXEC index。

| 文件 | 处置 |
|---|---|
| `docs/exec-plans/README.md` | CURRENT-UPDATED |
| `docs/exec-plans/completed/README.md` | CURRENT-UPDATED |
| `docs/exec-plans/CHAIN-A-UI-03-PROMPT.md` | SUPPORT-RETAIN |
| `docs/exec-plans/CHAIN-B-CI-V2-PROMPT.md` | SUPPORT-RETAIN |
| `docs/exec-plans/active/EXEC-045-ui-03c-library-progressive-disclosure.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-046-ui-03d-settings-legacy-release-closure.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-054-required-core-test-realignment.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-055-local-data-migration-recovery-rebuild-gate.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-056-local-web-chromium-e2e.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-057-ci-workflow-quality-supply-chain.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-058-required-gate-main-protection-closure.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-059-ui-design-system-component-foundation.md` | CANONICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-068-ui-04a-workspace-context-shell-routes.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-069-ui-04b-learning-context-drawer.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/active/EXEC-070-ui-04c-usernote-current-material-right-rail.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-071-ui-04d-learning-management-exposure-removal.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-072-ui-04e-library-v1-no-ocr-exposure.md` | CANONICAL-RETAIN |
| `docs/exec-plans/active/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md` | CANONICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-001-contracts-event-outbox-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-002-canonical-teaching-entry.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-003-content-evidence-bundle.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-004-assessment-learner-projection.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-005-review-planner-integration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-006-v0.2-e2e-quality-gate.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-007-v0.3-governance-preconditions.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-008-v0.3-contracts-schema-migration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-009-deterministic-teaching-policy-kernel.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-010-adaptive-transition-anti-oscillation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-011-cross-system-adaptive-execution.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-012-outcome-experiment-opve-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-013-v0.3-e2e-release-gate.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-014-rich-response-rendering.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-015-ui-01-learning-shell-workspace.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-016-ui-02a-library-knowledge-map.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-017-structure-preserving-epub-ingestion.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-018-multi-granularity-content-projections.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-019-knowledge-verification-publication.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-020-retrieval-projection-sys02-binding.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-021-learning-goal-knowledge-mapping.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-022-prerequisite-diagnostic-planner-bootstrap.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-023-book-learning-orchestration-api.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-024-book-to-learning-e2e-release-gate.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-025-ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-026-ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-027-ui-02b3-real-model-e2e.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-028-zhipu-development-model.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-029-ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-030-ui-02c-canonical-activity-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-031-p1-04a-library-organization.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-032-p1-04b-library-deduplication.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-033-p1-04c-library-ocr-review.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-034-identity-session-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-035-local-account-recovery.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-036-account-deletion-erasure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-037-p1-07-error-recovery-center.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-037-p1-05-p1-03-erasure-integration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-038-p1-01a-goal-definition-draft-replan.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-039-p1-01b-goal-lifecycle-achievement.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-040-p1-02a-model-configuration-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-041-p1-02b-model-settings-product-closure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-043-ui-03a-shell-routes-learning-domain.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-044-ui-03b-today-primary-hierarchy.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-047-local-owner-foundation-migration.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-048-backend-no-auth-loopback-cutover.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-049-frontend-settings-onboarding-deaccounting.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-050-auth-persistence-configuration-cleanup.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-051-local-identity-release-closure.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-052-ci-governance-test-oracle-classification.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-053-production-local-runtime-cutover.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-062-EXECUTION-REPORT.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1031-p1-03-recovery-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1032-p1-03-verified-restore.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1033-p1-03-user-data-export.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1034-p1-03-erasure-ui-release.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1061-p1-06a-onboarding-readiness-foundation.md` | HISTORICAL-RETAIN |
| `docs/exec-plans/completed/EXEC-1062-p1-06b-onboarding-product-closure.md` | HISTORICAL-RETAIN |

## 6. Release Evidence

| 文件 | 处置 |
|---|---|
| `docs/releases/book-to-adaptive-learning.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b1-material-learning-launch.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b2-guided-book-learning.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b3-real-model-guided-learning.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02b-goals-path-evidence.md` | HISTORICAL-RETAIN |
| `docs/releases/ui-02c-canonical-activity-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-07-error-recovery-center.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-05-account-lifecycle.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-02-model-settings.md` | HISTORICAL-RETAIN |
| `docs/releases/p1-06-first-use-onboarding.md` | HISTORICAL-RETAIN |
| `docs/releases/v0.3-production-sequential-policy-closure.md` | HISTORICAL-RETAIN |

## 7. Maintenance Rules

1. `PRODUCT-STRATEGY.md` 是最高产品战略意图；`PRODUCT-POSITIONING.md` 是最高可执行产品边界；`PRODUCT-DEFINITION.md` 是 Canonical Product WHAT；所有下位文档必须服从。
2. 当前工作状态以 Linear / current `main` 为准；静态 Gap Register、EXEC inventory 和历史 audit 不得维护第二套实时状态。
3. 当前说明必须随稳定代码和可执行命令更新；未提交实验不得写成已交付能力。
4. Canonical Spec/ADR 的语义变化不能借“文档整理”偷偷突破 Product Strategy / Positioning / Definition。
5. 历史文件保留当时语境；上级索引负责说明其 supersession/lifecycle。
6. 只有完全重复、没有独立证据/设计/审计价值的临时说明才删除。
7. 删除前记录替代来源；删除后运行文档链接/生命周期门禁。
8. 历史 Desktop/OCR/Account/PostgreSQL evidence 可以保留，但不得被解释为 v1 仍要求这些运行形态。
9. Product Discovery Research 支持 Strategy；Research 不能直接成为 Product Definition 或实现合同；未验证假设必须保留证据状态。
